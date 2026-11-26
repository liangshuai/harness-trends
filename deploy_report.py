#!/usr/bin/env python3
"""Stage the whole reports directory (index home, latest issue, every archived window), then publish."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parent
SITE=ROOT/'site'
REPORTS=ROOT/'reports'


def staged_files(reports):
    """index + latest copies + one canonical report per archived window; per-run duplicates stay local."""
    files=[reports/'index.html',reports/'latest.html',reports/'latest.md']
    archive=reports/'archive'
    if archive.is_dir():
        for folder in sorted(archive.iterdir()):
            for name in ('report.html','report.md'):
                path=folder/name
                if path.is_file():
                    files.append(path)
    missing=[str(p) for p in files if not p.is_file()]
    if missing:
        raise RuntimeError(f'缺少待发布文件（先运行 run_report.py 生成报告与首页）：{missing[:3]}')
    return files


def prepare():
    files=staged_files(REPORTS)
    bodies={p: p.read_text() for p in files if p.suffix in ('.html','.md')}
    home=bodies.get(REPORTS/'index.html','')
    latest=bodies.get(REPORTS/'latest.html','')
    if '<h1>AI Harness 市场观察周报</h1>' not in home or '历史期数' not in home:
        raise RuntimeError('首页校验失败（缺少标题或期数表），停止发布')
    if '<h1>AI Harness 市场观察周报</h1>' not in latest:
        raise RuntimeError('报告标题校验失败，停止发布')
    # Check all literal dotenv values without printing any of them.
    env=ROOT/'.env'
    if env.exists():
        for line in env.read_text().splitlines():
            if not line.strip() or line.lstrip().startswith('#'):continue
            _,sep,value=line.partition('=')
            value=value.strip().strip('"\'')
            if sep and len(value)>=12:
                for name,body in bodies.items():
                    if value in body:
                        raise RuntimeError(f'页面检测到环境配置值（{name.name}），停止发布')
    if SITE.exists():
        # Keep the Vercel project link (and its OIDC dotenv) across rebuilds; it is local
        # metadata and never part of the files staged for deployment.
        saved=SITE/'.vercel'
        keeper=ROOT/'.vercel-site-metadata'
        if keeper.exists():
            shutil.rmtree(keeper)
        if saved.is_dir():
            shutil.move(str(saved),str(keeper))
        shutil.rmtree(SITE)
        SITE.mkdir()
        if keeper.is_dir():
            shutil.move(str(keeper),str(SITE/'.vercel'))
    else:
        SITE.mkdir()
    for path in files:
        target=SITE/path.relative_to(REPORTS)
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(path,target)
    config={'$schema':'https://openapi.vercel.sh/vercel.json','framework':None,
            'buildCommand':None,'installCommand':None,'outputDirectory':'.','cleanUrls':True,
            'headers':[{'source':'/(.*)','headers':[{'key':'Cache-Control','value':'public, max-age=0, must-revalidate'},
                        {'key':'X-Content-Type-Options','value':'nosniff'}]}]}
    (SITE/'vercel.json').write_text(json.dumps(config,indent=2))
    # site/ is rebuilt from an explicit whitelist each time; only local Vercel metadata stays excluded.
    (SITE/'.vercelignore').write_text('.vercel\n')
    windows={p.parent.name for p in files if p.parent.parent.name=='archive'}
    print(f'已准备发布目录：首页 + 最新一期 + {len(windows)} 期历史存档。',flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-only',action='store_true')
    args=parser.parse_args()
    prepare()
    if args.prepare_only:return
    if not (SITE/'.vercel/project.json').exists():
        raise RuntimeError('发布目录尚未关联Vercel项目；请先完成首次项目部署')
    subprocess.run(['npx','--yes','vercel@65.12.1','deploy','--prod','--yes'],cwd=SITE,check=True)


if __name__=='__main__':main()
