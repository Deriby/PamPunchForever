extends SceneTree
# Staged art-review camera positions in the actual Godot scene, not gameplay tests.
var game: Node3D
func _initialize() -> void:
 create_timer(150).timeout.connect(func(): print("FAIL art review watchdog");quit(2))
 call_deferred("review")
func shot(name: String) -> void:
 await RenderingServer.frame_post_draw
 root.get_texture().get_image().save_png("/workspace/deliverables/style_pass/%s.png" % name)
func review() -> void:
 game=load("res://scenes/trail.tscn").instantiate()
 root.add_child(game)
 game.hud.root.visible=false
 game.begin_intro()
 game.mode_clock=5
 game.camera.fixed_position=Vector3(3.8,2.15,3.8)
 game.camera.fixed_target=Vector3(-.5,.95,-3.6)
 game.camera.initialized=false
 await create_timer(.7).timeout
 await shot("floresta_e_mestre")
 game.start_trail()
 game.player.controllable=false
 game.player.position=Vector3(game.center(-47),.5,-46)
 game.player.velocity=Vector3.ZERO
 game.camera.cinematic=false;game.camera.initialized=false
 game.hud.root.visible=false
 await create_timer(.7).timeout
 await shot("ruinas_e_travessia")
 game.player.visible=false
 game.camera.cinematic=true
 game.camera.fixed_position=Vector3(1.8,2.3,-44.5)
 game.camera.fixed_target=Vector3(1.1,1.0,-47)
 game.camera.initialized=false
 await create_timer(.4).timeout
 await shot("altar_detalhe")
 game.player.visible=true
 game.player.position=Vector3(0,.35,-31.8)
 game.camera.fixed_position=Vector3(4.0,2.5,-28.4)
 game.camera.fixed_target=Vector3(.8,1,-34.2)
 game.camera.initialized=false
 for old_enemy in game.enemy_root.get_children():
  if old_enemy is PamEnemy:
   old_enemy.visible=false;old_enemy.enabled=false
 var a: PamEnemy=game.spawn_enemy(Vector3(.3,.27,-34.0))
 var b: PamEnemy=game.spawn_enemy(Vector3(1.7,.27,-35.2))
 a.enabled=false;b.enabled=false
 await create_timer(.6).timeout
 await shot("guardioes_na_trilha")
 print("ART_REVIEW_COMPLETE fps=",Engine.get_frames_per_second()," draw_calls=",Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME))
 for child in game.get_children():
  if child is AudioStreamPlayer:child.stop()
 OS.delay_msec(100)
 game.queue_free()
 await process_frame
 PamArt.library.clear();PamArt.mats.clear()
 quit()
