extends SceneTree
## Validate and capture actual cartoon clips from the exported GLB, Godot 4.4.1.
const OUTPUT := "/workspace/deliverables/pam_cartoon/"
var viewport: SubViewport
var model: Node3D
var skeleton: Skeleton3D
var player: AnimationPlayer
var body: MeshInstance3D
var camera: Camera3D
var captures := 0
var report: Dictionary = {}
var validated := false

func _initialize() -> void:
	create_timer(100).timeout.connect(func(): push_error("Cartoon review timed out"); quit(2))
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

func shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	assert(viewport.get_texture().get_image().save_png(OUTPUT+name+".png") == OK)
	captures += 1

func record(clip: String, frames: int, prefix: String) -> void:
	for i in range(frames):
		await pose(clip, float(i)/30.0)
		for index in range(skeleton.get_bone_count()):
			assert(skeleton.get_bone_global_pose(index).origin.is_finite())
		await shot("%s_%03d" % [prefix, i])

func validate() -> void:
	assert(skeleton != null and skeleton.get_bone_count() == 22)
	assert(body.skin != null)
	assert(body.get_node(body.skeleton) == skeleton)
	assert(body.mesh.get_blend_shape_count() == 1)
	assert(body.find_blend_shape_by_name("Blink") == 0)
	var material := body.mesh.surface_get_material(0) as StandardMaterial3D
	assert(material.shading_mode == BaseMaterial3D.SHADING_MODE_UNSHADED)
	assert(material.vertex_color_use_as_albedo)
	assert(material.albedo_texture.get_size() == Vector2(128, 128))
	for clip in ["Guard", "Jab", "Cross", "Kick", "Combo", "Spin", "Run", "ElbowFlex", "KneeFlex"]:
		assert(player.has_animation(clip), "Missing clip "+clip)
	var knee_angles := {}
	for side in ["R", "L"]:
		var thigh := bone("thigh."+side)
		var shin := bone("shin."+side)
		var foot := bone("foot."+side)
		assert(skeleton.get_bone_parent(shin) == thigh)
		assert(skeleton.get_bone_parent(foot) == shin)
		assert(skeleton.get_bone_parent(bone("toe."+side)) == foot)
		await pose("KneeFlex", 0)
		var fixed := skeleton.get_bone_global_pose(thigh)
		var before := skeleton.get_bone_pose_rotation(shin)
		var ankle := skeleton.get_bone_global_pose(foot).origin
		await pose("KneeFlex", .4 if side == "R" else 1.4)
		var angle := rad_to_deg(before.angle_to(skeleton.get_bone_pose_rotation(shin)))
		assert(absf(angle-90) < 1, "Knee must bend to 90 degrees")
		assert(fixed.is_equal_approx(skeleton.get_bone_global_pose(thigh)), "Isolated knee must keep thigh still")
		assert(ankle.distance_to(skeleton.get_bone_global_pose(foot).origin) > .15)
		knee_angles[side] = angle
	report["knees_degrees"] = knee_angles
	await pose("Jab", .2)
	var forearm_scale := skeleton.get_bone_pose_scale(bone("forearm.R"))
	var fist_scale := skeleton.get_bone_pose_scale(bone("hand.R"))
	print("PAM_CARTOON_STRETCH forearm=", forearm_scale, " fist=", fist_scale)
	assert(forearm_scale.y > 1.07 and forearm_scale.y < 1.13)
	assert(fist_scale.x > 1.07 and fist_scale.x < 1.20)
	report["impact_forearm_scale"] = [forearm_scale.x, forearm_scale.y, forearm_scale.z]
	report["impact_fist_scale"] = [fist_scale.x, fist_scale.y, fist_scale.z]
	await pose("Jab", 19.0/30)
	assert(skeleton.get_bone_pose_scale(bone("forearm.R")).is_equal_approx(Vector3.ONE))
	assert(skeleton.get_bone_pose_scale(bone("hand.R")).is_equal_approx(Vector3.ONE))
	var max_drift := 0.0
	for clip in ["Jab", "Cross", "Kick"]:
		await pose(clip, 0)
		var left := skeleton.get_bone_global_pose(bone("foot.L")).origin
		var right := skeleton.get_bone_global_pose(bone("foot.R")).origin
		for time in [.10, .20, .30]:
			await pose(clip, time)
			print("PAM_FOOT_DRIFT ", clip, " ", time, " L=", left.distance_to(skeleton.get_bone_global_pose(bone("foot.L")).origin), " R=", right.distance_to(skeleton.get_bone_global_pose(bone("foot.R")).origin))
			max_drift = maxf(max_drift, left.distance_to(skeleton.get_bone_global_pose(bone("foot.L")).origin))
			if clip != "Kick":
				max_drift = maxf(max_drift, right.distance_to(skeleton.get_bone_global_pose(bone("foot.R")).origin))
	assert(max_drift < .004, "Fight support feet must remain planted")
	report["support_foot_max_drift"] = max_drift
	var previous := 0.0
	var rotation_sum := 0.0
	for i in range(43):
		await pose("Spin", i/30.0)
		var forward := skeleton.get_bone_global_pose(bone("root")).basis*Vector3.FORWARD
		var angle := atan2(forward.x, forward.z)
		if i > 0:
			rotation_sum += wrapf(angle-previous, -PI, PI)
		previous = angle
	assert(absf(rad_to_deg(rotation_sum)) > 700 and absf(rad_to_deg(rotation_sum)) < 740)
	report["spin_degrees"] = rad_to_deg(rotation_sum)
	await pose("Guard", 1.24)
	assert(body.get_blend_shape_value(0) > .5)
	await pose("Guard", 1.5)
	assert(body.get_blend_shape_value(0) < .01)
	report["blink_exported_and_played"] = true
	validated = true
	print("PAM_CARTOON_CHECKS_OK ", JSON.stringify(report))

func review() -> void:
	DirAccess.make_dir_recursive_absolute(OUTPUT)
	if FileAccess.file_exists(OUTPUT+"godot_cartoon_report.json"):
		DirAccess.remove_absolute(OUTPUT+"godot_cartoon_report.json")
	viewport = SubViewport.new()
	viewport.size = Vector2i(640, 480)
	viewport.own_world_3d = true
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	viewport.msaa_3d = Viewport.MSAA_DISABLED
	root.add_child(viewport)
	var world := Node3D.new()
	viewport.add_child(world)
	var background := WorldEnvironment.new()
	background.environment = Environment.new()
	background.environment.background_mode = Environment.BG_COLOR
	background.environment.background_color = Color("526861")
	background.environment.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	world.add_child(background)
	model = load("res://assets/models/pam_ps1_cartoon.glb").instantiate()
	world.add_child(model)
	discover(model)
	await validate()
	if not validated:
		push_error("Cartoon validation failed; no successful capture report generated")
		quit(2)
		return
	camera = Camera3D.new()
	world.add_child(camera)
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.size = 2.12
	camera.position = Vector3(3.6, 1.6, 5.0)
	camera.look_at(Vector3(0, .76, .025))
	camera.current = true
	await record("Combo", 67, "combo")
	await record("Spin", 43, "spin")
	await record("Guard", 49, "guard")
	camera.position = Vector3(6.0, 1.55, 1.45)
	camera.look_at(Vector3(0, .76, .025))
	await record("KneeFlex", 61, "knees")
	await record("Run", 25, "run")
	report.merge({"engine": Engine.get_version_info().string, "bones": skeleton.get_bone_count(),
		"clips": player.get_animation_list(), "captures": captures, "resolution": [640,480]}, true)
	var file := FileAccess.open(OUTPUT+"godot_cartoon_report.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "\t"))
	file.close()
	print("PAM_CARTOON_GODOT_OK ", JSON.stringify(report))
	viewport.queue_free()
	await process_frame
	quit()
