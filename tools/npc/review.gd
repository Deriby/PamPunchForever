extends SceneTree
## Verify the actual exported NPC skins and render their native animation clips.
const Animator = preload("res://scripts/npc_animator.gd")
var output := OS.get_environment("PAM_NPC_REVIEW_OUTPUT")
const EXPECTED := {"januri":[25,50004,1.8],"inimigo":[32,50000,1.7],"lar":[30,50000,1.9]}
var viewport: SubViewport
var npcs: Dictionary = {}
var report: Dictionary = {}

func _initialize() -> void:
	create_timer(220).timeout.connect(func(): push_error("NPC review timed out"); quit(2))
	call_deferred("review")

func mesh_in(node: Node) -> MeshInstance3D:
	if node is MeshInstance3D:
		return node
	for child in node.get_children():
		var found := mesh_in(child)
		if found:
			return found
	return null

func validate(npc: PamNpcAnimator, role: String) -> bool:
	var skeleton := npc.skeleton
	var body := mesh_in(npc.model)
	assert(skeleton.get_bone_count() == EXPECTED[role][0])
	assert(body.skin != null and body.get_node(body.skeleton) == skeleton)
	var material := body.mesh.surface_get_material(0) as StandardMaterial3D
	assert(material != null and material.albedo_texture.get_size() == Vector2(4096,4096))
	assert(material.normal_enabled and material.normal_texture != null and material.roughness_texture != null)
	assert(absf(body.mesh.get_aabb().size.y-float(EXPECTED[role][2])) < .002)
	var arrays := body.mesh.surface_get_arrays(0)
	assert(arrays[Mesh.ARRAY_INDEX].size()/3 == EXPECTED[role][1])
	for vertex in range(arrays[Mesh.ARRAY_VERTEX].size()):
		var total := 0.0
		for slot in range(4):
			var weight: float = arrays[Mesh.ARRAY_WEIGHTS][vertex*4+slot]
			var joint: int = arrays[Mesh.ARRAY_BONES][vertex*4+slot]
			assert(weight >= 0 and joint >= 0 and joint < body.skin.get_bind_count())
			total += weight
		assert(absf(total-1) < .0002,"Every vertex must be skinned and normalized")
	for clip in ["Idle","Guard","Walk","Run","Windup","Attack","Hit","Defeat","Power","ElbowFlex","KneeFlex"]:
		assert(npc.player.has_animation(clip))
		for fraction in [0.0,.37,.71,1.0]:
			npc.pose(clip,fraction*npc.length(clip),false)
			for index in range(skeleton.get_bone_count()):
				var transform := skeleton.get_bone_global_pose(index)
				assert(transform.origin.is_finite() and transform.basis.is_finite())
	var joints := {}
	for side in ["L","R"]:
		var shin := skeleton.find_bone("shin."+side)
		var thigh := skeleton.find_bone("thigh."+side)
		var ankle := skeleton.find_bone("foot."+side)
		assert(skeleton.get_bone_parent(shin) == thigh and skeleton.get_bone_parent(ankle) == shin)
		npc.pose("KneeFlex",0,false)
		var fixed := skeleton.get_bone_global_pose(thigh)
		var before := skeleton.get_bone_pose_rotation(shin)
		var foot := skeleton.get_bone_global_pose(ankle).origin
		npc.pose("KneeFlex",.4 if side == "R" else 1.4,false)
		var angle := rad_to_deg(before.angle_to(skeleton.get_bone_pose_rotation(shin)))
		assert(absf(angle-90) < 1)
		assert(fixed.is_equal_approx(skeleton.get_bone_global_pose(thigh)))
		assert(foot.distance_to(skeleton.get_bone_global_pose(ankle).origin) > .15)
		joints["knee_"+side] = angle
	var forearm := skeleton.find_bone("forearm.R")
	var upper := skeleton.find_bone("upper_arm.R")
	var hand := skeleton.find_bone("hand.R")
	npc.pose("ElbowFlex",0,false)
	var fixed := skeleton.get_bone_global_pose(upper)
	var before := skeleton.get_bone_pose_rotation(forearm)
	var wrist := skeleton.get_bone_global_pose(hand).origin
	npc.pose("ElbowFlex",.4,false)
	var elbow := rad_to_deg(before.angle_to(skeleton.get_bone_pose_rotation(forearm)))
	assert(absf(elbow-90) < 1 and fixed.is_equal_approx(skeleton.get_bone_global_pose(upper)))
	assert(wrist.distance_to(skeleton.get_bone_global_pose(hand).origin) > .15)
	joints["elbow_R"] = elbow
	var tails := {}
	for prefix in (["tail.L","tail.R"] if role == "inimigo" else (["tail"] if role == "lar" else [])):
		var index := skeleton.find_bone(prefix+".01")
		assert(index >= 0)
		npc.pose("Idle",0,false)
		var first := skeleton.get_bone_pose_rotation(index)
		npc.pose("Idle",.25,false)
		var angle := rad_to_deg(first.angle_to(skeleton.get_bone_pose_rotation(index)))
		assert(angle > 1)
		tails[prefix] = angle
	var max_rigid_error := 0.0
	for name in (["shell","hat","beard"] if role == "januri" else (["hat","sheath"] if role == "lar" else [])):
		var index := skeleton.find_bone(name)
		assert(index >= 0)
		for time in [0.0,.12,.30]:
			npc.pose("Attack",time,false)
			var basis := (skeleton.get_bone_global_pose(index)*skeleton.get_bone_global_rest(index).affine_inverse()).basis
			max_rigid_error = maxf(max_rigid_error,basis.get_scale().distance_to(Vector3.ONE))
	assert(max_rigid_error < .001,"Rigid accessories must not collapse or stretch")
	npc.pose("Attack",.12,false)
	var contact := npc.contact_point()-npc.global_position
	report[role] = {"bones":skeleton.get_bone_count(),"triangles":EXPECTED[role][1],
		"clips":npc.player.get_animation_list(),"joint_angles":joints,"tail_motion_degrees":tails,
		"max_rigid_scale_error":max_rigid_error,"pbr_size":[4096,4096],"attack_contact":[contact.x,contact.y,contact.z]}
	npc.pose("Idle",0,false)
	return true

func review() -> void:
	if output.is_empty(): output = ProjectSettings.globalize_path("res://build/npc_review/")
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
	var background := WorldEnvironment.new()
	background.environment = Environment.new()
	background.environment.background_mode = Environment.BG_COLOR
	background.environment.background_color = Color("526861")
	background.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	background.environment.ambient_light_color = Color(.84,.90,1)
	background.environment.ambient_light_energy = .65
	background.environment.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	world.add_child(background)
	for setting in [[Vector3(-35,-30,0),1.05],[Vector3(-20,150,0),.38]]:
		var light := DirectionalLight3D.new()
		light.rotation_degrees = setting[0]
		light.light_energy = setting[1]
		world.add_child(light)
	var camera := Camera3D.new()
	world.add_child(camera)
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.size = 3.15
	camera.position = Vector3(0,2.1,8)
	camera.look_at(Vector3(0,.95,0))
	camera.current = true
	var column := 0
	for role: String in EXPECTED:
		var npc := Animator.new()
		npc.character = role
		world.add_child(npc)
		npc.position.x = (column-1)*1.8
		npcs[role] = npc
		column += 1
		if not validate(npc,role):
			push_error("NPC validation failed: "+role)
			quit(2)
			return
	print("NPC_RIG_CHECKS_OK ",JSON.stringify(report))
	if not "--validate-only" in OS.get_cmdline_user_args():
		for frame in range(0 if "--stills-only" in OS.get_cmdline_user_args() else 90):
			var time := frame/30.0
			for role: String in npcs:
				var npc: PamNpcAnimator = npcs[role]
				if time < .4: npc.pose("Guard",time)
				elif time < .9: npc.pose("Windup",(time-.4)/.5*npc.length("Windup"))
				elif time < 1.47: npc.pose("Attack",time-.9)
				elif time < 2.4:
					if role == "januri": npc.pose("Power",(time-1.47)/.93*npc.length("Power"))
					else: npc.pose("Run",(time-1.47)*1.3)
				else: npc.pose("Idle",time-2.4)
			await process_frame
			await RenderingServer.frame_post_draw
			if viewport.get_texture().get_image().save_png(output+"showcase_%03d.png" % frame) != OK:
				quit(2)
				return
		for setting in [["guard","Guard",0.0,0.0],["attack","Attack",.12,.5],["run","Run",.1,.5],["elbows","ElbowFlex",.4,.5],["knees","KneeFlex",.4,.5],["defeat","Defeat",1.1,.5],["side","Guard",.2,PI/2],["back","Guard",.2,PI],["rest","",0.0,0.0]]:
			for role: String in npcs:
				var npc: PamNpcAnimator = npcs[role]
				npc.rotation.y = setting[3]
				if setting[1] == "": npc.bind_pose()
				else: npc.pose(setting[1],setting[2],false)
			await process_frame
			await RenderingServer.frame_post_draw
			if viewport.get_texture().get_image().save_png(output+setting[0]+".png") != OK:
				quit(2)
				return
		report["captures"] = 9 if "--stills-only" in OS.get_cmdline_user_args() else 99
	report["engine"] = Engine.get_version_info().string
	var file := FileAccess.open(output+"godot-report.json",FileAccess.WRITE)
	file.store_string(JSON.stringify(report,"\t"))
	file.close()
	print("NPC_REVIEW_OK ",JSON.stringify(report))
	viewport.queue_free()
	await process_frame
	PamArt.library.clear()
	PamArt.mats.clear()
	quit()
