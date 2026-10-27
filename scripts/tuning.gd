class_name PamTuning
extends Resource

# Valores originais em metros e segundos; nenhuma conversão de inteiros PS1.
@export var top_speed: float = 5.4
@export var acceleration: float = 30.0
@export var braking: float = 36.0
@export var air_acceleration: float = 13.0
@export var gravity: float = 25.0
@export var jump_speed: float = 9.1
@export var terminal_speed: float = 24.0
@export var jump_release_speed: float = 3.4
@export var coyote_time: float = 0.10
@export var jump_buffer: float = 0.12
@export var dodge_speed: float = 10.0
@export var camera_response: float = 6.0

# windup, active, recovery, damage, knockback, radius
const ATTACKS = {
 "jab": [0.065, 0.12, 0.14, 1, 3.0, 0.67],
 "cross": [0.085, 0.13, 0.16, 1, 4.0, 0.72],
 "kick": [0.12, 0.16, 0.24, 2, 7.0, 0.86],
 "heavy": [0.25, 0.17, 0.30, 3, 9.0, 0.86],
 "spin": [0.14, 0.30, 0.32, 2, 6.0, 1.12],
 "air": [0.10, 0.22, 0.24, 2, 5.0, 0.85]
}
