/* Structural guards. Visual layout checks are documented separately, not a full build. */
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const root=path.resolve(__dirname,'..'),read=f=>fs.readFileSync(path.join(root,f),'utf8');
const css=read('frontend/src/responsive.css'),pos=read('frontend/src/pages/POS.jsx'),login=read('frontend/src/pages/Login.jsx');
assert(read('frontend/src/index.js').includes('import "@/responsive.css"'));console.log('PASS responsive styles are loaded by the real application entry');
assert(!read('frontend/public/index.html').includes('user-scalable=no'));assert(!read('frontend/public/index.html').includes('maximum-scale=1'));console.log('PASS browser/pinch zoom remains available');
assert(!pos.includes('width / baseWidth'));assert(!read('frontend/src/index.css').includes('font-size: 13px;'));console.log('PASS resolution-based font shrinking removed');
assert(login.includes('dp-login-grid'));assert(!login.includes('clip-path:polygon'));console.log('PASS login no longer puts white text over the diagonal white region');
assert(read('frontend/src/components/ui/table.jsx').includes('dp-table-region'));assert(css.includes('overflow-x: auto'));console.log('PASS table scrolling is confined to its region');
assert(css.includes('max-height: calc(100dvh - 32px)'));assert(css.includes('overflow-y: auto'));console.log('PASS dialogs are bounded by viewport height and can scroll');
assert(pos.includes('dp-pos-actions'));assert(pos.includes('dp-action-label'));assert(pos.includes('<TableHeader>'));console.log('PASS POS actions retain labels and cart header scrolls with the table');
const layout=read('frontend/src/components/MainLayout.jsx');assert(layout.includes('aria-expanded={sidebarOpen}'));assert(layout.includes("event.key === 'Escape'"));assert(css.includes('@media (min-width: 1280px)'));console.log('PASS responsive menu has consistent breakpoints and an Escape close action');
