"""Original deterministic synthesis for ticket #10; no samples or borrowed music."""
from pathlib import Path
import json, math, random, struct, wave

RATE=22050
OUT=Path(__file__).parent
TAU=math.tau
metrics={}

def midi(number): return 440.0*2**((number-69)/12)

def write(name, samples, channels=1, peak=.45):
    rawpeak=max(abs(v) for v in samples) or 1
    scale=min(1.0,peak/rawpeak)
    samples=[v*scale for v in samples]
    with wave.open(str(OUT/(name+'.wav')),'wb') as f:
        f.setnchannels(channels);f.setsampwidth(2);f.setframerate(RATE)
        f.writeframes(struct.pack('<'+'h'*len(samples),*[round(v*32767) for v in samples]))
    metrics[name]={'frames':len(samples)//channels,'sample_rate':RATE,'channels':channels,'seconds':len(samples)/(RATE*channels),'peak':round(max(abs(v) for v in samples),6),'rms':round(math.sqrt(sum(v*v for v in samples)/len(samples)),6)}

def tone(buffer,start,duration,frequency,gain,decay=5.0,harmonics=(1.0,.18,.055),pan=0.0,stereo=False,wrap=False):
    frames=len(buffer)//(2 if stereo else 1)
    onset=round(start*RATE);length=round(duration*RATE)
    for i in range(length):
        t=i/RATE
        attack=min(1.0,t/.008)
        release=min(1.0,(length-i)/(RATE*.045))
        env=attack*release*math.exp(-decay*t/duration)
        value=sum(amp*math.sin(TAU*frequency*(h+1)*t) for h,amp in enumerate(harmonics))*gain*env
        at=onset+i
        if wrap:at%=frames
        elif at>=frames:break
        if stereo:
            buffer[at*2]+=value*math.sqrt((1-pan)/2)
            buffer[at*2+1]+=value*math.sqrt((1+pan)/2)
        else:buffer[at]+=value

# Soft wooden UI response, a restrained prep tap and ceramic placement.
click=[0.0]*round(.10*RATE)
tone(click,0,.10,760,.28,6,(1,.12))
tone(click,.008,.05,1450,.035,7,(1,))
write('click',click,peak=.32)
cook=[0.0]*round(.23*RATE)
for start,freq,gain in [(0,330,.2),(.075,410,.13),(.14,290,.1)]:tone(cook,start,.09,freq,gain,6,(1,.22))
write('cook',cook,peak=.32)
load=[0.0]*round(.26*RATE)
tone(load,0,.22,690,.24,5,(1,.12,.035))
tone(load,.018,.18,1040,.075,5,(1,))
write('load',load,peak=.34)
coin=[0.0]*round(.57*RATE)
for start,note,gain in [(0,76,.23),(.085,79,.18),(.16,84,.14)]:tone(coin,start,.38,midi(note),gain,4,(1,.26,.045))
write('coin',coin,peak=.40)

# Eight original bars at 100 BPM: Dm9, G13, Cmaj9, Am9, repeated with variation.
# All instrument tails wrap into the beginning, preserving a continuous loop.
beat=.6;bar=4*beat;duration=8*bar
music=[0.0]*(round(duration*RATE)*2)
chords=[(38,[53,57,60,64]),(43,[53,57,59,64]),(36,[52,55,59,62]),(45,[55,59,60,64])]*2
melodies=[[(.5,69),(1.75,72),(3,76)],[(.5,71),(2,69),(3.25,67)],[(.75,76),(2,74),(3.25,71)],[(.5,72),(2,71),(3,67)],[(.5,65),(1.75,69),(3,76)],[(.5,74),(2,71),(3.25,69)],[(.75,67),(2,71),(3.25,74)],[(.5,76),(2,72),(3.25,71)]]
for b,(bass,chord) in enumerate(chords):
    start=b*bar
    tone(music,start,1.6,midi(bass),.105,3,(1,.10),-.08,True,True)
    tone(music,start+2.5*beat,1.1,midi(bass+7),.06,3,(1,.08),.08,True,True)
    for strum,note in enumerate(chord):
        tone(music,start+.035*strum,2.8,midi(note),.030,2.7,(1,.08,.015),(-.4+.26*strum),True,True)
    for n,(offset,note) in enumerate(melodies[b]):
        tone(music,start+offset*beat,.86,midi(note),.073,4,(1,.22,.025),-.20 if n%2 else .24,True,True)
# Very soft, low-passed brushed pulse, original deterministic noise.
rng=random.Random(102026)
for tick in range(16):
    start=round((tick*1.2+.6)*RATE);filtered=0.0
    for i in range(round(.075*RATE)):
        filtered=.92*filtered+.08*rng.uniform(-1,1)
        value=filtered*.012*math.sin(math.pi*i/(.075*RATE))**2
        at=(start+i)%(len(music)//2)
        music[2*at]+=value;music[2*at+1]+=value
write('harbor_cafe',music,2,peak=.44)
metrics['harbor_cafe']['loop']=True
metrics['harbor_cafe']['bpm']=100
(OUT/'audio-verification.json').write_text(json.dumps(metrics,indent=2)+'\n')
print(json.dumps(metrics,indent=2))
