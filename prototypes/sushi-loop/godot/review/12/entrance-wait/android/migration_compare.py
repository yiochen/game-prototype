"""Strict v46 navigation1 to v47 admission1 migration; no legacy rewrites."""
from copy import deepcopy

def expected_admission_upgrade(legacy):
 assert legacy.get('customer_navigation_version')==1
 assert legacy.get('customer_admission_version',0)==0
 expected=deepcopy(legacy)
 expected['customer_admission_version']=1
 customers=expected['configuration']['customers']
 if 'entrance_wait_seconds' not in customers:customers['entrance_wait_seconds']=4.0
 for guest in expected['state']['customers']:
  guest['entrance_wait_elapsed']=0.0
  guest['wander_elapsed']=0.0
 return expected
