from __future__ import annotations

import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import re
import threading
import time
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


class FetchError(Exception):
    pass


class Client:
    """Read-only client. Persist public responses, never request credentials."""

    def __init__(self, root: Path, run_dir: Path, budget=44, cache_hours=24, offline=False):
        self.cache = root / 'data/cache'
        self.cache.mkdir(parents=True, exist_ok=True)
        self.raw = run_dir
        self.raw.mkdir(parents=True, exist_ok=True)
        self.budget = budget
        self.cache_seconds = cache_hours * 3600
        self.offline = offline
        self.github_calls = 0
        self.events = []
        self.memory = {}
        self.lock = threading.Lock()

    def get(self, url, *, token=None, fresh=False, _attempt=0):
        key = hashlib.sha256(url.encode()).hexdigest()
        path = self.cache / (key + '.json')
        cached = None
        if not fresh and url in self.memory:
            cached=self.memory[url]
        elif path.exists():
            cached = json.loads(path.read_text())
        if cached and (self.offline or (not fresh and (url in self.memory or time.time() - cached['fetched_unix'] < self.cache_seconds))):
            self._save(key, cached)
            if cached['status'] != 200:
                raise FetchError(f'HTTP {cached["status"]}（缓存）')
            return cached['body']
        if self.offline:
            raise FetchError('离线缓存缺失')
        if url.startswith('https://api.github.com/'):
            with self.lock:
                if self.github_calls >= self.budget:
                    raise FetchError('达到本次 GitHub 请求预算')
                self.github_calls += 1
        headers = {'User-Agent': 'harness-trends/1.0', 'Accept': 'application/json'}
        if token:
            headers['Authorization'] = 'Bearer ' + token
        try:
            with urlopen(Request(url, headers=headers), timeout=18) as response:
                body = response.read().decode('utf-8', 'replace')
                envelope = {'url': url, 'fetched_unix': time.time(), 'status': response.status, 'body': body,
                            'has_next': 'rel="next"' in response.headers.get('Link', '')}
        except HTTPError as exc:
            # Do not log server response bodies, headers, or credentials.
            if exc.code in (408,429,500,502,503,504) and _attempt<2:
                time.sleep(_attempt+1)
                return self.get(url,token=token,fresh=fresh,_attempt=_attempt+1)
            if exc.code == 404 and url.startswith('https://raw.githubusercontent.com/'):
                envelope={'url':url,'fetched_unix':time.time(),'status':404,'body':'','has_next':False}
                path.write_text(json.dumps(envelope))
                self._save(key,envelope)
            raise FetchError(f'HTTP {exc.code}') from None
        except (URLError, TimeoutError, OSError):
            if _attempt<1:
                time.sleep(1)
                return self.get(url,token=token,fresh=fresh,_attempt=_attempt+1)
            raise FetchError('网络请求失败或超时') from None
        path.write_text(json.dumps(envelope, ensure_ascii=False))
        self._save(key, envelope)
        return body

    def _save(self, key, envelope):
        (self.raw / (key + '.json')).write_text(json.dumps(envelope, ensure_ascii=False))
        with self.lock:
            self.memory[envelope['url']]=envelope
            self.events.append({k: envelope[k] for k in ['url', 'fetched_unix', 'status', 'has_next']})

    def json(self, url, **kwargs):
        try:
            return json.loads(self.get(url, **kwargs))
        except json.JSONDecodeError:
            raise FetchError('响应不是有效 JSON') from None


def npm_downloads(client, package, start, end):
    url = f'https://api.npmjs.org/downloads/range/{start}:{end}/' + quote(package, safe='@')
    try:
        payload = client.json(url)
        rows = payload.get('downloads')
        if not isinstance(rows, list) or not rows:
            raise FetchError('缺少逐日下载数据')
        expected = (end - start).days + 1
        days = {r['day'] for r in rows if isinstance(r.get('downloads'), int) and r['downloads'] >= 0}
        required = {(start + __import__('datetime').timedelta(days=i)).isoformat() for i in range(expected)}
        if days != required or len(rows) != expected:
            raise FetchError('下载窗口不完整')
        return {'package':package, 'status':'ok', 'total':sum(r['downloads'] for r in rows), 'daily':rows,
                'source':url, 'start':str(start), 'end':str(end)}
    except FetchError as exc:
        return {'package':package, 'status':'missing', 'total':None, 'reason':str(exc), 'source':url}


def is_human(account):
    return bool(account.get('id')) and account.get('type') == 'User' and not account.get('login', '').lower().endswith('[bot]')


def raw_json(client, repo, branch, path):
    url = f'https://raw.githubusercontent.com/{repo}/{quote(branch, safe="")}/{quote(path, safe="/")}'
    try:
        return client.json(url), url
    except FetchError:
        return None, url


def verify_repo(client, product, repo):
    """Conservative manifest checks. Unresolved is distinct from confirmed invalid."""
    name, branch = repo['full_name'], repo.get('default_branch', 'main')
    if name.lower() == product['repo'].lower():
        return {'repo':name, 'status':'excluded', 'reason':'核心仓库，非第三方插件'}
    pid = product['id']
    artifacts = []
    paths = ({'codex':['.codex-plugin/plugin.json', '.agents/plugins/marketplace.json'],
              'claude':['.claude-plugin/plugin.json', '.claude-plugin/marketplace.json'],
              'dsh':['package.json'], 'pi':['package.json']})[pid]
    for path in paths:
        manifest, source = raw_json(client, name, branch, path)
        if not isinstance(manifest, dict):
            continue
        if 'marketplace' in path:
            for entry in manifest.get('plugins', []):
                if not isinstance(entry, dict):
                    continue
                src = entry.get('source')
                # External marketplace entries are discovery leads, not plugins owned by this repo.
                if not isinstance(src, str) or not src.startswith('./') or '..' in src.split('/'):
                    continue
                subdir = src.removeprefix('./').rstrip('/')
                subpath = (subdir + '/' if subdir else '') + ('.codex-plugin/plugin.json' if pid == 'codex' else '.claude-plugin/plugin.json')
                child, childurl = raw_json(client, name, branch, subpath)
                if isinstance(child, dict) and child.get('name'):
                    artifacts.append({'name':child['name'], 'path':subdir, 'source':childurl})
        elif pid in ('codex', 'claude') and manifest.get('name'):
            artifacts.append({'name':manifest['name'], 'path':'', 'source':source})
        elif pid == 'pi':
            keywords = manifest.get('keywords', [])
            if isinstance(manifest.get('pi'), dict) or 'pi-package' in keywords:
                artifacts.append({'name':manifest.get('name', name), 'path':'', 'source':source})
        elif pid == 'dsh':
            text = json.dumps(manifest).lower()
            deps = {**manifest.get('dependencies', {}), **manifest.get('peerDependencies', {}), **manifest.get('devDependencies', {})}
            if any('deepseek' in k or '/dsh' in k for k in deps) or ('cordis' in text and any(t in text for t in ['dsh','deepseek'])):
                artifacts.append({'name':manifest.get('name', name), 'path':'', 'source':source})
    # Root and marketplace subdirectory may expose the same named publication.
    unique = {}
    for artifact in artifacts:
        unique.setdefault(str(artifact['name']).casefold(), artifact)
    return {'repo':name, 'status':'verified' if unique else 'unresolved',
            'artifacts':list(unique.values()), 'owner':repo['owner'], 'stars':repo.get('stargazers_count'),
            'branch':branch, 'pushed_at':repo.get('pushed_at'),
            'reason':None if unique else '未命中当前 manifest 规则或请求未完成；不能据此认定不是插件'}


def github_ecosystem(client, product, settings):
    query = product['query']
    url = 'https://api.github.com/search/repositories?' + urlencode({'q':query, 'per_page':100, 'sort':'stars', 'order':'desc'})
    token = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
    result = {'query':query, 'source':url, 'status':'missing', 'candidate_total':None, 'repos':[],
              'contributor_ids':[], 'publisher_ids':[], 'errors':[], 'selection':'搜索前100条内按仓库名哈希固定抽样；非全市场随机样本'}
    try:
        data = client.json(url, token=token)
        if not isinstance(data.get('items'), list):
            raise FetchError('搜索响应缺少 items')
    except FetchError as exc:
        result['errors'].append(str(exc))
        return result
    result.update(status='partial', candidate_total=data.get('total_count'), incomplete_search=bool(data.get('incomplete_results')))
    frame = data['items']
    result['frame_size'] = len(frame)
    sample = sorted(frame, key=lambda x:hashlib.sha256(x['full_name'].lower().encode()).hexdigest())[:settings['candidate_limit']]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        repos = list(pool.map(lambda r:verify_repo(client, product, r), sample))
    result['repos'] = repos
    result['checked_repos'] = len(repos)
    verified = [r for r in repos if r['status']=='verified']
    result['verified_repos'] = len(verified)
    result['verified_artifacts'] = sum(len(r['artifacts']) for r in verified)
    result['unresolved_repos'] = sum(r['status']=='unresolved' for r in repos)
    result['publisher_ids'] = sorted({r['owner']['id'] for r in verified if is_human(r['owner'])})
    selected = sorted(verified, key=lambda r:hashlib.sha256(r['repo'].lower().encode()).hexdigest())[:settings['contributor_repo_limit']]
    accounts, observed = {}, []
    for repo in selected:
        people = {}
        error = None
        truncated = False
        for page in range(1, settings['contributor_pages'] + 1):
            u = f"https://api.github.com/repos/{repo['repo']}/contributors?per_page=100&anon=1&page={page}"
            try:
                rows = client.json(u, token=token)
                if not isinstance(rows, list):
                    raise FetchError('贡献者数据不可读')
                for account in rows:
                    if is_human(account):
                        people[account['id']] = {'id':account['id'], 'login':account['login']}
                if len(rows) < 100:
                    break
                truncated = page == settings['contributor_pages']
            except FetchError as exc:
                error = str(exc)
                result['errors'].append(f"{repo['repo']}: {error}")
                break
        repo['contributors'] = list(people.values())
        repo['contributors_complete'] = error is None and not truncated
        repo['contributor_error'] = error
        repo['contributor_truncated'] = truncated
        # Full-repository contributors to monorepos are explicitly excluded from the author metric.
        path_ambiguous = any(a['path'] for a in repo['artifacts'])
        repo['path_ambiguous'] = path_ambiguous
        if error is None and not path_ambiguous:
            accounts.update(people)
            observed.append(repo)
    result['contributor_ids'] = sorted(accounts)
    result['contributor_accounts'] = list(accounts.values())
    result['contributor_repos_requested'] = len(selected)
    result['contributor_repos_observed'] = len(observed)
    result['contributor_plugin_count'] = sum(len(r['artifacts']) for r in observed)
    result['contributor_count'] = len(accounts) if observed else None
    result['publisher_count'] = len(result['publisher_ids'])
    result['identity_note'] = 'User类型且非[bot]账号；不等于已验证自然人。累计全仓提交者，可能含文档贡献；monorepo路径不明者不纳入主计数。'
    return result


def openrouter_window(client, products, config, start, end):
    output = {'status':'missing_key', 'start':str(start), 'end':str(end), 'products':{}, 'pages':[], 'errors':[]}
    key = os.environ.get('OPENROUTER_API_KEY')
    if not key:
        return output
    rows = []
    try:
        # Documented offset is bounded at 100. This is a ranked slice, not a census.
        for offset in (0,100):
            url = 'https://openrouter.ai/api/v1/datasets/app-rankings?' + urlencode(
                {'sort':'popular', 'start_date':str(start), 'end_date':str(end), 'limit':100, 'offset':offset})
            payload = client.json(url, token=key)
            meta = payload.get('meta', {})
            if meta.get('start_date') != str(start) or meta.get('end_date') != str(end):
                raise FetchError('OpenRouter 实际日期窗口与请求不一致')
            if not isinstance(payload.get('data'), list):
                raise FetchError('OpenRouter 缺少 data')
            output['pages'].append({'source':url, 'meta':meta})
            rows.extend(payload['data'])
            if len(payload['data']) <100:
                break
        unique = {str(r['app_id']):r for r in rows if r.get('app_id') is not None}
        for product in products:
            fixed = config.get('app_ids', {}).get(product['id'])
            matches = [r for r in unique.values() if (str(r['app_id']) == str(fixed) if fixed is not None else
                       r.get('app_name', '').casefold() in {n.casefold() for n in product['app_names']})]
            if len(matches) != 1:
                output['products'][product['id']] = {'status':'ambiguous' if matches else 'not_visible', 'tokens':None, 'requests':None}
                continue
            row = matches[0]
            tokens = int(row['total_tokens'])
            if tokens < 0:
                raise FetchError('OpenRouter Token 值无效')
            output['products'][product['id']] = {'status':'ok','tokens':tokens,'requests':row.get('total_requests'),
                                                 'app_id':row['app_id'],'app_name':row['app_name']}
        output['status'] = 'ok' if all(r['status']=='ok' for r in output['products'].values()) else 'partial'
        output['slice_total_tokens'] = sum(int(r['total_tokens']) for r in unique.values())
        output['ranked_apps_count'] = len(unique)
        output['top_apps'] = [dict(r, total_tokens=int(r['total_tokens'])) for r in
                              sorted(unique.values(),key=lambda r:int(r['total_tokens']),reverse=True)[:10]]
    except (FetchError, KeyError, TypeError, ValueError) as exc:
        output['status'] = 'error'
        output['errors'].append(str(exc) if isinstance(exc, FetchError) else 'OpenRouter 响应结构不符合预期')
        output['products'] = {}
    return output
