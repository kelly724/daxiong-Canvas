// ── iPad / touch support ──
// Handles: node drag, board pan, port linking (tap-to-link)
(function(){
    var ts = null;            // touch state for drag/pan
    var linkStart = null;      // { nodeId, portKind } for tap-to-link
    var lastTap = 0;          // for double-tap detection
    var tapTimer = null;       // long-press timer

    // ── Touch Start ──
    document.addEventListener('touchstart', function(e) {
        if (e.touches.length !== 1) { ts = null; linkStart = null; return; }
        var t = e.touches[0];
        var target = e.target;

        // === Port tap-to-link ===
        var portEl = target.closest('.port');
        if (portEl && portEl.dataset.node && portEl.dataset.port) {
            e.preventDefault();
            var now = Date.now();
            var nodeEl = portEl.closest('.node');
            var nodeId = nodeEl ? nodeEl.dataset.id : null;
            var kind = portEl.classList.contains('out') ? 'out' : 'in';

            if (linkStart && linkStart.nodeId !== nodeId) {
                // Second tap: complete the link
                completeLink(linkStart.nodeId, linkStart.portKind, nodeId, kind);
                linkStart = null;
            } else {
                // First tap: select this port as link start
                linkStart = { nodeId: nodeId, portKind: kind };
                // Visual feedback: highlight the port
                portEl.style.outline = '2px solid #007AFF';
                setTimeout(function(){ portEl.style.outline = ''; }, 800);
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
        }
    }, { passive: false });

    // ── Touch End ──
    document.addEventListener('touchend', function() {
        if (!ts) return;
        if (ts.mode === 'node') scheduleSave();
        if (ts.mode === 'board' && !ts.moved) { selected.clear(); refreshSelectionVisuals(); }
        ts = null;
        document.body.classList.remove('canvas-node-drag', 'canvas-board-pan');
        render();
    }, { passive: false });

    // ── Touch Cancel ──
    document.addEventListener('touchcancel', function() {
        if (!ts) return;
        ts = null;
        document.body.classList.remove('canvas-node-drag', 'canvas-board-pan');
        render();
    }, { passive: false });

    // ── Complete link helper ──
    function completeLink(fromNodeId, fromKind, toNodeId, toKind) {
        // Determine correct from/to based on port kinds
        var fromNode = nodes.find(function(n){ return n.id === fromNodeId; });
        var toNode   = nodes.find(function(n){ return n.id === toNodeId; });
        if (!fromNode || !toNode) return;

        // out → in  or  in → out  are valid
        var actualFrom = (fromKind === 'out') ? fromNodeId : toNodeId;
        var actualTo   = (fromKind === 'out') ? toNodeId   : fromNodeId;

        // Check if link already exists
        var exists = links.some(function(lk){
            return (lk.from === actualFrom && lk.to === actualTo) ||
                   (lk.from === actualTo && lk.to === actualFrom);
        });
        if (exists) { linkStart = null; return; }

        var newLink = { from: actualFrom, to: actualTo };
        links.push(newLink);
        renderLinks();
        scheduleSave();
    }
})();
