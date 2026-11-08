import copy
from datetime import date
import json
from pathlib import Path
import tempfile
import unittest

from harness_trends.collect import Client, FetchError, is_human, npm_downloads, openrouter_window
from harness_trends.metrics import compute, package_total, ratio_delta, scale_summary
from harness_trends.render import esc, render
from run_report import load_env, previous_snapshot, settled_end, METHOD
from harness_trends.executive import donut
from harness_trends.models_v2 import apply as apply_v2, npm_equivalent
from harness_trends.catalogs import parse_pi_catalog
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


if __name__=='__main__': unittest.main()
