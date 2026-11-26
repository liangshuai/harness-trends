# AI Harness 市场观察周报

数据窗口：2026-11-18 — 2026-11-24

详细报告：https://harness.mise.fun

## 一、主流Harness汇总表

| Harness | 周 Token 使用量（万亿） | OpenRouter市场份额 | 周下载量 | 开源贡献者 | 插件数量 | 本周新功能 | 洞察和行动 |
|---|---|---|---|---|---|---|---|
| Claude Code | 11.54T（**↑4.4%**） | 16.1% | 1,855.7万（**↓1.8%**） | 56 | 545 | 1）Code Mode 登陆云端终端会话：Amazon Bedrock、Google Agent Platform、Microsoft Foundry 与 Claude Platform on AWS（2.1.331）<br>2）支持 Anthropic 企业管理控制台管理的组织登录（2.1.330）<br>3）内置 easel 绘图 mod：按需绘制图表，Pro 及以上可用（2.1.330）<br>4）Opus 4.6 / Sonnet 4.6 在 Bedrock、Vertex 等渠道开放 auto mode（2.1.328） | 洞察：<br>1）Code Mode 一周内铺到四大云渠道：代码化工具调用成为跨云标配执行形态<br>2）企业控制台组织登录：企业身份体系直连是商业化前置动作<br>行动：<br>可借鉴 Code Mode 的跨云落地节奏与组织级登录，为底座准备多云渠道与企业身份（OIDC/SSO）接入层（计划 2026-12-08 前） |
| Pi | 6.38T（**↑47.6%**） | 8.9% | 792.5万（**↑14.8%**） | 310 | 5,728 | 1）GPT-6.2 Astra 与 Sol 上线 openai、azure、openai-codex 三个 provider（1.6.0，11-20）<br>2）GPT-6.2 Sol 设为默认模型（1.6.0） | 洞察：<br>1）新模型发布三天内三 provider 全跟进并设默认：小团队借多 provider 架构吃到模型红利<br>2）azure 与 openai-codex 双通道：企业合规渠道与个人渠道同版本节奏<br>行动：<br>可借鉴 pi 的多 provider 同步策略，底座模型接入层按 provider 抽象并保持新模型发布后数日内可用（计划 2026-12-01 前） |
| Codex | 3.39T（**↑1.9%**） | 4.7% | 2,844.6万（**↑6.8%**） | 479 | 1,310 | 1）GPT-6.2 Sol 成为默认模型（0.171.0，11-20）<br>2）TUI 工作区默认开启：文档/图片预览与子 agent 转录（0.171.0）<br>3）codex exec --remote 与 /rc、/remote：接入既有 app server 的远程会话与设备配对（0.171.0）<br>4）0.172.0（11-24）：会话线程跳转、斜杠命令 Tab 补全、MCP 按需启动、按工具设置审批人 | 洞察：<br>1）默认模型与默认工作区一周齐换：CLI 产品把「新模型即默认」当作分发渠道<br>2）MCP 缓存工具列表按首次调用启动：冷启动成本优化的共性做法<br>行动：<br>可借鉴 Codex 的模型默认化策略与远程会话/设备配对面板，为底座建模型灰度分发与远程托管会话能力（计划 2026-12-15 前） |
| DeepSeek Harness | 2.56T（**↑8.6%**） | 3.6% | 67.8万（**↑3.0%**） | 53 | 13,281 | 1）插件市场支持把 Git 仓库作为插件源，私有仓库插件可直接浏览安装（0.2.3-alpha.1，11-22）<br>2）实验性时间线插件：查看 agent 任务树、阻塞事项与进展报告（0.2.3-alpha.1）<br>3）代码审阅页面：集中处理本人相关 GitHub PR，页内与 agent 协作审阅并支持 GitLab（0.2.3-alpha.1）<br>4）会话状态区域：集中展示工作目录、变更请求、子 agent、任务与插件状态（0.2.3-alpha.1） | 洞察：<br>1）Git 仓库即插件源：安装面从市场扩到任意私有 Git，企业内分发插件的低门槛建法<br>2）时间线+代码审阅+会话状态三件套：agent 工作过程可视化成体系<br>行动：<br>可借鉴「Git 仓库即插件源」与页内协作审阅，底座插件分发支持私有 Git 源、把评审工作流嵌入主界面（计划 2026-12-12 前） |

**官方披露**

- **Codex**：2026-10-07 披露活跃用户 4,000万+（Codex 与 ChatGPT Work 合计口径）
- **DeepSeek Harness**：2026-11-04 披露日活 154万、月活 548万、单日Token 92.10万亿、公开第三方插件 3.49万

## 二、Token使用情况（行业）

- 四家周Token总量 23.87T（环比+13.3%）；周请求总量 2.51亿；份额第一 Claude Code 48.3%；Token环比变化最大 Pi +47.6%

### 模型使用量及占比

| Harness | 周 Token 使用量 | 样本内 Token 占比 | Token 使用量周环比 | 占比周变化（百分点） | 周模型请求量 |
|---|---|---|---|---|---|
| Claude Code | 11.54T | 48.3% | +4.4% | -4.1 | 1.22亿 |
| Pi | 6.38T | 26.7% | +47.6% | +6.2 | 7,188.2万 |
| Codex | 3.39T | 14.2% | +1.9% | -1.6 | 4,104.2万 |
| DSH | 2.56T | 10.7% | +8.6% | -0.5 | 1,665.0万 |

### 近四周 Token 使用量趋势（连续七天窗口，Token）

| Harness | 11-03 | 11-10 | 11-17 | 11-24 |
|---|---|---|---|---|
| Claude Code | 10.17T | 10.37T | 11.06T | 11.54T |
| Pi | 3.79T | 4.23T | 4.32T | 6.38T |
| Codex | 5.38T | 3.00T | 3.33T | 3.39T |
| DSH | 2.06T | 2.26T | 2.36T | 2.56T |

## 三、OpenRouter Top 10 动向

- **新进入 Top 10**：Portkey AI（第5名 · 周 Token 3.56T）——服务：AI 网关/控制平面：路由、缓存、守护与可观测，面向企业 LLM 流量
  - 集成视角：托管API网关，可作推理接入层而非执行引擎
- **本周增长最多**：pi（第4名 · 周 Token 6.38T，环比↑47.6%）——SDK：开源编码 agent，官方 TypeScript SDK 可编程嵌入，npm 分发、扩展生态完善
- **退出 Top 10**：Minds by Authentic Intelligence（上期第10名）

## 四、AI Coding 行业资讯

1）OpenAI 11-17发布GPT-6.2 Astra/Sol（Sol与6.1同价，超窗1天供参考）；本周Codex与pi相继把Sol设为默认，「新模型即默认」成分发惯例（来源：https://openai.com/index/introducing-gpt-6-2-astra-sol ）

2）智谱11-23发布GLM-5.4：首个loop transformer路线的通用编码模型（HN 1179分）；推理期循环展开的新架构，建议纳入底座模型评测集跟踪（来源：https://z.ai/blog/glm-5.4 ）

3）GPT-6.2 Astra成为首个打破Google工程师code golf纪录的模型（11-22，HN 358分）；极端代码压缩任务的能力信号，可作自测基准参考（来源：https://bjin.github.io/go-codegolf-benchmark/#leaderboard ）

4）IEEE Spectrum 11-20报道Epic Games在Unreal Engine开发中引入AI coding；引擎级大厂采纳是agent进入核心产线的信号（来源：https://spectrum.ieee.org/epic-games-unreal-engine-ai ）

5）路透11-24：微软在历史性宕机后内部宣布Code Red；可靠性成AI平台竞争新主战场，底座应把可观测性与降级演练当一等能力（来源：https://www.reuters.com/business/microsoft-declares-code-red-after-historic-outage-internal-memos-show-2026-11-24/ ）

6）Signal 11-20发文限制移动OS上AI agent对其数据的抓取（HN 584分）；数据源方开始主动设墙，agent数据获取合规需前置设计（来源：https://signal.org/blog/protecting-your-privacy/ ）

7）11-20热文《停止写代码，评审也会变差》（HN 405分）：与Harvard瓶颈研究互证，评审能力随手写减少而退化；建议保留深度编码练习与评审轮换（来源：https://cekrem.github.io/posts/if-you-stop-writing-code-you-also-get-worse-at-reviewing-it/ ）

8）11-23 Show HN：以可证伪假设驱动的代码优化agent skill；把科学方法写进agent工作流，质量层新实践，可直接借鉴其假设-验证循环（来源：https://chszlab.github.io/AgenticAlgorithmEngineering/ ）

9）11-24热文《LLM agents为母公司而非为你工作》（HN 1013分）：模型方与用户利益不完全一致；企业应自建策略层与审计，减少对厂商默认行为依赖（来源：https://michaelharley.net/posts/2026/11/01/llm-agents-work-for-their-parent-companies-not-for-you/ ）

10）11-20开源OpenComputer定位Devin替代（HN 131分）；开源自动化agent持续分流商业产品，可评估其作为底座执行引擎的可行性（来源：https://github.com/diggerhq/opencomputer ）

## 五、口径与来源

- **周 Token 使用量**：OpenRouter app-rankings 数据集，canonical app ID，窗口 2026-11-18 — 2026-11-24；只含OpenRouter可归因渠道，不代表全市场用量。Source: OpenRouter (openrouter.ai/apps), CC BY 4.0.
- **OpenRouter市场份额**：该应用周Token ÷ 榜单全部应用周Token合计，非四家内部占比（本轮已取得 200 个应用）。
- **周下载量**：npm downloads API 逐日加总的主包七天下载，含更新、CI 与重复下载，不等于活跃用户。
- **开源贡献者**：官方公开仓库的 GitHub contributors 数量（非匿名账号，与官网UI同口径）；仅统计公开官方仓库，闭源/内部镜像开发不计入。
- **插件数量**：来自各产品对应插件市场的公开计数，口径互不相同。
