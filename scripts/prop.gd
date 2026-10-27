class_name PamProp
extends Node3D

var kind := "seed"
var trail: Node
var visual: Node3D
var home := Vector3.ZERO
var clock := 0.0
var countdown := -1.0
var broken := false
var active := false
var hurt: Area3D
var body: StaticBody3D
var label: Label3D

func _ready() -> void:
 home = position
 match kind:
  "crate", "tnt":
   visual = PamArt.model(kind)
   body = StaticBody3D.new()
   add_child(body)
   PamArt.box_shape(body,Vector3(.76,.76,.76),Vector3.UP*.38)
   hurt = PamArt.hurtbox(self,Vector3(.85,.85,.85),Vector3.UP*.4)
   if kind == "tnt":
    label = Label3D.new()
    label.text = "!"
    label.font_size = 60
    label.outline_size = 10
    label.position.y = 1.1
    label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
    add_child(label)
  "checkpoint": visual = PamArt.model("shrine")
  "memory":
   visual = PamArt.model("amulet")
   visual.scale = Vector3.ONE*1.5
  _:
   visual = PamArt.model("seed")
   visual.scale = Vector3.ONE*.6
 add_child(visual)

func _physics_process(delta: float) -> void:
 if broken: return
 clock += delta
 if kind in ["seed","memory"]:
  visual.rotation.y += delta*1.8
  visual.position.y = sin(clock*3)*.12
 if not trail or not is_instance_valid(trail.player): return
 var p: PamPlayer = trail.player
 var dist := p.global_position.distance_to(global_position)
 if kind == "checkpoint" and dist < 1.25 and p.controllable:
  if not active:
   active = true
   trail.set_checkpoint(global_position+Vector3(0,.15,1.4))
   trail.impact(global_position+Vector3.UP*1.6,Color("9cf4c7"),28,1.5)
   visual.scale = Vector3.ONE*1.08
 elif kind in ["seed","memory"] and dist < .95:
  broken = true
  if kind == "memory":
   trail.memory_found = true
   trail.toast("LEMBRANÇA DE JABURANGA", "A força sem propósito se perde. Você ainda tem um caminho, Pam.",5)
  else: trail.seeds += 1
  trail.sound("collect",.45)
  trail.impact(global_position,Color("f8cc6b"),7,.6)
  queue_free()
 elif kind in ["crate","tnt"]:
  var flat := Vector2(p.global_position.x-global_position.x,p.global_position.z-global_position.z).length()
  if flat < .60 and p.velocity.y < -1 and p.global_position.y > global_position.y+.60 and p.global_position.y < global_position.y+1.0:
   receive_hit(1,Vector3.ZERO,"stomp")
   p.velocity.y = 7.5
 if countdown > 0:
  countdown -= delta
  label.text = str(ceili(countdown))
  visual.scale = Vector3.ONE*(1+sin(clock*25)*.04)
  if countdown <= 0: explode()

func receive_hit(_damage: int, _knock: Vector3, _attack: String) -> bool:
 if broken: return false
 if kind == "tnt":
  if countdown < 0:
   countdown = 3.0
   trail.sound("fuse",.5)
  return true
 if kind != "crate": return false
 broken = true
 trail.crates += 1
 trail.sound("break",.55)
 trail.impact(global_position+Vector3.UP*.4,Color("ce964d"),18,1.2)
 trail.spawn_pickup(global_position+Vector3.UP*.5,"seed")
 queue_free()
 return true

func explode() -> void:
 if broken: return
 broken = true
 trail.impact(global_position+Vector3.UP*.5,Color("ff7737"),40,2.5)
 trail.sound("boom",.75)
 trail.freeze_frame(.06)
 var center := global_position
 var p: PamPlayer = trail.player
 if p.global_position.distance_to(center) < 2.4:
  p.receive_hit(2,(p.global_position-center).normalized()*8,"tnt")
 for e in get_tree().get_nodes_in_group("enemies"):
  if is_instance_valid(e) and e.global_position.distance_to(center) < 2.7:
   e.receive_hit(5,(e.global_position-center).normalized()*8,"heavy")
 for prop in get_tree().get_nodes_in_group("props"):
  if prop != self and is_instance_valid(prop) and prop.global_position.distance_to(center) < 2.5:
   prop.receive_hit(5,Vector3.ZERO,"explosion")
 queue_free()
