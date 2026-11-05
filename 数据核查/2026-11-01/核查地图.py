from pathlib import Path
from collections import Counter
import json, math, hashlib, warnings
import numpy as np
import pyogrio
from pyogrio.raw import read
import shapely

BASE = Path(__file__).resolve().parent
SOURCE = BASE / '原始解包/丰台数据'

def clean(v):
    if isinstance(v, dict): return {str(k):clean(x) for k,x in v.items()}
    if isinstance(v, (list, tuple, np.ndarray)): return [clean(x) for x in v]
    if isinstance(v, np.generic): return clean(v.item())
    if isinstance(v, float) and not math.isfinite(v): return None
    return v

rows=[]
for path in sorted(SOURCE.rglob('*.TAB')):
    row={'path':str(path.relative_to(SOURCE)), 'name':path.stem}
    try:
        with warnings.catch_warnings(record=True) as ws:
            warnings.simplefilter('always')
            # GDAL converts the TAB-declared WindowsSimpChinese text to UTF-8.
            info=pyogrio.read_info(path, force_feature_count=True, force_total_bounds=True)
            meta,fids,wkb,columns=read(path,return_fids=True)
        row['info']=clean(info)
        row['warnings']=list(dict.fromkeys(str(w.message) for w in ws))
        row['read_records']=len(fids)
        gs=shapely.from_wkb(wkb) if wkb is not None else np.array([],dtype=object)
        present=~shapely.is_missing(gs)
        nonempty=present & ~shapely.is_empty(gs)
        row['null_geometry']=int((~present).sum())
        row['empty_geometry']=int((present & shapely.is_empty(gs)).sum())
        row['geometry_types']=dict(Counter(g.geom_type for g in gs[nonempty]))
        row['invalid_geometry']=int((nonempty & ~shapely.is_valid(gs)).sum())
        row['invalid_reasons']=dict(Counter(str(x).split('[')[0] for x in shapely.is_valid_reason(gs[nonempty & ~shapely.is_valid(gs)])))
        row['z_geometry']=int(shapely.has_z(gs).sum())
        row['fields']={}
        for name,values in zip(meta['fields'],columns):
            vals=[clean(v) for v in values]
            missing=sum(v is None or (isinstance(v,str) and not v.strip()) for v in vals)
            c=Counter(str(v) for v in vals if v is not None and (not isinstance(v,str) or v.strip()))
            literal_null=sum(isinstance(v,str) and v.strip().upper()=='NULL' for v in vals)
            stat={'nonempty':len(vals)-missing,'literal_NULL_count':literal_null,'nonempty_excluding_literal_NULL':len(vals)-missing-literal_null,'unique_nonempty':len(c),'zero_count':sum(isinstance(v,(int,float)) and v==0 for v in vals),'suspected_numeric_sentinel_count':sum(isinstance(v,(int,float)) and (v==-32767 or abs(v+999999.9)<0.001) for v in vals)}
            # Do not include addresses, phone numbers, or other personal/POI detail.
            if name in ('编码','Kind','类型','宽度','铺宽','最大纵坡','通行月份','空间层次','道路功能等级','道路技术等级','单向行驶标志','平均车速','道路的最高限速','始结点号','终结点号','显示等级'):
                stat['top_values']=c.most_common(10)
            row['fields'][str(name)]=stat
        pieces=[]
        for suffix in ('.TAB','.DAT','.MAP','.ID','.IND'):
            p=path.with_suffix(suffix)
            pieces.append((suffix,hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None))
        row['set_sha256']=hashlib.sha256(json.dumps(pieces).encode()).hexdigest()
        dat=path.with_suffix('.DAT')
        if dat.exists():
            h=dat.read_bytes()[:32]
            row['dbf_header_records']=int.from_bytes(h[4:8],'little')
            row['dbf_header_update_date_bytes']=list(h[1:4])
        print(json.dumps({'name':row['path'],'records':row['read_records'],'crs':info['crs'],'bounds':clean(info['total_bounds']),'geometry':row['geometry_types'],'null':row['null_geometry'],'invalid':row['invalid_geometry']},ensure_ascii=False),flush=True)
    except Exception as e:
        row['error']=repr(e)
        print('ERROR',row['path'],repr(e),flush=True)
    rows.append(row)
(BASE/'图层核查.json').write_text(json.dumps(clean(rows),ensure_ascii=False,indent=2),encoding='utf-8')
(BASE/'核查环境.json').write_text(json.dumps({'pyogrio':pyogrio.__version__,'GDAL':pyogrio.__gdal_version_string__,'shapely':shapely.__version__,'numpy':np.__version__},ensure_ascii=False,indent=2))
