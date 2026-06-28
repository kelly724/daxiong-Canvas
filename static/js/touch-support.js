// ── iPad / touch drag support ──
// Single touchstart handler: node drag + board pan. No event forwarding.
(function(){
    var ts = null;

    document.addEventListener('touchstart', function(e) {
        if (e.touches.length !== 1) { ts = null; return; }
        var t = e.touches[0];
        var target = e.target;

        // Node drag
        var nodeEl = target.closest('.node');
        if (nodeEl && nodeEl.dataset.id) {
            if (target.closest('textarea,input,select,button,[contenteditable="true"],.port,.resize-handle')) return;
            e.preventDefault();
            var node = nodes.find(function(n){ return n.id === nodeEl.dataset.id; });
            if (!node) return;
            ts = { mode:'node', node:node, sx:t.clientX, sy:t.clientY, ox:node.x, oy:node.y };
            document.body.classList.add('canvas-node-drag');
            return;
        }

        // Board pan
        if (target.closest('.board,#board,#world,#nodes,#links')) {
            e.preventDefault();
            ts = { mode:'board', sx:t.clientX, sy:t.clientY, ox:viewport.x, oy:viewport.y, moved:false };
            document.body.classList.add('canvas-board-pan');
        }
    }, { passive: false });

    document.addEventListener('touchmove', function(e) {
        if (!ts || e.touches.length !== 1) return;
        e.preventDefault();
        var t = e.touches[0];
        if (ts.mode === 'node') {
            var dx = (t.clientX - ts.sx) / viewport.scale;
            var dy = (t.clientY - ts.sy) / viewport.scale;
            ts.node.x = Math.round(ts.ox + dx);
            ts.node.y = Math.round(ts.oy + dy);
            var el = nodesEl.querySelector('.node[data-id="'+ts.node.id+'"]');
            if (el) { el.style.left = ts.node.x+'px'; el.style.top = ts.node.y+'px'; }
            renderLinks();
        } else if (ts.mode === 'board') {
            if (Math.hypot(t.clientX-ts.sx, t.clientY-ts.sy) > 4) ts.moved = true;
            viewport.x = ts.ox + (t.clientX - ts.sx);
            viewport.y = ts.oy + (t.clientY - ts.sy);
            applyViewport();
        }
    }, { passive: false });

    document.addEventListener('touchend', function() {
        if (!ts) return;
        if (ts.mode === 'node') scheduleSave();
        if (ts.mode === 'board' && !ts.moved) { selected.clear(); refreshSelectionVisuals(); }
        ts = null;
        document.body.classList.remove('canvas-node-drag', 'canvas-board-pan');
        render();
    }, { passive: false });

    document.addEventListener('touchcancel', function() {
        if (!ts) return;
        ts = null;
        document.body.classList.remove('canvas-node-drag', 'canvas-board-pan');
        render();
    }, { passive: false });
})();
