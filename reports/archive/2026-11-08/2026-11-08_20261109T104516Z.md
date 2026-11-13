# AI Agent Harness 市场观察周报

数据窗口：2026-11-02 — 2026-11-08（UTC）· 生成于 2026-11-09 18:45（北京时间）

## 一、四家汇总表

| Harness | 周Token（OpenRouter） | 周下载量 | 开源贡献者 | 插件数量 | 活跃用户 | 本周新功能 | 行动 |
|---|---|---|---|---|---|---|---|
| Claude Code | 10.05T（份额52.6%），环比-1.5% | 1,419.4万（环比+10.1%） | 56（anthropics/claude-code） | 529 | — | 1）2.1.319：Added support for MCP tasks in the terminal: when an MCP server ru…<br>2）2.1.319：Added the CLAUDE_CODE_DISABLE_MCP_TASK_BACKGROUND environment vari…<br>3）2.1.319：Added permissions.denyInsteadOfPrompting setting: a tool call that…<br>4）2.1.319：Added /claude-api latency-optimize to find where your Claude API c…<br>5）2.1.319：Added the CLAUDE_CODE_DISABLE_FEATURE_FLAGS environment variable, … | 评估denyInsteadOfPrompting对CI/子代理场景的适配成本；对照网关新能力（成本报表、pooled预算）评估企业侧管理开销是否下降。 |
| Codex | 2.62T（份额13.7%），环比-52.1% | 2,590.8万（环比-6.9%） | 478（openai/codex） | 1,265 | 4,000万+（Codex（含 ChatGPT Work），2026-10-07）<br>单品历史：超过500万WAU（2026-06-02） | 1）0.167.0：Open the agent command center with codex agents --no-daemon. The c…<br>2）0.167.0：Switch between connected backends from the terminal session picker…<br>3）0.167.0：Preview local image attachments while composing on supported termi…<br>4）0.167.0：Find API key and cloud provider options under “Sign in another way…<br>5）0.167.0：Opt into macOS or Windows system proxy settings from /experimental… | 实测codex agents --no-daemon命令中心、后端切换保留草稿与未读结果标记；评估多后端切换对混合云/多供应商部署的实际价值。 |
| Pi | 4.20T（份额22.0%），环比-7.6% | 663.4万（环比+5.5%） | 306（earendil-works/pi） | 5,360 | — | 1）1.5.0：Extension update changelogs: see what changed in installed extensi…<br>2）1.5.0：Faster streaming: large tool calls are parsed incrementally, and c…<br>3）1.5.0：Custom self-update commands: use PI_SELF_UPDATE_COMMAND or selfUpd…<br>4）1.5.0：GPT-6.1 Terra: available through OpenAI, Azure OpenAI Responses, a… | 研究扩展changelog与OSC 7501对外部集成面板的开放思路对自研harness插件体系的借鉴价值。 |
| DeepSeek Harness | 2.25T（份额11.8%），环比+19.3% | 82.7万（环比+8.1%） | 50（deepseek-ai/deepseek-harness） | 9,463 | 548万MAU / 154万DAU（官方披露，2026-11-04） | 1）0.2.2-rc.1：完善手机和平板适配，优化软键盘交互、导航与窄屏布局，保持菜单和操作入口可用。 @Stevring, @turtle2099, @Le…<br>2）0.2.2-rc.1：支持将聊天文本作为引用插入输入框，并在发送后显示紧凑预览。 @lsdsjy, @imccyu<br>3）0.2.2-rc.1：支持将完整历史会话复制为 Markdown，包含可用的原始日志路径。 @tianyicui<br>4）0.2.2-rc.1：工作步骤收起后保留全部助手文字回复，可切换为仅最终回答。 @imccyu<br>5）0.2.2-rc.1：支持统一右键与键盘菜单，覆盖会话、工作区和侧边栏，并支持开发者扩展。 @std4453 | 关注subagent_oar插件（把独立任务交给本机Codex/Claude CLI）的跨harness调度思路能否借鉴；评估插件热更新回滚机制对自家插件运维的参考价值。 |

> 本周新功能列为脚本采集的官方发布要点摘录；行动为编辑建议；数字均由脚本按当轮快照采集，不手工填写。

## 二、用量与生态指标汇总

- 四家周Token总量 19.11T（环比-13.5%）；周请求总量 2.06亿；份额第一 Claude Code 52.6%；Token环比变化最大 DSH +19.3%

### 用量与份额（OpenRouter · 周Token）

| Harness | 本周Token | 四家内部份额 | Token环比 | 份额周变化 | 本周请求 |
|---|---|---|---|---|---|
| Claude Code | 10.05T | 52.6% | -1.5% | +6.4 pp | 9,838.5万 |
| Pi | 4.20T | 22.0% | -7.6% | +1.4 pp | 4,090.6万 |
| Codex | 2.62T | 13.7% | -52.1% | -11.0 pp | 5,196.1万 |
| DSH | 2.25T | 11.8% | +19.3% | +3.2 pp | 1,443.4万 |

### 四周Token趋势（连续七天窗口，Token）

| Harness | 10-18 | 10-25 | 11-01 | 11-08 |
|---|---|---|---|---|
| Claude Code | 9.92T | 12.67T | 10.20T | 10.05T |
| Codex | 1.23T | 2.13T | 5.47T | 2.62T |
| Pi | 2.92T | 5.21T | 4.55T | 4.20T |
| DSH | 1.47T | 2.89T | 1.88T | 2.25T |

### 用户规模公开信息

| 产品范围 | 指标 | 公开数值 | 日期与说明 |
|---|---|---|---|
| Codex（含 ChatGPT Work） | 活跃用户（窗口未明确） | 4,000万 | 2026-10-07；合计口径 · 只计一次；活跃窗口未明示 |
| Codex（历史单品数据） | 历史WAU / 周活 | 超过500万 | 2026-06-02；不是当前人数 |
| DSH | DAU / 日活 | 154万 | 2026-11-04；官方API用户范围 |
| DSH | MAU / 月活 | 548万 | 2026-11-04；月窗口未明示 |

### DSH 官方披露

截至 2026-11-04（媒体转述厂商披露，不同于OpenRouter渠道数据）：日活 154.0万；月活 548.0万；单日Token 92.10T；公开第三方插件 3.5万（已去重）。

## 三、口径与来源

- **周Token**：OpenRouter app-rankings 数据集，canonical app ID，窗口 2026-11-02 — 2026-11-08；只含OpenRouter可归因渠道，不代表全市场用量。Source: OpenRouter (openrouter.ai/apps), CC BY 4.0.
- **周下载量**：npm downloads API 逐日加总的主包七天下载，含更新、CI 与重复下载，不等于活跃用户。
- **开源贡献者**：官方公开仓库的 GitHub contributors（非匿名账号，与官网UI同口径）；仅统计公开官方仓库，闭源/内部镜像开发不计入，厂商间口径差异见各行仓库名。
- **插件数量**：Claude Code 取 claude.com/marketplace/plugins 页面公布总数；Codex 取 mcptop.com 所示 ChatGPT 插件目录 Plugins 分类计数（该目录另有全量口径，见下注）；Pi 取 pi.dev 官方 Package Catalog 未筛选总数（含 extension/skill/theme/prompt 等类型，非纯 extension）；DSH 取 dshmarket.com 公布的社区插件总数。四者口径互不相同，不可直接横向排名。
- **本周新功能/行动**：本周新功能列为脚本按窗口提取的官方 Releases/CHANGELOG 要点摘录（截断显示，完整原文见HTML报告「本周新功能特性」部分）；行动为编辑建议，不属于采集数据。
- 注：ChatGPT 插件目录全量 12,404 个，本表取 Plugins 分类计数 1,265（mcptop.com，2026-11-09观测）。
