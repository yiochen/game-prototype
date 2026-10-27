"""Bind native staff artwork to the approved interactive prototype, without resampling."""
from pathlib import Path
import hashlib,json,struct

def verify_staff_ui(project, source_project=None):
    project=Path(project).resolve()
    prototype=Path(source_project or project).resolve().parent
    record=json.loads((project/'assets/ui/staff/manifest.json').read_text())
    if record.get('version')!=1 or set(record.get('artwork',{}))!={'resume-paper.png','hiring-stamp.png','assigned-stamp.png'}:
        raise ValueError('Incomplete approved staff artwork')
    for name,entry in record['artwork'].items():
        source=(prototype/entry['source']).resolve()
        if not source.is_relative_to(prototype):raise ValueError('Staff artwork reference escaped prototype')
        for path in [source,project/'assets/ui/staff'/name]:
            if hashlib.sha256(path.read_bytes()).hexdigest()!=entry['sha256']:raise ValueError(f'Changed staff artwork pixels: {name}')
        if min(struct.unpack_from('>II',(project/'assets/ui/staff'/name).read_bytes(),16))<400:raise ValueError('Staff art lacks approved resolution')
    if record['calibration']['paper_source_slices']!=[170]*4 or record['calibration']['paper_target_corner']!=36:
        raise ValueError('Staff paper corner calibration changed')
    return {'runtime_images':['assets/ui/staff/'+name for name in record['artwork']], 'approved_artwork':3}
