extends SceneTree
## Real GLB skin/animation review, rendered in Godot 4.4.1.
const OUTPUT := "/workspace/deliverables/pam_ps1_rig/"
var viewport: SubViewport
var model: Node3D
var skeleton: Skeleton3D
var player: AnimationPlayer

func _initialize() -> void:
	create_timer(90).timeout.connect(func(): push_error("Rig review timed out"); quit(2))
	call_deferred("review")

func discover(node: Node) -> void:
	if node is Skeleton3D:
		skeleton = node
	if node is AnimationPlayer:
		player = node
	for child in node.get_children():
		discover(child)

func pose(clip: String, time: float) -> void:
	player.play(clip)
	player.seek(time, true)
	player.pause()
	await process_frame

func shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	assert(viewport.get_texture().get_image().save_png(OUTPUT+name+".png") == OK)

func review() -> void:
	DirAccess.make_dir_recursive_absolute(OUTPUT)
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
	model = load("res://assets/models/pam_ps1_rig.glb").instantiate()
	world.add_child(model)
	discover(model)
	assert(skeleton != null and skeleton.get_bone_count() == 22)
	assert(player != null)
	for clip in ["Guard", "Jab", "Cross", "ElbowFlex", "Run"]:
		assert(player.has_animation(clip), "Missing exported animation "+clip)
	var meshes := model.find_children("*", "MeshInstance3D", true, false)
	assert(meshes.size() == 1, "Expected one skinned body mesh")
	var body := meshes[0] as MeshInstance3D
	assert(body.skin != null)
	assert(body.get_node(body.skeleton) == skeleton)
	var arrays := body.mesh.surface_get_arrays(0)
	assert(not arrays[Mesh.ARRAY_BONES].is_empty())
	assert(not arrays[Mesh.ARRAY_WEIGHTS].is_empty())
	var material := body.mesh.surface_get_material(0) as StandardMaterial3D
	assert(material.shading_mode == BaseMaterial3D.SHADING_MODE_UNSHADED)
	assert(material.vertex_color_use_as_albedo)
	assert(material.albedo_texture.get_size() == Vector2(128, 128))
	var upper := skeleton.find_bone("upper_arm.R")
	var forearm := skeleton.find_bone("forearm.R")
	var hand := skeleton.find_bone("hand.R")
	assert(upper >= 0 and forearm >= 0 and hand >= 0)
	assert(skeleton.get_bone_parent(hand) == forearm)
	assert(skeleton.get_bone_parent(forearm) == upper)
	await pose("ElbowFlex", 0)
	var upper_rest := skeleton.get_bone_global_pose(upper)
	var forearm_rest := skeleton.get_bone_pose_rotation(forearm)
	var hand_rest := skeleton.get_bone_global_pose(hand).origin
	await pose("ElbowFlex", .4)
	var travel := hand_rest.distance_to(skeleton.get_bone_global_pose(hand).origin)
	var flexion := rad_to_deg(forearm_rest.angle_to(skeleton.get_bone_pose_rotation(forearm)))
	print("PAM_ELBOW_MEASURE angle=", flexion, " travel=", travel, " length=", player.get_animation("ElbowFlex").length)
	assert(upper_rest.is_equal_approx(skeleton.get_bone_global_pose(upper)), "Shoulder must stay still")
	assert(travel > .20, "Hand must follow the independently bending elbow")
	assert(absf(flexion-90) < 1.0, "Expected a 90 degree elbow bend")
	var camera := Camera3D.new()
	world.add_child(camera)
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.size = 1.95
	camera.position = Vector3(3.5, 1.65, 5.0)
	camera.look_at(Vector3(0, .79, 0))
	camera.current = true
	await pose("Guard", 0)
	await shot("godot_guard")
	camera.position = Vector3(6.0, 1.55, 1.3)
	camera.look_at(Vector3(0, .79, 0))
	await pose("Jab", .2)
	await shot("godot_jab")
	await pose("Cross", .2)
	await shot("godot_cross")
	for i in range(32):
		await pose("Jab", .7*i/31.0)
		await shot("punch_%02d" % i)
	# Lateral view makes the hinge and continuous sleeve readable throughout flexion.
	camera.position = Vector3(6.0, 1.55, 1.3)
	camera.look_at(Vector3(0, .79, 0))
	for i in range(33):
		await pose("ElbowFlex", 1.6*i/32.0)
		await shot("flex_%02d" % i)
	var report := {"engine": Engine.get_version_info().string, "bones": skeleton.get_bone_count(),
		"skins": 1, "elbow_angle_degrees": flexion, "wrist_travel": travel,
		"stationary_upper_arm": true, "clips": player.get_animation_list(),
		"captures": 68, "resolution": [640, 480]}
	var file := FileAccess.open(OUTPUT+"godot_rig_report.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "\t"))
	file.close()
	print("PAM_RIG_GODOT_OK ", JSON.stringify(report))
	viewport.queue_free()
	await process_frame
	quit()
