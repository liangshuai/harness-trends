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

1）微软11-17 Ignite发布MAI Code 2/Flash：编码质量达GPT-6.1 Sol的98%、约40%价格，单任务$0.309；建议把「$/task」而非$/Mtok纳入底座模型选型指标（来源：https://microsoft.ai/news/introducing-mai-code-2-and-mai-code-2-flash）

2）Postman 11-18《2026 State of the API》：25%组织已在生产环境经API运行AI agents，API治理与就绪度成瓶颈；建议为agent流量单设配额与审计端点（来源：https://www.businesswire.com/news/home/20261118374573/en/One-in-Four-Organizations-Now-Run-AI-Agents-on-APIs-in-Production-Postmans-2026-State-of-the-API-Report-Finds）

3）字节TRAE CN个人版11-18起自动并入豆包飞书账号，代码/项目/权益全保留；统一账号与数据体系是AI编程工具留存基础，底座应支持组织级SSO与工作区可迁移（来源：https://docs.trae.cn/ide_important-notice-for-trae-account-upgrade-and-integration）

4）GitHub 11-16起Copilot下架多款旧模型（含Claude Opus 4.8退役），与MAI Code 2低价上市同周；底座模型层应可插拔可回退、清单版本化，防上游汰换即断供（来源：https://github.blog/changelog）

5）Grok核心工程师土豆姐11-17分享：团队月交付1.1万PR、回滚率约0.5%，靠代码库持续维护+规则约束+自动化测试与形式化验证；建议CI加属性测试关卡、按回滚率考核（来源：https://news.qq.com/rain/a/20261117V0B3AO00）

6）GitHub spec-kit本周三连发v1.4.1–1.4.3（11-16/17/19）：社区目录新增Jira生命周期与多仓工作区编排扩展；SDD正走向企业工具链集成，可借鉴「spec为源」的流程位（来源：https://github.com/github/spec-kit/releases）

## 五、口径与来源

- **周 Token 使用量**：OpenRouter app-rankings 数据集，canonical app ID，窗口 2026-11-12 — 2026-11-18；只含OpenRouter可归因渠道，不代表全市场用量。Source: OpenRouter (openrouter.ai/apps), CC BY 4.0.
- **OpenRouter市场份额**：该应用周Token ÷ 榜单全部应用周Token合计，非四家内部占比（本轮已取得 200 个应用）。
- **周下载量**：npm downloads API 逐日加总的主包七天下载，含更新、CI 与重复下载，不等于活跃用户。
- **开源贡献者**：官方公开仓库的 GitHub contributors 数量（非匿名账号，与官网UI同口径）；仅统计公开官方仓库，闭源/内部镜像开发不计入。
- **插件数量**：来自各产品对应插件市场的公开计数，口径互不相同。
