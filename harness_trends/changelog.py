"""Scripted extraction of each official repo's releases and changelog within the report window."""
from datetime import date, datetime, timezone
import json
import os
import re
from .collect import FetchError

# Bodies below this size are placeholder stubs (e.g. "Release 0.169.0-alpha.3"), not notes.
MIN_BODY_CHARS = 80
BODY_CAP = 20000
FEATURE_HEADINGS = ('New Features', '新增功能')


def _version_of(tag):
    return re.sub(r'^(rust-v|dsh-v|v)', '', tag or '')


def _clean(text):
    text = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', text)
    text = re.sub(r'</?[a-zA-Z][^>]*>', ' ', text)
    text = text.replace('**', '').replace('`', '')
    return re.sub(r'\s+', ' ', text).strip()


def _is_heading(line):
    return bool(re.match(r'^#{1,6}\s', line) or re.match(r'^<h[1-6]\b', line, re.I))


def _is_feature_heading(line):
    return any(marker in line for marker in FEATURE_HEADINGS)


def feature_bullets(text, limit=8):
    """Bullets under the first New Features / 新增功能 heading; falls back to Added-prefixed bullets."""
    collected, inside = [], False
    for line in text.splitlines():
        stripped = line.strip()
        if _is_heading(stripped):
            if inside and not _is_feature_heading(stripped):
                break
            inside = _is_feature_heading(stripped)
            continue
        if inside and re.match(r'^[-*]\s+', stripped):
            collected.append(_clean(stripped.lstrip('-* ')))
    if not collected:
        collected = [_clean(m) for m in re.findall(r'^\s*[-*]\s+(Added\b.*)$', text, re.M)]
    return collected[:limit]


def parse_changelog(markup, versions):
    """Return {version: section_text} for the requested versions of a `## <version>` changelog."""
    sections, current = {}, None
    for line in markup.splitlines():
        heading = re.match(r'^##\s+(\S+)\s*$', line.strip())
        if heading:
            current = heading.group(1)
            sections[current] = []
        elif current is not None:
            sections[current].append(line)
    joined = {v: '\n'.join(lines).strip() for v, lines in sections.items()}
    return {v: joined[v] for v in versions if joined.get(v)}


def collect_product_updates(client, products, window):
    """GitHub releases inside the window plus the CHANGELOG.md sections matching them."""
    token = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
    start, end = date.fromisoformat(window['start']), date.fromisoformat(window['end'])
    out = {}
    for product in products:
        pid, repo = product['id'], product['repo']
        row = {'repo':repo, 'status':'missing', 'releases':[], 'changelog':None, 'errors':[]}
        try:
            rows = client.json(f'https://api.github.com/repos/{repo}/releases?per_page=30', token=token)
            if not isinstance(rows, list):
                raise FetchError('Releases 响应不可读')
        except FetchError as exc:
            row['errors'].append(str(exc))
            out[pid] = row
            continue
        in_window = []
        for release in rows:
            tag = release.get('tag_name') or ''
            published = release.get('published_at')
            # Product release lines only; repos also tag vendored libraries (e.g. libcap-v2.75).
            if not published or not re.match(r'^(rust-v|dsh-v|v)\d', tag):
                continue
            day = datetime.fromisoformat(published.replace('Z', '+00:00')).astimezone(timezone.utc).date()
            if start <= day <= end:
                in_window.append({'tag':tag, 'version':_version_of(tag),
                                  'published_at':published, 'prerelease':bool(release.get('prerelease')),
                                  'html_url':release.get('html_url'),
                                  'body':(release.get('body') or '')[:BODY_CAP],
                                  'body_chars':len(release.get('body') or '')})
        row['releases'] = in_window
        row['status'] = 'ok' if in_window else 'empty'
        if in_window:
            versions = sorted({r['version'] for r in in_window if r['version']})
            try:
                # HEAD follows each repo's default branch, whatever it is named.
                markup = client.get(f'https://raw.githubusercontent.com/{repo}/HEAD/CHANGELOG.md')
                row['changelog'] = {'source':f'https://github.com/{repo}/blob/HEAD/CHANGELOG.md',
                                    'sections':parse_changelog(markup, versions), 'versions_found':versions}
            except FetchError:
                row['changelog'] = None
        out[pid] = row
    return out


def summarize(product_update):
    """Per-version highlight bullets: changelog section when present, else substantive release bodies."""
    summary = []
    changelog = product_update.get('changelog') or {}
    sections = changelog.get('sections') or {}
    for release in product_update.get('releases', []):
        version = release.get('version')
        item = {'tag':release['tag'], 'version':version, 'published_at':release['published_at'],
                'prerelease':release['prerelease'], 'html_url':release['html_url'],
                'highlights':[], 'basis':None}
        if sections.get(version):
            item['highlights'] = feature_bullets(sections[version])
            item['basis'] = 'CHANGELOG.md'
        elif release['body_chars'] >= MIN_BODY_CHARS:
            item['highlights'] = feature_bullets(release['body'])
            item['basis'] = 'GitHub Release'
        summary.append(item)
    return summary
