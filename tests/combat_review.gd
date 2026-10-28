extends SceneTree
## Exercise the actual review scene, including interruption and input controls.
const Scene = preload("res://scenes/pam_combat_review.tscn")
var passed := false

func _initialize() -> void:
	call_deferred("check_scene")

func key(stage: Node, code: Key) -> void:
	var event := InputEventKey.new()
	event.pressed = true
	event.keycode = code
	stage._unhandled_key_input(event)

func check_scene() -> void:
	await exercise()
	if not passed:
		push_error("Combat review controls failed")
		quit(2)
		return
	print("PAM_COMBAT_REVIEW_CONTROLS_OK")
	quit()

func exercise() -> void:
	var stage := Scene.instantiate()
	root.add_child(stage)
	for i in range(15):
		await process_frame
	assert(stage.clock > 0 and stage.clip == "Combo")
	key(stage,KEY_SPACE)
	var stopped: float = stage.clock
	for i in range(5):
		await process_frame
	assert(stage.clock == stopped)
	key(stage,KEY_RIGHT)
	assert(absf(stage.clock-stopped-1.0/30) < .0001)
	key(stage,KEY_LEFT)
	assert(absf(stage.clock-stopped) < .0001)
	key(stage,KEY_2)
	assert(stage.clip == "Spin" and not stage.paused)
	stage.sample("Spin",.5)
	key(stage,KEY_0)
	assert(stage.paused)
	for index in range(stage.skeleton.get_bone_count()):
		assert(stage.skeleton.get_bone_pose(index).is_equal_approx(stage.skeleton.get_bone_rest(index)))
	assert(stage.effects.stroke_count == 0 and stage.effects.accent_count == 0)
	key(stage,KEY_1)
	assert(stage.clip == "Combo" and not stage.paused)
	key(stage,KEY_5)
	assert(stage.clip == "Jump")
	key(stage,KEY_V)
	assert(stage.camera.position.is_equal_approx(Vector3(6,1.55,1.5)))
	key(stage,KEY_V)
	assert(stage.camera.position.is_equal_approx(Vector3(5,1.6,4)))
	stage.queue_free()
	await process_frame
	passed = true
