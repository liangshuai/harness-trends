---
name: harness-weekly
description: 生成或更新 Harness 市场观察周报（Codex/Claude Code/Pi/DSH 双格式报告）：全量取数、编辑笔记撰写与核实、渲染、测试、提交推送与线上发布。凡涉及 run_report.py、任何取数逻辑、周报内容修改或周期性更新任务时使用本 skill。
---

# Harness 周报工作流

## 核心原则（先读，不可违背）

1. **数字只由脚本采集**，永远不手工填写/修改报告中的任何数字。助手只写 `data/editorial/<窗口结束日>.json` 里的定性内容（洞察/行动/网络检索核实）。
2. **编辑与数据分离**：洞察、行动、feature_summary 是编辑观点；汇总表中的数字全部来自当轮 run 快照。编辑笔记不复述精确数值（避免与脚本数字漂移），洞察必须**面向本周新增功能点**且为**字符串数组**（逐条列举）。
3. **缺失不是 0**：任何来源取数失败渲染 `—` 并记录 reason，绝不补零或臆造。
4. **口径不混排**：OpenRouter 渠道量 ≠ 全市场；厂商披露与估算情景分开列示（活跃用户列只放官方披露，合计与单品口径各自保留）；四家插件目录口径互不相同，不做横向排名。
5. **全留档**：每轮运行的原始响应、缓存、run JSON、报告都进 git（该仓库不忽略 data/）。历史披露是固定锚点，保留原披露日期，不重写成本周新数据。
6. 密钥只经 `.env`（`OPENROUTER_API_KEY`、可选 `GITHUB_TOKEN`）进请求头，绝不进报告、快照或 git。

## 一条命令周更

```sh
cd /Users/liangshuai/workspace/harness-trends
python3 run_report.py --refresh          # 每周正式更新：忽略跨轮缓存，全量重采
python3 run_report.py                    # 常规：24h 缓存复用（改代码/加编辑笔记后重渲染用它，快）
python3 run_report.py --end 2026-11-05   # 固定窗口
python3 run_report.py --offline          # 断网复算
python3 run_report.py --render-only data/latest.json  # 只重建 HTML+MD，不联网（仅版式修改/审计）
python3 -m unittest discover -s tests    # 34 项单测，改动后必须跑
```

- 互斥文件锁防并发；窗口为最近完整 UTC 周一~周日七天。
- npm 日结探测：`@openai/codex` 与 `@anthropic-ai/claude-code` 同时为零则整体回退到最近有数据的 UTC 日（把结算延迟当下跌是错误）。
- GitHub API 预算 90 次/轮；超预算记缺失。
- 已配置外部定时任务（周一纽约 9 点）跑 `--refresh` + `deploy_report.py`，机器需可用。

## 取数逻辑总表（指标 → 来源 → 实现）

| 指标 | 来源与口径 | 实现 | 注意 |
|---|---|---|---|
| 周Token/请求/四家份额 | OpenRouter app-rankings 数据集，canonical app ID 固定在 `config.json openrouter.app_ids`（防同名 Pi 扩展混入） | `collect.openrouter_window` | 四家齐全才算份额；只有渠道量，非全市场 |
| 四周趋势 | 同上按周回取 4 窗口 | run_report 循环 | 缺失点留空不补零 |
| 周npm下载+环比 | npm downloads API 逐日加总主包 | `collect.npm_downloads` | 含更新/CI/重复下载，不等于用户 |
| GitHub 插件样本 | topic 搜索前100哈希抽样 → manifest 验证 → contributors | `collect.github_ecosystem` | 核心仓库（官方 repo）被排除；受限样本非总量 |
| Pi 插件目录总数 | pi.dev/packages 全分页抓取、跨包去重、作者去重 | `catalogs.collect_pi_catalog` | 官网目录优先于 GitHub 外推；含 extension/skill/theme/prompt |
| 三家插件市场计数 | claude.com/marketplace/plugins（sr-only status）；mcptop.com `?source=openai` 的 **Plugins 分类计数**（非目录全量，全量另存 directory_total）；dshmarket.com（hero `id="count"`） | `marketplaces.collect_marketplaces`，URL 在 `config.json marketplaces` | 解析失败 fail closed 记 missing；页面结构变了先改正则并加测试 |
| 开源贡献者 | 官方仓库 contributors，`per_page=1&anon=false`，Link 头 `rel="last"` 页码=精确总数（非匿名，与 GitHub UI 同口径） | `collect.official_repo` | 只反映公开官方仓库；闭源内部开发（如 anthropics/claude-code 公开仓只是镜像）不计入 |
| 本周新功能 | 官方仓库 GitHub Releases（窗口内、产品发布线标签 `rust-v|dsh-v|v` 前缀，过滤 libcap 之类）+ CHANGELOG.md（HEAD 引用取默认分支） | `changelog.collect_product_updates`，要点提取 `feature_bullets` | 正文 <80 字符视为占位 stub 不提要点；New Features/新增功能 优先，Claude 风格回退 Added 前缀 |
| 活跃用户披露 | Codex+ChatGPT Work 合计 4000万（2026-10-07，窗口未明示）、Codex 单品历史 WAU 500万（2026-06-02）、DSH 154万DAU/548万MAU（2026-11-04） | `metrics.user_disclosure_rows/user_cell`，源自 `user_disclosures`+`disclosure`+`models_v2` | 合计与单品分开、只计一次、不外推当期；Claude/Pi 无披露留空 |
| X 披露原帖 | 官方 oEmbed 解析 | `user_disclosures.py` | 只解析已登记帖子，不能自动发现新帖 |
| 规模估算 v2 | 各产品自身锚点（WAU/ARR/下载）+ 发布者并集 | `models_v2.py`，参数固定 config | 情景假设非置信区间；不随周更调参 |

## 编辑笔记（每周助手步骤）

1. 对四家分别**网络搜索本周新功能**（关键词带版本号，如 "Claude Code 2.1.319 release notes"）。
2. 与脚本采集的 Releases/CHANGELOG 原文**逐条核实**，feature_summary 里写明"网络检索与 CHANGELOG/Release 一致/差异"。
3. 写 `data/editorial/<窗口结束日>.json`（例 `data/editorial/2026-11-08.json`），结构：

```json
{
  "window_end": "2026-11-08", "prepared_at": "2026-11-09",
  "products": {
    "claude": {
      "insight": ["一条一个观点，面向本周功能主线", "…"],
      "action": "跟进建议一句话",
      "feature_summary": "网络检索核实结论…",
      "sources": ["https://github.com/anthropics/claude-code/releases"]
    }
  }
}
```

4. `python3 run_report.py`（缓存模式）重跑，把编辑笔记嵌入快照并重渲染两份报告。
5. 编辑笔记缺失时：洞察列自动降级为脚本提取的发布要点，不阻塞周更。

## 渲染结构（改版式时保持）

- **HTML `reports/latest.html`**：核心数据区 KPI + **四家汇总表**（8列：周Token/周下载量/开源贡献者/插件数量/活跃用户/洞察（本周新功能）/行动，行序 Claude Code→Codex→Pi→DSH）→ 份额图 → 用量 → 四周趋势 → 生态 → **本周新功能特性**（05，脚本原文+编辑核实）→ 规模估算 → 附录。
- **Markdown `reports/latest.md`（正式汇报文案）**：一、四家汇总表（同上同源）→ 二、用量与生态指标汇总（KPI/用量份额表/四周趋势表/用户规模公开信息/DSH披露）→ 三、口径与来源。新功能特性只在 HTML。
- 汇总表行构建单一数据源：`metrics.summary_rows`；洞察逐条编号+换行（MD 用 `1）…<br>`，HTML 纯文本 `<br>`，**不用真实列表标签**）；正式文案里不得出现：格式标签（"Markdown 版"）、仓库文件路径、"按用户指定"类字眼、实现细节。
- 两个渲染器共享 `metrics.py`；勿在 executive.py 与 markdown_report.py 之间互相 import（会循环依赖），共享逻辑放 metrics.py。

## 运行后校验清单

```sh
python3 -m unittest discover -s tests                       # 全绿
python3 -c "import json;d=json.load(open('data/latest.json'));print(d['window'],d['marketplaces'],d['official_repos'])"
grep -c 'summary-table' reports/latest.html                 # 汇总表存在
head -30 reports/latest.md                                  # 汇总表、无实现细节字眼
```

检查：四家 Token/下载齐全；市场计数 ok；贡献者 ok；窗口内发布数合理；MD 无 `<ol`、无内部路径。

## 发布

```sh
git add -A && git commit -m "update: 刷新周报数据至<窗口>窗口" && git push origin main
python3 deploy_report.py    # 可选：发布线上 https://harness-market-observer.vercel.app（只上传 index.html + vercel.json，MD 不上线）
```

## 常见坑

- Python 3.10：`datetime.fromisoformat` 不认 `Z` 后缀（代码里已替换为 `+00:00`），别引入回归。
- codex alpha 版 release 正文是 "Release x.y.z" 占位符，没有功能信息；stable 版才有完整 notes。
- mcptop 页面同时有 Plugins 分类计数与目录全量两个数字，汇总表取**分类计数**。
- anthropics/claude-code 公开仓库贡献者只有几十人是正常的（闭源镜像开发），报告口径已注明。
- `--render-only` 仅供版式/审计，不能当周更命令。
- 旧 run 快照缺 `product_updates` 等字段时渲染器必须优雅降级（有测试覆盖）。
