from .render_methodology import esc,table


def render_scales(run,config):
    from .executive import number,dot,heading,NAMES,COLORS
    from .models_v2 import npm_equivalent
    products=run['products'];spec=config['models_v2'];d=config['disclosure']
    s='<section id="scale">'+heading('SCALE ESTIMATES / MODEL 2.0','用户、插件作者与插件规模估算','独立模型 · 参考值与情景范围')
    s+='<div class="scope"><strong>用户口径已拆开：</strong>四家同列的用户数字仅为相同参数下的npm下载用户等效情景，不代表真实MAU、DAU或全渠道规模。厂商披露另列，禁止混排。插件作者由去重发布者推导，仍是低可信度估计；范围均不是置信区间。</div>'
    rows=[]
    for pid,p in products.items():
        row=[dot(pid)+esc(NAMES[pid])]
        for field in ('users','developers','plugins'):
            e=npm_equivalent(p.get('downloads_current')) if field=='users' else p['scale_estimates'][field]
            row.append(f'<strong>{number(e["reference"])}</strong><br><small class="muted">{number(e["low"])} — {number(e["high"])} · {esc(e["confidence"])}</small>')
            if pid=='pi' and field=='plugins':row[-1]+='<br><small class="muted">官网收录扩展包，含多种资源</small>'
        rows.append(row)
    s+=table(['Harness','npm下载用户等效情景（非总体）','公开插件作者/维护者估算','公开插件数量估算'],rows)
    catalog=run.get('model_v2_inputs',{}).get('pi_catalog',{})
    if catalog:
        s+='<p class="footnote">Pi采用<a href="https://pi.dev/packages">官网Package Catalog</a>的未筛选总数，采集时间 '+esc(catalog.get('observed_at','—'))+'；这是当次目录快照，不冒充用量窗口结束日的历史数量。已逐页读取 '+str(catalog.get('collected_packages',0))+' 个去重包；目录状态 '+esc(catalog.get('status','missing'))+'。</p>'
    s+='<p class="footnote">用户等效情景统一采用：周下载×25%÷每人每周3次×1.6；它只是相同假设下的分发活动换算。真实人类占比、重复下载及未下载的既有活跃用户均未知，不能据此认定谁的真实用户更多。</p>'
    disclosure_rows=[]
    registered=run.get('user_disclosures',config.get('user_disclosures',[]))
    primary=next((r for r in registered if r['id']=='codex-work-40m-primary'),None)
    population_policy=config.get('user_population_policy',{}).get('codex',{})
    if primary:
        disclosure_rows.append([esc(population_policy.get('label',primary['label'])),'WAU / 周活' if primary.get('period')=='WAU' else '活跃用户（窗口未明确）',number(primary['value']),
            esc(primary['as_of'])+'；合计口径 · <a href="'+esc(primary['source'])+'">Tibo原帖</a>'])
    disclosure_rows.extend([
        ['Codex（历史单品数据）','历史WAU / 周活','超过'+number(spec['codex']['wau_anchor']),esc(spec['codex']['as_of'])+'；不是当前人数'],
        ['DSH','DAU / 日活',number(d['dau']),esc(d['as_of'])+'；官方API用户范围'],
        ['DSH','MAU / 月活',number(d['mau']),esc(d['as_of'])+'；月窗口未明示']])
    s+='<div class="panel"><h3>用户规模公开信息</h3>'+table(['产品范围','指标','公开数值','日期与来源'],disclosure_rows)
    if primary:
        secondary=next((r for r in registered if r['id']=='codex-work-40m-commentary'),None)
        s+='<p class="footnote">本报告按约定将Codex与ChatGPT Work作为同一个用户规模分析对象，合计人数只计一次。此处采用10月7日4000万活跃用户作为参考，保留披露日期，不自动外推成11月新实测人数。Tibo原帖未说明活跃窗口；'
        s+=('<a href="'+esc(secondary['source'])+'">Peter Gostev</a>将其表述为周活，年底7000万和次年3月1亿是其预测，不计入已观测数据。' if secondary else '原帖未说明活跃窗口。')+'</p>'
    s+='<p class="footnote">月活不是日活。DSH桌面、源码等使用途径不会完整表现为npm下载，故不能拿npm用户等效量直接与披露人数排名。Pi全渠道覆盖率尚未取得证据。</p></div><div class="grid">'
    for field,title in [('developers','公开插件作者 / 维护者估算'),('plugins','公开插件数量估算')]:
        maximum=max([p['scale_estimates'][field]['high'] or 0 for p in products.values()]+[1])
        s+=f'<div class="panel"><h3>{title}</h3><p class="sub">彩色：参考值；灰色：情景上界</p>'
        for pid,p in sorted(products.items(),key=lambda x:x[1]['scale_estimates'][field]['reference'] or -1,reverse=True):
            e=p['scale_estimates'][field]
            s+=f'<div class="rank-row"><div class="rank-name">{dot(pid)}{esc(NAMES[pid])}</div><div class="bar-pair"><div class="bar-old" style="width:{(e["high"] or 0)/maximum*100:.3f}%"></div><div class="bar-current" style="width:{(e["reference"] or 0)/maximum*100:.3f}%;background:{COLORS[pid]}"></div></div><div class="rank-number"><strong>{number(e["reference"])}</strong><small class="muted">{esc(e["confidence"])}</small></div></div>'
        s+='</div>'
    s+='<div class="panel"><h3>跨仓库去重依据</h3><p class="sub">发布者ID取并集，已将同一发布者的多个仓库折叠；不再按contributors密度放大。</p>'
    rows=[]
    for pid,o in run['model_v2_inputs']['owners'].items():
        rows.append([esc(NAMES[pid]),str(o['sample_repos']),str(o['unique_publishers']),f'{o["owner_repo_ratio"]:.1%}' if o['owner_repo_ratio'] is not None else '—'])
    s+=table(['Harness','仓库样本','去重发布者身份','身份 / 仓库'],rows)+'<p class="footnote">这些是按stars排序的候选仓库，含组织身份，尚非代表性随机样本，也未逐项核实owner即作者。重复率是观测量；每身份1/1.15/1.4名作者、发现覆盖率等仍是假设。故作者估计可信度低。</p></div></div>'
    s+='<details><summary>模型v2公式、来源、假设与局限</summary>'
    s+='<p><strong>用户规模依据与情景参数（各自口径，不直接排名）：</strong>Codex采用包含Work的报告合并口径；其他产品的收入或分发换算仍只作情景审计，不作为已验证总体人数。</p>'
    for pid,p in products.items():
        s+='<h3>'+esc(NAMES[pid])+'</h3>'
        for field,label in [('users','用户'),('developers','插件作者'),('plugins','插件')]:
            e=p['scale_estimates'][field]
            s+=f'<p><strong>{label}：</strong>{esc(e["method"])}。<span class="muted">{esc(e["evidence"])}</span></p>'
    s+='<div class="formula">Codex用户参考：读取已核验的Codex与ChatGPT Work合计活跃人数，只计一次；不转换未知活跃周期\nClaude Code：25亿美元年化收入 / 12 / 月均收入ARPU / 付费活跃占比 × 自身分发趋势^弹性\nPi：自身周下载 × 人类下载占比 / 重复下载频次 / npm覆盖率 × MAU/WAU\n插件项目：自身查询命中 × manifest样本有效率 / 发现覆盖率\n插件发布单元：插件项目 × 每仓发布单元中位数（避免单个大目录拉高均值）\n插件作者：项目数 × 去重发布者/仓库 × 每发布者作者数\nDSH：插件直接使用披露的去重总量，以每仓发布单元中位数折回项目数，再估作者。</div>'
    s+=f'<p><a href="{esc(spec["codex"]["source"])}">Codex官方WAU锚点，2026-06-02</a> · <a href="{esc(spec["claude"]["source"])}">Claude Code官方收入锚点，2026-02-12</a> · <a href="{esc(config["disclosure"]["source"])}">DSH披露</a></p>'
    s+='<p class="footnote">来源日期较旧，不能直接代表11月。分发弹性、ARPU、付费活跃占比、人类下载占比、发现覆盖、作者人数均为可审计的研究假设，尚无独立样本验证。不同产品及不同角色的用户有交集，估算不能相加成全球人数。参数固定在config.json；每周更新数据，不自动调整参数使结果符合预期。</p>'
    s+='<details><summary>查看本轮完整参数</summary><pre class="formula">'+esc(__import__('json').dumps(spec,ensure_ascii=False,indent=2))+'</pre></details></details></section>'
    return s
