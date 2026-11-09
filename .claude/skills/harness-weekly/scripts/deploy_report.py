#!/usr/bin/env python3
"""Stage only the generated HTML, then publish it to the linked Vercel project."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parent
SITE=ROOT/'site'


def prepare():
    report=ROOT/'reports/latest.html'
    if not report.is_file():raise RuntimeError('请先运行 run_report.py 生成报告')
    body=report.read_text()
    if '<h1>Coding Agent Harness市场观察周报</h1>' not in body:
        raise RuntimeError('报告标题校验失败，停止发布')
    # Check all literal dotenv values without printing any of them.
    env=ROOT/'.env'
    if env.exists():
        for line in env.read_text().splitlines():
            if not line.strip() or line.lstrip().startswith('#'):continue
            _,sep,value=line.partition('=')
            value=value.strip().strip('\"\'')
            if sep and len(value)>=12 and value in body:
                raise RuntimeError('页面检测到环境配置值，停止发布')
    SITE.mkdir(exist_ok=True)
    # Vercel link creates an OIDC dotenv file. Keep it in local metadata,
    # never among the files selected for the static deployment.
    generated_env=SITE/'.env.local'
    if generated_env.exists():
        metadata=SITE/'.vercel'
        metadata.mkdir(exist_ok=True)
        generated_env.replace(metadata/'oidc.env.local')
    allowed={'index.html','vercel.json','.vercel','.vercelignore','.gitignore'}
    extra=[p.name for p in SITE.iterdir() if p.name not in allowed]
    if extra:raise RuntimeError('发布目录出现未授权文件，停止发布')
    shutil.copyfile(report,SITE/'index.html')
    config={'$schema':'https://openapi.vercel.sh/vercel.json','framework':None,
            'buildCommand':None,'installCommand':None,'outputDirectory':'.','cleanUrls':True,
            'headers':[{'source':'/(.*)','headers':[{'key':'Cache-Control','value':'public, max-age=0, must-revalidate'},
                        {'key':'X-Content-Type-Options','value':'nosniff'}]}]}
    (SITE/'vercel.json').write_text(json.dumps(config,indent=2))
    (SITE/'.vercelignore').write_text('*\n!index.html\n!vercel.json\n')
    print('已准备独立发布目录：仅包含报告HTML和站点配置。',flush=True)


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
