#!/bin/sh
# 仓库根目录是唯一权威版本。改动根目录代码/配置/测试后，执行本脚本把最新版本同步进 skill 内联副本。
# 一致性由根目录测试 test_skill_bundle_matches_repo_sources 强制校验，漏同步会挂测试。
set -e
cd "$(dirname "$0")/../../.."
SKILL=.claude/skills/harness-weekly
mkdir -p "$SKILL/scripts/harness_trends" "$SKILL/scripts/tests" "$SKILL/examples"
cp run_report.py deploy_report.py config.json .env.example "$SKILL/scripts/"
cp harness_trends/*.py "$SKILL/scripts/harness_trends/"
# Top 10 应用类型标注：MD「Top 10 动向」模块与 HTML 类型标签依赖它，缺文件会退化为「未标注」
mkdir -p "$SKILL/scripts/data"
cp data/app_types.json "$SKILL/scripts/data/"
cp tests/test_report.py "$SKILL/scripts/tests/"
# 披露原图：HTML 报告会内嵌其 base64，缺图会导致独立副本输出与仓库版有差异
mkdir -p "$SKILL/scripts/Harness-资料/raw"
cp Harness-资料/raw/*.jpg "$SKILL/scripts/Harness-资料/raw/"
# 范本：最近一期编辑笔记与 Markdown 报告示例（自然演进的历史样本，不要求与当期一致）
cp data/editorial/*.json "$SKILL/examples/" 2>/dev/null || true
cp reports/latest.md "$SKILL/examples/report-latest.md"
echo "已同步 $SKILL/scripts 与 examples/"
