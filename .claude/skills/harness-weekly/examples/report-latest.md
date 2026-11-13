# AI Harness 市场观察周报

数据窗口：2026-11-05 — 2026-11-11
详细报告：https://harness.mise.fun

## 一、主流Harness汇总表

| Harness | 周 Token 使用量（万亿） | OpenRouter市场份额 | 周下载量 | 开源贡献者 | 插件数量 | 本周新功能 | 洞察和行动 |
|---|---|---|---|---|---|---|---|
| Claude Code | 10.56T（**↑1.1%**） | 16.5% | 1,625.4万（**↑22.1%**） | 56 | 531 | 1）Fable 5.2 成为默认 Fable 模型：1M 上下文，$8/$40 每百万Token（2.1.321）<br>2）Vertex 上线 fast mode（global/us/eu），拒绝时自动回退标准速度（2.1.322）<br>3）claude remote-control 新增 --settings，为每个会话套用统一设置文件<br>4）MCP 任务后台化与 denyInsteadOfPrompting 无人值守权限策略（2.1.319） | 洞察：<br>1）fast mode 按区域自动回退：模型加速与渠道解耦的多云降级范式<br>2）remote-control --settings：远程批量会话统一配置，企业集中管理共性需求<br>行动：<br>受 remote-control --settings 与 denyInsteadOfPrompting 启发：底座可借鉴做集中配置下发与可审计的无人值守权限管理 |
| Pi | 4.04T（**↑2.3%**） | 6.3% | 678.8万（**↑7.9%**） | 308 | 5,451 | 1）pi auth login/logout：免启动会话即可登录登出，支持 API key（1.5.1）<br>2）空闲提示词缓存保温至30分钟，跨运行降低重复任务成本（1.5.1）<br>3）Anthropic 消息线程：只发送新增消息续接对话（1.5.1）<br>4）原目录被移动/删除的会话可 fork 到新位置（1.5.2） | 洞察：<br>1）空闲缓存保温30分钟：小改动直接降低重复任务成本，值得借鉴<br>2）消息线程只发增量：长会话带宽与延迟优化的共性思路<br>行动：<br>受缓存保温与增量消息线程启发：底座可借鉴内置提示词缓存保温与只发增量的消息续接，降低重复任务成本 |
| Codex | 3.34T（**↓33.3%**） | 5.2% | 2,623.4万（**↓1.1%**） | 477 | 1,269 | 1）Agent Command Center（codex agents --no-daemon）集中管理多个 agent，未读结果标记（0.167.0）<br>2）会话级后端切换保留草稿；本地图片预览与 Vertex AI 配置向导（0.167.0）<br>3）0.167.2：Vertex AI 默认增量发送工具声明，请求更轻量，可配置回退 | 洞察：<br>1）增量工具声明：随工具数增长只发 diff，是请求瘦身的通用解法<br>2）Command Center 与草稿保留持续打磨多 agent 并行的体验细节<br>行动：<br>受增量工具声明与 Command Center 启发：底座可借鉴按会话缓存工具定义只发 diff，并做多agent集中调度与结果回收 |
| DeepSeek Harness | 2.27T（**↑9.4%**） | 3.5% | 83.7万（**↑5.0%**） | 52 | 10,581 | 1）Git Worktree：按分支/提交/文件类型审阅改动，直连 GitHub 评审并同步进度<br>2）SubAgent 具名与多层协作；AgentTeam 按会话开启，共用成员与任务面板<br>3）桌面端支持切换正式版与开发版更新渠道 | 洞察：<br>1）AgentTeam 按会话共享成员与任务面板：多agent协作编排的直观实现<br>2）Worktree 评审直连 GitHub 并同步状态：把审查工作流嵌入 harness<br>行动：<br>受 AgentTeam 与 Worktree 评审启发：底座可借鉴按会话共享成员与任务面板的多agent编排，并把评审工作流嵌入 |

**官方披露**

- **Codex**：2026-10-07 披露活跃用户 4,000万+（Codex 与 ChatGPT Work 合计口径）
- **DeepSeek Harness**：2026-11-04 披露日活 154万、月活 548万、单日Token 92.10万亿、公开第三方插件 3.49万

**行动：本周最值得深入研究或借鉴**

1. 「请求瘦身」两例值得深研：Claude Code 按区域自动回退的 Vertex fast mode、Codex 增量工具声明
2. DSH AgentTeam 多agent协作面板与 Pi 空闲缓存保温，可直接借鉴

## 二、Token使用情况

- 四家周Token总量 20.21T（环比-5.9%）；周请求总量 2.21亿；份额第一 Claude Code 52.2%；Token环比变化最大 DSH +9.4%

### 模型使用量及占比

| Harness | 周 Token 使用量 | 样本内 Token 占比 | Token 使用量周环比 | 占比周变化（百分点） | 周模型请求量 |
|---|---|---|---|---|---|
| Claude Code | 10.56T | 52.2% | +1.1% | +3.6 | 1.08亿 |
| Pi | 4.04T | 20.0% | +2.3% | +1.6 | 3,929.8万 |
| Codex | 3.34T | 16.5% | -33.3% | -6.8 | 5,955.1万 |
| DSH | 2.27T | 11.2% | +9.4% | +1.6 | 1,433.0万 |

### 近四周 Token 使用量趋势（连续七天窗口，Token）

| Harness | 10-21 | 10-28 | 11-04 | 11-11 |
|---|---|---|---|---|
| Claude Code | 11.59T | 11.02T | 10.45T | 10.56T |
| Codex | 1.43T | 2.78T | 5.01T | 3.34T |
| Pi | 3.37T | 5.97T | 3.95T | 4.04T |
| DSH | 2.40T | 2.23T | 2.07T | 2.27T |

## 三、OpenRouter Top 10 动向

- **新进入 Top 10**：Minds by Authentic Intelligence（第10名 · 周 Token 1.40T）——产品：App Store 上架的消费级 AI 应用，定位「人与人真实连接」的 AI 实验室，非开发者工具
  - 集成视角：消费级产品，不适合作为执行引擎整合
- **本周增长最多**：omp（第7名 · 周 Token 3.21T，环比↑44.7%）——CLI：Oh My Pi（omp.sh），Rust 内核终端编码 agent，LSP/DAP 为一等工具，兼容 pi 扩展生态
- **退出 Top 10**：Portkey AI（上期第7名）

## 四、口径与来源

- **周 Token 使用量**：OpenRouter app-rankings 数据集，canonical app ID，窗口 2026-11-05 — 2026-11-11；只含OpenRouter可归因渠道，不代表全市场用量。Source: OpenRouter (openrouter.ai/apps), CC BY 4.0.
- **OpenRouter市场份额**：该应用周Token ÷ 榜单全部应用周Token合计，非四家内部占比（本轮已取得 200 个应用）。
- **周下载量**：npm downloads API 逐日加总的主包七天下载，含更新、CI 与重复下载，不等于活跃用户。
- **开源贡献者**：官方公开仓库的 GitHub contributors 数量（非匿名账号，与官网UI同口径）；仅统计公开官方仓库，闭源/内部镜像开发不计入。
- **插件数量**：来自各产品对应插件市场的公开计数，口径互不相同。
