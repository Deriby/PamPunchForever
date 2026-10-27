extends SceneTree
# Rendered review views, with staged positions for art inspection (not gameplay tests).
func _initialize() -> void:
 create_timer(90).timeout.connect(func(): print("FAIL capture watchdog"); quit(2))
 call_deferred("capture")
func shot(name: String) -> void:
 await RenderingServer.frame_post_draw
 root.get_texture().get_image().save_png("/tmp/pam_%s.png" % name)
func capture() -> void:
 var scene = load("res://scenes/trail.tscn").instantiate()
 root.add_child(scene)
 await create_timer(1).timeout
 await shot("title")
 scene.begin_intro()
 scene.mode_clock=12
 await create_timer(.2).timeout
 await shot("prologue")
 scene.start_trail()
 scene.camera.initialized=false
 await create_timer(1).timeout
 await shot("game")
 scene.player.position=Vector3(scene.center(-47),.5,-46)
 scene.player.velocity=Vector3.ZERO
 scene.camera.initialized=false
 scene.hud.toast_time=0
 await create_timer(.5).timeout
 await shot("checkpoint")
 print("RENDER CHECK: FPS ",Engine.get_frames_per_second()," draw calls ",Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME))
 scene.queue_free()
 await process_frame
 OS.delay_msec(100)
 PamArt.library.clear();PamArt.mats.clear()
 quit()
