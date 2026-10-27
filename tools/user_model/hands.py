"""Keep the supplied closed fingers/thumb rigid, with a narrow wrist transition."""

def protect_hands(body, scale):
    changed = 0
    protected = {'L': 0, 'R': 0}
    for vertex in body.data.vertices:
        x, y, z = vertex.co/scale
        if abs(x) < .435 or not .43 < z < .66:
            continue
        side = 'L' if x < 0 else 'R'
        t = max(0.0, min(1.0, (abs(x)-.435)/.020))
        hand = t*t*(3-2*t)
        desired = {name: weight for name, weight in
                   [('hand.'+side, hand), ('forearm.'+side, 1-hand)] if weight > .000001}
        current = {body.vertex_groups[g.group].name: g.weight for g in vertex.groups}
        if set(current) != set(desired) or any(abs(current.get(n,0)-w) > .00001 for n,w in desired.items()):
            for group in body.vertex_groups:
                group.remove([vertex.index])
            for name, weight in desired.items():
                body.vertex_groups[name].add([vertex.index], weight, 'REPLACE')
            changed += 1
        if hand == 1:
            protected[side] += 1
            assert len(vertex.groups) == 1
    return {'changed_vertices': changed, 'rigid_hand_vertices': protected,
            'full_hand_from_original_abs_x': .455, 'wrist_blend_original_x': [.435,.455],
            'geometry_edited': False, 'fingers_and_thumb_follow_hand_only': True}
