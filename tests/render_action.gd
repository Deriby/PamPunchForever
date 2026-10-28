extends SceneTree
## Capture real input, controller, collisions and supplied skin inside Fase 1.
## Run via tools/render_review.sh --fixed-fps 30 for the input schedule below.
const OUTPUT := "/workspace/deliverables/pam_action/"
var viewport: SubViewport
var game: Node3D
var p: PamPlayer
var started: Array[String] = []
var captures := 0
var completed := false

func _initialize() -> void:
	create_timer(170).timeout.connect(func(): push_error("Action capture timed out"); quit(2))
	call_deferred("run")

func frame(prefix: String, index: int) -> bool:
	await process_frame
	await RenderingServer.frame_post_draw
	if viewport.get_texture().get_image().save_png(OUTPUT+"%s_%03d.png" % [prefix,index]) != OK:
		return false
	captures += 1
	return true

func run() -> void:
	await capture()
	if not completed:
		push_error("Action capture failed")
		quit(2)
		return
	game.queue_free()
	await process_frame
	PamArt.library.clear()
	PamArt.mats.clear()
	quit()

func capture() -> void:
	DirAccess.make_dir_recursive_absolute(OUTPUT)
	viewport = SubViewport.new()
	viewport.size = Vector2i(640,480)
	viewport.own_world_3d = true
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	viewport.msaa_3d = Viewport.MSAA_2X
	root.add_child(viewport)
	game = preload("res://scenes/trail.tscn").instantiate()
	viewport.add_child(game)
	game.start_trail()
	game.hud.root.visible = false
	for child in game.get_children():
		if child is AudioStreamPlayer:
			child.stop()
	p = game.player
	p.reset_at(Vector3(0,.03,-6))
	p.controllable = true
	p.invulnerable = 0
	p.facing = Vector3.BACK
	game.camera.cinematic = true
	game.camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	game.camera.size = 2.6
	game.camera.fixed_position = Vector3(3.5,3.2,-1)
	game.camera.fixed_target = Vector3(0,.77,-6)
	game.camera.initialized = false
	for i in range(12):
		await physics_frame
	if "--camera-check" in OS.get_cmdline_user_args():
		var positions := [Vector3(2,3.5,-1),Vector3(3.5,3.2,-1),Vector3(0,4,-1),Vector3(2,3,-3)]
		for i in range(positions.size()):
			game.camera.size = 2.6
			game.camera.fixed_position = positions[i]
			game.camera.initialized = false
			await frame("camera",i)
		completed = true
		return
	p.move_started.connect(func(kind: String): started.append(kind))
	for i in range(60):
		if i in [0,7,16]:
			Input.action_press("action")
		elif i in [1,8,17]:
			Input.action_release("action")
		if not await frame("action",i):
			return
	assert(started == ["spin","medium","strong"],"Three actual presses must produce the requested combo")
	var action_order := started.duplicate()
	p.reset_at(Vector3(0,.03,-6))
	p.controllable = true
	p.invulnerable = 0
	p.facing = Vector3.BACK
	game.camera.size = 4.25
	game.camera.fixed_position = Vector3(3.5,4,-1)
	game.camera.fixed_target = Vector3(0,1.45,-6)
	game.camera.initialized = false
	for i in range(10):
		await physics_frame
	var old_jumps := p.jumps
	started.clear()
	for i in range(60):
		if i == 0:
			Input.action_press("jump")
		elif i == 3:
			Input.action_press("action")
		elif i == 4:
			Input.action_release("action")
		elif i == 7:
			Input.action_release("jump")
		if not await frame("jump",i):
			return
	assert(p.jumps == old_jumps+1 and started == ["spin"])
	var report := {"engine":Engine.get_version_info().string,"scene":"scenes/trail.tscn",
		"actual_input":true,"action_presses":3,"action_order":action_order,
		"jump_presses":1,"jump_action_order":started,"captures":captures,"resolution":[640,480],
		"fixed_render_fps":30,"physics_ticks":Engine.physics_ticks_per_second,"staged_camera":true}
	var file := FileAccess.open(OUTPUT+"capture-report.json",FileAccess.WRITE)
	file.store_string(JSON.stringify(report,"\t"))
	file.close()
	print("PAM_SINGLE_ACTION_RENDER_OK ",JSON.stringify(report))
	completed = true
