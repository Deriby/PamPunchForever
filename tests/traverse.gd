extends SceneTree
# End-to-end bot: no teleport, god mode, remote damage or forced gate opening.
# Uses the player's input path, actual movement, jump buffering and physical attacks.
var game: Node3D
var p: PamPlayer
var deaths := 0
var reached_checkpoint := false
var route := [Vector3(0,0,-9),Vector3(0,0,-15),Vector3(0,0,-23),Vector3(1,0,-31),Vector3(2,0,-36),Vector3(0,0,-43),Vector3(.85,0,-47),Vector3(-.8,0,-50.6),Vector3(-.5,0,-55),Vector3(0,0,-59.5),Vector3(.8,0,-67),Vector3(-1,0,-74),Vector3(-1.7,0,-80),Vector3(-3,0,-86),Vector3(-2,0,-94),Vector3(-.5,0,-101),Vector3(0,0,-107)]
var index := 0
func _initialize() -> void:
 create_timer(180).timeout.connect(func(): print("FAIL traversal watchdog"); quit(2))
 call_deferred("run")
func run() -> void:
 game = load("res://scenes/trail.tscn").instantiate()
 root.add_child(game)
 game.start_trail()
 p = game.player
 p.input_override = true
 p.died.connect(func(): deaths += 1)
 var last_jump := -500
 for frame in range(18000):
  await physics_frame
  if game.mode == "ending": break
  if deaths>0:
   print("FAIL route death at ",p.position," target ",index)
   break
  var target: Vector3 = route[index]
  if Vector2(p.position.x-target.x,p.position.z-target.z).length()<.7 and index<route.size()-1:
   index += 1
   target = route[index]
  var dir := target-p.position
  dir.y = 0
  p.test_motion = Vector2(dir.x,dir.z).normalized()
  # Fight at reach before the guardian's telegraphed blow.
  var nearest: PamEnemy
  var distance := 2.0
  for e in game.get_tree().get_nodes_in_group("enemies"):
   if e.dead: continue
   var v: float = e.position.distance_to(p.position)
   if v<distance:
    nearest=e;distance=v
  if nearest:
   var facing := nearest.position-p.position
   facing.y=0
   p.facing = facing.normalized()
   if distance<1.7:
    p.test_motion = Vector2.ZERO
    p.start_attack("heavy")
  # Jump all exposed water edges; platform at -55 is used as intermediate landing.
  var edge := (p.position.z < -27 and p.position.z > -29.3) or (p.position.z < -50.7 and p.position.z > -52.1) or (p.position.z < -54 and p.position.z > -57.5) or (p.position.z < -74.6 and p.position.z > -77.8)
  if edge and p.is_on_floor() and frame-last_jump>50:
   p.buffered_jump=.12
   last_jump=frame
  if frame%600==0: print("ROUTE ",index," pos ",p.position," health ",p.health)
 print("ROUTE RESULT mode=",game.mode," deaths=",deaths," checkpoint=",game.checkpoint_set," kills=",game.kills," seeds=",game.seeds," jumps=",p.jumps," hits=",p.attack_hits)
 var success: bool = game.mode=="ending" and deaths==0 and game.checkpoint_set and game.arena_done and p.attack_hits>0 and game.kills>=2
 for child in game.get_children():
  if child is AudioStreamPlayer: child.stop()
 OS.delay_msec(100)
 game.queue_free()
 for i in range(5):await physics_frame
 PamArt.library.clear();PamArt.mats.clear()
 quit(0 if success else 1)
