# AI Agent Harness 市场观察周报 · Markdown 版

数据窗口：2026-11-02 — 2026-11-08（UTC）· 生成于 2026-11-09 15:59（北京时间）· 方法版本 0.1.0
HTML 版：`reports/latest.html`；结构化快照：`data/latest.json`。

## 一、四家汇总表

| Harness | 周Token（OpenRouter） | 周npm下载 | 官方仓库Contributors | 插件数量 | 洞察（本周新功能） | 行动 |
|---|---|---|---|---|---|---|
| Claude Code | 10.05T（份额52.6%），环比-1.5% | 1,419.4万（环比+10.1%） | 56（anthropics/claude-code） | 529（Claude官方Marketplace） | 本周3版的功能主线是「无人值守」：denyInsteadOfPrompting把权限提示改为策略化拒绝并继续执行、MCP任务自动后台化、auto mode在网关侧强制服务端检查——权限模型从「人守着点允许」转向可审计的自动化运行；同时网关类功能（pooled预算规则、login_notice、JSON日志、成本报表）密集落地，显示企业网关是当前迭代重心。 | 评估denyInsteadOfPrompting对CI/子代理场景的适配成本；对照网关新能力（成本报表、pooled预算）评估企业侧管理开销是否下降。 |
| Codex | 2.62T（份额13.7%），环比-52.1% | 2,590.8万（环比-6.9%） | 478（openai/codex） | 1,265（ChatGPT插件目录（mcptop.com）） | 0.167.0的功能指向「多Agent统一调度」：Agent Command Center集中管理多个agent并标记未读结果、会话级后端切换保留草稿、本地图片预览与Vertex AI向导降低多云接入门槛——从单会话CLI转向调度面板，且明显在做多后端/多云以降低锁定；高频alpha+周度stable的节奏不变。 | 实测codex agents --no-daemon命令中心、后端切换保留草稿与未读结果标记；评估多后端切换对混合云/多供应商部署的实际价值。 |
| Pi | 4.20T（份额22.0%），环比-7.6% | 663.4万（环比+5.5%） | 306（earendil-works/pi） | 5,360（pi.dev官方Package Catalog） | 1.5.0的功能全部围绕「扩展生态的可维护性」：扩展更新changelog给作者一条触达用户的发布说明通道、流式渲染提速优化大输出体验、自定义自更新命令适配各种包管理器、OSC 7501把运行状态暴露给终端/面板——持续做可组合底座而非功能堆叠，生态基础设施优先于单点能力。 | 研究扩展changelog与OSC 7501对外部集成面板的开放思路对自研harness插件体系的借鉴价值。 |
| DeepSeek Harness | 2.25T（份额11.8%），环比+19.3% | 82.7万（环比+8.1%） | 50（deepseek-ai/deepseek-harness） | 9,463（dshmarket.com） | 0.2.2-rc.1的功能集中在「补易用性短板」：手机/平板适配、六种新语言、引用插入、历史导出Markdown、统一右键菜单，都是在向日常工具的可用性靠拢而非堆模型能力；插件热更新失败自动回滚与富文本详情页在强化「一切皆插件」的运维体验；实验性subagent_oar直接调度本机Codex/Claude CLI当子代理，是跨harness整合的差异化信号。 | 关注subagent_oar插件（把独立任务交给本机Codex/Claude CLI）的跨harness调度思路能否借鉴；评估插件热更新回滚机制对自家插件运维的参考价值。 |

> 洞察面向本周新增功能点，与行动均为编辑观点（`data/editorial/2026-11-08.json`，2026-11-09整理）；数字均由脚本按当轮快照采集，不手工填写。

## 二、本周新功能特性（脚本采集 CHANGELOG / Releases，网络检索交叉核实）

### Claude Code
- **窗口内发布**：2.1.319、2.1.318、2.1.317（来源：GitHub Releases + CHANGELOG.md）
- **2.1.319**（2026-11-06，正式版，CHANGELOG.md）要点：
  - Added support for MCP tasks in the terminal: when an MCP server runs a tool call as a task, Claude Code moves it to the background right away and tells Claude the result when it finishes
  - Added the CLAUDE_CODE_DISABLE_MCP_TASK_BACKGROUND environment variable to make Claude Code wait for an MCP task inside its tool call instead of moving it to the background right away
  - Added permissions.denyInsteadOfPrompting setting: a tool call that would wait on a permission prompt is denied and the turn continues, in terminal sessions, subagents and teammates
  - Added /claude-api latency-optimize to find where your Claude API code makes people wait and try faster settings against your eval
  - Added the CLAUDE_CODE_DISABLE_FEATURE_FLAGS environment variable, which stops feature-flag fetching without turning off telemetry; every flag then uses its built-in default
  - Added spend for today, this week and this month to /usage for developers behind a Claude apps gateway who have no spend limit, when the gateway runs this version or later
  - Added admin.pooled_conflict_rule and admin.pooled_priority_order to the Claude apps gateway, to set which pooled group budget pays first for a developer in several groups
  - Added an optional login_notice setting to the Claude apps gateway that shows an operator-defined message on the gateway's browser verification page and on Claude Code's sign-in screen
- **2.1.318**（2026-11-04，正式版，CHANGELOG.md）要点：
  - Added a record of your answer when Claude Code asks to turn on the mods it writes in a session
  - Added assume_role on mantle upstreams of the Claude apps gateway, for a role in another AWS account and for per-developer AWS cost attribution
  - Added an effort option to a mod's $.model.fork, so a quick side job can run at low whatever effort the session uses; the result reports the effort sent
  - Added the date a stored claude.ai sign-in ends to claude auth status (loginExpiresAt) and to claude -p JSON results (credential_expires_at)
  - Added a one-line stderr warning to claude -p text output, starting 10 days before a stored claude.ai sign-in ends
- **2.1.317**（2026-11-03，正式版，CHANGELOG.md）要点：
  - Added a warning to /schedule when a new cloud scheduled task gets connectors you did not ask for, with how to remove them
  - Added a check that asks before a web or shell tool call sends your account email address to the network
  - Added onFailure: "block" for Agent SDK hook callbacks, so a callback that fails blocks the action instead of letting it run
  - Added a notice in Claude Desktop's Code tab when your organization's remote managed settings haven't loaded for the session, and another once they do
  - Added a notice when auto mode's check has no answer for a subagent's tool call, which used to leave nothing in the main view
  - Added anthropic.plan, anthropic.seat_type, anthropic.provider and anthropic.custom_base_url to OTel metrics, events and spans
  - Added a cost report to the Claude apps gateway admin API, GET /v1/organizations/analytics/cost, for reading past spend over a date range in total, per developer, per day or per IdP group
  - Added a daily record of each developer's IdP groups on Claude apps gateways with admin: set, kept for admin.identity_retention_days, which the cost report groups by
- **网络检索核实（编辑）**：网络检索与CHANGELOG.md一致：v2.1.319新增permissions.denyInsteadOfPrompting（权限提示改为拒绝并继续）、MCP任务自动后台化（可用CLAUDE_CODE_DISABLE_MCP_TASK_BACKGROUND关闭）、auto mode在网关/关闭遥测时改走服务端检查；另新增/claude-api latency-optimize、/usage消费展示与/tasks的Earlier in this session行。第三方报道亦以denyInsteadOfPrompting为头条。
  - 来源：https://github.com/anthropics/claude-code/releases
  - 来源：https://support.claude.com/en/articles/12138966-release-notes
  - 来源：https://releasebot.io/updates/anthropic/claude-code

### Codex
- **窗口内发布**：0.169.0-alpha.3、0.169.0-alpha.2、0.167.0、0.168.0-alpha.7、0.168.0-alpha.6、0.168.0-alpha.3、0.167.0-alpha.3.2、0.168.0-alpha.2、0.168.0-alpha.1、0.167.0-alpha.5、0.167.0-alpha.3.1、0.167.0-alpha.4（来源：GitHub Releases + CHANGELOG.md）
- **0.167.0**（2026-11-06，正式版，GitHub Release）要点：
  - Open the agent command center with codex agents --no-daemon. The command center and session picker now mark unread results (#58238, #58239, #58263, #58264).
  - Switch between connected backends from the terminal session picker and keep your drafts when switching (#58280, #58457).
  - Preview local image attachments while composing on supported terminals, and open viewed local images from clickable transcript paths (#58261, #58446).
  - Find API key and cloud provider options under “Sign in another way.” Enable gcp_setup_wizard to set up Google Cloud Vertex AI with Application Default Credentials or a credential file (#57857, #58427).
  - Opt into macOS or Windows system proxy settings from /experimental (#58157).
  - Expand patch details directly in the transcript while an approval prompt is open (#58281).
- **网络检索核实（编辑）**：网络检索与官方Release Notes一致：0.167.0以Agent Command Center（codex agents --no-daemon）为头条，命令中心与会话选择器标记未读结果；支持后端切换保留草稿、本地图片预览、gcp_setup_wizard（Vertex AI）向导与系统代理设置opt-in。窗口内alpha版（0.168/0.169系列）发布说明为占位文本，未单独核实功能点。
  - 来源：https://github.com/openai/codex/releases
  - 来源：https://developers.openai.com/codex/release-notes

### Pi
- **窗口内发布**：1.5.0（来源：GitHub Releases）
- **1.5.0**（2026-11-02，正式版，GitHub Release）要点：
  - Extension update changelogs: see what changed in installed extension packages on the next fresh launch after an update. Package authors can choose the changelog path, and collapseChangelog condenses the notices. See Show a changelog.
  - Faster streaming: large tool calls are parsed incrementally, and code-heavy answers and tool rows reuse highlighting and rendered Markdown instead of repeating the work on every update. See Keep rendering responsive.
  - Custom self-update commands: use PI_SELF_UPDATE_COMMAND or selfUpdateCommand to update pi through a wrapper or another package manager. See Custom update command.
  - GPT-6.1 Terra: available through OpenAI, Azure OpenAI Responses, and OpenAI Codex, with tool search, mid-conversation thinking-level changes, and thinking off. Codex offers a 500K context window. See Models.
- **网络检索核实（编辑）**：网络检索与pi.dev官方changelog一致：1.5.0新增扩展更新changelog展示（作者可选路径、collapseChangelog折叠）、大工具调用增量解析与高亮/Markdown渲染复用提速、OSC 7501程序状态上报（工作/阻塞/完成）、自定义自更新命令与GPT-6.1 Terra接入；npm包@earendil-works/pi-coding-agent同步发布1.5.0。
  - 来源：https://pi.dev/changelog/releases/1.5.0
  - 来源：https://github.com/earendil-works/pi/releases

### DeepSeek Harness
- **窗口内发布**：0.2.2-rc.1、0.2.2-alpha.3（来源：GitHub Releases）
- **0.2.2-rc.1**（2026-11-04，预发布，GitHub Release）要点：
  - 完善手机和平板适配，优化软键盘交互、导航与窄屏布局，保持菜单和操作入口可用。 @Stevring, @turtle2099, @LegGasai, @EricMoin, @Saafo
  - 支持将聊天文本作为引用插入输入框，并在发送后显示紧凑预览。 @lsdsjy, @imccyu
  - 支持将完整历史会话复制为 Markdown，包含可用的原始日志路径。 @tianyicui
  - 工作步骤收起后保留全部助手文字回复，可切换为仅最终回答。 @imccyu
  - 支持统一右键与键盘菜单，覆盖会话、工作区和侧边栏，并支持开发者扩展。 @std4453
  - 文件预览支持常驻目录树和文件定位功能。 @yudshj
  - 新增日语、西班牙语、法语、德语、俄语和巴西葡萄牙语文案与界面配置。 @07akioni
  - 插件管理页支持展示富文本详情，并改善页面布局和导航行为。 @turtle1999, @turtle2099
- **0.2.2-alpha.3**（2026-11-03，预发布，GitHub Release）要点：
  - 支持统一右键与键盘菜单，覆盖会话、工作区和侧边栏，并支持开发者扩展 @std4453
  - 文件预览支持常驻目录树和文件定位功能。 @yudshj
  - 实验性「变更请求与工作树」统一代码审查与工作树入口，支持通过可搜索文件树和逐文件导航查看本地及 PR 差异，将选中代码和评论交给 Agent，并跟踪检查与评审状态。 @LegGasai
- **网络检索核实（编辑）**：网络检索与GitHub Release一致：v0.2.2-rc.1汇总自v0.2.1-rc.5的变更：手机/平板适配与软键盘交互、聊天文本引用插入、完整历史会话复制为Markdown、统一右键与键盘菜单、插件管理页富文本与第三方插件更新（失败自动回滚）、实验性subagent_oar插件及日/西/法/德/俄/巴葡六种新语言界面。
  - 来源：https://github.com/deepseek-ai/deepseek-harness/releases

## 三、口径与来源

- **周Token**：OpenRouter app-rankings 数据集，canonical app ID，窗口 2026-11-02 — 2026-11-08；只含OpenRouter可归因渠道，不代表全市场用量。Source: OpenRouter (openrouter.ai/apps), CC BY 4.0.
- **周npm下载**：npm downloads API 逐日加总的主包七天下载，含更新、CI 与重复下载，不等于活跃用户。
- **官方仓库Contributors**：GitHub REST contributors（非匿名账号，与官网UI同口径，Link头last页码精确计数）；仅统计公开官方仓库，闭源/内部镜像开发不计入，厂商间口径差异见各行仓库名。
- **插件数量**：Claude Code 取 claude.com/marketplace/plugins 页面公布总数；Codex 取 mcptop.com 所示 ChatGPT 插件目录 Plugins 分类计数（该目录另有全量口径，见数据快照 directory_total）；Pi 取 pi.dev 官方 Package Catalog 未筛选总数（含 extension/skill/theme/prompt 等类型，非纯 extension）；DSH 取 dshmarket.com 公布的社区插件总数。四者口径互不相同，不可直接横向排名。
- **新功能特性**：脚本按窗口提取官方 GitHub Releases 与 CHANGELOG.md 条目（原文引用，未翻译）；「网络检索核实」为编辑内容，附来源链接，与脚本采集分开标注。
- **洞察/行动**：面向本周新增功能点的编辑解读与建议，不属于采集数据；无编辑笔记的周次自动降级为脚本提取的发布要点摘要。
- 注：ChatGPT 插件目录全量 12,404 个，本表按用户指定取 Plugins 分类计数 1,265。（mcptop.com 观测于 2026-11-09）

原始响应与逐项采集状态见 `data/raw/`、`data/runs/` 与 HTML 版附录数据清单。
