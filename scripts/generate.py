from pathlib import Path
import json
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import ezdxf
from matplotlib.path import Path as MplPath
from matplotlib.patches import PathPatch
from shapely.geometry import Point,Polygon,LineString
from shapely.affinity import scale,rotate,translate
from shapely.ops import unary_union,nearest_points
OUT=Path(__file__).resolve().parents[1]; OUT.mkdir(parents=True,exist_ok=True)
def ell(cx,cy,rx,ry): return translate(scale(Point(0,0).buffer(1,resolution=128),rx,ry),cx,cy)
def line(points,w): return LineString(points).buffer(w/2,cap_style=1,join_style=1)
def leaf(cx,cy,rx,ry,a=0): return rotate(ell(cx,cy,rx,ry),a,origin=(cx,cy))
panel=ell(0,0,290,250); ring=panel.difference(panel.buffer(-16))
# Accurate frontal elephant anatomy.
head=ell(0,55,112,142)
left_ear=rotate(ell(-124,54,95,142),-8,origin=(-124,54))
right_ear=rotate(ell(124,54,95,142),8,origin=(124,54))
trunk=line([(0,25),(0,-34),(-7,-94),(4,-150),(26,-194),(54,-204)],48)
trunk=unary_union([trunk,ell(56,-202,27,23)])
tusks=unary_union([
 Polygon([(-66,-25),(-43,-39),(-54,-112),(-31,-78),(-25,-31)]),
 Polygon([(66,-25),(43,-39),(54,-112),(31,-78),(25,-31)])
])
# Lotus crown connects head to upper frame.
lotus=unary_union([
 leaf(0,181,22,56,0),leaf(-38,177,20,50,-32),leaf(38,177,20,50,32),
 leaf(-72,165,17,40,-54),leaf(72,165,17,40,54),line([(-91,154),(0,202),(91,154)],9)
])
# Botanical side scrolls from lower frame.
floral=[]
for s in (-1,1):
 floral += [line([(s*205,-174),(s*221,-125),(s*213,-71),(s*237,-20),(s*248,40),(s*237,98)],12),
            leaf(s*224,-116,17,32,-s*35),leaf(s*244,-59,17,31,s*42),
            leaf(s*246,13,17,32,-s*40),leaf(s*244,82,16,29,s*38)]
material=unary_union([ring,left_ear,right_ear,head,trunk,tusks,lotus,*floral])
# Negative-space anatomy and ornament.
cuts=[]
# Ear interiors, layered but broad.
for s in (-1,1):
 cuts += [rotate(ell(s*137,68,54,95),s*8,origin=(s*137,68)),
          rotate(leaf(s*163,55,14,43,s*12),s*12,origin=(s*163,55)),
          rotate(leaf(s*117,43,12,36,-s*10),-s*10,origin=(s*117,43))]
# Calm almond eyes and brows.
for s in (-1,1):
 eye=ell(s*45,85,25,12)
 cuts += [eye,rotate(ell(s*47,111,31,5),-s*10,origin=(s*47,111)),leaf(s*72,135,10,22,s*35)]
# Forehead jewel and cheek ornament.
cuts += [leaf(0,125,12,25),ell(0,84,8,12)]
for s in (-1,1):
 cuts += [leaf(s*78,45,10,25,s*38),leaf(s*88,10,9,22,s*48)]
# Trunk segmentation and tip nostril.
for y,w in [(-18,25),(-55,23),(-91,21),(-126,18),(-160,14)]: cuts.append(ell(0,y,w,5))
cuts += [rotate(ell(49,-202,10,5),-15,origin=(49,-202))]
# Tusks remain solid metal; cut narrow shadow accents beside them.
for s in (-1,1): cuts.append(rotate(leaf(s*39,-75,7,23,s*16),s*16,origin=(s*39,-75)))
ap=unary_union(cuts).intersection(material.buffer(-5))
# Merge cut profiles separated by less than 4.1 mm using smooth local cut bridges.
ap_parts=list(ap.geoms) if hasattr(ap,'geoms') else [ap]
for _ in range(150):
 best=None
 for i,a in enumerate(ap_parts):
  for j in range(i+1,len(ap_parts)):
   d=a.distance(ap_parts[j])
   if d<4.1 and (best is None or d<best[0]): best=(d,i,j)
 if best is None: break
 _,i,j=best; a,b=ap_parts[i],ap_parts[j]; pa,pb=nearest_points(a,b)
 bridge=LineString([(pa.x,pa.y),(pb.x,pb.y)]).buffer(2.05,cap_style=1)
 merged=unary_union([a,b,bridge]).buffer(0)
 ap_parts=[g for k,g in enumerate(ap_parts) if k not in (i,j)]+[merged]
ap=unary_union(ap_parts)
mounts=unary_union([Point(-150,211).buffer(4,resolution=48),Point(150,211).buffer(4,resolution=48)])
material=material.difference(unary_union([ap,mounts]))
parts=list(material.geoms) if hasattr(material,'geoms') else [material]
if len(parts)!=1:
 raise RuntimeError(f'Concept has {len(parts)} disconnected metal components after removing the base line')
material=parts[0]
# Production DXF and SVG.
doc=ezdxf.new('R2010'); doc.units=ezdxf.units.MM; doc.layers.add('CUT',color=7); msp=doc.modelspace()
def coords(poly): return [(round(x,4),round(y,4)) for x,y in list(poly.exterior.coords)[:-1]]
msp.add_lwpolyline(coords(material),close=True,dxfattribs={'layer':'CUT'})
for r in material.interiors:
 msp.add_lwpolyline(coords(Polygon(r)),close=True,dxfattribs={'layer':'CUT'})
doc.saveas(OUT/'original-lotus-elephant-panel.dxf')
def pd(r):
 pts=[(x+300,270-y) for x,y in list(r.coords)[:-1]]
 return 'M '+' L '.join(f'{x:.3f},{y:.3f}' for x,y in pts)+' Z'
d=' '.join([pd(material.exterior)]+[pd(r) for r in material.interiors])
(OUT/'original-lotus-elephant-panel.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="600mm" height="540mm" viewBox="0 0 600 540"><path d="{d}" fill="#111" fill-rule="evenodd"/></svg>\n')
def mp(poly):
 v=[]; c=[]
 for r in [poly.exterior,*poly.interiors]:
  pts=list(r.coords); v.extend(pts); c.extend([MplPath.MOVETO]+[MplPath.LINETO]*(len(pts)-2)+[MplPath.CLOSEPOLY])
 return MplPath(v,c)
fig,ax=plt.subplots(figsize=(8,8.7),dpi=190); fig.patch.set_facecolor('#eee8df'); ax.set_facecolor('#eee8df')
ax.add_patch(PathPatch(mp(material),facecolor='#171819',edgecolor='#090909',lw=.55))
ax.set_xlim(-305,305); ax.set_ylim(-285,275); ax.set_aspect('equal'); ax.axis('off')
ax.text(0,-276,'ORIGINAL LOTUS ELEPHANT  •  580 × 500 mm  •  2 mm STEEL',ha='center',va='bottom',fontsize=8,color='#4e4a45',weight='bold')
fig.savefig(OUT/'original-lotus-elephant-preview.jpg',bbox_inches='tight',facecolor=fig.get_facecolor()); plt.close(fig)
holes=[Polygon(r) for r in material.interiors]; mg=999.0; pair=None
for i,a in enumerate(holes):
 for j in range(i+1,len(holes)):
  dd=a.distance(holes[j])
  if dd<mg: mg=dd; pair=[i,j]
mass=material.area*2*7.85e-6
metrics={'width_mm':580.0,'height_mm':500.0,'thickness_mm':2.0,'material':'mild steel','connected_components':1,'geometry_valid':material.is_valid,'closed_profiles':1+len(material.interiors),'decorative_apertures':len(material.interiors)-2,'mounting_holes':2,'mounting_hole_diameter_mm':8.0,'minimum_profile_separation_mm':round(mg,3),'minimum_gap_pair':pair,'area_mm2':round(material.area,2),'cut_length_mm':round(material.length,2),'mass_kg':round(mass,4),'cut_price_at_2_usd_per_kg':round(mass*2,2)}
(OUT/'geometry-metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
print(json.dumps(metrics))
