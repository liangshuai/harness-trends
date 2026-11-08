"""Scripted provenance and source checks for every report data block."""
from datetime import datetime,timezone
import hashlib
from .collect import FetchError


def check_historical_sources(client,config):
    anchors=[('DSH历史披露',config['disclosure']['as_of'],config['disclosure']['source'])]
    anchors.extend((pid+'历史校准',config['models_v2'][pid]['as_of'],config['models_v2'][pid]['source']) for pid in ('codex','claude'))
    result=[]
    for name,asof,url in anchors:
        row={'name':name,'as_of':asof,'source':url,'checked_at':datetime.now(timezone.utc).isoformat(),
             'policy':'保留原披露日期，作为固定历史锚点；重抓来源不等于获得新的运营披露。'}
        try:
            body=client.get(url)
            row.update(status='source_retrieved',sha256=hashlib.sha256(body.encode()).hexdigest())
        except FetchError as exc:row.update(status='source_unavailable',reason=str(exc))
        result.append(row)
    return result


def inventory(run):
    out=[]
    def add(name,kind,status,source):out.append({'name':name,'refresh':kind,'status':status,'source':source})
    add('Token、请求数、四家份额、Top 10及其余应用','每次从OpenRouter API采集并计算',run['openrouter_current']['status'],'OpenRouter app-rankings')
    add('周环比与四周趋势','按日期回取历史窗口并计算',str(sum(w['status']=='ok' for w in run['openrouter_trend']))+'/'+str(len(run['openrouter_trend']))+'窗口完整','OpenRouter app-rankings')
    for pid,p in run['products'].items():
        add(p['name']+'下载与环比','npm逐日数据自动汇总','ok' if p['downloads_current'] is not None and p['downloads_previous'] is not None else 'missing','npm downloads API')
        add(p['name']+'仓库、发布单元及参与账号','GitHub发现、manifest验证、账号去重',p['github']['status'],'GitHub REST + raw manifests')
    catalog=run['model_v2_inputs']['pi_catalog']
    add('Pi目录扩展包及作者字段','官网全分页抓取、跨包去重',catalog['status'],catalog['source'])
    add('用户等效情景、插件作者及插件估算','根据当轮输入与固定参数重新计算','computed','models_v2 + config.json')
    for a in run.get('historical_source_checks',[]):add(a['name'],'固定历史披露；每次重抓源页检查，不冒充本周统计',a['status'],a['source'])
    for a in run.get('user_disclosures',[]):add(a['label'],'重抓官方嵌入源并核对产品范围、数值与周期；保留发帖日期',a['status'],a['source'])
    add('图表、标题摘要与HTML','只读取当轮结构化快照渲染','generated','executive.py + render_estimates_v2.py')
    return out
