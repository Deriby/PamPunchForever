extends SceneTree

var game: Node3D
var p: PamPlayer
var checks := 0
var failed := 0

func _initialize() -> void:
 create_timer(180).timeout.connect(func(): print("FAIL integration watchdog"); quit(2))
 call_deferred("run")

func check(condition: bool, label: String) -> void:
 checks += 1
 if not condition: failed += 1
 print(("PASS " if condition else "FAIL ")+label)

func ticks(n: int) -> void:
 for i in range(n): await physics_frame

func settle_at(pos: Vector3) -> void:
 p.global_position = pos
 p.velocity = Vector3.ZERO
 p.test_motion = Vector2.ZERO
 p.cancel_combo()
 p.stun = 0
 p.controllable = true
 await ticks(12)

func run() -> void:
 game = load("res://scenes/trail.tscn").instantiate()
 root.add_child(game)
 p = game.player
 check(InputMap.action_get_events("move_left")[1].physical_keycode==KEY_LEFT and InputMap.action_get_events("move_right")[1].physical_keycode==KEY_RIGHT and InputMap.action_get_events("debug")[0].physical_keycode==KEY_F3,"arrow and debug physical key mappings")
 await ticks(4)
 check(InputMap.has_action("action") and not InputMap.has_action("heavy") and not InputMap.has_action("spin") and not InputMap.has_action("dodge"),"one action and jump replace separate attack/dodge mappings")
 check(game.mode == "title" and game.hud.title.visible,"title and native scene load")
 game.begin_intro()
 game.mode_clock = 12
 await ticks(4)
 check(game.assassin.visible and game.master.visible,"opening presents both fighters")
 game.begin_duel()
 await ticks(2)
 check(p.controllable and game.assassin.enabled,"opening includes controllable confrontation")
 game.begin_aftermath()
 await ticks(3)
 check(p.knocked_out and p.rig.rotation.z>1,"forced defeat holds a knocked-down pose")
 game.mode_clock = 7
 await ticks(4)
 check(game.mode == "play" and p.controllable,"forced defeat transitions into the trail")
 p.input_override = true
 # Disable world enemies only for isolated movement fixtures.
 for e in game.enemy_root.get_children(): e.enabled = false
 await settle_at(Vector3(0,.1,-6))
 check(p.is_on_floor(),"spawn resolves onto floor")
 p.test_motion = Vector2(0,-1)
 await ticks(36)
 check(p.velocity.z < -5.0 and p.position.z < -7,"acceleration produces actual displacement")
 p.test_motion = Vector2.ZERO
 await ticks(28)
 check(absf(p.velocity.z)<.05,"braking reaches rest")
 await settle_at(Vector3(0,.1,-6))
 p.buffered_jump = .12
 var max_y := 0.0
 for i in range(110):
  await physics_frame
  max_y = maxf(max_y,p.position.y)
 check(max_y > 1.5 and max_y < 1.9 and p.is_on_floor(),"full jump rises and lands on collision floor")
 await settle_at(Vector3(0,.1,-6))
 # Real action release exercises the short jump path.
 p.input_override = false
 Input.action_press("jump")
 await ticks(1)
 Input.action_release("jump")
 var short_y := 0.0
 for i in range(100):
  await physics_frame
  short_y = maxf(short_y,p.position.y)
 check(short_y < max_y*.65 and short_y > .1,"button release shortens jump")
 p.input_override = true
 # Real ceiling and wall collisions.
 var roof := PamArt.solid(game,Vector3(0,1.9,-6),Vector3(3,.3,3),Color.GRAY)
 p.buffered_jump = .12
 await ticks(15)
 check(p.position.y < .6 and p.velocity.y <= 0,"ceiling stops upward motion")
 roof.queue_free(); await ticks(70)
 var wall := PamArt.solid(game,Vector3(0,.9,-7),Vector3(3,1.8,.2),Color.GRAY)
 p.test_motion = Vector2(0,-1)
 await ticks(55)
 check(p.position.z > -6.7,"swept world collision blocks wall")
 wall.queue_free()
 p.test_motion = Vector2.ZERO
 # Floor normals on a continuous ramp, without jumping or position correction.
 await settle_at(Vector3(0,.1,-4.1))
 var ramp := PamArt.solid(game,Vector3(0,.13,-6),Vector3(1.4,.1,3),Color.GRAY)
 ramp.rotation.x=.13
 p.test_motion=Vector2(0,-1)
 await ticks(48)
 check(p.position.y>.12 and p.is_on_floor(),"incline collision lifts and grounds moving player")
 ramp.queue_free()
 p.test_motion=Vector2.ZERO
 # Combat fixture uses live Area3D overlap and enemy reaction.
 await settle_at(Vector3(0,.1,-6))
 p.facing = Vector3.FORWARD
 var enemy: PamEnemy = game.spawn_enemy(Vector3(0,.05,-7.05))
 enemy.enabled = true
 enemy.home = enemy.position
 await ticks(5)
 p.press_action()
 await ticks(24)
 check(enemy.health==3 and p.attack_hits>0,"active hitbox strikes an actual enemy hurtbox once")
 check(enemy.state == "DANO" and enemy.velocity.length()>0,"enemy reacts with knockback and stun")
 await ticks(15)
 check(enemy.health==3,"single swing deduplicates repeated overlaps")
 enemy.queue_free(); await ticks(20)
 # Same button chains spin, medium punch and long strong punch.
 p.cancel_combo(); p.press_action(); p.press_action()
 await ticks(55)
 check(p.attack == "medium","buffered second input chains spin to medium")
 p.press_action()
 await ticks(36)
 check(p.attack == "strong","third input chains medium to strong")
 await ticks(80)
 var box: PamProp = game.add_prop("crate",Vector3(0,0,-7))
 await ticks(5)
 var before_crates: int = game.crates
 p.facing = Vector3.FORWARD
 p.press_action()
 await ticks(60)
 check(game.crates == before_crates+1 and not is_instance_valid(box),"physical spin breaks crate and releases pickup")
 # Attack without overlap cannot hurt.
 enemy = game.spawn_enemy(Vector3(2.3,.1,-7))
 enemy.enabled = true
 enemy.set_physics_process(false)
 p.press_action()
 await ticks(100)
 check(enemy.health==4,"attack outside hurtbox leaves enemy health unchanged")
 enemy.set_physics_process(true)
 await settle_at(Vector3(2.3,.1,-6.0))
 p.invulnerable = 0
 var old_health := p.health
 await ticks(180)
 check(p.health < old_health,"live enemy AI telegraphs, attacks, and damages player")
 enemy.queue_free()
 await settle_at(Vector3(0,.1,-6))
 p.invulnerable=0
 p.input_override=false
 Input.action_press("jump")
 await ticks(2)
 Input.action_release("jump")
 Input.action_press("action")
 await ticks(2)
 Input.action_release("action")
 check(p.attack=="spin" and p.velocity.y>0,"the same action button starts spin in the air")
 p.input_override=true
 await ticks(100)
 # Checkpoint through proximity, then death and actual respawn callback.
 await settle_at(Vector3(game.center(-47)+1.5,.3,-47))
 await ticks(5)
 check(game.checkpoint_set and p.health==p.max_health,"checkpoint proximity heals and saves location")
 p.invulnerable = 0
 p.global_position.y = -8
 await ticks(125)
 check(not p.respawning and p.position.distance_to(game.checkpoint)<.6 and p.health==p.max_health,"fall death returns to saved checkpoint")
 # Ride actual moving collision body; require floor and transport, not an open port/PID.
 p.global_position = game.moving_platform.global_position+Vector3.UP*.2
 p.velocity = Vector3.ZERO
 await ticks(25)
 var old_z := p.global_position.z
 await ticks(45)
 check(p.is_on_floor() and absf(p.position.z-old_z)>.1,"moving platform transports a grounded passenger")
 await settle_at(Vector3(6.7,1.1,-66))
 await ticks(20)
 check(game.memory_found,"secret branch collectible records mentor memory")
 await settle_at(Vector3(game.center(-89),.3,-89))
 await ticks(4)
 check(game.arena_spawned and game.arena_enemies.size()==2,"arena entry spawns both required guardians")
 for e in game.arena_enemies: e.receive_hit(10,Vector3.ZERO,"heavy")
 await ticks(10)
 check(game.arena_done and game.gate_block.collision_layer==0,"defeating arena guardians opens physical gate")
 await settle_at(Vector3(game.center(-106),.3,-106))
 await ticks(5)
 check(game.mode=="ending" and game.hud.ending.visible,"exit reaches authored level conclusion")
 # TNT countdown behavior tested independently from player overlap.
 var tnt: PamProp = game.add_prop("tnt",Vector3(5,0,-5))
 await ticks(2)
 tnt.receive_hit(1,Vector3.ZERO,"jab")
 check(tnt.countdown>2.9,"TNT arms a three-second countdown")
 await ticks(390)
 check(not is_instance_valid(tnt),"TNT countdown ends in explosion and cleanup")
 print("RESULT %d/%d passed" % [checks-failed,checks])
 for child in game.get_children():
  if child is AudioStreamPlayer: child.stop()
 OS.delay_msec(100)
 game.queue_free()
 await ticks(4)
 PamArt.library.clear();PamArt.mats.clear()
 quit(1 if failed else 0)
