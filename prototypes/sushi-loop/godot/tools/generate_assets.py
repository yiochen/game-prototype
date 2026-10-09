#!/usr/bin/env python3
"""Original deterministic ink illustrations and procedural musical score.
Run with Python 3; standard library only. Fonts are external OFL-licensed assets.
"""
from pathlib import Path
import math, random, wave, array, shutil
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets'
OUT.mkdir(exist_ok=True)
# OFL font binaries and license texts are downloaded separately into assets/fonts.
FONTS = OUT / 'fonts'
FONTS.mkdir(exist_ok=True)
INK='#2e3436'; CREAM='#fff4d9'; CORAL='#e97662'; GOLD='#efbb53'; MINT='#91bda1'; TEAL='#397e87'; NAVY='#133646'

def path(d, fill='none', stroke=INK, sw=5, extra=''):
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round" {extra}/>'
def ellipse(cx,cy,rx,ry,fill,stroke=INK,sw=5,extra=''):
    return f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>'
def circle(cx,cy,r,fill,stroke=INK,sw=5): return ellipse(cx,cy,r,r,fill,stroke,sw)
def rect(x,y,w,h,r,fill,stroke=INK,sw=5,extra=''):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>'
def svg(name,content,w=256,h=256):
    (OUT/f'{name}.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{content}</svg>')
    return content

def face(cx,cy,smile=True):
    return (ellipse(cx-20,cy+13,10,6,'#eea083','none')+ellipse(cx+24,cy+13,10,6,'#eea083','none')+
        path(f'M {cx-18},{cy} q 5,-9 10,0 M {cx+15},{cy} q 5,-9 10,0',sw=4)+
        path(f'M {cx-5},{cy+12} q 8,15 16,0 z',CORAL,sw=3)+path(f'M {cx+2},{cy+4} l -2,5 5,0',sw=2.5))
# Chef: soft cotton hat, apron, rolled sleeves and asymmetric stance.
chef=ellipse(127,236,69,10,'#3d514b','none',extra='opacity=".16"')
chef+=path('M 84 207 L 82 232 Q 96 244 114 234 L 113 207 Z','#4d6859')
chef+=path('M 137 204 L 146 229 Q 163 239 176 225 L 164 199 Z','#4d6859')
chef+=path('M 82 226 Q 98 231 112 225 L 117 239 Q 97 247 79 240 Z','#474442')
chef+=path('M 147 223 Q 163 224 174 216 L 184 232 Q 164 244 151 237 Z','#474442')
chef+=path('M 95 120 Q 74 143 72 190 Q 91 211 159 205 L 163 145 Q 150 127 140 123 Z',CREAM)
chef+=path('M 96 132 L 101 162 Q 119 173 143 161 L 142 130 M 86 169 Q 125 184 160 169 L 160 205 Q 119 216 78 197 Z',MINT,sw=4)
chef+=path('M 98 184 Q 120 192 143 183 L 141 196 Q 121 204 99 196 Z','#78a98d',sw=3)
chef+=path('M 80 137 Q 63 154 72 170 Q 82 181 102 167 L 120 154 L 109 138 L 91 150',CREAM)
chef+=path('M 154 140 Q 165 147 177 142 L 195 147 L 189 166 Q 166 174 150 159 Z',CREAM)
chef+=path('M 177 142 Q 188 135 194 143 Q 206 143 208 149 Q 215 153 207 160 L 189 166 Z','#f3c49c',sw=4)
chef+=ellipse(201,166,34,10,'#719b8d',sw=4)+ellipse(201,161,34,10,CREAM,sw=4)
chef+=path('M 183 151 Q 192 138 213 143 L 222 153 Q 207 165 183 158 Z',CORAL,sw=3)+path('M 194 145 l 7 10 M 206 144 l 7 11',CREAM,CREAM,2)
chef+=ellipse(117,104,47,42,'#f4c89e')+ellipse(70,112,10,13,'#f4c89e',sw=4)
chef+=path('M 74 106 Q 65 70 86 60 Q 116 40 151 67 L 156 90 Q 132 83 122 71 Q 100 91 79 88 L 78 108 Z','#584b40')
chef+=face(115,103)
chef+=path('M 76 74 L 71 57 Q 52 37 70 22 Q 80 12 95 20 Q 97 5 120 10 Q 140 6 148 23 Q 174 18 175 41 Q 175 51 163 61 L 159 78 Q 117 84 76 74 Z',CREAM)
chef+=path('M 78 62 Q 114 68 159 63 M 87 34 l 8 14 M 121 28 l 1 19 M 151 34 l -6 13',stroke='#b9b2a0',sw=4)
chef+=path('M 145 120 q 10 -1 12 -7',sw=2.5)
svg('chef',chef)
# Four customers in matching footprints, each with recognisable costume and hair.
for idx,(shirt,hair,skin) in enumerate([('#91bda1','#56463b','#f0c69e'),('#ebbc59','#915c54','#f4c9a4'),('#699bab','#333f42','#dca77f'),('#e79381','#594037','#bd835f')],1):
    s=ellipse(128,237,64,9,'#455a51','none',extra='opacity=".16"')
    s+=path('M 80 163 L 74 227 L 91 237 L 106 182 L 153 182 L 166 234 L 183 229 L 172 159 Z','#c79c68')
    s+=rect(76,161,98,36,9,'#d7b07d')+path('M 85 192 L 85 220 M 164 193 L 165 216',stroke='#95734e',sw=3)
    s+=path('M 104 190 L 98 225 Q 110 236 124 226 L 127 193 M 137 191 L 141 221 Q 154 233 166 221 L 160 185','#4c5c5c')
    s+=path('M 98 224 Q 106 225 120 222 L 126 235 Q 108 245 96 237 Z M 141 220 L 161 218 Q 172 219 174 232 Q 156 242 143 233 Z','#3f3b37')
    s+=path('M 86 125 Q 72 150 81 185 Q 122 205 172 185 Q 179 146 161 125 Z',shirt)
    s+=path('M 86 158 Q 73 138 70 151 Q 66 167 89 177 L 112 164 L 103 151 Z',skin,sw=4)
    s+=path('M 163 152 Q 184 153 177 172 Q 164 187 147 172 L 140 161 L 151 150 Z',skin,sw=4)
    s+=ellipse(128,174,40,10,'#90ae9d',sw=4)+ellipse(128,169,40,10,CREAM,sw=4)
    s+=path('M 107 163 Q 112 151 133 153 L 147 162 Q 132 173 108 168 Z',CORAL,sw=3)+path('M 118 155 l 8 10 M 131 155 l 7 10',stroke=CREAM,sw=2)
    s+=path('M 101 154 L 111 140 M 105 157 L 115 144',stroke='#69553c',sw=3)
    s+=ellipse(127,99,48,47,skin)+ellipse(80,109,11,14,skin,sw=4)+ellipse(175,110,10,13,skin,sw=4)
    if idx==1:
        s+=path('M 79 96 Q 66 82 76 64 L 69 55 L 89 53 L 88 38 L 107 45 Q 115 23 127 42 L 143 30 L 148 46 Q 180 41 182 80 L 176 104 L 165 88 L 158 68 Q 139 84 117 64 Q 108 85 89 84 L 84 100 Z',hair)
    elif idx==2:
        s+=path('M 79 112 Q 62 146 79 155 Q 97 158 101 142 Q 88 126 88 99 L 92 64 Q 119 86 161 74 L 166 103 Q 162 126 153 140 Q 155 161 178 149 Q 190 140 176 118 Q 192 64 166 47 Q 135 23 104 41 Q 68 45 72 86 Z',hair)
        s+=path('M 107 51 l -4 20 M 125 48 l -1 24 M 143 53 l 4 16',stroke='#c78a72',sw=3)
        s+=path('M 168 88 q 18 -17 23 -3 q -7 15 -22 10',CORAL,sw=3)
    elif idx==3:
        s+=path('M 79 91 Q 61 76 81 58 Q 70 39 96 37 Q 100 18 119 34 Q 136 15 148 38 Q 177 25 177 51 Q 195 60 181 86 L 173 100 L 166 81 L 160 65 Q 127 83 101 63 L 91 89 Z',hair)
        s+=circle(108,100,18,'none',sw=4)+circle(150,100,18,'none',sw=4)+path('M 126 99 L 132 99 M 89 97 l -11 -3 M 169 97 l 8 -3',sw=4)
    else:
        s+=circle(89,42,24,hair)+path('M 79 104 Q 57 83 81 49 Q 116 25 153 44 Q 184 59 177 99 L 162 88 L 151 64 Q 123 87 88 84 L 89 111 Z',hair)
        s+=path('M 92 56 q 8 -7 17 -7 M 116 46 q 13 -4 23 3',stroke='#916b52',sw=3)
    s+=face(126,103)
    svg(f'customer_{idx}',s)
    # Moving guests have no chair or dish; their easy stance reads as walking
    # when the runtime adds its small alternating bob.
    walk=s
    for unwanted in [
        path('M 80 163 L 74 227 L 91 237 L 106 182 L 153 182 L 166 234 L 183 229 L 172 159 Z','#c79c68'),
        rect(76,161,98,36,9,'#d7b07d'),
        path('M 85 192 L 85 220 M 164 193 L 165 216',stroke='#95734e',sw=3),
        ellipse(128,174,40,10,'#90ae9d',sw=4), ellipse(128,169,40,10,CREAM,sw=4),
        path('M 107 163 Q 112 151 133 153 L 147 162 Q 132 173 108 168 Z',CORAL,sw=3),
        path('M 118 155 l 8 10 M 131 155 l 7 10',stroke=CREAM,sw=2),
        path('M 101 154 L 111 140 M 105 157 L 115 144',stroke='#69553c',sw=3),
    ]: walk=walk.replace(unwanted,'')
    svg(f'customer_walk_{idx}',walk)
# Nose-up sub with cockpit, rivets, side tanks and rear fan.
sub=path('M 42 92 Q 14 99 13 124 L 14 161 Q 19 176 39 169 Z',GOLD)
sub+=path('M 119 92 Q 146 99 147 124 L 147 162 Q 138 178 123 168 Z',GOLD)
sub+=rect(10,125,22,29,7,'#e6a13b',sw=4)+rect(129,124,22,30,7,'#e6a13b',sw=4)
sub+=path('M 66 207 L 63 232 Q 53 226 42 232 L 40 242 Q 60 250 81 243 Q 105 250 120 241 L 117 232 Q 104 226 94 233 L 93 207 Z','#659597')
sub+=path('M 52 208 Q 26 185 29 145 L 31 75 Q 35 33 66 21 L 69 11 Q 81 2 94 11 L 97 22 Q 127 38 130 78 L 132 151 Q 132 195 105 209 Z',GOLD)
sub+=path('M 40 154 Q 72 172 120 155 L 120 189 Q 102 218 81 220 Q 51 217 39 188 Z','#98a398')
sub+=path('M 42 153 Q 75 162 119 153 M 45 66 Q 78 45 118 69 M 43 84 Q 40 112 42 126',stroke='#fff0ab',sw=6)
sub+=ellipse(80,98,32,35,CREAM,sw=5)+ellipse(80,98,23,26,'#46899f',sw=4)
sub+=path('M 65 91 Q 68 80 78 79 M 64 101 l 0 3',stroke='#c9edf0',sw=4)
sub+=path('M 69 182 L 72 213 M 90 184 L 93 211',sw=4)
sub+=ellipse(81,27,13,7,CREAM,sw=4)+path('M 50 44 Q 78 29 108 43',sw=3)
for x,y in [(45,76),(116,76),(44,143),(117,142),(52,183),(110,183)]: sub+=circle(x,y,2,INK,'none')
sub+=path('M 82 229 l 0 18',sw=5)
svg('submarine',sub,160,256)
# Sushi on warm porcelain plates, each visible at icon size.
def dishbase():
    return ellipse(128,182,109,42,'#e6d2ab',sw=5)+ellipse(127,174,110,42,CREAM,sw=5)+ellipse(128,174,86,27,'#f3dfb7',stroke='#d4bd93',sw=3)
def rice():
    s=path('M 53 148 Q 46 123 70 103 Q 118 91 171 111 Q 197 124 200 149 L 193 169 Q 134 191 65 171 Z',CREAM,sw=5)
    for x,y in [(69,151),(86,166),(112,171),(166,168),(184,148),(153,176),(61,138)]:s+=path(f'M {x} {y} l 5 2',stroke='#cfbea1',sw=3)
    return s
for kind in ['cucumber','salmon','shrimp','eel']:
    s=dishbase()
    if kind=='cucumber':
        for x,y in [(85,123),(151,151)]:
            s+=path(f'M {x-36} {y} L {x-34} {y+49} Q {x} {y+75} {x+35} {y+48} L {x+38} {y} Z','#3e5c50',sw=5)
            s+=ellipse(x,y,38,30,CREAM,sw=5)+ellipse(x,y,22,17,'#95bb68',sw=4)+path(f'M {x-7} {y-10} L {x-10} {y+6} L {x+8} {y+10} L {x+10} {y-8} Z','#bad581',sw=2)
            s+=path(f'M {x-25} {y+35} l 0 9 M {x+24} {y+26} l 0 12',stroke='#719477',sw=3)
    else:
        s+=rice()
        if kind=='salmon':
            s+=path('M 44 136 Q 44 96 94 80 Q 151 77 204 125 Q 212 136 204 152 Q 181 159 165 145 Q 121 118 80 139 Q 61 151 44 143 Z',CORAL,sw=5)
            s+=path('M 75 96 Q 103 108 117 127 M 100 87 Q 130 99 147 131 M 129 90 Q 157 107 177 143 M 156 103 Q 178 117 190 142',stroke='#ffd7b3',sw=6)
            s+=path('M 56 126 Q 70 104 86 101',stroke='#ffc39d',sw=3)
        elif kind=='shrimp':
            s+=path('M 51 138 Q 49 95 102 79 Q 146 72 175 117 L 184 123 L 197 104 L 209 118 L 220 105 L 227 129 L 208 144 L 202 158 L 179 147 Q 144 121 104 131 Q 82 149 51 138 Z','#ed9775',sw=5)
            s+=path('M 69 103 Q 95 115 93 133 M 91 85 Q 117 101 117 127 M 115 83 Q 143 100 142 130 M 141 92 Q 162 105 166 137',stroke='#fff0cd',sw=6)
            s+=path('M 189 128 l 14 10 M 201 120 l 2 15',stroke='#bc614e',sw=3)
        else:
            s+=path('M 44 133 Q 65 88 110 85 Q 165 89 211 130 L 204 150 Q 178 167 155 144 Q 110 125 67 150 Q 50 151 44 143 Z','#916750',sw=5)
            s+=path('M 65 116 L 183 139 M 77 102 L 200 130 M 56 130 L 168 153',stroke='#e6aa63',sw=5)
            s+=path('M 101 91 L 116 141 L 143 140 L 128 91 Z','#3e5c50',sw=4)
    svg(kind,s)
# Marine wildlife; clear silhouettes, coral warm species colors.
f=path('M 185 64 L 239 32 L 230 78 L 241 120 L 189 103 Z','#df7e62',sw=5)
f+=path('M 82 52 L 126 15 L 151 51 M 106 113 L 153 144 L 162 108','#e89a70',sw=5)
f+=path('M 15 84 Q 47 32 124 39 Q 184 43 204 83 Q 179 124 112 124 Q 51 127 15 84 Z','#efad81',sw=5)
f+=path('M 28 85 Q 86 112 174 91',stroke='#f9d1a6',sw=7)+path('M 132 55 Q 112 78 137 110 M 152 59 Q 137 78 157 101',stroke='#d68868',sw=3)
f+=circle(60,73,10,CREAM,sw=3)+circle(62,73,4,INK,'none')+path('M 22 88 q 18 12 26 2 M 102 80 l 23 12 -21 10',sw=3)
f+=ellipse(63,94,12,6,CORAL,'none')
svg('creature_salmon',f,256,160)
s=path('M 49 72 Q 45 29 89 27 Q 138 29 165 75 Q 195 79 202 62 L 198 37 L 223 42 L 243 30 L 246 59 Q 245 113 194 126 Q 131 148 92 104 Z','#efaa86',sw=5)
s+=path('M 74 34 Q 96 51 85 91 M 101 38 Q 118 62 105 106 M 125 52 Q 140 76 130 123 M 146 72 Q 163 91 159 129 M 167 82 L 182 129 M 189 80 l 19 39',stroke='#c87665',sw=4)
s+=path('M 55 63 Q 24 32 15 51 M 60 58 Q 44 9 22 16',stroke='#f9c6a3',sw=5)
s+=path('M 79 92 l -14 18 M 96 107 l -8 18 M 119 121 l -1 15',sw=4)
s+=ellipse(63,68,27,29,'#efaa86',sw=5)+circle(53,61,8,CREAM,sw=3)+circle(53,61,3,INK,'none')+path('M 42 79 q 10 8 20 1',sw=3)
s+=path('M 217 50 l 13 2 M 210 67 l 21 7',stroke='#fbe0b4',sw=4)
svg('creature_shrimp',s,256,160)
s=path('M 232 32 Q 184 34 197 76 Q 216 120 155 116 Q 135 117 129 91 Q 121 33 71 34 Q 26 37 13 83 Q 6 110 32 121 Q 66 128 82 94 Q 86 85 95 111 Q 105 151 159 146 Q 244 141 230 88 Q 214 52 232 32 Z','#81afa0',sw=5)
s+=path('M 220 44 Q 198 71 216 105 Q 216 134 164 136 Q 113 143 106 107 Q 91 62 75 80',stroke='#e6d699',sw=7)
s+=path('M 99 51 L 112 33 L 128 69 M 144 128 L 159 157 L 185 139','#c3bf80',sw=4)
s+=ellipse(41,77,28,30,'#94c1a6',sw=4)+circle(34,66,9,CREAM,sw=3)+circle(35,67,4,INK,'none')+path('M 18 86 q 15 14 31 0',sw=3)+ellipse(47,87,10,6,CORAL,'none')
s+=path('M 58 48 l 8 5 M 140 118 l 7 5 M 176 113 l 7 -5 M 211 82 l 5 -4',stroke='#477f79',sw=4)
svg('creature_eel',s,256,160)
# Salvage gear and supporting environment props.
s=''; cx=128;cy=128
pts=[]
for i in range(40):
    a=2*math.pi*i/40-math.pi/2;r=105 if i%4 in [0,1] else 84
    pts.append(f'{cx+math.cos(a)*r:.1f},{cy+math.sin(a)*r:.1f}')
s+=path('M '+' L '.join(pts)+' Z',GOLD,sw=8)+circle(128,128,56,'#dc9945',sw=7)+circle(128,128,34,CREAM,sw=7)+path('M 61 118 q 6 -37 41 -53 M 179 170 l -8 6',stroke='#ffe09a',sw=7)
svg('gear',s)
s=path('M 19 179 L 38 96 L 87 69 L 118 18 L 176 30 L 216 91 L 241 130 L 228 212 L 172 235 L 91 230 Z','#50737a',sw=7)
s+=path('M 38 96 L 89 127 L 118 18 M 89 127 L 128 183 L 173 153 L 216 91 M 128 183 L 91 230 M 173 153 L 228 212 M 176 30 L 154 84 L 173 153',stroke='#294c57',sw=5)
s+=path('M 127 40 l 30 1 M 49 110 l -11 53 M 186 174 l 27 26',stroke='#83a09c',sw=5)
s+=path('M 85 141 l -10 26 16 19 M 189 83 l 5 9',stroke='#345c63',sw=3)
svg('rock',s)
s=path('M 25 219 L 13 124 L 36 35 L 66 16 L 86 47 L 73 91 L 84 143 L 63 236 Z','#578187',sw=5)
s+=path('M 183 235 L 174 147 L 186 94 L 174 45 L 194 16 L 224 38 L 243 126 L 232 219 Z','#578187',sw=5)
s+=path('M 36 203 L 38 143 L 51 112 L 41 81 L 59 49 M 203 46 L 213 87 L 198 117 L 212 157 L 211 202',stroke='#244d5e',sw=4)
s+=ellipse(128,131,55,88,'#66d4cd','#a9f3d7',7,extra='opacity=".3"')+ellipse(128,131,48,80,'none','#6cdbc9',5)
s+=path('M 103 96 Q 139 55 155 106 Q 163 140 136 155 Q 118 166 107 144 Q 101 126 122 119 Q 139 113 139 128',stroke='#c2efd8',sw=5)
s+=path('M 28 126 l 17 -19 19 20 -16 18 Z M 193 126 l 15 -19 19 20 -16 18 Z',TEAL,'#9be7d0',4)
svg('portal',s)
s=path('M 106 199 Q 75 181 58 108 Q 105 104 124 186 Q 123 129 102 60 Q 148 78 142 175 Q 155 105 201 75 Q 206 142 151 190 Q 141 136 168 21 Q 188 78 156 175 Q 118 119 62 48 Q 48 104 111 187 Z',MINT,sw=5)
s+=path('M 128 206 L 133 139 M 121 185 L 76 73 M 148 188 L 187 105 M 144 170 L 167 55',stroke='#567e58',sw=4)
s+=path('M 66 192 Q 122 172 184 193 L 173 234 Q 124 259 79 234 Z','#c58e63',sw=5)+ellipse(125,191,60,16,'#ad7857',sw=5)
s+=path('M 89 214 l 5 14 M 156 214 l -3 14',stroke='#e1b87b',sw=4)
svg('plant',s)
s=path('M 117 6 L 117 26 M 108 27 L 147 27',sw=5)+path('M 88 41 Q 62 47 58 76 L 58 180 Q 62 211 91 215 L 160 215 Q 190 210 194 180 L 194 78 Q 190 48 163 41 Z',CREAM,sw=6)
s+=rect(84,31,83,19,7,GOLD,sw=4)+rect(85,208,83,18,6,GOLD,sw=4)
s+=path('M 65 78 Q 128 93 188 78 M 65 105 Q 128 120 188 105 M 65 134 Q 128 149 188 134 M 65 162 Q 128 177 188 162 M 70 188 Q 128 202 182 188',stroke='#d3ba86',sw=3)
s+=path('M 94 131 Q 122 103 153 130 Q 122 157 94 131 Z M 153 130 L 167 117 L 166 144 Z',CORAL,sw=4)+circle(106,127,3,INK,'none')+path('M 123 115 q 14 15 0 29',sw=3)
s+=path('M 126 226 L 126 247 M 111 245 L 140 245',stroke=CORAL,sw=5)
svg('lantern',s)
# Unbranded app icon and welcome illustration.
icon=rect(6,6,244,244,52,'#ead9b3',sw=0)+path('M 8 177 Q 50 144 96 168 Q 136 192 189 158 Q 224 142 249 156 L 249 243 L 8 243 Z','#71a8a1',sw=0)
icon+='<g transform="translate(76 12) scale(.60)">'+sub+'</g>'
icon+='<g transform="translate(7 102) scale(.60)">'+(OUT/'salmon.svg').read_text().split('>',1)[1].rsplit('</svg>',1)[0]+'</g>'
icon+=path('M 39 46 l 0 17 M 31 55 l 16 0 M 211 72 l 0 13 M 205 78 l 13 0',stroke=CREAM,sw=5)
svg('icon',icon)
cover=rect(0,0,720,1050,0,CREAM,sw=0)
cover+=path('M 0 584 Q 180 550 348 592 Q 539 632 720 564 L 720 1050 L 0 1050 Z','#2b727b',sw=0)
cover+=path('M 0 640 Q 201 606 396 648 Q 573 683 720 631 M 0 688 Q 201 654 396 696 Q 573 731 720 679',stroke='#529894',sw=3)
# Restaurant doorway, canopy, lamps and countertop.
cover+=rect(167,161,389,425,18,'#d7b787',sw=7)+rect(188,184,346,352,3,'#475c54',sw=6)
cover+=rect(169,161,386,36,8,'#be9366',sw=6)
for x in [192,304,416]: cover+=path(f'M {x} 198 L {x+107} 198 L {x+103} 329 Q {x+48} 341 {x} 326 Z',CORAL,sw=5)
cover+=path('M 276 263 Q 323 219 368 265 Q 324 305 276 263 Z M 368 265 L 401 238 L 401 292 Z',CREAM,CREAM,5)+circle(294,261,4,CORAL,'none')+path('M 330 232 Q 350 262 331 292',stroke=CORAL,sw=4)
cover+='<g transform="translate(48 197) scale(.48)">'+(OUT/'lantern.svg').read_text().split('>',1)[1].rsplit('</svg>',1)[0]+'</g>'
cover+='<g transform="translate(559 197) scale(.48)">'+(OUT/'lantern.svg').read_text().split('>',1)[1].rsplit('</svg>',1)[0]+'</g>'
cover+='<g transform="translate(250 339) scale(.94)">'+chef+'</g>'
cover+=rect(82,548,559,32,12,'#c08663',sw=7)+rect(100,580,523,34,5,'#a57353',sw=6)
cover+='<g transform="translate(42 460) scale(.53)">'+(OUT/'plant.svg').read_text().split('>',1)[1].rsplit('</svg>',1)[0]+'</g>'
cover+='<g transform="translate(542 452) scale(.53)">'+(OUT/'plant.svg').read_text().split('>',1)[1].rsplit('</svg>',1)[0]+'</g>'
cover+='<g transform="translate(282 706) rotate(-14 80 128) scale(1.1)">'+sub+'</g>'
cover+='<g transform="translate(25 719) scale(.64)">'+f+'</g>'
cover+='<g transform="translate(504 888) scale(.58)">'+(OUT/'creature_shrimp.svg').read_text().split('>',1)[1].rsplit('</svg>',1)[0]+'</g>'
for x,y,r in [(254,901,8),(239,937,13),(262,978,18),(478,740,13),(497,710,7),(94,925,8),(605,752,11)]: cover+=circle(x,y,r,'none','#80b9ae',3)
for x,y in [(90,391),(621,403),(494,76),(209,81)]:cover+=path(f'M {x} {y-12} l 0 24 M {x-12} {y} l 24 0',stroke=GOLD,sw=4)
svg('cover',cover,720,1050)
# Background compositions keep central play area quiet and contain no text.
ocean=rect(0,0,720,1280,0,NAVY,sw=0)
ocean+=path('M 160 0 Q 290 300 179 539 Q 260 856 208 1280 L 550 1280 Q 483 881 556 596 Q 454 220 576 0 Z','#1c4d5b',sw=0)
rng=random.Random(11)
for side in [0,1]:
    for y in range(-80,1360,150):
        x=-60+rng.randrange(40) if side==0 else 617+rng.randrange(35)
        ocean+=f'<g transform="translate({x} {y}) scale(.66)">'+(OUT/'rock.svg').read_text().split('>',1)[1].rsplit('</svg>',1)[0]+'</g>'
for i in range(60):
    x=rng.randrange(90,630);y=rng.randrange(1280)
    ocean+=ellipse(x,y,rng.randrange(2,7),rng.randrange(2,5),'#3e7278','none',extra='opacity=".6"')
svg('ocean_background',ocean,720,1280)
# WAV synthesizer. The 8-bar 120 BPM themes loop exactly; all motifs are original.
SR=22050
rng=random.Random(31)
def wav_write(name,L,R):
    peak=max(max(abs(x) for x in L),max(abs(x) for x in R),1e-4)
    gain=min(.88/peak,1.0)
    data=array.array('h')
    for l,r in zip(L,R):data.extend((int(max(-1,min(1,l*gain))*32767),int(max(-1,min(1,r*gain))*32767)))
    with wave.open(str(OUT/f'{name}.wav'),'wb') as wf:wf.setparams((2,2,SR,len(L),'NONE','not compressed'));wf.writeframes(data.tobytes())
def note(L,R,t,d,midi,amp=.2,kind='keys',pan=0,loop=False):
    f=440*2**((midi-69)/12); n=int(d*SR);start=int(t*SR)
    for i in range(n):
        sec=i/SR;env=min(1,sec/.006)*max(0,1-sec/d)**1.5
        if kind=='bass':v=(math.sin(2*math.pi*f*sec)+.22*math.sin(4*math.pi*f*sec))*math.exp(-sec*3)
        elif kind=='bell':v=(math.sin(2*math.pi*f*sec)+.38*math.sin(2*math.pi*f*2.01*sec)*math.exp(-sec*8)+.12*math.sin(2*math.pi*f*4*sec))*math.exp(-sec*2.4)
        else:v=(math.sin(2*math.pi*f*sec)+.35*math.sin(4*math.pi*f*sec)*math.exp(-sec*9)+.13*math.sin(6*math.pi*f*sec))*math.exp(-sec*4)
        j=(start+i)%len(L) if loop else start+i
        if j>=len(L):break
        v*=env*amp;L[j]+=v*math.sqrt((1-pan)/2);R[j]+=v*math.sqrt((1+pan)/2)
def music(name,water=False):
    L=[0.0]*(SR*16);R=L.copy();chords=[[53,57,60,64],[50,53,57,60],[55,58,62,65],[48,52,58,62]]
    melody=[72,76,77,79,76,72,69,72,74,77,81,79,77,74,72,70]
    for bar in range(8):
        chord=chords[bar%4];t=bar*2
        for beat in [0,1,2,3]:
            note(L,R,t+beat*.5,.55,chord[0]-12,.16,'bass',-.2,True)
        for beat in [0,.75,2,2.75]:
            for n in chord[1:]:note(L,R,t+beat*.5,1.2 if water else .42,n+12,.038 if water else .054,'bell' if water else 'keys',-.36,True)
        for j,beat in enumerate([.5,1.5,2.75]):
            pitch=melody[(bar*2+j)%len(melody)]+(0 if water else 12)
            note(L,R,t+beat*.5,.7 if water else .38,pitch,.105 if water else .11,'bell',.35,True)
        # Quiet brush percussion; high-pass by difference of adjacent samples.
        for beat in range(8):
            st=int((t+beat*.25)*SR);prev=0
            for k in range(int(SR*.065)):
                value=rng.uniform(-1,1);noise=(value-prev)*.012*(1-k/(SR*.065))**3;prev=value
                j=(st+k)%len(L);L[j]+=noise*.7;R[j]+=noise
        # Muted woodblock, never a hard digital click.
        if not water:
            for beat in [1,3]:note(L,R,t+beat*.5,.08,94,.07,'keys',.2,True)
    wav_write(name,L,R)
music('restaurant');music('ocean',True)
def effect(name,notes,duration=.7):
    L=[0.0]*int(SR*duration);R=L.copy()
    for t,d,m,a,k in notes:note(L,R,t,d,m,a,k,0)
    # tiny fade ensures no edge click
    for i in range(min(200,len(L))):
        f=i/200;L[i]*=f;R[i]*=f;L[-1-i]*=f;R[-1-i]*=f
    wav_write(name,L,R)
effect('click',[(0,.085,84,.32,'keys')],.12)
effect('coin',[(0,.18,88,.27,'bell'),(.065,.25,95,.21,'bell')],.38)
effect('build',[(0,.12,55,.35,'keys'),(.09,.12,62,.30,'keys'),(.17,.35,74,.25,'bell')],.60)
effect('upgrade',[(0,.22,72,.24,'bell'),(.10,.22,76,.24,'bell'),(.20,.25,79,.24,'bell'),(.30,.55,84,.27,'bell')],.95)
effect('sonar',[(0,.9,88,.30,'bell'),(.30,.7,88,.09,'bell')],1.1)
effect('harpoon',[(0,.08,43,.4,'bass'),(.025,.12,76,.21,'keys')],.23)
effect('hit',[(0,.15,32,.48,'bass'),(.04,.18,36,.31,'keys')],.3)
effect('catch',[(0,.25,72,.27,'bell'),(.1,.28,76,.28,'bell'),(.2,.3,79,.26,'bell'),(.36,.55,84,.28,'bell')],1.0)
effect('win',[(0,.30,72,.25,'bell'),(.16,.30,76,.25,'bell'),(.32,.30,79,.25,'bell'),(.50,1.0,84,.3,'bell'),(.50,1,72,.13,'bell'),(.50,1,76,.13,'bell')],1.6)
effect('splash',[(0,.18,43,.24,'bass'),(.06,.20,74,.18,'bell'),(.11,.18,81,.13,'bell'),(.18,.20,88,.08,'bell')],.48)
effect('warning',[(0,.19,64,.23,'bell'),(.24,.19,64,.23,'bell')],.5)
effect('boost',[(0,.16,60,.20,'bell'),(.06,.16,67,.2,'bell'),(.12,.22,74,.20,'bell')],.4)
for alias,target in {'pickup':'coin','shot':'harpoon','hook':'build','portal':'sonar','ui':'click'}.items():shutil.copyfile(OUT/f'{target}.wav',OUT/f'{alias}.wav')
print('Wrote original SVG artwork and stereo WAV effects/music to',OUT)

# Outcome illustrations. The receipt occupies x75..645 / y360..960;
# characters and all deliberate detail stay above/below that protected region.
def existing(name):return (OUT/(name+'.svg')).read_text().split('>',1)[1].rsplit('</svg>',1)[0]
def placed(name,x,y,scale=1,angle=0,cx=128,cy=128):
    return f'<g transform="translate({x} {y}) scale({scale}) rotate({angle} {cx} {cy})">'+existing(name)+'</g>'
def waterlines(y,color='#6daaa1'):
    result=''
    for i in range(8):
        yy=y+i*42;off=(i%2)*60
        result+=path(f'M {22+off} {yy} q 21 -7 46 0 M {175+off} {yy+7} q 32 -8 64 0 M {417-off} {yy-5} q 24 -6 52 0 M 619 {yy+9} q 23 -7 48 0',stroke=color,sw=3)
    return result

def kelp(x,y,scale=1,color='#4d8a7b'):
    return f'<g transform="translate({x} {y}) scale({scale})">'+path('M 20 156 Q 34 107 11 70 Q -4 43 14 8 M 23 135 Q 57 96 40 61 Q 35 45 44 21 M 19 156 Q 5 136 -4 102 Q -13 73 -3 61',stroke=INK,sw=12)+path('M 20 156 Q 34 107 11 70 Q -4 43 14 8 M 23 135 Q 57 96 40 61 Q 35 45 44 21 M 19 156 Q 5 136 -4 102 Q -13 73 -3 61',stroke=color,sw=6)+'</g>'

v=rect(0,0,506,432,20,CREAM,'none',0)
v+=path('M 0 293 Q 74 275 155 300 Q 232 322 307 295 Q 400 278 506 306 L 506 432 L 0 432 Z','#72aaa0','none',0)
v+=path('M 0 348 Q 89 326 167 350 Q 243 375 330 353 Q 426 330 506 354 L 506 432 L 0 432 Z','#3c7f86','none',0)
v+=rect(158,24,269,245,10,'#c69b6b',sw=5)+rect(178,48,229,210,4,'#405a51',sw=5)
v+=rect(148,17,291,30,7,'#bf9264',sw=5)
for x in [177,253,329]:v+=path(f'M {x} 49 L {x+75} 49 L {x+73} 137 Q {x+36} 147 {x} 136 Z',CORAL,sw=4)
v+=path('M 238 93 Q 263 69 289 94 Q 263 119 238 93 Z M 289 94 L 309 79 L 309 108 Z',CREAM,CREAM,3)+circle(246,92,2,CORAL,'none')+path('M 269 78 q 9 14 0 30',stroke=CORAL,sw=3)
v+=placed('chef',201,116,.63)
v+=rect(108,256,345,20,7,'#b77d5c',sw=5)+rect(124,276,312,17,2,'#d4b382',sw=4)
v+=placed('lantern',76,18,.33)+placed('lantern',428,43,.28)
v+=placed('plant',399,211,.33)
v+=placed('submarine',79,292,.48,20,80,128)
v+=placed('salmon',321,291,.60)
v+=path('M 18 370 q 21 -7 46 0 M 198 398 q 21 -7 46 0 M 376 412 q 21 -7 46 0 M 238 335 q 21 -7 46 0',stroke='#a0cdc0',sw=3)
for x,y in [(49,217),(469,174),(134,103)]:v+=path(f'M {x} {y-8} l 0 16 M {x-8} {y} l 16 0',stroke=GOLD,sw=3)
svg('title_vignette',v,506,432)

# Successful voyage: sunset harbor with a warmly lit little kitchen.
bg=rect(0,0,720,1280,0,'#f4dbaa','none',0)
bg+=circle(517,197,89,'#eeb45b','none')+path('M 0 235 Q 100 222 182 236 Q 291 227 392 239 Q 493 226 590 240 Q 659 222 720 235 L 720 1280 L 0 1280 Z','#71a7a1','none',0)
bg+=path('M 0 276 Q 175 242 341 281 Q 511 312 720 259 L 720 1280 L 0 1280 Z','#4f8d8e','none',0)
bg+=path('M 0 937 Q 156 916 336 951 Q 533 974 720 939 L 720 1280 L 0 1280 Z','#386e79','none',0)
# Background shoreline and pier, above the receipt.
bg+=path('M 0 222 L 72 215 L 92 201 L 108 211 L 158 194 L 175 213 L 226 218 L 272 213 L 299 232 L 0 258 Z','#b49b79','none',0)
bg+=rect(49,149,195,111,6,'#c49b70',sw=4)+rect(66,167,160,80,3,'#536b5c',sw=4)
bg+=path('M 38 157 L 91 115 L 231 127 L 257 160 Z',CORAL,sw=5)
for xx in [76,122,168]:bg+=path(f'M {xx} 169 L {xx+42} 169 L {xx+40} 209 L {xx} 208 Z','#eaae7b',sw=3)
bg+=path('M 105 239 L 115 308 M 215 243 L 222 294 M 42 257 L 280 265 M 44 268 L 282 276',stroke='#896b52',sw=8)
bg+=placed('lantern',250,161,.25)
bg+=path('M 420 113 q 10 -10 20 0 q 10 -10 20 0 M 597 155 q 9 -9 18 0 q 9 -9 18 0',stroke='#886f50',sw=3)
bg+=waterlines(950,'#6ca49e')
bg+=placed('submarine',442,1004,.77,24,80,128)
bg+=path('M 289 1089 Q 351 1068 408 1098 M 288 1110 Q 358 1093 413 1120',stroke='#a7cec0',sw=5)
bg+=placed('gear',63,1118,.26,-15)
bg+=path('M 552 986 l 0 18 M 543 995 l 18 0 M 631 1080 l 0 14 M 624 1087 l 14 0',stroke='#eed599',sw=4)
svg('results_complete',bg,720,1280)

# Early return: quiet corridor, deep water and a small distant harbor light.
bg=rect(0,0,720,1280,0,'#173f50','none',0)
bg+=path('M 262 0 Q 166 206 239 394 Q 185 726 236 979 Q 163 1178 202 1280 L 557 1280 Q 548 1132 477 964 Q 533 668 479 395 Q 535 185 444 0 Z','#285b69','none',0)
bg+=path('M 290 0 Q 278 218 335 391 L 398 394 Q 459 215 429 0 Z','#437b81','none',0)
for yy,xx,sc in [(52,-51,.78),(257,-72,.56),(946,-73,.71),(1118,-54,.74),(48,570,.79),(260,658,.48),(934,597,.77),(1143,631,.60)]:bg+=placed('rock',xx,yy,sc)
bg+=placed('portal',278,130,.67)
bg+=kelp(45,1018,.9,'#649586')+kelp(656,975,.9,'#649586')+kelp(70,150,.67,'#4f8c81')
bg+=waterlines(960,'#467b83')
bg+=placed('submarine',303,1027,.73,-9,80,128)
bg+=path('M 317 1009 L 352 834 L 393 1004 Z','#6caaa4','none',0,extra='opacity=".13"')
for x,y,r in [(373,1240,8),(386,1264,12),(243,1163,8),(218,1139,5),(473,244,8),(493,217,4)]:bg+=circle(x,y,r,'none','#80b6af',3)
svg('results_early',bg,720,1280)

# Hull-depleted presentation: a sheltered rocky alcove and scuffed panels.
# Damage is visual only; no rescue/repair/lost-salvage mechanics implied.
bg=rect(0,0,720,1280,0,'#273c4d','none',0)
bg+=path('M 128 0 L 592 0 Q 460 171 506 347 Q 582 522 499 768 Q 515 1006 582 1280 L 100 1280 Q 226 1099 195 917 Q 148 712 225 509 Q 262 268 128 0 Z','#375464','none',0)
for yy,xx,sc in [(-90,-4,1.2),(120,-43,.85),(944,-83,.78),(1125,-47,.87),(-36,531,1.15),(200,620,.73),(929,624,.76),(1125,562,.97)]:bg+=placed('rock',xx,yy,sc)
bg+=path('M 146 196 Q 224 114 330 107 Q 479 102 566 206',stroke='#6c8790',sw=5)
bg+=path('M 168 187 L 168 199 M 484 166 L 493 176 M 227 143 L 238 139',stroke='#a0a99e',sw=4)
bg+=kelp(602,1084,.65,'#986e7d')+kelp(85,206,.48,'#789184')
bg+=path('M 147 1201 Q 311 1145 574 1204 L 601 1280 L 102 1280 Z','#4c646c',sw=5)
bg+=path('M 177 1220 Q 329 1184 513 1216',stroke='#71827e',sw=4)
bg+='<g transform="translate(293 982) scale(.79) rotate(-25 80 128)">'+existing('submarine')+path('M 48 135 l 15 11 M 51 129 l 10 9 M 93 52 l 17 9 M 90 57 l 14 9',stroke='#927654',sw=3)+path('M 109 158 l -11 14 13 13',stroke=INK,sw=3)+'</g>'
for x,y,r in [(392,954,11),(411,911,7),(390,870,4),(553,269,7),(536,245,4)]:bg+=circle(x,y,r,'none','#7ca6ab',3)
bg+=path('M 505 1125 l 6 3 M 463 1250 l 19 -4 M 235 1225 l 21 -6',stroke='#95a19a',sw=4)
svg('results_failed',bg,720,1280)
print('Wrote presentation vignette and three distinct outcome backgrounds')

# Warm restaurant clearance props: variation for the blocked floor perimeter.
crate=ellipse(126,232,112,13,'#344b42','none',extra='opacity=".17"')
crate+=path('M 33 63 L 192 45 L 231 78 L 224 214 L 72 235 L 23 204 Z','#aa7955',sw=6)
crate+=path('M 33 63 L 79 96 L 231 78 L 192 45 Z','#e3bc84',sw=5)
crate+=path('M 79 96 L 74 234 L 224 214 L 231 78 Z','#cfa16c',sw=5)
crate+=path('M 30 76 L 68 103 L 63 220 L 31 199 Z','#bc8d61',sw=4)
crate+=path('M 83 113 L 227 97 M 80 164 L 225 146 M 78 215 L 223 195',stroke='#95724f',sw=4)
crate+=path('M 53 79 L 206 59 M 67 89 L 219 72 M 40 104 L 38 183 M 53 114 L 50 197',stroke='#b0855a',sw=3)
crate+=path('M 89 104 L 109 101 L 216 194 L 214 216 L 195 217 Z','#e2b981',sw=4)
crate+=path('M 213 93 L 230 94 L 223 118 L 93 226 L 74 223 L 76 202 Z','#e2b981',sw=4)
for x,y in [(97,112),(210,204),(216,106),(86,211)]:crate+=circle(x,y,2.4,INK,'none')
crate+=path('M 110 147 l 12 -2 M 154 190 l 14 -2 M 145 74 l 18 -2',stroke='#f4d299',sw=3)
svg('crate',crate)
rubble=ellipse(127,228,113,15,'#344b42','none',extra='opacity=".16"')
rubble+=path('M 16 189 L 47 125 L 89 117 L 121 169 L 107 225 L 50 232 Z','#778c83',sw=6)
rubble+=path('M 47 125 L 64 178 L 16 189 M 64 178 L 107 225 M 64 178 L 121 169',stroke='#4b645f',sw=4)
rubble+=path('M 130 158 L 159 111 L 206 121 L 235 162 L 223 218 L 170 229 L 135 201 Z','#9eaa93',sw=6)
rubble+=path('M 159 111 L 175 170 L 206 121 M 175 170 L 223 218 M 175 170 L 135 201',stroke='#687c6c',sw=4)
rubble+=path('M 26 192 L 199 56 L 214 64 L 211 79 L 221 83 L 57 224 L 36 217 Z','#c69766',sw=5)
rubble+=path('M 43 197 L 187 81 M 58 207 L 198 88',stroke='#e4bf89',sw=3)
rubble+=path('M 63 96 L 72 78 L 219 183 L 211 200 L 188 197 Z','#bb875d',sw=5)
rubble+=path('M 79 99 L 204 186',stroke='#e2b582',sw=3)
rubble+=path('M 41 87 L 61 74 L 71 43 L 99 36 L 104 54 L 91 72 L 86 103 L 64 117 Z','#708e8a',sw=5)
rubble+=path('M 74 44 L 95 40 M 56 88 l 10 -3',stroke='#a3b7a0',sw=3)
rubble+=circle(125,185,9,'#80694d',sw=3)+circle(125,185,3,CREAM,sw=2)
rubble+=path('M 17 236 L 29 224 L 47 230 L 43 243 Z','#b7b299',sw=3)+path('M 235 221 L 244 232 L 238 241 L 227 236 Z','#748b7f',sw=3)
svg('rubble',rubble)
print('Wrote four standing customer variants, crate and rubble')
