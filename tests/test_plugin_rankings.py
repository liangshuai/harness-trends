import json
from pathlib import Path
import unittest

from harness_trends.collect import FetchError
from harness_trends.plugin_rankings import (collect_plugin_rankings, parse_claude, parse_codex,
                                            parse_dsh, parse_pi, render_plugin_rankings, SPECS)


def claude_page(items):
    payload = '0:' + json.dumps({'items': items})
    # Test a flight chunk boundary inside a plugin object.
    return ''.join('<script>self.__next_f.push([1,' + json.dumps(part) + '])</script>'
                   for part in (payload[:50], payload[50:]))


class RankingTests(unittest.TestCase):
    def test_claude_sorts_installs_filters_compatibility_and_unknown_counts(self):
        items = [dict(_id='directoryPlugin.'+str(i), title='Plugin '+str(i), slug=str(i),
                      subheading='Tools', worksWith=[{'value':'claude-code'}], installs=i)
                 for i in range(12)]
        items += [dict(items[-1], slug='wrong-host', installs=999999, worksWith=[{'value':'claude'}]),
                  dict(items[-1], slug='unknown', installs=None)]
        rows = parse_claude(claude_page(items))
        self.assertEqual([r['value'] for r in rows], list(range(11, 1, -1)))
        self.assertNotIn('wrong-host', [r['id'] for r in rows])

    def test_pi_extracts_exact_downloads_and_rejects_changed_sort(self):
        page = '<option value="downloads" selected="">Most downloads</option>'
        page += '<article data-package-card="true" data-package-name="a&amp;b" data-package-downloads="15001"><p class="packages-desc">Search &amp; fetch</p><a data-package-path="/packages/a"></a></article>'
        self.assertEqual(parse_pi(page)[0]['value'], 15001)
        self.assertEqual(parse_pi(page)[0]['name'], 'a&b')
        with self.assertRaises(FetchError): parse_pi(page.replace('selected', 'other'))

    def test_dsh_uses_downloads_not_stars_and_only_popular_section(self):
        card = '<li class="pcard"><a class="pname" href="https://example.org/p"><span>owner/</span>plugin</a><p>Runs tools</p><div><span>★ 99999</span><span>1,234 / 30 days</span></div></li>'
        page = '<section id="popular">Ranked by npm downloads over the last 30 days.'+card+'</section>'+card
        self.assertEqual(len(parse_dsh(page)), 1)
        self.assertEqual(parse_dsh(page)[0]['value'], 1234)

    def test_codex_uses_position_not_daily_movement(self):
        page = 'publishes no scores<tbody><tr><td>999</td><td><a class="rank-link" href="/server/a"><span class="rank-name">A</span><span class="rank-blurb">Tools</span></a></td><td><span>#2</span></td></tr></tbody>'
        self.assertEqual(parse_codex(page)[0]['value'], 2)

    def test_failure_is_visible_for_all_four_and_legacy_render_has_module(self):
        class Offline:
            def get(self, url): raise FetchError('离线缓存缺失')
        result = collect_plugin_rankings(Offline(), {})
        self.assertEqual(set(result['products']), set(SPECS))
        for row in result['products'].values():
            self.assertEqual(row['status'], 'missing')
            self.assertEqual(row['entries'], [])
        page = render_plugin_rankings({'plugin_rankings':result})
        self.assertEqual(page.count('离线缓存缺失'), 4)
        self.assertIn('不是 Codex 专属活跃 Top 10', page)
        self.assertIn('id="plugin-rankings"', render_plugin_rankings({}))

    def test_short_list_is_partial_and_html_is_escaped(self):
        class Short:
            events = []
            def get(self, url):
                if 'claude.com' not in url: raise FetchError('unavailable')
                return claude_page([dict(_id='directoryPlugin.x', slug='x', title='<script>bad</script>',
                    subheading='<img src=x onerror=bad>', worksWith=[{'value':'claude-code'}], installs=0)])
        rankings = collect_plugin_rankings(Short(), {})
        self.assertEqual(rankings['products']['claude']['status'], 'partial')
        self.assertEqual(rankings['products']['claude']['entries'][0]['value'], 0)
        page = render_plugin_rankings({'plugin_rankings':rankings})
        self.assertNotIn('<script>bad</script>', page)
        self.assertIn('&lt;script&gt;', page)


if __name__ == '__main__': unittest.main()
