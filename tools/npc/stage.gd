extends Node3D
## F6 review of the actual runtime skins, with optional visible skeletons.
const Animator = preload("res://scripts/npc_animator.gd")
var actors: Array[PamNpcAnimator] = []
var clip := "Guard"
var clock := 0.0
var paused := false
var bones: MeshInstance3D
var lines := ImmediateMesh.new()
var caption: Label
var view_angle := 0.0

func _ready() -> void:
	var world := WorldEnvironment.new()
	world.environment = Environment.new()
	world.environment.background_mode = Environment.BG_COLOR
	world.environment.background_color = Color("526861")
	world.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	world.environment.ambient_light_color = Color(.84,.90,1)
	world.environment.ambient_light_energy = .65
	add_child(world)
	for setting in [[Vector3(-35,-30,0),1.05],[Vector3(-20,150,0),.38]]:
		var light := DirectionalLight3D.new()
		light.rotation_degrees = setting[0]
		light.light_energy = setting[1]
		add_child(light)
	var column := 0
	for role in ["januri","inimigo","lar"]:
		var npc := Animator.new()
		npc.character = role
		add_child(npc)
		npc.position.x = (column-1)*1.8
		actors.append(npc)
		column += 1
	var camera := Camera3D.new()
	add_child(camera)
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.size = 3.4
	camera.position = Vector3(0,2.1,8)
	camera.look_at(Vector3(0,.95,0))
	camera.current = true
	bones = MeshInstance3D.new()
	bones.mesh = lines
	var material := StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.albedo_color = Color("8ef5e0")
	material.no_depth_test = true
	bones.material_override = material
	bones.visible = false
	add_child(bones)
	var ui := CanvasLayer.new()
	add_child(ui)
	caption = Label.new()
	caption.position = Vector2(24,15)
	caption.add_theme_font_size_override("font_size",24)
	ui.add_child(caption)
	var help := Label.new()
	help.position = Vector2(24,50)
	help.text = "1 Guarda   2 Andar   3 Correr   4 Soco   5 Golpe forte   6 Reação   7 Derrota\n8 Cotovelo   9 Joelho   0 T-pose   B Ossos   V Girar   Espaço Pausar   ← → Quadro"
	help.add_theme_font_size_override("font_size",16)
	ui.add_child(help)
	var names := HBoxContainer.new()
	names.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	names.offset_top = -48
	ui.add_child(names)
	for name in ["JABURANGA (Januri)","INIMIGO","LAR"]:
		var label := Label.new()
		label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		label.add_theme_font_size_override("font_size",20)
		label.text = name
		names.add_child(label)
	sample()

func sample() -> void:
	for npc in actors:
		if clip.is_empty(): npc.bind_pose()
		else: npc.pose(clip,minf(clock,npc.length(clip)),false)
	caption.text = "ELENCO · "+("T-pose original" if clip.is_empty() else clip)+(" · PAUSADO" if paused else "")
	if bones.visible:
		lines.clear_surfaces()
		lines.surface_begin(Mesh.PRIMITIVE_LINES)
		for npc in actors:
			for index in range(npc.skeleton.get_bone_count()):
				var parent := npc.skeleton.get_bone_parent(index)
				if parent < 0: continue
				for bone in [parent,index]:
					lines.surface_add_vertex(npc.skeleton.to_global(npc.skeleton.get_bone_global_pose(bone).origin))
		lines.surface_end()

func _process(delta: float) -> void:
	if paused or clip.is_empty(): return
	clock += delta
	if clock > actors[0].length(clip)+.35: clock = 0
	sample()

func _unhandled_key_input(event: InputEvent) -> void:
	if not event is InputEventKey or not event.pressed or event.echo: return
	var clips := {KEY_1:"Guard",KEY_2:"Walk",KEY_3:"Run",KEY_4:"Attack",KEY_5:"Power",KEY_6:"Hit",KEY_7:"Defeat",KEY_8:"ElbowFlex",KEY_9:"KneeFlex",KEY_0:""}
	if clips.has(event.keycode):
		clip = clips[event.keycode]
		clock = 0
		paused = clip.is_empty()
	elif event.keycode == KEY_SPACE: paused = not paused
	elif event.keycode in [KEY_LEFT,KEY_RIGHT] and not clip.is_empty():
		paused = true
		clock = clampf(clock+(1.0/30 if event.keycode == KEY_RIGHT else -1.0/30),0,actors[0].length(clip))
	elif event.keycode == KEY_B: bones.visible = not bones.visible
	elif event.keycode == KEY_V:
		view_angle += PI/2
		for npc in actors: npc.rotation.y = view_angle
	sample()
