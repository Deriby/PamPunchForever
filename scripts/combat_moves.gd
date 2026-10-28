class_name PamCombatMoves
extends Resource
## Shared by the player, animation controller and Blender authoring tools.
@export var data: Dictionary = {}

func order() -> Array:
	return data["order"]

func move(kind: String) -> Dictionary:
	return data["moves"][kind]

func clip_time(kind: String, time: float) -> float:
	var info := move(kind)
	var times: Array = [0.0,info["windup"],info["active_end"],info["duration"]]
	var frames: Array = info["clip_frames"]
	for i in range(3):
		if time <= float(times[i+1]):
			return lerpf(float(frames[i]),float(frames[i+1]),clampf((time-float(times[i]))/(float(times[i+1])-float(times[i])),0,1))/30.0
	return float(frames[3])/30.0
