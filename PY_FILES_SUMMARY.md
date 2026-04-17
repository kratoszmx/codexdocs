# PY_FILES_SUMMARY.md

本文件只记录仓库内 Python 脚本的用途与用法。
项目规则见 `skills.txt`，项目状态与交接信息见 `HANDOFF.md`。

## `project_env.py`
**作用**
- 统一补充 sibling `../myutils` 到导入路径。
- 让本项目脚本可以直接复用 `myutils` 的通用函数。

**用法**
- 不直接单独运行。
- 由 `docs_scan.py`、`sync_common.py` 等脚本导入使用。

---

## `docs_scan.py`
**作用**
- 扫描一个或多个 Markdown 文件/目录。
- 提取标题层级与 Markdown 链接。
- 标记疑似空文档或疑似截断文档。
- 扫描过程中使用 `tqdm` 展示进度条。
- 内部复用 `myutils/markdown_utils.py`。

**用法**
- `python3 docs_scan.py <文件或目录>`
- `python3 docs_scan.py <文件或目录> --show-links`

---

## `sync_section.py`
**作用**
- 按单个来源前缀同步文档。
- 按 `docs/` 的本地镜像结构，将来源链接写入 `urls/` 下对应位置的 `.txt` 文件。
- 下载到 `docs/`，并对疑似空/截断文档自动重试。
- 通过底层共享同步逻辑显示 `tqdm` 进度条。

**用法**
- `python3 sync_section.py <prefix>`
- `python3 sync_section.py <prefix> --timeout 45`
- `python3 sync_section.py <prefix> --workers 6`
- 示例：
  - `python3 sync_section.py developers/codex/cli`
  - `python3 sync_section.py github/docs`

---

## `sync_selected_sections.py`
**作用**
- 按预设来源组批量同步文档。
- 将选中文档的聚合链接写入 `urls/selected_sections.txt`。
- 同时按 `docs/` 的本地镜像结构，将每篇文档来源链接写入 `urls/` 下对应位置的 `.txt` 文件。
- 下载到 `docs/`，并对疑似异常文档自动重试。
- 通过底层共享同步逻辑显示 `tqdm` 进度条。

**当前预设来源组**
- `developers/codex`
- `github/docs`

**用法**
- `python3 sync_selected_sections.py`
- `python3 sync_selected_sections.py --timeout 45`
- `python3 sync_selected_sections.py --workers 6`

---

## `sync_all_docs.py`
**作用**
- 基于双来源发现做全量同步、完整性检查与修复。
- 检查缺失文档。
- 检查空文档或疑似截断文档。
- 生成全站聚合来源列表 `urls/all.txt`。
- 重建与 `docs/` 镜像结构一致的 `urls/` 目录树，每篇文档对应一个来源 `.txt` 文件。
- 清理不再属于当前 Codex 文档集合的 stale `docs/` / `urls/` 文件。
- 在检查和下载阶段通过共享逻辑显示 `tqdm` 进度条。
- 下载阶段支持有限并发 worker，并通过 `myutils/http_utils.py` 在可用时复用 HTTP 连接。
- `--benchmark` 可打印索引抓取、元数据重建、下载、post-check 与总耗时，以及下载吞吐。

**来源发现**
- OpenAI Developers Codex 文档：`https://developers.openai.com/codex/llms.txt`
- `openai/codex` 仓库 Markdown 文档：GitHub tree API + raw URLs

**用法**
- `python3 sync_all_docs.py --check-only`：仅检查本地镜像是否缺失/疑似截断
- `python3 sync_all_docs.py`：修复缺失或异常文档
- `python3 sync_all_docs.py --update-all`：强制重下当前索引中的全部文档，用于内容刷新
- `python3 sync_all_docs.py --timeout 45`
- `python3 sync_all_docs.py --workers 6`
- `python3 sync_all_docs.py --update-all --benchmark`

---

## `sync_common.py`
**作用**
- 同步脚本的共享模块。
- 统一处理 Developers `llms.txt` 读取、GitHub tree API 读取、URL 提取、文档下载、空文档/截断检测、URL 列表写入、镜像化 `urls/` 来源记录写入等公共逻辑。
- 统一处理 URL 到本地镜像路径的映射规则：Developers 文档落到 `docs/developers/...`，GitHub 仓库文档落到 `docs/github/...`。
- 对 GitHub 仓库中那类短跳转 stub 文档做特殊判定，避免误报为坏文档。
- 在批量检查和下载时统一提供 `tqdm` 进度条。
- 内部复用 `myutils/http_utils.py` 与 `myutils/markdown_utils.py`。

**用法**
- 不直接单独运行。
- 由 `sync_all_docs.py`、`sync_section.py`、`sync_selected_sections.py` 导入使用。
