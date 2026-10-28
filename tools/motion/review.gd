extends SceneTree
## Native animation review, independently sampled from actual exported skins.
const Pam = preload("res://scripts/pam_animator.gd")
const Npc = preload("res://scripts/npc_animator.gd")
var output := OS.get_environment("PAM_MOTION_OUTPUT")
var actors: Dictionary = {}
var viewport: SubViewport
var report: Dictionary = {}

func _initialize() -> void:
	create_timer(500).timeout.connect(func(): push_error("Motion review timeout"); quit(2))
	call_deferred("review")

func sample(role: String, clip: String, time: float) -> void:
	var actor: Node3D = actors[role]
	if role == "pam": actor.sample_motion(clip,time,.1)
	else: actor.pose(clip,time,false)

func validate(role: String) -> bool:
	var actor: Node3D = actors[role]
	var skeleton: Skeleton3D = actor.skeleton
	var player: AnimationPlayer = actor.player
	var clips := ["Guard","Run","JumpStart","Rise","Fall","Land","Hit","HitHeavy","Death","DeathBack","DeathFall","Jump"]
	if role != "pam": clips.append("Defeat")
	for clip in clips:
		assert(player.has_animation(clip))
		var duration := player.get_animation(clip).length
		assert(duration > .09)
		for fraction in [0.0,.11,.37,.71,1.0]:
			sample(role,clip,duration*fraction)
			for index in range(skeleton.get_bone_count()):
				var pose := skeleton.get_bone_global_pose(index)
				assert(pose.origin.is_finite() and pose.basis.is_finite())
	var hip := skeleton.find_bone("hips")
	var head := skeleton.find_bone("head")
	var root_bone := skeleton.find_bone("root")
	sample(role,"Land",0)
	var hip_before := skeleton.get_bone_global_pose(hip).origin.y
	sample(role,"Land",.05)
	var compression := hip_before-skeleton.get_bone_global_pose(hip).origin.y
	assert(compression > .035,"Landing must compress the body")
	sample(role,"Hit",0)
	var head_before := skeleton.get_bone_global_pose(head).basis.get_rotation_quaternion()
	sample(role,"Hit",.10)
	var recoil := rad_to_deg(head_before.angle_to(skeleton.get_bone_global_pose(head).basis.get_rotation_quaternion()))
	assert(recoil > 5,"Damage must move the actual skeleton")
	sample(role,"Death",0)
	var root_before := skeleton.get_bone_global_pose(root_bone).basis.get_rotation_quaternion()
	sample(role,"Death",1.2)
	var collapse := rad_to_deg(root_before.angle_to(skeleton.get_bone_global_pose(root_bone).basis.get_rotation_quaternion()))
	assert(collapse > 65,"Death must reach a fallen pose")
	report[role] = {"clips":player.get_animation_list(),"landing_compression":compression,"head_recoil_degrees":recoil,"death_rotation_degrees":collapse}
	return true

func review() -> void:
	if output.is_empty(): output = ProjectSettings.globalize_path("res://build/motion_review/")
	output = output.trim_suffix("/")+"/"
	DirAccess.make_dir_recursive_absolute(output)
	viewport = SubViewport.new()
	viewport.size = Vector2i(1280,720)
	viewport.own_world_3d = true
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	viewport.msaa_3d = Viewport.MSAA_2X
	root.add_child(viewport)
	var world := Node3D.new()
	viewport.add_child(world)
	var environment := WorldEnvironment.new()
	environment.environment = Environment.new()
	environment.environment.background_mode = Environment.BG_COLOR
	environment.environment.background_color = Color("526861")
	environment.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.environment.ambient_light_color = Color(.84,.90,1)
	environment.environment.ambient_light_energy = .65
	world.add_child(environment)
	for config in [[Vector3(-35,-30,0),1.05],[Vector3(-20,150,0),.38]]:
		var light := DirectionalLight3D.new()
		light.rotation_degrees = config[0]
		light.light_energy = config[1]
		world.add_child(light)
	var camera := Camera3D.new()
	world.add_child(camera)
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.size = 3.8
	camera.position = Vector3(0,2.5,8)
	camera.look_at(Vector3(0,1,0))
	camera.current = true
	var index := 0
	for role in ["pam","januri","inimigo","lar"]:
		var actor: Node3D = Pam.new() if role == "pam" else Npc.new()
		if role != "pam": actor.character = role
		world.add_child(actor)
		actor.position.x = (index-1.5)*1.6
		actor.rotation.y = .25
		actors[role] = actor
		if not validate(role):
			push_error("Motion validation failed: "+role)
			quit(2)
			return
		index += 1
	print("MOTION_CLIPS_CHECKED ",JSON.stringify(report))
	if not "--validate-only" in OS.get_cmdline_user_args():
		for frame in range(186):
			var time := frame/30.0
			var clip := "Guard"
			var local_time := time
			if time >= .6 and time < 1.4: clip = "Run"; local_time = time-.6
			elif time >= 1.4 and time < 2.2: clip = "Jump"; local_time = time-1.4
			elif time >= 2.2 and time < 2.65: clip = "Hit"; local_time = time-2.2
			elif time >= 2.65 and time < 3.35: clip = "HitHeavy"; local_time = time-2.65
			elif time >= 3.35 and time < 4.95: clip = "Death"; local_time = time-3.35
			elif time >= 4.95 and time < 5.75: clip = "DeathFall"; local_time = time-4.95
			for role in actors: sample(role,clip,local_time)
			await process_frame
			await RenderingServer.frame_post_draw
			if viewport.get_texture().get_image().save_png(output+"motion_%03d.png" % frame) != OK:
				quit(2)
				return
		report["captures"] = 186
	report["engine"] = Engine.get_version_info().string
	var file := FileAccess.open(output+"native-motion-report.json",FileAccess.WRITE)
	file.store_string(JSON.stringify(report,"\t"))
	file.close()
	print("MOTION_REVIEW_OK")
	viewport.queue_free()
	await process_frame
	PamArt.library.clear(); PamArt.mats.clear()
	quit()
