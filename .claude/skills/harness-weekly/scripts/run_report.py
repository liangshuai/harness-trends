#!/usr/bin/env python3
"""Generate a weekly public-data report; Python 3.10+, no third-party dependencies."""
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

from harness_trends.collect import Client, FetchError, github_ecosystem, npm_downloads, openrouter_window, official_repo
from harness_trends.metrics import compute, package_total
from harness_trends.render import render
from harness_trends.models_v2 import collect_inputs, apply as apply_models_v2
from harness_trends.pipeline import check_historical_sources, inventory
from harness_trends.user_disclosures import collect_user_disclosures, apply_population_scope
from harness_trends.marketplaces import collect_marketplaces
from harness_trends.plugin_rankings import collect_plugin_rankings
from harness_trends.changelog import collect_product_updates
from harness_trends.markdown_report import render_markdown
from harness_trends.executive import NAMES

ROOT=Path(__file__).resolve().parent
METHOD='0.1.0'


def load_env(path):
    """Literal dotenv only: never source shell code or overwrite existing environment."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line=line.strip()
        if not line or line.startswith('#'):
            continue
        key, sep, value=line.removeprefix('export ').partition('=')
        key=key.strip()
        if sep and key in ('OPENROUTER_API_KEY','GITHUB_TOKEN','GH_TOKEN'):
            value=value.strip()
            if len(value)>1 and value[0]==value[-1] and value[0] in ('"',"'"):
                value=value[1:-1]
            if value:
                os.environ.setdefault(key,value)


def atomic_json(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value,ensure_ascii=False,indent=2))
    temp.replace(path)


def archive_dir(reports, end):
    """One folder per weekly window; every round's reports are filed here, never discarded."""
    folder=reports/'archive'/str(end)
    folder.mkdir(parents=True,exist_ok=True)
    return folder


def archive_current(reports, root):
    """Before each run: file the existing latest reports under their own window so no round is lost."""
    for name in ('latest.html','latest.md'):
        if (reports/name).exists():
            break
    else:
        return
    try:
        end=json.loads((root/'data/latest.json').read_text())['window']['end']
    except (OSError,ValueError,KeyError):
        return
    folder=archive_dir(reports,end)
    for name in ('latest.html','latest.md'):
        source=reports/name
        if source.exists():
            (folder/('report'+source.suffix)).write_text(source.read_text())


def previous_snapshot(root, end, signature):
    possibilities=[]
    for path in (root/'data/runs').glob('*.json'):
        try:
            item=json.loads(path.read_text())
            age=(end-date.fromisoformat(item['window']['end'])).days
            if 6<=age<=10 and item.get('method_version')==METHOD:
                possibilities.append(item)
        except (ValueError,KeyError):
            continue
    if not possibilities:
        return None,False
    chosen=max(possibilities,key=lambda x:x['generated_at'])
    return chosen,chosen.get('collection_signature')==signature


def settled_end(client, end):
    """Popular independent packages both zero is a settlement warning, not market collapse."""
    from urllib.parse import quote
    original=end
    for _ in range(3):
        counts=[]
        for package in ('@openai/codex','@anthropic-ai/claude-code'):
            url=f'https://api.npmjs.org/downloads/point/{end}/'+quote(package,safe='@')
            try:
                data=client.json(url,fresh=True)
                if data.get('start')!=str(end) or data.get('end')!=str(end) or not isinstance(data.get('downloads'),int):
                    return original,'npm结算探测未能确认，按请求窗口取数。'
                counts.append(data['downloads'])
            except FetchError:
                return original,'npm结算探测失败，按请求窗口取数并保留来源状态。'
        if any(v>0 for v in counts):
            note=(f'npm在{original}的两个高下载主包均返回零，疑似尚未结算；已统一回退至{end}。' if end!=original else '最新完整UTC日已检测到有效npm下载。')
            return end,note
        end-=timedelta(days=1)
    raise RuntimeError('连续三个UTC日的npm哨兵包均返回零；暂不发布可能不完整的周报。')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--end',type=date.fromisoformat,help='七天窗口结束日，默认最近完整UTC日')
    parser.add_argument('--offline',action='store_true',help='只读取已存在的公开响应缓存')
    parser.add_argument('--refresh',action='store_true',help='忽略跨轮缓存，重新采集全部运行数据；同轮重复请求仍去重')
    parser.add_argument('--candidate-limit',type=int,help='每家从搜索前100条内检查的候选数')
    parser.add_argument('--contributor-limit',type=int,help='每家读取贡献者的仓库上限')
    parser.add_argument('--render-only',type=Path,help='从一份已有run JSON重建HTML，不联网')
    args=parser.parse_args()
    config=json.loads((ROOT/'config.json').read_text())
    load_env(ROOT/'.env')
    reports=ROOT/'reports'; reports.mkdir(exist_ok=True)
    if args.render_only:
        run=json.loads(args.render_only.read_text())
        folder=archive_dir(reports,run['window']['end'])
        page=render(run,run.get('configuration',config))
        (folder/'report.html').write_text(page)
        (reports/'latest.html').write_text(page)
        markdown=render_markdown(run,run.get('configuration',config))
        (folder/'report.md').write_text(markdown)
        (reports/'latest.md').write_text(markdown)
        print('已重建 reports/latest.html 与 reports/latest.md')
        return 0
    if args.offline and args.refresh:parser.error('--offline 与 --refresh 不能同时使用')
    settings=config['collection'].copy()
    if args.candidate_limit is not None: settings['candidate_limit']=args.candidate_limit
    if args.contributor_limit is not None: settings['contributor_repo_limit']=args.contributor_limit
    if not 1<=settings['candidate_limit']<=100 or not 1<=settings['contributor_repo_limit']<=100:
        parser.error('candidate-limit 和 contributor-limit 必须在1–100之间')
    config['collection']=settings
    archive_current(reports,ROOT)
    end=args.end or datetime.now(timezone.utc).date()-timedelta(days=1)
    if end>=datetime.now(timezone.utc).date():
        parser.error('只能统计已完成的UTC日')
    settlement_note='用户指定统计日期；未自动回退。'
    if args.end is None:
        probe=Client(ROOT,ROOT/'data/preflight'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S'),cache_hours=0,offline=args.offline)
        end,settlement_note=settled_end(probe,end)
        print(settlement_note,flush=True)
    start=end-timedelta(days=6)
    previous_start, previous_end=start-timedelta(days=7),start-timedelta(days=1)
    disclosure_end=date.fromisoformat(config['disclosure']['as_of'])
    disclosure_start=disclosure_end-timedelta(days=6)
    now=datetime.now(timezone.utc)
    run_id=f'{end}_{now.strftime("%Y%m%dT%H%M%SZ")}'
    raw_dir=ROOT/'data/raw'/run_id
    client=Client(ROOT,raw_dir,settings['github_request_budget'],0 if args.refresh else settings['cache_hours'],args.offline)
    signature=hashlib.sha256(json.dumps({'settings':settings,'queries':[(p['id'],p['query']) for p in config['products']],
        'method':METHOD,'models':config.get('models_v2'),'catalogs':config.get('catalogs')},sort_keys=True).encode()).hexdigest()
    run={'id':run_id,'method_version':METHOD,'generated_at':now.isoformat(),'collection_signature':signature,'settlement_note':settlement_note,'refresh_mode':'live' if args.refresh else ('offline' if args.offline else 'cached'),
         'window':{'start':str(start),'end':str(end)},'previous_window':{'start':str(previous_start),'end':str(previous_end)},
         'anchor_window':{'start':str(disclosure_start),'end':str(disclosure_end)},'configuration':config,'products':{}}
    for product in config['products']:
        print(f'采集 {product["name"]}：npm窗口与公开插件样本…',flush=True)
        p={'name':product['name'], 'npm_current':[], 'npm_previous':[]}
        for package in product['npm']:
            p['npm_current'].append(npm_downloads(client,package,start,end))
            p['npm_previous'].append(npm_downloads(client,package,previous_start,previous_end))
        if product['id']=='dsh':
            p['npm_anchor']=[npm_downloads(client,package,disclosure_start,disclosure_end) for package in product['npm']]
        p['github']=github_ecosystem(client,product,settings)
        run['products'][product['id']]=p
        print(f'  验证插件 {p["github"].get("verified_artifacts",0)}；参与账号 {p["github"].get("contributor_count")}；采集状态 {p["github"]["status"]}',flush=True)
    cal_path=ROOT/'data/calibration.json'
    if cal_path.exists():
        calibration=json.loads(cal_path.read_text())
        if calibration.get('method_version') != METHOD or calibration.get('disclosure_as_of') != config['disclosure']['as_of']:
            calibration={**calibration,'accounts_per_plugin':None,
                         'note':'已有校准与当前方法或披露日期不一致；暂停B账号估算，需要人工建立新校准。'}
    else:
        gh=run['products']['dsh']['github']
        n=gh.get('contributor_plugin_count',0)
        a=gh.get('contributor_count')
        calibration={'created_at':run['generated_at'],'run_id':run_id,'method_version':METHOD,
                     'disclosure_as_of':config['disclosure']['as_of'],'accounts':a,'plugins':n,
                     'repos':[r['repo'] for r in gh.get('repos',[]) if r.get('contributors_complete') and not r.get('path_ambiguous')],
                     'accounts_per_plugin':a/n if a is not None and n else None,
                     'note':'当前受限公开样本密度迁移到历史公开插件总量，是未经独立验证的假设。'}
        if calibration['accounts_per_plugin'] is not None:
            atomic_json(cal_path,calibration)
    run['calibration']=calibration
    print('读取 OpenRouter 指定窗口（未配密钥时留空）…',flush=True)
    run['openrouter_current']=openrouter_window(client,config['products'],config['openrouter'],start,end)
    run['openrouter_previous']=openrouter_window(client,config['products'],config['openrouter'],previous_start,previous_end)
    run['openrouter_trend'] = []
    for offset in range(config['openrouter'].get('trend_weeks',4)-1,-1,-1):
        trend_end=end-timedelta(days=7*offset)
        trend_start=trend_end-timedelta(days=6)
        if offset == 0:
            trend=run['openrouter_current']
        elif offset == 1:
            trend=run['openrouter_previous']
        else:
            trend=openrouter_window(client,config['products'],config['openrouter'],trend_start,trend_end)
        run['openrouter_trend'].append(trend)
    compute(run,config)
    if config.get('models_v2'):
        print('模型v2：采集跨仓库发布者并集及产品自身历史基准…',flush=True)
        run['model_v2_inputs']=collect_inputs(client,config['products'],config)
        apply_models_v2(run,config)
    print('检查历史披露源并生成全报告数据清单…',flush=True)
    run['historical_source_checks']=check_historical_sources(client,config)
    run['user_disclosures']=collect_user_disclosures(client,config)
    apply_population_scope(run,config)
    print('采集插件市场目录计数、官方仓库贡献者与窗口内发布…',flush=True)
    run['marketplaces']=collect_marketplaces(client,config)
    print('采集四家插件 Top 10（安装量 / 下载量 / 共享目录位置）…',flush=True)
    run['plugin_rankings']=collect_plugin_rankings(client,config)
    run['official_repos']={p['id']:official_repo(client,p) for p in config['products']}
    run['product_updates']=collect_product_updates(client,config['products'],run['window'])
    for pid,row in run['official_repos'].items():
        print(f'  {NAMES.get(pid,pid)} 官方仓库贡献者 {row.get("contributors")}（{row["status"]}）；'
              f'窗口内发布 {len(run["product_updates"].get(pid,{}).get("releases",[]))} 个',flush=True)
    editorial_path=ROOT/'data/editorial'/f'{end}.json'
    run['editorial']=json.loads(editorial_path.read_text()) if editorial_path.exists() else None
    run['data_inventory']=inventory(run)
    previous,same=previous_snapshot(ROOT,end,signature)
    run['previous_snapshot']=previous
    run['same_collection_config']=same
    history=[]
    daily_runs={}
    for path in sorted((ROOT/'data/runs').glob('*.json')):
        try:
            old=json.loads(path.read_text())
            if old['window']['end']>=str(end) or old.get('collection_signature')!=signature:
                continue
            key=(old['window']['end'],old.get('method_version'))
            if key not in daily_runs or old['generated_at']>daily_runs[key]['generated_at']:
                daily_runs[key]=old
        except (ValueError,KeyError): pass
    for old in sorted(daily_runs.values(),key=lambda x:x['window']['end']):
        for p in old['products'].values():
            history.append({'end':old['window']['end'],'name':p['name'],'downloads':p.get('downloads_current'),
                            'observed':p.get('a_observed'),'b_reference':p.get('b_reference')})
    run['history']=history[-48:]
    run['requests']=client.events
    run['github_api_requests']=client.github_calls
    # Snapshot references do not recursively duplicate full history.
    if run['previous_snapshot']:
        run['previous_snapshot']={k:v for k,v in run['previous_snapshot'].items() if k in ('id','products','window','generated_at','collection_signature')}
    atomic_json(ROOT/'data/runs'/f'{run_id}.json',run)
    atomic_json(ROOT/'data/latest.json',run)
    page=render(run,config)
    folder=archive_dir(reports,end)
    (folder/f'{run_id}.html').write_text(page)
    (folder/'report.html').write_text(page)
    temp=reports/'latest.html.tmp';temp.write_text(page);temp.replace(reports/'latest.html')
    markdown=render_markdown(run,config)
    (folder/f'{run_id}.md').write_text(markdown)
    (folder/'report.md').write_text(markdown)
    temp=reports/'latest.md.tmp';temp.write_text(markdown);temp.replace(reports/'latest.md')
    print(f'完成：{reports/"latest.html"} 与 {reports/"latest.md"}；归档：{folder}',flush=True)
    print(f'运行快照：data/runs/{run_id}.json；GitHub实时请求 {client.github_calls} 次',flush=True)
    return 0 if any(p['downloads_current'] is not None or p['a_observed'] is not None for p in run['products'].values()) else 2


if __name__=='__main__':
    # Exclusive flock releases automatically even when the process is interrupted.
    import fcntl
    with (ROOT/'.run.lock').open('w') as lock:
        try:
            fcntl.flock(lock,fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print('已有报告任务运行中。',file=sys.stderr)
            sys.exit(3)
        sys.exit(main())
