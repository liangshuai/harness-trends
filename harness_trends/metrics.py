from __future__ import annotations


def ratio_delta(current, previous):
    if current is None or previous is None or previous <= 0:
        return None
    return current / previous - 1


def package_total(rows):
    return sum(r['total'] for r in rows) if rows and all(r['status']=='ok' for r in rows) else None


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
