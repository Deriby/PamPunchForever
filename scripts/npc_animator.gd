class_name PamNpcAnimator
extends Node3D
## Native FK skins for the supplied master, ordinary ninjas and Lar.
@export_enum("januri","inimigo","lar") var character := "inimigo"
var model: Node3D
var skeleton: Skeleton3D
var player: AnimationPlayer
var current_clip := ""
var previous_time := 0.0
var blend_clock := 0.0
var blend_from: Array[Transform3D] = []

func _ready() -> void:
	model = PamArt.model("npc_%s_rig" % character)
	add_child(model)
	discover(model)
	assert(skeleton != null and player != null,"NPC rig must contain skin and animation")
	player.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	pose("Idle",0)

func discover(node: Node) -> void:
	if node is Skeleton3D:
		skeleton = node
	if node is AnimationPlayer:
		player = node
	for child in node.get_children():
		discover(child)

func length(clip: String) -> float:
	return player.get_animation(clip).length

func pose(clip: String, time: float, transition: bool = true) -> void:
	assert(player.has_animation(clip),"Missing NPC clip "+clip)
	var changed := clip != current_clip or time < previous_time
	if changed:
		blend_from.clear()
		if not current_clip.is_empty() and transition:
			for index in range(skeleton.get_bone_count()):
				blend_from.append(skeleton.get_bone_pose(index))
		blend_clock = 0
		current_clip = clip
	else:
		blend_clock += maxf(0,time-previous_time)
	previous_time = time
	var sample_time := fmod(time,length(clip)) if clip in ["Idle","Guard","Walk","Run"] else clampf(time,0,length(clip))
	player.play(clip)
	player.seek(sample_time,true)
	player.pause()
	var weight := clampf(blend_clock/.055,0,1)
	if transition and weight < 1 and not blend_from.is_empty():
		for index in range(skeleton.get_bone_count()):
			skeleton.set_bone_pose(index,blend_from[index].interpolate_with(skeleton.get_bone_pose(index),weight))
	skeleton.force_update_all_bone_transforms()

func contact_point(name: String = "hand.R") -> Vector3:
	var index := skeleton.find_bone(name)
	var rest := skeleton.get_bone_global_rest(index)
	var distal := Vector3(-.15 if name.ends_with("L") else .15,0,0)
	var point := skeleton.get_bone_global_pose(index)*(rest.basis.inverse()*distal)
	return skeleton.to_global(point)

func bind_pose() -> void:
	player.stop()
	skeleton.reset_bone_poses()
	skeleton.force_update_all_bone_transforms()
	current_clip = ""
	blend_from.clear()
