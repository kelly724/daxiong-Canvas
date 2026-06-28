// ── iPad / touch support ──
// Correctly hooks into the existing startLink / endLink flow
(function(){
    var ts = null; // { mode:'node'|'board', ... }

    // ── Touch Start ──
    document.addEventListener('touchstart', function(e) {
        if (e.touches.length !== 1) { cancelTouchDrag(); return; }
        var t = e.touches[0];
        var target = e.target;

        // === Port: start link (call original startLink) ===
        var portEl = target.closest('.port');
        if (portEl) {
            e.preventDefault();
            var nodeEl = portEl.closest('.node');
            if (!nodeEl || !nodeEl.dataset.id) return;
            var nodeId = nodeEl.dataset.id;
            var kind   = portEl.classList.contains('out') ? 'out' : 'in';
            // Build a fake mouse event and call startLink directly
            var fe = {
                clientX: t.clientX, clientY: t.clientY,
                stopPropagation: function(){}, preventDefault: function(){},
                button: 0, target: portEl
            };
            if (typeof startLink === 'function') {
                startLink(fe, nodeId, kind);
                setupTouchLinkMove();
            }
            return;
        }

        // === Node drag ===
        var nodeEl2 = target.closest('.node');
        if (nodeEl2 && nodeEl2.dataset.id) {
            if (target.closest('textarea,input,select,button,[contenteditable="true"],.resize-handle')) return;
            e.preventDefault();
            var node = nodes.find(function(n){ return n.id === nodeEl2.dataset.id; });
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

    // ── Touch Move: update tempLink + node/board drag ──
    function setupTouchLinkMove() {
        // Override mousemove to use touch position for tempLink
        var origMouseMove = window.onmousemove;
        window.onmousemove = function(e2) {
            // e2 may be a fake event; tempLink update in startLink uses e2.clientX/Y
            // We let the original handler run, but it expects real mouse events
            // Instead, we update tempLink directly
            if (tempLink) {
                var t = event.touches ? event.touches[0] : (e2 || event);
                // Find current touch
                var touch = null;
                if (event.touches && event.touches.length > 0) touch = event.touches[0];
                else if (event.changedTouches && event.changedTouches.length > 0) touch = event.changedTouches[0];
                if (touch) {
                    var p = screenToWorld(touch.clientX, touch.clientY);
                    tempLink.x2 = p.x;
                    tempLink.y2 = p.y;
                    renderLinks();
                }
            }
            if (origMouseMove) origMouseMove(e2);
        };
    }

    document.addEventListener('touchmove', function(e) {
        if (e.touches.length !== 1) return;
        e.preventDefault();
        var t = e.touches[0];

        // Update tempLink from touch position
        if (tempLink) {
            var p = screenToWorld(t.clientX, t.clientY);
            tempLink.x2 = p.x;
            tempLink.y2 = p.y;
            renderLinks();
        }

        if (!ts) return;
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

    // ── Touch End: complete or cancel link ──
    document.addEventListener('touchend', function(e) {
        // If linking, complete the link via original endLink logic
        if (tempLink) {
            var touch = e.changedTouches[0];
            // Simulate mouseup at touch position to trigger startLink's onmouseup
            var fe = {
                clientX: touch.clientX, clientY: touch.clientY,
                stopPropagation: function(){}, preventDefault: function(){},
                target: document.elementFromPoint(touch.clientX, touch.clientY)
            };
            if (window.onmouseup) window.onmouseup(fe);
            tempLink = null;
            window.onmousemove = null;
            window.onmouseup = null;
            return;
        }

        if (!ts) return;
        if (ts.mode === 'node') scheduleSave();
        if (ts.mode === 'board' && !ts.moved) { selected.clear(); refreshSelectionVisuals(); }
        ts = null;
        document.body.classList.remove('canvas-node-drag', 'canvas-board-pan');
        render();
    }, { passive: false });

    // ── Touch Cancel ──
    document.addEventListener('touchcancel', function() {
        if (tempLink) { tempLink = null; window.onmousemove = null; window.onmouseup = null; renderLinks(); }
        ts = null;
        document.body.classList.remove('canvas-node-drag', 'canvas-board-pan');
        render();
    }, { passive: false });

    function cancelTouchDrag() { ts = null; }
})();
