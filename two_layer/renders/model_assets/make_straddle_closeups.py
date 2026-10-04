from PIL import Image, ImageDraw
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, matplotlib.patches as pa
for b in ['DC1a','DC1c']:
  ims=[]
  for s in ['top','bottom']:
    im=Image.open(f'routed_grayscale_{b}_{s}_straddle_corrected.png').convert('RGB'); w,h=im.size
    st=im.crop((0,int(h*0.92),w,h)); ims.append(st.resize((st.width*2,st.height*2)))
  W=Image.new('RGB',(ims[0].width,sum(i.height for i in ims)+60),'white'); d=ImageDraw.Draw(W); y=0
  for lab,i in zip(['TOP (F.Cu) edge strip, 2x crop','BOTTOM (B.Cu) edge strip, 2x crop (view mirrored)'],ims):
    d.text((8,y+8),lab,fill='black'); y+=30; W.paste(i,(0,y)); y+=i.height
  W.save(f'routed_grayscale_{b}_straddle_edge_closeup.png')
f,ax=plt.subplots(figsize=(8,5),dpi=200); T=1.6;mid=-0.8;pw=0.635
ax.add_patch(pa.Rectangle((0,-T),8,T,fc='#2a5a3a'))
for z in (0,-T-0.035): ax.add_patch(pa.Rectangle((0.4,z),4.1,0.035,fc='#c8a040'))
for zc in (mid+1.27,mid-1.27): ax.add_patch(pa.Rectangle((-8.64,zc-pw/2),11.64,pw,fc='#d9ae40',ec='k',lw=.3))
ax.add_patch(pa.Rectangle((-2.64,mid-2.54),2.54,5.08,fc='#111'))
ax.annotate('',(1.8,0.035),(1.8,0.1525),arrowprops=dict(arrowstyle='<->'));ax.text(1.9,0.25,'~0.12 mm air gap (pin to 35um pad)',fontsize=7)
ax.annotate('',(1.8,-T-0.035),(1.8,-1.7525),arrowprops=dict(arrowstyle='<->'));ax.text(1.9,-2.2,'~0.12 mm air gap',fontsize=7)
ax.text(5,-0.9,'PCB 1.6 mm',color='w',fontsize=8);ax.text(-2.6,1.9,'black bar (outboard)',fontsize=7)
ax.set_title('Nominal 2x38 header (2.54 mm row, 0.64 mm sq pin) centred on 1.6 mm board\ninner pin gap 1.905 mm vs 1.67 mm board+Cu: pins do NOT touch pads unless bent/clamped or solder-filled',fontsize=8)
ax.set_xlim(-9,8);ax.set_ylim(-3.6,2.3);ax.set_aspect('equal');ax.set_xlabel('mm (0 = board edge, + inward)');ax.set_ylabel('z mm')
plt.tight_layout();plt.savefig('straddle_fit_cross_section.png')
