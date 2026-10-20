"""Exact legacy-state comparison with only the authorized navigation migration."""
from copy import deepcopy
import json
from qa_common import PROJECT

def expected_navigation_upgrade(legacy):
 assert legacy.get('customer_navigation_version',0)==0,'Baseline45 must use legacy navigation version0'
 expected=deepcopy(legacy);expected['customer_navigation_version']=1
 defaults=json.loads((PROJECT/'content/starter.json').read_text())['customers']
 if 'customers' not in expected['configuration']:expected['configuration']['customers']=deepcopy(defaults)
 else:
  for key in ['wander_retry_seconds','wander_speed_multiplier']:
   if key not in expected['configuration']['customers']:expected['configuration']['customers'][key]=deepcopy(defaults[key])
 entrance=expected['configuration']['floor']['entrance']
 for guest in expected['state']['customers']:
  origin=entrance
  if guest['phase']=='leaving':
   seat=next((o for o in expected['state']['objects'] if o['id']==guest['seat_id']),None)
   if seat:origin=seat
  guest['navigation_mode']='goal';guest['path_origin']={'x':origin['x'],'y':origin['y']};guest['navigation_retry_elapsed']=0.;guest['wander_cursor']=0
  if guest['phase'] in ['waiting','eating']:
   guest['path_origin']={'x':guest['x'],'y':guest['y']};guest['path']=[];guest['path_index']=0
 return expected
