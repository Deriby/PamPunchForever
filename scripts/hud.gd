class_name PamHUD
extends CanvasLayer

var trail: Node
var root: Control
var title: Control
var overlay: Control
var stats: Label
var health: Label
var hint: Label
var toast_title: Label
var toast_body: Label
var debug_label: Label
var cinema: Control
var subtitle: Label
var speaker: Label
var ending: Control
var pause_panel: Control
var toast_time := 0.0
var debug_on := false
var fade: ColorRect
var cream := Color("f4e6c8")
var gold := Color("ebba65")
var muted := Color("9cbaab")
var body_font := preload("res://assets/fonts/body.ttf")
var title_font := preload("res://assets/fonts/title.ttf")

func rect(parent: Node, pos: Vector2, size: Vector2, color: Color) -> ColorRect:
 var r := ColorRect.new()
 r.position = pos; r.size = size; r.color = color
 r.mouse_filter = Control.MOUSE_FILTER_IGNORE
 parent.add_child(r)
 return r

func text(parent: Node, value: String, pos: Vector2, size: Vector2, font_size: int, color: Color, serif: bool = false) -> Label:
 var l := Label.new()
 l.text = value; l.position = pos; l.size = size
 l.add_theme_font_override("font",title_font if serif else body_font)
 l.add_theme_font_size_override("font_size",font_size)
 l.add_theme_color_override("font_color",color)
 l.add_theme_color_override("font_shadow_color",Color(0,0,0,.7))
 l.add_theme_constant_override("shadow_offset_y",2)
 l.mouse_filter = Control.MOUSE_FILTER_IGNORE
 parent.add_child(l)
 return l

func button(parent: Node, value: String, pos: Vector2, callback: Callable) -> Button:
 var b := Button.new()
 b.position = pos; b.size = Vector2(330,48); b.text = value
 b.add_theme_font_override("font",body_font)
 b.add_theme_font_size_override("font_size",17)
 b.add_theme_color_override("font_color",cream)
 var style := StyleBoxFlat.new()
 style.bg_color = Color("a33c2f")
 style.border_color = gold
 style.border_width_left = 3
 style.content_margin_left = 20
 b.add_theme_stylebox_override("normal",style)
 var hover := style.duplicate()
 hover.bg_color = Color("bc5138")
 b.add_theme_stylebox_override("hover",hover)
 b.add_theme_stylebox_override("focus",hover)
 parent.add_child(b)
 b.pressed.connect(callback)
 return b

func _ready() -> void:
 process_mode = Node.PROCESS_MODE_ALWAYS
 layer = 10
 root = Control.new()
 add_child(root)
 root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
 root.mouse_filter = Control.MOUSE_FILTER_IGNORE
 overlay = Control.new(); root.add_child(overlay)
 rect(overlay,Vector2(22,20),Vector2(350,75),Color(.025,.07,.065,.85))
 rect(overlay,Vector2(22,20),Vector2(3,75),gold)
 text(overlay,"PAM",Vector2(39,27),Vector2(90,27),20,cream,true)
 text(overlay,"A TRILHA DA VINGANÇA",Vector2(112,31),Vector2(245,24),12,gold)
 health = text(overlay,"",Vector2(39,56),Vector2(300,28),20,Color("ec9b65"))
 stats = text(overlay,"",Vector2(825,27),Vector2(300,66),16,cream)
 stats.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
 hint = text(overlay,"",Vector2(40,656),Vector2(1072,44),16,cream)
 hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
 rect(overlay,Vector2(40,645),Vector2(1072,1),Color(.8,.7,.45,.4))
 toast_title = text(overlay,"",Vector2(60,115),Vector2(1032,35),21,gold,true)
 toast_body = text(overlay,"",Vector2(60,151),Vector2(1032,70),16,cream)
 toast_body.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
 debug_label = text(overlay,"",Vector2(28,220),Vector2(650,120),14,Color("b5ffbb"))
 debug_label.visible = false
 title = Control.new();root.add_child(title)
 rect(title,Vector2.ZERO,Vector2(470,720),Color(.025,.07,.065,.91))
 rect(title,Vector2(48,65),Vector2(45,3),gold)
 text(title,"UMA JORNADA PELA AMAZÔNIA",Vector2(48,85),Vector2(390,35),12,gold)
 text(title,"PAM",Vector2(40,125),Vector2(410,150),112,cream,true)
 text(title,"PUNCH FOREVER",Vector2(48,274),Vector2(390,52),29,Color("ef9b69"),true)
 rect(title,Vector2(48,344),Vector2(330,1),Color(.7,.65,.4,.4))
 text(title,"Um mestre. Uma promessa.\nUm caminho sem volta.",Vector2(48,368),Vector2(370,90),21,cream)
 button(title,"COMEÇAR  /  ENTER",Vector2(48,494),func(): trail.begin_intro())
 text(title,"WASD / analógico  ·  mover\nJ / X  ·  giro → médio → forte\nEspaço / A  ·  pular      Esc  ·  pausa",Vector2(48,567),Vector2(400,80),13,muted)
 text(title,"01  /  A TRILHA DA VINGANÇA",Vector2(48,678),Vector2(390,24),12,gold)
 cinema = Control.new();root.add_child(cinema)
 rect(cinema,Vector2.ZERO,Vector2(1152,58),Color("081310"))
 rect(cinema,Vector2(0,576),Vector2(1152,144),Color(.025,.05,.045,.96))
 speaker = text(cinema,"",Vector2(86,592),Vector2(980,28),15,gold)
 subtitle = text(cinema,"",Vector2(86,626),Vector2(980,65),21,cream)
 subtitle.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
 text(cinema,"ENTER · avançar para o confronto",Vector2(825,20),Vector2(300,24),12,muted)
 ending = Control.new();root.add_child(ending)
 rect(ending,Vector2.ZERO,Vector2(1152,720),Color(.02,.06,.05,.92))
 text(ending,"FIM DA TRILHA  /  INÍCIO DA JORNADA",Vector2(95,100),Vector2(960,40),15,gold)
 text(ending,"A promessa fica.",Vector2(90,178),Vector2(980,100),58,cream,true)
 text(ending,"Pam alcança o antigo porto. Uma marca vermelha nas ruínas\naponta para o próximo destino do assassino.\n\n“Eu vou encontrar você. Mas vou lutar do meu jeito.”",Vector2(95,302),Vector2(980,160),21,cream)
 button(ending,"JOGAR NOVAMENTE  /  R",Vector2(95,568),func(): trail.restart())
 pause_panel = Control.new();root.add_child(pause_panel)
 rect(pause_panel,Vector2.ZERO,Vector2(1152,720),Color(.02,.055,.05,.95))
 text(pause_panel,"Respire, Pam.",Vector2(110,125),Vector2(950,80),52,cream,true)
 text(pause_panel,"WASD / setas / analógico: mover\nJ / X: giro → soco médio → soco forte (pressione a cada golpe)\nEspaço / A: pular (segure para subir mais)\n\nOs mesmos golpes funcionam no ar.\nF3: depuração  ·  R: voltar ao checkpoint\n\nAproxime-se do altar para salvar o checkpoint.\nO brilho dourado leva ao caminho. O verde guarda uma lembrança.",Vector2(110,240),Vector2(950,240),18,cream)
 button(pause_panel,"CONTINUAR  /  ESC",Vector2(110,560),func(): trail.toggle_pause())
 fade = rect(root,Vector2.ZERO,Vector2(1152,720),Color(0,0,0,0))
 show_mode("title")

func show_mode(mode: String) -> void:
 title.visible = mode == "title"
 ending.visible = mode == "ending"
 cinema.visible = mode in ["intro","aftermath"]
 overlay.visible = mode in ["play","duel"]
 pause_panel.visible = false

func _unhandled_input(event: InputEvent) -> void:
 if event.is_action_pressed("pause") and trail.mode in ["play","duel"]:
  trail.toggle_pause()
 if event.is_action_pressed("debug"):
  debug_on = not debug_on
  debug_label.visible = debug_on
 if event.is_action_pressed("confirm"):
  if trail.mode == "title": trail.begin_intro()
  elif trail.mode == "intro": trail.begin_duel()
 if event.is_action_pressed("restart"):
  if trail.mode == "ending": trail.restart()
  elif trail.mode == "play" and not get_tree().paused: trail.player.die()

func _process(delta: float) -> void:
 if not is_instance_valid(trail): return
 var p: PamPlayer = trail.player
 if is_instance_valid(p):
  health.text = "◆ ".repeat(maxi(p.health,0)) + "◇ ".repeat(p.max_health-maxi(p.health,0))
  stats.text = "%02d  SEMENTES\n%s" % [trail.seeds,"LEMBRANÇA ENCONTRADA" if trail.memory_found else "◇  LEMBRANÇA OCULTA"]
  if debug_on:
   debug_label.text = "FPS %d | v %.2f m/s | y %.2f\nPAM %s | câmera %s | trilho %.1f\nCombos %d | acertos %d | checkpoint %s" % [Engine.get_frames_per_second(),p.velocity.length(),p.position.y,p.state,trail.camera.state,trail.camera.offset,p.combo,p.attack_hits,str(trail.checkpoint)]
 if not get_tree().paused:
  toast_time = maxf(0,toast_time-delta)
 toast_title.visible = toast_time > 0
 toast_body.visible = toast_time > 0

func toast(a: String,b: String,duration: float) -> void:
 toast_title.text = a
 toast_body.text = b
 toast_time = duration
