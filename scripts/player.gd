class_name PamPlayer
extends CharacterBody3D

signal struck(target: Node3D, attack: String)
signal move_started(attack: String)
signal health_changed
signal died

const MOVES = preload("res://resources/combat_moves.tres")
const Animator = preload("res://scripts/pam_animator.gd")
var tuning: PamTuning = preload("res://resources/pam_tuning.tres")
var rig: PamAnimator
var facing := Vector3(0,0,-1)
var health := 5
var max_health := 5
var state := "IDLE"
var controllable := false
var attack := ""
var attack_clock := 0.0
var combo := 0
var combo_queue := false
var combo_grace := 0.0
var next_combo := 0
var queued_directions: Array[Vector3] = []
var hit_targets: Dictionary = {}
var attack_areas: Dictionary = {}
var last_tips: Dictionary = {}
var invulnerable := 0.0
var stun := 0.0
var coyote := 0.0
var buffered_jump := 0.0
var clock := 0.0
var respawning := false
var knocked_out := false
var jumps := 0
var landings := 0
var attack_hits := 0
var input_override := false
var test_motion := Vector2.ZERO
var trail: Node

func _ready() -> void:
	collision_layer = 2
	collision_mask = 1
	floor_snap_length = .22
	floor_max_angle = deg_to_rad(46)
	var shape := CollisionShape3D.new()
	var capsule := CapsuleShape3D.new()
	capsule.radius = .25
	capsule.height = 1.24
	shape.shape = capsule
	shape.position.y = .64
	add_child(shape)
	rig = Animator.new()
	add_child(rig)
	PamArt.hurtbox(self,Vector3(.55,1.1,.5),Vector3(0,.65,0))
	for name in ["hand.L","hand.R"]:
		var area := Area3D.new()
		area.name = "StrikeLeft" if name.ends_with("L") else "StrikeRight"
		area.collision_layer = 16
		area.collision_mask = 8
		add_child(area)
		var collision := CollisionShape3D.new()
		var sphere := SphereShape3D.new()
		sphere.radius = .17
		collision.shape = sphere
		area.add_child(collision)
		attack_areas[name] = area

func press_action(direction: Vector2 = Vector2.ZERO) -> void:
	if not controllable or stun > 0 or respawning or knocked_out:
		return
	var desired := Vector3(direction.x,0,direction.y).normalized() if direction.length() > .15 else facing
	if not attack.is_empty():
		# Early taps can queue the remaining strokes, never skip an animation or
		# spill into another cycle. The finisher keeps its full recovery.
		if queued_directions.size() < MOVES.order().size()-combo:
			queued_directions.append(desired)
		combo_queue = not queued_directions.is_empty()
		return
	facing = desired
	begin_move(next_combo if combo_grace > 0 else 0)

func begin_move(index: int, from_queue: bool = false) -> void:
	combo = index+1
	attack = MOVES.order()[index]
	attack_clock = 0
	if from_queue:
		facing = queued_directions.pop_front()
	else:
		queued_directions.clear()
	combo_queue = not queued_directions.is_empty()
	combo_grace = 0
	hit_targets.clear()
	last_tips.clear()
	rig.rotation.y = atan2(facing.x,facing.z)
	move_started.emit(attack)
	if trail:
		trail.sound("swing",.50 if attack == "strong" else .38)

func cancel_combo() -> void:
	attack = ""
	attack_clock = 0
	combo = 0
	combo_queue = false
	combo_grace = 0
	next_combo = 0
	queued_directions.clear()
	hit_targets.clear()
	last_tips.clear()
	if is_instance_valid(rig):
		rig.reset_motion()

func advance_combo(delta: float) -> void:
	if attack.is_empty():
		combo_grace = maxf(0,combo_grace-delta)
		if combo_grace <= 0:
			next_combo = 0
			combo = 0
		return
	attack_clock += delta
	var move := MOVES.move(attack)
	if combo_queue and attack_clock >= float(move["chain_at"]) and combo < MOVES.order().size():
		var remainder := attack_clock-float(move["chain_at"])
		begin_move(combo,true)
		attack_clock = remainder
	elif attack_clock >= float(move["duration"]):
		next_combo = combo if combo < MOVES.order().size() else 0
		combo_grace = float(MOVES.data["chain_grace"]) if next_combo > 0 else 0.0
		attack = ""
		combo_queue = false
		queued_directions.clear()
		last_tips.clear()
		if next_combo == 0:
			combo = 0

func _physics_process(delta: float) -> void:
	clock += delta
	invulnerable = maxf(0,invulnerable-delta)
	stun = maxf(0,stun-delta)
	var was_floor := is_on_floor()
	if was_floor:
		coyote = tuning.coyote_time
	else:
		coyote -= delta
	buffered_jump -= delta
	var movement := Vector2.ZERO
	if controllable and not respawning:
		movement = test_motion if input_override else Input.get_vector("move_left","move_right","move_forward","move_back")
		if not input_override:
			if Input.is_action_just_pressed("jump"):
				buffered_jump = tuning.jump_buffer
			if Input.is_action_just_released("jump") and velocity.y > tuning.jump_release_speed:
				velocity.y = tuning.jump_release_speed
			if Input.is_action_just_pressed("action"):
				press_action(movement)
	if buffered_jump > 0 and coyote > 0 and stun <= 0 and controllable and not respawning:
		velocity.y = tuning.jump_speed
		buffered_jump = 0
		coyote = 0
		jumps += 1
		if trail:
			trail.sound("jump",.3)
	if not was_floor:
		velocity.y = maxf(velocity.y-tuning.gravity*delta,-tuning.terminal_speed)
	advance_combo(delta)
	if stun <= 0:
		var target := Vector3(movement.x,0,movement.y)*tuning.top_speed
		if not attack.is_empty():
			target *= float(MOVES.data["movement_factor"])
			var move := MOVES.move(attack)
			if attack_clock >= float(move["windup"])*.6 and attack_clock <= float(move["active_end"]):
				target += facing*float(move["step_speed"])
		var accel := tuning.acceleration if was_floor else tuning.air_acceleration
		if movement.length() < .1 and was_floor:
			accel = tuning.braking
		velocity.x = move_toward(velocity.x,target.x,accel*delta)
		velocity.z = move_toward(velocity.z,target.z,accel*delta)
		if movement.length() > .1 and attack.is_empty():
			facing = Vector3(movement.x,0,movement.y).normalized()
	if not respawning:
		move_and_slide()
		if is_on_ceiling() and velocity.y > 0:
			velocity.y = 0
		if is_on_floor() and not was_floor:
			landings += 1
			if trail:
				trail.impact(global_position+Vector3.UP*.05,Color("bbaa77"),5,.6)
	rig.rotation.y = atan2(facing.x,facing.z) if not attack.is_empty() else lerp_angle(rig.rotation.y,atan2(facing.x,facing.z),1-exp(-18*delta))
	rig.position.y = -.12 if knocked_out else 0.0
	rig.rotation.z = 1.4 if knocked_out else (sin(stun*30)*.13 if stun > 0 else 0.0)
	rig.visible = not respawning and (invulnerable <= 0 or int(clock*22)%2 == 0)
	rig.sample_state(attack,attack_clock,delta,Vector2(velocity.x,velocity.z).length(),not is_on_floor())
	update_hitboxes()
	state = "DANO" if stun > 0 else (MOVES.move(attack)["label"] if not attack.is_empty() else ("AR" if not is_on_floor() else ("CORRIDA" if movement.length() > .1 else "IDLE")))
	if global_position.y < -7 and not respawning:
		die()

func update_hitboxes() -> void:
	var move := MOVES.move(attack) if not attack.is_empty() else {}
	var active := not move.is_empty() and attack_clock >= float(move["windup"]) and attack_clock <= float(move["active_end"])
	for name: String in attack_areas:
		var point := rig.fist_position(name)
		var area: Area3D = attack_areas[name]
		area.global_position = point
		if active and name in move["bones"]:
			var radius := float(move["radius"])
			(area.get_child(0).shape as SphereShape3D).radius = radius
			query_strike(last_tips.get(name,point),point,radius,move)
		last_tips[name] = point

func query_strike(before: Vector3, after: Vector3, radius: float, move: Dictionary) -> void:
	var query := PhysicsShapeQueryParameters3D.new()
	var distance := before.distance_to(after)
	if distance > .002:
		var capsule := CapsuleShape3D.new()
		capsule.radius = radius
		capsule.height = distance+radius*2
		query.shape = capsule
		query.transform = Transform3D(Basis(Quaternion(Vector3.UP,(after-before).normalized())),(before+after)*.5)
	else:
		var sphere := SphereShape3D.new()
		sphere.radius = radius
		query.shape = sphere
		query.transform.origin = after
	query.collision_mask = 8
	query.collide_with_bodies = false
	query.collide_with_areas = true
	for result in get_world_3d().direct_space_state.intersect_shape(query,32):
		var target := result["collider"].get_parent() as Node3D
		if target == self or not is_instance_valid(target) or hit_targets.has(target.get_instance_id()) or not target.has_method("receive_hit"):
			continue
		# A wall blocks the fist. A breakable's own world collider is its surface.
		var contact := target.global_position+Vector3.UP*.8
		for child in result["collider"].get_children():
			if child is CollisionShape3D:
				contact = child.global_position
				break
		# Check the hurtbox side of the sweep too: retracting a hand from beyond
		# a wall must not turn a previously blocked contact into damage.
		var ray := PhysicsRayQueryParameters3D.create(global_position+Vector3.UP*.82,contact,1)
		var obstacle := get_world_3d().direct_space_state.intersect_ray(ray)
		if not obstacle.is_empty() and obstacle["collider"] != target and obstacle["collider"].get_parent() != target:
			continue
		hit_targets[target.get_instance_id()] = true
		var direction := facing
		if attack == "spin":
			direction = (target.global_position-global_position)*Vector3(1,0,1)
			direction = direction.normalized() if direction.length() > .01 else facing
		if target.receive_hit(int(move["damage"]),direction*float(move["knockback"]),attack):
			attack_hits += 1
			struck.emit(target,attack)

func receive_hit(damage: int, knock: Vector3, _kind: String = "enemy") -> bool:
	if invulnerable > 0 or respawning or not controllable:
		return false
	health -= damage
	invulnerable = 1.25
	stun = .32
	velocity = knock+Vector3.UP*4.0
	cancel_combo()
	health_changed.emit()
	if trail:
		trail.impact(global_position+Vector3.UP*.7,Color("d85a46"),12,1)
		trail.freeze_frame(.055)
		trail.sound("hit",.65)
	if health <= 0:
		die()
	return true

func die() -> void:
	if respawning:
		return
	respawning = true
	controllable = false
	cancel_combo()
	died.emit()

func reset_at(point: Vector3) -> void:
	knocked_out = false
	global_position = point
	velocity = Vector3.ZERO
	health = max_health
	respawning = false
	invulnerable = 1.0
	stun = 0
	cancel_combo()
	health_changed.emit()
