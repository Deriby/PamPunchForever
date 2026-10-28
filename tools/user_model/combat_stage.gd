extends Node3D
## Standalone animation review; use F6 on scenes/pam_combat_review.tscn.
const Flourish = preload("res://scripts/combat_flourish.gd")
@export var autoplay := true
@export var show_controls := true
var skeleton: Skeleton3D
var player: AnimationPlayer
var body: MeshInstance3D
var effects: CombatFlourish
var camera: Camera3D
var clip := "Combo"
var clock := 0.0
var paused := false
var caption: Label

func discover(node: Node) -> void:
	if node is Skeleton3D:
		skeleton = node
	if node is AnimationPlayer:
		player = node
	if node is MeshInstance3D:
		body = node
	for child in node.get_children():
		discover(child)

func _ready() -> void:
	var background := WorldEnvironment.new()
	background.environment = Environment.new()
	background.environment.background_mode = Environment.BG_COLOR
	background.environment.background_color = Color("526861")
	background.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	background.environment.ambient_light_color = Color(.84,.90,1)
	background.environment.ambient_light_energy = .65
	background.environment.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	add_child(background)
	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-35,-30,0)
	key.light_energy = 1.05
	add_child(key)
	var fill := DirectionalLight3D.new()
	fill.rotation_degrees = Vector3(-20,150,0)
	fill.light_energy = .38
	fill.light_color = Color(.88,.94,1)
	add_child(fill)
	var model := preload("res://assets/models/pam_usuario_rig.glb").instantiate()
	add_child(model)
	discover(model)
	effects = Flourish.new()
	add_child(effects)
	camera = Camera3D.new()
	add_child(camera)
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.size = 2.15
	camera.position = Vector3(5,1.6,4)
	camera.look_at(Vector3(0,.77,0))
	camera.current = true
	player.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	if show_controls:
		var layer := CanvasLayer.new()
		add_child(layer)
		caption = Label.new()
		caption.position = Vector2(25,20)
		caption.add_theme_font_size_override("font_size",22)
		layer.add_child(caption)
		var help := Label.new()
		help.position = Vector2(25,58)
		help.text = "Revisão: 1 Combo   2 Giro   3 Médio   4 Forte   5 Pulo   0 T-pose\nEspaço: pausar   ← →: quadro   V: frente / lado"
		help.add_theme_font_size_override("font_size",16)
		layer.add_child(help)
	sample("Combo",0)

func sample(name: String, time: float) -> void:
	clip = name
	clock = time
	player.play(clip)
	player.seek(time,true)
	player.pause()
	skeleton.force_update_all_bone_transforms()
	effects.sample(skeleton,clip,time)
	if caption:
		caption.text = "PAM · "+{"Combo":"Giro → médio → forte", "Spin":"Giro", "Medium":"Soco médio", "Strong":"Soco forte", "Jump":"Pulo"}.get(clip,clip)

func _process(delta: float) -> void:
	if not autoplay or paused:
		return
	var end := player.get_animation(clip).length
	var next := clock+delta
	if next > end+.3:
		next = 0
	sample(clip,minf(next,end))
	# Keep the short end pause separate from the sampled (clamped) clip time.
	clock = next

func _unhandled_key_input(event: InputEvent) -> void:
	if not event is InputEventKey or not event.pressed or event.echo:
		return
	var keys := {KEY_1:"Combo",KEY_2:"Spin",KEY_3:"Medium",KEY_4:"Strong",KEY_5:"Jump"}
	if keys.has(event.keycode):
		paused = false
		sample(keys[event.keycode],0)
	elif event.keycode == KEY_SPACE:
		paused = not paused
	elif event.keycode in [KEY_LEFT,KEY_RIGHT]:
		paused = true
		var step := 1.0/30 if event.keycode == KEY_RIGHT else -1.0/30
		sample(clip,clampf(clock+step,0,player.get_animation(clip).length))
	elif event.keycode == KEY_0:
		paused = true
		player.stop()
		skeleton.reset_bone_poses()
		skeleton.force_update_all_bone_transforms()
		effects.clear()
		if caption:
			caption.text = "PAM · T-pose original"
	elif event.keycode == KEY_V:
		camera.position = Vector3(6,1.55,1.5) if camera.position.z > 2 else Vector3(5,1.6,4)
		camera.look_at(Vector3(0,.77,0))
