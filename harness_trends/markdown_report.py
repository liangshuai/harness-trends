"""Markdown weekly report: summary table first, then a digest of the HTML report's metrics."""
from datetime import datetime
from zoneinfo import ZoneInfo

from .executive import NAMES, number
from .metrics import SUMMARY_ORDER, default_insight, ratio_delta, summary_rows


def cell(text):
    """Keep editorial and scripted text from breaking out of a Markdown table cell."""
    return ' '.join(str(text).replace('|', '\\|').split())


def _percent(value):
    return f'{value:+.1%}' if value is not None else '—'


def _token_cell(row):
    if row['tokens'] is None:
        return '—'
    text = number(row['tokens'])
    if row['share'] is not None:
        text += f'（份额{row["share"]:.1%}）'
    if row['token_wow'] is not None:
        text += f'，环比{_percent(row["token_wow"])}'
    return text


def _downloads_cell(row):
    if row['downloads'] is None:
        return '—'
    text = number(row['downloads'])
    if row['download_wow'] is not None:
        text += f'（环比{_percent(row["download_wow"])}）'
    return text


def _contributors_cell(row):
    if row['contributors'] is None:
        return '—'
    return f'{row["contributors"]:,}（{row.get("repo") or ""}）'


def _plugins_cell(row):
    if row['plugins'] is None:
        return '—'
    return f'{row["plugins"]:,}（{row["plugin_source"]}）'


def _insight_cell(run, row):
    """Editorial insights are itemized: one numbered point per line, never merged into a paragraph."""
    value = row['insight']
    if isinstance(value, list) and value:
        return '<br>'.join(cell(f'{index}）{item}') for index, item in enumerate(value, 1))
    return cell(value or default_insight(run, row['pid']))


def summary_table(run, editorial):
    header = ['Harness', '周Token（OpenRouter）', '周下载量', '开源贡献者', '插件数量', '洞察（本周新功能）', '行动']
    lines = ['| ' + ' | '.join(header) + ' |', '|' + '|'.join(['---'] * len(header)) + '|']
    for row in summary_rows(run):
        lines.append('| ' + ' | '.join([
            cell(row['name']), _token_cell(row), _downloads_cell(row), _contributors_cell(row),
            _plugins_cell(row),
            _insight_cell(run, row),
            cell(row['action'] or '—')]) + ' |')
    return '\n'.join(lines)


def metrics_digest(run, config):
    """Markdown mirror of the HTML report's core metric sections."""
    products = run['products']
    cur = run['openrouter_current']
    ordered = sorted(products, key=lambda p: cur.get('products', {}).get(p, {}).get('tokens') or -1, reverse=True)
    complete = cur['status'] == 'ok' and all(cur.get('products', {}).get(p, {}).get('tokens') is not None for p in products)
    total = sum(cur['products'][p]['tokens'] for p in products) if complete else None
    prev = run['openrouter_previous']
    oldtotal = sum(prev['products'][p]['tokens'] for p in products) if all(prev.get('products', {}).get(p, {}).get('tokens') is not None for p in products) else None
    lines = ['## 二、用量与生态指标汇总', '']
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
    lines += ['### 用量与份额（OpenRouter · 周Token）', '',
              '| Harness | 本周Token | 四家内部份额 | Token环比 | 份额周变化 | 本周请求 |',
              '|---|---|---|---|---|---|']
    for pid in ordered:
        row = cur.get('products', {}).get(pid, {})
        old = prev.get('products', {}).get(pid, {})
        share, old_share = row.get('share_four'), old.get('share_four')
        pp = f'{(share - old_share) * 100:+.1f} pp' if share is not None and old_share is not None else '—'
        share_text = f'{share:.1%}' if share is not None else '—'
        lines.append(f'| {NAMES[pid]} | {number(row.get("tokens"))} | {share_text} | '
                     f'{_percent(growths[pid])} | {pp} | {number(row.get("requests"))} |')
    lines.append('')
    windows = run.get('openrouter_trend', [])
    if windows:
        lines += ['### 四周Token趋势（连续七天窗口，Token）', '',
                  '| Harness | ' + ' | '.join(w['end'][5:] for w in windows) + ' |',
                  '|' + '---|' * (len(windows) + 1)]
        for pid in SUMMARY_ORDER:
            if pid not in products:
                continue
            cells = [NAMES[pid]] + [number(w.get('products', {}).get(pid, {}).get('tokens')) for w in windows]
            lines.append('| ' + ' | '.join(cells) + ' |')
        lines.append('')
    lines += ['### DSH 官方披露', '']
    disclosure = config['disclosure']
    lines += [f'截至 {disclosure["as_of"]}（媒体转述厂商披露，不同于OpenRouter渠道数据）：'
              f'日活 {number(disclosure["dau"])}；月活 {number(disclosure["mau"])}；'
              f'单日Token {number(disclosure["tokens_daily"])}；公开第三方插件 {number(disclosure["plugins_union"])}（已去重）。', '']
    return lines


def render_markdown(run, config):
    generated = datetime.fromisoformat(run['generated_at']).astimezone(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M')
    start, end = run['window']['start'], run['window']['end']
    editorial = run.get('editorial')
    lines = ['# AI Agent Harness 市场观察周报', '']
    lines.append(f'数据窗口：{start} — {end}（UTC）· 生成于 {generated}（北京时间）')
    lines.append('')
    lines.append('## 一、四家汇总表')
    lines.append('')
    lines.append(summary_table(run, editorial))
    lines.append('')
    if editorial:
        lines.append('> 洞察面向本周新增功能点，行动为跟进建议，均为编辑观点；数字均由脚本按当轮快照采集，不手工填写。')
    else:
        lines.append('> 本轮无编辑笔记：洞察列降级为脚本提取的窗口内发布要点，行动列待补；数字均由脚本采集。')
    lines += ['', *metrics_digest(run, config)]
    lines.append('## 三、口径与来源')
    lines.append('')
    lines.append(f'- **周Token**：OpenRouter app-rankings 数据集，canonical app ID，窗口 {start} — {end}；'
                 '只含OpenRouter可归因渠道，不代表全市场用量。Source: OpenRouter (openrouter.ai/apps), CC BY 4.0.')
    lines.append('- **周下载量**：npm downloads API 逐日加总的主包七天下载，含更新、CI 与重复下载，不等于活跃用户。')
    lines.append('- **开源贡献者**：官方公开仓库的 GitHub contributors（非匿名账号，与官网UI同口径）；'
                 '仅统计公开官方仓库，闭源/内部镜像开发不计入，厂商间口径差异见各行仓库名。')
    lines.append('- **插件数量**：Claude Code 取 claude.com/marketplace/plugins 页面公布总数；Codex 取 mcptop.com 所示 ChatGPT 插件目录'
                 ' Plugins 分类计数（该目录另有全量口径，见下注）；Pi 取 pi.dev 官方 Package Catalog 未筛选总数'
                 '（含 extension/skill/theme/prompt 等类型，非纯 extension）；DSH 取 dshmarket.com 公布的社区插件总数。'
                 '四者口径互不相同，不可直接横向排名。')
    lines.append('- **洞察/行动**：面向本周新增功能点的编辑解读与建议，不属于采集数据；无编辑笔记的周次自动降级为脚本提取的发布要点摘要。')
    mcptop = run.get('marketplaces', {}).get('codex', {})
    if mcptop.get('directory_total') is not None and mcptop.get('count') is not None:
        note = f'- 注：ChatGPT 插件目录全量 {mcptop["directory_total"]:,} 个，本表取 Plugins 分类计数 {mcptop["count"]:,}'
        if mcptop.get('observed_at'):
            note += f'（mcptop.com，{mcptop["observed_at"][:10]}观测）'
        lines.append(note + '。')
    lines.append('')
    lines.append('各项指标的逐项采集状态与原始来源详见配套完整报告的数据附录。')
    return '\n'.join(lines) + '\n'
