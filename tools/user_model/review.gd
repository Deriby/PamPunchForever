extends SceneTree
## Validate the actual user mesh, tail repair and retargeted clips in Godot 4.4.1.
const OUTPUT := "/workspace/deliverables/pam_cartoon_v3/"
const Stage = preload("res://tools/user_model/combat_stage.gd")
var stage
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
	stage.sample(clip,time)
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
	var protected := 0
	for i in range(arrays[Mesh.ARRAY_VERTEX].size()):
		var point: Vector3 = arrays[Mesh.ARRAY_VERTEX][i]
		if absf(point.x) < .455*1.538545716 or point.y <= .43*1.538545716 or point.y >= .66*1.538545716:
			continue
		var expected := "hand.L" if point.x < 0 else "hand.R"
		for slot in range(4):
			var weight: float = arrays[Mesh.ARRAY_WEIGHTS][i*4+slot]
			if weight <= .00001:
				continue
			var bind: int = arrays[Mesh.ARRAY_BONES][i*4+slot]
			var named := String(body.skin.get_bind_name(bind))
			assert(named == expected if not named.is_empty() else body.skin.get_bind_bone(bind) == bone(expected),"Hand/thumb must not follow forearm")
			assert(absf(weight-1) < .00001)
		protected += 1
	assert(protected > 1000)
	report["rigid_hand_vertices_in_imported_mesh"] = protected
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
	var fore_length := skeleton.get_bone_global_pose(bone("forearm.R")).origin.distance_to(skeleton.get_bone_global_pose(bone("hand.R")).origin)
	var rest_length := skeleton.get_bone_global_rest(bone("forearm.R")).origin.distance_to(skeleton.get_bone_global_rest(bone("hand.R")).origin)
	assert(fore_length/rest_length > 1.23 and fore_length/rest_length < 1.27)
	report["impact_forearm_length_ratio"] = fore_length/rest_length
	report["jab_tip_forward"] = stage.effects.tip(skeleton,"hand.R").z
	assert(report["jab_tip_forward"] > .60)
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
	# Every striking limb must return to the same guard scale, including after
	# an interrupted spin. Also check fractional samples, not just baked keys.
	await pose("Guard",0)
	var resting_scales := {}
	for name in ["upper_arm.R","upper_arm.L","forearm.R","forearm.L","hand.R","hand.L","shin.R","foot.R"]:
		resting_scales[name] = skeleton.get_bone_global_pose(bone(name)).basis.get_scale()
	var recovery_error := 0.0
	var max_hand_skew := 0.0
	var max_hand_scale_spread := 1.0
	for clip in ["Jab","Cross","Kick","Combo","Spin"]:
		await pose(clip,player.get_animation(clip).length)
		for name: String in resting_scales:
			recovery_error = maxf(recovery_error,resting_scales[name].distance_to(skeleton.get_bone_global_pose(bone(name)).basis.get_scale()))
		for i in range(12):
			await pose(clip,(i+.37)*player.get_animation(clip).length/12.0)
			for index in range(skeleton.get_bone_count()):
				var transform := skeleton.get_bone_global_pose(index)
				assert(transform.origin.is_finite() and transform.basis.is_finite())
			for side in ["L","R"]:
				var hand := bone("hand."+side)
				var basis := (skeleton.get_bone_global_pose(hand)*skeleton.get_bone_global_rest(hand).affine_inverse()).basis
				var size := basis.get_scale()
				max_hand_scale_spread = maxf(max_hand_scale_spread,maxf(size.x,maxf(size.y,size.z))/minf(size.x,minf(size.y,size.z)))
				max_hand_skew = maxf(max_hand_skew,maxf(absf(basis.x.normalized().dot(basis.y.normalized())),maxf(absf(basis.x.normalized().dot(basis.z.normalized())),absf(basis.y.normalized().dot(basis.z.normalized())))))
	assert(recovery_error < .005,"Temporary scale must return to guard")
	assert(max_hand_skew < .04 and max_hand_scale_spread < 1.04,"Fingers must keep their shape through stretch")
	report["maximum_sampled_hand_skew"] = max_hand_skew
	report["maximum_sampled_hand_scale_spread"] = max_hand_scale_spread
	await pose("Spin",.5)
	await pose("Guard",0)
	for name: String in resting_scales:
		assert(resting_scales[name].distance_to(skeleton.get_bone_global_pose(bone(name)).basis.get_scale()) < .005)
	report["all_striking_limb_recovery_max_error"] = recovery_error
	var active_frames := 0
	var burst_frames := 0
	for i in range(22):
		await pose("Jab",i/30.0)
		if stage.effects.stroke_count > 0:
			active_frames += 1
		if stage.effects.accent_count > 0:
			burst_frames += 1
	assert(active_frames >= 5 and burst_frames >= 3)
	assert(stage.effects.stroke_count == 0 and stage.effects.accent_count == 0)
	await pose("Spin",.5)
	await pose("Guard",0)
	assert(stage.effects.stroke_count == 0 and stage.effects.accent_count == 0)
	report["jab_trail_frames"] = active_frames
	report["jab_accent_frames"] = burst_frames
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
	stage = Stage.new()
	stage.autoplay = false
	stage.show_controls = false
	viewport.add_child(stage)
	skeleton = stage.skeleton
	player = stage.player
	body = stage.body
	await validate()
	if not validated:
		push_error("User model validation failed")
		quit(2)
		return
	var camera: Camera3D = stage.camera
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
	for item in [["Guard",0.0,"hand_guard"],["Jab",.2,"hand_impact"]]:
		await pose(item[0],item[1])
		stage.effects.visible = false
		var transform := skeleton.global_transform*skeleton.get_bone_global_pose(bone("hand.R"))
		var rest := skeleton.get_bone_global_rest(bone("hand.R"))
		var center := transform*(rest.basis.inverse()*Vector3(.075,0,0))
		camera.size = .60
		camera.position = center+Vector3(.65,.48,.8)
		camera.look_at(center)
		await RenderingServer.frame_post_draw
		assert(viewport.get_texture().get_image().save_png(OUTPUT+item[2]+".png") == OK)
		captures += 1
	report.merge({"engine":Engine.get_version_info().string,"bones":22,"triangles":49970,
		"clips":player.get_animation_list(),"captures":captures,"resolution":[640,480],"albedo":[4096,4096]},true)
	var file := FileAccess.open(OUTPUT+"godot_user_report.json",FileAccess.WRITE)
	file.store_string(JSON.stringify(report,"\t"))
	file.close()
	print("PAM_USER_MODEL_GODOT_OK ",JSON.stringify(report))
	viewport.queue_free()
	await process_frame
	quit()
