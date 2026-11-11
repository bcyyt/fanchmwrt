#!/usr/bin/env python3
# fwx-dashboard 快捷方式条注入（S20P 移植版）
# 用法：python3 fwx-dashboard-shortcuts-patch.py <dashboard.htm 路径>
# 来源：OpenWRT-CI Scripts/vantage-shortcuts-patch.py 的 fwx 仪表盘适配版
#   - 快捷方式条：数据来自 /cgi-bin/statusmon（statusfw 提供），固定项对准 fwx 体系
#   - PPE 硬件 offload 占用行：数据来自 /cgi-bin/statusppe（statusppe 三件套）
#   - 样式对齐 fwx .card（含 data-darkmode 暗色跟随）
# 幂等：已注入时跳过。锚点缺失时报错退出（CI 可感知）。
import sys

path = sys.argv[1]
src = open(path, encoding='utf-8').read()

if 'fwx-scw' in src:
    print('fwx-dashboard-shortcuts: already patched, skip')
    sys.exit(0)

ANCHOR = '<div class="dashboard_mobile" id="dashboard-mobile"></div>'
if ANCHOR not in src:
    print('fwx-dashboard-shortcuts: anchor not found', file=sys.stderr)
    sys.exit(1)

BLOCK = r'''<section class="fwx-scw" id="fwx-scw">
    <div class="fwx-scw-title">快捷方式</div>
    <div class="fwx-scw-links" id="fwx-scw-links"><span class="fwx-scw-hint">加载中…</span></div>
    <div class="fwx-scw-ppe" id="fwx-scw-ppe" hidden></div>
</section>
<style>
    .fwx-scw {
        border-radius: 8px;
        border: 1px solid rgba(121, 141, 164, 0.36);
        padding: 10px 16px;
        margin: 0 0 12px;
    }
    [data-darkmode="true"] .fwx-scw { border-color: rgba(255, 255, 255, 0.24); }
    .fwx-scw-title { font-size: 13px; font-weight: 600; opacity: .75; margin: 2px 0 8px; }
    .fwx-scw-links { display: flex; flex-wrap: wrap; gap: 8px; }
    .fwx-scw-links a {
        display: inline-flex; align-items: center; gap: 6px;
        padding: 6px 13px; border-radius: 8px;
        border: 1px solid rgba(121, 141, 164, 0.3);
        text-decoration: none; color: inherit;
        font-size: 13px; font-weight: 500;
        background: rgba(121, 141, 164, 0.06);
        transition: background .15s;
    }
    [data-darkmode="true"] .fwx-scw-links a { border-color: rgba(255,255,255,.22); background: rgba(255,255,255,.06); }
    .fwx-scw-links a:hover { background: rgba(121, 141, 164, 0.16); }
    .fwx-scw-links a svg { width: 14px; height: 14px; opacity: .75; }
    .fwx-scw-hint { font-size: 12px; opacity: .5; }
    .fwx-scw-ppe { font-size: 12px; opacity: .65; margin-top: 8px; font-variant-numeric: tabular-nums; }
</style>
<script type="text/javascript">//<![CDATA[
(function() {
    var FIXED = [
        ['网络设置', '/cgi-bin/luci/admin/fwx_network', 'M5 12.55a11 11 0 0114.08 0'],
        ['防火墙', '/cgi-bin/luci/admin/fwx_network/firewall', 'M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z'],
        ['系统管理', '/cgi-bin/luci/admin/system/admin', 'M12 15.5a5.5 5.5 0 10-11 0 5.5 5.5 0 0011 0zM19.4 15a1.65 1.65 0 00.33 1.82']
    ];
    var ICONS = {
        iptv: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><polyline points="8 21 12 17 16 21"/></svg>',
        mediahub: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="2" width="20" height="20" rx="2"/><circle cx="12" cy="12" r="4"/></svg>',
        rtp2httpd: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>',
        lucky: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 010 20 15.3 15.3 0 010-20"/></svg>',
        daed: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
        natfrp: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>',
        docker: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="10" width="4" height="4"/><rect x="7" y="10" width="4" height="4"/><rect x="12" y="10" width="4" height="4"/><rect x="7" y="5" width="4" height="4"/><path d="M2 15h16a4 4 0 004-4"/></svg>',
        ttyd: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>',
        upnp: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82"/></svg>'
    };
    function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
    function svg(p) { return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="' + p + '"/></svg>'; }
    function scHref(h) { if (!h || h.charAt(0) === '/') return h; try { var u = new URL(h, location.href); u.hostname = location.hostname; return u.href; } catch (e) { return h; } }
    function render(list) {
        var wrap = document.getElementById('fwx-scw-links');
        if (!wrap) return;
        var html = '';
        FIXED.forEach(function(f) { html += '<a href="' + f[1] + '">' + svg(f[2]) + esc(f[0]) + '</a>'; });
        (list || []).forEach(function(s) {
            if (!s || !s.href || !s.label) return;
            html += '<a href="' + scHref(s.href) + '"' + ((s.target === '_blank' || s.id === 'rtp2httpd') ? ' target="_blank" rel="noopener noreferrer"' : '') + '>' + (ICONS[s.id] || svg('M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71')) + esc(s.label) + '</a>';
        });
        wrap.innerHTML = html;
    }
    function part(name, p) {
        if (!p || !p.t) return name + ': 0 (v4: 0 v6: 0)';
        return name + ': ' + p.t + ' (v4: ' + (p.v4 || 0) + ' v6: ' + (p.v6 || 0) + ')';
    }
    function loadPpe() {
        fetch('/cgi-bin/statusppe', { cache: 'no-store' }).then(function(r) { return r.json(); }).then(function(d) {
            var el = document.getElementById('fwx-scw-ppe');
            if (!el) return;
            el.hidden = false;
            el.textContent = 'CPU: USR ' + (d.usr || 0) + '% SYS ' + (d.sys || 0) + '%  |  ' + part('PPE0', d.ppe0) + '  ' + part('PPE1', d.ppe1);
        }).catch(function() {});
    }
    function load() {
        fetch('/cgi-bin/statusmon', { cache: 'no-store' }).then(function(r) { return r.json(); }).then(function(d) { render(d.shortcuts || []); }).catch(function() {});
        loadPpe();
    }
    load();
    setInterval(load, 60000);
})();
//]]></script>
'''

src = src.replace(ANCHOR, BLOCK + ANCHOR, 1)
open(path, 'w', encoding='utf-8').write(src)
print('fwx-dashboard-shortcuts: patched OK')
