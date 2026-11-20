# AI Harness 市场观察周报

数据窗口：2026-11-12 — 2026-11-18

详细报告：https://harness.mise.fun

## 一、主流Harness汇总表

| Harness | 周 Token 使用量（万亿） | OpenRouter市场份额 | 周下载量 | 开源贡献者 | 插件数量 | 本周新功能 | 洞察和行动 |
|---|---|---|---|---|---|---|---|
| Claude Code | 11.03T（**↑4.4%**） | 16.3% | 2,016.3万（**↑24.0%**） | 56 | 534 | 1）Code Mode 实验特性上线：Claude 通过编写 JavaScript 调用工具，并可与 agent teams 同开（2.1.323/2.1.326）<br>2）claude mcp add-json - 从 stdin 读取服务器 JSON，令牌不再暴露在命令行（2.1.327）<br>3）/status 列出损坏的 agent、技能、命令与输出样式文件及快捷键错误（2.1.327）<br>4）/install-github-app 变更仓库前增加确认（2.1.327） | 洞察：<br>1）Code Mode 与 agent teams 打通：代码化工具编排进入多agent协作主流程<br>2）mcp 配置走 stdin 传递：凭据不落命令行与进程列表，企业部署的共性安全需求<br>行动：<br>可借鉴 Code Mode 与 agent teams 的组合方式，在底座多agent编排中统一代码化工具调用，并把敏感配置改为 stdin/文件传递（计划 2026-12-05 前） |
| Pi | 4.61T（**↑14.0%**） | 6.8% | 698.9万（**↑3.0%**） | 309 | 5,423 | — | — |
| Codex | 2.92T（**↓12.6%**） | 4.3% | 2,732.2万（**↑4.1%**） | 480 | 1,297 | 1）TUI 内 WebRTC 实时语音通话（0.170.0，11-18）<br>2）终端工作区多 side-chat 标签；Command Center 按名称/提示/目录检索历史任务（0.169.0）<br>3）Sessions → Model Providers 浏览并选默认模型；终端内增改自定义模型供应商（0.168.0/0.169.0）<br>4）跨环境同名 MCP 服务器实验支持（0.170.0） | 洞察：<br>1）终端内实时语音（WebRTC）：语音交互进入 CLI 编码 agent 的主流形态<br>2）同名 MCP 服务器跨环境并存：按环境隔离同名工具服务的配置组织方式<br>行动：<br>可借鉴 Codex 的多环境 MCP 配置隔离与终端内模型供应商管理，为底座补齐多租户/多环境的工具与模型配置面（计划 2026-12-10 前） |
| DeepSeek Harness | 2.34T（**↑3.2%**） | 3.4% | 66.5万（**↓20.5%**） | 53 | 11,979 | 1）实验性「DeepSeek 会话导入」插件：把 DeepSeek App/网页版历史会话导入工作区继续对话（rc.3，11-13）<br>2）DeepSeek 模型改用服务端搜索且不按次收费，其他模型默认 DeepSeek Search API（rc.5，11-18）<br>3）修复 LiveShare 桌面端无法创建分享与异常响应处理（rc.4，11-17） | 洞察：<br>1）会话导入插件：把存量用户从 App/网页无摩擦迁入本地 harness，是低摩擦获客思路<br>2）服务端搜索不计次收费：把搜索成本内化到模型服务侧的定价设计<br>行动：<br>可借鉴会话导入的迁移思路，为底座提供从主流 Chat 产品的会话迁移入口，降低用户切换成本（计划 2026-11-30 前） |

**官方披露**

- **Codex**：2026-10-07 披露活跃用户 4,000万+（Codex 与 ChatGPT Work 合计口径）
- **DeepSeek Harness**：2026-11-04 披露日活 154万、月活 548万、单日Token 92.10万亿、公开第三方插件 3.49万

## 二、Token使用情况（行业）

- 四家周Token总量 20.89T（环比+3.4%）；周请求总量 2.14亿；份额第一 Claude Code 52.8%；Token环比变化最大 Pi +14.0%

### 模型使用量及占比

| Harness | 周 Token 使用量 | 样本内 Token 占比 | Token 使用量周环比 | 占比周变化（百分点） | 周模型请求量 |
|---|---|---|---|---|---|
| Claude Code | 11.03T | 52.8% | +4.4% | +0.5 | 1.05亿 |
| Pi | 4.61T | 22.1% | +14.0% | +2.0 | 4,826.8万 |
| Codex | 2.92T | 14.0% | -12.6% | -2.6 | 4,737.6万 |
| DSH | 2.34T | 11.2% | +3.2% | -0.0 | 1,379.8万 |

### 近四周 Token 使用量趋势（连续七天窗口，Token）

| Harness | 10-28 | 11-04 | 11-11 | 11-18 |
|---|---|---|---|---|
| Claude Code | 11.02T | 10.45T | 10.56T | 11.03T |
| Codex | 2.78T | 5.01T | 3.34T | 2.92T |
| Pi | 5.97T | 3.95T | 4.04T | 4.61T |
| DSH | 2.23T | 2.07T | 2.27T | 2.34T |

## 三、OpenRouter Top 10 动向

- 本周 Top 10 无新增应用。
- **本周增长最多**：Kilo Code（第3名 · 周 Token 8.32T，环比↑59.6%）——IDE插件：VS Code 等主流 IDE 的开源编码 agent 扩展

## 四、AI Coding 行业资讯

1）微软 11-17 在 Ignite 2026 发布 MAI Code 2 与 Code 2 Flash（共七款新模型），以远低于头部的价格逼近其编码质量，编码模型进入性价比竞争阶段

- ① 核心数据：官方称达到 GPT-6.1 Sol 编码质量的 98%、约 40% 价格；Claude Opus 5.5 的 96%、约 5% 价格
- ② 量化结果：四项编码基准均值通过率 63.2%，单任务成本 $0.309（对比 $0.761 与 $6.306）；定价 $0.50/百万输入、$2.50/百万输出（2027-05-17 前介绍价），已进入 GitHub Copilot
- ③ 指引：建议把「单任务成本（$/task）」而非 $/Mtok 纳入底座模型选型指标；在模型路由层建质量-成本二维评估，用同一基准集自测新模型再决定流量比例
- 补充：数据来自微软官方发布（11-17）；基准与价格细节经第三方 felloai 整理（11-17 后），介绍价可能调整，采用前以官方定价页为准。
- 来源：https://microsoft.ai/news/introducing-mai-code-2-and-mai-code-2-flash
- 来源：https://microsoft.ai/news/microsoft-ignite-2026
- 来源：https://felloai.com/mai-code-2

2）Postman 11-18 发布《2026 State of the API》：四分之一组织已在生产环境经 API 运行 AI agents，API 就绪度成为落地瓶颈

- ① 核心数据：25% 的受访组织已在生产环境通过 API 运行 AI agents
- ② 判断：报告指出 agent 采纳速度与 API 治理/就绪度脱节——agent 在扩、API 的配额、版本与审计没跟上
- ③ 指引：建议对自有产品输出面做 API 清单与分级（明确哪些可被 agent 调用），为 agent 流量单设配额与审计端点；底座侧应补齐 agent-API 网关能力
- 补充：BusinessWire 通稿发布于 11-18，结论以 Postman 官方报告全文为准。
- 来源：https://www.businesswire.com/news/home/20261118374573/en/One-in-Four-Organizations-Now-Run-AI-Agents-on-APIs-in-Production-Postmans-2026-State-of-the-API-Report-Finds

3）字节 TRAE CN 个人版账号 11-18 起自动并入豆包飞书账号体系，AI 编程工具账号向集团统一 ID 收拢

- ① 生效范围：11-18 起仅 CN 个人版自动升级，企业版不在范围内
- ② 迁移承诺：代码、项目、历史记录与会员权益全量保留，无需用户操作
- ③ 指引：统一账号与数据体系是 AI 编程工具留存和生态导流的基础设施；底座侧应支持组织级 SSO 与工作区数据可迁移（导入/导出）能力
- 补充：官方公告发布于 11 月上旬（docs.trae.cn），生效日 11-18 在本周窗口内；IT之家等 11-06 起报道，注意区分公告时间与生效时间。
- 来源：https://docs.trae.cn/ide_important-notice-for-trae-account-upgrade-and-integration
- 来源：https://www.ithome.com/1/023/552.htm

4）GitHub 11-16 起 Copilot 下架多款旧模型（含 Claude Opus 4.8 退役），与 MAI Code 2 低价上市同周，编码模型供给加速换血

- ① 变更：多款模型从多数 Copilot 体验中 deprecated；Claude Opus 4.8 退役，仅年付个人订户保留
- ② 组合判断：旧模型退场与新模型低价入市同周发生，平台侧在用便宜的新编码模型替换贵的旧模型
- ③ 指引：底座模型层必须可插拔且可回退——建立模型清单版本化与灰度切换，对上游汰换预留缓冲期配置，避免「上游下架即断供」
- 补充：来自 GitHub 官方变更公告与社区讨论（11-16），具体模型清单以 Copilot 文档为准。
- 来源：https://github.com/orgs/community/discussions
- 来源：https://github.blog/changelog

5）Grok 核心工程师土豆姐（Lauren Tan）11-17 分享 AI Coding 实战：以代码库维护+规则约束+自动化测试与形式化验证为主线，团队月交付 1.1 万个 PR、回滚率约 0.5%

- ① 量化结果：其团队月交付 11000 个 PR，回滚率仅约 0.5%（量子位 11-17 报道，原文为实践分享访谈）
- ② 方法主线：不追求一次性生成好代码，而是持续维护代码库、用规则文件约束 agent 行为、自动化测试加形式化验证兜底质量
- ③ 指引：为底座建「规则即代码」层——把团队规范写成 RULES/CLAUDE.md 类约束文件并纳入评审；在 CI 为 agent 生成的代码加属性测试/形式化验证关卡，用回滚率而非产量考核
- 补充：实践分享类条目（作者个人经验+团队数据，非同行评审研究）；报道由量子位发布于腾讯新闻（11-17），数据为转述，采用前建议对照其原始分享。
- 来源：https://news.qq.com/rain/a/20261117V0B3AO00

6）GitHub spec-kit 本周三连发（v1.4.1–v1.4.3，11-16/17/19）：SDD 生态从单仓模板走向扩展目录与多仓编排

- ① 版本动态：三天三个版本，社区目录新增 Jira 生命周期扩展、Multi-Repo Workspace Orchestration（多仓工作区编排）扩展、OKR Bet Spec 预设与 Elephant-Goldfish 模型扩展
- ② 信号：扩展机制增强（扩展技能可携带声明资源）、对 PowerShell 与非 ASCII 分支等工程细节持续修复，SDD 工具链在向企业既有研发流程（Jira 等）和多仓场景渗透
- ③ 指引：底座可借鉴「spec 为源」的流程位——需求先落 spec 再驱动 agent 实现；并预留与外部工具链（需求管理）的生命周期集成点和多仓工作区编排能力
- 补充：版本与变更来自 GitHub Releases 原文（11-16/17/19），均为官方发布；扩展目录条目以仓库 community catalog 为准。
- 来源：https://github.com/github/spec-kit/releases

## 五、口径与来源

- **周 Token 使用量**：OpenRouter app-rankings 数据集，canonical app ID，窗口 2026-11-12 — 2026-11-18；只含OpenRouter可归因渠道，不代表全市场用量。Source: OpenRouter (openrouter.ai/apps), CC BY 4.0.
- **OpenRouter市场份额**：该应用周Token ÷ 榜单全部应用周Token合计，非四家内部占比（本轮已取得 200 个应用）。
- **周下载量**：npm downloads API 逐日加总的主包七天下载，含更新、CI 与重复下载，不等于活跃用户。
- **开源贡献者**：官方公开仓库的 GitHub contributors 数量（非匿名账号，与官网UI同口径）；仅统计公开官方仓库，闭源/内部镜像开发不计入。
- **插件数量**：来自各产品对应插件市场的公开计数，口径互不相同。
