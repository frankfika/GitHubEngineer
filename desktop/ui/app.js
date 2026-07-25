
(() => {
  document.documentElement.dataset.gheUi = 'loading';
  if (window.__TAURI_INTERNALS__) document.documentElement.classList.add('is-tauri');
  const qs = (selector, root = document) => root.querySelector(selector);
  const qsa = (selector, root = document) => [...root.querySelectorAll(selector)];
  const root = qs('#assistant-root');
  const stream = qs('#conversation-stream');
  const composer = qs('#assistant-composer');
  const input = qs('#assistant-input');
  const scroller = qs('.workspace-scroll');
  const dialog = qs('#decision-dialog');
  const decisionForm = qs('#decision-form');
  const repoSwitcher = qs('#repo-switcher');
  const repoViewer = qs('#repo-viewer');
  const issueSummary = qs('#issue-summary');
  const issueInbox = qs('#issue-inbox');
  const refreshIssues = qs('#refresh-issues');
  const activeRepoHeading = qs('#active-repo-heading');
  const dailySummary = qs('#daily-summary');
  const ownedRepoCount = qs('#owned-repo-count');
  const repoPermission = qs('#repo-permission');
  const loadIssuesButton = qs('#load-issues-button');
  const repoMetrics = qs('#repo-metrics');
  const trendChart = qs('#repo-trend-chart');
  const trendCaption = qs('#trend-caption');
  const repoAccessDot = qs('#repo-access-dot');
  const monitorDialog = qs('#monitor-dialog');
  const monitorForm = qs('#monitor-form');
  const repositoryOnboarding = qs('#repository-onboarding');
  const ownedPickerPanel = qs('#owned-picker-panel');
  const ownedRepoSearch = qs('#owned-repo-search');
  const ownedRepoList = qs('#owned-repo-list');
  const repairDialog = qs('#repair-inspector');
  const repairTaskList = qs('#repair-task-list');
  const repairTaskCount = qs('#repair-task-count');
  const repairRepository = qs('#repair-repository');
  const repairTitle = qs('#repair-title');
  const repairDelivery = qs('#repair-delivery');
  const repairStream = qs('#repair-stream');
  const repairGuidanceInput = qs('#repair-guidance-input');
  const repairGuidanceSend = qs('#repair-guidance-send');
  const repairPublish = qs('#repair-publish');
  let pendingDecision = null;
  let currentRepository = root?.dataset.repo || '';
  let currentIssues = [];
  let ownedRepositories = [];
  let pendingIssueTask = null;
  let currentCanModify = false;
  let currentRepairMode = 'fork_pr';
  let repairCapabilities = null;
  let currentRepairIssue = null;
  let currentRepairRepository = '';
  let currentRepairJob = null;
  let repairPollTimer = null;
  let repairJobs = [];

  const escapeHtml = (value) => String(value)
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;').replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');

  const scrollToLatest = () => {
    if (scroller) scroller.scrollTo({ top: scroller.scrollHeight, behavior: 'smooth' });
  };

  const showToast = (message) => {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);
    window.setTimeout(() => toast.remove(), 3200);
  };

  const fetchJson = async (url, options) => {
    // 把 caller 传的 signal 透传给 fetch, 支持 AbortController
    const response = await fetch(url, options);
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || `请求失败 (${response.status})`);
    return result;
  };

  const relativeTime = (value) => {
    const timestamp = Date.parse(value);
    if (!Number.isFinite(timestamp)) return '时间未知';
    const minutes = Math.max(0, Math.floor((Date.now() - timestamp) / 60000));
    if (minutes < 2) return '刚刚更新';
    if (minutes < 60) return `${minutes} 分钟前`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours} 小时前`;
    const days = Math.floor(hours / 24);
    return `${days} 天前`;
  };

  const changedToday = (issue) => Date.now() - Date.parse(issue.updated_at) < 86400000;

  const deltaLabel = (value) => {
    const number = Number(value || 0);
    if (!number) return '较昨日无变化';
    return `${number > 0 ? '+' : ''}${number} 较昨日`;
  };

  const renderTrendChart = (history) => {
    if (!trendChart || !trendCaption) return;
    if (!history?.length) {
      trendChart.innerHTML = '<text x="300" y="62" text-anchor="middle">今天开始记录，明天会出现变化曲线</text>';
      trendCaption.textContent = '尚无历史快照';
      return;
    }
    const width = 600;
    const height = 92;
    const top = 10;
    const makePoints = (field) => {
      const values = history.map((point) => Number(point[field] || 0));
      const min = Math.min(...values);
      const max = Math.max(...values);
      return values.map((value, index) => {
        const x = history.length === 1 ? width / 2 : 8 + index * ((width - 16) / (history.length - 1));
        const y = max === min ? height / 2 : top + (max - value) * ((height - top * 2) / (max - min));
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      }).join(' ');
    };
    trendChart.innerHTML = `
      <line class="grid-line" x1="8" y1="46" x2="592" y2="46"></line>
      <polyline class="star-line" points="${makePoints('stars')}"></polyline>
      <polyline class="issue-line" points="${makePoints('open_issues')}"></polyline>
      <text x="8" y="116">${escapeHtml(history[0].date)}</text>
      <text x="592" y="116" text-anchor="end">${escapeHtml(history.at(-1).date)}</text>`;
    trendCaption.textContent = history.length === 1
      ? '已记录今天的基线'
      : `已连续记录 ${history.length} 天`;
  };

  const renderRepositoryMetrics = (result) => {
    const profile = result.profile || {};
    const deltas = result.deltas || {};
    currentCanModify = Boolean(result.can_ai_modify);
    currentRepairMode = result.repair_mode || (currentCanModify ? 'owner_pr' : 'fork_pr');
    // 成功拉过数据后, refresh 按钮才有意义
    if (refreshIssues) refreshIssues.hidden = false;
    if (repoPermission) {
      repoPermission.hidden = false;
      repoPermission.className = `repo-permission ${currentCanModify ? 'owner' : 'monitor'}`;
      repoPermission.textContent = currentCanModify
        ? 'Owner · 自动修复后提交 Draft PR'
        : '外部仓库 · 通过你的 Fork 贡献 PR';
    }
    if (repoAccessDot) repoAccessDot.className = `repo-access-dot ${currentCanModify ? 'owner' : 'monitor'}`;
    if (repoMetrics) {
      const metrics = [
        ['Stars', profile.stars, deltas.stars],
        ['Forks', profile.forks, deltas.forks],
        ['关注', profile.followers, deltas.followers],
        ['开放 Issue', result.open_count, deltas.open_issues],
      ];
      repoMetrics.innerHTML = metrics.map(([label, value, delta]) => {
        const number = Number(delta || 0);
        const direction = number > 0 ? 'positive' : (number < 0 ? 'negative' : '');
        return `<div class="repo-metric"><span>${label}</span><strong>${Number(value || 0).toLocaleString()}</strong><small class="${direction}">${deltaLabel(number)}</small></div>`;
      }).join('');
    }
    renderTrendChart(result.history || []);
  };

  const renderIssueInbox = (issues) => {
    if (!issueInbox || !issueSummary) return;
    const todayCount = issues.filter(changedToday).length;
    const unassignedCount = issues.filter((issue) => !issue.assignees?.length).length;
    issueSummary.innerHTML = `<span><strong>${issues.length}</strong> 个待处理</span><span><strong>${todayCount}</strong> 个今天有变化</span><span><strong>${unassignedCount}</strong> 个未分配</span>`;
    if (activeRepoHeading) {
      activeRepoHeading.textContent = todayCount
        ? `今天有 ${todayCount} 个 Issue 发生变化`
        : '今天没有新的 Issue 变化';
      // 成功路径也要 remove heading-failed: 万一这次是重试 / 切 repo 后
      // 第一次成功, heading 文本被覆盖成「今天有 N 个」, 颜色若还停在
      // warning 就误导用户当前还在失败.
      activeRepoHeading.classList.remove('heading-failed');
    }
    if (dailySummary) {
      dailySummary.textContent = issues.length
        ? `${currentRepository} · ${issues.length} 个开放 Issue，${unassignedCount} 个尚未分配`
        : `${currentRepository} · 当前没有开放 Issue`;
    }
    if (!issues.length) {
      issueInbox.innerHTML = '<div class="issue-empty"><strong>这个仓库现在没有开放 Issue</strong><span>可以切换其他仓库，或者稍后刷新。</span></div>';
      return;
    }
    const sorted = [...issues].sort((left, right) => {
      const attentionDelta = Number(changedToday(right)) - Number(changedToday(left));
      if (attentionDelta) return attentionDelta;
      const assignmentDelta = Number(!right.assignees?.length) - Number(!left.assignees?.length);
      if (assignmentDelta) return assignmentDelta;
      return Date.parse(right.updated_at) - Date.parse(left.updated_at);
    });
    issueInbox.innerHTML = sorted.slice(0, 30).map((issue) => {
      const labels = (issue.labels || []).slice(0, 2)
        .map((label) => `<span class="issue-label">${escapeHtml(label)}</span>`).join('');
      const attention = changedToday(issue)
        ? '<span class="issue-attention">今天有变化</span>'
        : '';
      const assignment = issue.assignees?.length
        ? `由 ${escapeHtml(issue.assignees.join(', '))} 处理`
        : '尚未分配';
      const repairReady = Boolean(repairCapabilities?.available);
      const repairLabel = repairCapabilities === null
        ? '检查修复环境…'
        : (repairReady ? (currentCanModify ? '自动修复' : '贡献修复') : '修复未就绪');
      const repairTitle = repairReady
        ? ''
        : ` title="${escapeHtml((repairCapabilities?.reasons || ['正在检查 GitHub 和编码 Agent 登录']).join('；'))}"`;
      return `<article class="issue-row">
        <div class="issue-main">
          <a class="issue-title" href="${escapeHtml(issue.url)}" target="_blank" rel="noreferrer"><span class="issue-number">#${issue.number}</span>${escapeHtml(issue.title)}</a>
          <div class="issue-meta">${attention}<span>${relativeTime(issue.updated_at)}</span><span>${issue.comments_count} 条评论</span><span>${assignment}</span>${labels}</div>
        </div>
        <button class="issue-command" type="button" data-issue-command="${issue.number}"${repairTitle} ${repairReady ? '' : 'disabled'}>${repairLabel}</button>
      </article>`;
    }).join('');
  };

  const loadRepairCapabilities = async () => {
    try {
      repairCapabilities = await fetchJson('/api/repair-capabilities');
    } catch (error) {
      repairCapabilities = {
        available: false,
        reasons: [error.message || '自动修复环境检查失败'],
      };
    }
    if (currentIssues.length) renderIssueInbox(currentIssues);
  };

  // 修 race condition: 上一次 in-flight 的 loadIssues 必须被 cancel,
  // 不然 sidebar A→B 连续点, A 的 fetch 晚于 B 回来, A.success 会覆盖
  // B 已经渲染好的 inbox. 用 module 级 AbortController + token 双重保护:
  // 1. fetch 阶段用 AbortController 真断网
  // 2. fetch 完成后还要再检查 token, 防止 race 窗口 (abort 异步生效)
  let loadIssuesToken = 0;
  const loadIssues = async (repository, force = false) => {
    if (!issueInbox || !issueSummary || !repository) return;
    const myToken = ++loadIssuesToken;
    currentRepository = repository;
    if (root) root.dataset.repo = repository;
    if (activeRepoHeading) {
      activeRepoHeading.textContent = `正在读取 ${repository}`;
      // heading-idle 是 SSR 给的「未选择仓库」灰色, 选了 repo 之后必须清掉,
      // 不然 heading 永远 var(--text-2) 灰字重 500, 跟「正在读取」状态不符.
      // heading-failed 是上一次失败残留, 这次重试 / 切 repo 也要清掉,
      // 不然 heading 染 warning 色误导用户当前还在失败.
      activeRepoHeading.classList.remove('heading-idle');
      activeRepoHeading.classList.remove('heading-failed');
    }
    if (dailySummary) dailySummary.textContent = '正在同步仓库动态…';
    // sidebar pill 的 active class 切换: 找出当前 selected 的 pill,
    // 之前 selected 的去掉. 之前用 qs('.repo-name') 是错的 — qs 取首
    // 匹配, 切到第二个 pill 时会改第一个 pill 的 repo 名 + href, tag 不动,
    // 出现 "name=B tag=owner" 错位.
    qsa('.repo-pill').forEach((pill) => {
      pill.classList.toggle('active', pill.dataset.selectRepo === repository);
    });
    if (loadIssuesButton) {
      loadIssuesButton.hidden = true;
      loadIssuesButton.disabled = true;
    }
    currentIssues = [];
    issueSummary.innerHTML = '<span><strong>—</strong> 正在同步 GitHub Issue…</span>';
    issueInbox.innerHTML = '<div class="issue-loading"><span></span><span></span><span></span></div>';
    try {
      const encoded = repository.split('/').map(encodeURIComponent).join('/');
      const result = await fetchJson(`/api/repositories/${encoded}/issues${force ? '?refresh=1' : ''}`);
      // race guard: 如果中途被新的 loadIssues 顶掉, 直接放弃写 DOM,
      // 不要把上一个 repo 的 inbox 覆盖到新 repo 的视图.
      if (myToken !== loadIssuesToken) return;
      currentIssues = result.issues || [];
      renderRepositoryMetrics(result);
      renderIssueInbox(currentIssues);
    } catch (error) {
      // 同样的 race guard: 失败时如果用户已经切到别的 repo, 不要把当前
      // 视图的 heading / 权限栏 / 摘要用旧的 repository 名覆盖掉.
      // (之前的实现用闭包 `repository` 写 DOM, 闭包错位 = P0 bug)
      if (myToken !== loadIssuesToken) return;
      if (error.name === 'AbortError') return;
      // 失败时必须把 heading / 权限栏 / 摘要一起回滚, 不要让用户
      // 看到「正在读取 X」但 issueInbox 又显示「读不到」的不一致状态.
      issueSummary.innerHTML = '<span><strong>同步失败</strong></span>';
      issueInbox.innerHTML = `<div class="issue-error"><strong>Issue 暂时读不到</strong><span>${escapeHtml(error.message || '请检查 GitHub 登录')}</span><div class="error-actions"><button class="soft-button" type="button" data-action="retry-load-issues">重试一次</button><button class="soft-button" type="button" data-open-monitor>换一个仓库</button></div></div>`;
      if (activeRepoHeading) {
        activeRepoHeading.textContent = `${repository} · 读取失败`;
        activeRepoHeading.classList.add('heading-failed');
      }
      if (dailySummary) dailySummary.textContent = '没有拉取任何数据, 不会自动重试';
      if (repoPermission) {
        repoPermission.hidden = false;
        repoPermission.className = 'repo-permission monitor';
        repoPermission.textContent = '未连接成功 · 点击「重试一次」或换一个仓库';
      }
      if (repoAccessDot) repoAccessDot.className = 'repo-access-dot monitor';
      if (loadIssuesButton) {
        loadIssuesButton.hidden = false;
        loadIssuesButton.disabled = false;
        loadIssuesButton.textContent = '重试';
      }
    }
  };

  const loadRepositories = async () => {
    if (!repoSwitcher) return;
    try {
      const result = await fetchJson('/api/repositories');
      const repositories = result.repositories || [];
      // 让 switcher.change 也能查到每个 repo 的 access, 用于更新 owner/monitor 标签
      window.gheRepositories = repositories;
      // 同时刷新 sidebar 的 pill, 加上 owner / monitor tag, 让用户一眼
      // 区分「我的」vs「外部」, 不需要切到主视图才能看到.
      // 点击 pill = 主动选这个 repo (主区切到「已配置」+ 自动 loadIssues).
      // 保留 href 是为了中键 / 右键「在新标签打开 brief」还能用.
      const sidebarList = qs('.repo-list');
      if (sidebarList) {
        if (!repositories.length) {
          sidebarList.innerHTML = '<div class="repo-pill"><span class="repo-name">尚未配置仓库</span></div>';
        } else {
          sidebarList.innerHTML = repositories.map((repository) => {
            const isOwner = repository.access === 'owner';
            const tag = isOwner
              ? '<span class="repo-tag owner">我的</span>'
              : '<span class="repo-tag monitor">外部</span>';
            const cls = isOwner ? 'repo-pill' : 'repo-pill is-monitor';
            return `<a class="${cls}" href="/ui/brief/${encodeURIComponent(repository.full_name)}" data-select-repo="${escapeHtml(repository.full_name)}" title="${escapeHtml(repository.full_name)} · ${isOwner ? '我的仓库' : '外部仓库'} (左键选中并监控, 中键打开简报)"><span class="repo-dot"></span><span class="repo-name">${escapeHtml(repository.full_name)}</span>${tag}</a>`;
          }).join('');
        }
      }
      if (ownedRepoCount) ownedRepoCount.textContent = String(repositories.length);
      repoViewer.textContent = result.viewer ? `@${result.viewer}` : '';
      // topbar select 只用来**切换**已选 repo, 永远不预选. 第一个 option
      // 是「— 请选择 —」, 强制用户主动选.
      repoSwitcher.innerHTML = '<option value="" selected disabled>— 请选择 —</option>'
        + repositories.map((repository) => {
            const suffix = repository.access === 'monitor'
              ? ' · 外部 · 可贡献'
              : (repository.private ? ' · 私有' : '');
            return `<option value="${escapeHtml(repository.full_name)}">${escapeHtml(repository.full_name)}${suffix}</option>`;
          }).join('');
      if (!repositories.length) {
        // 没配置任何 repo: 主区空状态, 引导添加
        currentRepository = '';
        repoSwitcher.innerHTML = '<option value="" selected disabled>还没有添加仓库</option>';
        repoSwitcher.disabled = true;
        if (root) root.classList.add('no-repositories');
        if (repositoryOnboarding) repositoryOnboarding.hidden = false;
        document.documentElement.classList.add('no-repositories');
        if (loadIssuesButton) loadIssuesButton.hidden = true;
        if (activeRepoHeading) {
          activeRepoHeading.textContent = '未选择仓库';
          // 重置回空状态时重新挂上 heading-idle, heading 视觉保持「未选」灰色
          activeRepoHeading.classList.add('heading-idle');
          activeRepoHeading.classList.remove('heading-failed');
        }
        if (dailySummary) dailySummary.textContent = '点右上角「+ 添加仓库」开始, 不会自动读取任何数据。';
        if (repoPermission) {
          repoPermission.hidden = true;
          repoPermission.textContent = '';
        }
        if (issueSummary) issueSummary.innerHTML = '<span><strong>—</strong> 个待处理</span>';
        if (issueInbox) issueInbox.innerHTML = '<div class="issue-empty"><strong>未选择仓库</strong><span>添加一个仓库后再开始监控。</span></div>';
        return;
      }
      // 有 repo 但 init 阶段**不预选任何** (不读 localStorage remembered,
      // 不 fallback 到 repositories[0], 也不信后端的 result.selected).
      // 跟「用户没主动选 = 没用」的原则一致, 避免刚启动就被某个 repo
      // 占据 heading / 触发 fetch. 用户从 sidebar 或 topbar 主动点才算
      // 选中.
      currentRepository = '';
      repoSwitcher.disabled = false;
      repoSwitcher.value = '';
      if (root) {
        root.classList.remove('no-repositories');
        root.dataset.repo = '';
      }
      if (repositoryOnboarding) repositoryOnboarding.hidden = true;
      document.documentElement.classList.remove('no-repositories');
      if (activeRepoHeading) {
        activeRepoHeading.textContent = '未选择仓库';
        // 同样: 重置回「未选」要加回 heading-idle class, 不然 heading 视觉会留
        // 在「已选」时的黑色加粗.
        activeRepoHeading.classList.add('heading-idle');
        activeRepoHeading.classList.remove('heading-failed');
      }
      if (dailySummary) dailySummary.textContent = repositories.length === 1
        ? `已加载 1 个追踪仓库, 左侧点一下开始。`
        : `已加载 ${repositories.length} 个追踪仓库, 左侧或上方选一个开始。`;
      if (repoPermission) {
        repoPermission.hidden = true;
        repoPermission.textContent = '';
      }
      if (loadIssuesButton) loadIssuesButton.hidden = true;
      // 重置回「未选择仓库」时, refresh 按钮也得 hidden — 不然处于
      // 「可见但 currentRepository 为空」状态, 点下去只会弹 toast,
      // 撞出「看着能点, 点了只弹 toast」的废按钮.
      if (refreshIssues) refreshIssues.hidden = true;
      if (issueSummary) issueSummary.innerHTML = '<span><strong>—</strong> 个待处理</span>';
      if (issueInbox) issueInbox.innerHTML = '<div class="issue-empty"><strong>未选择仓库</strong><span>点 sidebar 的 repo (或上方下拉) 选中后, 会自动拉取 Issue。</span></div>';
      // 重置时也清掉所有 pill 的 active class, 避免上一次的「selected」
      // 视觉残留. 用户没选 = 全不 active.
      qsa('.repo-pill').forEach((pill) => pill.classList.remove('active'));
    } catch (error) {
      repoSwitcher.innerHTML = '<option value="" selected disabled>无法读取仓库</option>';
      repoSwitcher.disabled = true;
      issueSummary.innerHTML = '<span><strong>—</strong> 个待处理</span>';
      issueInbox.innerHTML = `<div class="issue-error"><strong>仓库列表读取失败</strong><span>${escapeHtml(error.message || '请运行 gh auth login')}</span></div>`;
      if (loadIssuesButton) loadIssuesButton.hidden = true;
      if (refreshIssues) refreshIssues.hidden = true;
      currentRepository = '';
      if (root) root.dataset.repo = '';
      if (activeRepoHeading) {
        activeRepoHeading.textContent = '仓库列表读取失败';
        activeRepoHeading.classList.add('heading-failed');
      }
      if (dailySummary) dailySummary.textContent = '检查 GitHub token 或网络连接后再试, 没选 repo 之前不会自动重试。';
    }
  };

  const renderOwnedRepositoryChoices = () => {
    if (!ownedRepoList) return;
    const query = String(ownedRepoSearch?.value || '').trim().toLocaleLowerCase();
    const visible = ownedRepositories
      .filter((repository) => !query || repository.full_name.toLocaleLowerCase().includes(query))
      .slice(0, 40);
    if (!visible.length) {
      ownedRepoList.innerHTML = '<div class="issue-empty"><strong>没有匹配的仓库</strong><span>换个名称试试。</span></div>';
      return;
    }
    ownedRepoList.innerHTML = visible.map((repository) => `
      <div class="owned-repo-row">
        <div class="owned-repo-copy">
          <div class="owned-repo-name">${escapeHtml(repository.full_name)}</div>
          <div class="owned-repo-meta">${repository.private ? '私有仓库' : '公开仓库'}${repository.language ? ` · ${escapeHtml(repository.language)}` : ''}</div>
        </div>
        <button class="owned-repo-add" type="button" data-add-owned="${escapeHtml(repository.full_name)}" ${repository.tracked ? 'disabled' : ''}>${repository.tracked ? '已添加' : '添加'}</button>
      </div>`).join('');
  };

  const loadOwnedRepositoryChoices = async () => {
    if (!ownedPickerPanel || !ownedRepoList) return;
    ownedPickerPanel.hidden = false;
    ownedRepoList.innerHTML = '<div class="issue-loading"><span></span><span></span><span></span></div>';
    try {
      const result = await fetchJson('/api/owned-repositories');
      ownedRepositories = result.repositories || [];
      renderOwnedRepositoryChoices();
      ownedRepoSearch?.focus();
    } catch (error) {
      ownedRepoList.innerHTML = `<div class="issue-error"><strong>无法读取我的仓库</strong><span>${escapeHtml(error.message || '请检查 GitHub 登录')}</span></div>`;
    }
  };

  const addRepositoryToList = async (repository, button) => {
    if (button) {
      button.disabled = true;
      button.textContent = '添加中…';
    }
    try {
      const result = await fetchJson('/api/tracked-repositories', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repository }),
      });
      try { window.localStorage.setItem('ghe:selected-repository', result.full_name); } catch (_) {}
      monitorDialog?.close();
      monitorForm?.reset();
      await loadRepositories();
      // 用户主动添加仓库, 视为「明确要监控」, 自动拉一次数据
      // (如果失败, heading 会被回滚到失败态, 用户可以重试或换别的).
      showToast(`${result.full_name} 已添加到清单, 开始拉取数据…`);
      await loadIssues(result.full_name);
    } catch (error) {
      showToast(error.message || '无法添加仓库');
      if (button) {
        button.disabled = false;
        button.textContent = '添加';
      }
      throw error;
    }
  };

  const appendMessage = (role, html) => {
    if (!stream) return;
    const item = document.createElement('section');
    item.className = `message ${role}`;
    const isUser = role === 'user';
    item.innerHTML = `
      <div class="avatar ${isUser ? 'user-avatar' : ''}">${isUser ? '你' : 'GE'}</div>
      <div class="message-body">
        <div class="message-meta"><strong>${isUser ? '你' : 'GitHub Engineer'}</strong><span>刚刚</span></div>
        <div class="message-card">${html}</div>
      </div>`;
    stream.appendChild(item);
    scrollToLatest();
    return item;
  };

  const decisionLabels = {
    accepted: '接受',
    rejected: '拒绝',
    deferred: '延后',
  };

  const parseDecision = (prompt) => {
    const match = prompt.trim().match(/^(接受|同意|采纳|拒绝|不做|延后|推迟)\s*(.+?)(?:[，,]?\s*(?:因为|原因(?:是|为)?)|[；;。]\s*)[：:]?\s*(.+)$/);
    if (!match) return null;
    const status = /接受|同意|采纳/.test(match[1])
      ? 'accepted'
      : (/延后|推迟/.test(match[1]) ? 'deferred' : 'rejected');
    const subject = match[2].trim();
    const reason = match[3].trim();
    if (!subject || !reason) return null;
    const issueMatch = subject.match(/^#?(\d+)$/);
    return {
      status,
      reason,
      ...(issueMatch
        ? { issue_number: [Number(issueMatch[1])] }
        : { theme: [subject] }),
    };
  };

  const decisionSubject = (draft) => draft.issue_number?.length
    ? `Issue #${draft.issue_number[0]}`
    : (draft.theme?.[0] || '未指定范围');

  const renderBriefExcerpt = (markdown) => {
    const lines = markdown.split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean)
      .filter((line) => !/^```/.test(line))
      .slice(0, 14);
    if (!lines.length) return '<div class="brief-line">简报内容为空。</div>';
    return lines.map((line) => {
      const clean = line.replace(/^#{1,6}\s*/, '').replace(/^[-*]\s+/, '');
      const kind = /^#{1,6}\s/.test(line) ? ' heading' : (/^[-*]\s+/.test(line) ? ' bullet' : '');
      return `<div class="brief-line${kind}">${escapeHtml(clean)}</div>`;
    }).join('');
  };

  const saveDecision = async (payload) => {
    const response = await fetch('/decisions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || '无法记录决策');
    return result;
  };

  const repairStatusLabels = {
    queued: '修复任务已排队',
    cloning: '正在准备代码',
    coding: 'AI 正在修复并测试',
    review_ready: '等待你的检查',
    publish_queued: '已确认创建 PR',
    publishing: '正在创建 Draft PR',
    completed: '修复已提交',
    failed: '自动修复未完成',
  };

  const repairStorageKey = (repository, issueNumber) => `ghe:repair:${repository}#${issueNumber}`;

  const repairTaskClass = (status) => {
    if (status === 'review_ready') return 'review';
    if (status === 'completed') return 'done';
    if (status === 'failed') return 'failed';
    return 'running';
  };

  const renderRepairTaskList = (jobs = []) => {
    repairJobs = jobs;
    if (!repairTaskList) return;
    const activeCount = jobs.filter((job) => !['completed', 'failed'].includes(job.status)).length;
    if (repairTaskCount) repairTaskCount.textContent = String(activeCount);
    if (!jobs.length) {
      repairTaskList.innerHTML = '<div class="task-empty">还没有修复任务。<br>从 Issue 开始一个。</div>';
      return;
    }
    repairTaskList.innerHTML = jobs.slice(0, 30).map((job) => {
      const selected = currentRepairJob?.id === job.id ? ' active' : '';
      const title = job.issue_title || `Issue #${job.issue_number}`;
      const status = repairStatusLabels[job.status] || job.status || '未知状态';
      return `<button class="task-item${selected}" type="button" data-repair-job="${escapeHtml(job.id)}"><span class="task-item-dot ${repairTaskClass(job.status)}"></span><span><span class="task-item-title">${escapeHtml(title)}</span><span class="task-item-meta"><span>${escapeHtml(job.repository || '')} · #${escapeHtml(job.issue_number || '')}</span><span>${escapeHtml(status)}</span></span></span></button>`;
    }).join('');
  };

  const loadRepairJobs = async () => {
    try {
      const jobs = await fetchJson('/api/repairs');
      renderRepairTaskList(Array.isArray(jobs) ? jobs : []);
      if (currentRepairJob && !['review_ready', 'completed', 'failed'].includes(currentRepairJob.status)) {
        const latest = jobs.find((job) => job.id === currentRepairJob.id);
        if (latest) currentRepairJob = latest;
      }
    } catch (_) {
      // The task rail is supplementary; the selected conversation remains usable.
    }
  };

  const showRepairInspector = () => {
    if (!repairDialog) return;
    repairDialog.hidden = false;
    if (scroller) scroller.hidden = true;
  };

  const closeRepairInspector = () => {
    if (!repairDialog) return;
    repairDialog.hidden = true;
    if (scroller) scroller.hidden = false;
    window.clearTimeout(repairPollTimer);
  };

  const setRepairPhase = (status) => {
    const order = ['prepare', 'code', 'review', 'publish'];
    const current = ['queued', 'cloning'].includes(status)
      ? 'prepare'
      : (status === 'coding' ? 'code' : (status === 'review_ready' ? 'review' : 'publish'));
    const currentIndex = order.indexOf(current);
    qsa('[data-repair-phase]', repairDialog).forEach((element) => {
      const index = order.indexOf(element.dataset.repairPhase);
      element.classList.toggle('active', index === currentIndex);
      element.classList.toggle('complete', index < currentIndex || status === 'completed');
    });
  };

  const repairEvent = (role, title, body, output = '') => `
    <section class="repair-event ${role}">
      <div class="repair-event-avatar">${role === 'user' ? '你' : 'GE'}</div>
      <div class="repair-event-body">
        <div class="repair-event-meta">${role === 'user' ? '你的指导' : escapeHtml(title)}</div>
        <div class="repair-event-card">${body}${output ? `<div class="repair-output">${escapeHtml(output)}</div>` : ''}</div>
      </div>
    </section>`;

  const renderRepairSession = (job = null) => {
    if (!repairDialog || !repairStream || !currentRepairIssue) return;
    const destination = currentRepairMode === 'owner_pr'
      ? '你的分支 → Draft PR'
      : '你的 Fork → 上游 Draft PR';
    repairRepository.textContent = `${currentRepairRepository || currentRepository} · #${currentRepairIssue.number}`;
    repairTitle.textContent = currentRepairIssue.title;
    repairDelivery.textContent = destination;
    currentRepairJob = job;
    showRepairInspector();
    if (!job) {
      setRepairPhase('queued');
      repairStream.innerHTML = repairEvent(
        'assistant',
        '修复计划',
        `<strong>${currentCanModify ? '自动修复' : '贡献修复'}</strong><br>AI 会先在隔离目录修改代码并运行测试。代码完成后会暂停，等待你检查和指导；此阶段不会创建 Fork、Push 或 PR。<div class="suggestions"><button class="suggestion primary-suggestion" type="button" data-start-repair>开始编码</button><a class="suggestion" href="${escapeHtml(currentRepairIssue.url)}" target="_blank" rel="noreferrer">打开 Issue</a></div>`,
      );
      repairGuidanceInput.disabled = true;
      repairGuidanceSend.disabled = true;
      repairPublish.disabled = true;
      return;
    }
    setRepairPhase(job.status);
    const events = [
      repairEvent(
        'assistant',
        repairStatusLabels[job.status] || '修复会话',
        `<strong>${escapeHtml(repairStatusLabels[job.status] || job.status)}</strong><br>${escapeHtml(job.message || '')}`,
      ),
    ];
    (job.guidance || []).forEach((item) => {
      events.push(repairEvent('user', '你的指导', escapeHtml(item.text || '')));
    });
    if (job.agent_summary) {
      events.push(repairEvent(
        'assistant',
        '编码输出',
        '<strong>AI 的修改说明</strong>',
        `${job.agent_summary}${job.diff_stat ? `\n\n变更统计\n${job.diff_stat}` : ''}`,
      ));
    }
    if (job.pr_url) {
      events.push(repairEvent(
        'assistant',
        'Draft PR',
        `<strong>已经提交，等待人工审核</strong><div class="suggestions"><a class="suggestion primary-suggestion" href="${escapeHtml(job.pr_url)}" target="_blank" rel="noreferrer">查看 Draft PR</a></div>`,
      ));
    }
    repairStream.innerHTML = events.join('');
    renderRepairTaskList(repairJobs);
    const canGuide = job.status === 'review_ready';
    repairGuidanceInput.disabled = !canGuide;
    repairGuidanceSend.disabled = !canGuide;
    repairPublish.disabled = !canGuide;
    repairPublish.textContent = currentRepairMode === 'fork_pr'
      ? '确认 Fork 并创建 Draft PR'
      : '确认创建 Draft PR';
    repairStream.scrollTop = repairStream.scrollHeight;
  };

  const pollRepairJob = async (jobId) => {
    window.clearTimeout(repairPollTimer);
    try {
      const job = await fetchJson(`/api/repairs/${encodeURIComponent(jobId)}`);
      renderRepairSession(job);
      await loadRepairJobs();
      if (!['review_ready', 'completed', 'failed'].includes(job.status)) {
        repairPollTimer = window.setTimeout(() => pollRepairJob(jobId), 3000);
      }
    } catch (error) {
      if (repairStream) {
        repairStream.innerHTML = repairEvent(
          'assistant',
          '状态读取失败',
          escapeHtml(error.message || '稍后可以重新打开会话检查'),
        );
      }
    }
  };

  const presentIssueCommand = async (issue, instruction) => {
    currentRepairIssue = issue;
    currentRepairRepository = currentRepository;
    pendingIssueTask = {
      repository: currentRepository,
      issue_number: issue.number,
      instruction: instruction || `自动修复 Issue #${issue.number}`,
    };
    showRepairInspector();
    let savedJobId = '';
    try { savedJobId = window.localStorage.getItem(repairStorageKey(currentRepository, issue.number)) || ''; } catch (_) {}
    if (savedJobId) {
      try {
        const job = await fetchJson(`/api/repairs/${encodeURIComponent(savedJobId)}`);
        if (job.repository === currentRepository && Number(job.issue_number) === issue.number) {
          renderRepairSession(job);
          if (!['review_ready', 'completed', 'failed'].includes(job.status)) pollRepairJob(job.id);
          return;
        }
      } catch (_) {}
    }
    renderRepairSession();
  };

  const openRepairJob = async (job) => {
    currentRepairJob = job;
    currentRepairRepository = job.repository || currentRepository;
    currentRepairIssue = currentIssues.find((item) => Number(item.number) === Number(job.issue_number)) || {
      number: Number(job.issue_number),
      title: job.issue_title || `Issue #${job.issue_number}`,
      url: `https://github.com/${job.repository}/issues/${job.issue_number}`,
    };
    pendingIssueTask = null;
    showRepairInspector();
    renderRepairSession(job);
    if (!['review_ready', 'completed', 'failed'].includes(job.status)) pollRepairJob(job.id);
  };

  const presentIssueAnalysis = (issue) => {
    appendMessage('assistant', `<h3>${escapeHtml(currentRepository)}#${issue.number} 分析</h3><p><strong>${escapeHtml(issue.title)}</strong></p><div class="decision-summary"><div class="decision-summary-row"><span>状态</span><strong>${changedToday(issue) ? '今天有变化' : relativeTime(issue.updated_at)}</strong></div><div class="decision-summary-row"><span>讨论</span><strong>${issue.comments_count} 条评论 · ${issue.assignees?.length ? `已分配给 ${escapeHtml(issue.assignees.join(', '))}` : '尚未分配'}</strong></div></div><p style="margin-top:12px">需要落地时，可以继续说“修复 #${issue.number}”。${currentCanModify ? '系统会向你的仓库提交 Draft PR。' : '系统会通过你的 Fork 向上游贡献 Draft PR。'}</p>`);
  };

  const assistantReply = async (prompt) => {
    if (!root) return;
    const text = prompt.toLowerCase();
    const latest = root.dataset.latestBrief;
    const repo = root.dataset.repo || '当前仓库';
    const briefCount = root.dataset.briefCount || '0';
    const decisionCount = root.dataset.decisionCount || '0';
    const issueCommand = prompt.match(/(?:分析|处理|修复|安排)(?:一下|这个|下)?\s*(?:issue\s*)?#(\d+)/i);

    if (issueCommand) {
      const issueNumber = Number(issueCommand[1]);
      const issue = currentIssues.find((item) => item.number === issueNumber);
      if (!issue) {
        appendMessage('assistant', `<h3>当前列表里没有 #${issueNumber}</h3><p>先在上方切换到对应仓库，或刷新 Issue 列表后再试。</p>`);
      } else if (/分析/.test(prompt) && !/(处理|修复|安排)/.test(prompt)) {
        presentIssueAnalysis(issue);
      } else {
        presentIssueCommand(issue, prompt);
      }
      return;
    }

    if (/决策|决定|接受|同意|采纳|拒绝|不做|延后|推迟/.test(text)) {
      const draft = parseDecision(prompt);
      if (draft) {
        pendingDecision = draft;
        appendMessage('assistant', `<h3>我理解的是这个决定</h3><p>保存前只需要确认一次。</p><div class="decision-summary"><div class="decision-summary-row"><span>决定</span><strong><i class="status-dot ${draft.status}"></i>${decisionLabels[draft.status]}</strong></div><div class="decision-summary-row"><span>范围</span><strong>${escapeHtml(decisionSubject(draft))}</strong></div><div class="decision-summary-row"><span>原因</span><strong>${escapeHtml(draft.reason)}</strong></div></div><div class="suggestions"><button class="suggestion primary-suggestion" type="button" data-confirm-decision>确认记住</button><button class="suggestion" type="button" data-open-decision>修改细节</button></div>`);
      } else {
        appendMessage('assistant', `<h3>直接用一句话告诉我</h3><p>例如：<strong>拒绝 OAuth 重构，因为本季度先处理稳定性。</strong> 我会先复述给你确认，再写入记忆。</p><div class="suggestions"><button class="suggestion" type="button" data-open-decision>改用详细填写</button><a class="suggestion" href="/ui/decisions">已有 ${decisionCount} 条</a></div>`);
        if (input) {
          input.placeholder = '例如：延后 #42，因为要先完成发布…';
          input.focus();
        }
      }
      return;
    }
    if (/简报|优先|issue|问题|报告/.test(text)) {
      if (!latest) {
        appendMessage('assistant', `<h3>还没有可读的简报</h3><p>${escapeHtml(repo)} 尚未生成本地简报。生成后，我会直接在这里提炼重点。</p>`);
        return;
      }
      try {
        const briefPath = latest.replace('/ui/briefs/', '/briefs/');
        const response = await fetch(briefPath);
        if (!response.ok) throw new Error('无法读取最新简报');
        const markdown = await response.text();
        appendMessage('assistant', `<h3>最新本地简报</h3><p>我把最前面的关键信息直接展开了，不需要跳出对话；具体仓库以简报内容为准。</p><div class="inline-brief">${renderBriefExcerpt(markdown)}</div><div class="suggestions"><a class="suggestion" href="${escapeHtml(latest)}">查看完整简报</a><button class="suggestion" type="button" data-decision-guide>告诉我一个决定</button></div>`);
      } catch (error) {
        appendMessage('assistant', `<h3>简报暂时读不到</h3><p>${escapeHtml(error.message || '请稍后重试')}</p>`);
      }
      return;
    }
    if (/配置|仓库|repo|模型|目录/.test(text)) {
      appendMessage('assistant', `<h3>当前工作区</h3><p>正在跟踪 <strong>${escapeHtml(repo)}</strong>。配置仍由 <code>.ghe/config.yml</code> 管理，界面只展示安全的运行信息，不显示 Token 或模型密钥。</p>`);
      return;
    }
    appendMessage('assistant', '<h3>我可以帮你快速收敛维护工作</h3><p>你可以直接说“看看最新简报”“记录一个拒绝决定”或“当前仓库配置”。需要执行代码任务时，我会先帮你把范围和验收标准整理清楚。</p>');
  };

  if (composer && input) {
    composer.addEventListener('submit', (event) => {
      event.preventDefault();
      const value = input.value.trim();
      if (!value) return;
      appendMessage('user', `<p>${escapeHtml(value)}</p>`);
      input.value = '';
      input.style.height = 'auto';
      window.setTimeout(() => assistantReply(value), 180);
    });
    input.addEventListener('input', () => {
      input.style.height = 'auto';
      input.style.height = `${Math.min(input.scrollHeight, 126)}px`;
    });
    input.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
        event.preventDefault();
        composer.requestSubmit();
      }
    });
  }

  document.addEventListener('click', (event) => {
    const promptButton = event.target.closest('[data-prompt]');
    if (promptButton && input && composer) {
      input.value = promptButton.dataset.prompt || promptButton.textContent.trim();
      composer.requestSubmit();
      return;
    }
    if (event.target.closest('[data-decision-guide]')) {
      appendMessage('assistant', '<h3>把决定直接说出来</h3><p>一句话就够：<strong>接受 / 延后 / 拒绝什么，因为……</strong> 我会先复述，再让你确认。</p>');
      if (input) {
        input.placeholder = '例如：拒绝 OAuth 重构，因为本季度先处理稳定性…';
        input.focus();
      }
      return;
    }
    const issueCommandButton = event.target.closest('[data-issue-command]');
    if (issueCommandButton) {
      const issueNumber = Number(issueCommandButton.dataset.issueCommand);
      const issue = currentIssues.find((item) => item.number === issueNumber);
      if (issue) {
        presentIssueCommand(issue, currentCanModify
          ? `自动修复 Issue #${issue.number}，优先补齐验证`
          : `修复 Issue #${issue.number} 并通过 Fork 向上游贡献`);
      }
      return;
    }
    const repairTaskButton = event.target.closest('[data-repair-job]');
    if (repairTaskButton) {
      const job = repairJobs.find((item) => item.id === repairTaskButton.dataset.repairJob);
      if (job) openRepairJob(job);
      return;
    }
    if (event.target.closest('[data-start-repair]') && pendingIssueTask) {
      const button = event.target.closest('[data-start-repair]');
      button.disabled = true;
      button.textContent = '正在启动…';
      fetchJson('/api/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(pendingIssueTask),
      }).then((result) => {
        currentRepairJob = result;
        try {
          window.localStorage.setItem(
            repairStorageKey(result.repository, result.issue_number),
            result.id,
          );
        } catch (_) {}
        renderRepairSession(result);
        pollRepairJob(result.id);
        loadRepairJobs();
        pendingIssueTask = null;
      }).catch((error) => {
        showToast(error.message || '自动修复启动失败');
        button.disabled = false;
        button.textContent = '开始编码';
      });
      return;
    }
    if (event.target.closest('[data-confirm-decision]') && pendingDecision) {
      const button = event.target.closest('[data-confirm-decision]');
      button.disabled = true;
      button.textContent = '正在记住…';
      saveDecision(pendingDecision)
        .then((result) => {
          appendMessage('assistant', `<h3>已经记住</h3><p>这条 <strong>${escapeHtml(decisionLabels[result.status] || result.status)}</strong> 决策已保存。下一份简报会把它当作维护边界。</p>`);
          pendingDecision = null;
          button.closest('.suggestions')?.remove();
        })
        .catch((error) => {
          showToast(error.message || '记录失败，请稍后重试');
          button.disabled = false;
          button.textContent = '确认记住';
        });
      return;
    }
    if (event.target.closest('[data-open-decision]') && dialog) dialog.showModal();
    if (event.target.closest('[data-close-dialog]') && dialog) dialog.close();
    if (event.target.closest('[data-open-monitor]') && monitorDialog) monitorDialog.showModal();
    if (event.target.closest('[data-open-owned]') && monitorDialog) {
      monitorDialog.showModal();
      loadOwnedRepositoryChoices();
    }
    if (event.target.closest('[data-load-owned]')) loadOwnedRepositoryChoices();
    const ownedAddButton = event.target.closest('[data-add-owned]');
    if (ownedAddButton) {
      addRepositoryToList(ownedAddButton.dataset.addOwned, ownedAddButton).catch(() => {});
    }
    if (event.target.closest('[data-close-monitor]') && monitorDialog) monitorDialog.close();
    if (event.target.closest('[data-close-repair]')) closeRepairInspector();
  });

  if (decisionForm && dialog) {
    decisionForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const button = qs('button[type="submit"]', decisionForm);
      const payload = Object.fromEntries(new FormData(decisionForm).entries());
      if (payload.issue_number) payload.issue_number = [payload.issue_number];
      if (payload.theme) payload.theme = [payload.theme];
      button.disabled = true;
      button.textContent = '记录中…';
      try {
        const result = await saveDecision(payload);
        dialog.close();
        decisionForm.reset();
        if (stream) {
          appendMessage('assistant', `<h3>已经记住</h3><p>这条 <strong>${escapeHtml(result.status)}</strong> 决策已保存。下一次生成简报时，我会把它作为维护边界。</p>`);
        } else {
          showToast('决策已保存，下一份简报会使用这条记忆。');
        }
      } catch (error) {
        showToast(error.message || '记录失败，请稍后重试');
      } finally {
        button.disabled = false;
        button.textContent = '记录决策';
      }
    });
  }

  if (repoSwitcher) {
    repoSwitcher.addEventListener('change', () => {
      const repository = repoSwitcher.value;
      if (!repository) return;  // 用户选了 "— 请选择 —" 不动
      try { window.localStorage.setItem('ghe:selected-repository', repository); } catch (_) {}
      // topbar 下拉 = 用户明确选了 repo, 视为「开始用这个」, 立刻 loadIssues.
      loadIssues(repository);
    });
    loadRepairCapabilities();
    loadRepositories();
    loadRepairJobs();
  }

  // sidebar pill 左键 = 选中 + loadIssues (主区切换).
  // 中键 / 右键「在新标签打开」保留默认行为 (跳 /ui/brief/{repo}).
  document.addEventListener('click', (event) => {
    const pill = event.target.closest('[data-select-repo]');
    if (!pill) return;
    if (event.button !== 0) return;        // 中键右键放行
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;  // 修饰键放行
    event.preventDefault();
    const repository = pill.dataset.selectRepo;
    if (!repository) return;
    try { window.localStorage.setItem('ghe:selected-repository', repository); } catch (_) {}
    if (repoSwitcher) repoSwitcher.value = repository;  // 同步 topbar
    loadIssues(repository);
  });
  document.documentElement.dataset.gheUi = 'ready';

  if (refreshIssues) {
    refreshIssues.addEventListener('click', () => {
      if (currentRepository) loadIssues(currentRepository, true);
      else showToast('先选一个仓库, 再点刷新');
    });
  }

  if (loadIssuesButton) {
    loadIssuesButton.addEventListener('click', () => {
      // 用 currentRepository 而不是 dataset.repo: 失败回滚后 loadIssuesButton
      // 切到「重试」状态, 此时用户可能已经切到别的 repo, dataset.repo
      // 残留会导致点「重试」去拉旧 repo, 用全局 currentRepository 更稳.
      const target = currentRepository;
      if (target) loadIssues(target, loadIssuesButton.textContent === '重试');
    });
  }

  // 失败提示卡里的「重试 / 换仓库」按钮
  document.addEventListener('click', (event) => {
    const retry = event.target.closest('[data-action="retry-load-issues"]');
    if (retry && currentRepository) loadIssues(currentRepository, true);
  });

  if (ownedRepoSearch) {
    ownedRepoSearch.addEventListener('input', renderOwnedRepositoryChoices);
  }

  if (repairGuidanceSend) {
    repairGuidanceSend.addEventListener('click', async () => {
      const message = repairGuidanceInput.value.trim();
      if (!currentRepairJob || currentRepairJob.status !== 'review_ready' || !message) return;
      repairGuidanceSend.disabled = true;
      repairGuidanceSend.textContent = '发送中…';
      try {
        const result = await fetchJson(`/api/repairs/${encodeURIComponent(currentRepairJob.id)}/guidance`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message }),
        });
        repairGuidanceInput.value = '';
        renderRepairSession(result);
        pollRepairJob(result.id);
      } catch (error) {
        showToast(error.message || '指导发送失败');
      } finally {
        repairGuidanceSend.textContent = '发送指导';
        if (currentRepairJob?.status === 'review_ready') repairGuidanceSend.disabled = false;
      }
    });
  }

  if (repairPublish) {
    repairPublish.addEventListener('click', async () => {
      if (!currentRepairJob || currentRepairJob.status !== 'review_ready') return;
      repairPublish.disabled = true;
      repairPublish.textContent = '正在确认…';
      try {
        const result = await fetchJson(`/api/repairs/${encodeURIComponent(currentRepairJob.id)}/publish`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: '{}',
        });
        renderRepairSession(result);
        pollRepairJob(result.id);
      } catch (error) {
        showToast(error.message || 'Draft PR 创建失败');
        repairPublish.disabled = false;
        repairPublish.textContent = currentRepairMode === 'fork_pr'
          ? '确认 Fork 并创建 Draft PR'
          : '确认创建 Draft PR';
      }
    });
  }

  if (monitorForm && monitorDialog) {
    monitorForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const button = qs('button[type="submit"]', monitorForm);
      const repository = String(new FormData(monitorForm).get('repository') || '').trim();
      button.disabled = true;
      button.textContent = '添加中…';
      try {
        await addRepositoryToList(repository);
      } catch (_) {
      } finally {
        button.disabled = false;
        button.textContent = '添加到清单';
      }
    });
  }

  window.setInterval(() => {
    if (currentRepository && !document.hidden) loadIssues(currentRepository);
  }, 300000);
  window.setInterval(() => {
    if (!document.hidden) loadRepairJobs();
  }, 5000);
})();
