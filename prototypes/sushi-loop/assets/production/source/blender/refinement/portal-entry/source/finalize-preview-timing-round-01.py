"""Set exact1/12 APNG preview delay; native/published image pixels remain untouched."""
from pathlib import Path
import struct,zlib,json,hashlib
from PIL import Image
H=Path(__file__).resolve().parent.parent/'candidates/round-01';records=[]
for name in ['motion.png',*[f'enter-{d}.png' for d in 'NESW']]:
    p=H/'previews'/name;old=p.read_bytes();offset=8;chunks=[];frames=0;prior=[]
    while offset<len(old):
        n=struct.unpack('>I',old[offset:offset+4])[0];tag=old[offset+4:offset+8];data=old[offset+8:offset+8+n]
        if tag==b'fcTL':
            b=bytearray(data);prior.append(list(struct.unpack('>HH',b[20:24])));b[20:24]=struct.pack('>HH',1,12);data=bytes(b);frames+=1
        chunks.append(struct.pack('>I',len(data))+tag+data+struct.pack('>I',zlib.crc32(tag+data)&0xffffffff));offset+=n+12
    new=old[:8]+b''.join(chunks);assert frames==12
    # The only changed chunks are timing/control metadata; IDAT/fdAT pixel payloads remain exact.
    p.write_bytes(new)
    with Image.open(p) as im:
        assert im.n_frames==12
        durations=[]
        for i in range(im.n_frames):im.seek(i);durations.append(im.info['duration'])
    assert all(abs(v-1000/12)<1e-9 for v in durations)
    records.append({'path':str(p.relative_to(H.parent.parent)),'frames':frames,'delayNumerator':1,'delayDenominator':12,'fps':12,'plays':1,'priorUnsealedContainerDelays':prior,'oldUnsealedPreviewSHA256':hashlib.sha256(old).hexdigest(),'finalSHA256':hashlib.sha256(new).hexdigest(),'pixelPayloadsUnchanged':True})
out=H/'preview-timing.json';assert not out.exists();out.write_text(json.dumps({'scope':'Unsealed preview timing correction only, exact rational1/12s. Native/publication PNGs/atlases unchanged; no RGB/alpha repair. Final media are made immutable at handoff.','files':records},indent=2)+'\n')
