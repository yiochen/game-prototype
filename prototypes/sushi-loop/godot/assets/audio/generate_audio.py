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

# Tea pouring (#62): result chimes after a pour, a soft pour stream, a splash.
tea_ideal=[0.0]*round(1.0*RATE)
for start,note,gain in [(0,79,.2),(.08,83,.17),(.16,86,.15),(.24,91,.13)]:tone(tea_ideal,start,.7,midi(note),gain,4,(1,.2,.04))
write('tea_ideal',tea_ideal,peak=.38)
tea_good=[0.0]*round(.75*RATE)
for start,note,gain in [(0,79,.2),(.1,86,.16)]:tone(tea_good,start,.6,midi(note),gain,4,(1,.2,.04))
write('tea_good',tea_good,peak=.36)
tea_soft=[0.0]*round(.45*RATE)
tone(tea_soft,0,.4,midi(72),.18,5,(1,.3,.1))
write('tea_soft',tea_soft,peak=.3)
splash=[0.0]*round(.45*RATE)
tea_rng=random.Random(622026);filtered=0.0
for i in range(len(splash)):
    filtered=.7*filtered+.3*tea_rng.uniform(-1,1)
    splash[i]+=filtered*.5*math.exp(-9*i/RATE)
tone(splash,.05,.3,330,.12,5,(1,.3))
write('tea_splash',splash,peak=.34)
# A short, seamless burble of water for the stream; volume follows the flow.
pour=[0.0]*round(.8*RATE)
filtered=0.0
for i in range(len(pour)):
    filtered=.85*filtered+.15*tea_rng.uniform(-1,1)
    pour[i]+=filtered*(.8+.2*math.sin(TAU*14*i/RATE))
fade=round(.05*RATE)
for i in range(fade):
    pour[i]*=i/fade;pour[-1-i]*=i/fade
write('tea_pour',pour,peak=.3)

# Inkfin ink (#70): the first dive cues. A warning of three low glugs (one per
# purple pulse), the ink bursting out, and a soft rising wash as it lifts.
def sweep(buffer,start,duration,f0,f1,gain,decay=4.0,attack=.012):
    onset=round(start*RATE);length=round(duration*RATE);phase=0.0
    for i in range(length):
        t=i/RATE;k=i/length
        phase+=TAU*(f0+(f1-f0)*k)/RATE
        env=min(1.0,t/attack)*min(1.0,(length-i)/(RATE*.04))*math.exp(-decay*k)
        if onset+i<len(buffer):buffer[onset+i]+=math.sin(phase)*gain*env
def wash(buffer,start,duration,gain,smooth,shape,rng):
    onset=round(start*RATE);length=round(duration*RATE);filtered=0.0
    for i in range(length):
        filtered=smooth*filtered+(1-smooth)*rng.uniform(-1,1)
        if onset+i<len(buffer):buffer[onset+i]+=filtered*gain*shape(i/length)
ink_rng=random.Random(702026)
ink_warn=[0.0]*round(1.05*RATE)
for n,start in enumerate([0,.333,.666]):
    sweep(ink_warn,start,.26,150+18*n,96+14*n,.5,3.5)
    sweep(ink_warn,start+.02,.12,420+40*n,300+30*n,.07,5)
    wash(ink_warn,start,.3,.5,.93,lambda k:math.sin(math.pi*k)**2,ink_rng)
write('ink_warn',ink_warn,peak=.36)
ink_burst=[0.0]*round(1.5*RATE)
sweep(ink_burst,0,.55,230,62,.6,2.2,.02)
wash(ink_burst,0,1.5,2.4,.965,lambda k:min(1.0,k/.08)*math.exp(-3.2*k),ink_rng)
wash(ink_burst,.05,1.2,.5,.8,lambda k:min(1.0,k/.1)*math.exp(-5*k),ink_rng)
for start,freq in [(.22,520),(.36,640),(.47,470),(.63,720),(.8,560)]:sweep(ink_burst,start,.07,freq,freq*1.5,.07,3,.006)
write('ink_burst',ink_burst,peak=.4)
ink_lift=[0.0]*round(1.0*RATE)
wash(ink_lift,0,.95,1.6,.9,lambda k:math.sin(math.pi*k)*(1-k),ink_rng)
for start,note,gain in [(.05,69,.13),(.22,74,.12),(.4,81,.1)]:tone(ink_lift,start,.5,midi(note),gain,4,(1,.2,.04))
write('ink_lift',ink_lift,peak=.3)
# Scene music: one loop per scene. Like harbor_cafe, every tail wraps into the
# start of its loop. `level` scales each track to a fixed peak for the mix.
def pad(buffer,start,duration,frequency,gain,pan=0.0):
    frames=len(buffer)//2;onset=round(start*RATE);length=round(duration*RATE)
    left=math.sqrt((1-pan)/2);right=math.sqrt((1+pan)/2)
    for i in range(length):
        t=i/RATE
        value=(math.sin(TAU*frequency*.997*t)+math.sin(TAU*frequency*1.003*t)+.2*math.sin(TAU*frequency*2*t))*gain*math.sin(math.pi*i/length)**2
        at=(onset+i)%frames
        buffer[at*2]+=value*left;buffer[at*2+1]+=value*right
def noise(buffer,start,duration,gain,smooth,shape,rng,pan=0.0):
    frames=len(buffer)//2;onset=round(start*RATE);length=round(duration*RATE);filtered=0.0
    left=math.sqrt((1-pan)/2);right=math.sqrt((1+pan)/2)
    for i in range(length):
        filtered=smooth*filtered+(1-smooth)*rng.uniform(-1,1)
        value=filtered*gain*shape(i/length)
        at=(onset+i)%frames
        buffer[at*2]+=value*left;buffer[at*2+1]+=value*right
def thump(buffer,start,duration,f0,f1,gain):
    frames=len(buffer)//2;onset=round(start*RATE);length=round(duration*RATE);phase=0.0
    for i in range(length):
        k=i/length;phase+=TAU*(f1+(f0-f1)*(1-k)**3)/RATE
        value=math.sin(phase)*gain*min(1.0,i/(RATE*.004))*(1-k)**2
        at=(onset+i)%frames
        buffer[at*2]+=value*.707;buffer[at*2+1]+=value*.707
def level(samples,peak):
    scale=peak/(max(abs(v) for v in samples) or 1)
    return [v*scale for v in samples]
def track(name,samples,peak,bpm):
    write(name,level(samples,peak),2,peak=peak)
    metrics[name]['loop']=True;metrics[name]['bpm']=bpm
music_rng=random.Random(772026)

# Workshop, "Tinker Dock": eight bars at 96 BPM in F. A marimba arpeggio,
# a whistled tune, and tiny hammer taps on the backbeat.
beat=60/96;bar=4*beat
tinker=[0.0]*(round(8*bar*RATE)*2)
chords=[(41,[60,64,65,69]),(38,[60,62,65,69]),(34,[58,62,65,69]),(36,[58,60,65,67])]*2
tunes=[[(0,72),(1.5,77),(2,76),(3,72)],[(0,74),(1.5,77),(2.5,74)],[(0,70),(1.5,74),(2,77),(3,74)],[(0,72),(2,67),(3,70)],
       [(0,77),(1.5,81),(2,79),(3,77)],[(0,74),(1.5,77),(2.5,81)],[(0,82),(1.5,81),(2,77),(3,74)],[(0,72),(1,77),(2,79),(3,70)]]
for b,(bass,chord) in enumerate(chords):
    start=b*bar
    for offset,note,gain in [(0,bass,.12),(1.5,bass,.07),(3,bass+7,.08)]:
        tone(tinker,start+offset*beat,.7,midi(note),gain,3.5,(1,.12),0,True,True)
    for step,index in enumerate([0,2,1,3,2,1,3,2]):
        tone(tinker,start+step*beat/2,.34,midi(chord[index]+12),.05 if step%2 else .065,6,(1,0,0,.22),-.45+.3*index,True,True)
    for offset,note in tunes[b]:
        tone(tinker,start+offset*beat,.8,midi(note+12),.06,3.5,(1,.06),.12,True,True)
    for offset in (1,3):
        tone(tinker,start+offset*beat,.07,2100,.03,7,(1,.4),.5,True,True)
        tone(tinker,start+(offset+.5)*beat,.05,1650,.014,7,(1,),-.5,True,True)
    for step in range(8):
        noise(tinker,start+(step+.5)*beat/2,.05,.05,.3,lambda k:(1-k)**2,music_rng,.3)
track('tinker_dock',tinker,.22,96)

# Expedition route, "Deep Current": eight bars at 80 BPM in A minor. Slow
# pads, echoing bell arpeggios and a low swell of water.
beat=60/80;bar=4*beat
deep=[0.0]*(round(8*bar*RATE)*2)
chords=[(33,[57,60,64,71]),(29,[57,60,64,65]),(36,[55,59,60,64]),(28,[55,59,62,64])]*2
tunes=[[(2,76)],[(1,77),(3,76)],[(2,79)],[(1,74),(3,71)],[(2,81)],[(1,79),(3,77)],[(2,76),(3.5,79)],[(1,74)]]
for b,(bass,chord) in enumerate(chords):
    start=b*bar
    tone(deep,start,2.8,midi(bass+12),.11,2,(1,.2,.04),0,True,True)
    for offset in (1,2,3):tone(deep,start+offset*beat,.5,midi(bass+12),.035,4,(1,),0,True,True)
    for n,note in enumerate(chord):pad(deep,start-.3,bar+.9,midi(note),.016,-.5+.33*n)
    for step,index in enumerate([0,1,2,3,2,1,2,3]):
        for echo,gain in enumerate([.05,.02,.008]):
            side=(-.5 if step%2 else .5)*(-1)**echo
            tone(deep,start+(step/2+.75*echo)*beat,1.1,midi(chord[index]+12),gain,5,(1,0,.12,0,.05),side,True,True)
    for offset,note in tunes[b]:
        tone(deep,start+offset*beat,2.2,midi(note),.05,3,(1,.1),.1,True,True)
        tone(deep,start+(offset+1.5)*beat,2.0,midi(note),.016,3,(1,.1),-.4,True,True)
    if b%2==0:noise(deep,start,2*bar,.5,.985,lambda k:math.sin(math.pi*k)**2,music_rng,-.2 if b%4 else .2)
track('deep_current',deep,.16,80)

# Bonus passage behind a portal, "Portal Ride": eight bars at 132 BPM in C
# lydian. The ride lasts about eight seconds, so it sparkles from the first
# beat: racing sixteenth arpeggios, a bouncing bass and a rising tune.
beat=60/132;bar=4*beat
ride=[0.0]*(round(8*bar*RATE)*2)
chords=[(36,[60,64,67,71]),(38,[62,66,69,72]),(40,[59,64,67,71]),(43,[59,62,66,69])]*2
tunes=[[(0,79),(1,83),(2,84),(3,88)],[(0,90),(1.5,86),(2,84),(3,81)],[(0,83),(1,86),(2,88),(3,91)],[(0,90),(1,86),(2,83),(3,86)],
       [(0,88),(1,91),(2,95),(3,96)],[(0,98),(1.5,96),(2,93),(3,90)],[(0,95),(1,91),(2,88),(3,86)],[(0,90),(1,93),(2,95),(3,98)]]
for b,(bass,chord) in enumerate(chords):
    start=b*bar
    for step in range(8):
        tone(ride,start+step*beat/2,.2,midi(bass+(12 if step%2 else 0)),.1 if step%2==0 else .06,4,(1,.25,.08),0,True,True)
    for step in range(16):
        note=chord[step%4]+12*(1+(step//4)%2)
        tone(ride,start+step*beat/4,.22,midi(note),.04,6,(1,0,.15,0,.06),.6 if step%2 else -.6,True,True)
    for n,note in enumerate(chord):pad(ride,start-.1,bar+.3,midi(note),.012,-.45+.3*n)
    for offset,note in tunes[b]:
        tone(ride,start+offset*beat,.6,midi(note),.06,3.5,(1,.15,.04),.1,True,True)
        tone(ride,start+(offset+.75)*beat,.5,midi(note),.018,4,(1,.1),-.5,True,True)
    for step in range(8):
        noise(ride,start+(step+.5)*beat/2,.04,.06,.15,lambda k:(1-k)**2,music_rng,-.3)
    for offset in (0,2):thump(ride,start+offset*beat,.16,110,50,.14)
track('portal_ride',ride,.2,132)

# Creature encounter, "Storm Chase": sixteen bars at 150 BPM in D minor. A
# driving eighth-note bass, kick and snare, chord stabs and an urgent lead,
# doubled an octave up on the second pass.
beat=60/150;bar=4*beat
storm=[0.0]*(round(16*bar*RATE)*2)
chords=[(38,[62,65,69]),(38,[62,65,69]),(34,[62,65,70]),(36,[60,64,67]),(38,[62,65,69]),(38,[62,65,69]),(34,[62,65,70]),(33,[61,64,69])]*2
leads=[[(0,74,1),(1,77,.5),(1.5,76,.5),(2,74,1),(3,69,1)],[(0,72,.5),(.5,74,1.5),(2,77,1),(3,81,1)],
       [(0,82,1.5),(1.5,81,.5),(2,77,1),(3,74,1)],[(0,76,1),(1,79,1),(2,76,.5),(2.5,72,.5),(3,76,1)],
       [(0,74,1),(1,77,.5),(1.5,76,.5),(2,74,1),(3,81,1)],[(0,84,.5),(.5,86,1.5),(2,84,.5),(2.5,81,.5),(3,77,1)],
       [(0,82,1),(1,79,1),(2,77,1),(3,74,1)],[(0,73,1),(1,76,1),(2,81,1),(3,85,1)]]*2
for b,(bass,chord) in enumerate(chords):
    start=b*bar;again=b>=8
    for step,lift in enumerate([0,0,12,0,0,0,12,7]):
        tone(storm,start+step*beat/2,.2,midi(bass+lift),.12 if step%2==0 else .09,4,(1,.5,.25,.12),0,True,True)
    for offset in (0,2):thump(storm,start+offset*beat,.2,130,44,.3)
    if b%4==3:thump(storm,start+3.5*beat,.16,130,44,.22)
    for offset in (1,3):
        noise(storm,start+offset*beat,.14,.42,.45,lambda k:(1-k)**3,music_rng)
        tone(storm,start+offset*beat,.08,190,.06,6,(1,.3),0,True,True)
    for step in range(8):
        noise(storm,start+(step+.5)*beat/2,.04,.1 if step%2 else .06,.12,lambda k:(1-k)**2,music_rng,.35)
    for offset in (0,1.5,3):
        for n,note in enumerate(chord):
            tone(storm,start+offset*beat,.22,midi(note),.034,4,(1,.4,.2,.1),-.5+.5*n,True,True)
    for offset,note,length in leads[b]:
        tone(storm,start+offset*beat,length*beat+.12,midi(note),.085,2.6,(1,.35,.15,.06),.15,True,True)
        if again:tone(storm,start+offset*beat,length*beat+.1,midi(note+12),.03,3,(1,.2),-.3,True,True)
    if again:
        for step in range(16):
            tone(storm,start+step*beat/4,.1,midi(chord[step%3]+24),.012,5,(1,),.6 if step%2 else -.6,True,True)
track('storm_chase',storm,.3,150)

# Issue #76 reef cues (moved from design/boulderhead-preview/audio/generate_reef_audio.py on approval):
# reef_breach the parrotfish's first ram into a reef wall; reef_smash each row after that;
# reef_crash the submarine ramming reef; reef_bump the same, quieter, during hit protection.
def reef_cues():
    def _reef_write(name, samples, peak):
        scale = peak / (max(abs(v) for v in samples) or 1)
        with wave.open(str(OUT / (name + '.wav')), 'wb') as f:
            f.setnchannels(1); f.setsampwidth(2); f.setframerate(RATE)
            f.writeframes(struct.pack('<' + 'h' * len(samples), *[round(v * scale * 32767) for v in samples]))


    def sweep(buffer, start, duration, f0, f1, gain, decay=4.0, attack=.004):
        """Falling sine: the body of an impact."""
        onset = round(start * RATE); length = round(duration * RATE); phase = 0.0
        for i in range(length):
            k = i / length
            phase += TAU * (f1 + (f0 - f1) * (1 - k) ** 3) / RATE
            env = min(1.0, i / (RATE * attack)) * math.exp(-decay * k) * min(1.0, (length - i) / (RATE * .02))
            if onset + i < len(buffer): buffer[onset + i] += math.sin(phase) * gain * env


    def crunch(buffer, start, duration, gain, rng, low=.0, high=.0, decay=8.0):
        """Band-limited noise: `low` smooths away the hiss, `high` removes the rumble (0 keeps all)."""
        onset = round(start * RATE); length = round(duration * RATE); lp = hp = 0.0
        for i in range(length):
            lp = low * lp + (1 - low) * rng.uniform(-1, 1)
            hp = high * hp + (1 - high) * lp
            k = i / length
            env = min(1.0, i / (RATE * .002)) * math.exp(-decay * k)
            if onset + i < len(buffer): buffer[onset + i] += (lp - hp) * gain * env


    def ring(buffer, start, duration, frequency, gain, decay=9.0):
        """A struck metal partial."""
        onset = round(start * RATE); length = round(duration * RATE)
        for i in range(length):
            t = i / RATE
            if onset + i < len(buffer): buffer[onset + i] += math.sin(TAU * frequency * t) * gain * min(1.0, t / .001) * math.exp(-decay * t)


    def pebbles(buffer, start, span, count, gain, rng):
        """Small fragments landing: short bright ticks thinning out."""
        for n in range(count):
            at = start + span * (n / count) ** 1.4 + rng.uniform(0, span / count)
            crunch(buffer, at, .025 + rng.uniform(0, .02), gain * (1 - .6 * n / count) * rng.uniform(.6, 1), rng, .1, .75, 6)


    def bubbles(buffer, start, count, gain, rng):
        for n in range(count):
            f = rng.uniform(420, 760)
            sweep(buffer, start + n * rng.uniform(.04, .09), .06, f, f * 1.7, gain, 3, .006)


    rng = random.Random(762026)

    smash = [0.0] * round(.55 * RATE)
    sweep(smash, 0, .32, 170, 46, .9, 3.2)
    crunch(smash, 0, .2, 1.2, rng, .2, 0, 10)
    crunch(smash, .01, .32, .7, rng, .6, 0, 7)
    pebbles(smash, .08, .38, 7, .5, rng)
    bubbles(smash, .12, 3, .05, rng)
    _reef_write('reef_smash', smash, .42)

    breach = [0.0] * round(1.3 * RATE)
    sweep(breach, 0, .5, 150, 38, 1.0, 2.6)
    sweep(breach, .1, .45, 120, 34, .8, 2.8)
    crunch(breach, 0, .3, 1.4, rng, .15, 0, 9)
    crunch(breach, .02, 1.2, .9, rng, .96, 0, 3.2)
    crunch(breach, .1, .35, .8, rng, .5, 0, 6)
    pebbles(breach, .15, 1.0, 16, .55, rng)
    bubbles(breach, .25, 6, .05, rng)
    _reef_write('reef_breach', breach, .5)

    crash = [0.0] * round(.5 * RATE)
    for f, g, d in [(312, .5, 11), (497, .35, 13), (781, .25, 16), (1163, .15, 20)]:
        ring(crash, 0, .45, f, g, d)
    sweep(crash, 0, .22, 120, 52, .8, 3.5)
    crunch(crash, 0, .18, 1.1, rng, .25, 0, 10)
    pebbles(crash, .05, .3, 6, .5, rng)
    _reef_write('reef_crash', crash, .48)
    _reef_write('reef_bump', crash, .22)

reef_cues()

(OUT/'audio-verification.json').write_text(json.dumps(metrics,indent=2)+'\n')
print(json.dumps(metrics,indent=2))
