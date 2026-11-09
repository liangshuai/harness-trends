"""Chart-first, self-contained HTML for management reporting."""
import base64
from datetime import datetime
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo
from .render_methodology import esc, table, render as methodology
from .changelog import summarize
from .metrics import SUMMARY_ORDER, default_insight, scale_summary, summary_rows, user_cell

COLORS={'codex':'#305aef','claude':'#d77653','dsh':'#318e80','pi':'#9d7ad4','other':'#dbe0e9'}
NAMES={'codex':'Codex','claude':'Claude Code','dsh':'DSH','pi':'Pi'}


def number(v):
    if v is None:return '—'
    if abs(v)>=1e12:return f'{v/1e12:,.2f}T'
    if abs(v)>=1e9:return f'{v/1e9:,.2f}B'
    if abs(v)>=1e8:return f'{v/1e8:,.2f}亿'
    if abs(v)>=1e4:return f'{v/1e4:,.1f}万'
    return f'{v:,.0f}'


def growth(a,b):return a/b-1 if a is not None and b and b>0 else None


def change(v):
    return '<span class="muted">暂无对照</span>' if v is None else f'<span class="{"up" if v>=0 else "down"}">{v:+.1%}</span>'


def dot(pid):return f'<span class="dot" style="background:{COLORS[pid]}"></span>'


def donut(rows,center,caption,label):
    total=sum(v for _,_,v in rows)
    if total<=0:return '<div class="empty">数据不足，暂不生成份额图</div>'
    arcs=[];legend=[];offset=0
    for pid,name,value in rows:
        share=value/total*100
        arcs.append(f'<circle cx="150" cy="150" r="112" fill="none" stroke="{COLORS[pid]}" stroke-width="35" pathLength="100" stroke-dasharray="{share:.10f} {100-share:.10f}" stroke-dashoffset="{-offset:.10f}" transform="rotate(-90 150 150)"><title>{esc(name)}：{share:.1f}% · {number(value)} Token</title></circle>')
        offset+=share
        legend.append(f'<div class="legend-row"><span>{dot(pid)}{esc(name)}</span><strong>{share:.1f}%</strong><span class="muted">{number(value)}</span></div>')
    svg=f'<svg class="donut" viewBox="0 0 300 300" role="img" aria-label="{esc(label)}"><title>{esc(label)}</title>'+''.join(arcs)+f'<text x="150" y="146" text-anchor="middle" class="donut-value">{esc(center)}</text><text x="150" y="172" text-anchor="middle" class="donut-caption">{esc(caption)}</text></svg>'
    return '<div class="donut-layout">'+svg+'<div class="legend">'+''.join(legend)+'</div></div>'


def bars(products,current,previous,field,unit):
    maximum=max([current.get(p,{}).get(field) or 0 for p in products]+[previous.get(p,{}).get(field) or 0 for p in products]+[1])
    rows=[]
    for pid in sorted(products,key=lambda p:current.get(p,{}).get(field) or -1,reverse=True):
        now=current.get(pid,{}).get(field);old=previous.get(pid,{}).get(field)
        rows.append(f'<div class="rank-row"><div class="rank-name">{dot(pid)}{esc(NAMES[pid])}</div><div class="bar-pair"><div class="bar-old" style="width:{(old or 0)/maximum*100:.5f}%" title="前周 {number(old)}"></div><div class="bar-current" style="width:{(now or 0)/maximum*100:.5f}%;background:{COLORS[pid]}" title="本周 {number(now)}"></div></div><div class="rank-number"><strong>{number(now)}</strong><small>{change(growth(now,old))}</small></div></div>')
    return '<div>'+''.join(rows)+'</div><div class="mini-key"><i></i>浅灰：前一周 <b></b>彩色：本周 · '+esc(unit)+'</div>'


def trend_svg(windows,products):
    if not windows:return '<div class="empty">历史用量尚未取得</div>'
    left,right,top,bottom=60,865,25,260
    maximum=max([w.get('products',{}).get(p,{}).get('tokens') or 0 for w in windows for p in products]+[1])*1.15
    x=lambda i:left+(right-left)*i/max(1,len(windows)-1)
    y=lambda v:bottom-(bottom-top)*v/maximum
    parts=[]
    for i in range(5):
        v=maximum*i/4;yy=y(v)
        parts.append(f'<line x1="{left}" x2="{right}" y1="{yy:.3f}" y2="{yy:.3f}" stroke="#e9edf3"/><text x="{left-12}" y="{yy+4:.3f}" text-anchor="end" class="axis">{v/1e12:.1f}T</text>')
    for i,w in enumerate(windows):
        parts.append(f'<text x="{x(i):.3f}" y="{bottom+28}" text-anchor="middle" class="axis">{esc(w["end"][5:])}</text>')
    for pid in products:
        segment=[]
        for i,w in enumerate(windows):
            v=w.get('products',{}).get(pid,{}).get('tokens')
            if v is None:
                if len(segment)>1:parts.append(f'<polyline points="{" ".join(segment)}" fill="none" stroke="{COLORS[pid]}" stroke-width="3"/>')
                segment=[];continue
            segment.append(f'{x(i):.3f},{y(v):.3f}')
            parts.append(f'<circle cx="{x(i):.3f}" cy="{y(v):.3f}" r="5" fill="{COLORS[pid]}" stroke="white" stroke-width="2"><title>{esc(NAMES[pid])} / {esc(w["start"])}—{esc(w["end"])}：{number(v)}</title></circle>')
        if len(segment)>1:parts.append(f'<polyline points="{" ".join(segment)}" fill="none" stroke="{COLORS[pid]}" stroke-width="3"/>')
    return '<svg class="trend-svg" viewBox="0 0 900 310" role="img" aria-label="连续七天窗口的Token用量趋势">'+''.join(parts)+'</svg>'


CSS='''
:root{--ink:#242424;--muted:#777777;--line:#E8E9EB;--paper:#FFFFFF;--primary:#F05A23;--secondary:#FFF1EA;--aux:#F6F7F8}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--ink);font:14px/1.65 -apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif}a{color:#B33D13;text-underline-offset:3px}header{background:#FFFFFF;color:var(--ink);border-top:4px solid var(--primary);border-bottom:1px solid var(--line);padding:37px max(calc((100vw - 1160px)/2),26px) 35px;position:relative;overflow:hidden}header:after{content:'';position:absolute;width:480px;height:480px;right:-80px;top:-300px;border:90px solid var(--secondary);border-radius:50%;pointer-events:none}.eyebrow{font-size:10px;letter-spacing:3.5px;color:#AF451F}.header-row{display:flex;justify-content:space-between;align-items:flex-end;gap:20px;position:relative;z-index:1}h1{font-size:36px;line-height:1.2;letter-spacing:-1px;margin:14px 0 9px}.header-sub{color:#777777;margin:0;font-size:13px}.issue{font-size:12px;color:#777777;text-align:right;white-space:nowrap}.issue strong{display:block;font-size:19px;color:#242424;margin-bottom:5px}nav{position:sticky;top:0;z-index:5;background:#ffffffed;backdrop-filter:blur(12px);border-bottom:1px solid var(--line);display:flex;gap:28px;padding:13px max(calc((100vw - 1160px)/2),26px);overflow:auto}nav a{font-size:12px;color:#666666;text-decoration:none;white-space:nowrap}main{max-width:1212px;padding:25px 26px 55px;margin:auto}section{margin:34px 0;scroll-margin-top:70px}h2{font-size:22px;letter-spacing:-.4px;line-height:1.4;margin:0}h3{font-size:16px;margin:0 0 5px}.section-head{display:flex;align-items:flex-end;justify-content:space-between;gap:15px;margin-bottom:17px}.section-label{font-size:10px;letter-spacing:2px;color:#777777;margin-bottom:5px}.sub,.muted{color:var(--muted)}.sub{font-size:12px;margin:5px 0}.scope{font-size:12px;background:var(--secondary);color:#775040;padding:11px 16px;border-radius:7px;margin-bottom:21px}.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:15px}.kpi,.panel{background:white;border:1px solid var(--line);border-radius:10px;padding:23px}.kpi-label{color:#777777;font-size:12px}.kpi-value{font-size:31px;font-weight:680;line-height:1.3;letter-spacing:-1px;margin:12px 0 8px}.kpi-note{font-size:11px;color:#777777}.up{color:#238b70;font-weight:600}.down{color:#ca725e;font-weight:600}.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}.dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:9px;flex-shrink:0}.panel{min-width:0}.donut-layout{display:flex;align-items:center;justify-content:center;gap:10px;margin:10px 0}.donut{width:52%;max-width:285px;flex-shrink:0}.donut-value{font-size:27px;fill:#242424;font-weight:700;letter-spacing:-.5px}.donut-caption{font-size:10px;fill:#777777}.legend{flex:1;min-width:0}.legend-row{display:grid;grid-template-columns:minmax(72px,1fr) 44px 53px;gap:7px;align-items:center;padding:11px 0;border-bottom:1px solid var(--aux);font-size:11px}.legend-row>span:first-child{display:flex;align-items:center;white-space:normal}.legend-row strong{text-align:right;font-size:12px}.legend-row>span:last-child{text-align:right}.legend-row:last-child{border:0}.footnote{font-size:10px;line-height:1.7;color:#777777;margin-top:15px}.rank-row{display:grid;grid-template-columns:106px 1fr 88px;gap:12px;align-items:center;margin:24px 0}.rank-name{font-size:12px;white-space:nowrap}.bar-pair{position:relative;height:27px}.bar-old{position:absolute;top:0;height:10px;background:#E7E9EC;border-radius:3px}.bar-current{position:absolute;bottom:0;height:10px;border-radius:3px;min-width:0}.rank-number{text-align:right;line-height:1.4}.rank-number strong{font-size:15px}.rank-number small{display:block;font-size:10px;margin-top:3px}.mini-key{font-size:10px;color:#777777;display:flex;align-items:center;gap:6px;margin-top:18px}.mini-key i,.mini-key b{display:inline-block;width:12px;height:6px;background:#E7E9EC;border-radius:2px}.mini-key b{background:var(--primary);margin-left:8px}.insights{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:18px}.insight{padding:18px;background:var(--secondary);border-radius:8px;font-size:12px}.insight b{display:block;margin-bottom:6px;font-size:13px}.trend-svg{width:100%;display:block;margin-top:18px}.axis{font-size:11px;fill:#777777;font-family:inherit}.chart-key{display:flex;gap:22px;flex-wrap:wrap;font-size:11px;margin:13px 0}.table-scroll{overflow:auto;background:white;border:1px solid var(--line);border-radius:9px;margin:16px 0}table{width:100%;border-collapse:collapse;white-space:nowrap;font-size:12px}th{font-size:11px;font-weight:500;background:var(--aux);color:#666666;text-align:left}td,th{padding:14px 17px;border-bottom:1px solid var(--aux)}tbody tr:last-child td{border:0}td:first-child{font-weight:600}.badge{font-size:10px;color:#666666;border:1px solid var(--line);border-radius:4px;padding:3px 7px}.badge.official{background:var(--secondary);color:#A8411A;border-color:#F4D4C5}.dsh-metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:15px;margin-top:18px}.dsh-metrics .value{font-size:27px;font-weight:650;line-height:1.5}.dsh-metrics small{color:#777777;font-size:10px}.disclosure-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:18px 0}.disclosure-grid img{width:100%;height:auto;border:1px solid var(--line);border-radius:7px}.chart-caption{font-size:11px;color:#777777;margin:8px 0}.button,button{border:1px solid var(--line);background:white;color:#A8411A;border-radius:6px;padding:8px 12px;font-size:11px;cursor:pointer;text-decoration:none;display:inline-block}details{background:white;border:1px solid var(--line);border-radius:8px;padding:19px;margin:16px 0}summary{font-size:13px;font-weight:600;cursor:pointer}.details-body{padding-top:15px}.formula{white-space:pre-wrap;overflow-wrap:anywhere;font:12px/1.8 ui-monospace,monospace;background:var(--aux);border-radius:7px;padding:16px}footer{font-size:10px;color:#777777;border-top:1px solid var(--line);padding-top:23px;margin-top:34px}.empty{padding:80px 15px;text-align:center;color:#777777}.alert{background:var(--secondary);color:#775040;padding:15px;border-radius:8px;font-size:12px}.method-detail section{margin:28px 0}.method-detail h2{font-size:19px}.method-detail .cards{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.method-detail .card{padding:13px;background:var(--aux);border-radius:6px}.method-detail .number{font-size:24px}.method-detail .tag{font-size:10px;color:#777777}.method-detail .notice{padding:12px;background:var(--secondary);margin:15px 0}.method-detail .bar-row{display:grid;grid-template-columns:115px 1fr 65px;gap:10px;margin:13px 0}.method-detail .bar-track{height:12px;background:var(--aux)}.method-detail .bar-track>div{height:100%}.method-detail .foot{font-size:11px;color:#777777}@media(max-width:1000px){.donut-layout{flex-direction:column}.donut{width:80%}.legend{width:100%}.kpi-value{font-size:25px}.rank-row{grid-template-columns:87px 1fr 73px;gap:7px}.insights{grid-template-columns:1fr}}@media(max-width:660px){header{padding:28px 20px}.header-row{display:block}h1{font-size:29px}.issue{text-align:left;margin-top:20px}.issue strong{font-size:14px}.kpis{grid-template-columns:1fr 1fr;gap:10px}.kpi,.panel{padding:17px}.grid{grid-template-columns:1fr}.donut-layout{flex-direction:row}.donut{width:48%}.legend-row{grid-template-columns:1fr 42px 48px}.dsh-metrics{grid-template-columns:1fr 1fr}main{padding:22px 16px}nav{padding:12px 20px;gap:20px}.section-head{align-items:flex-start}.disclosure-grid{grid-template-columns:1fr}.method-detail .cards{grid-template-columns:1fr 1fr}.kpi-note{font-size:10px}}@media print{body{background:white;font-size:11px}header{background:white;color:#242424;padding:16px 20px;border-bottom:2px solid var(--primary)}header:after,nav,.no-print,button{display:none}header .header-sub,header .issue,header .issue strong{color:#777777}h1{font-size:27px}main{padding:15px 20px}.panel,.kpi,.table-scroll{break-inside:avoid}.section-head{break-after:avoid}.grid{grid-template-columns:1fr 1fr}.donut-layout{flex-direction:row}.donut{width:48%}.kpis{grid-template-columns:repeat(4,1fr)}.kpi-value{font-size:23px}.insights{grid-template-columns:repeat(3,1fr)}.table-scroll{overflow:visible}table{white-space:normal}.footnote{font-size:9px}details:not([open]){display:none}section{margin:24px 0}.trend-svg{max-height:230px}a{color:inherit}}

h1,.kpi-value{color:var(--primary)}nav a:hover,nav a:focus-visible{color:#A8411A;background:var(--secondary);border-radius:4px}button:hover{background:var(--secondary);border-color:var(--primary)}a:focus-visible,button:focus-visible,summary:focus-visible{outline:2px solid var(--primary);outline-offset:3px}
.summary-table table{white-space:normal}.summary-table td,.summary-table th{vertical-align:top;min-width:84px}.summary-table td:nth-child(7),.summary-table td:nth-child(8){min-width:240px}.summary-table small{display:inline-block;margin-top:3px}#features ul{padding-left:20px;margin:8px 0}#features ul ul{margin:5px 0;padding-left:18px}
'''


def heading(kicker,title,right=''):
    return f'<div class="section-head"><div><div class="section-label">{esc(kicker)}</div><h2>{esc(title)}</h2></div><p class="sub">{esc(right)}</p></div>'


def product_publisher_count(product):
    return product['github'].get('publisher_count',0)


def summary_section(run, config):
    """Four-harness summary table at the top of the report, mirroring the Markdown edition."""
    rows=[]
    for row in summary_rows(run):
        token='<strong>'+number(row['tokens'])+'</strong>' if row['tokens'] is not None else '—'
        if row['share'] is not None:token+=f'<br><small class="muted">份额 {row["share"]:.1%}</small>'
        if row['token_wow'] is not None:token+='<br><small>'+change(row['token_wow'])+'</small>'
        downloads=number(row['downloads']) if row['downloads'] is not None else '—'
        if row['download_wow'] is not None:downloads+='<br><small>'+change(row['download_wow'])+'</small>'
        contributors='—' if row['contributors'] is None else f'{row["contributors"]:,}<br><small class="muted">{esc(row.get("repo") or "")}</small>'
        plugins='—' if row['plugins'] is None else f'{row["plugins"]:,}<br><small class="muted">{esc(row["plugin_source"] or "")}</small>'
        user_lines=user_cell(run,config,row['pid'])
        users='<br>'.join(esc(line) for line in user_lines) if user_lines else '<span class="muted">—</span>'
        raw=row['insight']
        if isinstance(raw,list) and raw:
            # Plain numbered lines, not a real list element: keeps table rows compact and aligned.
            insight='<br>'.join(f'{index}）{esc(item)}' for index,item in enumerate(raw,1))
        else:
            insight=esc(raw or default_insight(run,row['pid']))
        action=esc(row['action']) if row['action'] else '<span class="muted">—</span>'
        rows.append([dot(row['pid'])+esc(row['name']),token,downloads,contributors,plugins,users,insight,action])
    body=('<div class="table-scroll summary-table"><table><thead><tr>'
          +''.join(f'<th scope="col">{esc(x)}</th>' for x in
                   ['Harness','周Token / OpenRouter','周下载量','开源贡献者','插件数量','活跃用户','洞察（本周新功能）','行动'])
          +'</tr></thead><tbody>'+''.join('<tr>'+''.join(f'<td>{x}</td>' for x in row)+'</tr>' for row in rows)
          +'</tbody></table></div>')
    return ('<p class="sub" style="margin:20px 0 0"><strong>四家汇总</strong>：Token与下载量为渠道观测；开源贡献者为官方公开仓库非匿名账号计数；'
            '插件数量各家目录口径不同，不可横向排名；活跃用户仅列官方披露（合计与单品分开）；洞察与行动为编辑观点。</p>'+body)


def features_section(run):
    """This week's shipped features: scripted Releases/CHANGELOG extraction plus editorial verification."""
    updates=run.get('product_updates') or {}
    if not updates:
        return ''
    views=(run.get('editorial') or {}).get('products',{})
    s='<section id="features">'+heading('05 / WEEKLY FEATURES','本周新功能特性','脚本采集 GitHub Releases + CHANGELOG.md 原文 · 网络检索核实为编辑内容')
    for pid in SUMMARY_ORDER:
        product=run['products'].get(pid)
        update=updates.get(pid)
        if product is None or update is None:
            continue
        releases=update.get('releases',[])
        versions='、'.join(r.get('version') or r.get('tag','') for r in releases) or '窗口内无发布'
        s+=f'<div class="panel" style="margin-top:14px"><div class="section-head"><div><h3>{dot(pid)}{esc(product["name"])}</h3>' \
           f'<p class="sub">窗口内发布：{esc(versions)}（来源：GitHub Releases{" + CHANGELOG.md" if update.get("changelog") else ""}）</p></div></div>'
        items=[]
        for item in summarize(update):
            if not item['highlights']:
                continue
            bullets=''.join(f'<li>{esc(b)}</li>' for b in item['highlights'])
            items.append(f'<li><b>{esc(item["version"])}</b>（{esc(item["published_at"][:10])}，'
                         f'{"预发布" if item["prerelease"] else "正式版"}，{esc(item["basis"])}）<ul>{bullets}</ul></li>')
        if items:
            s+='<ul>'+''.join(items)+'</ul>'
        elif update.get('status')=='missing':
            reason='；'.join(update.get('errors') or ['未知原因'])
            s+=f'<p class="sub">脚本采集失败：{esc(reason)}；本产品仅剩编辑内容。</p>'
        else:
            s+='<p class="sub">窗口内发布说明为占位文本，无可提取功能要点。</p>'
        view=views.get(pid) or {}
        if view.get('feature_summary'):
            s+=f'<p><span class="badge">编辑</span> 网络检索核实：{esc(view["feature_summary"])}</p>'
            for source in view.get('sources',[]):
                s+=f'<p class="footnote">来源：<a href="{esc(source)}" target="_blank" rel="noopener">{esc(source)}</a></p>'
        s+='</div>'
    return s+'</section>'


def scale_section(run,config):
    if run.get('estimation_model_version')=='2.0':
        from .render_estimates_v2 import render_scales
        return render_scales(run,config)
    products=run['products']
    summaries={pid:scale_summary(p,config['estimation']['reference_alpha']) for pid,p in products.items()}
    s='<section id="scale">'+heading('SCALE ESTIMATES / CONDITIONAL MODEL','用户、开发者与插件规模估算','四家同一模型 · 参考值 + 参数情景范围')
    s+='<div class="alert"><strong>实验估算 · 可信度低</strong>　以下是DSH披露锚点结合npm下载强度推导的规模情景，不是已验证人数。月活是MAU等效规模；开发者是累计公开参与账号等效规模，含文档等贡献，不等于自然人。范围来自α=0.7/1.0/1.3的敏感性分析，不是置信区间。</div>'
    rows=[]
    for pid,p in products.items():
        summary=summaries[pid];cells=[dot(pid)+esc(NAMES[pid])]
        for field in ('users','developers','plugins'):
            e=summary[field]
            if field=='developers':
                cells.append(f'<strong>总体暂不可估</strong><br><small class="muted">观察到个人发布者 {product_publisher_count(p)} 个账号</small>')
            else:
                cells.append(f'<strong>{number(e["reference"])}</strong><br><small class="muted">{number(e["low"])} — {number(e["high"])}</small>')
        cells.append('DSH披露锚点 / npm强度外推')
        rows.append(cells)
    s+=table(['Harness','月活用户估算 / MAU','开发者规模 / 发布者样本','公开插件数量估算','依据'],rows)
    s+='<p class="footnote">粗体为α=1参考值，下方为参数情景范围。三项共用同一个下载强度倍数，不能视为三路独立验证的证据；渠道差异、更新频次和高产作者会放大偏差。DSH厂商披露MAU为548万、公开插件为3.49万（11月4日），本表是按报告窗口推演，故不必等于披露点。</p><div class="grid">'
    s+='<div class="alert"><strong>开发者总量估算已撤回。</strong> 先前将DSH的201个累计贡献账号/8个插件外推，混淆了贡献者、插件作者和发布者；高协作仓库又使密度偏大。现在只展示个人发布者的样本账号数，不给出总开发者人数；用户和插件数仍是未经独立校准的实验情景。</div>'
    for field,title in [('users','月活用户估算'),('plugins','公开插件数量估算')]:
        maximum=max([summaries[p][field]['high'] or 0 for p in products]+[1])
        s+=f'<div class="panel"><h3>{title}</h3><p class="sub">色条：参考值；灰条：情景上界</p>'
        for pid in sorted(products,key=lambda p:summaries[p][field]['reference'] or -1,reverse=True):
            e=summaries[pid][field]
            s+=f'<div class="rank-row"><div class="rank-name">{dot(pid)}{esc(NAMES[pid])}</div><div class="bar-pair"><div class="bar-old" style="width:{(e["high"] or 0)/maximum*100:.4f}%"></div><div class="bar-current" style="width:{(e["reference"] or 0)/maximum*100:.4f}%;background:{COLORS[pid]}"></div></div><div class="rank-number"><strong>{number(e["reference"])}</strong><small class="muted">条件估算</small></div></div>'
        s+='</div>'
    s+='<div class="panel"><h3>GitHub路线独立对照</h3><p class="sub">候选范围外推，范围仅限各自查询命中；与跨渠道B情景口径不同。</p>'
    s+=table(['Harness','观察到个人发布者账号（样本）','A公开插件外推'],[[esc(NAMES[p]),str(product_publisher_count(products[p])),number(v['a_plugins'])] for p,v in summaries.items()])
    s+='<p class="footnote">A插件 = 搜索命中数 × 样本已验证发布单元 / 检查仓库数。市场目录、monorepo与未发现插件会影响结果；两条路线的差距不能当作真实误差。</p></div></div>'
    s+='<details><summary>本页估算的简要公式与校准参数</summary><div class="formula">下载倍数 R = 目标Harness本周npm下载 / DSH披露日前七天npm下载\nMAU情景 = 548万 × R^α\n插件情景 = 3.49万 × R^α\n开发者总体人数：已撤回贡献者密度外推，仅保留去重后的样本观测\nα = 0.7、1.0、1.3；参考值使用1.0。\n固定DSH样本：'+esc(run['calibration'].get('accounts','—'))+'个参与账号 / '+esc(run['calibration'].get('plugins','—'))+'个插件。累计参与账号跨更多插件的重复率未知，此锚点可能显著高估。</div></details></section>'
    return s


def render(run,config):
    products=run['products']; cur=run['openrouter_current'].get('products',{});prev=run['openrouter_previous'].get('products',{})
    complete=run['openrouter_current']['status']=='ok' and all(cur.get(p,{}).get('tokens') is not None for p in products)
    total=sum(cur[p]['tokens'] for p in products) if complete else None
    oldtotal=sum(prev[p]['tokens'] for p in products) if all(prev.get(p,{}).get('tokens') is not None for p in products) else None
    requests=sum(cur[p]['requests'] for p in products) if complete and all(cur[p].get('requests') is not None for p in products) else None
    ordered=sorted(products,key=lambda p:cur.get(p,{}).get('tokens') or -1,reverse=True)
    leader=ordered[0] if complete else None
    share=cur[leader]['tokens']/total if leader and total else None
    growths={p:growth(cur.get(p,{}).get('tokens'),prev.get(p,{}).get('tokens')) for p in products}
    valid={p:v for p,v in growths.items() if v is not None}
    fastest=max(valid,key=valid.get) if valid else None
    generated=datetime.fromisoformat(run['generated_at']).astimezone(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M')
    start,end=run['window']['start'],run['window']['end']
    pages=run['openrouter_current'].get('pages',[])
    asof=pages[-1].get('meta',{}).get('as_of','—') if pages else '—'
    s='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AI Agent Harness 市场观察周报 · 数据汇报版</title><style>'+CSS+'</style></head><body>'
    s+=f'<header><div class="eyebrow">HARNESS INTELLIGENCE / WEEKLY BRIEF</div><div class="header-row"><div><h1>AI Agent Harness 市场观察周报</h1><p class="header-sub">Codex · Claude Code · DeepSeek Harness · Pi</p></div><div class="issue"><strong>{esc(end)}</strong>数据窗口 {esc(start)} — {esc(end)} / UTC</div></div></header><nav><a href="#overview">核心数据</a><a href="#share">用量份额</a><a href="#usage">规模与增长</a><a href="#trend">四周趋势</a><a href="#ecosystem">生态与用户</a><a href="#features">本周新功能</a><a href="#appendix">数据附录</a></nav><main><div class="scope">统计口径：OpenRouter公开数据；图表分别注明分母，不代表全市场用户份额。生成于 {esc(generated)}（北京时间）。</div>'
    s+='<section id="overview" style="margin-top:0"><div class="kpis">'
    kpis=[('四家样本 · 周Token总量',number(total),'较前周 '+change(growth(total,oldtotal))),('四家样本 · 周请求总量',number(requests),'一次任务可能包含多次请求'),('本周Token份额第一',f'{share:.1%}' if share is not None else '—',NAMES[leader] if leader else '等待完整数据'),('Token增长最快',f'{valid[fastest]:+.1%}' if fastest else '—',NAMES[fastest] if fastest else '等待对照窗口')]
    for label,value,note in kpis:s+=f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div><div class="kpi-note">{note}</div></div>'
    s+='</div>'
    s+=summary_section(run,config)
    if complete:
        ds=cur.get('dsh',{}).get('share_four');dsold=prev.get('dsh',{}).get('share_four')
        pp=(ds-dsold)*100 if ds is not None and dsold is not None else None
        dsnote=f'DSH Token环比 {growths["dsh"]:+.1%}' if growths.get('dsh') is not None else 'DSH前周数据缺失'
        if pp is not None:dsnote+=f'，四家内部份额变化 {pp:+.1f} 个百分点。'
        npm={p:v.get('download_wow') for p,v in products.items() if v.get('download_wow') is not None}
        nl=max(npm,key=npm.get) if npm else None
        npmnote=f'{NAMES[nl]} 本周npm下载环比 {npm[nl]:+.1%}，为四家中最高。' if nl else '下载趋势待补齐。'
        s+=f'<div class="insights"><div class="insight"><b>用量领先 / {NAMES[leader]}</b>占四家样本Token的 {share:.1%}，本周用量 {number(cur[leader]["tokens"])}。</div><div class="insight"><b>份额变化 / DSH</b>{dsnote}</div><div class="insight"><b>分发热度 / npm</b>{esc(npmnote)} 下载次数不等于活跃用户。</div></div>'
    else:s+='<div class="alert">OpenRouter数据尚未完整匹配，份额图暂不计算；其余可用数据仍保留。</div>'
    s+='</section><section id="share">'+heading('01 / TOKEN SHARE','代表性用量份额','OpenRouter · 周Token')+'<div class="grid"><div class="panel"><h3>四家 Harness 内部份额</h3><p class="sub">分母：四家同窗口Token之和</p>'
    selected=[(p,NAMES[p],cur[p]['tokens']) for p in ordered] if complete else []
    s+=donut(selected,number(total),'四家周Token合计','四家Harness的OpenRouter周Token份额')+'<p class="footnote">只反映本渠道可归因用量，不包含订阅、直连API与其他云渠道。</p></div><div class="panel"><h3>放到公开应用榜单中看 · Top 10</h3><p class="sub">分母：本轮已取得公开应用集合，最多200个</p>'
    overall=run['openrouter_current'].get('slice_total_tokens')
    top=run['openrouter_current'].get('top_apps',[])
    palette=['#687894','#DDA64E','#719552','#B56894','#419AA4','#9D7352','#A1A84F','#7F8792','#BD8C86','#568377']
    canonical={str(v.get('app_id')):pid for pid,v in cur.items() if v.get('app_id') is not None}
    broader=[]
    for index,app in enumerate(top):
        pid=canonical.get(str(app['app_id']),'app_'+str(app['app_id']))
        COLORS.setdefault(pid,palette[index%len(palette)])
        broader.append((pid,f'{index+1}. '+app['app_name'],int(app['total_tokens'])))
    top_total=sum(row[2] for row in broader)
    if broader and overall and overall>=top_total:
        broader.append(('other','其余已取得应用',overall-top_total))
    else:broader=[]
    s+=donut(broader,f'{top_total/overall:.1%}' if broader else '—','前10名合计占集合比例','OpenRouter公开应用前10名及其余已取得应用的Token份额')+'<p class="footnote">按本周Token排名展示前10名，含非编码工具；占比以已取得公开应用集合为分母，不代表整个Harness市场份额。</p></div></div></section>'
    s+='<section id="usage">'+heading('02 / VOLUME & MOMENTUM','用量规模与周增长','本周 vs 前一完整七天窗口')+'<div class="grid"><div class="panel"><h3>Token消耗排名</h3><p class="sub">输入 + 输出Token；T = 万亿，B = 十亿</p>'+bars(products,cur,prev,'tokens','Token')+'</div><div class="panel"><h3>请求量排名</h3><p class="sub">反映交互强度，不等于用户数量</p>'+bars(products,cur,prev,'requests','次')+'</div></div>'
    rows=[]
    for p in ordered:
        r=cur.get(p,{});old=prev.get(p,{});a=r.get('share_four');b=old.get('share_four')
        pp=(a-b)*100 if a is not None and b is not None else None
        rows.append([dot(p)+esc(NAMES[p]),number(r.get('tokens')),f'{a:.1%}' if a is not None else '—',change(growths[p]),f'{pp:+.1f} pp' if pp is not None else '—',number(r.get('requests'))])
    s+=table(['Harness','本周Token','四家内部份额','Token周环比','份额周变化','本周请求次数'],rows)+'</section><section id="trend">'+heading('03 / FOUR-WEEK TREND','四周用量趋势','连续、互不重叠的七天窗口')+'<div class="panel"><div class="chart-key">'+''.join('<span>'+dot(p)+esc(NAMES[p])+'</span>' for p in products)+'</div>'+trend_svg(run.get('openrouter_trend',[]),products)+'<p class="footnote">横轴为窗口结束日（UTC），缺失点留空不补零。按同一应用ID回取历史数据。</p></div></section>'
    s+='<section id="ecosystem">'+heading('04 / DISTRIBUTION & ECOSYSTEM','分发热度与公开生态','下载观测 / GitHub样本')+'<div class="panel"><h3>npm主包下载</h3><p class="sub">分发下载次数，包含更新、CI及重复下载</p>'
    s+=bars(products,{p:{'downloads':v.get('downloads_current')} for p,v in products.items()},{p:{'downloads':v.get('downloads_previous')} for p,v in products.items()},'downloads','下载次数')+'</div>'
    rows=[]
    for p,v in products.items():
        g=v['github'];rows.append([dot(p)+esc(NAMES[p]),number(v.get('downloads_current')),change(v.get('download_wow')),number(g.get('verified_artifacts')),number(v.get('a_observed')),f'{g.get("checked_repos",0)} 个候选 / {g.get("contributor_repos_observed",0)} 个贡献者仓库'])
    s+=table(['Harness','周npm下载','下载周环比','已核验发布单元','样本参与账号','本轮覆盖'],rows)+'<p class="footnote">插件与参与账号是受限公开样本，不是生态总量；一个仓库可能有多个插件。四家发现入口及覆盖不同，不按样本账号数做全市场排名。</p>'
    d=config['disclosure'];s+=f'<div class="panel" style="margin-top:22px"><div class="section-head"><div><h3>DSH 官方披露规模</h3><p class="sub">截至 {esc(d["as_of"])} · 媒体转述厂商披露，不同于OpenRouter渠道数据</p></div><span class="badge official">厂商披露</span></div><div class="dsh-metrics">'
    for v,label,note in [(d['dau'],'日活用户','官方API用户范围'),(d['mau'],'月活用户','具体月窗口未明示'),(d['tokens_daily'],'单日Token','官方API使用口径'),(d['plugins_union'],'公开第三方插件','厂商公开资料估算、已去重')]:s+=f'<div><small>{label}</small><div class="value">{number(v)}</div><small>{note}</small></div>'
    s+='</div><p class="footnote">其他三家尚未取得可直接比较的同口径用户披露；四家用户、开发者和插件估算已列在主报告“规模估算”部分，与厂商披露分开呈现。</p>'
    gallery=[];root=Path(__file__).resolve().parent.parent
    for label,filename in [('用户增长','dsh-disclosure-dashboard.jpg'),('Token用量','dsh-tokens.jpg'),('公开插件','dsh-plugins.jpg')]:
        path=root/'Harness-资料/raw'/filename
        if path.exists():
            src='data:image/jpeg;base64,'+base64.b64encode(path.read_bytes()).decode()
            gallery.append(f'<div><img alt="DSH披露原图：{label}" src="{src}" loading="lazy"><p class="chart-caption">{label} · 披露原图</p></div>')
    if gallery:s+='<details class="no-print"><summary>查看披露原图：用户、Token、插件</summary><div class="disclosure-grid">'+''.join(gallery)+'</div><p class="footnote">用户与Token原图前五点为连续七天日均，11月4日为单日值，不能直接做同口径周环比。</p></details>'
    s+='</div></section>'+features_section(run)+scale_section(run,config)+'<section id="appendix">'+heading('APPENDIX / ESTIMATES & EVIDENCE','估算与数据附录','答疑备用，不进入主报告份额图')
    rows=[]
    for p,v in products.items():
        mid=next((r for r in v.get('b_scenarios',[]) if r['alpha']==1.0),{})
        rows.append([esc(NAMES[p]),number(v.get('a_candidate_projection')),number(v.get('b_reference')),number(mid.get('mau')),f'{v["b_a_scale_ratio"]:,.1f}×' if v.get('b_a_scale_ratio') is not None else '—'])
    if run.get('estimation_model_version')=='2.0':
        s+='<details><summary>估算版本修正记录</summary><p>已废弃“DSH用户/下载比例迁移到其他产品”及“累计贡献者密度乘插件总数”。模型v2使用产品自身用户/收入锚点，以及跨仓库发布者并集。新估算与旧模型不能做连续周环比；原始历史文件保留供审计，不代表旧估算仍有效。</p></details>'
    else:
        s+='<details><summary>两种路线的规模估算与偏差对照</summary><div class="details-body"><p class="sub">A为GitHub候选范围条件外推，B为DSH公开插件锚点与npm强度外推。均未经真实总体数据校准；B/A不是准确率，MAU情景不是官方用户数，不用于市场人数结论。</p>'+table(['Harness','A参与账号外推','B参与账号情景','B月活用户情景','B/A（异口径）'],rows)+'<p class="footnote">本轮建议以可复核的渠道用量和公开生态证据为主体；两种外推保留作研究对照，不能取平均得到真实人数。α参数范围不是置信区间。</p></div></details>'
    legacy=methodology(run,config).split('<main>',1)[1].split('</main>',1)[0] if run.get('estimation_model_version')!='2.0' else '<p>模型v2已替代旧的DSH下载倍数和贡献者密度外推。全部参数、校准基准与源数据保存在本轮结构化数据中；本页规模估算部分附有完整公式。</p>'
    if run.get('estimation_model_version')=='2.0':
        evidence=[]
        for pid,p in products.items():
            for repo in p['github'].get('repos',[]):
                if repo['status']=='verified':
                    evidence.append([esc(NAMES[pid]),'<a href="https://github.com/'+esc(repo['repo'])+'">'+esc(repo['repo'])+'</a>',str(len(repo['artifacts']))])
        legacy+=table(['Harness','已核验插件仓库','发布单元数'],evidence)
        issues=[NAMES[pid]+': '+error for pid,o in run['model_v2_inputs']['owners'].items() for error in o.get('errors',[])]
        legacy+='<p>发布者采样异常：'+(esc('；'.join(issues)) if issues else '本轮未记录请求错误；不代表覆盖完整。')+'</p>'
    legacy=re.sub(r'id="([^"]+)"',r'id="method-\1"',legacy)
    legacy=re.sub(r'href="#([^"]+)"',r'href="#method-\1"',legacy)
    legacy=re.sub(r'<button[^>]*>.*?</button>','',legacy)
    s+='<details><summary>完整计算方法、插件清单与异常记录</summary><div class="method-detail">'+legacy+'</div></details><div class="no-print"><button id="download">下载结构化数据</button> <button onclick="window.print()">打印 / 保存PDF</button></div></section>'
    if run.get('data_inventory'):
        audit=table(['报告数据','刷新方式','本轮状态','来源'],[[esc(r['name']),esc(r['refresh']),esc(r['status']),esc(r['source'])] for r in run['data_inventory']])
        s+='<details><summary>全报告自动化数据清单与刷新状态</summary>'+audit+'<p class="footnote">运行数据每次重采；历史披露按原日期保留并检查源页，不把固定锚点当成本周新披露。模型假设固定版本，不随周更随意修改。</p></details>'
    s+=f'<footer><strong>口径摘要</strong>　Token份额 = 对应应用Token / 图中注明的样本Token总和；采用canonical app ID，避免同名应用重复；未成功取数时留空。<br>{esc(run.get("settlement_note",""))}<br>API快照时间：{esc(asof)}。原始证据、校准参数及历次运行记录均已保存。<br>Source: OpenRouter (openrouter.ai/apps), as of {esc(asof)}. Licensed under CC BY 4.0.<br><a href="https://openrouter.ai/apps">OpenRouter Apps</a> · <a href="{esc(d["source"])}">DSH披露来源</a> · 方法 {esc(run["method_version"])} / Executive 1.0</footer></main>'
    data=json.dumps({k:v for k,v in run.items() if k not in ('previous_snapshot','requests')},ensure_ascii=False).replace('<','\\u003c').replace('&','\\u0026')
    s+=f'<script type="application/json" id="report-data">{data}</script>'
    s=s.replace('<a href="#appendix">数据附录</a>','<a href="#scale">规模估算</a><a href="#appendix">数据附录</a>')
    return s+'''<script>document.getElementById('download').addEventListener('click',()=>{const b=new Blob([document.getElementById('report-data').textContent],{type:'application/json'});const u=URL.createObjectURL(b);const a=document.createElement('a');a.href=u;a.download='harness-weekly-data.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000)});</script></body></html>'''
