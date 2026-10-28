extends SceneTree
## Physical regression tests of the real controller, skin and one-button input.
const Player = preload("res://scripts/player.gd")
var world: Node3D
var p: PamPlayer
var checks := 0
var failed := 0
var started: Array[String] = []
var targets: Array[Node3D] = []

class Target extends Node3D:
	var health := 50
	var hits: Array[String] = []
	var impulses: Array[float] = []
	func receive_hit(damage: int, knock: Vector3, kind: String) -> bool:
		health -= damage
		hits.append(kind)
		impulses.append(knock.length())
		return true

func _initialize() -> void:
	create_timer(100).timeout.connect(func(): push_error("Action combat watchdog"); quit(2))
	call_deferred("run")

func check(condition: bool, label: String) -> void:
	checks += 1
	failed += 0 if condition else 1
	print(("PASS " if condition else "FAIL ")+label)

func ticks(count: int) -> void:
	for i in range(count):
		await physics_frame

func tap() -> void:
	Input.action_press("action")
	await ticks(1)
	Input.action_release("action")
	await ticks(1)

func reset_player() -> void:
	Input.action_release("action")
	Input.action_release("jump")
	for target in targets:
		if is_instance_valid(target):
			target.queue_free()
	targets.clear()
	p.cancel_combo()
	p.reset_at(Vector3(0,.05,0))
	p.controllable = true
	p.input_override = false
	p.facing = Vector3.BACK
	await ticks(12)
	started.clear()

func target_at(point: Vector3, size: Vector3 = Vector3(.8,.35,.08)) -> Target:
	var target := Target.new()
	world.add_child(target)
	target.position = point
	PamArt.hurtbox(target,size,Vector3.ZERO)
	targets.append(target)
	return target

func until_attack(kind: String, limit: int = 200) -> void:
	for i in range(limit):
		if p.attack == kind:
			return
		await physics_frame

func run() -> void:
	world = Node3D.new()
	root.add_child(world)
	PamArt.solid(world,Vector3(0,-.25,0),Vector3(12,.5,12),Color.GRAY)
	p = Player.new()
	world.add_child(p)
	p.move_started.connect(func(kind: String): started.append(kind))
	await reset_player()
	check(p.rig.skeleton.get_bone_count() == 22 and p.rig.player.has_animation("Medium") and p.rig.player.has_animation("Strong"),"approved supplied rig is the active player")
	var action: Array[InputEvent] = InputMap.action_get_events("action")
	var jump: Array[InputEvent] = InputMap.action_get_events("jump")
	check(action[0].physical_keycode == KEY_J and action[1].button_index == JOY_BUTTON_X and jump[0].physical_keycode == KEY_SPACE and jump[1].button_index == JOY_BUTTON_A,"J/X action and Space/A jump")
	check(not InputMap.has_action("light") and not InputMap.has_action("heavy") and not InputMap.has_action("spin") and not InputMap.has_action("dodge"),"obsolete gameplay buttons removed")
	Input.action_press("action")
	await ticks(110)
	check(started == ["spin"] and p.attack.is_empty(),"holding action produces one spin, no automatic combo")
	Input.action_release("action")
	await reset_player()
	await tap()
	await tap()
	await tap()
	await until_attack("medium")
	check(started == ["spin","medium"],"rapid presses preserve the order without skipping the medium punch")
	await until_attack("strong")
	check(started == ["spin","medium","strong"],"three early taps queue the whole combo on the same button")
	await tap()
	await ticks(20)
	check(p.attack == "strong" and started.size() == 3,"finisher recovery cannot be bypassed by mashing")
	await ticks(100)
	await tap()
	check(p.attack == "spin","completed combo restarts at spin")
	await reset_player()
	await tap()
	await until_attack("")
	await ticks(6)
	await tap()
	check(p.attack == "medium","short gap between taps preserves the combo")
	await reset_player()
	await tap()
	await ticks(110)
	await tap()
	check(p.attack == "spin","expired combo grace restarts at spin")
	await reset_player()
	var close := target_at(Vector3(0,.88,.61))
	await ticks(3)
	await tap()
	await tap()
	await until_attack("medium")
	await tap()
	await until_attack("")
	check(close.hits == ["spin","medium","strong"] and close.health == 45,"each physical stroke damages a hurtbox once, including both spin hands")
	check(close.impulses.size() == 3 and close.impulses[2] > close.impulses[1],"finisher produces a stronger physical reaction")
	await reset_player()
	await tap()
	await tap()
	await until_attack("medium")
	var distant := target_at(Vector3(0,.88,.99))
	await ticks(26)
	check(distant.hits.is_empty(),"medium punch does not damage beyond its visible reach")
	await tap()
	await until_attack("strong")
	await until_attack("")
	check(distant.hits == ["strong"] and distant.health == 47,"long strong punch physically reaches the farther hurtbox")
	await reset_player()
	var far := target_at(Vector3(0,.88,1.9))
	var blocked := target_at(Vector3(0,.88,.88))
	var wall := PamArt.solid(world,Vector3(0,.8,.4),Vector3(3,1.6,.08),Color.GRAY)
	await ticks(3)
	await tap()
	await tap()
	await until_attack("medium")
	await tap()
	await until_attack("")
	check(blocked.hits.is_empty(),"solid wall blocks damage from extended fists")
	check(far.hits.is_empty(),"no damage outside actual swept fist volumes")
	wall.queue_free()
	await reset_player()
	await tap()
	await tap()
	p.invulnerable = 0
	p.receive_hit(1,Vector3.ZERO)
	await ticks(70)
	check(p.attack.is_empty() and not p.combo_queue and p.combo_grace == 0,"damage cancels queued stages and temporary stretch")
	await tap()
	check(p.attack == "spin","first action after damage starts a fresh combo")
	await reset_player()
	Input.action_press("jump")
	await ticks(3)
	Input.action_release("jump")
	await tap()
	check(not p.is_on_floor() and p.attack == "spin","same action and jump work together in the air")
	p.die()
	p.reset_at(Vector3(0,.05,0))
	p.controllable = true
	await tap()
	check(p.attack == "spin" and not p.combo_queue,"respawn clears combo progress and queued inputs")
	print("ACTION_COMBAT_RESULT %d/%d passed" % [checks-failed,checks])
	world.queue_free()
	await ticks(3)
	PamArt.library.clear()
	PamArt.mats.clear()
	quit(0 if failed == 0 else 1)
