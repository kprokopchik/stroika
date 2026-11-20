/* Стройка: меню и просмотр планов с зумом (щипок, перетаскивание, колесо, двойной тап, кнопки, полный экран). */
(function () {
  'use strict';

  // ---------- меню
  var btn = document.querySelector('.menu-btn');
  function setNav(open) {
    document.body.classList.toggle('nav-open', open);
    if (btn) btn.setAttribute('aria-expanded', open ? 'true' : 'false');
  }
  if (btn) btn.addEventListener('click', function () { setNav(!document.body.classList.contains('nav-open')); });
  document.querySelectorAll('[data-close-nav]').forEach(function (el) { el.addEventListener('click', function () { setNav(false); }); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') setNav(false); });
  // текущий пункт меню — в зону видимости
  var cur = document.querySelector('.sidenav a.cur');
  if (cur && cur.scrollIntoView) cur.scrollIntoView({ block: 'center' });

  // ---------- зум планов
  var MAX = 14;

  function PanZoom(root) {
    var stage = root.querySelector('.pz-stage');
    var s = 1, tx = 0, ty = 0;
    var pts = new Map();
    var gesture = null;    // {d, mx, my} для щипка или {x, y} для сдвига
    var lastTap = 0, moved = false, settle = null;

    function size() { return root.getBoundingClientRect(); }
    function clamp() {
      var r = size(), w = r.width, h = r.height;
      if (s <= 1) { s = 1; tx = 0; ty = 0; return; }
      var minX = w - w * s, minY = h - h * s;
      tx = Math.min(0, Math.max(minX, tx));
      ty = Math.min(0, Math.max(minY, ty));
    }
    function apply(live) {
      clamp();
      stage.style.transform = 'translate(' + tx + 'px,' + ty + 'px) scale(' + s + ')';
      // во время жеста — растровое ускорение, после — перерисовка в векторе для чёткости
      stage.style.willChange = live ? 'transform' : 'auto';
      if (!live) { clearTimeout(settle); }
    }
    function zoomAt(k, px, py, live) {
      var ns = Math.min(MAX, Math.max(1, s * k));
      k = ns / s;
      tx = px - (px - tx) * k;
      ty = py - (py - ty) * k;
      s = ns;
      apply(live);
    }
    function local(e) { var r = size(); return { x: e.clientX - r.left, y: e.clientY - r.top }; }
    function center() { var r = size(); return { x: r.width / 2, y: r.height / 2 }; }

    root.addEventListener('pointerdown', function (e) {
      if (e.target.closest('.pz-bar, .pz-layers')) return;
      root.setPointerCapture(e.pointerId);
      pts.set(e.pointerId, local(e));
      moved = false;
      if (pts.size === 1) { var p = pts.get(e.pointerId); gesture = { x: p.x, y: p.y }; root.classList.add('dragging'); }
      if (pts.size === 2) {
        var a = Array.from(pts.values());
        gesture = { d: Math.hypot(a[0].x - a[1].x, a[0].y - a[1].y), mx: (a[0].x + a[1].x) / 2, my: (a[0].y + a[1].y) / 2 };
      }
    });
    root.addEventListener('pointermove', function (e) {
      if (!pts.has(e.pointerId)) return;
      pts.set(e.pointerId, local(e));
      if (pts.size === 2 && gesture && gesture.d) {
        var a = Array.from(pts.values());
        var d = Math.hypot(a[0].x - a[1].x, a[0].y - a[1].y);
        var mx = (a[0].x + a[1].x) / 2, my = (a[0].y + a[1].y) / 2;
        tx += mx - gesture.mx; ty += my - gesture.my;
        zoomAt(d / gesture.d, mx, my, true);
        gesture = { d: d, mx: mx, my: my };
        moved = true;
      } else if (pts.size === 1 && gesture && gesture.x !== undefined) {
        var p = pts.get(e.pointerId);
        var dx = p.x - gesture.x, dy = p.y - gesture.y;
        if (Math.abs(dx) + Math.abs(dy) > 3) moved = true;
        tx += dx; ty += dy;
        gesture = { x: p.x, y: p.y };
        apply(true);
      }
    });
    function end(e) {
      if (!pts.has(e.pointerId)) return;
      var p = pts.get(e.pointerId);
      pts.delete(e.pointerId);
      if (pts.size === 1) { var q = Array.from(pts.values())[0]; gesture = { x: q.x, y: q.y }; return; }
      if (pts.size === 0) {
        root.classList.remove('dragging');
        gesture = null;
        // двойной тап / двойной клик: приблизить или вернуть
        var now = Date.now();
        if (!moved && e.type === 'pointerup') {
          if (now - lastTap < 320) {
            if (s > 1.5) { s = 1; tx = 0; ty = 0; apply(false); } else { zoomAt(2.6, p.x, p.y, false); }
            lastTap = 0;
          } else { lastTap = now; }
        }
        apply(false);
      }
    }
    root.addEventListener('pointerup', end);
    root.addEventListener('pointercancel', end);
    root.addEventListener('wheel', function (e) {
      e.preventDefault();
      var p = local(e);
      var dy = e.deltaMode === 1 ? e.deltaY * 16 : e.deltaY;
      zoomAt(Math.exp(-dy * 0.0016), p.x, p.y, true);
      clearTimeout(settle);
      settle = setTimeout(function () { apply(false); }, 160);
    }, { passive: false });
    root.addEventListener('dblclick', function (e) { e.preventDefault(); });

    function on(sel, fn) { var b = root.querySelector(sel); if (b) b.addEventListener('click', fn); return b; }
    on('[data-pz-in]', function () { var c = center(); zoomAt(1.6, c.x, c.y, false); });
    on('[data-pz-out]', function () { var c = center(); zoomAt(1 / 1.6, c.x, c.y, false); });
    on('[data-pz-fit]', function () { s = 1; tx = 0; ty = 0; apply(false); });
    var full = on('[data-pz-full]', function () {
      var onf = !root.classList.contains('is-full');
      root.classList.toggle('is-full', onf);
      document.body.classList.toggle('pz-lock', onf);
      full.setAttribute('aria-pressed', onf ? 'true' : 'false');
      full.textContent = onf ? 'Закрыть' : 'На весь экран';
      s = 1; tx = 0; ty = 0; apply(false);
    });
    // слои: мебель, розетки, трубы… — включаются и выключаются чекбоксами
    root.querySelectorAll('[data-pz-layer]').forEach(function (cb) {
      function sync() {
        root.querySelectorAll(cb.getAttribute('data-pz-layer')).forEach(function (el) { el.style.display = cb.checked ? '' : 'none'; });
      }
      cb.addEventListener('change', sync);
      sync();
    });
    var orig = root.querySelector('[data-pz-orig]');
    if (orig) orig.addEventListener('change', function () { root.classList.toggle('show-orig', orig.checked); });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && root.classList.contains('is-full') && full) full.click();
    });
    window.addEventListener('resize', function () { apply(false); });
  }

  document.querySelectorAll('[data-pz]').forEach(function (el) { new PanZoom(el); });
})();
