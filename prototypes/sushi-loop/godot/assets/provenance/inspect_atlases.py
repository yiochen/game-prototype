"""Read-only alpha/component inspection. Requires Pillow and NumPy."""
from pathlib import Path
import numpy as np
from PIL import Image

def components(path, threshold=16):
    im=Image.open(path)
    mask=np.asarray(im.getchannel('A'))>threshold
    parent=[]; bounds=[]; area=[]; previous=[]
    def root(i):
        while parent[i]!=i:
            parent[i]=parent[parent[i]]; i=parent[i]
        return i
    def merge(a,b):
        a,b=root(a),root(b)
        if a!=b:
            parent[b]=a
            bounds[a]=[min(bounds[a][0],bounds[b][0]),min(bounds[a][1],bounds[b][1]),max(bounds[a][2],bounds[b][2]),max(bounds[a][3],bounds[b][3])]
            area[a]+=area[b]
        return a
    for y,row in enumerate(mask):
        edges=np.diff(np.pad(row.astype(np.int8),(1,1)))
        starts=np.flatnonzero(edges==1); ends=np.flatnonzero(edges==-1)
        current=[]; p=0
        for start,end in zip(starts,ends):
            start,end=int(start),int(end)
            i=len(parent);parent.append(i);bounds.append([start,y,end,y+1]);area.append(end-start)
            while p<len(previous) and previous[p][1]<start:p+=1
            k=p
            while k<len(previous) and previous[k][0]<=end:
                i=merge(i,previous[k][2]);k+=1
            current.append((start,end,i))
        previous=current
    return sorted([(area[i],bounds[i]) for i in range(len(parent)) if parent[i]==i and area[i]>8],reverse=True)

if __name__=='__main__':
    for name in ['chef','customers','props','belts','clutter']:
        path=Path(__file__).parent.parent/'production'/f'{name}.png'
        if path.exists():print(name,components(path)[:24])
