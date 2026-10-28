"""Landmarks measured on the supplied meshes, in original Blender world units.

The enemy's two supplied tail branches are retained. Lar's blade is sheathed;
the rig does not fabricate a separate commercial or placeholder weapon mesh.
"""
PROFILES = {
    'januri': {
        'height':1.8, 'role':'master', 'hips':.35,'spine':.425,'chest':.525,
        'neck':.645,'head':.70,'head_tip':.825,'shoulder':(.16,.015,.625),
        'elbow':(.31,.012,.618),'wrist':(.415,.005,.61),'hand_end':(.505,.005,.61),
        'thigh':(.105,.025,.29),'knee':(.14,.015,.165),'ankle':(.155,.005,.072),
        'toe':(.155,-.12,.028),'toe_end':(.155,-.19,.024),
        'hand_full':.425,'hand_blend':.405,'head_full':.71,
        'tails':[],
        'extras': {
            'shell':((0,.17,.30),(0,.17,.76),'chest'),
            'hat':((0,0,.84),(0,0,.98),'head'),
            'beard':((0,-.15,.69),(0,-.18,.445),'head')}
    },
    'inimigo': {
        'height':1.7, 'role':'enemy','hips':.285,'spine':.37,'chest':.45,
        'neck':.535,'head':.59,'head_tip':.755,'shoulder':(.15,.005,.532),
        'elbow':(.28,.005,.52),'wrist':(.375,0,.512),'hand_end':(.45,0,.51),
        'thigh':(.09,.015,.26),'knee':(.105,.006,.145),'ankle':(.12,0,.06),
        'toe':(.12,-.09,.025),'toe_end':(.12,-.16,.02),
        'hand_full':.39,'hand_blend':.365,'head_full':.59,
        'tails': [
            ('tail.L',[(-.04,.10,.25),(-.16,.22,.175),(-.26,.32,.128),(-.36,.41,.135),(-.45,.485,.165)]),
            ('tail.R',[(.04,.10,.26),(.07,.20,.205),(.12,.30,.178),(.20,.40,.195),(.305,.498,.262)])],
        'extras': {},
        'ribbon':[(.12,.075,.70),(.20,.14,.63),(.23,.205,.55)]
    },
    'lar': {
        'height':1.9, 'role':'assassin','hips':.305,'spine':.39,'chest':.465,
        'neck':.55,'head':.61,'head_tip':.72,'shoulder':(.16,.008,.535),
        'elbow':(.285,.005,.525),'wrist':(.39,0,.52),'hand_end':(.46,0,.515),
        'thigh':(.10,.01,.28),'knee':(.115,.005,.15),'ankle':(.13,0,.065),
        'toe':(.13,-.10,.028),'toe_end':(.13,-.17,.023),
        'hand_full':.405,'hand_blend':.377,'head_full':.60,
        'tails': [
            ('tail',[(.05,.09,.26),(.10,.19,.185),(.17,.30,.155),(.25,.42,.155),(.35,.526,.18)])],
        'extras': {
            'hat':((0,0,.73),(0,0,.82),'head'),
            'sheath':((.08,-.12,.40),(.23,.09,.32),'hips')},
        'ribbon':[(0,.02,.85),(.10,.16,.74),(.18,.27,.60)]
    }
}
