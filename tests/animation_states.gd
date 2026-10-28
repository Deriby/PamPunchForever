extends SceneTree
## Real physical events must select and finish the corresponding skin clips.
var world: Node3D
var p: PamPlayer
var checks := 0
var failures := 0

func _initialize() -> void:
	create_timer(90).timeout.connect(func(): push_error("Animation state timeout"); quit(2))
	call_deferred("run")

func check(ok: bool, message: String) -> void:
	checks += 1
	if not ok: failures += 1
	print(("PASS " if ok else "FAIL ")+message)

func ticks(count: int) -> void:
	for index in range(count): await physics_frame

func enemy_at(position: Vector3) -> PamEnemy:
	var enemy := PamEnemy.new()
	enemy.player = p
	enemy.position = position
	world.add_child(enemy)
	return enemy

func run() -> void:
	world = Node3D.new()
	root.add_child(world)
	PamArt.solid(world,Vector3(0,-.2,0),Vector3(30,.4,30),Color.GRAY)
	p = PamPlayer.new()
	world.add_child(p)
	p.reset_at(Vector3(0,.05,0))
	p.controllable = true
	p.input_override = true
	await ticks(40)
	check(p.rig.current_clip == "Guard","grounded resting player samples the breathing guard")
	p.buffered_jump = .12
	await ticks(8)
	check(p.rig.current_clip == "Rise" and p.velocity.y > 0,"real jump selects rising animation")
	var fell := false
	var landed := false
	for index in range(150):
		await physics_frame
		fell = fell or (p.rig.current_clip == "Fall" and p.velocity.y < 0)
		landed = landed or (p.rig.current_clip == "Land" and p.is_on_floor())
	check(fell,"jump apex switches to falling animation")
	check(landed,"collision landing plays compression and recovery")
	check(p.rig.current_clip == "Guard","landing returns to breathing guard")
	p.invulnerable = 0
	p.receive_hit(1,Vector3(1,0,0))
	await ticks(6)
	check(p.rig.current_clip == "Hit" and p.rig.visible,"damage recoils visibly before invulnerability blinking")
	await ticks(75)
	p.invulnerable = 0
	p.receive_hit(2,Vector3.ZERO,"explosion")
	await ticks(6)
	check(p.rig.current_clip == "HitHeavy","heavy damage selects the stronger full-body recoil")
	await ticks(100)
	p.health = 1
	p.invulnerable = 0
	p.press_action(); p.press_action()
	p.receive_hit(1,Vector3(2,0,0))
	await ticks(12)
	check(p.respawning and p.rig.visible and p.rig.current_clip == "Death","fatal damage plays a visible death instead of hiding Pam")
	p.press_action()
	check(p.attack.is_empty() and not p.combo_queue,"death prevents attacks and clears queued combo inputs")
	await ticks(150)
	var root_bone := p.rig.skeleton.find_bone("root")
	var rotation := p.rig.skeleton.get_bone_pose_rotation(root_bone).get_angle()
	check(rotation > 1 and p.rig.visible,"death reaches and holds a fallen skeletal pose")
	p.reset_at(Vector3.ZERO)
	p.controllable = true
	await ticks(40)
	check(not p.respawning and p.rig.current_clip == "Guard" and p.rig.rotation.z == 0,"respawn clears the death pose and returns control")
	var normal := enemy_at(Vector3(9,.05,0))
	await ticks(10)
	normal.receive_hit(1,Vector3.ZERO,"medium")
	await ticks(6)
	check(normal.rig.current_clip == "Hit","ordinary enemy visibly reacts to a medium strike")
	normal.health = 1
	normal.receive_hit(1,Vector3.ZERO,"spin")
	await ticks(130)
	check(is_instance_valid(normal) and normal.dead and normal.rig.current_clip == "Defeat","enemy completes the normal collapse before removal")
	check(not normal.receive_hit(1,Vector3.ZERO,"spin"),"defeated enemy cannot receive another damaging hit")
	await ticks(140)
	check(not is_instance_valid(normal),"completed enemy defeat settles before corpse removal")
	var strong := enemy_at(Vector3(-9,.05,0))
	await ticks(10)
	strong.receive_hit(1,Vector3.ZERO,"strong")
	await ticks(6)
	check(strong.rig.current_clip == "HitHeavy","strong enemy hit uses a distinct recoil")
	strong.health = 1
	strong.receive_hit(3,Vector3(4,0,0),"strong")
	await ticks(10)
	check(strong.dead and strong.rig.current_clip == "DeathBack","strong finisher selects backward defeat with physical knockback")
	p.global_position.y = -8
	await ticks(2)
	check(p.respawning and p.rig.current_clip == "DeathFall","void death uses the falling defeat animation")
	print("ANIMATION_STATES_RESULT %d/%d passed" % [checks-failures,checks])
	world.queue_free()
	await ticks(3)
	PamArt.library.clear(); PamArt.mats.clear()
	quit(0 if failures == 0 else 1)
