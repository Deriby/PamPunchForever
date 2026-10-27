class_name PamPlayer
extends CharacterBody3D

signal struck(target: Node3D, attack: String)
signal health_changed
signal died

var tuning: PamTuning = preload("res://resources/pam_tuning.tres")
var rig: Node3D
var facing := Vector3(0,0,-1)
var health := 5
var max_health := 5
var state := "IDLE"
var controllable := false
var attack := ""
var attack_clock := 0.0
var combo := 0
var combo_queue := false
var hit_targets: Dictionary = {}
var attack_area: Area3D
var attack_shape: SphereShape3D
var invulnerable := 0.0
var stun := 0.0
var dodge_time := 0.0
var dodge_cooldown := 0.0
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
 floor_snap_length = 0.22
 floor_max_angle = deg_to_rad(46)
 var c := CollisionShape3D.new()
 var capsule := CapsuleShape3D.new()
 capsule.radius = .25
 capsule.height = 1.24
 c.shape = capsule
 c.position.y = .64
 add_child(c)
 rig = PamArt.model("pam")
 add_child(rig)
 PamArt.hurtbox(self,Vector3(.55,1.1,.5),Vector3(0,.65,0))
 attack_area = Area3D.new()
 attack_area.collision_layer = 16
 attack_area.collision_mask = 8
 add_child(attack_area)
 var cs := CollisionShape3D.new()
 attack_shape = SphereShape3D.new()
 attack_shape.radius = .67
 cs.shape = attack_shape
 attack_area.add_child(cs)

func start_attack(kind: String) -> void:
 if not controllable or stun > 0 or dodge_time > 0 or respawning: return
 if attack != "":
  if kind == "jab" and attack in ["jab","cross"]: combo_queue = true
  return
 attack = kind if is_on_floor() else "air"
 combo = 0
 attack_clock = 0
 combo_queue = false
 hit_targets.clear()
 attack_shape.radius = float(PamTuning.ATTACKS[attack][5])
 if trail: trail.sound("swing",.45)

func _physics_process(delta: float) -> void:
 clock += delta
 invulnerable = maxf(0,invulnerable-delta)
 stun = maxf(0,stun-delta)
 dodge_cooldown = maxf(0,dodge_cooldown-delta)
 var was_floor := is_on_floor()
 if was_floor: coyote = tuning.coyote_time
 else: coyote -= delta
 buffered_jump -= delta
 var movement := Vector2.ZERO
 if controllable and not respawning:
  movement = test_motion if input_override else Input.get_vector("move_left","move_right","move_forward","move_back")
  if not input_override:
   if Input.is_action_just_pressed("jump"): buffered_jump = tuning.jump_buffer
   if Input.is_action_just_released("jump") and velocity.y > tuning.jump_release_speed:
    velocity.y = tuning.jump_release_speed
   if Input.is_action_just_pressed("light"): start_attack("jab")
   if Input.is_action_just_pressed("heavy"): start_attack("heavy")
   if Input.is_action_just_pressed("spin"): start_attack("spin")
   if Input.is_action_just_pressed("dodge") and dodge_cooldown <= 0 and attack == "" and stun <= 0:
    dodge_time = .24
    dodge_cooldown = .65
    invulnerable = .28
    if movement.length() > .1: facing = Vector3(movement.x,0,movement.y).normalized()
    if trail: trail.sound("swing",.35)
 if buffered_jump > 0 and coyote > 0 and stun <= 0 and controllable and not respawning:
  velocity.y = tuning.jump_speed
  buffered_jump = 0
  coyote = 0
  jumps += 1
  if trail: trail.sound("jump",.3)
 if not was_floor: velocity.y = maxf(velocity.y-tuning.gravity*delta,-tuning.terminal_speed)
 if stun <= 0:
  var target := Vector3(movement.x,0,movement.y) * tuning.top_speed
  if attack != "": target *= .24
  var accel := tuning.acceleration if was_floor else tuning.air_acceleration
  if movement.length() < .1 and was_floor: accel = tuning.braking
  velocity.x = move_toward(velocity.x,target.x,accel*delta)
  velocity.z = move_toward(velocity.z,target.z,accel*delta)
  if movement.length() > .1 and attack == "": facing = Vector3(movement.x,0,movement.y).normalized()
 if dodge_time > 0:
  dodge_time -= delta
  velocity.x = facing.x*tuning.dodge_speed
  velocity.z = facing.z*tuning.dodge_speed
 attack_area.position = facing * (.67 if attack != "spin" else 0.0) + Vector3.UP*.77
 if attack != "": update_attack(delta)
 if not respawning:
  move_and_slide()
  if is_on_ceiling() and velocity.y > 0: velocity.y = 0
  if is_on_floor() and not was_floor:
   landings += 1
   if trail: trail.impact(global_position+Vector3.UP*.05,Color("bbaa77"),5,.6)
 rig.rotation.y = lerp_angle(rig.rotation.y,atan2(facing.x,facing.z),1.0-exp(-18*delta))
 var phase := 0.0
 if attack != "":
  var a: Array = PamTuning.ATTACKS[attack]
  phase = attack_clock / (float(a[0])+float(a[1])+float(a[2]))
 if attack == "spin": rig.rotation.y = atan2(facing.x,facing.z)+phase*TAU*1.5
 rig.position.y = abs(sin(clock*13))*.035*minf(Vector2(velocity.x,velocity.z).length()/3,1) if is_on_floor() else 0
 if dodge_time > 0: rig.rotation.z = sin(dodge_time/.24*PI)*.7
 else: rig.rotation.z = move_toward(rig.rotation.z,0,delta*6)
 rig.visible = not respawning and (invulnerable <= 0 or int(clock*22)%2==0)
 PamArt.pose(rig,clock,Vector2(velocity.x,velocity.z).length(),attack,phase,not is_on_floor())
 if knocked_out:
  rig.rotation.z = 1.4
  rig.position.y = -.12
 state = "DANO" if stun > 0 else ("ESQUIVA" if dodge_time > 0 else (attack.to_upper() if attack != "" else ("AR" if not is_on_floor() else ("CORRIDA" if movement.length()>.1 else "IDLE"))))
 if global_position.y < -7 and not respawning: die()

func update_attack(delta: float) -> void:
 attack_clock += delta
 var data: Array = PamTuning.ATTACKS[attack]
 if attack_clock >= float(data[0]) and attack_clock <= float(data[0])+float(data[1]):
  for area in attack_area.get_overlapping_areas():
   var target := area.get_parent() as Node3D
   if target == self or hit_targets.has(target.get_instance_id()): continue
   if target.has_method("receive_hit"):
    hit_targets[target.get_instance_id()] = true
    if target.receive_hit(int(data[3]),facing*float(data[4]),attack):
     attack_hits += 1
     struck.emit(target,attack)
 if attack_clock >= float(data[0])+float(data[1])+float(data[2]):
  if combo_queue and attack in ["jab","cross"]:
   attack = "cross" if attack == "jab" else "kick"
   combo += 1
   attack_clock = 0
   combo_queue = false
   hit_targets.clear()
   attack_shape.radius = float(PamTuning.ATTACKS[attack][5])
   if trail: trail.sound("swing",.4)
  else:
   attack = ""
   combo = 0

func receive_hit(damage: int, knock: Vector3, _kind: String = "enemy") -> bool:
 if invulnerable > 0 or respawning or not controllable: return false
 health -= damage
 invulnerable = 1.25
 stun = .32
 velocity = knock + Vector3.UP*4.0
 attack = ""
 health_changed.emit()
 if trail:
  trail.impact(global_position+Vector3.UP*.7,Color("d85a46"),12,1)
  trail.freeze_frame(.055)
  trail.sound("hit",.65)
 if health <= 0: die()
 return true

func die() -> void:
 if respawning: return
 respawning = true
 controllable = false
 attack = ""
 died.emit()

func reset_at(point: Vector3) -> void:
 knocked_out = false
 global_position = point
 velocity = Vector3.ZERO
 health = max_health
 respawning = false
 invulnerable = 1.0
 stun = 0
 attack = ""
 health_changed.emit()
