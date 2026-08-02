# 贡献指南

感谢你愿意贡献 GitHub Engineer。本文档说明如何提 issue、提 PR、搭建开发环境、跑测试、遵守代码风格和 commit 规范。

## 如何提 Issue

- **Bug**: 先在现有 issue 中搜索是否已有报告, 包含复现步骤、期望行为、实际行为、环境 (Python 版本、OS、相关配置)。
- **功能建议**: 写清楚问题场景和希望的能力, 说明 v0.1-v0.4 当前是否已覆盖, 引用 `README.md` 和 `DESIGN.md` 的相关章节。
- **安全问题**: 不要公开提 issue, 走 SECURITY 流程 (见 `README.md`)。

## 如何提 PR

1. Fork 仓库, 从 `main` 切出 feature 分支 (`feat/xxx` 或 `fix/xxx`)。
2. 开发完成后跑 `make test` (或 `.venv/bin/pytest tests/ -v`) 确认全部测试通过。
3. 一个 PR 只做一件事, 描述写清"改了什么 / 为什么 / 怎么验证"。
4. 关联对应 issue (如有), 在 review 通过前保持可 rebase。

## 开发环境

```bash
git clone <your-fork-url>
cd github-engineer
make venv
make install-dev
```

`make install-dev` 会同时装上 `pytest` 和 `pytest-cov`, 并把 `ghe` 命令注册到当前 venv。

## 测试

```bash
make test                          # 全部 382 个测试
.venv/bin/pytest tests/test_config.py -v  # 单文件
.venv/bin/pytest -k delegation -v         # 按名字筛选
make test-fast                     # CI 友好, 不带 -v
make smoke                         # e2e smoke (list-decisions + config parse)
```

新功能必须带测试。`src/` 下的业务代码改动请同步更新 `tests/`。

## 代码风格

- 遵循 [PEP 8](https://peps.python.org/pep-0008/), 4 空格缩进, 行长不超过 100 字符。
- 公开函数加 type hints, 内部函数也尽量带; `from __future__ import annotations` 已在 `src/main.py` 中使用, 其它模块可参照。
- 优先用 `pathlib.Path` 而不是 `os.path`; YAML 用 `PyYAML.safe_load`; 外部 IO 失败要抛具体异常, 不吞错。
- 提交前自检: `python -c "import src.main"` 可正常导入。

## Commit 规范

使用 [Conventional Commits](https://www.conventionalcommits.org/):

- `feat: <scope> <desc>` — 新功能
- `fix: <scope> <desc>` — 修 bug
- `docs: <desc>` — 仅文档
- `refactor: <scope> <desc>` — 不改行为的重构
- `test: <scope> <desc>` — 测试相关
- `chore: <desc>` — 构建/工具/杂项

`<scope>` 可省略或填模块名 (`config`, `analyzer`, `delegation` ...)。
中文或英文描述都可以, 保持简洁。
