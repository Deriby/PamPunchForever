class_name PamAnimator
extends Node3D
## The supplied skin, sampled on physics time so visible fists and hits agree.
const MOVES = preload("res://resources/combat_moves.tres")
const Flourish = preload("res://scripts/combat_flourish.gd")
var model: Node3D
var skeleton: Skeleton3D
var player: AnimationPlayer
var effects: CombatFlourish
var current_clip := ""
var blend_from: Array[Transform3D] = []
var blend_clock := 0.0
var locomotion_clock := 0.0
var previous_time := 0.0

func _ready() -> void:
	model = preload("res://assets/models/pam_usuario_rig.glb").instantiate()
	add_child(model)
	discover(model)
	player.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	effects = Flourish.new()
	effects.show_accents = false
	add_child(effects)
	sample_state("",0,0,0,false)

func discover(node: Node) -> void:
	if node is Skeleton3D:
		skeleton = node
	if node is AnimationPlayer:
		player = node
	for child in node.get_children():
		discover(child)

func sample_state(attack: String, time: float, delta: float, speed: float, airborne: bool) -> void:
	locomotion_clock += delta*(1.2+speed*.35)
	var clip := "Jump" if airborne else ("Run" if speed > .2 else "Guard")
	var sample_time := fmod(locomotion_clock,player.get_animation(clip).length)
	if not attack.is_empty():
		clip = MOVES.move(attack)["clip"]
		sample_time = MOVES.clip_time(attack,time)
	sample_pose(clip,sample_time,delta)
	if attack.is_empty():
		effects.clear()
	else:
		effects.sample(skeleton,clip,sample_time)

func sample_motion(clip: String, time: float, delta: float, loop: bool = false) -> void:
	var duration := player.get_animation(clip).length
	var sample_time := fmod(time,duration) if loop else clampf(time,0,duration)
	sample_pose(clip,sample_time,delta)
	effects.clear()

func sample_pose(clip: String, sample_time: float, delta: float) -> void:
	if clip != current_clip:
		blend_from.clear()
		if not current_clip.is_empty():
			for index in range(skeleton.get_bone_count()):
				blend_from.append(skeleton.get_bone_pose(index))
		current_clip = clip
		blend_clock = 0
	previous_time = sample_time
	player.play(clip)
	player.seek(sample_time,true)
	player.pause()
	blend_clock += delta
	var weight := clampf(blend_clock/float(MOVES.data["blend_time"]),0,1)
	if weight < 1 and not blend_from.is_empty():
		for index in range(skeleton.get_bone_count()):
			skeleton.set_bone_pose(index,blend_from[index].interpolate_with(skeleton.get_bone_pose(index),weight))
	skeleton.force_update_all_bone_transforms()

func fist_position(name: String) -> Vector3:
	return effects.to_global(effects.tip(skeleton,name))

func reset_motion() -> void:
	effects.clear()
	blend_from.clear()
	current_clip = ""
	sample_state("",0,0,0,false)
