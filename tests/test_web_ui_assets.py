"""Keep packaged desktop assets aligned with the server-rendered UI.

``src.web_ui`` is the source of truth because installed wheels serve these
constants directly.  The desktop copies exist for Tauri packaging and must be
regenerated from the same constants instead of being edited independently.
"""

import shutil
import subprocess
from pathlib import Path

from src.web_ui import APP_CSS, APP_JS, DIFF_VIEW_CLIENT_JS


ROOT = Path(__file__).resolve().parents[1]


def test_packaged_desktop_assets_match_web_ui() -> None:
    assert (ROOT / "desktop/ui/app.css").read_text(encoding="utf-8") == APP_CSS
    assert (ROOT / "desktop/ui/app.js").read_text(encoding="utf-8") == APP_JS
    assert (
        (ROOT / "desktop/ui/diff-view-client.js").read_text(encoding="utf-8")
        == DIFF_VIEW_CLIENT_JS
    )


def test_packaged_javascript_is_valid_and_has_race_guards() -> None:
    script = ROOT / "desktop/ui/app.js"
    node = shutil.which("node")
    assert node, "Node.js is required to validate the packaged desktop script"
    subprocess.run([node, "--check", str(script)], check=True, capture_output=True)

    source = script.read_text(encoding="utf-8")
    assert "_diffLoadGeneration" in source
    assert "_diffLoadController?.abort()" in source
    assert "String(currentRepairJob?.id || '') === jobId" in source
    assert "_decisionWriteTail" in source
    assert "_decisionVersions" in source
    assert "pendingDecisionWrites(jobId) === 0" in source
    assert "generation === publishGeneration" in source
    assert "if (!job) {\n      // Opening a new issue" in source
    assert "hideDiffView();\n      setRepairPhase('queued');" in source
    assert "event.metaKey || event.ctrlKey || event.altKey) return" not in source
    assert "!event.altKey || !event.shiftKey" in source
    assert "Date.now() + 20000" in source


def test_repair_ux_exposes_real_phases_verification_and_data_boundary() -> None:
    source = APP_JS
    shell_source = (ROOT / "src/web_ui.py").read_text(encoding="utf-8")

    assert "分析并准备修复" in source
    assert "读取代码 → 定位问题 → 修改代码 → 运行验证 → 等待审核" in source
    assert "const order = ['read', 'locate', 'modify', 'verify', 'review']" in source
    assert "验证通过" in source
    assert "验证失败" in source
    assert "未验证" in source
    assert "这不代表 Issue 已经修复" in source
    assert "历史任务的工作区已经不存在" in source
    assert "Issue 内容与为定位问题选取的仓库源码片段会发送" in source
    assert "Claude CLI 在本机工作区读取和修改代码" in source
    assert "AI 会先在隔离目录修改代码并运行测试" not in source

    for phase in ("read", "locate", "modify", "verify", "review"):
        assert f'data-repair-phase="{phase}"' in shell_source


def test_demo_and_unverified_repairs_fail_closed_before_publish() -> None:
    source = APP_JS

    assert "演示模式 · fake" in source
    assert "fake Provider 只演示工作流" in source
    assert "const providerAllowsPublishing" in source
    assert "Boolean(provider) && !isDemoRepair(job)" in source
    assert "&& providerSafe" in source
    assert "&& verification.status === 'passed'" in source
    assert "演示模式禁止创建 Draft PR" in source
    assert "需要明确的测试或验证通过结果后才能发布" in source

    click_guard = source.index("if (!providerAllowsPublishing(currentRepairJob))")
    confirmation_request = source.index("/confirm-token", click_guard)
    publish_request = source.index("/publish", confirmation_request)
    assert click_guard < confirmation_request < publish_request
