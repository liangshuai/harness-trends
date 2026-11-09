# Harness Observatory

每周生成 Codex、Claude Code、DSH、Pi 的 HTML 数据报告。Python 3.10+，macOS/Linux，无第三方依赖。

```sh
cp .env.example .env  # 已有 .env 时不要覆盖
python3 run_report.py --refresh
```

`.env` 配置 `OPENROUTER_API_KEY` 和可选 `GITHUB_TOKEN`。密钥只用于请求头，不进入报告与原始快照。

## 全报告一条命令重建

每周统一执行 `python3 run_report.py --refresh`。该模式忽略跨轮缓存，重新采集OpenRouter（含Top10、份额与四周趋势）、npm当前/前周下载、GitHub插件与贡献账号、500仓库发布者去重样本、Pi官网全目录与作者标签，再统一计算和渲染HTML。不会由助手手工填写报告数字。源页、原始JSON、计算输入、参数版本和HTML逐轮留档。单轮重复请求仍复用，避免重复调用。

历史厂商披露和模型假设是版本化的固定输入，不是每周新统计：每次检查源页并保存校验结果，始终显示其原始披露日期；来源无法访问也保留这一状态，不擅自编造或自动改口径。报告附录有全量数据清单与每项刷新状态。

`--render-only` 仅供版式修改和审计复现，不能作为每周数据更新命令。

## 输出与周更

- `reports/latest.html`：当前汇报版，开头核心数据区即四家汇总表（周Token、周下载量、开源贡献者、插件数量、活跃用户、洞察、行动），随后是份额图、四周趋势、本周新功能特性、规模估算及数据附录；断网可阅读。
- `reports/latest.md`：Markdown 版周报，正式汇报文案（不带格式标签与实现细节），开篇即同一张四家汇总表，第二节为用量与生态指标汇总（KPI、用量份额表、四周趋势表、用户规模公开信息、DSH披露）；新功能特性不在 Markdown 版中，见 HTML 完整版。
- `data/latest.json`、`data/runs/`：当前及历史结构化快照。
- `data/raw/`、`data/cache/`：公开原始响应、请求来源和缓存。
- `config.json`：产品、来源、采样上限及所有情景参数。

已配置的 Codex 自动任务每周一纽约时间上午9点运行同一命令。机器和执行环境需要可用。默认检查npm日结；两个高下载主包同时返回零时，统一回退至最近有有效下载数据的UTC日，避免把结算延迟画成下跌。

## Markdown 周报的口径与编辑笔记

汇总表数字全部脚本采集：Token与npm来自既有采集；官方仓库Contributors用 GitHub contributors（非匿名账号、与官网UI同口径，per_page=1 时 Link 头 last 页码即精确总数），只反映公开官方仓库，内部开发不计入；插件数量各家指定来源——Claude Code 取 claude.com/marketplace/plugins 公布总数、Codex 取 mcptop.com 所示 ChatGPT 插件目录 Plugins 分类计数（目录全量另存 directory_total）、Pi 取 pi.dev 官方 Package Catalog、DSH 取 dshmarket.com 公布总数，四者口径互不相同，不做横向排名。新功能特性由脚本按窗口提取官方 GitHub Releases 与 CHANGELOG.md 原文条目（`harness_trends/changelog.py`，只认产品发布线标签，占位式发布说明不算要点）。

活跃用户列只放官方披露，口径与 HTML 报告「用户规模公开信息」一致：Codex 用与 ChatGPT Work 的合计披露（4000万，2026-10-07）并保留单品历史 WAU 锚点，DSH 用 154万DAU/548万MAU（2026-11-04）；合计与单品分开、只计一次，不与 npm 下载等效情景混排；Claude Code 与 Pi 无用户数披露，留空。`user_population_policy` 合并口径为分析约定，非产品架构事实。

洞察列面向本周新增功能点：解读当周 CHANGELOG/Releases 功能主线（策略意图、方向信号），不评述用量份额等汇总数据；行动列给出跟进建议。两者与"网络检索核实"段是编辑内容，存放在 `data/editorial/<窗口结束日>.json`，运行时嵌入快照留档；文件缺失时洞察列自动降级为脚本提取的窗口内发布要点，不阻塞周更。编辑笔记只写定性判断，不复述精确数值，避免与当轮采集数字漂移；数字仍不允许手工填写。

```sh
python3 run_report.py --end 2026-11-05  # 固定窗口
python3 run_report.py --end 2026-11-05 --offline  # 缓存复算
python3 run_report.py --render-only data/latest.json  # 只重建HTML
python3 -m unittest discover -s tests -v
```

## 新增公开用户信息

报告已收录2026-10-07的Codex + ChatGPT Work合计4000万活跃用户信息：Tibo原帖未明确活跃窗口，Peter Gostev转述为周活。两条来源通过X官方oEmbed接口由脚本解析，保留产品范围和原发帖日期；预测7000万/1亿不提取为实测。按用户指定的报告分析口径，将两者统一列为“Codex（含 ChatGPT Work）”，采用4000万活跃用户参考值，只计一次；这是分析口径约定，不是产品架构事实断言。原帖未明示活跃周期时，不改写为DAU或MAU。合并规则在user_population_policy中，周更由脚本应用。6月500万WAU降为历史单品披露；基于它外推当前总体MAU的模型已停用。登记信息位于config.json的user_disclosures，周更自动核对原帖，不能声称可自动发现尚未登记的全部新帖子。

## 用户展示口径修正

厂商DAU/WAU/MAU披露与未知渠道覆盖的总体用户情景不再混排。主表仅显示四家相同参数下的npm下载用户等效情景，不能当作真实渠道MAU或总体人数；厂商披露单列。下列产品总体用户模型保留为审计假设，不进入横向用户排名。

## 规模模型 v2

**已废弃** DSH用户/下载系数跨产品迁移，以及累计仓库贡献者密度乘插件总量。旧的1.79亿Codex用户和大几十万DSH开发者不再是有效估算。历史文件保留作审计，不能与新版本直接做周环比。

用户采用不同模型，避免把不同分发渠道视为等价：

- Codex：2026-06-02官方披露超过500万WAU，以500万作保守锚；乘假设的MAU/WAU比率，并以Codex自身披露期至当期npm下载变化的弱弹性调整。不是把WAU直接当MAU，也不使用Work+Codex合计人数。
- Claude Code：2026-02-12官方披露超过25亿美元年化收入，按25亿锚定，除以假设的月均收入和付费活跃占比，再用自身分发趋势调整。得到活跃席位等效量，不是去重真实MAU；含企业和API收入归因偏差。
- DSH：保留2026-11-04的548万MAU披露，不通过下载倍数制造当期人数。
- Pi：自身下载乘人类下载占比，除以重复下载频次与npm渠道覆盖，再作月周活转换。没有绝对人数锚点，可信度低。

Pi优先直接采集官网Package Catalog：每周自动读取未筛选总数、按50条分页抓取全部包、按包名去重、按作者字段归一大小写后去重，并记录来源时间与完整性。目录包含extension、skill、theme、prompt及组合包，不冒充纯extension数量。抓取失败会记录缺失，不静默退回GitHub外推。该目录数是采集时点，不是用量窗口结束日的历史数据。

其他产品的插件独立估计：自身GitHub查询命中 × manifest样本有效率 × 每仓发布单元中位数 ÷ 假设发现覆盖。中位数避免单个大型marketplace拉高平均值，但会漏多插件长尾。DSH直接保留官方3.49万公开插件去重估算。

开发者改为**公开插件作者/维护者人数情景**：先在每家最多500个仓库中按owner ID跨仓库取并集，估计重复发布率；以插件项目数 × 去重发布者/仓库比例 × 假设的每发布者作者人数推算。组织按发布者身份处理，不把组织ID声称为一个自然人。它不包含全部工具使用者、公司员工或核心项目贡献者。

所有参数在 `models_v2` 中公开。MAU/WAU、收入ARPU、付费占比、人类下载占比、更新频次、发现覆盖率及每身份作者数都是研究者情景假设，未独立校准。区间是情景敏感性范围，不是统计置信区间。来源较旧和头部非随机样本会产生偏差；不能将不同产品估计相加为全球独立人数。

## 数据采集与口径

GitHub manifest验证默认每家检查24个候选、最多8个仓库读取累计贡献者；与用于发布者去重的最多500仓库样本分别记录。后者只检查公开仓库元数据，没有逐一验证插件内容。原始contributors按ID取并集，但不再用于开发者总量外推。

OpenRouter固定canonical app ID，排除同名Pi扩展。按指定UTC窗口回取当前、前周与四周历史；四家齐全才计算四家内部Token份额。另有最多200个已取得公开应用集合的份额图。两者都不是全市场用户份额。聚合数据按CC BY 4.0标注来源与时间。

脚本有互斥文件锁、超时、短暂失败重试、缓存与原始证据保留。GitHub请求预算默认90；未配置token可能触及平台额度，会记录缺失，不自动填零。


## Vercel 发布

线上地址：https://harness-market-observer.vercel.app

每周任务先执行 `python3 run_report.py --refresh`，成功后执行 `python3 deploy_report.py`，同步更新固定线上地址。发布脚本只复制报告到独立 `site/` 目录，上传文件白名单为 `index.html` 与 `vercel.json`；Vercel本地登录及项目关联保留在本机。`.env`、原始采集数据与采集脚本不随站点上传。
