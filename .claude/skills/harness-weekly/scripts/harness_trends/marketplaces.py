"""Official marketplace catalog counts, one designated public source per product.

Pi does not come through here: its official pi.dev Package Catalog is already
collected in full by catalogs.py and takes precedence over any third-party page.
"""
from datetime import datetime, timezone
import re
from .collect import FetchError


def _observed_at(client, url):
    event = next((e for e in reversed(client.events) if e['url'] == url), None)
    return datetime.fromtimestamp(event['fetched_unix'], timezone.utc).isoformat() if event else datetime.now(timezone.utc).isoformat()


def parse_dshmarket(markup):
    """dshmarket.com states its community plugin count in several places; take the live hero counter first."""
    for pattern in (r'id="count">([\d,]+)</span>',
                    r'([\d,]+)\s+community\s+plugins',
                    r'Browse\s+(?:all\s+)?([\d,]+)\s+plugins'):
        match = re.search(pattern, markup)
        if match:
            return int(match.group(1).replace(',', ''))
    raise FetchError('dshmarket.com 未识别到插件总数，需检查页面结构')


def parse_mcptop(markup):
    """mcptop.com tracks the ChatGPT Plugin Directory. The report cites the Plugins facet
    (the directory also publishes a larger all-plugins total, kept for context)."""
    facet = re.search(r'title="Plugins">\s*Plugins\s*</span>\s*<span[^>]*>\s*([\d,]+)\s*</span>', markup)
    if not facet:
        raise FetchError('mcptop.com 未识别到 Plugins 分类计数，需检查页面结构')
    total = re.search(r'that.s\s+([\d,]+)\s+plugins', markup)
    return int(facet.group(1).replace(',', '')), int(total.group(1).replace(',', '')) if total else None


def parse_claude_marketplace(markup):
    """claude.com/marketplace/plugins announces the result count in a screen-reader status line."""
    match = re.search(r'role="status">\s*([\d,]+)\s+plugins?\s*</p>', markup)
    if not match:
        raise FetchError('claude.com/marketplace/plugins 未识别到插件总数，需检查页面结构')
    return int(match.group(1).replace(',', ''))


def collect_marketplaces(client, config):
    """Fetch the three marketplace landing pages and parse their published counts."""
    specs = {'dsh': ('dshmarket.com 社区插件市场', parse_dshmarket),
             'codex': ('mcptop.com · ChatGPT插件目录', parse_mcptop),
             'claude': ('claude.com/marketplace/plugins', parse_claude_marketplace)}
    settings = config.get('marketplaces', {})
    out = {}
    for pid, (label, parser) in specs.items():
        url = settings.get(pid, {}).get('url')
        row = {'label':label, 'source':url, 'status':'missing', 'count':None, 'observed_at':None}
        if not url:
            row['reason'] = 'config.json 未配置 marketplaces.' + pid + '.url'
            out[pid] = row
            continue
        try:
            markup = client.get(url)
            parsed = parser(markup)
            if pid == 'codex':
                count, directory_total = parsed
                row['directory_total'] = directory_total
                row['unit'] = 'ChatGPT插件目录 Plugins 分类计数；目录全量见 directory_total'
            else:
                count = parsed
                row['unit'] = '官网公布的插件总数'
            row.update(status='ok', count=count, observed_at=_observed_at(client, url))
        except FetchError as exc:
            row['reason'] = str(exc)
        out[pid] = row
    return out
