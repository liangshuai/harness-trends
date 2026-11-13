# Coding Agent Harness市场观察周报

数据窗口：2026-11-05 — 2026-11-11（UTC）· 生成于 2026-11-13 09:15（北京时间）

## 一、主流Harness汇总表

| Harness | 周Token（OpenRouter） | 周下载量 | 开源贡献者 | 插件数量 | 活跃用户 | 本周新功能 | 洞察 |
|---|---|---|---|---|---|---|---|
| Claude Code | 10.56T（份额52.2%），环比+1.1% | 1,625.4万（环比+22.1%） | 56（anthropics/claude-code） | 531 | — | 1）Fable 5.2 成为默认 Fable 模型：1M 上下文，$8/$40 每百万Token（2.1.321）<br>2）Vertex 上线 fast mode（global/us/eu），拒绝时自动回退标准速度（2.1.322）<br>3）claude remote-control 新增 --settings，为每个会话套用统一设置文件<br>4）MCP 任务后台化与 denyInsteadOfPrompting 无人值守权限策略（2.1.319） | 1）fast mode 按区域自动回退：模型加速与渠道解耦的多云降级范式<br>2）remote-control --settings：远程批量会话统一配置，企业集中管理共性需求 |
| Codex | 3.34T（份额16.5%），环比-33.3% | 2,623.4万（环比-1.1%） | 477（openai/codex） | 1,269 | 4,000万+（Codex（含 ChatGPT Work），2026-10-07）<br>单品历史：超过500万WAU（2026-06-02） | 1）Agent Command Center（codex agents --no-daemon）集中管理多个 agent，未读结果标记（0.167.0）<br>2）会话级后端切换保留草稿；本地图片预览与 Vertex AI 配置向导（0.167.0）<br>3）0.167.2：Vertex AI 默认增量发送工具声明，请求更轻量，可配置回退 | 1）增量工具声明：随工具数增长只发 diff，是请求瘦身的通用解法<br>2）Command Center 与草稿保留持续打磨多 agent 并行的体验细节 |
| Pi | 4.04T（份额20.0%），环比+2.3% | 678.8万（环比+7.9%） | 308（earendil-works/pi） | 5,502 | — | 1）pi auth login/logout：免启动会话即可登录登出，支持 API key（1.5.1）<br>2）空闲提示词缓存保温至30分钟，跨运行降低重复任务成本（1.5.1）<br>3）Anthropic 消息线程：只发送新增消息续接对话（1.5.1）<br>4）原目录被移动/删除的会话可 fork 到新位置（1.5.2） | 1）空闲缓存保温30分钟：小改动直接降低重复任务成本，值得借鉴<br>2）消息线程只发增量：长会话带宽与延迟优化的共性思路 |
| DeepSeek Harness | 2.27T（份额11.2%），环比+9.4% | 83.7万（环比+5.0%） | 52（deepseek-ai/deepseek-harness） | 10,581 | 548万MAU / 154万DAU（官方披露，2026-11-04） | 1）Git Worktree：按分支/提交/文件类型审阅改动，直连 GitHub 评审并同步进度<br>2）SubAgent 具名与多层协作；AgentTeam 按会话开启，共用成员与任务面板<br>3）桌面端支持切换正式版与开发版更新渠道 | 1）AgentTeam 按会话共享成员与任务面板：多agent协作编排的直观实现<br>2）Worktree 评审直连 GitHub 并同步状态：把审查工作流嵌入 harness |

> 洞察基于本周新增功能的分析，不反映数据变化情况；所涉产品均为第三方产品，其数据波动无法溯源。

**行动：本周最值得深入研究或借鉴**：1）「请求瘦身」两例值得深研：Claude Code 按区域自动回退的 Vertex fast mode、Codex 增量工具声明 2）DSH AgentTeam 多agent协作面板与 Pi 空闲缓存保温，可直接借鉴

## 二、用量与生态指标汇总

- 四家周Token总量 20.21T（环比-5.9%）；周请求总量 2.21亿；份额第一 Claude Code 52.2%；Token环比变化最大 DSH +9.4%

### 用量与份额（OpenRouter · 周Token）

| Harness | 本周Token | 四家内部份额 | Token环比 | 份额周变化 | 本周请求 |
|---|---|---|---|---|---|
| Claude Code | 10.56T | 52.2% | +1.1% | +3.6 pp | 1.08亿 |
| Pi | 4.04T | 20.0% | +2.3% | +1.6 pp | 3,929.8万 |
| Codex | 3.34T | 16.5% | -33.3% | -6.8 pp | 5,955.1万 |
| DSH | 2.27T | 11.2% | +9.4% | +1.6 pp | 1,433.0万 |

### 四周Token趋势（连续七天窗口，Token）

| Harness | 10-21 | 10-28 | 11-04 | 11-11 |
|---|---|---|---|---|
| Claude Code | 11.59T | 11.02T | 10.45T | 10.56T |
| Codex | 1.43T | 2.78T | 5.01T | 3.34T |
| Pi | 3.37T | 5.97T | 3.95T | 4.04T |
| DSH | 2.40T | 2.23T | 2.07T | 2.27T |

### 用户规模公开信息

| 产品范围 | 指标 | 公开数值 | 日期与说明 |
|---|---|---|---|
| Codex（含 ChatGPT Work） | 活跃用户（窗口未明确） | 4,000万 | 2026-10-07；合计口径 · 只计一次；活跃窗口未明示 |
| Codex（历史单品数据） | 历史WAU / 周活 | 超过500万 | 2026-06-02；不是当前人数 |
| DSH | DAU / 日活 | 154万 | 2026-11-04；官方API用户范围 |
| DSH | MAU / 月活 | 548万 | 2026-11-04；月窗口未明示 |

## 三、口径与来源

- **周Token**：OpenRouter app-rankings 数据集，canonical app ID，窗口 2026-11-05 — 2026-11-11；只含OpenRouter可归因渠道，不代表全市场用量。Source: OpenRouter (openrouter.ai/apps), CC BY 4.0.
- **周下载量**：npm downloads API 逐日加总的主包七天下载，含更新、CI 与重复下载，不等于活跃用户。
- **开源贡献者**：官方公开仓库的 GitHub contributors（非匿名账号，与官网UI同口径）；仅统计公开官方仓库，闭源/内部镜像开发不计入，厂商间口径差异见各行仓库名。
- **插件数量**：Claude Code 取 claude.com/marketplace/plugins 页面公布总数；Codex 取 mcptop.com 所示 ChatGPT 插件目录 Plugins 分类计数（该目录另有全量口径，见下注）；Pi 取 pi.dev 官方 Package Catalog 未筛选总数（含 extension/skill/theme/prompt 等类型，非纯 extension）；DSH 取 dshmarket.com 公布的社区插件总数。四者口径互不相同，不可直接横向排名。
- **本周新功能/洞察**：本周新功能列为编辑从当周官方 Releases/CHANGELOG 中总结挑选的重点摘要（经网络检索核实）；洞察为编辑对新增功能中值得同行借鉴的价值点与共性需求的分析，不反映数据变化；无编辑笔记的周次本周新功能自动降级为脚本提取的原文摘录。
- 注：ChatGPT 插件目录全量 13,550 个，本表取 Plugins 分类计数 1,269（mcptop.com，2026-11-13观测）。
