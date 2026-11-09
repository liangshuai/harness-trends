"""Markdown weekly report: summary table first, scripted evidence, editorial views kept separate."""
from datetime import datetime
from zoneinfo import ZoneInfo

from .changelog import summarize
from .executive import NAMES, number

# Row order follows the requested briefing order, not token ranking.
ROW_ORDER = ['claude', 'codex', 'pi', 'dsh']
PLUGIN_SOURCE = {'claude':'Claude官方Marketplace', 'codex':'ChatGPT插件目录（mcptop.com）',
                 'pi':'pi.dev官方Package Catalog', 'dsh':'dshmarket.com'}


def cell(text):
    """Keep editorial and scripted text from breaking out of a Markdown table cell."""
    return ' '.join(str(text).replace('|', '\\|').split())


def _wow(current, previous):
    if current is None or previous is None or previous <= 0:
        return None
    return current / previous - 1


def _token_cell(run, pid):
    row = run['openrouter_current'].get('products', {}).get(pid, {})
    prev = run['openrouter_previous'].get('products', {}).get(pid, {})
    tokens, share = row.get('tokens'), row.get('share_four')
    if tokens is None:
        return '—'
    text = number(tokens)
    if share is not None:
        text += f'（份额{share:.1%}）'
    wow = _wow(tokens, prev.get('tokens'))
    if wow is not None:
        text += f'，环比{wow:+.1%}'
    return text


def _downloads_cell(product):
    current, previous = product.get('downloads_current'), product.get('downloads_previous')
    if current is None:
        return '—'
    text = number(current)
    wow = _wow(current, previous)
    if wow is not None:
        text += f'（环比{wow:+.1%}）'
    return text


def _plugins_cell(run, pid):
    if pid == 'pi':
        catalog = run.get('model_v2_inputs', {}).get('pi_catalog', {})
        count = catalog.get('total')
    else:
        count = run.get('marketplaces', {}).get(pid, {}).get('count')
    if count is None:
        return '—'
    return f'{count:,}（{PLUGIN_SOURCE[pid]}）'


def _contributors_cell(run, pid):
    row = run.get('official_repos', {}).get(pid, {})
    count = row.get('contributors')
    if count is None:
        return '—'
    return f'{count:,}（{row.get("repo", "")}）'


def _default_insight(run, pid):
    """Scripted fallback so the table stays complete in weeks without an editorial file.
    Insight is about the week's shipped features, so the fallback summarizes release
    highlights instead of volume metrics."""
    update = (run.get('product_updates') or {}).get(pid, {})
    releases = update.get('releases', [])
    highlights = []
    for item in summarize(update):
        highlights.extend(item['highlights'])
    if highlights:
        lead = highlights[0][:60] + ('…' if len(highlights[0]) > 60 else '')
        return f'窗口内{len(releases)}个发布，功能要点如：{lead}（脚本提取，无编辑点评）'
    if releases:
        return f'窗口内{len(releases)}个发布，发布说明为占位文本，无可提取要点（脚本提取，无编辑点评）'
    return '窗口内无发布，无新增功能可析（脚本提取，无编辑点评）'


def summary_table(run, editorial):
    header = ['Harness', '周Token（OpenRouter）', '周npm下载', '官方仓库Contributors', '插件数量', '洞察（本周新功能）', '行动']
    lines = ['| ' + ' | '.join(header) + ' |', '|' + '|'.join(['---'] * len(header)) + '|']
    views = (editorial or {}).get('products', {})
    for pid in ROW_ORDER:
        product = run['products'].get(pid)
        if product is None:
            continue
        view = views.get(pid, {})
        lines.append('| ' + ' | '.join([
            cell(product['name']), _token_cell(run, pid), _downloads_cell(product),
            _contributors_cell(run, pid), _plugins_cell(run, pid),
            cell(view.get('insight') or _default_insight(run, pid)),
            cell(view.get('action') or '—')]) + ' |')
    return '\n'.join(lines)


def _feature_section(run, pid, view):
    update = (run.get('product_updates') or {}).get(pid, {})
    product = run['products'][pid]
    releases = update.get('releases', [])
    versions = '、'.join(r['version'] or r['tag'] for r in releases) if releases else '窗口内无发布'
    lines = [f'### {product["name"]}']
    if update.get('status') == 'missing':
        reason = '；'.join(update.get('errors')) if update.get('errors') else '未知原因'
        lines.append(f'- 脚本采集失败：{reason}；本节仅剩编辑内容。')
    lines.append(f'- **窗口内发布**：{versions}（来源：GitHub Releases{" + CHANGELOG.md" if update.get("changelog") else ""}）')
    for item in summarize(update):
        if not item['highlights']:
            continue
        lines.append(f'- **{item["version"]}**（{item["published_at"][:10]}，{"预发布" if item["prerelease"] else "正式版"}，{item["basis"]}）要点：')
        lines.extend(f'  - {bullet}' for bullet in item['highlights'])
    if view.get('feature_summary'):
        lines.append(f'- **网络检索核实（编辑）**：{view["feature_summary"]}')
        for source in view.get('sources', []):
            lines.append(f'  - 来源：{source}')
    return '\n'.join(lines)


def render_markdown(run, config):
    generated = datetime.fromisoformat(run['generated_at']).astimezone(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M')
    start, end = run['window']['start'], run['window']['end']
    editorial = run.get('editorial')
    lines = ['# AI Agent Harness 市场观察周报 · Markdown 版', '']
    lines.append(f'数据窗口：{start} — {end}（UTC）· 生成于 {generated}（北京时间）· 方法版本 {run["method_version"]}')
    lines.append(f'HTML 版：`reports/latest.html`；结构化快照：`data/latest.json`。')
    lines.append('')
    lines.append('## 一、四家汇总表')
    lines.append('')
    lines.append(summary_table(run, editorial))
    lines.append('')
    if editorial:
        lines.append(f'> 洞察面向本周新增功能点，与行动均为编辑观点（`data/editorial/{editorial.get("window_end", end)}.json`，'
                     f'{editorial.get("prepared_at", "")[:10]}整理）；数字均由脚本按当轮快照采集，不手工填写。')
    else:
        lines.append('> 本轮无编辑笔记：洞察列降级为脚本提取的窗口内发布要点，行动列待补；数字均由脚本采集。')
    lines.append('')
    lines.append('## 二、本周新功能特性（脚本采集 CHANGELOG / Releases，网络检索交叉核实）')
    lines.append('')
    views = (editorial or {}).get('products', {})
    for pid in ROW_ORDER:
        if pid in run['products']:
            lines.append(_feature_section(run, pid, views.get(pid, {})))
            lines.append('')
    lines.append('## 三、口径与来源')
    lines.append('')
    lines.append(f'- **周Token**：OpenRouter app-rankings 数据集，canonical app ID，窗口 {start} — {end}；'
                 '只含OpenRouter可归因渠道，不代表全市场用量。Source: OpenRouter (openrouter.ai/apps), CC BY 4.0.')
    lines.append('- **周npm下载**：npm downloads API 逐日加总的主包七天下载，含更新、CI 与重复下载，不等于活跃用户。')
    lines.append('- **官方仓库Contributors**：GitHub REST contributors（非匿名账号，与官网UI同口径，Link头last页码精确计数）；'
                 '仅统计公开官方仓库，闭源/内部镜像开发不计入，厂商间口径差异见各行仓库名。')
    lines.append('- **插件数量**：Claude Code 取 claude.com/marketplace/plugins 页面公布总数；Codex 取 mcptop.com 所示 ChatGPT 插件目录'
                 ' Plugins 分类计数（该目录另有全量口径，见数据快照 directory_total）；Pi 取 pi.dev 官方 Package Catalog 未筛选总数'
                 '（含 extension/skill/theme/prompt 等类型，非纯 extension）；DSH 取 dshmarket.com 公布的社区插件总数。'
                 '四者口径互不相同，不可直接横向排名。')
    lines.append('- **新功能特性**：脚本按窗口提取官方 GitHub Releases 与 CHANGELOG.md 条目（原文引用，未翻译）；'
                 '「网络检索核实」为编辑内容，附来源链接，与脚本采集分开标注。')
    lines.append('- **洞察/行动**：面向本周新增功能点的编辑解读与建议，不属于采集数据；无编辑笔记的周次自动降级为脚本提取的发布要点摘要。')
    mcptop = run.get('marketplaces', {}).get('codex', {})
    if mcptop.get('directory_total') is not None and mcptop.get('count') is not None:
        note = f'- 注：ChatGPT 插件目录全量 {mcptop["directory_total"]:,} 个，本表按用户指定取 Plugins 分类计数 {mcptop["count"]:,}。'
        if mcptop.get('observed_at'):
            note += f'（mcptop.com 观测于 {mcptop["observed_at"][:10]}）'
        lines.append(note)
    lines.append('')
    lines.append(f'原始响应与逐项采集状态见 `data/raw/`、`data/runs/` 与 HTML 版附录数据清单。')
    return '\n'.join(lines) + '\n'
