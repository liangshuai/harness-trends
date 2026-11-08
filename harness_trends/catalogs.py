"""Official package catalogs take precedence over repository extrapolation."""
import concurrent.futures
from datetime import datetime,timezone
import html
import math
import re
from .collect import FetchError


def parse_pi_catalog(markup):
    text=html.unescape(re.sub(r'<[^>]+>',' ',markup))
    text=re.sub(r'\s+',' ',text)
    match=re.search(r'All\s+packages\s+(\d[\d,]*)\s*[-–]\s*(\d[\d,]*)\s*/\s*([\d,]+)',text)
    if not match:raise FetchError('Pi官网未识别到未筛选目录总数，需检查页面结构')
    total=int(match.group(3).replace(',',''))
    cards=[]
    for article in re.findall(r'<article\b[^>]*data-package-card="true".*?</article>',markup,re.S):
        name=re.search(r'data-package-name="([^"]+)"',article)
        if not name:continue
        meta=re.search(r'<div\b[^>]*class="packages-meta"[^>]*>\s*<span[^>]*>(.*?)</span>',article,re.S)
        author=html.unescape(re.sub('<[^>]+>','',meta.group(1))).strip() if meta else None
        types=re.search(r'data-package-types="([^"]*)"',article)
        cards.append({'name':html.unescape(name.group(1)),'author':author,
                      'types':html.unescape(types.group(1)).split() if types else []})
    return total,cards


def collect_pi_catalog(client,settings):
    url=settings['url'];stamp=datetime.now(timezone.utc).isoformat()
    result={'source':url,'observed_at':stamp,'status':'missing','total':None,'entries':[],
            'unit':'官网收录扩展包（含extension、skill、theme、prompt及组合包）','errors':[]}
    try:
        total,first=parse_pi_catalog(client.get(url))
    except FetchError as exc:
        result['errors'].append(str(exc));return result
    source_event=next((e for e in reversed(client.events) if e['url']==url),None)
    if source_event:result['observed_at']=datetime.fromtimestamp(source_event['fetched_unix'],timezone.utc).isoformat()
    result['total']=total;entries={r['name']:r for r in first}
    pages=math.ceil(total/50);limit=min(pages,settings.get('max_pages',200))
    def fetch(page):
        try:
            _,rows=parse_pi_catalog(client.get(url+'?page='+str(page)))
            return page,rows,None
        except FetchError as exc:return page,[],str(exc)
    completed=1
    with concurrent.futures.ThreadPoolExecutor(max_workers=settings.get('workers',4)) as pool:
        for page,rows,error in pool.map(fetch,range(2,limit+1)):
            completed+=1
            for row in rows:entries[row['name']]=row
            if error:result['errors'].append(f'page {page}: {error}')
            if completed%20==0:print(f'  Pi官网目录：已读取{completed}/{pages}页，去重{len(entries)}个包',flush=True)
    result['entries']=list(entries.values());result['collected_packages']=len(entries)
    result['unique_author_labels']=sorted({r['author'].casefold() for r in entries.values() if r['author'] and r['author'].casefold() not in ('unknown','anonymous','n/a','-')})
    result['observed_authors']=len(result['unique_author_labels'])
    result['authors_complete']=(not result['errors'] and len(entries)==total and all(r['author'] for r in entries.values()))
    result['status']='ok' if result['authors_complete'] else 'partial'
    result['pages_expected']=pages;result['pages_requested']=limit
    if limit<pages:result['errors'].append('达到目录分页上限，作者列表不完整')
    if len(entries)!=total:result['errors'].append('逐页包并集与首页计数不一致；目录更新或分页变化，不能声称作者已全量')
    return result
