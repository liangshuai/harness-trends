"""Public plugin popularity proxies. Never infer active users from directory order."""
from datetime import datetime, timezone
import html
import json
from pathlib import Path
import re
from urllib.parse import urljoin, urlsplit

from .collect import FetchError
from .marketplaces import _observed_at

SPECS = {
    'claude': ('Claude Code', 'https://claude.com/marketplace/plugins', '累计安装量', '累计；截至来源采集时点',
               '仅纳入 worksWith 明示 claude-code 且有安装量的插件；累计安装不等于近期活跃。'),
    'pi': ('Pi', 'https://pi.dev/packages', 'npm 月下载量', '来源标注 /mo；滚动月窗口',
           '官方 Most downloads 列表；含 extension、skill、theme、prompt 及组合包；下载包含更新与 CI。'),
    'codex': ('Codex', 'https://mcptop.com/?source=openai', '目录排名', '第三方每日目录快照',
              'mcptop 记录 ChatGPT / Codex 共享目录的位置，无公开活跃量或安装量；不是 Codex 专属活跃 Top 10，兼容性以插件详情为准。'),
    'dsh': ('DSH', 'https://dshmarket.com/', 'npm 近 30 天下载量', '滚动 30 天',
            '市场 Most installed 实际按 npm downloads 排序；下载不是独立安装或活跃用户。'),
}


def clean(value):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', value))).strip()


def capture(pattern, text):
    match = re.search(pattern, text, re.S)
    if not match:
        raise FetchError('插件榜单页面结构变化，缺少预期字段')
    return match.group(1)


def parse_claude(markup):
    # Next flight payloads can split an object across script boundaries. Decode
    # each JS string as JSON, concatenate, then decode the actual items array.
    chunks = []
    for encoded in re.findall(r'self\.__next_f\.push\(\[1,("(?:\\.|[^"\\])*")\]\)', markup):
        chunks.append(json.loads(encoded))
    payload = ''.join(chunks)
    marker = re.search(r'"items":\s*(\[)\s*\{\s*"_id":\s*"directoryPlugin\.', payload)
    if not marker:
        raise FetchError('Claude 未识别到插件结构化目录')
    items, _ = json.JSONDecoder().raw_decode(payload[marker.start(1):])
    rows = []
    for item in items:
        compatible = any(w.get('value') == 'claude-code' for w in (item.get('worksWith') or []))
        count = item.get('installs')
        if compatible and type(count) is int and count >= 0:
            rows.append({'id': item['slug'], 'name': item['title'], 'description': item.get('subheading') or '',
                         'value': count, 'url': 'https://claude.com/marketplace/plugins/' + item['slug']})
    return sorted(rows, key=lambda r: (-r['value'], r['id']))[:10]


def parse_pi(markup):
    if not re.search(r'<option value="downloads" selected', markup):
        raise FetchError('Pi 页面未确认按下载量排序')
    rows = []
    for card in re.findall(r'<article\b[^>]*data-package-card="true".*?</article>', markup, re.S):
        name = html.unescape(capture(r'data-package-name="([^"]+)"', card))
        rows.append({'id': name, 'name': name,
                     'description': clean(capture(r'<p class="packages-desc">(.*?)</p>', card)),
                     'value': int(capture(r'data-package-downloads="(\d+)"', card)),
                     'url': urljoin('https://pi.dev', html.unescape(capture(r'data-package-path="([^"]+)"', card)))})
    return sorted(rows, key=lambda r: (-r['value'], r['id']))[:10]


def parse_dsh(markup):
    section = capture(r'<section[^>]*id="popular"[^>]*>(.*?)</section>', markup)
    if 'Ranked by npm downloads over the last 30 days.' not in section:
        raise FetchError('DSH 排序口径发生变化')
    rows = []
    for card in re.findall(r'<li class="pcard">(.*?)</li>', section, re.S):
        link = re.search(r'<a class="pname" href="([^"]+)">(.*?)</a>', card, re.S)
        if not link:
            raise FetchError('DSH 榜单缺少插件链接')
        name = clean(link[2]).replace('/ ', '/')
        rows.append({'id': link[1], 'name': name, 'url': html.unescape(link[1]),
                     'description': clean(capture(r'<p>(.*?)</p>', card)),
                     'value': int(capture(r'([\d,]+) / 30 days', card).replace(',', ''))})
    return sorted(rows, key=lambda r: (-r['value'], r['id']))[:10]


def parse_codex(markup):
    if 'publishes no scores' not in markup:
        raise FetchError('共享目录位置榜的口径未确认')
    tbody = capture(r'<tbody>(.*?)</tbody>', markup)
    rows = []
    for card in re.findall(r'<tr\b[^>]*>(.*?)</tr>', tbody, re.S):
        name = clean(capture(r'<span class="rank-name">(.*?)</span>', card))
        rows.append({'id': capture(r'class="rank-link" href="([^"]+)"', card), 'name': name,
                     'description': clean(capture(r'<span class="rank-blurb">(.*?)</span>', card)),
                     'value': int(capture(r'>#(\d+)</span>', card)),
                     'url': urljoin('https://mcptop.com', capture(r'class="rank-link" href="([^"]+)"', card))})
    return sorted(rows, key=lambda r: (r['value'], r['id']))[:10]


PARSERS = {'claude': parse_claude, 'pi': parse_pi, 'codex': parse_codex, 'dsh': parse_dsh}


def collect_plugin_rankings(client, config):
    result = {'version': 1, 'collected_at': datetime.now(timezone.utc).isoformat(), 'products': {}}
    for pid, (name, default_url, metric, window, note) in SPECS.items():
        url = config.get('plugin_rankings', {}).get(pid, {}).get('url', default_url)
        row = {'name': name, 'source': url, 'metric': metric, 'window': window, 'note': note,
               'status': 'missing', 'entries': [], 'observed_at': None,
               'ranking_kind': 'directory_order' if pid == 'codex' else 'popularity_proxy'}
        try:
            markup = client.get(url)
            row['observed_at'] = _observed_at(client, url)
            entries = PARSERS[pid](markup)
            if len({e['id'] for e in entries}) != len(entries) or not entries:
                raise FetchError('榜单为空或插件标识重复')
            row['entries'] = [dict(e, rank=i) for i, e in enumerate(entries, 1)]
            row['status'] = 'ok' if len(entries) == 10 else 'partial'
            if len(entries) < 10:
                row['reason'] = f'只取得 {len(entries)} 条可核验条目，不补齐虚构名次'
        except (FetchError, ValueError, KeyError, TypeError) as exc:
            row['reason'] = str(exc)
        result['products'][pid] = row
    return result


def safe_link(url, label):
    from .render_methodology import esc
    if urlsplit(url).scheme not in ('https', 'http'):
        return esc(label)
    return f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(label)}</a>'


def load_plugin_translations():
    """Editorial Chinese descriptions keyed by plugin URL (data/plugin_rankings/translations.json).
    Missing entries fall back to the collected source text."""
    path = Path(__file__).resolve().parent.parent/'data/plugin_rankings/translations.json'
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        return {}
    return data.get('plugins') or {}


def render_plugin_rankings(run):
    from .render_methodology import esc, table
    products = run.get('plugin_rankings', {}).get('products', {})
    translations = load_plugin_translations()
    body = ('<section id="plugin-rankings"><div class="section-head"><div>'
            '<div class="section-label">PLUGIN POPULARITY / TOP 10</div><h2>Harness Top10 插件观察</h2>'
            '<p class="sub">安装与下载为热度代理，不等于活跃用户；各榜仅在自身口径内排序，不跨产品比较数值。</p></div></div>')
    body += '<div class="plugin-tables">'
    for pid, (name, url, metric, _, _) in SPECS.items():
        row = products.get(pid, {})
        title = name + (' · Top 10' if pid == 'codex' else ' · 热度 Top 10')
        # The metric label is presentation: always take it from SPECS, not the stored snapshot.
        body += f'<h3>{esc(title)}</h3><p class="sub">{safe_link(row.get("source", url), "榜单来源")} · {esc(metric)}</p>'
        entries = []
        for entry in row.get('entries', []):
            value = f"#{entry['value']}" if pid == 'codex' else f"{entry['value']:,}"
            description = translations.get(entry['url']) or entry['description']
            entries.append([str(entry['rank']), safe_link(entry['url'], entry['name']), esc(value), esc(description)])
        if entries:
            body += table(['榜内名次', '插件', metric, '功能介绍'], entries)
        if row.get('status') != 'ok':
            body += '<p class="alert">' + esc(row.get('reason', '该快照尚未采集插件榜单；下次运行 --refresh 自动采集。')) + '</p>'
    return body + '</div></section>'
