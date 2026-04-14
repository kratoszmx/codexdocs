# HANDOFF.md

本文件只保留 `openclaw_docs` 项目的交接信息。
项目规则看 `skills.txt`；Python 脚本用途和命令看 `PY_FILES_SUMMARY.md`。

## 项目定位
- 维护 `https://docs.openclaw.ai/` 的本地 Markdown 镜像。
- 将 `docs/` 作为官网文档的镜像目录持续维护；官网根级的分散 Markdown 文件，以及 `automation`、`debug`、`diagnostics`、`nodes`、`plugins`、`security`、`start`、`web` 这些顶级 section，在本地统一归档到 `docs/others/`。
- 要求结果可复查、可修复、可复跑。

## 当前状态
- 已确认进入项目后先读 `skills.txt` 的工作规则。
- 仓库已具备扫描、分区同步、批量同步、全站校验/修复脚本。
- 仓库现在通过 `project_env.py` 接入 sibling `../myutils`，复用通用 HTTP 与 Markdown 工具函数，减少本项目重复实现。
- `docs/` 已作为镜像目录使用，`docs/others/` 已用于归档官网根级的分散 Markdown 文件以及 `automation`、`debug`、`diagnostics`、`nodes`、`plugins`、`security`、`start`、`web` 这些顶级 section，`urls/` 用于按 `docs/` 镜像结构记录对应来源链接。
- 已完成一轮全站文档补齐与异常文档修复。
- 项目说明文档已整理为中文。

## 当前重点
- 持续保持文档镜像与官网一致。
- 发现缺失、空文档或疑似截断文档时，优先用现有脚本修复。
- 可复用的通用逻辑优先上收到 `../myutils`，避免在本项目再次实现。

## 接手建议
- 先读 `skills.txt`，再根据任务决定是否查看 `PY_FILES_SUMMARY.md`。
- 若只想诊断本地镜像是否缺失或疑似截断，可跑 `python3 sync_all_docs.py --check-only`；若要确保当前索引下的正文内容刷新，以 `python3 sync_all_docs.py --update-all` 为准。
- 本文件只记录项目状态、当前关注点和交接信息；不要在这里重复写通用规则或脚本用法。
