extends SceneTree
## Validate the actual user mesh, tail repair and retargeted clips in Godot 4.4.1.
const OUTPUT := "/workspace/deliverables/pam_usuario/"
var viewport: SubViewport
var model: Node3D
var skeleton: Skeleton3D
var player: AnimationPlayer
var body: MeshInstance3D
var validated := false
var captures := 0
var report: Dictionary = {}

func _initialize() -> void:
	create_timer(160).timeout.connect(func(): push_error("User model review timed out"); quit(2))
	call_deferred("review")

func discover(node: Node) -> void:
	if node is Skeleton3D:
		skeleton = node
	if node is AnimationPlayer:
		player = node
	if node is MeshInstance3D:
		body = node
	for child in node.get_children():
		discover(child)

func bone(name: String) -> int:
	var index := skeleton.find_bone(name)
	assert(index >= 0, "Missing bone "+name)
	return index

func pose(clip: String, time: float) -> void:
	player.play(clip)
	player.seek(time, true)
	player.pause()
	await process_frame

func validate() -> void:
	assert(skeleton != null and skeleton.get_bone_count() == 22)
	assert(body.skin != null and body.get_node(body.skeleton) == skeleton)
	assert(absf(body.mesh.get_aabb().size.y-1.6) < .002)
	var material := body.mesh.surface_get_material(0) as StandardMaterial3D
	assert(material != null and material.albedo_texture.get_size() == Vector2(4096,4096))
	assert(material.normal_enabled and material.normal_texture != null)
	assert(material.roughness_texture != null)
	for clip in ["Guard","Jab","Cross","Kick","Combo","Spin","Run","ElbowFlex","KneeFlex"]:
		assert(player.has_animation(clip), "Missing clip "+clip)
	var arrays := body.mesh.surface_get_arrays(0)
	assert(arrays[Mesh.ARRAY_INDEX].size()/3 == 49970)
	var rear := 0.0
	for vertex in arrays[Mesh.ARRAY_VERTEX]:
		if absf(vertex.x) < .115 and vertex.y > .362 and vertex.y < .514:
			rear = minf(rear,vertex.z)
	assert(rear > -.32, "Tail geometry must be absent from the bind mesh")
	report["tail_region_rear_extent"] = rear
	var joints := {}
	for side in ["R","L"]:
		var thigh := bone("thigh."+side)
		var shin := bone("shin."+side)
		var foot := bone("foot."+side)
		assert(skeleton.get_bone_parent(shin) == thigh)
		assert(skeleton.get_bone_parent(foot) == shin)
		assert(skeleton.get_bone_parent(bone("toe."+side)) == foot)
		await pose("KneeFlex",0)
		var fixed := skeleton.get_bone_global_pose(thigh)
		var before := skeleton.get_bone_pose_rotation(shin)
		var ankle := skeleton.get_bone_global_pose(foot).origin
		await pose("KneeFlex",.4 if side == "R" else 1.4)
		var angle := rad_to_deg(before.angle_to(skeleton.get_bone_pose_rotation(shin)))
		assert(absf(angle-90) < 1)
		assert(fixed.is_equal_approx(skeleton.get_bone_global_pose(thigh)))
		assert(ankle.distance_to(skeleton.get_bone_global_pose(foot).origin) > .12)
		joints["knee_"+side] = angle
	await pose("ElbowFlex",0)
	var upper := skeleton.get_bone_global_pose(bone("upper_arm.R"))
	var elbow := skeleton.get_bone_pose_rotation(bone("forearm.R"))
	var wrist := skeleton.get_bone_global_pose(bone("hand.R")).origin
	await pose("ElbowFlex",.4)
	var elbow_angle := rad_to_deg(elbow.angle_to(skeleton.get_bone_pose_rotation(bone("forearm.R"))))
	assert(absf(elbow_angle-90) < 1)
	assert(upper.is_equal_approx(skeleton.get_bone_global_pose(bone("upper_arm.R"))))
	assert(wrist.distance_to(skeleton.get_bone_global_pose(bone("hand.R")).origin) > .22)
	joints["elbow_R"] = elbow_angle
	report["joint_angles_degrees"] = joints
	await pose("Jab",.2)
	var arm_scale := skeleton.get_bone_pose_scale(bone("forearm.R"))
	var fist_scale := skeleton.get_bone_pose_scale(bone("hand.R"))
	print("PAM_USER_STRETCH ",arm_scale," ",fist_scale)
	assert(arm_scale.y > 1.04 and arm_scale.y < 1.22)
	assert(fist_scale.x > 1.05 and fist_scale.x < 1.25)
	report["impact_forearm_scale"] = [arm_scale.x,arm_scale.y,arm_scale.z]
	report["impact_hand_scale"] = [fist_scale.x,fist_scale.y,fist_scale.z]
	await pose("Jab",19.0/30)
	assert(skeleton.get_bone_pose_scale(bone("forearm.R")).distance_to(Vector3.ONE) < .003)
	var max_drift := 0.0
	for clip in ["Jab","Cross","Kick"]:
		await pose(clip,0)
		var left := skeleton.get_bone_global_pose(bone("foot.L")).origin
		var right := skeleton.get_bone_global_pose(bone("foot.R")).origin
		for time in [.10,.20,.30]:
			await pose(clip,time)
			max_drift = maxf(max_drift,left.distance_to(skeleton.get_bone_global_pose(bone("foot.L")).origin))
			if clip != "Kick":
				max_drift = maxf(max_drift,right.distance_to(skeleton.get_bone_global_pose(bone("foot.R")).origin))
	print("PAM_USER_FOOT_DRIFT ",max_drift)
	assert(max_drift < .004)
	report["sampled_support_foot_max_drift"] = max_drift
	var previous := 0.0
	var total := 0.0
	for i in range(43):
		await pose("Spin",i/30.0)
		var forward := skeleton.get_bone_global_pose(bone("root")).basis*Vector3.FORWARD
		var angle := atan2(forward.x,forward.z)
		if i > 0:
			total += wrapf(angle-previous,-PI,PI)
		previous = angle
	assert(absf(rad_to_deg(total)) > 700 and absf(rad_to_deg(total)) < 740)
	report["spin_degrees"] = rad_to_deg(total)
	validated = true
	print("PAM_USER_MODEL_CHECKS_OK ",JSON.stringify(report))

func record(clip: String, count: int, prefix: String) -> bool:
	for i in range(count):
		await pose(clip,i/30.0)
		for index in range(skeleton.get_bone_count()):
			if not skeleton.get_bone_global_pose(index).origin.is_finite():
				push_error("Non-finite pose in "+clip)
				return false
		await RenderingServer.frame_post_draw
		if viewport.get_texture().get_image().save_png(OUTPUT+"%s_%03d.png" % [prefix,i]) != OK:
			return false
		captures += 1
	return true

func review() -> void:
	DirAccess.make_dir_recursive_absolute(OUTPUT)
	if FileAccess.file_exists(OUTPUT+"godot_user_report.json"):
		DirAccess.remove_absolute(OUTPUT+"godot_user_report.json")
	viewport = SubViewport.new()
	viewport.size = Vector2i(640,480)
	viewport.own_world_3d = true
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	viewport.msaa_3d = Viewport.MSAA_2X
	root.add_child(viewport)
	var world := Node3D.new()
	viewport.add_child(world)
	var background := WorldEnvironment.new()
	background.environment = Environment.new()
	background.environment.background_mode = Environment.BG_COLOR
	background.environment.background_color = Color("526861")
	background.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	background.environment.ambient_light_color = Color(.84,.90,1)
	background.environment.ambient_light_energy = .65
	background.environment.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	world.add_child(background)
	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-35,-30,0)
	key.light_energy = 1.05
	world.add_child(key)
	var fill := DirectionalLight3D.new()
	fill.rotation_degrees = Vector3(-20,150,0)
	fill.light_energy = .38
	fill.light_color = Color(.88,.94,1)
	world.add_child(fill)
	model = load("res://assets/models/pam_usuario_rig.glb").instantiate()
	world.add_child(model)
	discover(model)
	await validate()
	if not validated:
		push_error("User model validation failed")
		quit(2)
		return
	var camera := Camera3D.new()
	world.add_child(camera)
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.size = 2.1
	camera.position = Vector3(3.5,1.6,5)
	camera.look_at(Vector3(0,.77,0))
	camera.current = true
	for item in [["Combo",67,"combo"],["Spin",43,"spin"],["Guard",19,"guard"]]:
		if not await record(item[0],item[1],item[2]):
			quit(2)
			return
	camera.position = Vector3(6,1.55,1.5)
	camera.look_at(Vector3(0,.77,0))
	for item in [["KneeFlex",61,"knees"],["Run",25,"run"],["ElbowFlex",49,"elbows"]]:
		if not await record(item[0],item[1],item[2]):
			quit(2)
			return
	report.merge({"engine":Engine.get_version_info().string,"bones":22,"triangles":49970,
		"clips":player.get_animation_list(),"captures":captures,"resolution":[640,480],"albedo":[4096,4096]},true)
	var file := FileAccess.open(OUTPUT+"godot_user_report.json",FileAccess.WRITE)
	file.store_string(JSON.stringify(report,"\t"))
	file.close()
	print("PAM_USER_MODEL_GODOT_OK ",JSON.stringify(report))
	viewport.queue_free()
	await process_frame
	quit()
