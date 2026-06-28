// ── iPad / touch support ──
// Handles: node drag, board pan, port tap-to-link
(function(){
    var ts = null;       // touch state for drag/pan
    var linkStart = null; // { nodeId, portEl } for tap-to-link
    var firstNodeId = null;// node id when touch started on a port

    // ── Touch Start ──
    document.addEventListener('touchstart', function(e) {
        if (e.touches.length !== 1) { ts = null; return; }
        var t = e.touches[0];
        var target = e.target;

        // === Port tap detection (before node drag!) ===
        var portEl = target.closest('.port');
        if (portEl) {
            e.preventDefault();
            var nodeEl = portEl.closest('.node');
            if (!nodeEl || !nodeEl.dataset.id) return;
            var nodeId = nodeEl.dataset.id;
            var kind   = portEl.classList.contains('out') ? 'out' : 'in';

            if (linkStart && linkStart.nodeId !== nodeId) {
                // Second tap: complete link
                completeLink(linkStart.nodeId, linkStart.portKind, nodeId, kind);
                linkStart = null;
            } else {
                // First tap: store as link start
                linkStart = { nodeId: nodeId, portKind: kind };
                // Visual feedback
                portEl.style.boxShadow = '0 0 0 3px #007AFF80';
                setTimeout(function(){ portEl.style.boxShadow = ''; }, 600);
            }
            return; // <-- IMPORTANT: stop here, don't start node drag
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
    function completeLink(fromId, fromKind, toId, toKind) {
        var fromNode = nodes.find(function(n){ return n.id === fromId; });
        var toNode   = nodes.find(function(n){ return n.id === toId; });
        if (!fromNode || !toNode) return;

        // out → in is valid; same-kind links are invalid
        if (fromKind === toKind) return;

        var actualFrom = (fromKind === 'out') ? fromId : toId;
        var actualTo   = (fromKind === 'out') ? toId   : fromId;

        // Check duplicate
        var exists = links.some(function(lk){
            return (lk.from === actualFrom && lk.to === actualTo);
        });
        if (exists) return;

        links.push({ from: actualFrom, to: actualTo });
        renderLinks();
        scheduleSave();
    }
})();
