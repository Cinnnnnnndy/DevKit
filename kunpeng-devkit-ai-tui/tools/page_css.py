"""设计系统页面外壳 —— screens.html / design-input.html 共用。

色值与间距全部照抄 web/index.html 的 token 定义（唯一真值仍是 docs/VISUAL.md），
两份生成页因此不会各自漂移出一套配色。
"""

CSS = """
:root{
  --ark-blue-500:#0077ff; --ark-blue-600:#3d98ff; --ark-domain-aux:#7c8db8;
  --ark-green-500:#04d793; --ark-orange-500:#ffaa3b; --ark-red-500:#ff4b7b;
  --ark-neutral-0:#0b0b0b; --ark-neutral-1:#101010; --ark-neutral-2:#141414;
  --kunpeng:#ed1c24;
  --space-1:4px; --space-2:8px; --space-3:12px; --space-4:16px; --space-5:20px; --space-6:24px;
  --radius-sm:6px; --radius-md:8px; --radius-lg:12px; --radius-pill:999px;
  --duration-fast:100ms; --easing-default:cubic-bezier(.4,0,.2,1);
  --font-sans:'Inter','Source Han Sans SC','PingFang SC','Noto Sans SC',-apple-system,sans-serif;
  --font-mono:'JetBrains Mono','Fira Code','SFMono-Regular',Consolas,monospace;
  --fs-display:28px; --fs-title-md:20px; --fs-title-sm:16px; --fs-body:14px; --fs-body-sm:12px; --fs-label:11px;
  --grid-unit:4px; --chart-trim:calc(var(--grid-unit) * 3);
}
:root[data-theme="dark"],:root{
  --background:var(--ark-neutral-1); --background-elevated:var(--ark-neutral-2);
  --surface-1:#161616; --surface-2:#1c1c1c; --surface-3:#262626;
  --foreground:rgba(255,255,255,.90); --foreground-secondary:rgba(255,255,255,.60);
  --foreground-muted:rgba(255,255,255,.40); --foreground-disabled:rgba(255,255,255,.25);
  --border-subtle:rgba(255,255,255,.06); --border-default:rgba(255,255,255,.10); --border-strong:rgba(255,255,255,.16);
  --primary:var(--ark-blue-500); --primary-hover:var(--ark-blue-600); --accent:var(--ark-domain-aux);
  --success:var(--ark-green-500); --warning:var(--ark-orange-500); --danger:var(--ark-red-500);
  --state-hover:rgba(255,255,255,.06); --state-selected:rgba(0,119,255,.14);
  --tone-info-bg:rgba(0,119,255,.16); --tone-warning-bg:rgba(255,170,59,.16);
}
:root[data-theme="light"]{
  --background:#f5f5f5; --background-elevated:#ffffff;
  --surface-1:#ffffff; --surface-2:#f2f2f2; --surface-3:#e6e6e6;
  --foreground:rgba(0,0,0,.88); --foreground-secondary:rgba(0,0,0,.58);
  --foreground-muted:rgba(0,0,0,.42); --foreground-disabled:rgba(0,0,0,.26);
  --border-subtle:rgba(0,0,0,.07); --border-default:rgba(0,0,0,.12); --border-strong:rgba(0,0,0,.20);
  --state-hover:rgba(0,0,0,.04); --state-selected:rgba(0,119,255,.10);
}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth;scroll-padding-top:72px}
body{background:var(--background);color:var(--foreground);font-family:var(--font-sans);
  font-size:var(--fs-body);line-height:1.65;-webkit-font-smoothing:antialiased}
a{color:var(--primary-hover);text-decoration:none}
a:hover{color:var(--primary)}
.topbar{position:fixed;top:0;left:0;right:0;height:56px;background:var(--background-elevated);
  border-bottom:1px solid var(--border-subtle);display:flex;align-items:center;gap:var(--space-3);
  padding:0 var(--space-5);z-index:60}
.kpmark{color:var(--kunpeng);font-size:15px}
.brand{font-weight:700;font-size:15px;letter-spacing:-.01em}
.vchip{font-family:var(--font-mono);font-size:var(--fs-label);color:var(--foreground-muted);
  background:var(--surface-2);border:1px solid var(--border-subtle);border-radius:var(--radius-sm);padding:2px 7px}
.tagline{font-size:var(--fs-body-sm);color:var(--foreground-muted)}
.tb-right{margin-left:auto;display:flex;align-items:center;gap:var(--space-3)}
.tb-right a{font-size:var(--fs-body-sm);color:var(--foreground-muted)}
.tbtn{font:500 12px/1 var(--font-sans);color:var(--foreground);background:var(--surface-2);
  border:1px solid var(--border-subtle);border-radius:var(--radius-lg);padding:7px 13px;cursor:pointer}
.tbtn:hover{background:var(--surface-3)}
.wrap{display:flex;max-width:1720px;margin:0 auto;padding-top:56px}
nav{width:228px;flex-shrink:0;position:sticky;top:56px;height:calc(100vh - 56px);overflow-y:auto;
  padding:var(--space-6) var(--space-3) 60px var(--space-5);border-right:1px solid var(--border-subtle)}
.ngrp{font-size:var(--fs-label);font-weight:500;letter-spacing:.09em;text-transform:uppercase;
  color:var(--foreground-disabled);margin:var(--space-5) 0 var(--space-2) var(--space-2)}
.ngrp:first-child{margin-top:0}
nav a{display:flex;align-items:center;gap:9px;color:var(--foreground-secondary);padding:5px var(--space-2);
  border-radius:var(--radius-sm);font-size:13px}
nav a::before{content:'';width:4px;height:4px;border-radius:50%;background:var(--foreground-disabled);flex-shrink:0}
nav a:hover{color:var(--foreground);background:var(--state-hover)}
nav a.on{color:var(--primary-hover);background:var(--state-selected)}
nav a.on::before{background:var(--primary-hover)}
.nfoot{margin-top:var(--space-6);padding:var(--space-4) var(--space-2) 0;border-top:1px solid var(--border-subtle);
  font-family:var(--font-mono);font-size:var(--fs-label);color:var(--foreground-disabled);line-height:1.9}
main{flex:1;min-width:0;padding:var(--space-6) 32px 140px}
.eyebrow{font-size:var(--fs-label);font-weight:500;letter-spacing:.09em;text-transform:uppercase;
  color:var(--primary-hover);margin-bottom:var(--space-2)}
h1{font-size:var(--fs-display);font-weight:700;letter-spacing:-.02em;margin-bottom:var(--space-3)}
h2{font-size:var(--fs-title-md);font-weight:600;letter-spacing:-.01em;margin-bottom:var(--space-3)}
h3{font-size:var(--fs-title-sm);font-weight:600;margin:var(--space-6) 0 var(--space-3)}
section{padding-top:var(--space-6);margin-bottom:52px}
.desc{color:var(--foreground-secondary);font-size:var(--fs-body);margin-bottom:var(--space-4);max-width:82ch}
.sublabel{font-size:var(--fs-label);font-weight:500;letter-spacing:.09em;text-transform:uppercase;
  color:var(--foreground-muted);margin:var(--space-6) 0 var(--space-3);display:flex;align-items:center;gap:var(--space-3)}
.sublabel::after{content:'';flex:1;height:1px;background:var(--border-subtle)}
p{margin:var(--space-3) 0;color:var(--foreground-secondary)}
strong,b{color:var(--foreground);font-weight:600}
code{font-family:var(--font-mono);font-size:12px;background:var(--surface-2);white-space:nowrap;
  border:1px solid var(--border-subtle);padding:1px 6px;border-radius:var(--radius-sm);color:var(--foreground)}
kbd{font-family:var(--font-mono);font-size:var(--fs-label);background:var(--surface-3);
  border:1px solid var(--border-default);border-bottom-width:2px;padding:2px 6px;
  border-radius:var(--radius-sm);color:var(--foreground)}
pre{font-family:var(--font-mono);background:var(--ark-neutral-0);border:1px solid var(--border-subtle);
  border-radius:var(--radius-lg);padding:var(--space-4) var(--space-5);overflow-x:auto;
  font-size:12px;line-height:1.5;margin:var(--space-3) 0;color:#E8E8E8}
pre.dense{--row:calc(var(--grid-unit) * 5);font-size:11px;line-height:var(--row);
  padding:var(--chart-trim);margin:var(--space-3) 0;border:1px solid var(--border-default);
  border-radius:var(--radius-lg);background:var(--surface-1);overflow-x:auto}
/* 整屏帧：字号抬到 12.5px，160 列约 1200px，正好落在放宽后的正文宽里 */
pre.screen{--row:16px;font-size:12.5px;line-height:var(--row);background:#0B0B0B;
  border:0;border-radius:0;padding:14px 16px;margin:0;background-image:none}

/* ── 应用窗口外壳：让整屏帧看起来像一个跑起来的应用，而不是一段代码 ── */
.win{border:1px solid var(--border-default);border-radius:var(--radius-lg);overflow:hidden;
  background:#0B0B0B;box-shadow:0 1px 3px rgba(0,0,0,.4),0 18px 44px rgba(0,0,0,.5);
  margin:var(--space-4) 0 var(--space-5)}
.win-bar{display:flex;align-items:center;gap:10px;height:34px;padding:0 12px;
  background:linear-gradient(180deg,#1a1a1a,#141414);border-bottom:1px solid var(--border-subtle)}
.win-bar .kp{color:var(--kunpeng);font-size:13px;line-height:1}
.win-bar .nm{font-size:12px;font-weight:600;color:var(--foreground);letter-spacing:-.01em}
.win-bar .sub{font-family:var(--font-mono);font-size:10.5px;color:var(--foreground-disabled)}
.win-bar .meta{margin-left:auto;display:flex;gap:8px;align-items:center}
.win-bar .tag{font-family:var(--font-mono);font-size:10px;padding:2px 7px;border-radius:var(--radius-sm);
  background:var(--surface-2);border:1px solid var(--border-subtle);color:var(--foreground-muted)}
.win-bar .tag.on{color:var(--primary-hover);border-color:rgba(0,119,255,.34);background:rgba(0,119,255,.12)}
.win-scroll{overflow-x:auto}
.win-foot{display:flex;gap:14px;flex-wrap:wrap;padding:9px 14px;border-top:1px solid var(--border-subtle);
  background:var(--surface-1);font-size:11.5px;color:var(--foreground-muted)}
.win-foot b{color:var(--foreground-secondary);font-weight:600}
.win-foot code{font-size:11px;background:var(--surface-2)}
pre .cm{color:#707070} pre .pr{color:#3d98ff} pre .ac{color:#7c8db8}
pre .ok{color:#04d793} pre .wn{color:#ffaa3b} pre .er{color:#ff4b7b}
pre .o8{color:#773303} pre .o6{color:#D15905} pre .o4{color:#FA8838} pre .o3{color:#FBAB74}
pre .g8{color:#4D7209} pre .g6{color:#86C70F} pre .g4{color:#B3F141} pre .g3{color:#CAF57A}
pre .a4{color:#F4CB22} pre .a6{color:#CA8A04}
pre .v4{color:#9B3CF6} pre .v6{color:#6E0ACD}
pre .br{color:#0077FF} pre .t{color:#E8E8E8;font-weight:600} pre .sel{background:#18293C}
/* ── 背景色带：色值直接取自实现的 theme/tokens.ts，不另调 ──
 * selected #18293C · focus #162E49 · surface2/3/4 · dangerBackground #351B24
 * successBackground 是 tokens.ts 尚缺的一档，按同族推导（base #101010 + 15.5% 色）
 * 得 #0E2F24，已列入待补 token。 */
pre .bsel{background:#18293C} pre .bfoc{background:#162E49}
pre .bs2{background:#1C1C1C} pre .bs3{background:#262626} pre .bs4{background:#313131}
pre .bdel{background:#351B24} pre .badd{background:#0E2F24}
pre .bwarn{background:#382A18} pre .binfo{background:#142538}
pre .bpri{background:#0077FF;color:#fff;font-weight:600}
pre .bkp{background:#ED1C24;color:#fff;font-weight:600}
pre .fw{font-size:2ch}
/* 回退字体给 Braille / ⏸ 的步进因字体而异（实测 1.217 / 0.830 格），调字号治不了。
   钉成 width:1ch 的行内块：无论用哪个回退字体，它都只占一格，整行不会被推歪。 */
pre .hw{display:inline-block;width:1ch;overflow:hidden;vertical-align:bottom;line-height:inherit}
:root[data-theme="light"] pre.dense,:root[data-theme="light"] pre.screen{background:#0b0b0b;color:#E8E8E8}
.fig{position:relative;margin:var(--space-4) 0}
.fig-t{position:absolute;top:-0.6em;left:var(--space-4);padding:0 var(--space-2);
  background:var(--background);font-size:11px;color:var(--foreground-secondary);line-height:1;z-index:1;white-space:nowrap}
.fig pre.dense{margin:0}
table{width:100%;border-collapse:collapse;margin:var(--space-3) 0;font-size:var(--fs-body-sm)}
th{text-align:left;font-size:var(--fs-label);font-weight:500;letter-spacing:.06em;text-transform:uppercase;
  color:var(--foreground-muted);padding:var(--space-2) var(--space-3);border-bottom:1px solid var(--border-default)}
td{padding:var(--space-2) var(--space-3);border-bottom:1px solid var(--border-subtle);
  vertical-align:top;color:var(--foreground-secondary)}
tr:hover td{background:var(--state-hover)}
td:first-child{color:var(--foreground);font-weight:500;white-space:nowrap}
td.mono,th.mono{font-family:var(--font-mono)}
.grid{display:grid;gap:var(--space-3);margin:var(--space-4) 0}
.g2{grid-template-columns:repeat(auto-fit,minmax(320px,1fr))}
.g3{grid-template-columns:repeat(auto-fit,minmax(240px,1fr))}
.g4{grid-template-columns:repeat(auto-fit,minmax(168px,1fr))}
.card{background:var(--surface-1);border:1px solid var(--border-default);border-radius:var(--radius-lg);padding:var(--space-4)}
.card h4{font-size:13px;font-weight:600;color:var(--foreground);margin-bottom:var(--space-2)}
.card p{font-size:var(--fs-body-sm);color:var(--foreground-secondary);margin:var(--space-2) 0}
.stat{background:var(--surface-1);border:1px solid var(--border-default);border-radius:var(--radius-lg);padding:var(--space-4)}
.stat b{display:block;font-size:26px;font-weight:700;letter-spacing:-.02em;line-height:1.2}
.stat span{font-size:var(--fs-body-sm);color:var(--foreground-muted)}
.badge{display:inline-block;font-size:var(--fs-label);font-weight:500;padding:2px 9px;
  border-radius:var(--radius-pill);background:var(--surface-2);border:1px solid var(--border-default);
  color:var(--foreground-secondary);margin:2px 4px 2px 0}
.badge.p{color:var(--primary-hover)} .badge.s{color:var(--success)}
.badge.w{color:var(--warning)} .badge.d{color:var(--danger)}
.chipm{display:inline-block;font-family:var(--font-mono);font-size:var(--fs-label);padding:2px 9px;
  border-radius:var(--radius-pill);background:var(--surface-2);border:1px solid var(--border-subtle);
  color:var(--foreground-secondary);margin:2px 4px 2px 0}
.rule{font-size:var(--fs-body-sm);color:var(--foreground-secondary);
  border-left:2px solid var(--border-strong);padding-left:var(--space-3);margin:var(--space-3) 0}
.note{background:var(--tone-info-bg);border:1px solid rgba(0,119,255,.28);border-radius:var(--radius-lg);
  padding:var(--space-3) var(--space-4);margin:var(--space-4) 0;font-size:13px;color:var(--foreground-secondary)}
.note b{color:var(--primary-hover)}
.warn{background:var(--tone-warning-bg);border-color:rgba(255,170,59,.28)}
.warn b{color:var(--warning)}
footer{margin-top:72px;padding-top:var(--space-5);border-top:1px solid var(--border-subtle);
  font-size:var(--fs-label);color:var(--foreground-disabled);font-family:var(--font-mono);line-height:2}
@media(max-width:980px){nav{display:none}main{padding:var(--space-5) var(--space-5) 80px}}
"""

JS = """
const secs=[...document.querySelectorAll('section[id]')],links=[...document.querySelectorAll('nav a[href^="#"]')];
const io=new IntersectionObserver(es=>{es.forEach(e=>{if(e.isIntersecting){
  links.forEach(a=>a.classList.toggle('on',a.getAttribute('href')==='#'+e.target.id));}})},
  {rootMargin:'-64px 0px -70% 0px'});
secs.forEach(s=>io.observe(s));
function tt(){const r=document.documentElement,d=r.getAttribute('data-theme')==='dark';
  r.setAttribute('data-theme',d?'light':'dark');document.getElementById('tl').textContent=d?'Dark':'Light';}
"""
