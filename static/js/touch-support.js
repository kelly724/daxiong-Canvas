// ── iPad / touch support ──
// Handles: node drag, board pan, node-tap-to-link
(function(){
    var ts = null;       // touch state for drag/pan
    var selNode = null;   // first tapped node (for linking)

    // ── Helper: is this element a port or inside a port? ──
    function isPort(el) {
        return !!(el && el.closest && el.closest('.port'));
    }

    // ── Touch Start ──
    document.addEventListener('touchstart', function(e) {
        if (e.touches.length !== 1) { ts = null; return; }
        var t = e.touches[0];
        var target = e.target;

        // === PORT tap: start link (try both out and in) ===
        if (isPort(target)) {
            e.preventDefault();
            var nodeEl = target.closest('.node');
            if (!nodeEl || !nodeEl.dataset.id) return;
            var nid = nodeEl.dataset.id;

            if (selNode && selNode !== nid) {
                // Second tap: link selNode → nid
                doLink(selNode, nid);
                selNode = null;
                clearNodeHighlights();
            } else {
                // First tap: highlight this node
                selNode = nid;
                highlightNode(nid);
            }
            return;
        }

        // === Node tap (not on port, not on controls) ===
        var nodeEl = target.closest('.node');
        if (nodeEl && nodeEl.dataset.id) {
            if (target.closest('textarea,input,select,button,[contenteditable="true"],.resize-handle')) return;
            e.preventDefault();
            var nid = nodeEl.dataset.id;

            if (selNode && selNode !== nid) {
                doLink(selNode, nid);
                selNode = null;
                clearNodeHighlights();
                return;
            }

            // Start drag
            var node = nodes.find(function(n){ return n.id === nid; });
            if (!node) return;
            selNode = nid;
            highlightNode(nid);
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

    // ── Link two nodes: connect first out → first in ──
    function doLink(fromId, toId) {
        // Find first out port on fromId, first in port on toId
        var fromNode = nodes.find(function(n){ return n.id === fromId; });
        var toNode   = nodes.find(function(n){ return n.id === toId; });
        if (!fromNode || !toNode) return;

        // Check if link already exists
        var exists = links.some(function(lk){
            return (lk.from === fromId && lk.to === toId);
        });
        if (exists) return;

        links.push({ from: fromId, to: toId });
        renderLinks();
        scheduleSave();
    }

    // ── Highlight a node (visual feedback for selection) ──
    function highlightNode(nid) {
        clearNodeHighlights();
        var el = nodesEl.querySelector('.node[data-id="'+nid+'"]');
        if (el) el.style.outline = '3px solid #007AFF';
    }
    function clearNodeHighlights() {
        var els = nodesEl.querySelectorAll('.node');
        for (var i = 0; i < els.length; i++) els[i].style.outline = '';
    }
})();
