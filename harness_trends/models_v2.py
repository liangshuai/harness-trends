"""Separate user and ecosystem models; no cross-product DSH download scaling."""
from datetime import date
import hashlib
import json
import math
import os
from statistics import median
import time
from urllib.parse import urlencode
from .collect import FetchError, npm_downloads
from .metrics import package_total
from .catalogs import collect_pi_catalog


def collect_inputs(client,products,config):
    spec=config['models_v2'];out={'owners':{},'baselines':{},'version':spec['version']}
    token=os.getenv('GITHUB_TOKEN') or os.getenv('GH_TOKEN')
    for p in products:
        items={};errors=[];total=None
        for page in range(1,spec['owner_pages']+1):
            calls_before=client.github_calls
            url='https://api.github.com/search/repositories?'+urlencode({'q':p['query'],'per_page':100,'sort':'stars','order':'desc','page':page})
            try:
                data=client.json(url,token=token)
                total=data.get('total_count')
                if not isinstance(data.get('items'),list):raise FetchError('搜索缺少items')
                for repo in data['items']:
                    if repo['full_name'].lower()!=p['repo'].lower():items[repo['id']]=repo
                if len(data['items'])<100:break
            except FetchError as exc:
                errors.append(str(exc));break
            if client.github_calls>calls_before:time.sleep(2.1)
        owners={r['owner']['id']:r['owner'] for r in items.values()}
        out['owners'][p['id']]={'sample_repos':len(items),'unique_publishers':len(owners),
            'personal_publishers':sum(x['type']=='User' for x in owners.values()),'candidate_total':total,
            'owner_repo_ratio':len(owners)/len(items) if items else None,
            'publisher_ids':sorted(owners),'repo_ids':sorted(items),'errors':errors,
            'selection':'按stars排序的前500个候选仓库；未逐一验证，非全市场随机样本'}
        print(f'  {p["name"]} 发布者核验：{len(items)}仓库 / {len(owners)}个去重发布者身份',flush=True)
    for pid in ('codex','claude'):
        s=spec[pid];p=next(p for p in products if p['id']==pid)
        out['baselines'][pid]=npm_downloads(client,p['npm'][0],date.fromisoformat(s['download_start']),date.fromisoformat(s['download_end']))
    print('  采集Pi官网完整目录与作者字段…',flush=True)
    out['pi_catalog']=collect_pi_catalog(client,config.get('catalogs',{}).get('pi',{'url':'https://pi.dev/packages'}))
    return out


def interval(values,method,evidence,confidence='低'):
    if not values or any(v is None for v in values):
        return {'reference':None,'low':None,'high':None,'method':method,'evidence':evidence,'confidence':'输入缺失'}
    return {'reference':values[1],'low':min(values),'high':max(values),'method':method,'evidence':evidence,'confidence':confidence}


def npm_equivalent(downloads):
    values=([downloads*h/r*m for h,r,m in [(0.1,6,1.3),(0.25,3,1.6),(0.4,2,2.2)]]
            if downloads is not None else None)
    return interval(values,'周下载 × 人类下载占比 ÷ 重复下载频次 × 月周活系数',
        '四家共用人类占比10%/25%/40%、周重复下载6/3/2次、月周活1.3/1.6/2.2；不除以未知渠道覆盖率。仅为下载用户等效情景，非实际渠道MAU或总体人数。')


def apply(run,config):
    spec=config['models_v2'];inputs=run['model_v2_inputs'];d=config['disclosure']
    for pid,p in run['products'].items():
        current=p['downloads_current'];g=p['github'];s=spec.get(pid,{})
        p['npm_user_equivalent']=npm_equivalent(current)
        if pid=='codex':
            base=inputs['baselines'][pid].get('total')
            values=[s['wau_anchor']*s['mau_per_wau'][i]*(current/base)**s['growth_elasticity'][i] for i in range(3)] if current is not None and base else None
            users=interval(values,'自身WAU锚点 × 月周活转换 × 自身下载增幅的弹性',f'2026-06-02官方披露WAU超过500万；按500万作保守锚。自身基准下载{base}，当期{current}。WAU不是MAU；转化与弹性是假设。')
            if s.get('current_estimate_enabled',True) is False:
                users=interval(None,'旧锚点总体用户情景已停用',
                    '6月Codex单独WAU是历史点；10月4000万为Codex与ChatGPT Work合计活跃用户，不能替换成Codex单独WAU或MAU。最新合计信息在公开披露表单列。')
        elif pid=='claude':
            base=inputs['baselines'][pid].get('total')
            values=[s['arr_anchor']/12/s['monthly_spend'][i]/s['paid_share'][i]*(current/base)**s['growth_elasticity'][i] for i in range(3)] if current is not None and base else None
            users=interval(values,'自身年化收入 ÷ 月度ARPU ÷ 付费活跃占比 × 自身分发趋势',f'2026-02-12官方Code年化收入超过25亿美元，按25亿锚定；月度ARPU40/80/150美元及付费占比为假设，含企业/API折算偏差。基准下载{base}。这是活跃席位等效量，非已验证MAU。')
        elif pid=='pi':
            values=[current*s['human_download_fraction'][i]/s['downloads_per_wau'][i]/s['npm_user_coverage'][i]*s['mau_per_wau'][i] for i in range(3)] if current is not None else None
            users=interval(values,'自身下载 × 人类占比 ÷ 重复下载频次 ÷ npm覆盖 × 月周活转换','无官方绝对用户锚点；人类下载占比10%–40%、每活跃用户周下载2–6次、npm覆盖70%–100%均为情景假设。')
        else:
            users=interval([d['mau']]*3,'保留厂商MAU披露点，不用下载推算','2026-11-04，548万MAU；媒体转述厂商披露，范围按其官方API口径，非当前全渠道人数。','厂商披露')
        owner=inputs['owners'][pid];density=owner.get('owner_repo_ratio')
        checked=g.get('checked_repos',0);verified=g.get('verified_repos',0)
        typical=median([len(r['artifacts']) for r in g.get('repos',[]) if r['status']=='verified']) if verified else None
        projects=g['candidate_total']*verified/checked if checked and g.get('candidate_total') is not None else None
        if pid=='dsh':
            plugin_values=[d['plugins_union']]*3
            project_values=[d['plugins_union']/typical]*3 if typical else None
            plugin_method='厂商公开插件去重总数'
        elif pid=='pi':
            catalog=inputs.get('pi_catalog',{})
            count=catalog.get('total')
            plugin_values=[count]*3 if count is not None else None
            project_values=[count/typical]*3 if count is not None and typical else None
            plugin_method='Pi官网Package Catalog的未筛选总数，优先于GitHub外推'
        else:
            project_values=[projects/c for c in spec['plugins']['discovery_coverage']] if projects is not None else None
            plugin_values=[v*typical for v in project_values] if project_values and typical else None
            plugin_method='自身GitHub命中 × 样本有效率 × 每仓发布单元中位数 ÷ 发现覆盖'
        plugins=interval(plugin_values,plugin_method,'不用单个大型marketplace拉高平均数；中位数会漏掉长尾多插件仓库。覆盖率50%/75%/100%是显式假设。','厂商披露估算' if pid=='dsh' else '低')
        dev_values=[project_values[i]*density*spec['plugins']['humans_per_publisher'][i] for i in range(3)] if project_values and density else None
        developers=interval(dev_values,'插件项目数 × 去重发布者/仓库比例 × 每发布者作者人数',f'在{owner["sample_repos"]}个候选仓库内对owner ID取并集，得到{owner["unique_publishers"]}个发布者身份（含组织）；每身份1/1.15/1.4名作者为假设。发布者≠作者，头部样本重复率未必可迁移至长尾。')
        if pid=='pi':
            catalog=inputs.get('pi_catalog',{})
            plugins=interval(plugin_values,plugin_method,
                f'来源{catalog.get("source","https://pi.dev/packages")}；采集于{catalog.get("observed_at","未知")}。单位为官网收录扩展包，包含多种资源，不是纯extension数；不覆盖未收录或私有包。','官网目录观测' if plugin_values else '目录采集失败')
            if catalog.get('observed_authors') is not None and catalog.get('collected_packages',0)>0:
                authors=catalog['observed_authors']
                developers=interval([authors]*3,'官网全目录作者字段跨包去重',
                    f'从{catalog["collected_packages"]}个包逐页提取author标签并取并集，得到{authors}个作者身份。'+
                    ('目录完整。' if catalog.get('authors_complete') else '本轮目录不完整，该数仅为已观察到的作者标签数，不是总体估计。')+
                    '未验证为自然人；同人多账号和组织/共享身份仍可能影响人数。',
                    '目录作者身份观测' if catalog.get('authors_complete') else '部分目录作者身份观测')
        p['scale_estimates']={'users':users,'developers':developers,'plugins':plugins,'a_plugins':plugins['reference'],'a_developers':developers['reference'],'model_version':'2.0'}
        p['developer_estimate_status']='publisher_dedup_model_v2_low_confidence'
        p['a_candidate_projection']=developers['reference'];p['b_reference']=developers['reference']
        p['b_a_scale_ratio']=None
        p['b_scenarios']=[{'scenario':k,'alpha':a,'value':developers[k],'mau':users[k],'plugins':plugins[k]} for a,k in [(None,'low'),(1.0,'reference'),(None,'high')]]
    run['estimation_model_version']='2.0'
    return run
