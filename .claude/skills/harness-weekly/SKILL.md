---
name: harness-weekly
description: 生成或更新 Harness 市场观察周报（Codex/Claude Code/Pi/DSH 双格式报告）：脚本采集、网络检索、编辑笔记生成、渲染、校验、提交推送与线上发布的完整操作手册。凡涉及 run_report.py、任何取数逻辑、周报内容修改、周期性更新或在新机器复现周报时使用本 skill。
---

# Harness 周报完整操作手册

## 0. 报告由三类工作构成（先分清）

| 类别 | 内容 | 谁来做 | 章节 |
|---|---|---|---|
| A 脚本采集 | 报告里**所有数字**：Token、下载、贡献者、插件数、活跃用户披露、新功能原文 | `run_report.py` 一条命令 | §2 |
| B 网络检索 | 四家本周新功能的第三方报道与官方发布说明交叉材料 | Agent 联网搜索 | §3 |
| C Agent 生成 | 洞察（逐条）、行动、网络检索核实结论 → `data/editorial/<窗口结束日>.json` | Agent 按规则撰写 | §4 |

每周流程固定顺序：**A 采集 → B 检索 → C 写笔记 → A' 重跑嵌入 → 校验 → 提交推送**。
换机器跑同样报告：先做 §1 初始化，再按 §2→§6 顺序执行，任何一步都不允许跳过或改序。

## 0.5 本 skill 是自包含的（只拿到 skill 文件夹也能用）

```
harness-weekly/
├── SKILL.md            本手册
├── scripts/            全部运行代码的内联副本（run_report.py、harness_trends/、tests/、config.json、.env.example、deploy_report.py、Harness-资料/raw 披露原图）
├── examples/           范本：编辑笔记 editorial-*.json、示例报告 report-latest.md
└── sync.sh             仓库→skill 同步脚本
```

两种使用方式：
- **在本仓库内**（正常情况）：直接用仓库根目录的脚本（§2 的命令在仓库根执行）。根目录是唯一权威版本。
- **只拿到本 skill 文件夹**（分发给他人在别的机器/项目用）：

```sh
mkdir harness-trends && cp -r <skill路径>/scripts/. harness-trends/ && cd harness-trends
cp .env.example .env && 编辑 .env 填密钥（见 §1）
python3 run_report.py --refresh          # 之后按 §2→§7 正常执行
python3 -m unittest discover -s tests    # 副本内运行会自动跳过与仓库比对的一致性测试
```

**维护规则**：在本仓库改了任何代码/配置/测试后，必须执行 `sh .claude/skills/harness-weekly/sync.sh` 同步内联副本；根目录测试 `test_skill_bundle_matches_repo_sources` 会逐文件比对，漏同步直接挂测试。examples/ 里的范本随 sync 自然更新，不要求与当期一致。

## 核心原则（不可违背）

1. **数字只由脚本采集**（A 类），永远不手工填写/修改报告中任何数字。Agent 只产出 C 类定性内容。
2. **编辑与数据分离**：编辑内容只存在于 `data/editorial/<窗口结束日>.json`，运行时嵌入快照。
3. **缺失不是 0**：任何来源失败渲染 `—` 并记 reason，不补零、不臆造、不用页面数据顶替。
4. **口径不混排**：OpenRouter 渠道量 ≠ 全市场；活跃用户只列官方披露（合计与单品分开、只计一次）；四家插件目录口径不同不横向排名；厂商披露与估算情景分列。
5. **全留档**：原始响应、缓存、run JSON、报告全部进 git；历史披露保留原披露日期，不重写成本周数据。
6. 密钥只经 `.env` 进请求头，绝不进报告、快照或 git。

---

## 1. 新机器初始化（换机复现的前提）

```sh
git clone git@github.com:liangshuai/harness-trends.git   # 或 https://github.com/liangshuai/harness-trends.git
cd harness-trends
cp .env.example .env
# 编辑 .env，填两个键：
#   OPENROUTER_API_KEY=sk-or-v1-...   必需。https://openrouter.ai/settings/keys 创建。
#     没有它 Token 列全空（口径不允许用网页数据补），报告就不完整。
#   GITHUB_TOKEN=ghp_...              强烈建议。github.com → Settings → Developer settings →
#     Personal access tokens (classic)，勾 public_repo 只读即可。没有它容易触发匿名限流（403）。
python3 --version        # 必须 ≥3.10，<3.12（无第三方依赖，无需 pip install）
python3 -m unittest discover -s tests   # 应输出 34 tests OK
```

线上发布（可选）额外需要：本机 `vercel` 已登录且项目已关联（只在原机器保留；新机器不发布会影响 git 内报告）。

---

## 2. A 类：脚本采集（严格按序执行）

### 2.1 主命令

```sh
python3 run_report.py --refresh
```

每周正式更新用 `--refresh`（忽略跨轮缓存全量重采，约 3–8 分钟：Pi 目录约 108 页 + GitHub 采样 + OpenRouter 多窗口）。
改代码或加了编辑笔记后重渲染用**不带参数**的 `python3 run_report.py`（24h 缓存复用，秒级）。

### 2.2 逐行核对预期输出

```
采集 Codex：npm窗口与公开插件样本…
  验证插件 13；参与账号 14；采集状态 partial     ← 插件验证数 7~300 均正常（claude 最高）
采集 Claude Code / DeepSeek Harness / Pi …
读取 OpenRouter 指定窗口…
模型v2：采集跨仓库发布者并集及产品自身历史基准…
  <产品> 发布者核验：~500仓库 / ~400个去重发布者身份
  采集Pi官网完整目录与作者字段…（读到约108页）
检查历史披露源并生成全报告数据清单…
采集插件市场目录计数、官方仓库贡献者与窗口内发布…
  Codex 官方仓库贡献者 478（ok）；窗口内发布 N 个
  Claude Code 官方仓库贡献者 56（ok）；窗口内发布 N 个
  DSH 官方仓库贡献者 50（ok）；窗口内发布 N 个
  Pi 官方仓库贡献者 306（ok）；窗口内发布 N 个
完成：reports/latest.html 与 reports/latest.md
```

### 2.3 异常处理表

| 现象 | 处理 |
|---|---|
| GitHub 状态 missing，reason 含 403/预算 | 检查 `GITHUB_TOKEN` 是否生效；直接重跑一次；仍失败则记缺失照常出报告，绝不能手填 |
| npm 报"连续三个UTC日的npm哨兵包均返回零" | npm 日结延迟，等几小时或次日重跑 |
| OpenRouter 状态 missing_key | `.env` 未配置 key，回到 §1 |
| 某市场计数 missing（页面结构变化） | 修 `marketplaces.py` 对应解析正则 → 补/改 tests 里对应 fixture → 重跑。改口径前先看 §5 模板 |
| Pi 目录 partial | 记录 errors 照常出报告；下轮自动重试 |

### 2.4 产物清单（全部要进 git）

- `data/latest.json`：当轮结构化快照（报告全部数字的来源）
- `data/runs/<窗口>_<时间戳>.json`：历史快照
- `reports/latest.html`、`reports/latest.md`：两份报告
- `data/raw/`、`data/cache/`：原始响应与缓存

---

## 3. B 类：网络检索（每家依次执行，不可省略）

先从快照取窗口内版本号作为检索关键词：

```sh
python3 -c "
import json;r=json.load(open('data/latest.json'))
for pid,u in r['product_updates'].items():
    print(pid,[x['version'] for x in u['releases']])"
```

然后**按固定顺序 claude → codex → pi → dsh** 逐家检索：

| 家 | 检索词（依次尝试，命中即止） | 核对基准（脚本已采好原文） |
|---|---|---|
| Claude Code | ① `Claude Code <最新版本号> release new features` ② `Claude Code changelog <年月>` | `product_updates.claude.changelog.sections`（CHANGELOG.md 原文） |
| Codex | `OpenAI Codex CLI <stable版本> release notes new features`（**只搜 stable，如 0.167.0**；alpha 正文是占位文本） | releases 里 body_chars≥80 的 stable 版正文 |
| Pi | ① `pi coding agent <版本> release new features` ② `site:pi.dev changelog` | v1.5.0 等 release 正文 + pi.dev/changelog |
| DSH | `DeepSeek Harness <版本号> release new features` | release 正文（中文，直接引用） |

每家记录四样东西，供 §4 使用：
1. 功能要点清单（逐条，带来源 URL）；
2. 与脚本采集原文**逐条比对**的结论：一致 / 有出入（写明差异）/ 检索不到；
3. 第三方报道的头条角度（如有）；
4. 来源 URL 列表（官方 1 条 + 第三方 0–2 条）。

判定规则：检索结果与 CHANGELOG/Release 原文一致 → feature_summary 写"网络检索与<源>一致"；有出入 → 写明差异并附来源，**以官方原文为准**；检索不到 → 写"未检索到第三方报道，以官方发布说明为准"。

---

## 4. C 类：Agent 生成编辑笔记

写到 `data/editorial/<窗口结束日>.json`（窗口结束日 = `data/latest.json` 的 `window.end`，如 `2026-11-08`；独立分发的副本无历史范本时，参考 `examples/editorial-*.json`）。

### 4.1 完整 JSON 结构（字段必填情况与写法公式）

```json
{
  "window_end": "<window.end>",
  "prepared_at": "<撰写日 YYYY-MM-DD>",
  "note": "编辑内容：洞察/行动/feature_summary为人工与网络检索观点，仅本文件；报告全部数字由脚本按当轮快照采集，不手工填写。",
  "general_sources": ["四家 releases 页共4-5条URL"],
  "products": {
    "claude": {
      "insight": ["…", "…", "…"],
      "action": "…",
      "feature_summary": "…",
      "sources": ["…"]
    },
    "codex": { … }, "pi": { … }, "dsh": { … }
  }
}
```

### 4.2 逐字段生成规则

- **insight**（数组，每家 3–4 条，一条一个观点）：
  - 只写**本周窗口内新增功能点**的解读，不写用量/份额/下载（那些是 A 类数字，表格里已有）；
  - 写法公式：`<功能/主线>：<它做了什么>，<意味着什么：策略意图或方向信号>`；
  - 禁止出现当轮易变数字（份额%、环比%、下载量）；禁止跨产品用量排名表述；
  - 范例（可直接仿写）：`"功能主线是「无人值守」：denyInsteadOfPrompting 将权限提示改为策略化拒绝并继续执行"`。
- **action**（每家 1 句）：动词开头（实测/评估/跟踪/关注），由 insight 直接推出，如 `"实测codex agents --no-daemon命令中心、后端切换保留草稿与未读结果标记"`。
- **feature_summary**（每家 1 段）：套用 `"网络检索与<官方源>一致：<要点1>；<要点2>。第三方报道以<X>为头条。"`；差异与缺失按 §3 判定规则写。
- **sources**：该家检索实际用到的 URL 数组。
- 完整真实范本：`data/editorial/2026-11-08.json`（结构与口径以它为准）。

### 4.3 生成后自检

```sh
python3 -c "import json;d=json.load(open('data/editorial/<日期>.json'));print(sorted(d['products']),all(isinstance(p['insight'],list) and len(p['insight'])>=2 for p in d['products'].values()))"
# 应输出四家 id 且 insight 全为数组
```

### 4.4 嵌入与重渲染

```sh
python3 run_report.py          # 缓存模式，把编辑笔记写进快照并重渲染两份报告
```

缺失编辑笔记的周次：洞察列自动降级为脚本提取的发布要点（`窗口内N个发布，功能要点如：…`），行动列 `—`，不阻塞。

---

## 5. 报告模板（结构与格式基准，改版式不得偏离）

成品实例见 `examples/report-latest.md`（Markdown 版完整样例；HTML 结构见 5.2 描述）。

### 5.1 Markdown（`reports/latest.md`）逐节模板

```
# AI Agent Harness 市场观察周报
数据窗口：<start> — <end>（UTC）· 生成于 <北京时间>（北京时间）

## 一、四家汇总表
| Harness | 周Token（OpenRouter） | 周下载量 | 开源贡献者 | 插件数量 | 活跃用户 | 洞察（本周新功能） | 行动 |
（行序固定：Claude Code → Codex → Pi → DeepSeek Harness）

> 洞察面向本周新增功能点，行动为跟进建议，均为编辑观点；数字均由脚本按当轮快照采集，不手工填写。

## 二、用量与生态指标汇总
- KPI 一行：四家周Token总量 X（环比x%）；周请求总量 X；份额第一 <家> x%；Token环比变化最大 <家> x%
### 用量与份额（OpenRouter · 周Token）      ← 6列表：本周Token/四家内部份额/Token环比/份额周变化(pp)/本周请求
### 四周Token趋势（连续七天窗口，Token）     ← 行=四家，列=四个窗口结束日(MM-DD)
### 用户规模公开信息                          ← 4列表：产品范围/指标/公开数值/日期与说明（4行固定：Codex合计/Codex单品历史/DSH DAU/DSH MAU）
### DSH 官方披露                              ← 一行文字：日活/月活/单日Token/公开第三方插件

## 三、口径与来源
- 周Token / 周下载量 / 开源贡献者 / 插件数量 / 洞察与行动 各一条 + mcptop 口径注
```

**每列单元格格式**（汇总表，number() 规则：≥1e12→`x.xxT`；≥1e9→`x.xxB`；≥1e8→`x.xx亿`；≥1e4→`x.x万`）：

| 列 | 格式示例 |
|---|---|
| 周Token | `10.05T（份额52.6%），环比-1.5%` |
| 周下载量 | `1,419.4万（环比+10.1%）` |
| 开源贡献者 | `478（openai/codex）` |
| 插件数量 | `1,265`（纯数字，无来源标注） |
| 活跃用户 | Codex 两行：`4,000万+（Codex（含 ChatGPT Work），2026-10-07）`<br>`单品历史：超过500万WAU（2026-06-02）`；DSH：`548万MAU / 154万DAU（官方披露，2026-11-04）`；Claude/Pi：`—` |
| 洞察 | `1）xxx<br>2）yyy`（纯文本编号+换行，**不用列表标签**） |
| 行动 | 一句话；无编辑笔记时 `—` |

正式文案禁则：不出现"Markdown 版"类格式标签、仓库文件路径、字段名、"按用户指定"类实现措辞、真实 `<ol>/<ul>`。

### 5.2 HTML（`reports/latest.html`）结构

导航：核心数据 → 用量份额 → 规模与增长 → 四周趋势 → 生态与用户 → 本周新功能 → 规模估算 → 数据附录。

1. **核心数据**：4 张 KPI 卡（周Token总量/请求总量/份额第一/增长最快）+ **四家汇总表**（与 MD 同源同列，共享 `metrics.summary_rows`）；
2. 用量份额（环形图 ×2）；规模与增长（Token/请求条形）；四周趋势（折线）；
3. 生态与用户（npm 下载、GitHub 样本、DSH 披露卡）；
4. **本周新功能特性**（05）：每家一个 panel = 窗口内发布版本行 + 各版本脚本采集要点（原文引用）+ `编辑` 徽标的"网络检索核实"段 + 来源链接；
5. 规模估算、数据附录（含全量采集状态清单）。

渲染代码约束：汇总行构建与洞察降级在 `metrics.py`（`summary_rows/default_insight/user_disclosure_rows/user_cell`），HTML 渲染 `executive.py`，MD 渲染 `markdown_report.py`；**executive 与 markdown_report 不得互相 import**（共享逻辑一律放 metrics.py，否则循环依赖）。

---

## 6. 校验清单（换机零偏差验证，全过才算完成）

```sh
python3 -m unittest discover -s tests          # 34 项全 OK
python3 - <<'EOF'
import json;d=json.load(open('data/latest.json'))
assert d['openrouter_current']['status']=='ok'
assert all(v['status']=='ok' for v in d['marketplaces'].values())
assert all(v['status']=='ok' for v in d['official_repos'].values())
assert all('releases' in u for u in d['product_updates'].values())
print('快照校验通过',d['window'])
EOF
head -30 reports/latest.md                      # 汇总表4行8列、无内部路径/格式标签
python3 -c "page=open('reports/latest.html').read();assert 'summary-table' in page and 'id=\"features\"' in page;print('HTML校验通过')"
grep -c '（合计与单品分开）\|配套完整报告\|按用户指定' reports/latest.md   # 应为 0
```

## 7. 提交与发布

```sh
git add -A && git commit -m "update: 刷新周报数据至<窗口>窗口" && git push origin main
python3 deploy_report.py    # 可选，发布 https://harness-market-observer.vercel.app
                            # 白名单仅 index.html + vercel.json；MD 与数据目录不上线
```

commit 信息按当轮实际内容写（数据刷新 / 版式修改 / 逻辑修改 分开描述）。

## 8. 取数逻辑速查（改采集逻辑时对照）

| 指标 | 实现 | 关键口径 |
|---|---|---|
| OpenRouter Token/份额 | `collect.openrouter_window` | canonical app ID 在 `config.json openrouter.app_ids`；四家齐全才算份额 |
| npm 下载 | `collect.npm_downloads` | 逐日必须完整否则 missing；结算探测自动回退 |
| GitHub 插件样本 | `collect.github_ecosystem` | topic 搜索前100哈希抽样；官方仓库排除 |
| Pi 目录 | `catalogs.collect_pi_catalog` | 官网全分页、跨包去重、作者归一 |
| 三家市场计数 | `marketplaces.collect_marketplaces` | URL 在 `config.json marketplaces`；解析失败 fail closed |
| 开源贡献者 | `collect.official_repo` | `per_page=1&anon=false`，Link 头 last 页码=精确值 |
| 窗口内发布 | `changelog.collect_product_updates` | 只认 `rust-v/dsh-v/v` 前缀标签；正文<80字为占位不提要点 |
| 活跃用户披露 | `metrics.user_disclosure_rows` | 只用官方披露，合计与单品分开 |
| 规模估算 v2 | `models_v2.py` | 参数固定 config，不随周更调参 |

## 9. 常见坑

- Python 3.10：`fromisoformat` 不认 `Z` 后缀（代码已处理），别引入回归。
- codex alpha 版正文是 "Release x.y.z" 占位符，无功能信息；只有 stable 版有完整 notes。
- mcptop 页面有 Plugins 分类计数与目录全量两个数，汇总表取**分类计数**（全量在快照 `directory_total`）。
- anthropics/claude-code 公开仓贡献者仅几十人是正常的（闭源镜像开发），口径已注明。
- `--render-only` 仅供版式/审计，不能当周更命令。
- 旧快照缺新字段（如 `product_updates`）时渲染器必须优雅降级（有测试覆盖）。
