extends SceneTree
## Staged captures triggered by real controller damage, jump and death paths.
var output := OS.get_environment("PAM_MOTION_OUTPUT")
var game: Node3D

func _initialize() -> void:
	create_timer(180).timeout.connect(func(): push_error("Motion game capture timeout"); quit(2))
	call_deferred("capture")

func ticks(count: int) -> void:
	for index in range(count): await physics_frame

func shot(name: String) -> bool:
	RenderingServer.render_loop_enabled = true
	await process_frame
	await RenderingServer.frame_post_draw
	var result := root.get_texture().get_image().save_png(output+name+".png") == OK
	RenderingServer.render_loop_enabled = false
	return result

func capture() -> void:
	if output.is_empty(): output = ProjectSettings.globalize_path("res://build/motion_review/")
	output = output.trim_suffix("/")+"/"
	DirAccess.make_dir_recursive_absolute(output)
	game = load("res://scenes/trail.tscn").instantiate()
	root.add_child(game)
	game.start_trail()
	game.set_process(false)
	game.hud.root.visible = false
	for enemy in game.enemy_root.get_children(): enemy.enabled = false; enemy.visible = false
	var p: PamPlayer = game.player
	p.reset_at(Vector3(0,.15,-9))
	p.input_override = true
	p.controllable = true
	game.camera.cinematic = true
	game.camera.fixed_position = Vector3(3.1,2.1,-5)
	game.camera.fixed_target = Vector3(0,.85,-9.5)
	game.camera.initialized = false
	# Advance physics without drawing hundreds of frames on a software renderer.
	RenderingServer.render_loop_enabled = false
	await ticks(45)
	p.buffered_jump = .12
	await ticks(18)
	assert(p.rig.current_clip == "Rise")
	if not await shot("movimento-pulo-na-fase"): quit(2); return
	print("MOTION_GAME_JUMP_CAPTURED")
	await ticks(120)
	p.invulnerable = 0
	p.receive_hit(1,Vector3.ZERO,"enemy")
	await ticks(10)
	assert(p.rig.current_clip == "Hit")
	if not await shot("movimento-dano-na-fase"): quit(2); return
	print("MOTION_GAME_HIT_CAPTURED")
	await ticks(100)
	var enemy: PamEnemy = game.spawn_enemy(Vector3(-1.1,.1,-10.8))
	enemy.health = 1
	enemy.receive_hit(3,Vector3.ZERO,"strong")
	await ticks(72)
	p.invulnerable = 0
	p.receive_hit(p.health,Vector3.ZERO,"enemy")
	await ticks(85)
	assert(p.respawning and p.rig.visible and p.rig.current_clip == "Death")
	assert(is_instance_valid(enemy) and enemy.rig.current_clip == "DeathBack")
	if not await shot("movimento-mortes-na-fase"): quit(2); return
	for child in game.get_children():
		if child is AudioStreamPlayer: child.stop()
	game.queue_free()
	await process_frame
	PamArt.library.clear(); PamArt.mats.clear()
	print("MOTION_GAME_CAPTURES_OK")
	quit()
