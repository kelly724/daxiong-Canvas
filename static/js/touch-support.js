// ── iPad / touch drag support ──
// Handles: node drag, board pan, port linking
(function(){
    var ts = null; // { mode:'node'|'board'|'link', ... }

    // ── Touch Start ──
    document.addEventListener('touchstart', function(e) {
        if (e.touches.length !== 1) { ts = null; return; }
        var t = e.touches[0];
        var target = e.target;

        // === Port linking (touch port to start link) ===
        var portEl = target.closest('.port');
        if (portEl && portEl.dataset.node && portEl.dataset.port) {
            e.preventDefault();
            var nodeEl = portEl.closest('.node');
            var node = nodeEl ? nodes.find(function(n){ return n.id === nodeEl.dataset.id; }) : null;
            if (node) {
                var kind = portEl.classList.contains('out') ? 'out' : 'in';
                // Simulate mousedown on the port to start link
                var fe = { button:0, clientX:t.clientX, clientY:t.clientY, target:portEl,
                    preventDefault:function(){}, stopPropagation:function(){} };
                // Directly call startLink if available, otherwise dispatch mousedown
                if (typeof startLink === 'function') {
                    startLink(fe, node.id, kind);
                }
                ts = { mode:'link' };
                document.body.classList.add('canvas-linking');
            }
            return;
        }

        // === Node drag ===
        var nodeEl = target.closest('.node');
        if (nodeEl && nodeEl.dataset.id) {
            if (target.closest('textarea,input,select,button,[contenteditable="true"],.resize-handle')) return;
            e.preventDefault();
            var node = nodes.find(function(n){ return n.id === nodeEl.dataset.id; });
            if (!node) return;
            ts = { mode:'node', node:node, sx:t.clientX, sy:t.clientY, ox:node.x, oy:node.y };
            document.body.classList.add('canvas-node-drag');
            return;
        }

        // === Board pan ===
        if (target.closest('.board,#board,#world,#nodes,#links')) {
            e.preventDefault();
            ts = { mode:'board', sx:t.clientX, sy:t.clientY, ox:viewport.x, oy:viewport.y, moved:false };
            document.body.classList.add('canvas-board-pan');
        }
    }, { passive: false });

    // ── Touch Move ──
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
        } else if (ts.mode === 'link') {
            // Update temp link position during touch move
            if (typeof tempLink !== 'undefined' && tempLink) {
                // tempLink is updated via renderLinks, we just need to trigger a render
                // The link follows the mouse in desktop; for touch we update via the same mechanism
                if (window.onmousemove) {
                    window.onmousemove({ clientX:t.clientX, clientY:t.clientY,
                        stopPropagation:function(){}, preventDefault:function(){} });
                }
            }
        }
    }, { passive: false });

    // ── Touch End ──
    document.addEventListener('touchend', function(e) {
        if (!ts) return;

        if (ts.mode === 'link') {
            // Check if touch ended on a port (to complete the link)
            var touch = e.changedTouches[0];
            var el = document.elementFromPoint(touch.clientX, touch.clientY);
            if (el) {
                var targetPort = el.closest('.port');
                if (targetPort && typeof endLink === 'function') {
                    var fe = { clientX:touch.clientX, clientY:touch.clientY, target:targetPort,
                        preventDefault:function(){}, stopPropagation:function(){} };
                    endLink(fe);
                } else if (typeof cancelLink === 'function') {
                    cancelLink();
                }
            } else if (typeof cancelLink === 'function') {
                cancelLink();
            }
            document.body.classList.remove('canvas-linking');
            render();
        } else {
            if (ts.mode === 'node') scheduleSave();
            if (ts.mode === 'board' && !ts.moved) { selected.clear(); refreshSelectionVisuals(); }
            render();
        }
        ts = null;
        document.body.classList.remove('canvas-node-drag', 'canvas-board-pan');
    }, { passive: false });

    // ── Touch Cancel ──
    document.addEventListener('touchcancel', function() {
        if (!ts) return;
        if (ts.mode === 'link' && typeof cancelLink === 'function') cancelLink();
        ts = null;
        document.body.classList.remove('canvas-node-drag', 'canvas-board-pan', 'canvas-linking');
        render();
    }, { passive: false });
})();
