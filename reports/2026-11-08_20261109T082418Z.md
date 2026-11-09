# AI Agent Harness 市场观察周报 · Markdown 版

数据窗口：2026-11-02 — 2026-11-08（UTC）· 生成于 2026-11-09 16:24（北京时间）· 方法版本 0.1.0
HTML 完整版：`reports/latest.html`（含四周趋势图、规模估算、本周新功能特性与数据附录）；结构化快照：`data/latest.json`。

## 一、四家汇总表

| Harness | 周Token（OpenRouter） | 周npm下载 | 官方仓库Contributors | 插件数量 | 洞察（本周新功能） | 行动 |
|---|---|---|---|---|---|---|
| Claude Code | 10.05T（份额52.6%），环比-1.5% | 1,419.4万（环比+10.1%） | 56（anthropics/claude-code） | 529（Claude官方Marketplace） | 1）功能主线是「无人值守」：denyInsteadOfPrompting 将权限提示改为策略化拒绝并继续执行<br>2）MCP 任务自动后台化，长工具调用不再阻塞会话<br>3）auto mode 在网关/关遥测时改走服务端检查，权限模型从「人守着点允许」转向可审计的自动化<br>4）网关类功能密集落地（pooled预算规则、login_notice、JSON日志、成本报表），企业网关是当前迭代重心 | 评估denyInsteadOfPrompting对CI/子代理场景的适配成本；对照网关新能力（成本报表、pooled预算）评估企业侧管理开销是否下降。 |
| Codex | 2.62T（份额13.7%），环比-52.1% | 2,590.8万（环比-6.9%） | 478（openai/codex） | 1,265（ChatGPT插件目录（mcptop.com）） | 1）0.167.0 上线 Agent Command Center，集中管理多个 agent 并标记未读结果<br>2）会话级后端切换保留草稿，配合 Vertex AI 向导（gcp_setup_wizard）降低多云接入门槛<br>3）从单会话 CLI 转向调度面板，明显在做多后端/多云以降低锁定<br>4）高频 alpha + 周度 stable 的发布节奏不变 | 实测codex agents --no-daemon命令中心、后端切换保留草稿与未读结果标记；评估多后端切换对混合云/多供应商部署的实际价值。 |
| Pi | 4.20T（份额22.0%），环比-7.6% | 663.4万（环比+5.5%） | 306（earendil-works/pi） | 5,360（pi.dev官方Package Catalog） | 1）扩展更新 changelog 给作者一条触达用户的发布说明通道<br>2）流式渲染提速（大工具调用增量解析、高亮/Markdown渲染复用）优化大输出体验<br>3）自定义自更新命令适配各种包管理器，OSC 7501 向终端/面板暴露运行状态<br>4）整体在做可组合底座而非功能堆叠，生态基础设施优先于单点能力 | 研究扩展changelog与OSC 7501对外部集成面板的开放思路对自研harness插件体系的借鉴价值。 |
| DeepSeek Harness | 2.25T（份额11.8%），环比+19.3% | 82.7万（环比+8.1%） | 50（deepseek-ai/deepseek-harness） | 9,463（dshmarket.com） | 1）功能集中在补易用性短板：手机/平板适配、六种新语言、引用插入、历史导出Markdown、统一右键菜单<br>2）插件热更新失败自动回滚 + 富文本详情页，强化「一切皆插件」的运维体验<br>3）实验性 subagent_oar 直接调度本机 Codex/Claude CLI 当子代理，是跨harness整合的差异化信号<br>4）方向是向日常工具的可用性靠拢，而非堆模型能力 | 关注subagent_oar插件（把独立任务交给本机Codex/Claude CLI）的跨harness调度思路能否借鉴；评估插件热更新回滚机制对自家插件运维的参考价值。 |

> 洞察面向本周新增功能点，与行动均为编辑观点（`data/editorial/2026-11-08.json`，2026-11-09整理）；数字均由脚本按当轮快照采集，不手工填写。

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

### 公开插件与参与账号样本（GitHub）

| Harness | 已核验发布单元 | 样本参与账号 | 本轮覆盖 |
|---|---|---|---|
| Claude Code | 283 | 103 | 24 个候选 / 4 个贡献者仓库 |
| Codex | 13 | 14 | 24 个候选 / 7 个贡献者仓库 |
| Pi | 20 | 48 | 24 个候选 / 8 个贡献者仓库 |
| DSH | 7 | 201 | 24 个候选 / 7 个贡献者仓库 |

样本为受限公开观测，不是生态总量；一个仓库可能有多个插件，四家发现入口与覆盖不同。
### DSH 官方披露

截至 2026-11-04（媒体转述厂商披露，不同于OpenRouter渠道数据）：日活 154.0万；月活 548.0万；单日Token 92.10T；公开第三方插件 3.5万（已去重）。

## 三、口径与来源

- **周Token**：OpenRouter app-rankings 数据集，canonical app ID，窗口 2026-11-02 — 2026-11-08；只含OpenRouter可归因渠道，不代表全市场用量。Source: OpenRouter (openrouter.ai/apps), CC BY 4.0.
- **周npm下载**：npm downloads API 逐日加总的主包七天下载，含更新、CI 与重复下载，不等于活跃用户。
- **官方仓库Contributors**：GitHub REST contributors（非匿名账号，与官网UI同口径，Link头last页码精确计数）；仅统计公开官方仓库，闭源/内部镜像开发不计入，厂商间口径差异见各行仓库名。
- **插件数量**：Claude Code 取 claude.com/marketplace/plugins 页面公布总数；Codex 取 mcptop.com 所示 ChatGPT 插件目录 Plugins 分类计数（该目录另有全量口径，见数据快照 directory_total）；Pi 取 pi.dev 官方 Package Catalog 未筛选总数（含 extension/skill/theme/prompt 等类型，非纯 extension）；DSH 取 dshmarket.com 公布的社区插件总数。四者口径互不相同，不可直接横向排名。
- **本周新功能特性**：见 HTML 完整版 `reports/latest.html` 的「本周新功能特性」部分（脚本采集 Releases/CHANGELOG 原文 + 网络检索核实）。
- **洞察/行动**：面向本周新增功能点的编辑解读与建议，不属于采集数据；无编辑笔记的周次自动降级为脚本提取的发布要点摘要。
- 注：ChatGPT 插件目录全量 12,404 个，本表按用户指定取 Plugins 分类计数 1,265。（mcptop.com 观测于 2026-11-09）

原始响应与逐项采集状态见 `data/raw/`、`data/runs/` 与 HTML 版附录数据清单。
