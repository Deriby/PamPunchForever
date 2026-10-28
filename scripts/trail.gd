extends Node3D

var player: PamPlayer
var camera: PamRailCamera
var hud: PamHUD
var mode := "title"
var mode_clock := 0.0
var seeds := 0
var crates := 0
var kills := 0
var memory_found := false
var checkpoint := Vector3(0,.2,-5)
var checkpoint_set := false
var master: Node3D
var assassin: PamEnemy
var props: Node3D
var enemy_root: Node3D
var moving_platform: AnimatableBody3D
var moving_home := Vector3(0,.0,-55)
var world_clock := 0.0
var music: AudioStreamPlayer
var sounds: Dictionary = {}
var effects: Array[Dictionary] = []
var stage := -1
var arena_spawned := false
var arena_done := false
var arena_enemies: Array[PamEnemy] = []
var gate: Node3D
var gate_block: StaticBody3D
var gate_lift := 0.0
var camera_cutaways: Array[Node3D] = []
var freeze_id := 0
var run_time := 0.0
var rng := RandomNumberGenerator.new()
var forest: PamForest

func _ready() -> void:
 rng.seed = 9281
 build_environment()
 forest = PamForest.new();add_child(forest)
 props = Node3D.new(); add_child(props)
 enemy_root = Node3D.new(); add_child(enemy_root)
 build_level()
 forest.bake()
 bake_terrain()
 player = PamPlayer.new()
 player.name = "Pam"
 player.trail = self
 add_child(player)
 player.position = Vector3(1.2,.1,0)
 player.facing = Vector3(-.5,0,1).normalized()
 player.died.connect(on_player_died)
 camera = PamRailCamera.new()
 camera.player = player
 add_child(camera)
 camera.current = true
 camera.cinematic = true
 camera.fixed_position = Vector3(0,1.8,4.2)
 camera.fixed_target = Vector3(.35,.9,0)
 hud = PamHUD.new(); hud.trail = self; add_child(hud)
 master = PamArt.model("jaburanga"); add_child(master)
 master.position = Vector3(-1.2,0,-2.6)
 master.rotation.y = .65
 assassin = PamEnemy.new();assassin.boss = true;assassin.player = player;assassin.trail = self
 enemy_root.add_child(assassin);assassin.position = Vector3(1,0,-4)
 assassin.visible = false; assassin.enabled = false
 setup_audio()
 # Headless testing opts in explicitly; normal game always opens at the title.
 if "--play" in OS.get_cmdline_user_args(): start_trail()

func build_environment() -> void:
 var world := WorldEnvironment.new()
 var env := Environment.new()
 env.background_mode = Environment.BG_SKY
 var sky := Sky.new()
 var sky_material := ProceduralSkyMaterial.new()
 sky_material.sky_top_color = Color("456b78")
 sky_material.sky_horizon_color = Color("b8c4a3")
 sky_material.ground_horizon_color = Color("92a185")
 sky_material.ground_bottom_color = Color("354a3c")
 sky_material.sun_angle_max = 6.0
 sky_material.sun_curve = .15
 sky.sky_material = sky_material
 env.sky = sky
 env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
 env.ambient_light_color = Color("b9c4b4")
 env.ambient_light_energy = .38
 env.tonemap_mode = Environment.TONE_MAPPER_LINEAR
 env.fog_enabled = true
 env.fog_light_color = Color("658b7d")
 env.fog_density = .015
 env.fog_sky_affect = .5
 world.environment = env
 add_child(world)
 var sun := DirectionalLight3D.new()
 sun.rotation_degrees = Vector3(-55,-32,0)
 sun.light_color = Color("fff0d6")
 sun.light_energy = .78
 sun.shadow_enabled = true
 sun.directional_shadow_max_distance = 30
 sun.directional_shadow_mode = DirectionalLight3D.SHADOW_ORTHOGONAL
 add_child(sun)
 # River beneath the broken route; faceted banks are actual modeled geometry.
 var water := MeshInstance3D.new()
 var plane := PlaneMesh.new();plane.size = Vector2(130,190);plane.subdivide_width = 35;plane.subdivide_depth = 45
 water.mesh = plane
 water.position = Vector3(0,-2.1,-50)
 var shader := Shader.new()
 shader.code = "shader_type spatial; render_mode cull_disabled; void vertex(){VERTEX.y += sin(VERTEX.x*0.9+TIME*0.7)*0.023+sin(VERTEX.z*1.5+TIME)*0.017;} void fragment(){float rip=sin(UV.y*270.0+sin(UV.x*85.0+TIME*0.5)*2.8+TIME*1.3); float pool=sin(UV.x*35.0+sin(UV.y*28.0))*0.5+0.5; ALBEDO=mix(vec3(0.025,0.12,0.13),vec3(0.10,0.29,0.24),pool)*0.9+smoothstep(0.88,0.99,rip)*vec3(0.08,0.15,0.12); ROUGHNESS=0.4;}"
 var wm := ShaderMaterial.new();wm.shader = shader;water.material_override = wm
 add_child(water)

func center(z: float) -> float:
 if z > -20: return 0
 if z > -36: return lerpf(0,2,(-z-20)/16)
 if z > -50: return lerpf(2,-1,(-z-36)/14)
 if z > -67: return lerpf(-1,1,(-z-50)/17)
 if z > -85: return lerpf(1,-3,(-z-67)/18)
 return lerpf(-3,0,clampf((-z-85)/23,0,1))

func ground_y(z: float) -> float:
 if z > -29: return 0.0
 if z > -52: return .25
 if z > -76: return .45
 return .15

func add_land(z1: float,z2: float,width: float, height: float) -> void:
 var z := (z1+z2)/2
 PamArt.solid(self,Vector3(center(z),height-.65,z),Vector3(width,1.3,absf(z2-z1)+.03),Color("70815a"))
 # Painted dirt ribbon runs through mossy ground, leaving natural irregular verges.
 var path_tool := SurfaceTool.new()
 path_tool.begin(Mesh.PRIMITIVE_TRIANGLES)
 var steps := maxi(2,ceili(absf(z1-z2)/1.4))
 var offsets := [-1.9,-1.48,-.72,.72,1.48,1.9]
 var tones := [Color("74815b"),Color("9b8c66"),Color("a58f6a"),Color("a58f6a"),Color("9b8c66"),Color("74815b")]
 for j in range(steps):
  var za := lerpf(z1,z2,float(j)/steps)
  var zb := lerpf(z1,z2,float(j+1)/steps)
  for k in range(5):
   var va := Vector3(center(za)+float(offsets[k])*(.93+.07*sin(za*1.2)),height+.012,za)
   var vb := Vector3(center(za)+float(offsets[k+1])*(.93+.07*sin(za*1.2)),height+.012,za)
   var vc := Vector3(center(zb)+float(offsets[k])*(.93+.07*sin(zb*1.2)),height+.012,zb)
   var vd := Vector3(center(zb)+float(offsets[k+1])*(.93+.07*sin(zb*1.2)),height+.012,zb)
   path_tool.set_color(tones[k]);path_tool.add_vertex(va)
   path_tool.set_color(tones[k]);path_tool.add_vertex(vc)
   path_tool.set_color(tones[k+1]);path_tool.add_vertex(vb)
   path_tool.set_color(tones[k+1]);path_tool.add_vertex(vb)
   path_tool.set_color(tones[k]);path_tool.add_vertex(vc)
   path_tool.set_color(tones[k+1]);path_tool.add_vertex(vd)
 path_tool.generate_normals()
 var path_mesh := MeshInstance3D.new()
 path_mesh.mesh=path_tool.commit();path_mesh.material_override=PamArt.mats["terrain_earth"]
 add_child(path_mesh);path_mesh.add_to_group("terrain_visuals")
 # Leaf litter, buried stones and root-wrapped banks dress the same safe collision.
 for i in range(int(absf(z2-z1)*.8)):
  var zz := rng.randf_range(z2,z1)
  var x := center(z)+rng.randf_range(-width*.42,width*.42)
  place_model("leaf_litter",Vector3(x,height+.012,zz),Vector3.ONE*rng.randf_range(.75,1.3),rng.randf()*TAU)
 for side in [-1,1]:
  for i in range(maxi(1,int(absf(z2-z1)/2.4))):
   var zz := lerpf(z1,z2,(float(i)+.5)/maxf(1,absf(z2-z1)/2.4))
   place_model("rock",Vector3(center(z)+side*(width*.5-.05),height-.16,zz),Vector3(.58,.45,.72),rng.randf()*TAU)
  place_model("root",Vector3(center(z)+side*(width*.5-.15),height+.01,z),Vector3.ONE*.75,rng.randf()*TAU)
 # Dense but non-colliding undergrowth frames the playable corridor.
 for side in [-1,1]:
  var count := maxi(1,int(absf(z1-z2)/4.0))
  for j in range(count):
   var zz := lerpf(z1,z2,(float(j)+.5)/count)
   place_model("thicket",Vector3(center(z)+side*(width*.5-.12),height,zz),Vector3.ONE*.90,float(j)*2.4)
 # Model the exposed rock face below each island; collision stays at the authored edge.
 for cliff_z in [z1-.07,z2+.10]:
  for j in range(5):
   place_model("rock",Vector3(center(z)+lerpf(-width*.40,width*.40,float(j)/4),height-1.30,cliff_z),Vector3(.9,1.18,.63),float(j)*1.7)

func build_level() -> void:
 # Forest floor encloses a narrow stream; banks sit below the playable trail.
 for bank_z in range(8,-120,-12):
  for side in [-1,1]:
   PamArt.solid(self,Vector3(center(bank_z)+side*17,-1.25,bank_z-6),Vector3(21,1.6,12.2),Color("405b37"),false)
 add_land(5,-8,8,0)
 for bounds in [[-8,-17,6.8],[-17,-26,5.8],[-29,-36,6.4],[-36,-44,6],[-44,-52,7],[-58,-66,6.5],[-66,-76,5.7],[-78,-88,6],[-88,-98,8],[-98,-110,7]]:
  add_land(float(bounds[0]),float(bounds[1]),float(bounds[2]),ground_y(float(bounds[1])+.1))
 # Optional sloping root teaches continuous incline contact on the left.
 for ramp_data in [[-20.5,.13],[-23.5,-.13]]:
  var root_ramp := PamArt.solid(self,Vector3(-1.8,.13,float(ramp_data[0])),Vector3(1.3,.1,3.0),Color("78623e"))
  root_ramp.rotation.x = float(ramp_data[1])
 # Crossing boards at the first and final narrow gaps leave visible water between planks.
 for z in [-26.4,-26.95,-27.5,-28.05,-28.6]:
  var plank := StaticBody3D.new()
  add_child(plank);plank.position=Vector3(center(z),-.09,z)
  PamArt.box_shape(plank,Vector3(2.3,.18,.42))
  plank.add_child(PamArt.model("bridge_board"))
  plank.rotation.z = sin(z)*.025
 place_model("bridge_rails",Vector3(center(-27.5),0,-27.5))
 # This optional side path crosses back from the shrine clearing.
 for x in [3.1,3.7,4.3,4.9,5.5]:
  PamArt.solid(self,Vector3(x,.34,-64.5),Vector3(.52,.22,1.7),Color("a27d48"),true,"wood")
 PamArt.solid(self,Vector3(6.7,-.2,-65),Vector3(2.5,1.3,4.8),Color("7e8451"))
 spawn_pickup(Vector3(6.7,1.3,-66),"memory")
 for x in [4.0,5.2,6.4]: spawn_pickup(Vector3(x,1.0,-64.5),"seed")
 # Shuttle uses AnimatableBody3D; CharacterBody floor velocity carries the passenger.
 moving_platform = AnimatableBody3D.new()
 moving_platform.name = "Balsa"
 add_child(moving_platform)
 moving_home.x = center(-55)
 moving_home.y = .32
 moving_platform.position = moving_home
 PamArt.box_shape(moving_platform,Vector3(2.4,.25,2.1))
 moving_platform.add_child(PamArt.model("raft"))
 # Decorative mooring stones and posts.
 for z in [-51.5,-58.5]:
  for x in [-1.7,1.7]: place_model("rock",Vector3(center(z)+x,ground_y(z),z),Vector3.ONE*.6)
 # Tall flanking trees, undergrowth, scattered fallen trunks and river rocks.
 for i in range(88):
  var z := rng.randf_range(-116,8)
  var side := -1 if i%2 else 1
  var x := center(z)+side*rng.randf_range(7.2,15)
  var y := -.6 if absf(x-center(z))>9 else -.1
  place_model("tree%d" % (i%3),Vector3(x,y,z),Vector3.ONE*rng.randf_range(.9,1.45),rng.randf()*TAU)
  if i%2==0: place_model("rock",Vector3(x*.75,-1.2,z),Vector3.ONE*rng.randf_range(1.2,2.5))
 for i in range(168):
  var z := rng.randf_range(-111,5)
  var x := center(z)+(-1 if i%2 else 1)*rng.randf_range(2.6,5.2)
  if z > -26 or (z < -29 and z > -52) or (z < -58 and z > -76) or z < -78:
   var plant := ["fern","broadleaf","fern","broadleaf","bromeliad"][i%5] as String
   place_model(plant,Vector3(x,ground_y(z)-.02,z),Vector3.ONE*rng.randf_range(.65,1.2),rng.randf()*TAU)
 for i in range(72):
  var zz := rng.randf_range(-113,7)
  var side := -1 if i%2 else 1
  place_model("thicket",Vector3(center(zz)+side*rng.randf_range(7.0,12.0),-.45,zz),Vector3.ONE*rng.randf_range(.95,1.4),rng.randf()*TAU)
 # Mossy outcrops break the channel banks into natural silhouettes.
 for zz in range(4,-116,-4):
  for side in [-1,1]:
   place_model("rock",Vector3(center(zz)+side*6.65,-1.60,zz),Vector3(1.2,1.3,1.8),float(zz)*.31)
 # Ruins have stepped lintels and gold inlays, deliberately fictional.
 for z in [-43.5,-79.5,-101.0]:
  var x := center(z)
  for side in [-1,1]:
   var pillar := StaticBody3D.new()
   add_child(pillar);pillar.position=Vector3(x+side*2.75,1.4,z)
   PamArt.box_shape(pillar,Vector3(.8,2.8,.9))
   var visual := PamArt.model("ruin_pillar")
   pillar.add_child(visual);visual.position.y=-1.4
  var lintel := Node3D.new()
  add_child(lintel);lintel.position=Vector3(x,3.35,z)
  lintel.add_child(PamArt.model("ruin_lintel"))
  lintel.set_meta("camera_cutaway",true)
  camera_cutaways.append(lintel)
  for side in [-1,1]:
   var fern := PamArt.model("fern")
   lintel.add_child(fern);fern.position=Vector3(side*2.7,.25,0);fern.scale=Vector3.ONE*.7
 # Checkpoint and readable trails of collectible seeds.
 add_prop("checkpoint",Vector3(center(-47)+1.5,.25,-47))
 for z in [-6,-9,-12,-15,-20,-23,-30,-33,-38,-42,-49,-59,-62,-69,-73,-80,-84,-88,-98,-104]:
  spawn_pickup(Vector3(center(z),ground_y(z)+.65,z),"seed")
 for pos in [Vector3(-.7,0,-11),Vector3(.5,0,-12),Vector3(-1,0,-22),Vector3(2,.25,-34),Vector3(-1,.25,-39),Vector3(1,.45,-61),Vector3(-2,.45,-71),Vector3(0,.15,-82),Vector3(-2,.15,-96)]: add_prop("crate",pos)
 add_prop("tnt",Vector3(2.5,.25,-40))
 add_prop("tnt",Vector3(-2,.15,-83))
 for z in [-18,-35,-63,-72]: spawn_enemy(Vector3(center(z)+.6,ground_y(z)+.1,z))
 # Closing shrine, suspended panels and visible arena gate.
 gate = Node3D.new();add_child(gate);gate.position = Vector3(center(-98),.15,-98)
 gate_block = StaticBody3D.new();gate.add_child(gate_block)
 PamArt.box_shape(gate_block,Vector3(5.9,2.6,.45),Vector3.UP*1.3)
 gate.add_child(PamArt.model("gate"))
 place_model("shrine",Vector3(center(-106),.15,-106),Vector3.ONE*1.25)
 for dock_z in range(-110,-117,-1):
  PamArt.solid(self,Vector3(0,-.05,dock_z),Vector3(3.5,.22,.82),Color("927346"),true,"wood")
 for side in [-1,1]:
  for dock_z in [-111,-115]:
   PamArt.solid(self,Vector3(side*1.6,-.3,dock_z),Vector3(.17,1.4,.17),Color("705235"),true,"wood")
 # An original crimson cloth is the killer's visual clue.
 var cloth := MeshInstance3D.new()
 var clothmesh := PlaneMesh.new();clothmesh.size = Vector2(.6,1.3)
 cloth.mesh = clothmesh;cloth.material_override = PamArt.material(Color("9b322c"))
 add_child(cloth);cloth.position = Vector3(1.7,1.5,-105.5);cloth.rotation_degrees.x = 90

func place_model(key: String,pos: Vector3,s: Vector3 = Vector3.ONE,angle: float = 0) -> Node3D:
 if key in ["tree0","tree1","tree2","fern","rock","broadleaf","bromeliad","root","leaf_litter","thicket"]:
  forest.place(key,pos,s,angle)
  return null
 var model := PamArt.model(key)
 add_child(model);model.position = pos;model.scale = s;model.rotation.y = angle
 return model

func add_prop(kind: String,pos: Vector3) -> PamProp:
 var p := PamProp.new();p.kind = kind;p.trail = self;p.position = pos
 props.add_child(p);p.add_to_group("props")
 return p

func spawn_pickup(pos: Vector3,kind: String) -> void:
 add_prop(kind,pos)

func spawn_enemy(pos: Vector3) -> PamEnemy:
 var e := PamEnemy.new();e.position = pos;e.trail = self;e.player = player
 e.variant = absi(int(pos.z))%2
 enemy_root.add_child(e);e.add_to_group("enemies")
 return e

func _process(delta: float) -> void:
 mode_clock += delta
 if mode == "title":
  PamArt.pose(master,mode_clock,.0)
 elif mode == "intro": update_intro()
 elif mode == "duel":
  if mode_clock > 11: begin_aftermath()
  hud.hint.text = "J / X · giro → soco médio → soco forte    Espaço / A · pular"
 elif mode == "aftermath": update_aftermath()
 elif mode == "play":
  run_time += delta
  update_progress()
 for lintel in camera_cutaways:
  lintel.visible = mode != "play" or not (player.position.z < lintel.position.z+1.5 and player.position.z > lintel.position.z-10)
 update_effects(delta)
 if gate and arena_done: gate.position.y = lerpf(gate.position.y,3.4,1-exp(-delta*2))

func _physics_process(delta: float) -> void:
 world_clock += delta
 if moving_platform:
  moving_platform.position = moving_home + Vector3(0,sin(world_clock)*.06,sin(world_clock*1.15)*1.45)
 # Enemies created before the player get their dependency after scene construction.
 for e in enemy_root.get_children():
  if e is PamEnemy and not is_instance_valid(e.player): e.player = player

func begin_intro() -> void:
 if mode != "title": return
 mode = "intro";mode_clock = 0;stage = -1
 player.position = Vector3(0,.1,0)
 hud.show_mode(mode)
 camera.fixed_position = Vector3(3.4,2.1,3)
 camera.fixed_target = Vector3(-.4,1,-1.7)
 player.facing = Vector3(-.5,0,-1).normalized()

func line_for(who: String,words: String) -> void:
 hud.speaker.text = who
 hud.subtitle.text = words

func update_intro() -> void:
 var t := mode_clock
 assassin.visible = t >= 8
 if t < 4:
  line_for("ALGUMAS SEMANAS ANTES…", "Enviado do Japão à Amazônia, Pam encontrou mais que um mestre.")
  PamArt.pose(master,t,0,"jab",fmod(t,.8)/.8)
 elif t < 8:
  line_for("JABURANGA", "Ser rápido não basta. Saiba por que você luta.")
  PamArt.pose(master,t,0)
 elif t < 10.5:
  assassin.visible = true
  line_for("UM VISITANTE SEM NOME", "Seu tempo acabou, velho mestre.")
  camera.fixed_position = Vector3(-4,2,-1)
  camera.fixed_target = Vector3(0,1,-3)
 elif t < 16:
  line_for("", "")
  # Short rapid advances and precise strikes demonstrate Jaburanga's strength.
  var f := fmod(t-10.5,1.1)/1.1
  master.position = Vector3(-1.2,0,-2.6).lerp(Vector3(.55,0,-3.7),sin(f*PI)*.85)
  master.rotation.y = -1.0
  PamArt.pose(master,t,3,"spin",f)
  PamArt.pose(assassin.rig,t,0,"heavy",fmod(f+.5,1))
  if int((t-10.5)*3)>stage:
   stage = int((t-10.5)*3)
   impact(master.position+Vector3(.3,.9,-.2),Color("f5cf7f"),8,.8)
   sound("hit",.25)
 elif t < 19:
  master.rotation.z = lerpf(master.rotation.z,-1.5,.08)
  master.position.y = -.12
  assassin.position = Vector3(.5,0,-3.8)
  line_for("PAM", "Mestre…? Não. NÃO!")
  camera.fixed_position = Vector3(-2,1.1,.8)
  camera.fixed_target = Vector3(-.2,.65,-2.5)
 else: begin_duel()

func begin_duel() -> void:
 if mode not in ["intro","title"]: return
 mode = "duel"; mode_clock = 0
 master.rotation.z = -1.5
 master.position = Vector3(-1.3,-.13,-2.7)
 assassin.visible = true;assassin.enabled = true
 assassin.position = Vector3(.4,.1,-3.8)
 assassin.home = assassin.position
 assassin.player = player
 player.controllable = true
 camera.cinematic = false
 hud.show_mode(mode)
 toast("VOCÊ NÃO VAI LEVÁ-LO!", "Enfrente o assassino. J / X encadeia os golpes; Espaço / A pula.",4)

func begin_aftermath() -> void:
 if mode == "aftermath": return
 mode = "aftermath";mode_clock = 0
 Engine.time_scale = 1
 assassin.enabled = false
 player.controllable = false
 player.respawning = false
 player.cancel_combo()
 player.health = 1
 player.position = Vector3(0,.1,.8)
 player.velocity = Vector3.ZERO
 player.knocked_out = true
 player.rig.rotation.z = 1.1
 camera.cinematic = true
 camera.fixed_position = Vector3(3,1.6,3.7)
 camera.fixed_target = Vector3(0,.6,-1.5)
 hud.show_mode(mode)
 sound("boom",.5)

func update_aftermath() -> void:
 if mode_clock < 3:
  line_for("O ASSASSINO", "A raiva só torna você previsível.")
 elif mode_clock < 6:
  assassin.visible = false
  line_for("PAM", "Eu vou encontrar você.")
 else: start_trail()

func start_trail() -> void:
 mode = "play";mode_clock = 0
 master.visible = false
 assassin.visible = false;assassin.enabled = false
 player.rig.rotation.z = 0
 player.reset_at(checkpoint)
 player.facing = Vector3.FORWARD
 player.controllable = true
 camera.cinematic = false
 hud.show_mode(mode)
 toast("01  /  A TRILHA DA VINGANÇA", "O luto fica para trás. A promessa segue com você.",4)

func update_progress() -> void:
 var z := player.position.z
 if z > -15: hud.hint.text = "WASD / setas · mover     Espaço · pular (segure para subir mais)     J · quebrar caixas"
 elif z > -25: hud.hint.text = "J, J, J / X, X, X · giro → soco médio → soco forte     Espaço / A · pular"
 elif z > -31: hud.hint.text = "A ponte está à frente. Salte para alcançar a margem mais alta."
 elif z > -43: hud.hint.text = "Pule sobre o inimigo ou ataque no ar com J. Cuidado com as caixas de pavio!"
 elif z > -52: hud.hint.text = "Aproxime-se do altar para recuperar o fôlego e salvar seu caminho."
 elif z > -61: hud.hint.text = "Observe o movimento da balsa. Salte no momento certo."
 elif z > -71: hud.hint.text = "Nem toda lembrança fica na trilha principal. Procure o brilho à direita."
 elif z > -88: hud.hint.text = "Atravesse a fenda com um pulo longo. A ruína está logo adiante."
 elif z > -99: hud.hint.text = "A CLAREIRA DOS GUARDIÕES  ·  Derrote os dois guardiões para abrir a passagem."
 else: hud.hint.text = "O antigo porto. A marca vermelha. Seu próximo passo."
 if z < -88 and not arena_spawned:
  arena_spawned = true
  arena_enemies.append(spawn_enemy(Vector3(center(-93)-1.2,.25,-93)))
  arena_enemies.append(spawn_enemy(Vector3(center(-94)+1.2,.25,-94)))
  toast("A CLAREIRA DOS GUARDIÕES", "Leia a antecipação dos golpes. Mova-se, pule e encadeie o contra-ataque.",4)
 if arena_spawned and not arena_done:
  arena_done = true
  for e in arena_enemies:
   if is_instance_valid(e) and not e.dead: arena_done = false
  if arena_done:
   gate_block.collision_layer = 0
   gate_block.collision_mask = 0
   toast("CAMINHO ABERTO", "O porto guarda uma pista. Continue até o altar.",4)
   sound("checkpoint",.7)
 if z < -105 and arena_done and absf(player.position.x-center(z))<2.5:
  finish_level()

func set_checkpoint(pos: Vector3) -> void:
 checkpoint = pos
 checkpoint_set = true
 player.health = player.max_health
 player.health_changed.emit()
 toast("CHECKPOINT  /  O ALTAR DAS RAÍZES", "Seu caminho está guardado. R retorna aqui; o progresso vale nesta sessão.",4)
 sound("checkpoint",.6)

func on_player_died() -> void:
 if mode == "duel":
  begin_aftermath()
  return
 if mode != "play": return
 hud.fade.color.a = .8
 await get_tree().create_timer(.7).timeout
 player.reset_at(checkpoint)
 player.controllable = true
 hud.fade.color.a = 0
 # Reset surviving enemy positions, preserving defeated enemies / collectibles.
 for e in enemy_root.get_children():
  if e is PamEnemy and not e.boss and not e.dead:
   e.global_position = e.home
   e.velocity = Vector3.ZERO
   e.state = "PATRULHA"
 toast("LEVANTE, PAM.","Respire. Observe. Tente de novo.",2.5)

func finish_level() -> void:
 mode = "ending"
 player.controllable = false
 hud.show_mode(mode)
 sound("checkpoint",.7)

func restart() -> void:
 get_tree().paused = false
 Engine.time_scale = 1
 get_tree().reload_current_scene()

func toggle_pause() -> void:
 if mode not in ["play","duel"]: return
 get_tree().paused = not get_tree().paused
 hud.pause_panel.visible = get_tree().paused

func toast(a: String,b: String,duration: float = 3) -> void:
 if hud: hud.toast(a,b,duration)

func impact(pos: Vector3,color: Color,count: int = 12,strength: float = 1) -> void:
 if camera: camera.shake = maxf(camera.shake,.5*strength)
 for i in range(count):
  var m := MeshInstance3D.new()
  var mesh := PrismMesh.new();mesh.size = Vector3(.055,.12,.05)*rng.randf_range(.6,1.8)
  m.mesh = mesh
  m.material_override = PamArt.material(color,.15)
  add_child(m);m.global_position = pos
  var v := Vector3(rng.randf_range(-2,2),rng.randf_range(1,3),rng.randf_range(-2,2))*strength
  effects.append({"node":m,"velocity":v,"life":rng.randf_range(.2,.55)})

func update_effects(delta: float) -> void:
 for i in range(effects.size()-1,-1,-1):
  var e: Dictionary = effects[i]
  e.life -= delta
  if e.life <= 0:
   e.node.queue_free();effects.remove_at(i)
  else:
   e.velocity.y -= delta*8
   e.node.position += e.velocity*delta
   e.node.rotate_x(delta*5)
   e.node.scale = Vector3.ONE*minf(1,e.life*5)

func freeze_frame(seconds: float) -> void:
 freeze_id += 1
 var id := freeze_id
 Engine.time_scale = .14
 await get_tree().create_timer(seconds,true,false,true).timeout
 if freeze_id == id: Engine.time_scale = 1.0

func setup_audio() -> void:
 for key in ["swing","hit","break","jump","collect","checkpoint","boom","fuse"]:
  sounds[key] = load("res://assets/audio/%s.wav" % key)
 music = AudioStreamPlayer.new();add_child(music)
 music.stream = load("res://assets/audio/trilha.wav")
 music.volume_db = -18
 music.finished.connect(func(): music.play())
 music.play()

func sound(key: String,volume: float = .5) -> void:
 if not sounds.has(key): return
 var s := AudioStreamPlayer.new()
 add_child(s);s.stream = sounds[key];s.volume_db = linear_to_db(volume)-6
 s.pitch_scale = rng.randf_range(.94,1.06)
 s.finished.connect(s.queue_free)
 s.play()

func _exit_tree() -> void:
 Engine.time_scale = 1
 for child in get_children():
  if child is AudioStreamPlayer: child.stop()
 sounds.clear()

func bake_terrain() -> void:
 # Batch by shared material; keep colliders, animated ferry and camera cutaways separate.
 var groups: Dictionary = {}
 for candidate in get_tree().get_nodes_in_group("terrain_visuals"):
  var mesh := candidate as MeshInstance3D
  var ancestor := mesh.get_parent()
  var dynamic := false
  while ancestor != self and ancestor != null:
   if ancestor == gate or ancestor is AnimatableBody3D or ancestor.has_meta("camera_cutaway"):
    dynamic = true
    break
   ancestor = ancestor.get_parent()
  if dynamic: continue
  var mat := mesh.material_override
  var id := mat.get_instance_id()
  if not groups.has(id):
   var tool := SurfaceTool.new()
   tool.begin(Mesh.PRIMITIVE_TRIANGLES)
   groups[id] = {"surface":tool,"material":mat}
  groups[id].surface.append_from(mesh.mesh,0,global_transform.affine_inverse()*mesh.global_transform)
  mesh.queue_free()
 for id in groups:
  var combined := MeshInstance3D.new()
  combined.mesh = groups[id].surface.commit()
  combined.material_override = groups[id].material
  combined.name = "TerrainMaterialBatch"
  add_child(combined)
