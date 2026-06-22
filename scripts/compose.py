#!/usr/bin/env python3
"""Team AM poster compositor — HTML rendered headless by Chrome at exact device px.

Device-size aware: pass spec["size"]=[W,H] for the target display type. Layout
(headline size, margins, device width, shadow) scales from the iPhone 6.9" base
(1320x2868) so iPad 13" (2048x2732) renders correctly too. Captions are real
text (never baked by an image model). bg chosen for contrast with the app UI.

Display types:
  APP_IPHONE_67         -> [1320, 2868]
  APP_IPAD_PRO_3GEN_129 -> [2048, 2732]   (Apple wants 2048x2732 for 13")

spec keys: screenshot, out, bg, ink, accent, bezel, headline, size?(=[1320,2868]),
           rot?(=0), dw?(default 0.79*W), badge?
"""
import base64, subprocess, sys, json, os, tempfile
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

TEMPLATE = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
  html,body{{margin:0;padding:0;width:{W}px;height:{H}px;overflow:hidden;}}
  .poster{{width:{W}px;height:{H}px;position:relative;background:{bg};
    font-family:Georgia,'Times New Roman',serif;display:flex;flex-direction:column;align-items:center;}}
  .headline{{margin-top:{mt}px;text-align:center;line-height:1.08;font-weight:700;
    font-size:{fs}px;color:{ink};letter-spacing:-1px;padding:0 {pad}px;}}
  .headline .accent{{color:{accent};}}
  .diamond{{width:{dia}px;height:{dia}px;background:{accent};transform:rotate(45deg);margin-top:{dim}px;border-radius:4px;}}
  .stage{{flex:1;display:flex;align-items:center;justify-content:center;width:100%;margin-top:-{sm}px;}}
  .device{{transform:rotate({rot}deg);
    box-shadow:0 {s1}px {s2}px -{s3}px rgba(20,16,12,.45),0 {s4}px {s5}px -{s6}px rgba(20,16,12,.30);
    border-radius:{br}px;border:{bw}px solid {bezel};background:{bezel};width:{dw}px;}}
  .device img{{display:block;width:100%;border-radius:{ir}px;}}
  .badge{{position:absolute;bottom:{bb}px;left:50%;transform:translateX(-50%);background:rgba(255,255,255,.88);
    border:1px solid rgba(20,16,12,.10);border-radius:999px;padding:{bp1}px {bp2}px;font-size:{bfs}px;color:{ink};
    font-family:-apple-system,system-ui,sans-serif;font-weight:600;box-shadow:0 8px 24px rgba(20,16,12,.12);}}
</style></head><body><div class="poster">
  <div class="headline">{headline}</div><div class="diamond"></div>
  <div class="stage"><div class="device"><img src="data:image/png;base64,{img}"></div></div>
  {badge}
</div></body></html>"""

def render(spec):
    W,H = spec.get('size',[1320,2868]); k = W/1320.0           # scale from iPhone base
    img=base64.b64encode(open(spec['screenshot'],'rb').read()).decode()
    badge = f'<div class="badge">{spec["badge"]}</div>' if spec.get('badge') else ''
    dw = spec.get('dw', round(0.79*W))
    px = lambda v: round(v*k)
    html=TEMPLATE.format(W=W,H=H,bg=spec['bg'],ink=spec['ink'],accent=spec['accent'],bezel=spec['bezel'],
        rot=spec.get('rot',0),dw=dw,headline=spec['headline'],img=img,badge=badge,
        mt=px(170),fs=px(96),pad=px(90),dia=px(26),dim=px(38),sm=px(30),
        s1=px(50),s2=px(90),s3=px(20),s4=px(18),s5=px(36),s6=px(12),
        br=px(74),bw=px(14),ir=px(60),bb=px(120),bp1=px(14),bp2=px(30),bfs=px(34))
    hp=tempfile.NamedTemporaryFile('w',suffix='.html',delete=False); hp.write(html); hp.close()
    subprocess.run([CHROME,'--headless','--disable-gpu','--no-sandbox','--hide-scrollbars',
        f'--window-size={W},{H}','--force-device-scale-factor=1','--screenshot='+spec['out'],'file://'+hp.name],
        capture_output=True, timeout=60)
    os.unlink(hp.name)
    print('rendered', spec['out'], f'{W}x{H}', os.path.exists(spec['out']) and os.path.getsize(spec['out']) or 'FAIL')

if __name__=='__main__':
    render(json.loads(sys.argv[1]))
