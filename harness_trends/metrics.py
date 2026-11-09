from __future__ import annotations

from .changelog import summarize

# Briefing order for the shared summary table, shared by the HTML and Markdown reports.
SUMMARY_ORDER = ['claude', 'codex', 'pi', 'dsh']


def ratio_delta(current, previous):
    if current is None or previous is None or previous <= 0:
        return None
    return current / previous - 1


def package_total(rows):
    return sum(r['total'] for r in rows) if rows and all(r['status']=='ok' for r in rows) else None


def cn_number(value):
    """Chinese magnitude formatting without importing the HTML renderer."""
    if value is None:
        return None
    if abs(value) >= 1e8:
        return f'{value / 1e8:,.2f}亿'
    if abs(value) >= 1e4:
        return f'{value / 1e4:,.0f}万'
    return f'{value:,.0f}'


def user_disclosure_rows(run, config):
    """User-scale public disclosures, combined and single-product figures kept apart.
    Mirrors the HTML report's「用户规模公开信息」panel."""
    registered = run.get('user_disclosures', config.get('user_disclosures', []))
    primary = next((r for r in registered if r.get('id') == 'codex-work-40m-primary'), None)
    policy = (config.get('user_population_policy') or {}).get('codex', {})
    disclosure = config.get('disclosure') or {}
    spec = (config.get('models_v2') or {}).get('codex', {})
    rows = []
    if primary:
        rows.append({'scope':policy.get('label', primary.get('label', 'Codex')),
                     'metric':'WAU / 周活' if primary.get('period') == 'WAU' else '活跃用户（窗口未明确）',
                     'value':primary['value'], 'display':cn_number(primary['value']),
                     'as_of':primary.get('as_of'), 'note':'合计口径 · 只计一次；活跃窗口未明示'})
    if spec.get('wau_anchor'):
        rows.append({'scope':'Codex（历史单品数据）', 'metric':'历史WAU / 周活',
                     'value':spec['wau_anchor'], 'display':'超过' + cn_number(spec['wau_anchor']),
                     'as_of':spec.get('as_of'), 'note':'不是当前人数'})
    if disclosure.get('dau'):
        rows.append({'scope':'DSH', 'metric':'DAU / 日活', 'value':disclosure['dau'],
                     'display':cn_number(disclosure['dau']),
                     'as_of':disclosure.get('as_of'), 'note':'官方API用户范围'})
        rows.append({'scope':'DSH', 'metric':'MAU / 月活', 'value':disclosure['mau'],
                     'display':cn_number(disclosure['mau']),
                     'as_of':disclosure.get('as_of'), 'note':'月窗口未明示'})
    return rows


def user_cell(run, config, pid):
    """Summary-table lines for active users; disclosures only, each figure keeps its own scope.
    Returns a list of plain-text lines (no markup), or None when nothing is disclosed."""
    if pid == 'codex':
        rows = user_disclosure_rows(run, config)
        texts = []
        combined = next((r for r in rows if 'Codex' in r['scope'] and '历史' not in r['scope']), None)
        history = next((r for r in rows if '历史' in r['scope']), None)
        if combined:
            texts.append(f'{combined["display"]}+（{combined["scope"]}，{combined["as_of"]}）')
        if history:
            texts.append(f'单品历史：{history["display"]}WAU（{history["as_of"]}）')
        return texts or None
    if pid == 'dsh':
        disclosure = config.get('disclosure') or {}
        if disclosure.get('mau'):
            return [f'{cn_number(disclosure["mau"])}MAU / {cn_number(disclosure["dau"])}DAU（官方披露，{disclosure["as_of"]}）']
    return None


def summary_rows(run):
    """One raw-value row per harness for the shared summary table; renderers format their own cells."""
    views = (run.get('editorial') or {}).get('products', {})
    rows = []
    for pid in SUMMARY_ORDER:
        product = run['products'].get(pid)
        if product is None:
            continue
        current = run['openrouter_current'].get('products', {}).get(pid, {})
        previous = run['openrouter_previous'].get('products', {}).get(pid, {})
        repo = (run.get('official_repos') or {}).get(pid, {})
        plugins = None
        if pid == 'pi':
            plugins = (run.get('model_v2_inputs') or {}).get('pi_catalog', {}).get('total')
        else:
            plugins = (run.get('marketplaces') or {}).get(pid, {}).get('count')
        view = views.get(pid, {})
        rows.append({'pid':pid, 'name':product['name'],
                     'tokens':current.get('tokens'), 'share':current.get('share_four'),
                     'token_wow':ratio_delta(current.get('tokens'), previous.get('tokens')),
                     'downloads':product.get('downloads_current'), 'download_wow':product.get('download_wow'),
                     'contributors':repo.get('contributors'), 'repo':repo.get('repo'),
                     'plugins':plugins,
                     'action':view.get('action')})
    return rows


def feature_highlights(run, pid, limit=5, width=66):
    """Lines for the「本周新功能」column: scripted release highlights, newest version first.
    Each line is '<version>：<highlight>', truncated to keep the summary table compact."""
    update = (run.get('product_updates') or {}).get(pid, {})
    lines = []
    for item in summarize(update):
        for bullet in item['highlights']:
            text = bullet if len(bullet) <= width else bullet[:width] + '…'
            lines.append(f'{item["version"]}：{text}')
            if len(lines) >= limit:
                return lines
    return lines


def scale_summary(product, reference_alpha=1.0):
    """Conditional ranges, not confidence intervals or verified population counts."""
    result={}
    for name,key in [('users','mau'),('developers','value'),('plugins','plugins')]:
        scenarios=product.get('b_scenarios',[])
        values=[s[key] for s in scenarios if s.get(key) is not None]
        mid=next((s.get(key) for s in scenarios if s['alpha']==reference_alpha),None)
        result[name]={'reference':mid,'low':min(values) if values else None,'high':max(values) if values else None}
    gh=product['github']
    result['a_plugins']=(gh['candidate_total']*gh['verified_artifacts']/gh['checked_repos']
                         if gh.get('candidate_total') is not None and gh.get('verified_artifacts') is not None and gh.get('checked_repos') else None)
    result['a_developers']=product.get('a_candidate_projection')
    return result


def compute(run, config):
    products = run['products']
    anchor = products['dsh']
    anchor_npm = package_total(anchor['npm_anchor'])
    # Calibration is a fixed historical run; its sample is not silently replaced every week.
    calibration = run['calibration']
    d = config['disclosure']
    # Withdraw population estimates: cumulative repository contributors do not
    # identify plugin creators, and a union of identities cannot scale linearly.
    anchor_authors = None
    estimates = {}
    for pid, p in products.items():
        current, previous = package_total(p['npm_current']), package_total(p['npm_previous'])
        p['downloads_current'], p['downloads_previous'] = current, previous
        p['download_wow'] = ratio_delta(current, previous)
        gh = p['github']
        observed = gh.get('contributor_count')
        n = gh.get('contributor_plugin_count', 0)
        # A extrapolation is explicitly conditional on unverified candidates and representativeness.
        checked = gh.get('checked_repos', 0)
        candidate = gh.get('candidate_total')
        # Scale unique sampled accounts by candidate/checked; not an unbiased union estimator.
        contributing_repos = gh.get('contributor_repos_observed', 0)
        verified = gh.get('verified_repos', 0)
        a = (observed / contributing_repos * verified / checked * candidate
             if observed is not None and contributing_repos and checked and candidate is not None else None)
        p['a_candidate_projection_diagnostic'] = a
        p['a_candidate_projection'] = None
        p['developer_estimate_status'] = 'withdrawn_unvalidated_contributor_extrapolation'
        p['a_observed'] = observed
        p['b_scenarios'] = []
        for alpha in config['estimation']['alpha_scenarios']:
            factor = (current / anchor_npm) ** alpha if current is not None and anchor_npm else None
            value = anchor_authors * factor if anchor_authors is not None and factor is not None else None
            p['b_scenarios'].append({'alpha':alpha, 'value':value,
                'mau':d['mau']*factor if factor is not None else None,
                'plugins':d['plugins_union']*factor if factor is not None else None})
        b = next((s['value'] for s in p['b_scenarios'] if s['alpha']==config['estimation']['reference_alpha']), None)
        p['b_reference'] = b
        # A is a GitHub-scope projection; B is a cross-channel projection. No fake relative-error number.
        p['b_a_scale_ratio'] = b/a if a and b is not None else None
        p['a_coverage'] = checked/candidate if candidate else None
        p['accounts_per_plugin'] = observed/n if observed is not None and n else None
        p['scale_estimates']=scale_summary(p,config['estimation']['reference_alpha'])
        estimates[pid] = (None,b)
    a0,b0 = estimates.get('dsh', (None,None))
    for pid,p in products.items():
        a,b = estimates[pid]
        p['a_index'] = a/a0*100 if a is not None and a0 else None
        p['b_index'] = b/b0*100 if b is not None and b0 else None
        p['index_gap'] = p['b_index']-p['a_index'] if p['a_index'] is not None and p['b_index'] is not None else None
    for window in ('openrouter_current','openrouter_previous'):
        data=run[window]
        complete = data['status']=='ok' and len(data['products'])==len(products)
        denom = sum(r['tokens'] for r in data['products'].values()) if complete else None
        for pid in products:
            row=data['products'].get(pid, {})
            row['share_four'] = row.get('tokens')/denom if denom else None
            data['products'][pid]=row
    return run
