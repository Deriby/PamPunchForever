class_name PamRailCamera
extends Camera3D

var player: PamPlayer
var curve := Curve3D.new()
var state := "TRILHO"
var shake := 0.0
var focus := Vector3.ZERO
var cinematic := false
var fixed_position := Vector3.ZERO
var fixed_target := Vector3.ZERO
var initialized := false
var offset := 0.0

func _ready() -> void:
 fov = 52
 near = .12
 far = 160
 for p in [Vector3(0,0,6),Vector3(0,0,-18),Vector3(2,0,-36),Vector3(-1,0,-50),Vector3(1,0,-67),Vector3(-3,0,-85),Vector3(0,0,-108)]:
  curve.add_point(p)

func _process(delta: float) -> void:
 if not is_instance_valid(player): return
 var desired: Vector3
 var target: Vector3
 if cinematic:
  desired = fixed_position
  target = fixed_target
  state = "CINEMA"
 else:
  var probe := player.global_position
  probe.y = 0
  offset = curve.get_closest_offset(probe)
  var rail := curve.sample_baked(offset)
  target = Vector3(lerpf(rail.x,probe.x,.62),player.global_position.y*.35+.8,probe.z-1.5)
  desired = Vector3(lerpf(rail.x,probe.x,.28),5.5+maxf(0,player.global_position.y*.28),probe.z+7.6)
  state = "SEGREDO" if probe.x>4.0 and probe.z < -58 else "TRILHO"
  if state == "SEGREDO":
   desired.x = probe.x*.7
   desired.y = 6.8
 if not initialized:
  global_position = desired
  focus = target
  initialized = true
 global_position = global_position.lerp(desired,1.0-exp(-delta*5.8))
 focus = focus.lerp(target,1.0-exp(-delta*8.0))
 shake = maxf(0,shake-delta*1.8)
 var jitter := Vector3(sin(Time.get_ticks_msec()*.13),cos(Time.get_ticks_msec()*.09),0)*shake*.1
 look_at(focus+jitter,Vector3.UP)
