#!/usr/bin/env python3
"""Refresh only plugin leaderboards; optionally rebuild the current HTML report."""
import argparse
from datetime import datetime, timezone
import fcntl
import json
from pathlib import Path
import sys

from harness_trends.collect import Client
from harness_trends.plugin_rankings import collect_plugin_rankings
from harness_trends.pipeline import inventory
from harness_trends.render import render
from run_report import archive_current, archive_dir, atomic_json

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline', action='store_true', help='只读取缓存，保留缓存原始采集时间')
    parser.add_argument('--update-report', action='store_true', help='把新榜单接入当前快照并重建 HTML，保留其他模块原始数据与日期')
    args = parser.parse_args()
    config = json.loads((ROOT / 'config.json').read_text())
    now = datetime.now(timezone.utc)
    stamp = now.strftime('%Y%m%dT%H%M%SZ')
    client = Client(ROOT, ROOT / 'data/raw' / ('plugins_' + stamp), cache_hours=0, offline=args.offline)
    rankings = collect_plugin_rankings(client, config)
    snapshot = {'plugin_rankings': rankings, 'requests': client.events}
    atomic_json(ROOT / 'data/plugin_rankings' / (stamp + '.json'), snapshot)
    atomic_json(ROOT / 'data/plugin_rankings/latest.json', snapshot)
    for pid, row in rankings['products'].items():
        print(f'{pid}: {row["status"]} · {len(row["entries"])}/10 · {row.get("reason", row["metric"])}')
    if args.update_report:
        run = json.loads((ROOT / 'data/latest.json').read_text())
        archive_current(ROOT / 'reports', ROOT)
        run['id'] = run['window']['end'] + '_' + stamp + '_plugins'
        run['plugin_rankings'] = rankings
        run['requests'] = run.get('requests', []) + client.events
        run['data_inventory'] = inventory(run)
        # Other data are deliberately not re-dated: this is a plugin-only refresh.
        atomic_json(ROOT / 'data/runs' / (run['id'] + '.json'), run)
        atomic_json(ROOT / 'data/latest.json', run)
        page = render(run, run.get('configuration', config))
        folder = archive_dir(ROOT / 'reports', run['window']['end'])
        (folder / (run['id'] + '.html')).write_text(page)
        (folder / 'report.html').write_text(page)
        temp = ROOT / 'reports/latest.html.tmp'
        temp.write_text(page)
        temp.replace(ROOT / 'reports/latest.html')
        print('已更新 reports/latest.html；其他模块的统计窗口与生成时间保持原记录。')
    return 0 if all(r['status'] == 'ok' for r in rankings['products'].values()) else 2


if __name__ == '__main__':
    with (ROOT / '.run.lock').open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print('已有报告任务运行中。', file=sys.stderr)
            sys.exit(3)
        sys.exit(main())
