# Harness 方法研究证据汇总

# 01-披露与口径

关联原始证据：06-dsh-disclosure.md 13-ifeng-original.md dsh-disclosure-dashboard.jpg dsh-tokens.jpg dsh-plugins.jpg

媒体转述厂商披露。正文和图片均已核读：154万DAU、548万MAU、92.1T单日Token、3.49万去重公开插件；GitHub 2.94万、npm 1.85万。没有独立作者总数。趋势前五点为七天日均，末点为单日。58.94%为创建或使用，不能推作者。

核验日：2026-11-06。可信度：官方文档/API较高；厂商运营披露为媒体转述，未独立审计；推导和建议不冒充实测。


# 02-OpenRouter

关联原始证据：01-openrouter-data-doc.md 02-openrouter-apps.md 03-openrouter-api-probe.md 21-openrouter-attribution.md

官方文档与页面。四家条目可见；归因和可见性选择影响样本。文档支持日期窗口、Token与请求字段；无凭据探测401，带凭据的历史完整性未验证。只能做渠道内份额。

核验日：2026-11-06。可信度：官方文档/API较高；厂商运营披露为媒体转述，未独立审计；推导和建议不冒充实测。


# 03-GitHub

关联原始证据：11-github-dsh-topic.md 14-dsh-readme.md 15-github-contributors-doc.md 19-github-search-doc.md

官方仓库及平台文档。topic发现可行但包含核心仓库，命中数27763不是插件数。每次搜索最多1000条；contributors有缓存与邮箱关联限制。主仓README默认分支master，先前main请求404已经找到正确入口。

核验日：2026-11-06。可信度：官方文档/API较高；厂商运营披露为媒体转述，未独立审计；推导和建议不冒充实测。


# 04-npm

关联原始证据：07-npm-codex.md 08-npm-claude.md 09-npm-dsh.md 10-npm-pi.md 16-npm-doc.md 22-pi-old-npm.md

官方npm下载端点与接口文档。2026-10-30至11-05七个UTC日：Codex 26010557；Claude Code 13612394；DSH 826814；Pi新包6067871、旧包350572。是包下载次数，不是人数，且未登记所有迁移别名。

核验日：2026-11-06。可信度：官方文档/API较高；厂商运营披露为媒体转述，未独立审计；推导和建议不冒充实测。


# 05-生态入口

关联原始证据：05-pi-packages.md 12-pi-manifest.md 17-claude-setup.md 18-codex-plugin-doc.md 20-dsh-site.md

官方产品文档。Pi以pi-package和pi资源配置发现，支持npm/git/local；Codex与Claude插件需按manifest/目录识别；DSH有桌面与npm入口。统一发布单元，资源类型单列，作者账号与使用者分开。

核验日：2026-11-06。可信度：官方文档/API较高；厂商运营披露为媒体转述，未独立审计；推导和建议不冒充实测。


不适用的资料阶段：本任务为数据采集方法研究，已取得直接相关API及插件文档，无须下载不相关PDF补充产品/商业框架。详细决策与限制见上级目录 Harness-竞品分析报告.md。
