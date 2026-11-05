from pathlib import Path
import json
import numpy as np
import pyogrio
from pyogrio.raw import read, write
import shapely
from shapely.ops import transform, orient
from pyproj import Transformer
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.path import Path as MplPath
from matplotlib.patches import PathPatch, Patch
from matplotlib.lines import Line2D
from matplotlib.font_manager import FontProperties

BASE=Path(__file__).resolve().parent
SRC=BASE/'原始解包/丰台数据/数据/丰台数据/丰台数据'
OUT=BASE/'可用地图'
OUT.mkdir(exist_ok=True)
target=OUT/'丰台基础地图.gpkg'
if target.exists(): raise SystemExit('Output exists; preserve the existing export.')
layers={}
checks=[]
for name in ('丰台政区','植被','水系','道路','铁路'):
    meta,fids,wkb,data=read(SRC/(name+'.TAB'),return_fids=True)
    write(target,geometry=wkb,field_data=data,fields=meta['fields'],layer=name,driver='GPKG',geometry_type=meta['geometry_type'],crs=meta['crs'],layer_metadata={'source':str((SRC/(name+'.TAB')).relative_to(BASE)), 'note':'Original geometry and attributes; CRS follows source metadata and is not independently verified. Missing-value sentinels remain unchanged.'})
    outmeta,_,outwkb,outdata=read(target,layer=name)
    assert len(wkb)==len(outwkb)
    assert list(meta['fields'])==list(outmeta['fields'])
    assert meta['crs']==outmeta['crs']
    assert bool(shapely.equals_exact(shapely.from_wkb(wkb),shapely.from_wkb(outwkb),tolerance=0).all())
    for a,b in zip(data,outdata):
        if a.dtype.kind=='f': assert np.array_equal(a,b,equal_nan=True)
        else: assert np.array_equal(a,b)
    checks.append({'layer':name,'records':len(wkb),'crs':meta['crs'],'geometry_and_attributes_roundtrip_equal':True})
    layers[name]=shapely.from_wkb(wkb)
(OUT/'转换核验.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')

font=FontProperties(fname='/Library/Fonts/Arial Unicode.ttf')
plt.rcParams['font.family']=font.get_name()
plt.rcParams['axes.unicode_minus']=False
project=Transformer.from_crs('EPSG:4326','EPSG:32650',always_xy=True).transform
def project_km(x,y,z=None):
    X,Y=project(x,y)
    return np.asarray(X)/1000,np.asarray(Y)/1000
projected={name:[transform(project_km,g) for g in geoms] for name,geoms in layers.items()}
fig,ax=plt.subplots(figsize=(13.5,7.2),dpi=150)
fig.subplots_adjust(left=.065,right=.98,top=.86,bottom=.21)
fig.patch.set_facecolor('#f8fafc');ax.set_facecolor('#ffffff')

def draw_poly(g,color,edge=None,lw=0):
    if g.geom_type=='MultiPolygon':
        for p in g.geoms: draw_poly(p,color,edge,lw)
        return
    g=orient(g,sign=1.0)
    verts=[];codes=[]
    for ring in (g.exterior,*g.interiors):
        a=np.asarray(ring.coords)
        verts.extend(a);codes.extend([MplPath.MOVETO]+[MplPath.LINETO]*(len(a)-2)+[MplPath.CLOSEPOLY])
    ax.add_patch(PathPatch(MplPath(verts,codes),facecolor=color,edgecolor=edge,linewidth=lw))

for g in projected['植被']:draw_poly(g,'#a8cfa1')
for g in projected['水系']:draw_poly(g,'#86bce0')
ax.add_collection(LineCollection([np.asarray(g.coords) for g in projected['道路']],colors='#7d8792',linewidths=.22,alpha=.75))
for g in projected['丰台政区']:draw_poly(g,'none','#334155',.85)
b=shapely.total_bounds(projected['丰台政区'])
ax.set_xlim(b[0]-.5,b[2]+.5);ax.set_ylim(b[1]-.6,b[3]+.6);ax.set_aspect('equal')
ax.set_xlabel('投影横坐标 / km');ax.set_ylabel('投影纵坐标 / km')
ax.tick_params(labelsize=9);ax.grid(alpha=.12)
for s in ax.spines.values():s.set_color('#cbd5e1')
fig.suptitle('丰台历史地图：道路、植被与水系',x=.065,ha='left',y=.97,fontsize=20,color='#172554')
fig.text(.065,.914,'从老师提供的地图文件读取  ·  26,145 条道路  /  730 个植被面  /  104 个水系要素',fontsize=11,color='#475569')
fig.legend(handles=[Line2D([0],[0],color='#7d8792',lw=1,label='道路'),Patch(facecolor='#a8cfa1',label='植被'),Patch(facecolor='#86bce0',label='水系'),Line2D([0],[0],color='#334155',lw=1,label='政区边界')],loc='lower left',bbox_to_anchor=(.06,.095),ncol=4,frameon=False,fontsize=11)
fig.text(.065,.065,'按源文件 WGS84 标记投影显示，尚未做实地配准；这不是已验证的定向越野地图。',fontsize=10,color='#475569')
fig.text(.065,.031,'空白处表示这些图层未描述其地表性质，不代表开阔地或可通行区域。',fontsize=10,color='#475569')
fig.savefig(BASE/'丰台地图预览.png',dpi=150)
plt.close(fig)
print('Export validated:',target)
print('Preview saved:',BASE/'丰台地图预览.png')
