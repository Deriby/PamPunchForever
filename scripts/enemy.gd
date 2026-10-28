class_name PamEnemy
extends CharacterBody3D

signal defeated
var player: PamPlayer
var trail: Node
var rig: PamNpcAnimator
var home := Vector3.ZERO
var health := 4
var state := "PATRULHA"
var timer := 0.0
var clock := 0.0
var cooldown := 0.0
var direction := Vector3.FORWARD
var attack_area: Area3D
var hit_sent := false
var hurt_duration := .42
var boss := false
var variant := 0
var enabled := true
var dead := false
var telegraph: MeshInstance3D

func _ready() -> void:
 collision_layer = 4
 collision_mask = 1
 floor_snap_length = .25
 home = position
 PamArt.box_shape(self,Vector3(.55,1.4,.5),Vector3.UP*.75)
 rig = PamNpcAnimator.new()
 rig.character = "lar" if boss else "inimigo"
 add_child(rig)
 PamArt.hurtbox(self,Vector3(.65,1.45,.6),Vector3.UP*.8)
 attack_area = Area3D.new()
 attack_area.collision_layer = 16
 attack_area.collision_mask = 8
 add_child(attack_area)
 PamArt.box_shape(attack_area,Vector3(.5,.6,.55),Vector3.ZERO)
 telegraph = MeshInstance3D.new()
 var ring := TorusMesh.new()
 ring.inner_radius = .43
 ring.outer_radius = .49
 ring.rings = 16
 ring.ring_segments = 6
 telegraph.mesh = ring
 telegraph.material_override = PamArt.material(Color("ffb549"),.7)
 add_child(telegraph)
 telegraph.position.y = .035
 telegraph.visible = false

func _physics_process(delta: float) -> void:
 if not enabled or not is_instance_valid(player): return
 clock += delta
 cooldown -= delta
 if dead:
  timer += delta
  rig.pose("Defeat",timer)
  rig.position.y = -maxf(0,timer-.8)*.4
  if timer > 1: queue_free()
  return
 var to_player := player.global_position-global_position
 to_player.y = 0
 var dist := to_player.length()
 if global_position.y < -6:
  finish()
  return
 if state == "DANO":
  timer -= delta
  velocity.x = move_toward(velocity.x,0,delta*6)
  velocity.z = move_toward(velocity.z,0,delta*6)
  if timer <= 0: state = "PERSEGUIR"
 elif state == "ANTECIPACAO":
  timer += delta
  velocity.x = 0; velocity.z = 0
  telegraph.visible = true
  telegraph.scale = Vector3.ONE*(1.0+sin(timer*25)*.1)
  if timer > .48:
   state = "ATAQUE"; timer = 0; hit_sent = false
 elif state == "ATAQUE":
  timer += delta
  velocity.x = direction.x*2.0 if timer < .16 else 0.0
  velocity.z = direction.z*2.0 if timer < .16 else 0.0
  if timer >= .08 and timer < .20 and not hit_sent:
   for area in attack_area.get_overlapping_areas():
    if area.get_parent() == player:
     var ray := PhysicsRayQueryParameters3D.create(global_position+Vector3.UP*.9,player.global_position+Vector3.UP*.7,1)
     if get_world_3d().direct_space_state.intersect_ray(ray).is_empty():
      hit_sent = player.receive_hit(1,direction*5,"enemy")
  if timer > .55:
   state = "PERSEGUIR"; cooldown = .55; telegraph.visible = false
 else:
  var target := home+Vector3(sin(clock*.8)*.9,0,0)
  if dist < 6.0 and player.controllable and abs(player.position.y-position.y)<2.0:
   state = "PERSEGUIR"
   target = player.global_position
   if dist < 1.25 and cooldown <= 0:
    state = "ANTECIPACAO"; timer = 0
  else: state = "PATRULHA"
  var desired := target-global_position
  desired.y = 0
  if desired.length() > .12:
   direction = desired.normalized()
   var speed := 1.9 if state == "PERSEGUIR" else .65
   velocity.x = direction.x*speed; velocity.z = direction.z*speed
  else:
   velocity.x = 0; velocity.z = 0
 velocity.y -= 25*delta
 move_and_slide()
 rig.rotation.y = lerp_angle(rig.rotation.y,atan2(direction.x,direction.z),1-exp(-12*delta))
 if state == "DANO": rig.pose("Hit",hurt_duration-timer)
 elif state == "ANTECIPACAO": rig.pose("Windup",timer/.48*rig.length("Windup"))
 elif state == "ATAQUE": rig.pose("Attack",timer/.55*rig.length("Attack"))
 elif Vector2(velocity.x,velocity.z).length() > .2: rig.pose("Run" if state == "PERSEGUIR" else "Walk",clock*1.4)
 else: rig.pose("Idle",clock)
 attack_area.global_position = rig.contact_point()
 attack_area.rotation.y = atan2(direction.x,direction.z)
 # Stomp uses actual descending feet above the hurtbox, with bounce.
 if player.velocity.y < -1 and dist < .62 and player.global_position.y > global_position.y+1.05 and player.global_position.y < global_position.y+1.65:
  if receive_hit(2,Vector3.ZERO,"stomp"): player.velocity.y = 7.0

func receive_hit(damage: int, knock: Vector3, kind: String) -> bool:
 if dead or not enabled: return false
 if boss:
  if trail: trail.impact(global_position+Vector3.UP,Color("f4c47e"),9,.8)
  return true
 health -= damage
 state = "DANO"
 timer = .7 if kind in ["strong","heavy"] else .42
 hurt_duration = timer
 velocity = knock + Vector3.UP*(2.8 if kind in ["strong","heavy","kick","air"] else 1.3)
 telegraph.visible = false
 if trail:
  trail.impact(global_position+Vector3.UP*.8,Color("ffd584"),14,1.1)
  trail.freeze_frame(.085 if kind in ["strong","heavy"] else .05)
  trail.sound("hit",.65)
 if health <= 0: finish()
 return true

func finish() -> void:
 if dead: return
 dead = true
 timer = 0
 collision_layer = 0
 defeated.emit()
 if trail:
  trail.kills += 1
  trail.spawn_pickup(global_position+Vector3.UP*.4,"seed")
