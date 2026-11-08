from __future__ import annotations

import html
import json
from pathlib import Path


def esc(value):
    return html.escape(str(value), quote=True)


def num(value):
    if value is None:
        return '—'
    if abs(value) >= 1e12:
        return f'{value/1e12:,.2f}T'
    if abs(value) >= 1e9:
        return f'{value/1e9:,.2f}B'
    if abs(value) >= 1e6:
        return f'{value/1e6:,.2f}M'
    return f'{value:,.0f}'


def pct(value):
    return '—' if value is None else f'{value:+.1%}'


def table(headers, rows):
    return '<div class="table-scroll"><table><thead><tr>'+''.join(f'<th scope="col">{esc(x)}</th>' for x in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join(f'<td>{x}</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table></div>'


def chart(products, field, label, color):
    maximum=max([p.get(field) or 0 for p in products.values()]+[1])
    parts=[]
    for p in products.values():
        v=p.get(field)
        width=(v or 0)/maximum*100
        parts.append(f'<div class="bar-row"><div class="bar-label">{esc(p["name"])}</div><div class="bar-track"><div style="width:{width:.3f}%;background:{color}"></div></div><span>{num(v)}</span></div>')
    return f'<div class="chart" role="img" aria-label="{esc(label)}">'+''.join(parts)+'</div>'


def render(run, config):
    products=run['products']
    d=config['disclosure']
    arows=[]; brows=[]; nrows=[]; orows=[]; grows=[]; evidence=[]; weekly=[]
    for pid,p in products.items():
        g=p['github']
        arows.append([esc(p['name']),num(g.get('candidate_total')),num(g.get('checked_repos')),num(g.get('verified_artifacts')),
                      num(g.get('contributor_repos_observed')),num(p['a_observed']),num(g.get('publisher_count')),num(p['a_candidate_projection'])])
        vals=[x['value'] for x in p['b_scenarios'] if x['value'] is not None]
        mids=next((x for x in p['b_scenarios'] if x['alpha']==1.0),{})
        brows.append([esc(p['name']),num(p['b_reference']),f'{num(min(vals))}–{num(max(vals))}' if vals else '—',num(mids.get('plugins')),num(mids.get('mau'))])
        nrows.append([esc(p['name']),num(p['downloads_previous']),num(p['downloads_current']),pct(p['download_wow']),'<br>'.join(esc(r['package']) for r in p['npm_current'])])
        o=run['openrouter_current']['products'].get(pid, {})
        old=run['openrouter_previous']['products'].get(pid,{})
        wow=o.get('tokens')/old['tokens']-1 if o.get('tokens') is not None and old.get('tokens') else None
        orows.append([esc(p['name']),num(o.get('tokens')),num(o.get('requests')),f'{o["share_four"]:.1%}' if o.get('share_four') is not None else '—',pct(wow),esc(o.get('status','missing_key'))])
        grows.append([esc(p['name']),num(p['a_index']),num(p['b_index']),num(p['index_gap']),f'{p["b_a_scale_ratio"]:.2f}×' if p['b_a_scale_ratio'] is not None else '—'])
        for repo in g.get('repos',[]):
            if repo['status']=='verified':
                source='https://github.com/'+repo['repo']
                contributors=repo.get('contributors',[])
                state='未取贡献者' if 'contributors_complete' not in repo else ('全仓接口完成' if repo['contributors_complete'] else '截断或失败')
                if repo.get('path_ambiguous'): state+='；monorepo不纳入主计数'
                evidence.append([esc(p['name']),f'<a href="{esc(source)}" target="_blank" rel="noopener">{esc(repo["repo"])}</a>',
                                 '<br>'.join(esc(a['name']) for a in repo['artifacts']),str(len(contributors)),esc(state)])
        oldp=(run.get('previous_snapshot') or {}).get('products',{}).get(pid,{})
        oldg=oldp.get('github',{})
        current_ids=set(g.get('contributor_ids',[])); old_ids=set(oldg.get('contributor_ids',[]))
        comparable=(bool(oldp) and run.get('same_collection_config')
                    and not g.get('errors') and not oldg.get('errors')
                    and not any(r.get('contributor_truncated') for r in g.get('repos',[])+oldg.get('repos',[]))
                    and {r['repo'] for r in g.get('repos',[]) if r.get('contributors_complete')}=={r['repo'] for r in oldg.get('repos',[]) if r.get('contributors_complete')})
        weekly.append([esc(p['name']),num(oldp.get('a_observed')),num(p['a_observed']),
                       num(len(current_ids-old_ids)) if comparable else '不可比',num(len(old_ids-current_ids)) if comparable else '不可比',
                       '固定仓库样本变化；仍非全生态增长' if comparable else '无上周快照或抓取覆盖变化'])
    cal=run['calibration']
    available_ratios=[(p['b_a_scale_ratio'],p['name']) for p in products.values() if p['b_a_scale_ratio'] is not None]
    largest=max(available_ratios) if available_ratios else None
    disagreement=(f'本轮最大量级分歧出现在 {esc(largest[1])}：B约为A的 {largest[0]:,.1f} 倍。'
                  if largest else '本轮缺少可对照的数据，不计算路线量级比。')
    current=run['window']; prev=run['previous_window']
    errors=[]
    for p in products.values():
        for r in p['npm_current']+p['npm_previous']+p.get('npm_anchor',[]):
            if r['status']!='ok': errors.append(f'{p["name"]} / {r["package"]}：{r.get("reason")}')
        errors.extend(p['name']+' / '+x for x in p['github'].get('errors',[]))
    errors.extend(run['openrouter_current']['errors']+run['openrouter_previous']['errors'])
    for window in run.get('openrouter_trend',[]):
        errors.extend(f'历史窗口 {window["start"]}—{window["end"]}：{error}' for error in window.get('errors',[]))
    missing_or=run['openrouter_current']['status']=='missing_key'
    raw_data={k:v for k,v in run.items() if k not in ('previous_snapshot','requests')}
    embedded=json.dumps(raw_data,ensure_ascii=False).replace('<','\\u003c').replace('&','\\u0026')
    history=run.get('history',[])
    history_rows=[[esc(x['end']),esc(x['name']),num(x.get('downloads')),num(x.get('observed')),num(x.get('b_reference'))] for x in history]
    notice='OpenRouter 尚未配置 API key，本报告未使用页面 Today 数值补填。' if missing_or else 'OpenRouter 已按指定 UTC 窗口请求；缺失或重名条目留空，四家齐全时才计算样本份额。'
    html_doc='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Harness Observatory · 周度规模与趋势</title><style>
:root{--ink:#172924;--muted:#66756f;--paper:#f4f4ed;--green:#166b55;--line:#dce2d9;--amber:#99602b}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.7 -apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif}a{color:#166b55;text-underline-offset:3px}header{background:#173a30;color:white;padding:48px max(5vw,24px) 36px}header .eyebrow{letter-spacing:3px;font-size:12px;color:#b5d7bd}h1{font-size:clamp(30px,4vw,50px);line-height:1.18;margin:14px 0}header p{max-width:850px;color:#d1e0d7}header .meta{font-size:13px;color:#bdd0c4}nav{position:sticky;top:0;background:#f4f4edf5;backdrop-filter:blur(12px);padding:12px 5vw;display:flex;gap:20px;overflow:auto;border-bottom:1px solid var(--line);z-index:2}nav a{white-space:nowrap;text-decoration:none;font-size:13px}main{max-width:1260px;margin:auto;padding:32px 24px 60px}section{scroll-margin-top:75px;margin:36px 0}h2{font-size:26px;margin:0 0 8px;letter-spacing:-.5px}h3{font-size:17px}p{margin:10px 0}.sub{color:var(--muted);max-width:950px}.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.card,.panel{background:#fff;border:1px solid var(--line);border-radius:12px;padding:22px}.card .number{font-size:30px;font-weight:650;margin:10px 0}.card small{color:var(--muted)}.tag{font-size:11px;padding:3px 8px;background:#e7eee5;border-radius:20px;display:inline-block}.tag.estimate{background:#fff0d9;color:#87521b}.notice{padding:16px 20px;background:#fff5df;border-left:4px solid #c89646;border-radius:4px;margin:20px 0}.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}.table-scroll{overflow-x:auto;background:white;border:1px solid var(--line);border-radius:10px;margin:16px 0}table{border-collapse:collapse;width:100%;font-size:13px;white-space:nowrap}th,td{text-align:left;padding:13px 15px;border-bottom:1px solid #edf0e9;vertical-align:top}th{font-weight:600;background:#edf1e8;color:#4a6053}td:first-child{font-weight:600}tbody tr:last-child td{border:0}code{font-size:12px;background:#eaf0e6;border-radius:4px;padding:2px 5px;overflow-wrap:anywhere}.formula{background:#edf1e8;padding:16px;border-radius:8px;font:13px/1.8 ui-monospace,monospace;white-space:pre-wrap}.bar-row{display:grid;grid-template-columns:115px 1fr 65px;gap:12px;align-items:center;margin:17px 0;font-size:12px}.bar-track{height:15px;background:#ecf0e8;border-radius:4px;overflow:hidden}.bar-track>div{height:100%;border-radius:4px}.bar-row>span{text-align:right}.foot{font-size:12px;color:var(--muted);border-top:1px solid var(--line);padding-top:22px}details{background:white;border:1px solid var(--line);border-radius:8px;padding:16px;margin:14px 0}summary{cursor:pointer;font-weight:600}button{background:var(--green);color:white;border:0;padding:9px 15px;border-radius:6px;cursor:pointer}ul,ol{padding-left:22px}.muted{color:var(--muted)}@media(max-width:780px){.cards,.grid{grid-template-columns:1fr 1fr}.grid{grid-template-columns:1fr}main{padding:22px 16px}header{padding:32px 22px}.card{padding:16px}.card .number{font-size:24px}.bar-row{grid-template-columns:95px 1fr 65px}}@media print{nav,button{display:none}body{background:white}header{color:#172924;background:#edf1e8}header p,header .meta{color:#476151}.table-scroll{overflow:visible}table{white-space:normal}.panel,.card,table{break-inside:avoid}details{display:block}section{break-before:auto}}
</style></head><body>'''
    html_doc+=f'''<header><div class="eyebrow">HARNESS OBSERVATORY / WEEKLY RESEARCH</div><h1>四个 Harness，<br>两条规模观测路线。</h1><p>Codex · Claude Code · DeepSeek Harness · Pi<br>把公开采集与条件外推放在同一份报告中，保留差异，也保留不知道的部分。</p><div class="meta">UTC 窗口 {esc(current['start'])} — {esc(current['end'])} · 生成 {esc(run['generated_at'])} · 方法 {esc(run['method_version'])}</div></header>
<nav><a href="#overview">概览</a><a href="#route-a">A · 公开采集</a><a href="#route-b">B · 情景外推</a><a href="#compare">偏差对照</a><a href="#tokens">OpenRouter</a><a href="#weekly">周度变化</a><a href="#method">方法与来源</a></nav><main>
<section id="overview"><h2>先看证据，再看估算</h2><p class="sub">本轮是受预算限制的 manifest 验证与贡献者样本采集；A 的全量外推和 B 的人数均为强假设情景，不能作为真实用户数或市场人口普查。</p><div class="notice">{esc(notice)}</div><div class="cards">'''
    for p in products.values():
        html_doc+=f'<div class="card"><span class="tag">A · 样本观测</span><h3>{esc(p["name"])}</h3><div class="number">{num(p["a_observed"])}</div><small>去重公开参与账号<br>{num(p["github"].get("verified_artifacts"))} 个已验证发布单元 / {num(p["github"].get("contributor_repos_observed"))} 个贡献者仓库样本</small></div>'
    html_doc+='''</div></section><section id="route-a"><h2>A / 从公开插件查参与账号</h2><p class="sub">搜索候选 → manifest 验证 → 仓库与子目录去重 → contributors → 按 GitHub ID 去重。组织、明确 bot 排除。计的是累计公开参与账号，包含文档等贡献，不等于独立插件作者或自然人数。</p>'''
    html_doc+=table(['Harness','搜索命中','检查仓库','验证发布单元','贡献者仓库样本','去重参与账号','个人owner账号','A条件外推'],arows)
    html_doc+='''<div class="formula">A条件外推 = 样本去重参与账号 ÷ 可归因贡献者仓库数 ×（验证仓库数 ÷ 检查仓库数）× 搜索命中数</div><p class="sub">该外推假设搜索前100条样本可代表全部命中、身份去重率可迁移，并忽略未发现来源。重复作者跨更多仓库出现会导致非线性偏差；未命中 manifest 不等于无效。它是用于检验的粗略情景，不是抽样无偏估计。只覆盖 GitHub 搜索口径。</p></section>'''
    html_doc+='''<section id="route-b"><h2>B / 历史方法记录：开发者外推已撤回</h2><p class="notice">以下开发者公式仅保留作历史审计，已不再计算或发布开发者总量。累计贡献者的去重并集不能按插件数线性放大。</p><p class="sub">厂商未披露独立开发者总数。下面先用固定 DSH 贡献者样本推导“参与账号/插件”比例，再用官方公开插件估算构造账号锚点；其余产品按 npm 下载强度迁移。用户与插件列也采用同一强假设，不伪装成官方数字。</p>'''
    html_doc+=f'''<div class="formula">DSH账号锚点 = 34,900 × 固定DSH样本去重参与账号 / 该样本插件数
B账号情景 = DSH账号锚点 ×（目标当周npm下载 / DSH披露日前7天npm下载）^α
B用户情景 = 5,480,000 × 同一下载强度比^α
B插件情景 = 34,900 × 同一下载强度比^α
α = 0.7 / 1.0 / 1.3；范围仅为参数敏感性，不是置信区间。</div><p class="sub">固定校准建立于 {esc(cal.get('created_at','—'))}，样本比率 {cal.get('accounts_per_plugin') if cal.get('accounts_per_plugin') is not None else '缺失'}；披露日为 {esc(d['as_of'])}。当前样本与历史披露日期不一致是额外假设；锚点保存在 data/calibration.json，周更不会悄悄重置。</p>'''
    html_doc+=table(['Harness','B账号 α=1','α情景范围','插件情景 α=1','MAU情景 α=1'],brows)
    html_doc+='''<div class="notice">B 的大数可能主要由 npm 渠道结构和升级频次驱动。用户情景尤其未经独立验证，不能用于用户份额排名；58.94%“创建或使用插件”没有被当作作者比例。作者跨多个插件、SDK依赖、CI、缓存及旧包迁移均会影响结果。</div></section>'''
    html_doc+='''<section id="compare"><h2>差距有多大，能决定什么？</h2><p class="sub">A 只覆盖 GitHub 搜索候选，B 试图外推跨渠道公开生态，两者量级比不是准确率。为帮助比较形状，另将每条路线各自的 DSH 设为100；指数差是代理指标分歧，不是真实人数误差。</p>'''
    html_doc+=table(['Harness','A指数 DSH=100','B指数 DSH=100','B−A 指数点','B/A量级比（异口径）'],grows)
    html_doc+='<div class="grid"><div class="panel"><h3>A · 候选范围外推指数</h3>'+chart(products,'a_index','A路线指数','#21765a')+'</div><div class="panel"><h3>B · 下载强度外推指数</h3>'+chart(products,'b_index','B路线指数','#b28244')+'</div></div>'
    html_doc+=f'''<div class="panel" style="margin-top:20px"><h3>当前建议：保留 A 的观测证据，B 作为敏感性对照</h3><p>{disagreement} 两个量级均有强假设，不应取平均。不能因为两条估计接近就宣布准确，也不能只因偏差大就判定某条错误。A保留可复核账号与插件清单；B目前依赖渠道比例和作者密度迁移。需要更多同口径披露、扩大样本、路径级贡献核验后，才适合选择绝对人数模型。缺失数据不参与路线选择。</p></div></section>'''
    html_doc+='''<section id="tokens"><h2>OpenRouter / 代表性渠道，而非全市场</h2><p class="sub">Token = 上游统计的 prompt + completion；只包含可归因公开应用。订阅、官方 API、其他云渠道不在此样本中；不同 tokenizer 使跨产品比较近似。</p>'''
    html_doc+=table(['Harness','本周Token','请求数','四家样本份额','Token周环比','数据状态'],orows)
    html_doc+='''<div class="formula">四家样本份额 = 该应用窗口Token / 四家同窗口Token总和
只有四家均成功匹配 canonical app 且窗口一致时才显示份额；缺失不是0。
接口按 total_tokens 排序读取最多200条。找不到的应用留空，不能用榜单截断推断零用量。</div></section>'''
    html_doc+=f'''<section id="weekly"><h2>周度变化 / 下载强度与样本连续性</h2><p class="sub">当前：{esc(current['start'])}—{esc(current['end'])}；前一窗口：{esc(prev['start'])}—{esc(prev['end'])}。均为连续七个完整 UTC 日。下载可以比较自身趋势，不等于用户增减。</p>'''
    html_doc+=table(['Harness','前7天下载','当前7天下载','环比','纳入的主包/历史别名'],nrows)
    html_doc+='<h3>与上一份周快照比较</h3>'+table(['Harness','上次账号','本次账号','新增观察账号','未再观察账号','可比性'],weekly)
    html_doc+='<p class="sub">首次运行没有历史快照。只在6–10天前存在相同采集配置且贡献者仓库集合一致时计算账号集合变化；更早或不同覆盖的快照不冒充周环比。</p>'
    if history_rows: html_doc+='<details><summary>已保存的历史结果</summary>'+table(['窗口结束日','Harness','下载次数','A样本账号','B账号情景'],history_rows)+'</details>'
    html_doc+='</section><section id="method"><h2>方法、覆盖与可复核来源</h2>'
    html_doc+=f'''<p>DSH披露：DAU {num(d['dau'])}、MAU {num(d['mau'])}、单日Token {num(d['tokens_daily'])}；公开插件去重 {num(d['plugins_union'])}，其中GitHub {num(d['plugins_github'])}、npm {num(d['plugins_npm'])}。<a href="{esc(d['source'])}">报道与原始配图</a>。属于媒体转述厂商披露，插件数本身为公开资料估算。</p><ul><li>不同产品搜索规则和生态可发现性不同；默认只检查前100条中的固定哈希样本，尚非全量。</li><li>manifest只检查当前规则支持的布局；未解析目录、外部marketplace来源和私有插件会漏掉。核实的是结构证据，不是安装可用性或安全审核。</li><li>contributors缓存、匿名邮箱、fork继承历史、机器人漏识别会影响账号数；本轮没有声称完成自然人去重或近90天活跃统计。</li><li>npm主包只计分发下载。Pi新旧包合并次数不去重用户；其他未登记分发入口不在统计中。</li><li>所有缺失用“—”，不把失败当零。缓存有采集时间，报告完整记录本次请求证据。</li><li>本报告数据文件只含公开响应，不含请求凭据。OpenRouter聚合数据若发布，应按CC BY 4.0注明来源与meta.as_of。</li></ul>'''
    html_doc+='<details><summary>已验证插件与贡献者采集状态</summary>'+table(['Harness','仓库','发布单元','全仓识别账号','状态'],evidence)+'</details>'
    html_doc+='<details><summary>异常与缺失（'+str(len(errors))+'项）</summary><ul>'+(''.join('<li>'+esc(e)+'</li>' for e in errors) or '<li>本轮已执行请求未记录错误；不代表覆盖完整。</li>')+'</ul></details>'
    html_doc+='''<p class="sub"><a href="https://github.com/OpenRouterTeam/docs/blob/main/cookbook/administration/data-api.mdx">OpenRouter 数据口径</a> · <a href="https://openrouter.ai/docs/app-attribution">应用归因</a> · <a href="https://github.com/npm/registry/blob/main/docs/download-counts.md">npm 下载接口</a> · <a href="https://docs.github.com/en/rest/repos/repos#list-repository-contributors">GitHub 贡献者接口</a></p><button id="download">下载本轮结构化数据</button> <button onclick="window.print()">打印 / 保存 PDF</button></section>'''
    html_doc+=f'<div class="foot">Harness Observatory · {esc(run["method_version"])} · 公开观测 / 厂商披露 / 条件外推分层展示。完整证据与运行记录保存在同一项目 data/ 目录。</div></main><script type="application/json" id="report-data">{embedded}</script>'
    html_doc+='''<script>document.getElementById('download').addEventListener('click',()=>{const blob=new Blob([document.getElementById('report-data').textContent],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='harness-weekly-data.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)});</script></body></html>'''
    return html_doc
