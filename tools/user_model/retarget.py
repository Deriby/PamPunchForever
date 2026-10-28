"""Shared retarget and planted-foot solver; ordinary baked glTF bones at runtime."""
import bpy
import math
from mathutils import Matrix, Vector

class Retargeter:
    def __init__(self, source, rig):
        self.source, self.rig = source, rig
        self.correction = {}
        for name in self.source.data.bones.keys():
            world_normal = Vector((0,0,1)) if name.startswith(('foot.','toe.')) else Vector((0,-1,0))
            a = self.source.data.bones[name].matrix_local.to_quaternion().inverted() @ world_normal
            b = self.rig.data.bones[name].matrix_local.to_quaternion().inverted() @ world_normal
            a.y, b.y = 0, 0
            self.correction[name] = b.normalized().rotation_difference(a.normalized())

    def interpolate_matrix(self, a, b, weight):
        a, b = a.decompose(), b.decompose()
        return Matrix.LocRotScale(a[0].lerp(b[0],weight), a[1].slerp(b[1],weight), a[2].lerp(b[2],weight))

    def plant(self, side, goal, weight):
        if weight < .001:
            return
        thigh, shin, foot = ['%s.%s' % (name,side) for name in ['thigh','shin','foot']]
        fk = {name:self.rig.pose.bones[name].matrix_basis.copy() for name in [thigh,shin,foot]}
        foot_rotation, foot_scale = self.rig.pose.bones[foot].matrix.to_quaternion(), self.rig.pose.bones[foot].matrix.to_scale()
        hip = self.rig.pose.bones[thigh].head.copy()
        first, second = self.rig.data.bones[thigh].length, self.rig.data.bones[shin].length
        axis = (goal-hip).normalized()
        distance = max(.01,min(first+second-.0001,(goal-hip).length))
        forward = Vector((0,-1,0))
        forward = (forward-axis*forward.dot(axis)).normalized()
        along = (first*first-second*second+distance*distance)/(2*distance)
        knee = hip+axis*along+forward*math.sqrt(max(0,first*first-along*along))
        endpoint = hip+axis*distance
        for name, head, tail in [(thigh,hip,knee),(shin,knee,endpoint)]:
            rest = self.rig.data.bones[name]
            delta = (rest.tail_local-rest.head_local).rotation_difference(tail-head)
            self.rig.pose.bones[name].matrix = Matrix.LocRotScale(head,delta@rest.matrix_local.to_quaternion(),Vector((1,1,1)))
            bpy.context.view_layer.update()
        self.rig.pose.bones[foot].matrix = Matrix.LocRotScale(endpoint,foot_rotation,foot_scale)
        bpy.context.view_layer.update()
        if weight < .999:
            ik = {name:self.rig.pose.bones[name].matrix_basis.copy() for name in [thigh,shin,foot]}
            for name in [thigh,shin,foot]:
                self.rig.pose.bones[name].matrix_basis = self.interpolate_matrix(fk[name],ik[name],weight)
            bpy.context.view_layer.update()

    def retarget(self, clip):
        for item in self.rig.pose.bones:
            if item.name not in self.source.pose.bones:
                item.matrix_basis = Matrix.Identity(4)
                continue
            src = self.source.pose.bones[item.name]
            if item.parent:
                rest_parent = self.rig.data.bones[item.parent.name].matrix_local
                relative_head = rest_parent.inverted() @ item.bone.head_local
                head = item.parent.matrix @ relative_head
            else:
                head = item.bone.head_local+(src.head-self.source.data.bones[item.name].head_local)
            item.matrix = Matrix.LocRotScale(head,src.matrix.to_quaternion()@self.correction[item.name],src.matrix.to_scale())
            bpy.context.view_layer.update()
        if clip in ['ElbowFlex','KneeFlex']:
            return
        goals, weights = {}, {}
        for side in ['L','R']:
            src_foot = self.source.pose.bones['foot.'+side].head.copy()
            src_rest = self.source.data.bones['foot.'+side].head_local
            goals[side] = src_foot+self.rig.data.bones['foot.'+side].head_local-src_rest
            if clip in ['Guard','Jab','Cross','Run'] or (clip in ['Kick','Combo'] and side == 'L'):
                weight = 1.0
            else:
                height = max(0,src_foot.z-src_rest.z)
                weight = max(0,min(1,1-height/.055))
                weight = weight*weight*(3-2*weight)
            weights[side] = weight
        lower = 0.0
        for side in ['L','R']:
            if weights[side] < .999:
                continue
            hip = self.rig.pose.bones['thigh.'+side].head
            goal = goals[side]
            reach = self.rig.data.bones['thigh.'+side].length+self.rig.data.bones['shin.'+side].length-.004
            horizontal = (hip.x-goal.x)**2+(hip.y-goal.y)**2
            vertical = math.sqrt(max(.0001,reach*reach-horizontal))
            lower = max(lower,hip.z-goal.z-vertical)
        if lower > 0:
            matrix = self.rig.pose.bones['root'].matrix.copy()
            matrix.translation.z -= lower
            self.rig.pose.bones['root'].matrix = matrix
            bpy.context.view_layer.update()
        for side in ['L','R']:
            self.plant(side,goals[side],weights[side])
