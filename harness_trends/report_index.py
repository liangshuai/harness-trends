"""Self-contained home page for the reports directory: latest issue plus every archived window.
All links are relative so the directory deploys as a static site anywhere."""
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from .render_methodology import esc


def collect_windows(reports):
    """One row per archived window with a canonical report page; newest first.
    Early windows may predate the Markdown edition and carry HTML only."""
    rows = []
    archive = reports/'archive'
    if not archive.is_dir():
        return rows
    for folder in sorted((d for d in archive.iterdir() if d.is_dir()), key=lambda d: d.name, reverse=True):
        page, markdown = folder/'report.html', folder/'report.md'
        if not page.is_file():
            continue
        text = markdown.read_text() if markdown.is_file() else ''
        match = re.search(r'数据窗口：(\d{4}-\d{2}-\d{2}) — (\d{4}-\d{2}-\d{2})', text)
        start = match.group(1) if match else ''
        end = match.group(2) if match else folder.name
        rows.append({'start': start, 'end': end or folder.name, 'folder': folder.name,
                     'html': f'archive/{folder.name}/report.html',
                     'md': f'archive/{folder.name}/report.md' if markdown.is_file() else None})
    return rows


def render_report_index(reports, current_window):
    """Write reports/index.html: latest issue card on top, then the full history table."""
    rows = collect_windows(reports)
    generated = datetime.now(timezone.utc).astimezone(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M')
    latest_end = max((r['end'] for r in rows), default='')
    is_latest = current_window['end'] >= latest_end if latest_end else True
    cards = ['<div class="card latest"><div class="tag">最新一期</div>'
             f'<div class="win">{esc(current_window["start"])} — {esc(current_window["end"])}</div>'
             '<div class="links">'
             f'<a href="latest.html">查看本期报告（HTML）</a>'
             f'<a href="latest.md" class="md">Markdown 版</a>'
             + (f'<a href="archive/{esc(current_window["end"])}/report.html">存档副本</a>' if any(
                 r['end'] == current_window['end'] for r in rows) else '')
             + '</div></div>']
    body = []
    for row in rows:
        mark = ' <span class="badge">最新</span>' if is_latest and row['end'] == current_window['end'] else ''
        md_cell = f'<a href="{esc(row["md"])}">Markdown</a>' if row['md'] else '<span class="muted">—</span>'
        body.append(f'<tr><td>{esc(row["end"])}{mark}</td><td>{esc(row["start"])} — {esc(row["end"])}</td>'
                    f'<td><a href="{esc(row["html"])}">HTML</a></td>'
                    f'<td>{md_cell}</td></tr>')
    table = ('<table><thead><tr><th>期号（窗口结束日）</th><th>数据窗口</th><th>报告</th><th>Markdown</th></tr></thead>'
             '<tbody>' + ''.join(body) + '</tbody></table>') if rows else '<p class="empty">暂无历史期数。</p>'
    html = ('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>AI Harness 市场观察周报 · 历史期数</title><style>' + INDEX_CSS + '</style></head><body>'
            '<header><div class="eyebrow">HARNESS INTELLIGENCE / WEEKLY BRIEF</div>'
            '<h1>AI Harness 市场观察周报</h1>'
            f'<p class="sub">全部历史期数索引 · 共 {len(rows)} 期 · 更新于 {esc(generated)}（北京时间）</p></header>'
            '<main>' + ''.join(cards) + '<h2>历史期数</h2>' + table +
            '<p class="foot">本页与各期报告均为纯静态相对链接，reports 目录可作为静态站点整体部署；'
            '每期报告页内导航含「查看历史」回到本页、「MD 版」查看该期 Markdown。</p></main></body></html>')
    (reports/'index.html').write_text(html)
    return reports/'index.html'


INDEX_CSS = ''':root{--ink:#242424;--muted:#777;--line:#E8E9EB;--aux:#F6F7F8;--primary:#F05A23;--secondary:#FFF1EA}
*{box-sizing:border-box}body{margin:0;color:var(--ink);font:14px/1.7 -apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;background:#fff}
header{border-top:4px solid var(--primary);border-bottom:1px solid var(--line);padding:34px 26px 28px;max-width:900px;margin:0 auto}
.eyebrow{font-size:10px;letter-spacing:3.5px;color:#AF451F}h1{font-size:30px;margin:12px 0 8px;color:var(--primary)}
.sub{color:var(--muted);margin:0}main{max-width:900px;margin:0 auto;padding:10px 26px 50px}
h2{font-size:18px;margin:26px 0 10px}
.card{border:1px solid var(--line);border-radius:10px;padding:22px;margin:18px 0;background:var(--secondary)}
.card.latest{border-color:#F4D4C5}.card .tag{font-size:10px;letter-spacing:2px;color:#A8411A;margin-bottom:8px}
.card .win{font-size:22px;font-weight:680;margin-bottom:12px}.card .links{display:flex;gap:18px;flex-wrap:wrap}
a{color:#B33D13;text-underline-offset:3px}.card .links a{text-decoration:none;border:1px solid #F4D4C5;border-radius:6px;padding:7px 12px;font-size:12px;background:#fff}
.card .links a.md{border-color:var(--line)}
table{width:100%;border-collapse:collapse;font-size:13px;background:#fff;border:1px solid var(--line);border-radius:9px;overflow:hidden}
th{font-size:11px;font-weight:500;background:var(--aux);color:#666;text-align:left}th,td{padding:12px 15px;border-bottom:1px solid var(--aux)}
tbody tr:last-child td{border:0}td:first-child{font-weight:600}.badge{font-size:10px;color:#A8411A;border:1px solid #F4D4C5;background:var(--secondary);border-radius:4px;padding:2px 6px;margin-left:6px}
.empty{color:var(--muted)}.muted{color:var(--muted)}.foot{font-size:11px;color:var(--muted);margin-top:18px}
@media(max-width:660px){h1{font-size:24px}.card .win{font-size:18px}table{font-size:12px}th,td{padding:9px 10px}}'''
