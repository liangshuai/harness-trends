"""Markdown weekly report: summary table first, then a digest of the HTML report's metrics."""
from .executive import NAMES, number
from .metrics import (SUMMARY_ORDER, feature_lines, load_app_types, official_disclosure_groups,
                      ratio_delta, summary_rows, top10_changes)


def cell(text):
    """Keep editorial and scripted text from breaking out of a Markdown table cell."""
    return ' '.join(str(text).replace('|', '\\|').split())


def _percent(value):
    return f'{value:+.1%}' if value is not None else '—'


def _arrow(value):
    """Week-over-week as a compact bolded ↑/↓ marker, e.g. （**↑22.1%**）."""
    if value is None:
        return ''
    return f'（**↑{value:.1%}**）' if value >= 0 else f'（**↓{abs(value):.1%}**）'


def _token_cell(row):
    if row['tokens'] is None:
        return '—'
    return number(row['tokens']) + _arrow(row['token_wow'])


def _share_cell(row):
    """Market share of the whole OpenRouter ranked slice, not of the four harnesses."""
    return f'{row["share_market"]:.1%}' if row['share_market'] is not None else '—'


def _downloads_cell(row):
    if row['downloads'] is None:
        return '—'
    return number(row['downloads']) + _arrow(row['download_wow'])


def _contributors_cell(row):
    if row['contributors'] is None:
        return '—'
    return f'{row["contributors"]:,}'


def _plugins_cell(row):
    if row['plugins'] is None:
        return '—'
    return f'{row["plugins"]:,}'


def _features_cell(run, pid):
    """本周新功能 column: editorial summaries first, scripted highlights as fallback."""
    highlights = feature_lines(run, pid)
    if not highlights:
        return '—'
    return '<br>'.join(cell(f'{index}）{item}') for index, item in enumerate(highlights, 1))


def _insight_cell(row):
    """洞察和行动 column: labelled 洞察 numbered lines, then the editorial 行动
    (what this week's features inspire for an enterprise agent foundation to borrow)."""
    parts = []
    value = row['insight']
    if isinstance(value, list) and value:
        parts.append('洞察：<br>' + '<br>'.join(cell(f'{index}）{item}') for index, item in enumerate(value, 1)))
    action = row.get('action')
    if isinstance(action, list) and action:
        action_text = '；'.join(cell(item) for item in action)
    elif action:
        action_text = cell(action)
    else:
        action_text = None
    if action_text:
        parts.append('行动：<br>' + action_text)
    return '<br>'.join(parts) if parts else '—'


def summary_table(run, editorial, config):
    header = ['Harness', '周 Token 使用量（万亿）', 'OpenRouter市场份额', '周下载量', '开源贡献者', '插件数量', '本周新功能', '洞察和行动']
    lines = ['| ' + ' | '.join(header) + ' |', '|' + '|'.join(['---'] * len(header)) + '|']
    for row in summary_rows(run):
        lines.append('| ' + ' | '.join([
            cell(row['name']), _token_cell(row), _share_cell(row), _downloads_cell(row), _contributors_cell(row),
            _plugins_cell(row),
            _features_cell(run, row['pid']),
            _insight_cell(row)]) + ' |')
    return '\n'.join(lines)


def official_disclosure_block(run, config):
    """官方披露 under the summary table, grouped per harness in plain bullets (no table)."""
    groups = official_disclosure_groups(run, config)
    if not groups:
        return []
    lines = ['**官方披露**', '']
    for group in groups:
        lines.append(f'- **{cell(group["name"])}**：' + '；'.join(cell(item) for item in group['items']))
    return lines


def _app_label(app, types):
    info = types.get(str(app.get('app_id'))) or {}
    kind = info.get('type') or '未标注'
    return (f'{kind}：{info["note"]}' if info.get('note') else kind), info


def top10_section(run):
    """OpenRouter Top 10 movement: new entrants with positioning, the fastest grower, dropouts."""
    changes = top10_changes(run)
    if not changes['newcomers'] and changes['grower'] is None and not changes['dropouts']:
        return []
    types = load_app_types()
    lines = ['## 三、OpenRouter Top 10 动向', '']
    if changes['newcomers']:
        for app in changes['newcomers']:
            label, info = _app_label(app, types)
            lines.append(cell(f'- **新进入 Top 10**：{app["app_name"]}（第{app.get("rank") or "?"}名 · '
                              f'周 Token {number(app.get("total_tokens"))}）——{label}'))
            if info.get('fit'):
                lines.append(f'  - 集成视角：{cell(info["fit"])}')
    else:
        lines.append('- 本周 Top 10 无新增应用。')
    grower, wow = changes['grower'], changes['grower_wow']
    if grower is not None and wow is not None:
        label, _ = _app_label(grower, types)
        wow_text = f'↑{wow:.1%}' if wow >= 0 else f'↓{abs(wow):.1%}'
        lines.append(cell(f'- **本周增长最多**：{grower["app_name"]}（第{grower.get("rank") or "?"}名 · '
                          f'周 Token {number(grower.get("total_tokens"))}，环比{wow_text}）——{label}'))
    for app in changes['dropouts']:
        lines.append(cell(f'- **退出 Top 10**：{app["app_name"]}（上期第{app.get("rank") or "?"}名）'))
    lines.append('')
    return lines


def metrics_digest(run, config):
    """Markdown mirror of the HTML report's core metric sections."""
    products = run['products']
    cur = run['openrouter_current']
    ordered = sorted(products, key=lambda p: cur.get('products', {}).get(p, {}).get('tokens') or -1, reverse=True)
    complete = cur['status'] == 'ok' and all(cur.get('products', {}).get(p, {}).get('tokens') is not None for p in products)
    total = sum(cur['products'][p]['tokens'] for p in products) if complete else None
    prev = run['openrouter_previous']
    oldtotal = sum(prev['products'][p]['tokens'] for p in products) if all(prev.get('products', {}).get(p, {}).get('tokens') is not None for p in products) else None
    lines = ['## 二、Token使用情况（行业）', '']
    kpi = []
    if total is not None:
        text = f'四家周Token总量 {number(total)}'
        if ratio_delta(total, oldtotal) is not None:
            text += f'（环比{_percent(ratio_delta(total, oldtotal))}）'
        kpi.append(text)
    requests = sum(cur['products'][p].get('requests') for p in products) if complete and all(cur['products'][p].get('requests') is not None for p in products) else None
    if requests is not None:
        kpi.append(f'周请求总量 {number(requests)}')
    if complete and total:
        kpi.append(f'份额第一 {NAMES[ordered[0]]} {cur["products"][ordered[0]]["tokens"] / total:.1%}')
    growths = {p: ratio_delta(cur.get('products', {}).get(p, {}).get('tokens'), prev.get('products', {}).get(p, {}).get('tokens')) for p in products}
    valid = {p: v for p, v in growths.items() if v is not None}
    if valid:
        fastest = max(valid, key=valid.get)
        kpi.append(f'Token环比变化最大 {NAMES[fastest]} {_percent(valid[fastest])}')
    if kpi:
        lines += ['- ' + '；'.join(kpi), '']
    lines += ['### 模型使用量及占比', '',
              '| Harness | 周 Token 使用量 | 样本内 Token 占比 | Token 使用量周环比 | 占比周变化（百分点） | 周模型请求量 |',
              '|---|---|---|---|---|---|']
    for pid in ordered:
        row = cur.get('products', {}).get(pid, {})
        old = prev.get('products', {}).get(pid, {})
        share, old_share = row.get('share_four'), old.get('share_four')
        pp = f'{(share - old_share) * 100:+.1f}' if share is not None and old_share is not None else '—'
        share_text = f'{share:.1%}' if share is not None else '—'
        lines.append(f'| {NAMES[pid]} | {number(row.get("tokens"))} | {share_text} | '
                     f'{_percent(growths[pid])} | {pp} | {number(row.get("requests"))} |')
    lines.append('')
    windows = run.get('openrouter_trend', [])
    if windows:
        lines += ['### 近四周 Token 使用量趋势（连续七天窗口，Token）', '',
                  '| Harness | ' + ' | '.join(w['end'][5:] for w in windows) + ' |',
                  '|' + '---|' * (len(windows) + 1)]
        for pid in SUMMARY_ORDER:
            if pid not in products:
                continue
            cells = [NAMES[pid]] + [number(w.get('products', {}).get(pid, {}).get('tokens')) for w in windows]
            lines.append('| ' + ' | '.join(cells) + ' |')
        lines.append('')
    return lines


def render_markdown(run, config):
    start, end = run['window']['start'], run['window']['end']
    editorial = run.get('editorial')
    lines = ['# AI Harness 市场观察周报', '']
    lines.append(f'数据窗口：{start} — {end}')
    detail_url = (config.get('report') or {}).get('detail_url')
    if detail_url:
        lines.append(f'详细报告：{detail_url}')
    lines.append('')
    lines.append('## 一、主流Harness汇总表')
    lines.append('')
    lines.append(summary_table(run, editorial, config))
    lines.append('')
    lines += official_disclosure_block(run, config)
    if editorial:
        takeaways = editorial.get('takeaways') or []
        if takeaways:
            lines += ['', '**行动：本周最值得深入研究或借鉴**', '']
            lines += [f'{index}. {cell(item)}' for index, item in enumerate(takeaways, 1)]
    else:
        lines += ['', '> 本轮无编辑笔记：本周新功能列为脚本提取的官方发布原文摘录，洞察与结尾总结待补；数字均由脚本采集。']
    lines += ['', *metrics_digest(run, config)]
    lines += top10_section(run)
    lines.append('## 四、口径与来源')
    lines.append('')
    lines.append(f'- **周 Token 使用量**：OpenRouter app-rankings 数据集，canonical app ID，窗口 {start} — {end}；'
                 '只含OpenRouter可归因渠道，不代表全市场用量。Source: OpenRouter (openrouter.ai/apps), CC BY 4.0.')
    ranked = (run.get('openrouter_current') or {}).get('ranked_apps_count')
    share_note = '- **OpenRouter市场份额**：该应用周Token ÷ 榜单全部应用周Token合计，非四家内部占比。'
    if ranked:
        share_note = share_note[:-1] + f'（本轮已取得 {ranked} 个应用）。'
    lines.append(share_note)
    lines.append('- **周下载量**：npm downloads API 逐日加总的主包七天下载，含更新、CI 与重复下载，不等于活跃用户。')
    lines.append('- **开源贡献者**：官方公开仓库的 GitHub contributors 数量（非匿名账号，与官网UI同口径）；'
                 '仅统计公开官方仓库，闭源/内部镜像开发不计入。')
    lines.append('- **插件数量**：来自各产品对应插件市场的公开计数，口径互不相同。')
    return '\n'.join(lines).rstrip() + '\n'
