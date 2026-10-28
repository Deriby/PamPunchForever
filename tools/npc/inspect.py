"""Inspect and render supplied NPCs before choosing any rig landmarks."""
import bpy
import json
import os
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(os.environ.get('PAM_NPC_REVIEW_OUTPUT',ROOT/'build/npc_review'))
OUT.mkdir(parents=True,exist_ok=True)
report = {}
for role in ['januri','inimigo','lar']:
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(ROOT/f'assets/source/npcs/{role}_original.glb'))
    body = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
    body.data.transform(body.matrix_world)
    body.matrix_world.identity()
    lo = Vector(tuple(min(v.co[i] for v in body.data.vertices) for i in range(3)))
    hi = Vector(tuple(max(v.co[i] for v in body.data.vertices) for i in range(3)))
    report[role] = {'vertices':len(body.data.vertices),'triangles':len(body.data.polygons),
                    'min':list(lo),'max':list(hi),'materials':[m.name for m in body.data.materials]}
    print('NPC_INSPECT',role,json.dumps(report[role]),flush=True)
    # Work in a common 1.8 m stage only for camera/landmark comparison.
    factor = 1.8/(hi.z-lo.z)
    body.location.z = -lo.z*factor
    body.scale = (factor,)*3
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 8
    scene.cycles.use_denoising = False
    scene.render.resolution_x,scene.render.resolution_y = 640,800
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.film_transparent = True
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.22,.25,.30,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = .65
    scene.view_settings.view_transform = 'AgX'
    for name,point,energy,size in [('Key',(-3,-4,5),500,4),('Fill',(3,-1,3),220,3),('Rim',(0,4,4),350,3)]:
        data = bpy.data.lights.new(name,'AREA')
        data.energy,data.size = energy,size
        light = bpy.data.objects.new(name,data)
        scene.collection.objects.link(light)
        light.location = point
        light.rotation_euler = (Vector((0,0,.9))-light.location).to_track_quat('-Z','Y').to_euler()
    data = bpy.data.cameras.new('Inspection')
    camera = bpy.data.objects.new('Inspection',data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    data.type,data.ortho_scale = 'ORTHO',2.3
    for name,point in [('front',(0,-7,1.1)),('back',(0,7,1.1)),('side',(7,0,1.1))]:
        camera.location = point
        camera.rotation_euler = (Vector((0,0,.9))-camera.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath = str(OUT/f'{role}_{name}.png')
        bpy.ops.render.render(write_still=True)
(OUT/'inspection.json').write_text(json.dumps(report,indent=2)+'\n')
print('NPC_INSPECTION_OK')
