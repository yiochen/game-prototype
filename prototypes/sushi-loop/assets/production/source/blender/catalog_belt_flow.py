"""Normalize corner deck UVs to incoming-to-outgoing travel coordinates.
The deck geometry and its centerline derivative stay unchanged. Universal -7t
phase makes all directed module ports agree at every animation sample.
"""
import json
REVERSED=frozenset(('belt-corner-e-n','belt-corner-n-w','belt-corner-s-e','belt-corner-w-s'))
def augment(asset,asset_id=None):
    ident=asset_id or asset.get('id') or asset['root'].get('production_id')
    if not ident or not ident.startswith('belt-corner-'):raise ValueError('Expected native corner belt')
    if asset['root'].get('directed_flow_uv')=='incoming-to-outgoing-v1':return asset
    deck=asset['parts']['connected_turn_deck']
    if ident in REVERSED:
        for loop in deck.data.uv_layers.active.data:loop.uv.x=1.-loop.uv.x
        deck.data.update()
    phase=asset['phaseNode']
    def pose(clip,t):phase.outputs[0].default_value=-7*t
    asset['pose']=pose
    asset['flow'].update(uvConvention='incoming-to-outgoing-v1',incomingUV=0.,outgoingUV=1.,shaderPhase='-7*t')
    asset['root']['directed_flow_uv']='incoming-to-outgoing-v1'
    asset['root']['directed_flow_record']=json.dumps(asset['flow'],sort_keys=True)
    return asset
