// Apply the saved preference before the stylesheet paints the page.
(() => {
 let theme;
 try { theme = localStorage.getItem('matrix-graph-theme'); } catch {}
 if (!['light', 'dark'].includes(theme)) {
  theme = window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
 }
 document.documentElement.dataset.theme = theme;
 try {const w=Number(localStorage.getItem('matrix-graph-pane-width'));if(w>=280&&w<=900)document.documentElement.style.setProperty('--equation-pane-width',Math.max(280,Math.min(w,window.innerWidth-328))+'px');} catch {}
})();
