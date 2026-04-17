# HANDOFF.md

本文件只保留 `codex_docs` 项目的交接信息。
项目规则看 `skills.txt`；Python 脚本用途和命令看 `PY_FILES_SUMMARY.md`。

## 项目定位
- 维护 Codex CLI 相关官方在线文档的本地 Markdown 镜像。
- 当前镜像来源分两类：
  - OpenAI Developers 的 Codex 文档，基于 `https://developers.openai.com/codex/llms.txt` 发现页面，并过滤到 CLI / 本地客户端相关页面；
  - `openai/codex` 仓库中的官方 Markdown 文档，基于 GitHub tree API 发现并过滤到面向 CLI 使用者的 README / docs 页面，再从 raw URL 下载。
- `docs/` 作为镜像目录持续维护，按来源拆分为 `docs/developers/...` 与 `docs/github/...`；`urls/` 按同样结构记录每篇文档的来源 URL。
- 要求结果可复查、可修复、可复跑。

## 当前状态
- 已确认进入项目后先读 `skills.txt` 的工作规则。
- 仓库已具备扫描、单前缀同步、预设来源组同步、批量同步、全量校验/修复脚本。
- 仓库通过 `project_env.py` 接入 sibling `../myutils`，复用通用 HTTP 与 Markdown 工具函数，减少本项目重复实现。
- `sync_common.py` 已从 OpenClaw 固定站点模型改为 Codex 双来源模型：Developers + GitHub repo。
- `sync_all_docs.py` 现在会在重建 `urls/` 记录时同步清理 stale `docs/` 镜像文件，避免旧 OpenClaw 文档残留。
- 已完成一轮真实同步，当前发现并镜像了 52 份文档：38 份 Developers 文档，14 份 GitHub 仓库 Markdown 文档。
- 已修正对 GitHub 短跳转 stub 文档的误判问题；当前 `python3 sync_all_docs.py --check-only` 结果为 `missing=0`, `bad=0`。
- 测试当前通过：`pytest -q`。

## 当前重点
- 持续保持 Codex 文档镜像与官方来源一致。
- 发现缺失、空文档或疑似截断文档时，优先用现有脚本修复。
- 若后续发现新的官方 Codex 文档入口，需要优先补进发现逻辑，而不是手工散加 URL。
- 可复用的通用逻辑优先上收到 `../myutils`，避免在本项目再次实现。

## 接手建议
- 先读 `skills.txt`，再根据任务决定是否查看 `PY_FILES_SUMMARY.md`。
- 若只想诊断本地镜像是否缺失或疑似截断，可跑 `python3 sync_all_docs.py --check-only`。
- 若要确保当前索引下的正文内容刷新，以 `python3 sync_all_docs.py --update-all` 为准。
- 若只想抓某一个来源前缀，可用 `python3 sync_section.py developers/codex/cli` 或 `python3 sync_section.py github/docs`。
- 本文件只记录项目状态、当前关注点和交接信息；不要在这里重复写通用规则或脚本用法。
