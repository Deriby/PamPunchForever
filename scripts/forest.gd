class_name PamForest
extends Node3D
# Static foliage is grouped into MultiMesh draws; character rigs stay independent.
var placements: Dictionary = {}

func place(key: String, pos: Vector3, size: Vector3, angle: float) -> void:
 if not placements.has(key): placements[key] = []
 var basis := Basis(Vector3.UP,angle).scaled(size)
 placements[key].append(Transform3D(basis,pos))

func bake() -> void:
 for key in placements:
  var source: Node3D = PamArt.model(key)
  var meshes := source.find_children("*","MeshInstance3D",true,false)
  var chunks: Dictionary = {}
  for placement: Transform3D in placements[key]:
   var cell := Vector2i(floori(placement.origin.x/20.0),floori(placement.origin.z/24.0))
   if not chunks.has(cell): chunks[cell] = []
   chunks[cell].append(placement)
  for source_mesh in meshes:
   var mesh := source_mesh as MeshInstance3D
   var local := mesh.transform
   var parent := mesh.get_parent()
   while parent != source and parent is Node3D:
    local = parent.transform*local
    parent = parent.get_parent()
   for cell in chunks:
    var multi := MultiMesh.new()
    multi.transform_format = MultiMesh.TRANSFORM_3D
    multi.mesh = mesh.mesh
    multi.instance_count = chunks[cell].size()
    for i in range(multi.instance_count):
     multi.set_instance_transform(i,chunks[cell][i]*local)
    var inst := MultiMeshInstance3D.new()
    inst.multimesh = multi
    inst.material_override = mesh.material_override
    inst.visibility_range_end = 85.0 if key.begins_with("tree") else 58.0
    inst.visibility_range_end_margin = 5.0
    if key in ["fern","broadleaf","bromeliad","leaf_litter","thicket"]:
     inst.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
    add_child(inst)
  source.free()
 placements.clear()
