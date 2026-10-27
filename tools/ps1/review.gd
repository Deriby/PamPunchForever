extends SceneTree
## Capture the actual exported study at a native 320 x 240 resolution.
const OUTPUT := "/workspace/deliverables/pam_ps1/"
var viewport: SubViewport
var model: Node3D

func _initialize() -> void:
	create_timer(60).timeout.connect(func(): push_error("PS1 review timed out"); quit(2))
	call_deferred("capture")

func inspect(node: Node) -> void:
	if node is MeshInstance3D:
		for surface in node.mesh.get_surface_count():
			var material = node.mesh.surface_get_material(surface)
			assert(material is StandardMaterial3D, "Expected the exported standard material")
			assert(material.shading_mode == BaseMaterial3D.SHADING_MODE_UNSHADED)
			assert(material.vertex_color_use_as_albedo)
			assert(material.albedo_texture.get_size() == Vector2(128, 128))
	for child in node.get_children():
		inspect(child)

func shot(label: String) -> void:
	await process_frame
	await RenderingServer.frame_post_draw
	var result := viewport.get_texture().get_image().save_png(OUTPUT + "native_" + label + ".png")
	assert(result == OK, "Could not save native render")
	print("PS1_NATIVE_CAPTURE ", label, " 320x240")

func capture() -> void:
	viewport = SubViewport.new()
	viewport.size = Vector2i(320, 240)
	viewport.own_world_3d = true
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	viewport.msaa_3d = Viewport.MSAA_DISABLED
	root.add_child(viewport)
	var world := Node3D.new()
	viewport.add_child(world)
	var environment := WorldEnvironment.new()
	environment.environment = Environment.new()
	environment.environment.background_mode = Environment.BG_COLOR
	environment.environment.background_color = Color("526861")
	environment.environment.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	world.add_child(environment)
	var floor_mesh := MeshInstance3D.new()
	floor_mesh.mesh = PlaneMesh.new()
	floor_mesh.mesh.size = Vector2(200, 200)
	var floor_material := StandardMaterial3D.new()
	floor_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	floor_material.albedo_color = Color("526861")
	floor_mesh.material_override = floor_material
	floor_mesh.position.y = -.015
	world.add_child(floor_mesh)
	model = load("res://assets/models/pam_ps1_estudo.glb").instantiate()
	world.add_child(model)
	inspect(model)
	for pivot in ["Head", "Torso", "ArmL", "ArmR", "LegL", "LegR"]:
		assert(model.find_child(pivot, true, false), "Missing pivot " + pivot)
	var camera := Camera3D.new()
	world.add_child(camera)
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.size = 1.9
	camera.position = Vector3(2.6, 1.62, 6.0)
	camera.look_at(Vector3(0, .77, 0))
	camera.current = true
	await shot("idle")
	model.find_child("ArmR", true, false).rotation.x = -.85
	model.find_child("ArmL", true, false).rotation.x = .85
	model.find_child("LegR", true, false).rotation.x = .7
	model.find_child("LegL", true, false).rotation.x = -.7
	model.find_child("Torso", true, false).rotation.x = .12
	await shot("run")
	model.find_child("ArmR", true, false).rotation.x = -1.48
	model.find_child("ArmL", true, false).rotation.x = -.6
	model.find_child("LegR", true, false).rotation = Vector3.ZERO
	model.find_child("LegL", true, false).rotation = Vector3.ZERO
	model.find_child("Torso", true, false).rotation = Vector3.ZERO
	await shot("punch")
	print("PS1_REVIEW_OK material, atlas, vertex colors, pivots and native captures")
	viewport.queue_free()
	await process_frame
	quit()
