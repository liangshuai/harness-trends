# AI Agent Harness 市场观察周报

数据窗口：2026-11-02 — 2026-11-08（UTC）· 生成于 2026-11-09 19:36（北京时间）

## 一、四家汇总表

| Harness | 周Token（OpenRouter） | 周下载量 | 开源贡献者 | 插件数量 | 活跃用户 | 本周新功能 | 行动 |
|---|---|---|---|---|---|---|---|
| Claude Code | 10.05T（份额52.6%），环比-1.5% | 1,419.4万（环比+10.1%） | 56（anthropics/claude-code） | 529 | — | 1）denyInsteadOfPrompting：无人值守时权限提示改为策略化拒绝并继续执行<br>2）MCP 任务自动后台化，长工具调用不再阻塞会话<br>3）auto mode 网关侧安全检查收紧，权限决策可审计<br>4）/usage 新增消费展示；网关新增成本报表与 pooled 预算规则 | 评估denyInsteadOfPrompting对CI/子代理场景的适配成本；对照网关新能力（成本报表、pooled预算）评估企业侧管理开销是否下降。 |
| Codex | 2.62T（份额13.7%），环比-52.1% | 2,590.8万（环比-6.9%） | 478（openai/codex） | 1,265 | 4,000万+（Codex（含 ChatGPT Work），2026-10-07）<br>单品历史：超过500万WAU（2026-06-02） | 1）Agent Command Center（codex agents --no-daemon）集中管理多个 agent，未读结果标记<br>2）会话级后端切换保留草稿<br>3）本地图片预览；Vertex AI 配置向导 gcp_setup_wizard<br>4）macOS/Windows 系统代理设置可在 /experimental 开启 | 实测codex agents --no-daemon命令中心、后端切换保留草稿与未读结果标记；评估多后端切换对混合云/多供应商部署的实际价值。 |
| Pi | 4.20T（份额22.0%），环比-7.6% | 663.4万（环比+5.5%） | 306（earendil-works/pi） | 5,360 | — | 1）扩展更新 changelog：作者可向用户推送更新说明，可折叠展示<br>2）流式渲染提速：大工具调用增量解析、高亮与渲染复用<br>3）OSC 7501 程序状态上报（工作/阻塞/完成）<br>4）自定义自更新命令；GPT-6.1 Terra 接入 | 研究扩展changelog与OSC 7501对外部集成面板的开放思路对自研harness插件体系的借鉴价值。 |
| DeepSeek Harness | 2.25T（份额11.8%），环比+19.3% | 82.7万（环比+8.1%） | 50（deepseek-ai/deepseek-harness） | 9,463 | 548万MAU / 154万DAU（官方披露，2026-11-04） | 1）手机/平板适配：软键盘交互、导航与窄屏布局优化<br>2）插件热更新失败自动回滚；管理页富文本详情<br>3）完整历史会话可复制为 Markdown<br>4）实验性 subagent_oar：把独立任务交给本机 Codex/Claude CLI 执行 | 关注subagent_oar插件（把独立任务交给本机Codex/Claude CLI）的跨harness调度思路能否借鉴；评估插件热更新回滚机制对自家插件运维的参考价值。 |

> 本周新功能为编辑整理的当周重点功能摘要（源自官方发布并经网络检索核实）；行动为编辑建议；数字均由脚本按当轮快照采集，不手工填写。

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
- **本周新功能/行动**：本周新功能列为编辑从当周官方 Releases/CHANGELOG 中总结挑选的重点摘要（经网络检索核实）；无编辑笔记的周次自动降级为脚本提取的原文摘录；行动为编辑建议。
- 注：ChatGPT 插件目录全量 12,404 个，本表取 Plugins 分类计数 1,265（mcptop.com，2026-11-09观测）。
