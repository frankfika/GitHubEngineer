"""Keep packaged desktop assets aligned with the server-rendered UI.

``src.web_ui`` is the source of truth because installed wheels serve these
constants directly.  The desktop copies exist for Tauri packaging and must be
regenerated from the same constants instead of being edited independently.
"""

import shutil
import subprocess
from pathlib import Path

from src.web_ui import APP_CSS, APP_JS, DIFF_VIEW_CLIENT_JS, render_shell


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
    assert "await confirmFullDiffForSubmission(jobId)" in source
    assert "generation === publishGeneration" in source
    assert "if (!job) {\n      // Opening a new issue" in source
    assert "hideDiffView();\n      setRepairPhase('queued');" in source
    assert "event.metaKey || event.ctrlKey || event.altKey) return" not in source
    assert "!event.altKey || !event.shiftKey" in source
    assert "Date.now() + 20000" in source


def test_packaged_bootstrap_promises_an_embedded_backend() -> None:
    bootstrap = (ROOT / "desktop" / "index.html").read_text(encoding="utf-8")

    assert "前端与本地服务已包含在应用中" in bootstrap
    assert "ghe --serve" not in bootstrap
    assert '<a class="skip-link" href="#main-workspace">跳到主要内容</a>' in bootstrap


def test_configured_repository_is_selected_and_loaded_on_startup() -> None:
    source = APP_JS

    assert "window.localStorage.getItem('ghe:selected-repository')" in source
    assert "repositoryNames.has(result.selected)" in source
    assert "repositories[0].full_name" in source
    assert "repoSwitcher.value = selectedRepository" in source
    assert "await loadIssues(selectedRepository)" in source
    assert "永远不预选" not in source


def test_secondary_pages_refresh_shared_repository_state_and_keep_links_working() -> None:
    source = APP_JS

    load_repositories = source[source.index("const loadRepositories = async () => {") :]
    load_repositories = load_repositories[: load_repositories.index("\n  const renderOwnedRepositoryChoices")]
    first_fetch = load_repositories.index("fetchJson('/api/repositories')")
    secondary_return = load_repositories.index("if (!repoSwitcher) return")
    assert first_fetch < load_repositories.index("updateModeIndicator") < secondary_return
    assert "if (repoViewer) {" in load_repositories
    assert "if (repoSwitcher) {" in load_repositories
    assert "if (issueSummary) issueSummary.innerHTML" in load_repositories
    assert "if (issueInbox) {" in load_repositories
    assert "diffConnectGithub.hidden = Boolean(authenticated)" in source

    repository_click = source[source.index("const pill = event.target.closest('[data-select-repo]')") :]
    repository_click = repository_click[: repository_click.index("\n  if (refreshIssues)")]
    assert "if (!issueInbox || !issueSummary) return" in repository_click
    assert repository_click.index("if (!issueInbox || !issueSummary) return") < repository_click.index(
        "event.preventDefault()"
    )


def test_unverified_repair_offers_explicit_host_verification_consent() -> None:
    source = APP_JS

    assert "data-allow-host-verification" in source
    assert "我理解风险，在本机运行测试" in source
    assert "canRequestHostVerification" in source
    assert "return { status, detail, reason }" in source
    assert "window.confirm('本机验证会执行这个仓库里的测试代码" in source
    assert "JSON.stringify({ allow_host_verification: true })" in source


def test_failed_verification_remains_visible_and_can_be_retried_from_diff() -> None:
    source = APP_JS
    shell_source = (ROOT / "src/web_ui.py").read_text(encoding="utf-8")

    assert "const renderDiffVerification = (job) =>" in source
    assert "No module named" in source
    assert "测试环境缺少依赖" in source
    assert "data-retry-verification" in source
    assert "查看失败摘要" in source
    assert "将再次在本机执行这个仓库的测试代码" in source
    assert "dependency_missing" in source
    assert "重新检测并验证" in source
    assert "if (diffViewOverview) diffViewOverview.scrollTop = 0" in source
    assert 'id="diff-view-verification" aria-live="polite"' in shell_source


def test_first_launch_onboarding_reflects_real_connection_state() -> None:
    source = APP_JS

    assert "const codingAgentReady = Boolean(currentCodingAgent?.configured && currentCodingAgent?.healthy)" in source
    assert "currentGithubAuthenticated = Boolean(result.viewer)" in source
    assert "currentGithubAccount = String(result.viewer || '')" in source
    assert "准备完成，只差添加仓库" in source
    assert "Coding Agent 已就绪" in source
    assert "GitHub 已连接" in source
    assert "if (root?.classList.contains('no-repositories')) showOnboardingIfFirstTime()" in source


def test_shell_has_keyboard_skip_link() -> None:
    shell_source = (ROOT / "src/web_ui.py").read_text(encoding="utf-8")

    assert '<a class="skip-link" href="#main-workspace">跳到主要内容</a>' in shell_source
    assert '<main class="workspace" id="main-workspace" tabindex="-1">' in shell_source
    assert ".skip-link:focus" in shell_source


def test_adding_repository_does_not_fetch_issues_twice() -> None:
    source = APP_JS
    add_flow = source[source.index("const addRepositoryToList = async") :]
    add_flow = add_flow[: add_flow.index("const appendMessage")]

    assert "await loadRepositories()" in add_flow
    assert "await loadIssues(" not in add_flow
    assert "if (ownedPickerPanel) ownedPickerPanel.hidden = true" in add_flow
    assert "if (ownedRepoSearch) ownedRepoSearch.value = ''" in add_flow
    assert "ownedRepositories = []" in add_flow


def test_repair_ux_exposes_real_phases_verification_and_data_boundary() -> None:
    source = APP_JS
    shell_source = (ROOT / "src/web_ui.py").read_text(encoding="utf-8")

    assert "开始修复" in source
    assert "完成后你只需要查看改动，再决定是否提交" in source
    assert "const order = ['read', 'locate', 'modify', 'verify', 'review']" in source
    assert "验证通过" in source
    assert "验证失败" in source
    assert "等待验证" in source
    assert "验证环境不完整" in source
    assert "这不表示代码本身失败" in source
    assert "missingVerificationTools" in source
    assert "实时修复过程" in source
    assert "每 3 秒自动更新" in source
    assert "读取 Issue 与代码" in source
    assert "运行测试与验证" in source
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
    assert "演示内容不能提交到 GitHub" in source
    assert "修复通过测试或验证后才能提交" in source

    click_guard = source.index("if (!providerAllowsPublishing(currentRepairJob))")
    confirmation_request = source.index("/confirm-token", click_guard)
    publish_request = source.index("/publish", confirmation_request)
    assert click_guard < confirmation_request < publish_request


def test_diff_preview_has_an_offline_fallback_and_single_submit_decision() -> None:
    source = APP_JS
    styles = APP_CSS
    shell = render_shell(title="test", body="", repos=[])

    assert "增强代码视图暂时不可用，已显示离线文本改动" in source
    assert 'class="diff-view-plain"' in source
    assert "const { doc } = _buildDiffDoc(diffData);" in source
    assert "${escapeHtml(doc)}" in source
    assert "renderDiffSidebar();\n      const mounted = await mountDiffEditor" in source
    assert "if (!mounted || !isCurrentRequest()) return;" in source
    assert "const confirmFullDiffForSubmission" in source
    assert 'id="repair-publish"' in shell
    assert 'id="repair-skip-submit"' in shell
    assert "暂不提交" in shell
    assert "代码改动" in shell
    assert "滚动查看全部文件" in shell
    assert "repairSkipSubmit.hidden = !canRevise" in source
    assert ".diff-view-overview { max-height: 156px; overflow: auto;" in styles
    assert ".diff-view-body { display: grid; grid-template-rows: auto minmax(0, 1fr); min-height: 180px;" in styles
    assert 'id="diff-accept-all"' not in shell
    assert 'id="diff-reject-all"' not in shell
    assert 'id="diff-continue-chat"' not in shell


def test_coding_agent_indicator_is_keyboard_accessible_and_reuses_saved_key() -> None:
    source = APP_JS

    assert '<button class="coding-agent-indicator"' in render_shell(
        title="test", body="", repos=[]
    )
    assert "currentCodingAgent.provider ===" in source
    assert "currentCodingAgent.last_error_kind !== 'api_key_invalid'" in source
    assert "error.error_kind === 'api_connection_failed'" in source


def test_brief_generation_has_visible_progress_and_completion_navigation() -> None:
    source = APP_JS

    assert "const startBriefGeneration = async () =>" in source
    assert "fetchJson('/api/briefs/generate'" in source
    assert "`/api/brief-jobs/${encodeURIComponent(jobId)}`" in source
    assert "window.location.assign(job.url)" in source
    assert "briefGenerateButton.addEventListener('click', startBriefGeneration)" in source
