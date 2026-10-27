class_name PamArt
extends RefCounted

static var library: Dictionary = {}
static var mats: Dictionary = {}

static func model(key: String) -> Node3D:
 if not library.has(key):
  library[key] = load("res://assets/models/%s.glb" % key)
 return library[key].instantiate()

static func material(color: Color, glow: float = 0.0) -> StandardMaterial3D:
 var key := str(color) + str(glow)
 if mats.has(key): return mats[key]
 var m := StandardMaterial3D.new()
 m.albedo_color = color
 m.roughness = 0.95
 if glow > 0:
  m.emission_enabled = true
  m.emission = color
  m.emission_energy_multiplier = glow
 mats[key] = m
 return m

static func solid(parent: Node3D, pos: Vector3, size: Vector3, color: Color, collision: bool = true, surface: String = "earth") -> Node3D:
 var root := StaticBody3D.new() if collision else Node3D.new()
 parent.add_child(root)
 root.position = pos
 var mesh := MeshInstance3D.new()
 # Bevelled octagonal silhouette with stratified sides; collisions remain simple.
 var v: Array[Vector3] = []
 var w := size.x / 2.0
 var d := size.z / 2.0
 var cut := minf(w, d) * 0.14
 var ring := [Vector2(-w+cut,-d),Vector2(w-cut,-d),Vector2(w,-d+cut),Vector2(w,d-cut),Vector2(w-cut,d),Vector2(-w+cut,d),Vector2(-w,d-cut),Vector2(-w,-d+cut)]
 var st := SurfaceTool.new()
 st.begin(Mesh.PRIMITIVE_TRIANGLES)
 for i in range(8):
  var a: Vector2 = ring[i]
  var b: Vector2 = ring[(i+1)%8]
  var tone := color.lightened(0.035 * (i%3))
  triangle(st, Vector3(0,size.y/2,0),Vector3(a.x,size.y/2,a.y),Vector3(b.x,size.y/2,b.y),tone)
  var top_a := Vector3(a.x,size.y/2,a.y)
  var top_b := Vector3(b.x,size.y/2,b.y)
  var low_a := Vector3(a.x,-size.y/2,a.y)
  var low_b := Vector3(b.x,-size.y/2,b.y)
  var side_color := Color("6d5a43") if surface == "earth" else color.darkened(.22)
  triangle(st,top_a,low_a,top_b,side_color.darkened((i%3)*.035))
  triangle(st,top_b,low_a,low_b,side_color.darkened(.08))
 st.generate_normals()
 mesh.mesh = st.commit()
 var material_key := "terrain_"+surface
 var m: StandardMaterial3D
 if mats.has(material_key):
  m = mats[material_key]
 else:
  m = StandardMaterial3D.new()
  m.vertex_color_use_as_albedo = true
  m.vertex_color_is_srgb = true
  m.albedo_texture = load("res://assets/textures/style/terrain_%s.png" % surface)
  m.uv1_triplanar = true
  m.uv1_world_triplanar = true
  m.uv1_scale = Vector3.ONE*(.6 if surface == "earth" else 1.0)
  m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
  m.cull_mode = BaseMaterial3D.CULL_DISABLED
  mats[material_key] = m
 mesh.material_override = m
 root.add_child(mesh)
 mesh.add_to_group("terrain_visuals")
 if collision:
  var shape := CollisionShape3D.new()
  var box := BoxShape3D.new()
  box.size = size
  shape.shape = box
  root.add_child(shape)
 return root

static func triangle(st: SurfaceTool, a: Vector3,b: Vector3,c: Vector3,color: Color) -> void:
 st.set_color(color)
 st.add_vertex(a); st.add_vertex(b); st.add_vertex(c)

static func box_shape(parent: Node3D, size: Vector3, pos: Vector3 = Vector3.ZERO) -> CollisionShape3D:
 var c := CollisionShape3D.new()
 var s := BoxShape3D.new()
 s.size = size
 c.shape = s
 c.position = pos
 parent.add_child(c)
 return c

static func hurtbox(parent: Node3D, size: Vector3, pos: Vector3) -> Area3D:
 var a := Area3D.new()
 a.collision_layer = 8
 a.collision_mask = 0
 a.monitorable = true
 parent.add_child(a)
 box_shape(a,size,pos)
 return a

static func pose(rig: Node3D, time: float, speed: float, attack: String = "", phase: float = 0.0, airborne: bool = false) -> void:
 var arm_l := rig.find_child("ArmL",true,false) as Node3D
 var arm_r := rig.find_child("ArmR",true,false) as Node3D
 var leg_l := rig.find_child("LegL",true,false) as Node3D
 var leg_r := rig.find_child("LegR",true,false) as Node3D
 var head := rig.find_child("Head",true,false) as Node3D
 var torso := rig.find_child("Torso",true,false) as Node3D
 var stride := sin(time*13.0) * clampf(speed/5.0,0,1)
 if arm_l: arm_l.rotation = Vector3(stride*.7-.12,0,-.10)
 if arm_r: arm_r.rotation = Vector3(-stride*.7-.12,0,.10)
 if leg_l: leg_l.rotation = Vector3(-stride*.8,0,0)
 if leg_r: leg_r.rotation = Vector3(stride*.8,0,0)
 if head: head.rotation.z = sin(time*2.0)*.025
 if torso: torso.rotation = Vector3(0,0,sin(time*13.0)*.025*minf(speed,1.0))
 if airborne:
  if leg_l: leg_l.rotation.x = -.65
  if leg_r: leg_r.rotation.x = .6
  if arm_l: arm_l.rotation.x = -1.1
  if arm_r: arm_r.rotation.x = -.8
 if attack != "":
  var punch := sin(clampf(phase,0,1)*PI)
  if arm_r: arm_r.rotation.x = -punch*2.0
  if arm_l: arm_l.rotation.x = -0.7
  if torso: torso.rotation.y = punch * -.45
  if attack in ["kick","air"]:
   if leg_r: leg_r.rotation.x = -punch*1.9
  if attack == "heavy":
   if arm_l: arm_l.rotation.x = -punch*2.5
   if arm_r: arm_r.rotation.x = -punch*2.5
  if attack == "spin":
   if arm_l: arm_l.rotation.z = -1.5
   if arm_r: arm_r.rotation.z = 1.5
