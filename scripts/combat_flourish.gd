class_name CombatFlourish
extends Node3D
## Small mesh strokes at the wrists/foot. No mesh or rest-pose edits.
## sample() uses clip time, so pause, slow motion and frame stepping stay in sync.

const WINDOWS := {
	"Jab": [[4, 11, "hand.R"]],
	"Cross": [[5, 12, "hand.L"]],
	"Kick": [[7, 16, "foot.R"]],
	"Combo": [[4, 11, "hand.R"], [14, 22, "hand.L"], [28, 38, "foot.R"]],
	"Spin": [[9, 28, "hand.R"], [9, 28, "hand.L"]]
}
const ACCENTS := {
	"Jab": [[6, "hand.R"]], "Cross": [[7, "hand.L"]],
	"Kick": [[9, "foot.R"]], "Combo": [[6, "hand.R"], [16, "hand.L"], [30, "foot.R"]]
}
var mesh := ImmediateMesh.new()
var surface := MeshInstance3D.new()
var paths: Dictionary = {}
var accents: Array[Dictionary] = []
var last_clip := ""
var last_time := -1.0
var stroke_count := 0
var accent_count := 0

func _ready() -> void:
	var material := StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.vertex_color_use_as_albedo = true
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	material.cull_mode = BaseMaterial3D.CULL_DISABLED
	material.no_depth_test = false
	surface.mesh = mesh
	surface.material_override = material
	surface.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(surface)

func clear() -> void:
	paths.clear()
	accents.clear()
	mesh.clear_surfaces()
	last_time = -1.0
	stroke_count = 0
	accent_count = 0

func tip(skeleton: Skeleton3D, name: String) -> Vector3:
	var index := skeleton.find_bone(name)
	var pose := skeleton.global_transform * skeleton.get_bone_global_pose(index)
	# Godot may realign imported bone axes. Transform the known distal direction
	# of this T-pose through the bind basis instead of assuming bone-local Y.
	var distal := Vector3(0,0,.17)
	if name.begins_with("hand"):
		distal = Vector3(-.17 if name.ends_with("L") else .17,0,0)
	var local_tip := skeleton.get_bone_global_rest(index).basis.inverse()*distal
	return to_local(pose*local_tip)

func triangle(a: Vector3, b: Vector3, c: Vector3, color: Color) -> void:
	mesh.surface_set_color(color)
	mesh.surface_add_vertex(a)
	mesh.surface_add_vertex(b)
	mesh.surface_add_vertex(c)

func ribbon(points: Array, color: Color, width: float) -> void:
	for i in range(1, points.size()):
		var a: Vector3 = points[i-1]["point"]
		var b: Vector3 = points[i]["point"]
		var tangent := b-a
		if tangent.length_squared() < .00002:
			continue
		var view := to_local(get_viewport().get_camera_3d().global_position)-(a+b)*.5
		var side := tangent.cross(view).normalized()
		if side.length_squared() < .1:
			side = Vector3.RIGHT
		var old_width := width*float(i-1)/points.size()
		var new_width := width*float(i)/points.size()
		triangle(a-side*old_width, a+side*old_width, b+side*new_width, color)
		triangle(a-side*old_width, b+side*new_width, b-side*new_width, color)

func sample(skeleton: Skeleton3D, clip: String, time: float) -> void:
	if clip != last_clip or time < last_time or time-last_time > .12:
		clear()
	last_clip = clip
	mesh.clear_surfaces()
	var frame := time*30.0
	var advanced := time > last_time+.00001
	for window in WINDOWS.get(clip, []):
		var name: String = window[2]
		if not paths.has(name):
			paths[name] = []
		var points: Array = paths[name]
		if advanced and frame >= window[0] and frame <= window[1]:
			points.append({"point":tip(skeleton,name), "time":time})
		while not points.is_empty() and time-float(points[0]["time"]) > .105:
			points.pop_front()
	for marker in ACCENTS.get(clip, []):
		var at := float(marker[0])/30.0
		if advanced and last_time < at and time >= at:
			accents.append({"point":tip(skeleton,marker[1]), "time":at})
	accents = accents.filter(func(a: Dictionary) -> bool: return time-float(a["time"]) <= .125)
	stroke_count = 0
	for points: Array in paths.values():
		if points.size() > 1:
			stroke_count += 1
	accent_count = accents.size()
	if stroke_count == 0 and accent_count == 0:
		last_time = time
		return
	mesh.surface_begin(Mesh.PRIMITIVE_TRIANGLES)
	for points: Array in paths.values():
		ribbon(points,Color(1,.67,.24,.50),.038)
		ribbon(points,Color(1,.95,.73,.86),.013)
	# An animation accent, deliberately smaller than the fist. Gameplay contact
	# effects must call their hit-confirmed path; these markers apply no damage.
	for accent: Dictionary in accents:
		var age := clampf((time-float(accent["time"]))/ .125,0,1)
		var center: Vector3 = accent["point"]
		var radius := lerpf(.070,.16,age)
		var alpha := 1.0-age
		var camera_basis := global_basis.inverse()*get_viewport().get_camera_3d().global_basis
		for i in range(5):
			var angle := i*TAU/5.0
			var dir := camera_basis*Vector3(cos(angle),sin(angle),0)
			var cross := camera_basis*Vector3(-sin(angle),cos(angle),0)*.016*(1-age*.6)
			triangle(center+dir*.035-cross,center+dir*radius,center+dir*.035+cross,Color(1,.87,.45,alpha))
	mesh.surface_end()
	last_time = time
