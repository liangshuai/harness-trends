"""Parse explicitly registered disclosures with product scope and period intact."""
from datetime import datetime,timezone
import html
import re
from urllib.parse import urlencode
from .collect import FetchError


def parse_x_disclosure(payload):
    block=payload.get('html','')
    match=re.search(r'<p\b[^>]*>(.*?)</p>',block,re.S)
    text=html.unescape(re.sub('<[^>]+>',' ',match.group(1))) if match else ''
    text=re.sub(r'\s+',' ',text).strip()
    # Only the observed "reached/high of ... active users" clause is eligible;
    # projections elsewhere in the tweet must not replace a disclosure.
    number=re.search(r'(?:reached|high\s+of)\s+(\d+(?:\.\d+)?)\s*m(?:illion)?\s+(weekly\s+)?active\s+users',text,re.I)
    if not number:raise FetchError('原帖未识别到已达到的活跃用户数字')
    combined='codex' in text.casefold() and ('chatgpt work' in text.casefold() or re.search(r'codex\s*&\s*work',text,re.I))
    return {'value':int(float(number.group(1))*1000000),'period':'WAU' if number.group(2) else 'active_window_unspecified',
            'scope':['codex','chatgpt_work'] if combined else ['codex'],'text':text,'author':payload.get('author_name')}


def collect_user_disclosures(client,config):
    result=[]
    for entry in config.get('user_disclosures',[]):
        row=dict(entry,checked_at=datetime.now(timezone.utc).isoformat(),status='registered_historical')
        try:
            url='https://publish.twitter.com/oembed?'+urlencode({'url':entry['source']})
            data=parse_x_disclosure(client.json(url))
            if set(data['scope'])!=set(entry['scope']):raise FetchError('来源产品范围与登记范围不符，停止自动覆盖')
            row.update(data,status='source_verified',verification_url=url)
        except FetchError as exc:
            row.update(status='verification_unavailable',reason=str(exc))
        result.append(row)
    return result


def apply_population_scope(run,config):
    policy=config.get('user_population_policy',{}).get('codex',{})
    if policy.get('scope')!=['codex','chatgpt_work']:return run
    anchor=next((r for r in run.get('user_disclosures',[]) if r['id']==policy.get('anchor_disclosure_id')),None)
    if anchor is None or set(anchor['scope'])!={'codex','chatgpt_work'}:return run
    value=anchor['value']
    estimate={'reference':value,'low':value,'high':value,'period':anchor['period'],
              'scope':anchor['scope'],'report_label':policy['label'],'as_of':anchor['as_of'],'source':anchor['source'],
              'confidence':'公开信息 / 报告合并口径',
              'method':'按本报告约定，将Codex与ChatGPT Work统一为用户规模分析对象；合计数只计一次',
              'evidence':'采用'+anchor['as_of']+'公开合计活跃人数，不再按6月旧锚点外推。原帖未明确周期时，不改写成DAU、WAU或MAU。'}
    run['products']['codex']['scale_estimates']['users']=estimate
    run['user_population_policy']=config['user_population_policy']
    for scenario in run['products']['codex'].get('b_scenarios',[]):
        scenario['mau']=None
        scenario['active_users']=value
    return run
