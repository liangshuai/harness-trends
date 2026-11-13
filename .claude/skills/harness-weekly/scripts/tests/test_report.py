import copy
from datetime import date
import json
from pathlib import Path
import tempfile
import unittest

from harness_trends.collect import Client, FetchError, is_human, npm_downloads, openrouter_window
from harness_trends.metrics import compute, package_total, ratio_delta, scale_summary
from harness_trends.render import esc, render
from run_report import archive_current, archive_dir, load_env, previous_snapshot, settled_end, METHOD
from harness_trends.executive import donut
from harness_trends.models_v2 import apply as apply_v2, npm_equivalent
from harness_trends.catalogs import parse_pi_catalog
from harness_trends.marketplaces import parse_dshmarket, parse_mcptop, parse_claude_marketplace
from harness_trends.changelog import collect_product_updates, feature_bullets, parse_changelog, summarize
from harness_trends.markdown_report import render_markdown
from harness_trends.pipeline import check_historical_sources, inventory
from harness_trends.user_disclosures import parse_x_disclosure, apply_population_scope
import re
from unittest.mock import patch


class FakeClient:
    def __init__(self, payload): self.payload=payload
    def json(self, *args, **kwargs): return self.payload


def fixture():
    config=json.loads(Path('config.json').read_text())
    products={}
    for p in config['products']:
        products[p['id']]={'name':p['name'],'npm_current':[{'package':'x','status':'ok','total':200}],
            'npm_previous':[{'package':'x','status':'ok','total':100}],
            'github':{'contributor_count':4,'contributor_plugin_count':2,'contributor_repos_observed':2,
                      'verified_repos':4,'checked_repos':10,'candidate_total':100,'repos':[],
                      'contributor_ids':[1,2,3,4],'publisher_count':2}}
    products['dsh']['npm_anchor']=[{'status':'ok','total':100}]
    run={'products':products,'calibration':{'accounts_per_plugin':2},'openrouter_current':{'status':'ok','products':{p:{'status':'ok','tokens':10,'requests':1} for p in products},'errors':[]},
         'openrouter_previous':{'status':'ok','products':{p:{'status':'ok','tokens':5} for p in products},'errors':[]},
         'window':{'start':'2026-10-30','end':'2026-11-05'},'previous_window':{'start':'2026-10-23','end':'2026-10-29'},
         'generated_at':'2026-11-06','method_version':METHOD}
    return run,config


class ReportTests(unittest.TestCase):
    def test_report_population_policy_counts_codex_work_once_without_mau_relabel(self):
        run,config=fixture();compute(run,config)
        config['user_population_policy']={'codex':{'scope':['codex','chatgpt_work'],'label':'Codex（含 ChatGPT Work）','anchor_disclosure_id':'primary'}}
        run['user_disclosures']=[{'id':'primary','scope':['codex','chatgpt_work'],'value':40000000,
            'period':'active_window_unspecified','as_of':'2026-10-07','source':'https://x.com/thsottiaux/status/example'},
            {'id':'secondary','scope':['codex','chatgpt_work'],'value':40000000,'period':'WAU'}]
        apply_population_scope(run,config)
        estimate=run['products']['codex']['scale_estimates']['users']
        self.assertEqual(estimate['reference'],40000000)
        self.assertEqual(estimate['period'],'active_window_unspecified')
        self.assertEqual(estimate['report_label'],'Codex（含 ChatGPT Work）')
        self.assertTrue(all(s['mau'] is None for s in run['products']['codex']['b_scenarios']))

    def test_combined_codex_work_disclosure_is_not_codex_only_or_forecast(self):
        primary=parse_x_disclosure({'html':'<p>A new high of 40M active users across Codex and ChatGPT Work.</p>'})
        self.assertEqual(primary['value'],40000000)
        self.assertEqual(primary['scope'],['codex','chatgpt_work'])
        self.assertEqual(primary['period'],'active_window_unspecified')
        commentary=parse_x_disclosure({'html':'<p>Codex &amp; Work reached 40m weekly active users. They will reach c.70m by year end.</p>'})
        self.assertEqual(commentary['value'],40000000)
        self.assertEqual(commentary['period'],'WAU')

    def test_historical_source_failure_keeps_dated_anchor_explicit(self):
        class Unavailable:
            def get(self,*args,**kwargs):raise FetchError('HTTP 403')
        run,config=fixture()
        checks=check_historical_sources(Unavailable(),config)
        self.assertEqual(len(checks),3)
        self.assertTrue(all(c['status']=='source_unavailable' for c in checks))
        self.assertEqual(checks[0]['as_of'],config['disclosure']['as_of'])
        self.assertTrue(all('历史锚点' in c['policy'] for c in checks))

    def test_inventory_covers_entire_report_not_only_pi(self):
        run,config=fixture();compute(run,config)
        run['openrouter_trend']=[run['openrouter_current']]*4
        run['model_v2_inputs']={'pi_catalog':{'status':'ok','source':'https://pi.dev/packages'}}
        for p in run['products'].values():p['github']['status']='partial'
        names=' '.join(r['name'] for r in inventory(run))
        for expected in ('Top 10','四周趋势','Codex下载','Claude Code下载','DeepSeek Harness下载','Pi下载','Pi目录','估算','HTML'):
            self.assertIn(expected,names)

    def test_live_refresh_fetches_again_between_runs_but_memoizes_within_run(self):
        class Response:
            status=200;headers={}
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self):return b'{"value":1}'
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with patch('harness_trends.collect.urlopen',return_value=Response()) as request:
                first=Client(root,root/'raw1',cache_hours=0)
                first.json('https://example.com/public');first.json('https://example.com/public')
                self.assertEqual(request.call_count,1)
                second=Client(root,root/'raw2',cache_hours=0)
                second.json('https://example.com/public')
                self.assertEqual(request.call_count,2)

    def test_official_pi_catalog_parser_and_source_precedence(self):
        markup='<h2>All packages</h2><p>1-50 / 5,348</p><article data-package-card="true" data-package-name="@team/a" data-package-types="extension skill"><div class="packages-meta"><span>author-a</span><span>10K/mo</span></div></article>'
        total,entries=parse_pi_catalog(markup)
        self.assertEqual(total,5348)
        self.assertEqual(entries[0]['author'],'author-a')
        self.assertEqual(entries[0]['types'],['extension','skill'])
        run,config=fixture();compute(run,config)
        for p in run['products'].values():p['github']['repos']=[{'status':'verified','artifacts':[{'name':'plugin'}]}]*4
        run['model_v2_inputs']={'baselines':{'codex':{'total':100},'claude':{'total':100}},
            'owners':{p:{'sample_repos':500,'unique_publishers':200,'owner_repo_ratio':0.4} for p in run['products']},
            'pi_catalog':{'source':'https://pi.dev/packages','total':5348,'authors_complete':True,'observed_authors':2476,'collected_packages':5348}}
        apply_v2(run,config)
        self.assertEqual(run['products']['pi']['scale_estimates']['plugins']['reference'],5348)
        self.assertEqual(run['products']['pi']['scale_estimates']['developers']['reference'],2476)
        run['model_v2_inputs']['pi_catalog']={'status':'missing','total':None}
        apply_v2(run,config)
        self.assertIsNone(run['products']['pi']['scale_estimates']['plugins']['reference'])

    def test_npm_equivalent_uses_same_parameters_without_total_market_claim(self):
        dsh=npm_equivalent(826814);pi=npm_equivalent(6418443)
        self.assertAlmostEqual(pi['reference']/dsh['reference'],6418443/826814)
        self.assertIn('非实际渠道MAU或总体人数',dsh['evidence'])
        self.assertIsNone(npm_equivalent(None)['reference'])

    def test_failed_source_not_zero(self):
        self.assertIsNone(package_total([{'status':'missing','total':None}]))
        self.assertIsNone(ratio_delta(2,0))

    def test_npm_rejects_duplicate_or_missing_days(self):
        payload={'downloads':[{'day':'2026-11-01','downloads':3}]*2}
        row=npm_downloads(FakeClient(payload),'x',date(2026,11,1),date(2026,11,2))
        self.assertEqual(row['status'],'missing')
        self.assertIsNone(row['total'])

    def test_human_account_filter(self):
        self.assertFalse(is_human({'id':1,'type':'Bot','login':'x'}))
        self.assertFalse(is_human({'id':1,'type':'User','login':'x[bot]'}))
        self.assertFalse(is_human({'id':1,'type':'Organization','login':'x'}))

    def test_scenario_math_and_four_app_shares(self):
        run,config=fixture();compute(run,config)
        self.assertEqual(run['products']['codex']['a_candidate_projection_diagnostic'],80)
        self.assertIsNone(run['products']['codex']['a_candidate_projection'])
        self.assertIsNone(run['products']['codex']['b_reference'])
        self.assertEqual(run['openrouter_current']['products']['codex']['share_four'],.25)
        self.assertEqual(run['products']['codex']['download_wow'],1)

    def test_missing_or_product_suppresses_all_four_shares(self):
        run,config=fixture();run['openrouter_current']['status']='partial'
        run['openrouter_current']['products']['pi']={'status':'not_visible','tokens':None}
        compute(run,config)
        self.assertTrue(all(p['share_four'] is None for p in run['openrouter_current']['products'].values()))

    def test_no_anchor_yields_no_fabricated_developers(self):
        run,config=fixture();run['calibration']['accounts_per_plugin']=None;compute(run,config)
        self.assertIsNone(run['products']['codex']['b_reference'])

    def test_openrouter_requires_exact_window(self):
        payload={'meta':{'start_date':'wrong','end_date':'2026-11-05'},'data':[]}
        with patch.dict('os.environ',{'OPENROUTER_API_KEY':'test-secret'}):
            row=openrouter_window(FakeClient(payload),[],{},date(2026,10,30),date(2026,11,5))
        self.assertEqual(row['status'],'error')
        self.assertNotIn('test-secret',json.dumps(row))

    def test_no_key_does_not_request(self):
        class NoRequest:
            def json(self,*a,**k): raise AssertionError('must not request')
        with patch.dict('os.environ',{},clear=True):
            self.assertEqual(openrouter_window(NoRequest(),[],{},'a','b')['status'],'missing_key')

    def test_html_embedded_data_cannot_escape_script(self):
        run,config=fixture();run['products']['codex']['name']='</script><script>alert(1)</script>'
        compute(run,config);page=render(run,config)
        self.assertNotIn('</script><script>alert(1)',page)
        self.assertIn('\\u003c/script>',page)
        self.assertIn('不是置信区间',page)

    def test_dotenv_is_literal_and_does_not_override_environment(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'.env';path.write_text('OPENROUTER_API_KEY="$(echo not-executed)"\nGITHUB_TOKEN=new\nIGNORED=value')
            with patch.dict('os.environ',{'GITHUB_TOKEN':'existing'},clear=True):
                load_env(path)
                import os
                self.assertEqual(os.environ['GITHUB_TOKEN'],'existing')
                self.assertEqual(os.environ['OPENROUTER_API_KEY'],'$(echo not-executed)')
                self.assertNotIn('IGNORED',os.environ)

    def test_same_day_or_month_old_is_not_weekly_baseline(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'data/runs').mkdir(parents=True)
            for end in ['2026-11-05','2026-10-01']:
                (root/'data/runs'/f'{end}.json').write_text(json.dumps({'window':{'end':end},'method_version':METHOD,'generated_at':end}))
            self.assertEqual(previous_snapshot(root,date(2026,11,5),'x'),(None,False))

    def test_synchronized_zero_npm_day_rolls_back_whole_window(self):
        class Probe:
            def json(self,url,**kwargs):
                day=url.split('/point/')[1].split('/')[0]
                return {'start':day,'end':day,'downloads':0 if day=='2026-11-06' else 20}
        end,note=settled_end(Probe(),date(2026,11,6))
        self.assertEqual(end,date(2026,11,5))
        self.assertIn('回退',note)

    def test_donut_segments_have_exact_denominator(self):
        svg=donut([('codex','Codex',1),('claude','Claude Code',3)],'4','Token','sample')
        shares=[float(x) for x in re.findall(r'stroke-dasharray="([0-9.]+) ',svg)]
        self.assertEqual(shares,[25,75])
        self.assertEqual(sum(shares),100)

    def test_scale_summary_covers_all_three_dimensions_and_both_routes(self):
        run,config=fixture();compute(run,config)
        p=run['products']['codex'];summary=scale_summary(p)
        self.assertEqual(summary['users']['reference'],10960000)
        self.assertEqual(summary['plugins']['reference'],69800)
        self.assertIsNone(summary['developers']['reference'])
        self.assertLess(summary['users']['low'],summary['users']['reference'])
        self.assertGreater(summary['users']['high'],summary['users']['reference'])
        self.assertIsNone(summary['a_developers'])

    def test_pinned_canonical_id_resolves_duplicate_pi_name(self):
        data={'meta':{'start_date':'2026-10-30','end_date':'2026-11-05'},'data':[
            {'app_id':1,'app_name':'pi','total_tokens':'100','total_requests':10},
            {'app_id':2,'app_name':'pi','total_tokens':'3','total_requests':1}]}
        with patch.dict('os.environ',{'OPENROUTER_API_KEY':'test-secret'}):
            result=openrouter_window(FakeClient(data),[{'id':'pi','app_names':['pi']}],{'app_ids':{'pi':1}},date(2026,10,30),date(2026,11,5))
        self.assertEqual(result['status'],'ok')
        self.assertEqual(result['products']['pi']['tokens'],100)

    def test_skill_bundle_matches_repo_sources(self):
        """The skill ships an inlined copy of every script it runs; drift fails here."""
        skill=Path('.claude/skills/harness-weekly/scripts')
        if not skill.exists():
            self.skipTest('skill 内联副本不存在（本测试运行于独立分发的副本内）')
        for relative in ['run_report.py','deploy_report.py','config.json','.env.example','tests/test_report.py']:
            self.assertEqual((skill/relative).read_text(),Path(relative).read_text(),
                             f'skill 内联脚本与仓库版本不一致：{relative}；执行 .claude/skills/harness-weekly/sync.sh 同步')
        if Path('data/app_types.json').exists():
            self.assertEqual((skill/'data/app_types.json').read_text(),Path('data/app_types.json').read_text(),
                             'skill 内联副本与仓库版本不一致：data/app_types.json；执行 .claude/skills/harness-weekly/sync.sh 同步')
        for module in Path('harness_trends').glob('*.py'):
            self.assertEqual((skill/'harness_trends'/module.name).read_text(),module.read_text(),
                             f'skill 内联脚本与仓库版本不一致：harness_trends/{module.name}；执行 sync.sh 同步')

    def test_v2_dedup_and_own_product_anchor_replace_bad_transfer(self):
        run,config=fixture();compute(run,config)
        config['models_v2']['codex']['current_estimate_enabled']=True
        for p in run['products'].values():
            p['github']['repos']=[{'status':'verified','artifacts':[{'name':'plugin'}]}]*4
        run['model_v2_inputs']={'baselines':{'codex':{'total':100},'claude':{'total':100}},
            'owners':{p:{'sample_repos':500,'unique_publishers':200,'owner_repo_ratio':0.4} for p in run['products']}}
        apply_v2(run,config)
        codex=run['products']['codex']['scale_estimates']['users']['reference']
        dsh=run['products']['dsh']['scale_estimates']['developers']['reference']
        self.assertAlmostEqual(dsh,34900*0.4*1.15)
        self.assertLess(codex,20000000)
        config2=copy.deepcopy(config);config2['disclosure']['mau']*=100
        run['products']['dsh']['github']['contributor_count']=1000000
        apply_v2(run,config2)
        self.assertEqual(run['products']['codex']['scale_estimates']['users']['reference'],codex)
        self.assertEqual(run['products']['dsh']['scale_estimates']['developers']['reference'],dsh)
        run['model_v2_inputs']['owners']['dsh']['owner_repo_ratio']=0.2
        apply_v2(run,config)
        self.assertAlmostEqual(run['products']['dsh']['scale_estimates']['developers']['reference'],dsh/2)


class MarkdownReportTests(unittest.TestCase):
    def markdown_run(self):
        run,config=fixture();compute(run,config)
        run['marketplaces']={'claude':{'status':'ok','count':529,'source':'https://claude.com/marketplace/plugins'},
            'codex':{'status':'ok','count':1265,'directory_total':12404,'source':'https://mcptop.com/?source=openai'},
            'dsh':{'status':'ok','count':9463,'source':'https://dshmarket.com/'}}
        run['official_repos']={p:{'status':'ok','contributors':{'claude':56,'codex':478,'dsh':50,'pi':306}[p],
            'repo':{'claude':'anthropics/claude-code','codex':'openai/codex','dsh':'deepseek-ai/deepseek-harness','pi':'earendil-works/pi'}[p]} for p in run['products']}
        run['model_v2_inputs']={'pi_catalog':{'status':'ok','total':5360,'source':'https://pi.dev/packages'}}
        # Ranked-slice fixtures back the market-share column, the Top 10 movement module and the HTML badges.
        run['openrouter_current']['slice_total_tokens']=100
        run['openrouter_current']['ranked_apps_count']=8
        run['openrouter_current']['top_apps']=[
            {'app_id':501,'app_name':'Agent One','rank':1,'total_tokens':40,'total_requests':9},
            {'app_id':502,'app_name':'Claude Code','rank':2,'total_tokens':10,'total_requests':1},
            {'app_id':503,'app_name':'New App','rank':3,'total_tokens':8,'total_requests':2}]
        run['openrouter_previous']['top_apps']=[
            {'app_id':501,'app_name':'Agent One','rank':1,'total_tokens':30,'total_requests':9},
            {'app_id':502,'app_name':'Claude Code','rank':2,'total_tokens':5,'total_requests':1},
            {'app_id':504,'app_name':'Old App','rank':3,'total_tokens':8,'total_requests':2}]
        run['openrouter_trend']=[{'start':'2026-10-23','end':'2026-10-29','products':{p:{'tokens':5} for p in run['products']}},
                                 {'start':'2026-10-30','end':'2026-11-05','products':{p:{'tokens':10} for p in run['products']}}]
        run['product_updates']={'codex':{'repo':'openai/codex','status':'ok','changelog':None,'releases':[
            {'tag':'rust-v0.167.0','version':'0.167.0','published_at':'2026-11-06T01:40:00Z','prerelease':False,
             'html_url':'https://github.com/openai/codex/releases/tag/rust-v0.167.0',
             'body':'## New Features\n\n- Open the agent command center with `codex agents --no-daemon` (#58238).\n\n## Bug Fixes\n\n- Saved chats stay visible after you switch model providers.','body_chars':140}]},
            'claude':{'repo':'anthropics/claude-code','status':'ok','changelog':{'sections':{}},'releases':[]},
            'dsh':{'repo':'deepseek-ai/deepseek-harness','status':'empty','changelog':None,'releases':[]},
            'pi':{'repo':'earendil-works/pi','status':'ok','changelog':None,'releases':[
                {'tag':'v1.5.0','version':'1.5.0','published_at':'2026-11-02T11:05:31Z','prerelease':False,
                 'html_url':'https://github.com/earendil-works/pi/releases/tag/v1.5.0',
                 'body':'Release 1.5.0','body_chars':14}]}}
        return run,config

    def test_marketplace_parsers_read_published_counts(self):
        self.assertEqual(parse_dshmarket('<p>Browse and search <b><span id="count">9463</span> community plugins</b></p>'),9463)
        self.assertEqual(parse_claude_marketplace('<p class="sr-only" role="status">529 plugins</p>'),529)
        facet,total=parse_mcptop('<li aria-label="Highlight Plugins"><span title="Plugins">Plugins</span>'
                                 '<span class="tnum">1,265</span></li><p>Right now that’s 12,404 plugins, updated daily.</p>')
        self.assertEqual(facet,1265);self.assertEqual(total,12404)

    def test_marketplace_parsers_fail_closed_on_unknown_markup(self):
        for parser,markup in ((parse_dshmarket,'<html>no counter</html>'),(parse_mcptop,'<html>no facet</html>'),
                              (parse_claude_marketplace,'<html>no status</html>')):
            with self.assertRaises(FetchError):parser(markup)

    def test_feature_bullets_support_headings_chinese_and_added_fallback(self):
        english=feature_bullets('## New Features\n\n- Open the **agent command center** with `codex agents`.\n- Second feature.\n\n## Bug Fixes\n\n- A fix.')
        self.assertEqual(english,['Open the agent command center with codex agents.','Second feature.'])
        chinese=feature_bullets('<h3 id="cn">新增功能</h3>\n\n- 完善手机和平板适配。 @a\n- 支持将聊天文本作为引用插入。\n\n### 体验优化\n\n- 其他优化。')
        self.assertEqual(chinese,['完善手机和平板适配。 @a','支持将聊天文本作为引用插入。'])
        changelog=feature_bullets('## 2.1.319\n\n- Added support for MCP tasks in the terminal.\n- Fixed an empty diff.')
        self.assertEqual(changelog,['Added support for MCP tasks in the terminal.'])

    def test_parse_changelog_extracts_requested_versions_only(self):
        sections=parse_changelog('# Changelog\n\n## 2.1.319\n\n- Added MCP tasks.\n\n## 2.1.318\n\n- Older.\n',['2.1.319'])
        self.assertEqual(list(sections),['2.1.319']);self.assertIn('MCP tasks',sections['2.1.319'])

    def test_updates_collector_filters_window_and_marks_stub_bodies(self):
        class ReleaseClient:
            def json(self,url,**kwargs):
                return [{'tag_name':'rust-v0.167.0','published_at':'2026-11-06T01:40:00Z','prerelease':False,
                          'html_url':'u','body':'## New Features\n\n- Agent command center with lots of text to exceed the stub threshold for sure.'},
                         {'tag_name':'rust-v0.169.0-alpha.3','published_at':'2026-11-07T19:31:41Z','prerelease':True,
                          'html_url':'u','body':'Release 0.169.0-alpha.3'},
                         {'tag_name':'rust-v0.150.0','published_at':'2026-10-01T00:00:00Z','prerelease':False,
                          'html_url':'u','body':'Old release outside the window with a long enough body to matter for the check.'}]
            def get(self,url,**kwargs):raise FetchError('HTTP 404')
        updates=collect_product_updates(ReleaseClient(),[{'id':'codex','repo':'openai/codex'}],
                                        {'start':'2026-11-02','end':'2026-11-08'})
        row=updates['codex']
        self.assertEqual(row['status'],'ok')
        self.assertEqual([r['version'] for r in row['releases']],['0.167.0','0.169.0-alpha.3'])
        summary=summarize(row)
        self.assertEqual(summary[0]['highlights'],['Agent command center with lots of text to exceed the stub threshold for sure.'])
        self.assertEqual(summary[0]['basis'],'GitHub Release')
        self.assertEqual(summary[1]['highlights'],[])

    def test_markdown_summary_table_merges_scripted_numbers_and_editorial_views(self):
        run,config=self.markdown_run()
        run['editorial']={'window_end':'2026-11-05','prepared_at':'2026-11-06','products':{
            'claude':{'features':['denyInsteadOfPrompting：权限提示改为策略化拒绝','MCP任务后台化'],'insight':['无人值守权限策略值得借鉴','工具调用阻塞会话的共性痛点']},
            'codex':{'insight':['多agent集中管理是通用交互范式']},
            'pi':{},'dsh':{}}}
        page=render_markdown(run,config)
        self.assertIn('| Harness | 周 Token 使用量（万亿） | OpenRouter市场份额 | 周下载量 | 开源贡献者 | 插件数量 | 本周新功能 | 洞察 |',page)
        self.assertNotIn('Markdown 版',page)
        self.assertNotIn('data/editorial',page)
        self.assertNotIn('按用户指定',page)
        self.assertIn('| 529 |',page)
        self.assertIn('| 1,265 |',page)
        self.assertIn('| 5,360 |',page)
        self.assertIn('| 9,463 |',page)
        self.assertNotIn('Claude官方Marketplace）',page)
        self.assertNotIn('dshmarket.com）',page)
        # Contributors carry the bare count; repo names stay out of the summary table.
        self.assertIn('| 478 |',page)
        self.assertIn('| 56 |',page)
        self.assertNotIn('（openai/codex）',page)
        # 活跃用户 column is gone; disclosures moved to the 官方披露 block below the table.
        self.assertNotIn('| 活跃用户 |',page)
        self.assertIn('**官方披露**',page)
        self.assertIn('活跃用户 4,000万+（Codex 与 ChatGPT Work 合计口径，2026-10-07，OpenAI 团队成员公开帖）',page)
        self.assertIn('单品历史周活 超过500万 WAU（2026-06-02，历史口径，非当前人数）',page)
        self.assertIn('日活 154万、月活 548万、单日Token 92.10万亿（2026-11-04，厂商披露）',page)
        self.assertIn('公开第三方插件 3.49万（去重后，2026-11-04）',page)
        # Market share is computed against the whole ranked slice, arrows mark week-over-week direction.
        self.assertIn('（↑100.0%）',page)
        self.assertIn('| 10.0% |',page)
        # Editorial Chinese feature summaries take precedence; scripted fallback keeps version prefixes.
        self.assertIn('1）denyInsteadOfPrompting：权限提示改为策略化拒绝<br>2）MCP任务后台化',page)
        self.assertIn('1）0.167.0：Open the agent command center with codex agents --no-daemon (#5823…',page)
        # 洞察 column carries borrowing-value analysis; 行动 column is gone.
        self.assertIn('1）无人值守权限策略值得借鉴<br>2）工具调用阻塞会话的共性痛点',page)
        self.assertIn('1）多agent集中管理是通用交互范式',page)
        self.assertNotIn('行动</th>',page)
        self.assertNotIn('| 行动',page)
        # The old footnote and the mcptop directory note are gone.
        self.assertNotIn('不反映数据变化情况',page)
        self.assertNotIn('目录全量 12,404',page)
        self.assertNotIn('\t',page)

    def test_insight_cell_and_takeaways_escape_pipes(self):
        run,config=self.markdown_run()
        run['editorial']={'window_end':'2026-11-05','prepared_at':'2026-11-06',
            'takeaways':['方向A|B值得深研'],
            'products':{'claude':{'insight':['借鉴A|B','共性C']},'codex':{},'pi':{},'dsh':{}}}
        page=render_markdown(run,config)
        self.assertIn('1）借鉴A\\|B<br>2）共性C',page)
        self.assertIn('**行动：本周最值得深入研究或借鉴**',page)
        # Takeaways render as a real numbered list below the table.
        self.assertIn('1. 方向A\\|B值得深研',page)
        html_page=render(run,config)
        self.assertIn('1）借鉴A|B<br>2）共性C',html_page)
        # HTML takeaways render as a real ordered list.
        self.assertIn('<ol class="takeaways"><li>方向A|B值得深研</li></ol>',html_page)

    def test_markdown_without_editorial_keeps_features_and_blanks_insight(self):
        run,config=self.markdown_run();run['editorial']=None
        page=render_markdown(run,config)
        self.assertIn('本轮无编辑笔记',page)
        codex=next(line for line in page.splitlines() if line.startswith('| Codex '))
        self.assertIn('0.167.0：Open the agent command center with codex agents --no-daemon (#5823…',codex)
        claude=next(line for line in page.splitlines() if line.startswith('| Claude Code'))
        self.assertTrue(claude.rstrip().endswith('| — |'))

    def test_markdown_replaces_features_with_html_sourced_metrics_digest(self):
        run,config=self.markdown_run()
        run['editorial']={'window_end':'2026-11-05','prepared_at':'2026-11-06','products':{}}
        page=render_markdown(run,config)
        self.assertIn('# AI Harness 市场观察周报',page)
        self.assertIn('数据窗口：2026-10-30 — 2026-11-05',page)
        self.assertNotIn('（UTC）',page)
        self.assertNotIn('生成于',page)
        self.assertIn('## 二、模型使用与生态规模',page)
        self.assertIn('### 模型使用量及占比',page)
        self.assertIn('| Harness | 周 Token 使用量 | 样本内 Token 占比 | Token 使用量周环比 | 占比周变化（百分点） | 周模型请求量 |',page)
        self.assertIn('### 近四周 Token 使用量趋势（连续七天窗口，Token）',page)
        self.assertNotIn('### DSH 官方披露',page)
        # User-scale disclosures live under the summary table now, not in the digest.
        self.assertNotIn('### 用户规模公开信息',page)
        self.assertIn('**官方披露**',page)
        self.assertNotIn('（合计与单品分开）',page)
        self.assertNotIn('合计口径与单品口径分开列示',page)
        self.assertNotIn('公开插件与参与账号样本',page)
        # The feature digest now lives only in the HTML report.
        self.assertNotIn('## 二、本周新功能特性',page)
        self.assertNotIn('窗口内发布：',page)
        self.assertNotIn('网络检索核实（编辑）',page)
        self.assertNotIn('HTML 完整版',page)

    def test_markdown_top10_section_and_market_share_use_whole_slice(self):
        run,config=self.markdown_run()
        run['editorial']={'window_end':'2026-11-05','prepared_at':'2026-11-06','products':{}}
        page=render_markdown(run,config)
        self.assertIn('## 三、OpenRouter Top 10 动向',page)
        self.assertIn('- **新进入 Top 10**：New App（第3名 · 周 Token 8）——未标注',page)
        self.assertIn('- **本周增长最多**：Claude Code（第2名 · 周 Token 10，环比↑100.0%）——未标注',page)
        self.assertIn('- **退出 Top 10**：Old App（上期第3名）',page)
        # Share is measured against the whole ranked slice, spelled out in 口径与来源.
        self.assertIn('- **OpenRouter市场份额**：该应用周Token ÷ 榜单全部应用周Token合计，非四家内部占比（本轮已取得 8 个应用）。',page)
        self.assertIn('## 四、口径与来源',page)
        self.assertNotIn('本周新功能/洞察',page)
        # A quiet week still states there were no new entrants.
        run['openrouter_previous']['top_apps']=run['openrouter_current']['top_apps']
        page=render_markdown(run,config)
        self.assertIn('本周 Top 10 无新增应用',page)

    def test_top10_type_labels_come_from_app_types_file(self):
        run,config=self.markdown_run()
        run['editorial']={'window_end':'2026-11-05','prepared_at':'2026-11-06','products':{}}
        types={'503':{'type':'SDK','note':'官方SDK可嵌入','fit':'可方便地整合为执行引擎'},
               '502':{'type':'CLI','note':'终端编码agent','fit':'可直接调度'}}
        with patch('harness_trends.markdown_report.load_app_types',return_value=types), \
             patch('harness_trends.executive.load_app_types',return_value=types):
            page=render_markdown(run,config)
            self.assertIn('- **新进入 Top 10**：New App（第3名 · 周 Token 8）——SDK：官方SDK可嵌入',page)
            self.assertIn('  - 集成视角：可方便地整合为执行引擎',page)
            self.assertIn('——CLI：终端编码agent',page)
            html_page=render(run,config)
            # The label is a dedicated tag column in the Top10 legend and a pill in the moves panel.
            self.assertIn('<span class="type-tag t-cli" title="可直接调度">CLI</span>',html_page)
            self.assertIn('<span class="type-tag t-sdk" title="可方便地整合为执行引擎">SDK</span>',html_page)
            self.assertIn('class="legend-row tags"',html_page)
            self.assertIn('<h3>Top 10 动向</h3>',html_page)
            self.assertIn('新进入 Top 10</b>：New App',html_page)
            self.assertIn('集成视角：可方便地整合为执行引擎',html_page)
            self.assertIn('退出 Top 10</b>：Old App（上期第3名）',html_page)

    def test_summary_table_orders_rows_by_market_share(self):
        run,config=self.markdown_run()
        # Uneven tokens make market shares distinct: claude 40%, pi 30%, dsh 20%, codex 10%.
        for pid,tokens in (('claude',40),('pi',30),('dsh',20),('codex',10)):
            run['openrouter_current']['products'][pid]['tokens']=tokens
        compute(run,config)
        page=render_markdown(run,config)
        order=[line.split('|')[1].strip() for line in page.splitlines() if line.startswith('| ') and not line.startswith('|--')]
        summary=order[1:5]
        self.assertEqual(summary,['Claude Code','Pi','DeepSeek Harness','Codex'])
        html_page=render(run,config)
        start=html_page.find('table-scroll summary-table');seg=html_page[start:html_page.find('</table>',start)]
        positions=[seg.find(name) for name in ('Claude Code','Pi','DeepSeek Harness','Codex')]
        self.assertEqual(positions,sorted(positions))

    def test_reports_are_archived_per_window_before_each_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);reports=root/'reports';reports.mkdir()
            data=root/'data';data.mkdir()
            (data/'latest.json').write_text(json.dumps({'window':{'start':'2026-10-30','end':'2026-11-05'}}))
            archive_current(reports,root)
            self.assertFalse((reports/'archive').exists())
            (reports/'latest.md').write_text('# old')
            (reports/'latest.html').write_text('<html>old</html>')
            archive_current(reports,root)
            self.assertEqual((archive_dir(reports,'2026-11-05')/'report.md').read_text(),'# old')
            self.assertEqual((reports/'archive'/'2026-11-05'/'report.html').read_text(),'<html>old</html>')
            # A broken snapshot never blocks the run; existing latest files stay untouched.
            (data/'latest.json').write_text('{oops')
            (reports/'latest.md').write_text('# newer')
            archive_current(reports,root)
            self.assertEqual((reports/'latest.md').read_text(),'# newer')

    def test_html_renders_summary_table_and_features_section(self):
        run,config=self.markdown_run()
        run['editorial']={'window_end':'2026-11-05','prepared_at':'2026-11-06','takeaways':['研究权限分级设计'],
            'products':{
            'claude':{'features':['权限提示改为策略化拒绝并继续执行','MCP长任务后台化'],
                      'feature_summary':'与CHANGELOG一致',
                      'sources':['https://github.com/anthropics/claude-code/releases']},
            'codex':{'features':['多agent集中管理中心']},'pi':{},'dsh':{}}}
        page=render(run,config)
        self.assertIn('summary-table',page)
        self.assertIn('>本周新功能</th>',page)
        self.assertIn('>活跃用户</th>',page)
        self.assertIn('4,000万+（Codex（含 ChatGPT Work），2026-10-07）',page)
        self.assertIn('548万MAU / 154万DAU（官方披露，2026-11-04）',page)
        self.assertIn('>洞察</th>',page)
        self.assertIn('本周最值得深入研究或借鉴',page)
        self.assertIn('<ol class="takeaways"><li>研究权限分级设计</li></ol>',page)
        self.assertIn('不反映数据变化情况',page)
        # The rankings panel got a plain title and the Top 10 moves panel sits in the same section.
        self.assertIn('公开应用榜单Top10',page)
        self.assertNotIn('放到公开应用榜单中看',page)
        self.assertIn('<h3>Top 10 动向</h3>',page)
        # Features lead with editorial Chinese summaries; scripted原文 stays archived in a fold.
        self.assertIn('<ol class="feature-cn"><li>权限提示改为策略化拒绝并继续执行</li>',page)
        self.assertIn('官方发布原文（脚本采集，核对用）',page)
        self.assertIn('id="features"',page)
        self.assertIn('href="#features"',page)
        self.assertIn('Open the agent command center with codex agents --no-daemon (#58238).',page)
        self.assertIn('网络检索核实：与CHANGELOG一致',page)
        # Old snapshots without product_updates skip the section instead of crashing.
        run2,config2=self.markdown_run();run2.pop('product_updates')
        page2=render(run2,config2)
        self.assertNotIn('id="features"',page2)
        self.assertIn('summary-table',page2)

    def test_html_features_section_flags_collection_failures(self):
        run,config=self.markdown_run()
        run['product_updates']['claude']={'repo':'anthropics/claude-code','status':'missing','errors':['HTTP 403'],'releases':[]}
        run['editorial']={'window_end':'2026-11-05','prepared_at':'2026-11-06','products':{
            'claude':{'feature_summary':'与CHANGELOG一致','sources':['https://github.com/anthropics/claude-code/releases']}}}
        page=render(run,config)
        self.assertIn('脚本采集失败：HTTP 403；本产品仅剩编辑内容。',page)
        self.assertIn('网络检索核实：与CHANGELOG一致',page)


if __name__=='__main__': unittest.main()
