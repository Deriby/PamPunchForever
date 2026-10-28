extends SceneTree
## Staged visual inspection of the actual game and the F6 rig-review scene.
## These frames demonstrate rendering/integration, not manual gameplay.
var output := OS.get_environment("PAM_NPC_REVIEW_OUTPUT")

func _initialize() -> void:
	create_timer(120).timeout.connect(func(): push_error("NPC cast capture timed out"); quit(2))
	call_deferred("capture")

func shot(name: String) -> bool:
	for index in range(3): await process_frame
	await RenderingServer.frame_post_draw
	return root.get_texture().get_image().save_png(output+name+".png") == OK

func capture() -> void:
	if output.is_empty(): output = ProjectSettings.globalize_path("res://build/npc_review/")
	output = output.trim_suffix("/")+"/"
	DirAccess.make_dir_recursive_absolute(output)
	var game: Node3D = load("res://scenes/trail.tscn").instantiate()
	root.add_child(game)
	game.begin_intro()
	game.mode_clock = 9.0
	game.update_intro()
	game.set_process(false)
	game.player.controllable = false
	game.master.pose("Guard",.2,false)
	game.camera.fixed_position = Vector3(3.4,2.1,1.4)
	game.camera.fixed_target = Vector3(-.2,1.05,-3)
	game.camera.initialized = false
	game.hud.root.visible = false
	if not await shot("npc-prologo"): quit(2); return
	game.start_trail()
	game.player.position = Vector3(0,.3,-32)
	game.player.controllable = false
	game.player.velocity = Vector3.ZERO
	game.hud.root.visible = false
	game.camera.cinematic = true
	game.camera.fixed_position = Vector3(3.6,2.2,-29)
	game.camera.fixed_target = Vector3(.3,1,-34)
	game.camera.initialized = false
	for enemy in game.enemy_root.get_children(): enemy.enabled = false; enemy.visible = false
	var ninja: PamEnemy = game.spawn_enemy(Vector3(.3,.27,-34))
	ninja.enabled = false
	ninja.rig.rotation.y = -.3
	ninja.rig.pose("Guard",.2,false)
	if not await shot("npc-trilha"): quit(2); return
	game.queue_free()
	await process_frame
	var stage: Node3D = load("res://scenes/npc_rig_review.tscn").instantiate()
	root.add_child(stage)
	stage.paused = true
	stage.clip = "KneeFlex"
	stage.clock = .4
	stage.bones.visible = true
	stage.sample()
	if not await shot("npc-ossos"): quit(2); return
	stage.queue_free()
	await process_frame
	PamArt.library.clear()
	PamArt.mats.clear()
	print("NPC_CAST_CAPTURE_OK")
	quit()
