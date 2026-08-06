"""Presentation assets for the local maintainer-assistant UI.

The web service deliberately stays dependency-free.  Keeping the CSS, the
small progressive-enhancement script, and the application shell here stops
``main.py`` from becoming a second frontend framework while still allowing the
installed wheel to serve a polished interface without package-data plumbing.
"""

from __future__ import annotations

from html import escape


APP_CSS = r"""
:root {
  color-scheme: light dark;
  --canvas: #f4f4f1;
  --sidebar: rgba(246, 246, 243, .86);
  --surface: rgba(255, 255, 253, .82);
  --surface-solid: #fffffd;
  --surface-soft: rgba(245, 245, 241, .82);
  --text: #171816;
  --text-2: #5d6059;
  --text-3: #92968d;
  --line: rgba(27, 29, 25, .10);
  --line-strong: rgba(27, 29, 25, .17);
  --accent: #1d4f43;
  --accent-soft: #e2eee9;
  --success: #237a51;
  --warning: #9a6514;
  --danger: #a8473e;
  --sidebar-width: 72px;
  --ease: cubic-bezier(.25, .1, .25, 1);
}

@media (prefers-color-scheme: dark) {
  :root {
    --canvas: #111310;
    --sidebar: rgba(23, 25, 22, .88);
    --surface: rgba(29, 31, 28, .84);
    --surface-solid: #1d1f1c;
    --surface-soft: rgba(39, 42, 37, .82);
    --text: #f3f4ef;
    --text-2: #b5b9af;
    --text-3: #7d8278;
    --line: rgba(255, 255, 255, .09);
    --line-strong: rgba(255, 255, 255, .16);
    --accent: #a8d8c6;
    --accent-soft: #243c34;
    --success: #78c99e;
    --warning: #ddb46e;
    --danger: #e6948b;
  }
}

* { box-sizing: border-box; }
[hidden] { display: none !important; }
html, body { height: 100%; }
body {
  margin: 0;
  overflow: hidden;
  background: var(--canvas);
  color: var(--text);
  font: 14px/1.55 -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", sans-serif;
  -webkit-font-smoothing: antialiased;
}
button, input, select, textarea { font: inherit; }
button, a { -webkit-tap-highlight-color: transparent; }
button:disabled { cursor: not-allowed; }
button:focus-visible, a:focus-visible, input:focus-visible, select:focus-visible, textarea:focus-visible, summary:focus-visible {
  outline: 2px solid color-mix(in srgb, var(--accent) 72%, transparent);
  outline-offset: 2px;
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: none; }
.skip-link { position: fixed; z-index: 1000; top: 8px; left: 8px; padding: 9px 12px; color: var(--text); background: var(--surface-solid); border: 2px solid var(--accent); border-radius: 8px; transform: translateY(-160%); transition: transform .12s ease; }
.skip-link:focus { transform: translateY(0); }

.app-shell { display: flex; width: 100%; height: 100dvh; }
.sidebar {
  width: 276px;
  flex: 0 0 276px;
  display: flex;
  flex-direction: column;
  padding: 18px 12px 14px;
  background: var(--sidebar);
  backdrop-filter: blur(28px) saturate(1.15);
  border-right: 1px solid var(--line);
}
.is-tauri .sidebar { padding-top: 44px; }
.brand { display: flex; align-items: center; gap: 9px; min-height: 38px; padding: 0 7px; }
.brand-mark, .avatar {
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  color: #f7faf7;
  background: var(--accent);
}
.brand-mark { width: 28px; height: 28px; border-radius: 9px; }
.brand-mark svg { width: 15px; height: 15px; }
.brand-title { display: block; margin: 0; color: var(--text); font-size: 13px; font-weight: 700; letter-spacing: -.01em; }
.workspace-label { display: block; margin: 17px 8px 6px; color: var(--text-3); font-size: 10px; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; }
.repo-list { display: grid; gap: 3px; max-height: 112px; overflow: auto; }
.repo-pill {
  display: flex;
  align-items: center;
  gap: 9px;
  min-height: 38px;
  padding: 8px 10px;
  overflow: hidden;
  color: var(--text-2);
  border: 1px solid transparent;
  border-radius: 10px;
  transition: .2s var(--ease);
}
.repo-pill:hover { color: var(--text); background: var(--surface-soft); }
.repo-pill.active { color: var(--text); background: var(--surface); border-color: var(--line); }
.repo-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--success); box-shadow: 0 0 0 3px color-mix(in srgb, var(--success) 13%, transparent); }
.repo-pill.is-monitor .repo-dot { background: var(--warning); box-shadow: 0 0 0 3px color-mix(in srgb, var(--warning) 13%, transparent); }
.repo-pill .repo-tag { flex: 0 0 auto; font-size: 9px; padding: 1px 5px; border-radius: 4px; letter-spacing: .04em; }
.repo-pill .repo-tag.owner { color: var(--success); background: color-mix(in srgb, var(--success) 12%, transparent); }
.repo-pill .repo-tag.monitor { color: var(--warning); background: color-mix(in srgb, var(--warning) 12%, transparent); }
.repo-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.side-nav { display: grid; gap: 6px; margin-top: 24px; }
.nav-link {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  min-height: 38px;
  padding: 8px;
  color: var(--text-2);
  border-radius: 10px;
  transition: .2s var(--ease);
}
.nav-link span { position: static; width: auto; height: auto; overflow: visible; clip-path: none; font-size: 12px; font-weight: 560; }
.nav-link:hover { color: var(--text); background: var(--surface-soft); }
.nav-link.active { color: var(--text); background: var(--surface); box-shadow: inset 0 0 0 1px var(--line); }
.nav-link svg { width: 16px; height: 16px; stroke-width: 1.7; }
.sidebar-footer { display: block; margin-top: auto; padding: 12px 8px 0; color: var(--text-3); font-size: 10px; border-top: 1px solid var(--line); }
.online { display: inline-flex; align-items: center; gap: 6px; }
.online::before { content: ""; width: 6px; height: 6px; border-radius: 50%; background: var(--success); }

.workspace { min-width: 0; flex: 1; display: flex; flex-direction: column; background: var(--surface); }
.repair-inspector { min-height: 0; flex: 1; display: grid; grid-template-rows: auto auto minmax(0, 1fr) auto; background: var(--surface); }
.repair-inspector[hidden] { display: none; }
.repair-inspector-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; padding: 24px 30px 17px; border-bottom: 1px solid var(--line); }
.repair-inspector-header h2 { margin: 0; font-size: 20px; letter-spacing: -.02em; }
.repair-inspector-header p { margin: 5px 0 0; color: var(--text-3); font-size: 12px; }
.repair-inspector-kicker { margin-bottom: 4px; color: var(--text-3); font-size: 10px; font-weight: 700; letter-spacing: .06em; }
.repair-inspector .repair-progress { padding: 0 30px; }
.repair-inspector .repair-stream { padding: 24px 30px; }
.repair-inspector .repair-controls { padding: 14px 30px 18px; }
.repair-inspector.repair-failed { background: color-mix(in srgb, var(--danger) 4%, var(--surface)); }
.repair-inspector.repair-failed .repair-progress { background: color-mix(in srgb, var(--danger) 7%, transparent); }
.repair-inspector.repair-failed .repair-progress span { color: var(--text-3); }
.repair-inspector.repair-failed .repair-progress span::after { background: transparent; }
.topbar {
  z-index: 5;
  min-height: 62px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 0 18px;
  background: color-mix(in srgb, var(--surface) 82%, transparent);
  backdrop-filter: blur(22px);
  border-bottom: 1px solid var(--line);
}
.topbar-title { min-width: 58px; display: flex; align-items: center; gap: 9px; font-size: 13px; font-weight: 620; }
.topbar-title span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.topbar-kicker, .topbar-status { display: none; }
.topbar-repo { min-width: 0; flex: 1; display: flex; align-items: center; justify-content: center; gap: 9px; }
.repo-picker-label { display: grid; flex: 0 0 auto; line-height: 1.15; cursor: pointer; }
.repo-picker-label strong { color: var(--text); font-size: 11px; font-weight: 680; }
.repo-picker-label small { margin-top: 3px; color: var(--text-3); font-size: 9px; }
.topbar-repo select {
  width: min(390px, 44vw);
  min-height: 38px;
  padding: 7px 32px 7px 11px;
  color: var(--text);
  background: var(--surface-solid);
  border: 1px solid var(--line-strong);
  border-radius: 9px;
  outline: 0;
  font-size: 13px;
  font-weight: 650;
  cursor: pointer;
}
.topbar-repo select:hover, .topbar-repo select:focus { border-color: color-mix(in srgb, var(--accent) 45%, var(--line-strong)); }
.repo-access-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--text-3); }
.repo-access-dot.owner { background: var(--success); }
.repo-access-dot.monitor { background: var(--warning); }
.mode-indicator { display: inline-flex; align-items: center; gap: 6px; padding: 5px 10px; border-radius: 999px; font-size: 10px; font-weight: 650; letter-spacing: .02em; cursor: help; white-space: nowrap; }
.mode-indicator[data-mode="anonymous"] { color: #b88a16; background: color-mix(in srgb, var(--warning) 12%, transparent); border: 1px solid color-mix(in srgb, var(--warning) 35%, transparent); }
.mode-indicator[data-mode="authenticated"] { color: var(--success); background: color-mix(in srgb, var(--success) 14%, transparent); border: 1px solid color-mix(in srgb, var(--success) 38%, transparent); }
.mode-indicator::before { content: ""; width: 6px; height: 6px; border-radius: 50%; background: currentColor; }

/* Coding Agent 顶部状态徽章 — 跟 mode-indicator 并列, 三种状态:
   unconfigured (灰) / configured (绿) / invalid (琥珀). */
.coding-agent-indicator { display: inline-flex; align-items: center; gap: 6px; padding: 5px 10px; border-radius: 999px; font: inherit; font-size: 10px; font-weight: 650; letter-spacing: .02em; cursor: pointer; white-space: nowrap; border: 1px solid var(--line); appearance: none; }
.coding-agent-indicator::before { content: ""; width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
.coding-agent-indicator[data-state="unconfigured"] { color: var(--text-3); background: var(--surface-soft); border-color: var(--line); font-weight: 500; }
.coding-agent-indicator[data-state="configured"] { color: var(--success); background: color-mix(in srgb, var(--success) 12%, transparent); border-color: color-mix(in srgb, var(--success) 35%, transparent); }
.coding-agent-indicator[data-state="invalid"] { color: var(--warning); background: color-mix(in srgb, var(--warning) 14%, transparent); border-color: color-mix(in srgb, var(--warning) 38%, transparent); }
.coding-agent-indicator[data-state="demo"] { color: var(--warning); background: color-mix(in srgb, var(--warning) 14%, transparent); border-color: color-mix(in srgb, var(--warning) 38%, transparent); }
.monitor-repo-button { min-height: 38px; padding: 6px 10px; color: var(--text-2); background: transparent; border: 1px solid var(--line); border-radius: 9px; cursor: pointer; font-size: 11px; white-space: nowrap; }
.monitor-repo-button:hover { color: var(--text); border-color: var(--line-strong); }

.workspace-scroll { min-height: 0; flex: 1; overflow: auto; scroll-behavior: smooth; }
.conversation, .content-page { width: min(840px, 100%); margin: 0 auto; padding: 42px 28px 148px; }
.conversation { min-height: 100%; }
.message { display: flex; align-items: flex-start; gap: 14px; margin-bottom: 28px; animation: message-in .35s var(--ease) both; }
.message.user { flex-direction: row-reverse; }
.avatar { width: 32px; height: 32px; border-radius: 10px; font-size: 11px; font-weight: 700; }
.avatar.user-avatar { color: var(--text); background: var(--surface-soft); border: 1px solid var(--line); }
.message-body { min-width: 0; max-width: calc(100% - 46px); }
.message-meta { display: flex; align-items: center; gap: 8px; margin: 1px 0 7px; color: var(--text-3); font-size: 11px; }
.message-meta strong { color: var(--text-2); font-size: 12px; }
.message.user .message-meta { justify-content: flex-end; }
.message-card {
  padding: 18px 20px;
  background: var(--surface-solid);
  border: 1px solid var(--line);
  border-radius: 6px 18px 18px 18px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, .025);
}
.message.user .message-card { padding: 11px 15px; background: var(--accent); color: var(--canvas); border: 0; border-radius: 18px 6px 18px 18px; }
.message-card h2 { margin: 2px 0 8px; font-size: clamp(20px, 3vw, 25px); line-height: 1.25; letter-spacing: -.025em; }
.message-card h3 { margin: 0 0 6px; font-size: 15px; }
.message-card p { margin: 0; color: var(--text-2); }
.message.user .message-card p { color: inherit; }
.message-card p + p { margin-top: 10px; }
.eyebrow { margin-bottom: 8px; color: var(--success); font-size: 11px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }

.signal-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-top: 16px; }
.signal {
  min-width: 0;
  padding: 11px 12px;
  background: var(--surface-soft);
  border: 1px solid var(--line);
  border-radius: 11px;
}
.signal strong { display: block; font-size: 17px; line-height: 1.2; }
.signal span { display: block; margin-top: 3px; overflow: hidden; color: var(--text-3); font-size: 10px; text-overflow: ellipsis; white-space: nowrap; text-transform: uppercase; letter-spacing: .04em; }
.assistant-note { display: flex; gap: 9px; margin-top: 14px; padding-top: 13px; color: var(--text-3); font-size: 12px; border-top: 1px solid var(--line); }
.assistant-note svg { width: 15px; height: 15px; flex: 0 0 auto; margin-top: 1px; }

.workbench-card { width: min(680px, 100%); }
.workbench-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
.workbench-heading .eyebrow { margin-bottom: 5px; }
.workbench-heading h3 { margin-bottom: 5px; }
.refresh-button { flex: 0 0 auto; font-size: 18px; }
.repo-permission { margin-top: 14px; padding: 8px 10px; color: var(--text-2); background: var(--surface-soft); border: 1px solid var(--line); border-radius: 9px; font-size: 11px; }
.repo-permission.owner { color: var(--success); }
.repo-permission.monitor { color: var(--warning); }
.metric-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 7px; margin-top: 9px; }
.repo-metric { min-width: 0; padding: 10px 11px; background: var(--surface-soft); border: 1px solid var(--line); border-radius: 10px; }
.repo-metric span { display: block; color: var(--text-3); font-size: 9px; font-weight: 680; letter-spacing: .04em; text-transform: uppercase; }
.repo-metric strong { display: block; margin-top: 3px; font-size: 18px; line-height: 1.2; }
.repo-metric small { display: block; margin-top: 3px; color: var(--text-3); font-size: 9px; }
.repo-metric small.positive { color: var(--success); }
.repo-metric small.negative { color: var(--danger); }
.trend-panel { margin-top: 8px; padding: 11px 12px 8px; background: var(--surface-soft); border: 1px solid var(--line); border-radius: 10px; }
.trend-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 10px; }
.trend-header strong { display: block; font-size: 11px; }
.trend-header span { color: var(--text-3); font-size: 9px; }
.trend-legend { display: flex; gap: 9px; }
.trend-legend span::before { content: ""; display: inline-block; width: 12px; height: 2px; margin: 0 4px 3px 0; background: var(--accent); }
.trend-legend span:last-child::before { background: var(--warning); }
.repo-trend-chart { display: block; width: 100%; height: 92px; margin-top: 5px; overflow: visible; }
.repo-trend-chart .grid-line { stroke: var(--line); stroke-width: 1; }
.repo-trend-chart .star-line { fill: none; stroke: var(--accent); stroke-width: 2.3; vector-effect: non-scaling-stroke; }
.repo-trend-chart .issue-line { fill: none; stroke: var(--warning); stroke-width: 2; stroke-dasharray: 4 3; vector-effect: non-scaling-stroke; }
.repo-trend-chart text { fill: var(--text-3); font: 9px -apple-system, sans-serif; }
.repo-control {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  margin-top: 16px;
  padding: 9px 11px;
  background: var(--surface-soft);
  border: 1px solid var(--line);
  border-radius: 11px;
}
.repo-control label { color: var(--text-3); font-size: 10px; font-weight: 680; letter-spacing: .04em; text-transform: uppercase; }
.repo-control select {
  min-width: 0;
  width: 100%;
  padding: 3px 26px 3px 5px;
  overflow: hidden;
  color: var(--text);
  background: transparent;
  border: 0;
  outline: 0;
  font-size: 13px;
  font-weight: 650;
  text-overflow: ellipsis;
}
.repo-viewer { padding: 0; color: var(--text-3); background: transparent; border: 0; cursor: pointer; font-size: 10px; white-space: nowrap; }
.repo-viewer:hover { color: var(--text); }
.issue-summary { display: flex; gap: 16px; padding: 12px 2px 8px; color: var(--text-3); font-size: 11px; }
.issue-summary strong { color: var(--text); font-size: 13px; }
.issue-inbox { display: grid; gap: 7px; max-height: 390px; overflow: auto; padding: 2px; }
.issue-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 9px 12px;
  padding: 12px 12px 11px;
  background: var(--surface-soft);
  border: 1px solid var(--line);
  border-radius: 11px;
  transition: border-color .2s var(--ease), transform .2s var(--ease);
}
.issue-row:hover { border-color: var(--line-strong); transform: translateY(-1px); }
.issue-main { min-width: 0; }
.issue-title { display: block; overflow: hidden; color: var(--text); font-size: 12px; font-weight: 650; text-overflow: ellipsis; white-space: nowrap; }
.issue-title:hover { color: var(--accent); }
.issue-number { margin-right: 6px; color: var(--text-3); font-weight: 580; }
.issue-meta { display: flex; flex-wrap: wrap; gap: 5px 9px; margin-top: 6px; color: var(--text-3); font-size: 10px; }
.issue-label { max-width: 118px; padding: 1px 6px; overflow: hidden; background: var(--surface-solid); border: 1px solid var(--line); border-radius: 99px; text-overflow: ellipsis; white-space: nowrap; }
.issue-attention { color: var(--warning); font-weight: 650; }
.issue-command {
  align-self: center;
  min-height: 32px;
  padding: 6px 9px;
  color: var(--text-2);
  background: var(--surface-solid);
  border: 1px solid var(--line);
  border-radius: 8px;
  cursor: pointer;
  font-size: 11px;
  font-weight: 640;
}
.issue-command:hover { color: var(--text); border-color: var(--line-strong); }
.issue-command:disabled { cursor: not-allowed; opacity: .48; }
.issue-command:disabled:hover { color: var(--text-2); border-color: var(--line); }
.issue-commands { display: flex; flex-direction: column; align-items: flex-end; gap: 4px; }
.issue-command { display: inline-flex; flex-direction: column; align-items: center; gap: 2px; line-height: 1.3; }
.issue-command-sub { color: var(--text-3); font-size: 9.5px; font-weight: 500; }
.issue-loading { display: grid; gap: 7px; padding-top: 3px; }
.issue-loading span { height: 60px; background: var(--surface-soft); border: 1px solid var(--line); border-radius: 11px; animation: loading 1.2s ease-in-out infinite alternate; }
.issue-empty, .issue-error { padding: 30px 18px; color: var(--text-2); background: var(--surface-soft); border: 1px dashed var(--line-strong); border-radius: 11px; text-align: center; }
.issue-error strong, .issue-empty strong { display: block; margin-bottom: 5px; color: var(--text); }
.task-file { display: block; margin-top: 8px; padding: 9px 11px; overflow-wrap: anywhere; color: var(--text-2); background: var(--surface-soft); border: 1px solid var(--line); border-radius: 9px; font: 11px/1.5 "SF Mono", ui-monospace, monospace; }

/* The home screen is a single daily readout. Conversation chrome only appears
   after the user gives the assistant a command. */
.today-view { padding-top: 30px; }
.today-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 20px; }
.today-copy { min-width: 0; }
.today-kicker { margin-bottom: 5px; color: var(--success); font-size: 11px; font-weight: 700; letter-spacing: .08em; }
.today-header h1 { margin: 0; font-size: clamp(25px, 4vw, 34px); line-height: 1.18; letter-spacing: -.035em; }
.today-header p { margin: 8px 0 0; color: var(--text-2); }
.today-view .refresh-button { margin-top: 2px; border: 1px solid var(--line); cursor: pointer; }
.today-view .repo-permission {
  display: inline-flex;
  margin-top: 13px;
  padding: 4px 9px;
  border: 0;
  border-radius: 99px;
  font-size: 10px;
}
.today-view .repo-permission.owner { background: color-mix(in srgb, var(--success) 10%, transparent); }
.today-view .repo-permission.monitor { background: color-mix(in srgb, var(--warning) 11%, transparent); }
.today-view .metric-grid {
  margin-top: 16px;
  gap: 0;
  background: transparent;
  border-top: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
}
.today-view .repo-metric { padding: 12px 16px; background: transparent; border: 0; border-radius: 0; }
.today-view .repo-metric + .repo-metric { border-left: 1px solid var(--line); }
.today-view .repo-metric strong { margin-top: 2px; font-size: 21px; }
.today-view .trend-panel { margin-top: 18px; padding: 0; background: transparent; border: 0; border-radius: 0; }
.today-view .repo-trend-chart { height: 58px; margin-top: 2px; }
.issues-section { margin-top: 18px; border-top: 1px solid var(--line); }
.issues-heading { display: flex; align-items: center; justify-content: space-between; gap: 18px; padding: 15px 0 7px; }
.issues-heading h2 { margin: 0; font-size: 16px; letter-spacing: -.01em; }
.today-view .issue-summary { padding: 0; justify-content: flex-end; }
.today-view .issue-inbox { display: block; max-height: none; padding: 0; overflow: visible; }

/* === 空状态 / 失败回滚 / owner-monitor 区分 === */
.today-view #active-repo-heading.heading-idle { color: var(--text-2); font-weight: 500; }
.today-view #active-repo-heading.heading-failed { color: var(--warning); }
.repo-load-row { margin-top: 8px; display: flex; gap: 8px; }
.repo-load-row #load-issues-button[hidden] { display: none; }
.error-actions { margin-top: 12px; display: flex; gap: 8px; justify-content: center; flex-wrap: wrap; }
.repo-permission[hidden] { display: none; }
.repo-permission { font-size: 12px; padding: 6px 10px; border-radius: 7px; }
.today-view .issue-row {
  padding: 13px 0;
  background: transparent;
  border: 0;
  border-top: 1px solid var(--line);
  border-radius: 0;
}
.today-view .issue-row:hover { transform: none; border-color: var(--line-strong); }
.today-view .issue-command { background: transparent; }
.today-view .issue-loading { gap: 0; }
.today-view .issue-loading span { height: 66px; background: transparent; border: 0; border-top: 1px solid var(--line); border-radius: 0; }
#conversation-stream:not(:empty) { margin-top: 34px; padding-top: 26px; border-top: 1px solid var(--line); }
.repository-onboarding {
  min-height: min(520px, calc(100dvh - 190px));
  display: grid;
  place-content: center;
  justify-items: center;
  padding: 34px 20px;
  text-align: center;
}
.repository-onboarding[hidden] { display: none; }
.onboarding-icon { display: grid; place-items: center; width: 64px; height: 64px; margin-bottom: 20px; color: var(--text-3); background: var(--surface-soft); border: 1px solid var(--line); border-radius: 20px; }
.onboarding-icon svg { width: 40px; height: 40px; }
.repository-onboarding h1 { margin: 0; font-size: 28px; font-weight: 600; letter-spacing: -.03em; }
.repository-onboarding p { max-width: 480px; margin: 12px 0 0; color: var(--text-2); line-height: 1.65; }
.onboarding-steps { display: grid; gap: 12px; margin: 28px 0; padding: 20px; background: var(--surface-soft); border: 1px solid var(--line); border-radius: 12px; text-align: left; }
.onboarding-step { display: flex; align-items: center; gap: 12px; }
.step-number { display: grid; place-items: center; width: 28px; height: 28px; flex: 0 0 28px; color: var(--accent); background: var(--accent-soft); border-radius: 50%; font-size: 13px; font-weight: 600; }
.step-number.complete { color: var(--success); background: color-mix(in srgb, var(--success) 14%, transparent); }
.step-text { color: var(--text-2); font-size: 14px; }
.onboarding-actions { display: flex; gap: 10px; margin-top: 24px; }
.onboarding-hint { margin-top: 16px; padding: 10px 16px; color: var(--text-2); background: var(--accent-soft); border-radius: 8px; font-size: 13px; line-height: 1.5; }
.today-view.no-repositories > :not(.repository-onboarding) { display: none; }
.no-repositories .composer-wrap { display: none; }

.suggestions { display: flex; gap: 8px; margin-top: 14px; overflow-x: auto; scrollbar-width: none; }
.suggestions::-webkit-scrollbar { display: none; }
.suggestion, .soft-button, .primary-button, .icon-button {
  border: 0;
  cursor: pointer;
  transition: transform .18s var(--ease), background .18s var(--ease), border-color .18s var(--ease);
}
.suggestion {
  flex: 0 0 auto;
  min-height: 38px;
  padding: 8px 12px;
  color: var(--text-2);
  background: var(--surface-soft);
  border: 1px solid var(--line);
  border-radius: 10px;
  font-size: 12px;
  font-weight: 570;
}
.primary-suggestion { color: var(--surface-solid); background: var(--accent); border-color: transparent; }
.primary-suggestion:hover { color: var(--surface-solid); background: color-mix(in srgb, var(--accent) 90%, var(--text)); }
.suggestion:hover, .soft-button:hover { color: var(--text); border-color: var(--line-strong); transform: translateY(-1px); }
.primary-suggestion:hover { color: var(--surface-solid); border-color: transparent; }
.suggestion:active, .soft-button:active, .primary-button:active, .icon-button:active { transform: scale(.97); }

.inline-brief {
  display: grid;
  gap: 7px;
  margin-top: 14px;
  padding: 14px;
  background: var(--surface-soft);
  border: 1px solid var(--line);
  border-radius: 12px;
}
.brief-line { color: var(--text-2); font-size: 12px; overflow-wrap: anywhere; }
.brief-line.heading { color: var(--text); font-size: 13px; font-weight: 680; }
.brief-line.bullet { position: relative; padding-left: 13px; }
.brief-line.bullet::before { content: ""; position: absolute; left: 1px; top: .72em; width: 4px; height: 4px; border-radius: 50%; background: var(--accent); }
.decision-summary { display: grid; gap: 8px; margin-top: 13px; padding: 13px 14px; background: var(--surface-soft); border: 1px solid var(--line); border-radius: 12px; }
.decision-summary-row { display: grid; grid-template-columns: 58px 1fr; gap: 9px; color: var(--text-2); font-size: 12px; }
.decision-summary-row span:first-child { color: var(--text-3); }
.status-dot { display: inline-block; width: 7px; height: 7px; margin-right: 7px; border-radius: 50%; background: var(--warning); }
.status-dot.accepted { background: var(--success); }
.status-dot.rejected { background: var(--danger); }
.status-dot.deferred { background: var(--warning); }

.composer-wrap {
  position: fixed;
  z-index: 8;
  left: var(--sidebar-width);
  right: 0;
  bottom: 0;
  padding: 9px max(24px, calc((100vw - var(--sidebar-width) - 840px) / 2 + 28px)) 10px;
  background: transparent;
  pointer-events: none;
}
.composer {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  min-height: 58px;
  padding: 9px 9px 9px 16px;
  background: color-mix(in srgb, var(--surface-solid) 90%, transparent);
  backdrop-filter: blur(24px);
  border: 1px solid var(--line-strong);
  border-radius: 18px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, .07);
  pointer-events: auto;
}
.composer textarea {
  min-height: 38px;
  max-height: 126px;
  flex: 1;
  resize: none;
  padding: 9px 0;
  color: var(--text);
  background: transparent;
  border: 0;
  outline: 0;
  font-size: 14px;
  line-height: 20px;
}
.composer textarea::placeholder { color: var(--text-3); }
.send-button {
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  color: var(--canvas);
  background: var(--accent);
  border: 0;
  border-radius: 12px;
  cursor: pointer;
}
.send-button svg { width: 17px; height: 17px; }
.composer-hint { display: none; }

.content-page { padding-bottom: 70px; }
.page-heading { margin-bottom: 26px; }
.page-heading .eyebrow { margin-bottom: 6px; }
.page-heading h2 { margin: 0; font-size: clamp(24px, 4vw, 32px); line-height: 1.2; letter-spacing: -.035em; }
.page-heading p { max-width: 560px; margin: 8px 0 0; color: var(--text-2); }
.brief-generation-controls { display: grid; grid-template-columns: auto minmax(180px, 1fr) auto; align-items: center; gap: 9px; max-width: 680px; margin-top: 18px; }
.brief-generation-controls label { color: var(--text-2); font-size: 11px; font-weight: 650; }
.brief-generation-controls select { min-width: 0; }
.brief-generation-controls .primary-button { min-height: 38px; }
.brief-generation-controls [role="status"] { grid-column: 2 / -1; min-height: 17px; color: var(--text-2); font-size: 11px; }
.page-actions { display: flex; gap: 8px; margin-top: 16px; }
.soft-button, .primary-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 40px;
  padding: 8px 13px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 620;
}
.soft-button { color: var(--text-2); background: var(--surface-soft); border: 1px solid var(--line); }
.primary-button { color: var(--canvas); background: var(--accent); }
.card-list { display: grid; gap: 10px; }
.brief-card, .decision-card, .empty-state {
  padding: 17px 18px;
  background: var(--surface-solid);
  border: 1px solid var(--line);
  border-radius: 14px;
}
.brief-card { display: flex; align-items: center; justify-content: space-between; gap: 18px; transition: .2s var(--ease); }
.brief-card:hover { border-color: var(--line-strong); transform: translateY(-1px); }
.brief-card-main { min-width: 0; }
.brief-card-name { overflow-wrap: anywhere; color: var(--text); font-weight: 620; }
.brief-card-meta { margin-top: 4px; color: var(--text-3); font-size: 11px; }
.brief-card-arrow { flex: 0 0 auto; color: var(--text-3); font-size: 18px; }
.decision-card { display: grid; grid-template-columns: auto 1fr; gap: 12px 16px; }
.decision-meta { color: var(--text-3); font-size: 11px; }
.decision-reason { grid-column: 2; color: var(--text-2); }
.badge { align-self: start; padding: 3px 8px; border-radius: 99px; font-size: 10px; font-weight: 700; letter-spacing: .04em; text-transform: uppercase; }
.badge-rejected { color: var(--danger); background: color-mix(in srgb, var(--danger) 12%, transparent); }
.badge-deferred { color: var(--warning); background: color-mix(in srgb, var(--warning) 13%, transparent); }
.badge-accepted { color: var(--success); background: color-mix(in srgb, var(--success) 12%, transparent); }
.empty-state { padding: 42px 22px; color: var(--text-2); text-align: center; border-style: dashed; }

.brief-meta { margin-bottom: 20px; color: var(--text-3); font-size: 11px; }
.brief-body { padding: 24px clamp(18px, 4vw, 34px); background: var(--surface-solid); border: 1px solid var(--line); border-radius: 16px; }
.brief-body h1 { margin: 0 0 20px; font-size: clamp(24px, 4vw, 32px); letter-spacing: -.035em; }
.brief-body h2 { margin: 28px 0 10px; padding-top: 22px; font-size: 18px; border-top: 1px solid var(--line); }
.brief-body h3 { margin: 20px 0 7px; font-size: 15px; }
.brief-body p { margin: 8px 0; color: var(--text-2); overflow-wrap: anywhere; }
.brief-body ul { padding-left: 20px; color: var(--text-2); }
.brief-body li { margin: 5px 0; }
code, pre { font-family: "SF Mono", "JetBrains Mono", ui-monospace, monospace; }
code { padding: 2px 5px; background: var(--surface-soft); border: 1px solid var(--line); border-radius: 5px; font-size: .88em; }
pre { padding: 13px 15px; overflow-x: auto; background: var(--surface-soft); border: 1px solid var(--line); border-radius: 10px; font-size: 12px; }

.dialog { width: min(520px, calc(100% - 28px)); padding: 0; color: var(--text); background: var(--surface-solid); border: 1px solid var(--line-strong); border-radius: 18px; box-shadow: 0 24px 80px rgba(0,0,0,.24); }
.dialog::backdrop { background: rgba(0,0,0,.44); backdrop-filter: blur(5px); }
.dialog-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 14px; padding: 20px 20px 15px; border-bottom: 1px solid var(--line); }
.dialog-header h2 { margin: 0; font-size: 18px; }
.dialog-header p { margin: 4px 0 0; color: var(--text-3); font-size: 12px; }
.icon-button { width: 34px; height: 34px; color: var(--text-2); background: var(--surface-soft); border-radius: 9px; }
.decision-form { display: grid; gap: 15px; padding: 18px 20px 20px; }
.picker-divider { position: relative; height: 1px; margin: 0 20px; background: var(--line); text-align: center; }
.picker-divider span { position: relative; top: -9px; padding: 0 9px; color: var(--text-3); background: var(--surface-solid); font-size: 10px; }
.owned-picker { padding: 19px 20px 20px; }
.owned-picker-trigger { width: 100%; }
.owned-picker-panel { display: grid; gap: 10px; margin-top: 13px; }
.owned-picker-panel[hidden] { display: none; }
.owned-repo-list { max-height: 260px; overflow: auto; border-top: 1px solid var(--line); }
.owned-repo-row { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: center; gap: 12px; min-height: 50px; padding: 8px 1px; border-bottom: 1px solid var(--line); }
.owned-repo-copy { min-width: 0; }
.owned-repo-name { overflow: hidden; color: var(--text); font-size: 12px; font-weight: 650; text-overflow: ellipsis; white-space: nowrap; }
.owned-repo-meta { margin-top: 2px; color: var(--text-3); font-size: 10px; }
.owned-repo-add { min-width: 56px; min-height: 30px; padding: 5px 9px; color: var(--text-2); background: transparent; border: 1px solid var(--line); border-radius: 8px; cursor: pointer; font-size: 10px; }
.owned-repo-add:hover { color: var(--text); border-color: var(--line-strong); }
.owned-repo-add:disabled { cursor: default; opacity: .55; }
.github-setup { display: grid; gap: 12px; padding: 18px 20px 20px; }
.github-setup-card { padding: 13px 14px; color: var(--text-2); background: var(--surface-soft); border: 1px solid var(--line); border-radius: 11px; font-size: 12px; line-height: 1.6; }
.github-setup-card strong { display: block; margin-bottom: 3px; color: var(--text); font-size: 13px; }
.github-setup-card code { display: block; margin-top: 9px; padding: 9px 10px; overflow-x: auto; color: var(--text); background: var(--surface-solid); white-space: nowrap; }
.github-setup-actions { display: flex; flex-wrap: wrap; gap: 8px; }
.github-setup-note { margin: 0; color: var(--text-3); font-size: 11px; line-height: 1.55; }
.repair-setup-status { display: grid; gap: 3px; padding: 12px 14px; border: 1px solid var(--line); border-radius: 11px; }
.repair-setup-status strong { font-size: 13px; }
.repair-setup-status span { color: var(--text-2); font-size: 11px; line-height: 1.5; }
.repair-setup-status.blocked { background: color-mix(in srgb, var(--danger) 8%, var(--surface-solid)); border-color: color-mix(in srgb, var(--danger) 28%, var(--line)); }
.repair-setup-status.blocked strong { color: var(--danger); }
.repair-setup-status.optional { background: var(--surface-soft); border-color: var(--line); }
.repair-setup-status.optional strong { color: var(--text); }
.repair-setup-status.ready { background: color-mix(in srgb, var(--success) 8%, var(--surface-solid)); border-color: color-mix(in srgb, var(--success) 28%, var(--line)); }
.repair-setup-status.ready strong { color: var(--success); }
.repair-setup-status.pending { background: color-mix(in srgb, var(--warning) 8%, var(--surface-solid)); border-color: color-mix(in srgb, var(--warning) 28%, var(--line)); }
.repair-setup-status.pending strong { color: var(--warning); }

/* Coding Agent 配置对话框: 5 步 stepper, field-hint 灰色小提示, 失败卡 tone-amber/tone-soft. */
.coding-agent-setup { display: grid; gap: 14px; padding: 16px 20px 20px; }
.coding-agent-stepper { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.coding-agent-stepper .coding-agent-step-dot { width: 12px; height: 12px; border-radius: 50%; background: var(--surface-soft); border: 1px solid var(--line); }
.coding-agent-stepper .coding-agent-step-dot.active { background: var(--accent); border-color: var(--accent); }
.coding-agent-stepper .coding-agent-step-dot.complete { background: color-mix(in srgb, var(--success) 60%, transparent); border-color: color-mix(in srgb, var(--success) 70%, transparent); }
.coding-agent-stepper .coding-agent-step-label { margin-left: 4px; color: var(--text-2); font-size: 12px; }
.field-hint { color: var(--text-3); font-size: 11px; line-height: 1.5; }
.field-hint code { font-size: 10px; padding: 1px 4px; color: var(--text-2); background: var(--surface-soft); border-radius: 3px; }
.coding-agent-test-col { display: flex; align-items: end; }
.coding-agent-test-col button { width: 100%; }

/* 失败卡片: 按 error_kind 分色. danger 红 / warning 琥珀 / amber 浅琥珀 (临时问题) /
   neutral 灰 (需要看细节) / success 绿 (重试即可). */
.repair-error-card { display: grid; gap: 6px; padding: 14px 16px; border: 1px solid var(--line); border-radius: 12px; margin-top: 12px; }
.repair-error-card strong { font-size: 13px; line-height: 1.4; }
.repair-error-card span { color: var(--text-2); font-size: 12px; line-height: 1.55; }
.repair-error-card small { color: var(--text-3); font-size: 11px; line-height: 1.5; }
.repair-error-card.tone-danger { background: color-mix(in srgb, var(--danger) 8%, var(--surface-solid)); border-color: color-mix(in srgb, var(--danger) 32%, var(--line)); }
.repair-error-card.tone-danger strong { color: var(--danger); }
.repair-error-card.tone-warning { background: color-mix(in srgb, var(--warning) 9%, var(--surface-solid)); border-color: color-mix(in srgb, var(--warning) 30%, var(--line)); }
.repair-error-card.tone-warning strong { color: var(--warning); }
.repair-error-card.tone-amber { background: color-mix(in srgb, var(--warning) 5%, var(--surface-solid)); border-color: color-mix(in srgb, var(--warning) 20%, var(--line)); }
.repair-error-card.tone-amber strong { color: color-mix(in srgb, var(--warning) 80%, var(--text)); }
.repair-error-card.tone-neutral { background: var(--surface-soft); border-color: var(--line); }
.repair-error-card.tone-neutral strong { color: var(--text-2); }
.connection-steps { display: grid; gap: 10px; margin: 0; padding: 0; list-style: none; counter-reset: connection-step; }
.connection-steps[hidden], .github-setup-actions button[hidden] { display: none; }
.connection-steps li { display: grid; grid-template-columns: 24px minmax(0, 1fr); align-items: center; gap: 9px; color: var(--text-2); font-size: 12px; counter-increment: connection-step; }
.connection-steps li::before { content: counter(connection-step); display: grid; place-items: center; width: 24px; height: 24px; color: var(--text); background: var(--surface-soft); border: 1px solid var(--line); border-radius: 50%; font-size: 10px; font-weight: 700; }
.connection-help { border-top: 1px solid var(--line); }
.connection-help summary { padding: 12px 1px 0; color: var(--text-3); cursor: pointer; font-size: 11px; }
.connection-help[open] summary { color: var(--text-2); }
.connection-help-body { margin-top: 10px; padding: 11px 12px; color: var(--text-2); background: var(--surface-soft); border-radius: 9px; font-size: 11px; line-height: 1.55; }
.connection-help-body code { display: block; margin: 8px 0; padding: 8px 9px; overflow-x: auto; color: var(--text); background: var(--surface-solid); border: 1px solid var(--line); border-radius: 7px; white-space: nowrap; }
.repair-kicker { margin-bottom: 3px; color: var(--text-3); font-size: 10px; font-weight: 650; letter-spacing: .04em; }
.repair-progress { display: grid; grid-template-columns: repeat(5, 1fr); gap: 1px; padding: 0 20px; border-bottom: 1px solid var(--line); }
.repair-progress span { position: relative; padding: 10px 4px 11px; color: var(--text-3); font-size: 10px; text-align: center; }
.repair-progress span::after { content: ""; position: absolute; left: 0; right: 0; bottom: -1px; height: 2px; background: transparent; }
.repair-progress span.active { color: var(--text); font-weight: 650; }
.repair-progress span.active::after { background: var(--accent); }
.repair-progress span.complete { color: var(--success); }
.repair-progress span[data-verification-state="failed"],
.repair-progress span[data-verification-state="unverified"] { color: var(--warning); }
.repair-progress span[data-verification-state="failed"]::after,
.repair-progress span[data-verification-state="unverified"]::after { background: var(--warning); }
.repair-stream { min-height: 0; overflow: auto; padding: 20px; background: color-mix(in srgb, var(--surface-soft) 40%, transparent); }
.repair-event { display: grid; grid-template-columns: 28px minmax(0, 1fr); gap: 10px; margin-bottom: 16px; }
.repair-event.user { grid-template-columns: minmax(0, 1fr) 28px; }
.repair-event-avatar { display: grid; place-items: center; width: 28px; height: 28px; color: var(--surface-solid); background: var(--accent); border-radius: 9px; font-size: 9px; font-weight: 700; }
.repair-event.user .repair-event-avatar { grid-column: 2; color: var(--text); background: var(--surface-solid); border: 1px solid var(--line); }
.repair-event-body { min-width: 0; }
.repair-event.user .repair-event-body { grid-row: 1; text-align: right; }
.repair-event-meta { margin-bottom: 4px; color: var(--text-3); font-size: 9px; }
.repair-event-card { display: inline-block; max-width: 100%; padding: 11px 13px; color: var(--text-2); background: var(--surface-solid); border: 1px solid var(--line); border-radius: 5px 13px 13px; text-align: left; overflow-wrap: anywhere; }
.repair-event-card.tone-error { color: var(--text); background: color-mix(in srgb, var(--danger) 9%, var(--surface-solid)); border-color: color-mix(in srgb, var(--danger) 32%, var(--line)); }
.repair-event-card.tone-error strong { color: var(--danger); }
.repair-safety-note { margin-top: 10px; padding: 9px 11px; border: 1px solid color-mix(in srgb, var(--warning) 42%, var(--line)); border-radius: 8px; background: color-mix(in srgb, var(--warning) 10%, var(--surface-solid)); color: var(--text-2); }
.repair-safety-note strong { display: block; color: var(--warning); margin-bottom: 2px; }
.repair-verification { margin-top: 10px; padding: 9px 11px; border: 1px solid var(--line); border-radius: 8px; background: var(--surface-soft); }
.repair-verification strong { display: block; margin-bottom: 2px; }
.repair-verification[data-status="passed"] strong { color: var(--success); }
.repair-verification[data-status="failed"] strong { color: var(--danger); }
.repair-verification[data-status="unverified"] strong { color: var(--warning); }
.diff-view-verification { padding: 0 15px 12px; }
.diff-view-verification:empty { display: none; }
.diff-view-verification .repair-verification { margin-top: 0; }
.verification-recovery { margin-top: 8px; color: var(--text-2); font-size: 12px; line-height: 1.5; }
.verification-recovery .suggestions { margin-top: 8px; }
.verification-log { margin-top: 8px; }
.verification-log summary { color: var(--text-2); cursor: pointer; font-weight: 650; }
.verification-log pre { max-height: 180px; margin: 8px 0 0; padding: 10px; overflow: auto; border-radius: 7px; background: var(--surface); color: var(--text-2); font: 11px/1.45 var(--mono); white-space: pre-wrap; }
.repair-error-detail { margin-top: 8px; color: var(--text-2); font-size: 11px; line-height: 1.55; }
.repair-error-card { display: grid; gap: 4px; margin-top: 10px; padding: 12px 14px; border-radius: 9px; }
.repair-error-card strong { font-size: 13px; }
.repair-error-card span { color: var(--text-2); font-size: 11.5px; }
.repair-error-card small { color: var(--text-3); font-size: 11px; line-height: 1.5; }
.repair-error-card .suggestions { margin-top: 8px; }
.repair-error-card.tone-warning { background: color-mix(in srgb, var(--warning) 8%, var(--surface-solid)); border: 1px solid color-mix(in srgb, var(--warning) 30%, var(--line)); }
.repair-error-card.tone-warning strong { color: var(--warning); }
.repair-error-card.tone-danger { background: color-mix(in srgb, var(--danger) 8%, var(--surface-solid)); border: 1px solid color-mix(in srgb, var(--danger) 32%, var(--line)); }
.repair-error-card.tone-danger strong { color: var(--danger); }
.repair-error-card.tone-neutral { background: var(--surface-soft); border: 1px solid var(--line); }
.repair-error-card.tone-neutral strong { color: var(--text); }
.repair-log { margin-top: 8px; padding: 10px 12px; background: var(--surface-solid); border: 1px solid var(--line); border-radius: 7px; max-height: 240px; overflow: auto; }
.repair-log pre { margin: 0; padding: 0; color: var(--text-2); font: 10.5px/1.5 "SF Mono", ui-monospace, monospace; white-space: pre-wrap; word-break: break-all; }
.soft-suggestion { color: var(--text-2); background: var(--surface-soft); border: 1px solid var(--line); border-radius: 7px; padding: 6px 10px; cursor: pointer; font-size: 11px; font-weight: 600; }
.soft-suggestion:hover { color: var(--text); border-color: var(--line-strong); }
.repair-event.user .repair-event-card { color: var(--surface-solid); background: var(--accent); border: 0; border-radius: 13px 5px 13px 13px; }
.repair-event-card strong { color: var(--text); }
.repair-event.user .repair-event-card strong { color: inherit; }
.repair-live-progress { margin-top: 13px; padding-top: 12px; border-top: 1px solid var(--line); }
.repair-live-progress-heading { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 9px; }
.repair-live-progress-heading strong { font-size: 12px; }
.repair-live-progress-heading span { color: var(--text-3); font-size: 10px; }
.repair-progress-list { display: grid; gap: 0; }
.repair-progress-item { position: relative; display: grid; grid-template-columns: 12px minmax(0, 1fr) auto; gap: 9px; align-items: start; min-height: 38px; padding-bottom: 9px; }
.repair-progress-item:last-child { min-height: 0; padding-bottom: 0; }
.repair-progress-item:not(:last-child)::before { content: ""; position: absolute; top: 12px; bottom: 0; left: 4px; width: 1px; background: var(--line); }
.repair-progress-dot { position: relative; z-index: 1; width: 9px; height: 9px; margin-top: 3px; border: 2px solid var(--surface-solid); border-radius: 50%; background: var(--text-3); box-shadow: 0 0 0 1px var(--line-strong); }
.repair-progress-item.done .repair-progress-dot { background: var(--success); }
.repair-progress-item.current .repair-progress-dot { background: var(--warning); box-shadow: 0 0 0 3px color-mix(in srgb, var(--warning) 16%, transparent); animation: repair-progress-pulse 1.5s ease-in-out infinite; }
.repair-progress-item.failed .repair-progress-dot { background: var(--danger); }
.repair-progress-copy { min-width: 0; }
.repair-progress-copy strong { display: block; font-size: 11.5px; line-height: 1.35; }
.repair-progress-copy span { display: block; margin-top: 2px; color: var(--text-3); font-size: 10.5px; line-height: 1.45; }
.repair-progress-time { color: var(--text-3); font-size: 9.5px; white-space: nowrap; }
@keyframes repair-progress-pulse { 50% { opacity: .45; transform: scale(.82); } }
.repair-output { margin-top: 9px; padding: 9px 10px; color: var(--text-2); background: var(--surface-soft); border: 1px solid var(--line); border-radius: 8px; font: 10px/1.5 "SF Mono", ui-monospace, monospace; white-space: pre-wrap; }
.repair-controls { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: end; gap: 10px; padding: 14px 18px 18px; border-top: 1px solid var(--line); background: var(--surface-solid); }
.repair-controls textarea { width: 100%; min-height: 52px; max-height: 110px; resize: none; padding: 10px 11px; color: var(--text); background: var(--surface-soft); border: 1px solid var(--line); border-radius: 10px; outline: 0; }
.repair-controls textarea:focus { border-color: var(--line-strong); }
.repair-controls textarea:disabled { opacity: .55; }
.repair-actions { display: flex; justify-content: flex-end; gap: 8px; }
.repair-actions .primary-button:disabled, .repair-actions .soft-button:disabled { cursor: not-allowed; opacity: .45; }
/* diff view (CodeMirror 6) — sits inside the repair inspector and
   replaces the regular repair stream when the job is in review_ready. */
.repair-inspector-header-actions { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 8px; align-items: center; }
.diff-view { display: grid; grid-template-rows: auto minmax(0, auto) minmax(180px, 1fr) auto; min-height: 0; overflow: hidden; flex: 1; border-top: 1px solid var(--line); background: var(--surface-solid); }
.diff-view[hidden] { display: none; }
.diff-view-meta { display: flex; align-items: center; gap: 14px; padding: 12px 18px; border-bottom: 1px solid var(--line); font-size: 11px; color: var(--text-2); flex-wrap: wrap; }
.diff-view-meta strong { color: var(--text); font-size: 12px; font-weight: 650; }
.diff-view-stats { color: var(--text-3); font-family: "SF Mono", ui-monospace, monospace; font-size: 10.5px; }
.diff-view-stats .add { color: var(--success); }
.diff-view-stats .rem { color: var(--danger); }
.diff-view-overview { max-height: 156px; overflow: auto; border-bottom: 1px solid var(--line); }
.diff-view-summary { margin: 0; padding: 12px 18px 5px; color: var(--text); font-size: 12px; line-height: 1.55; white-space: pre-wrap; }
.diff-view-upgrade { margin-left: auto; padding: 4px 10px; color: var(--success); background: color-mix(in srgb, var(--success) 14%, transparent); border-radius: 999px; font-size: 10.5px; }
.diff-view-body { display: grid; grid-template-rows: auto minmax(0, 1fr); min-height: 180px; overflow: hidden; }
.diff-view-code-heading { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 9px 18px; border-bottom: 1px solid var(--line); background: var(--surface-soft); }
.diff-view-code-heading strong { font-size: 12px; }
.diff-view-code-heading span { color: var(--text-3); font-size: 10.5px; }
.diff-view-editor { min-width: 0; overflow: auto; }
.diff-view-fallback-note { padding: 9px 14px; color: var(--warning); background: color-mix(in srgb, var(--warning) 9%, var(--surface)); border-bottom: 1px solid var(--line); font-size: 11px; }
.diff-view-plain { min-width: 100%; width: max-content; min-height: calc(100% - 38px); margin: 0; padding: 14px 18px; color: var(--text-2); background: var(--surface-solid); font: 12px/1.55 "SF Mono", ui-monospace, monospace; white-space: pre; tab-size: 4; }
.diff-view-editor .cm-editor { height: 100%; background: var(--surface-solid); font-family: "SF Mono", ui-monospace, monospace; font-size: 12px; }
.diff-view-editor .cm-scroller { font-family: "SF Mono", ui-monospace, monospace; line-height: 1.55; }
.diff-view-editor .cm-gutters { background: var(--surface-solid); border-right: 1px solid var(--line); color: var(--text-3); }
.diff-view-editor .cm-content { padding: 12px 0; }
.diff-view-editor .cm-line.diff-add { background: color-mix(in srgb, var(--success) 10%, transparent); box-shadow: inset 3px 0 0 var(--success); }
.diff-view-editor .cm-line.diff-rem { background: color-mix(in srgb, var(--danger) 10%, transparent); box-shadow: inset 3px 0 0 var(--danger); }
.diff-view-editor .cm-line.diff-hunk { background: color-mix(in srgb, var(--accent) 8%, transparent); color: var(--accent); font-weight: 600; cursor: pointer; box-shadow: inset 3px 0 0 var(--accent); }
.diff-view-editor .cm-line.diff-hunk-active { background: color-mix(in srgb, var(--accent) 22%, transparent); }
.diff-view-editor .cm-line.diff-hunk-accepted { background: color-mix(in srgb, var(--success) 22%, transparent) !important; color: var(--success) !important; }
.diff-view-editor .cm-line.diff-hunk-rejected { background: color-mix(in srgb, var(--danger) 22%, transparent) !important; color: var(--danger) !important; text-decoration: line-through; }
.diff-view-sidebar { min-width: 0; background: var(--surface); border-left: 1px solid var(--line); padding: 14px; overflow-y: auto; }
.diff-view-sidebar-title { margin: 0 0 10px; color: var(--text-3); font-size: 10px; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; }
.diff-hunk-card { padding: 10px 12px; background: var(--surface-soft); border: 1px solid var(--line); border-radius: 8px; margin-bottom: 8px; cursor: pointer; transition: border-color .12s, background .12s; }
.diff-hunk-card:hover { border-color: var(--line-strong); }
.diff-hunk-card.active { border-color: var(--accent); background: color-mix(in srgb, var(--accent) 12%, var(--surface-soft)); }
.diff-hunk-card-header { display: flex; align-items: center; gap: 8px; font-family: "SF Mono", ui-monospace, monospace; font-size: 10.5px; color: var(--accent); font-weight: 600; }
.diff-hunk-card-file { margin-top: 4px; color: var(--text-3); font-family: "SF Mono", ui-monospace, monospace; font-size: 10px; word-break: break-all; }
.diff-hunk-card-stats { display: flex; gap: 10px; margin-top: 6px; font-family: "SF Mono", ui-monospace, monospace; font-size: 10px; color: var(--text-3); }
.diff-hunk-card-stats .add { color: var(--success); }
.diff-hunk-card-stats .rem { color: var(--danger); }
.diff-hunk-card-actions { display: flex; gap: 6px; margin-top: 8px; }
.diff-hunk-card-status { margin-left: auto; padding: 1px 6px; border-radius: 3px; font-size: 9.5px; font-weight: 600; }
.diff-hunk-card-status-pending { color: var(--text-3); border: 1px solid var(--line-strong); }
.diff-hunk-card-status-accepted { color: var(--success); background: color-mix(in srgb, var(--success) 14%, transparent); }
.diff-hunk-card-status-rejected { color: var(--danger); background: color-mix(in srgb, var(--danger) 14%, transparent); }
.diff-hunk-card .hunk-btn { flex: 1; padding: 4px 8px; color: var(--text-2); background: var(--surface-soft); border: 1px solid var(--line-strong); border-radius: 5px; cursor: pointer; font: inherit; font-size: 10.5px; font-weight: 600; }
.diff-hunk-card .hunk-btn-accept { color: var(--success); border-color: color-mix(in srgb, var(--success) 35%, var(--line)); }
.diff-hunk-card .hunk-btn-accept:hover { background: color-mix(in srgb, var(--success) 14%, var(--surface-soft)); }
.diff-hunk-card .hunk-btn-reject { color: var(--danger); border-color: color-mix(in srgb, var(--danger) 35%, var(--line)); }
.diff-hunk-card .hunk-btn-reject:hover { background: color-mix(in srgb, var(--danger) 14%, var(--surface-soft)); }
.diff-view-cta { display: flex; align-items: center; gap: 10px; padding: 9px 18px; border-top: 1px solid var(--line); background: var(--surface); }
.diff-view-status { flex: 1; color: var(--text-3); font-size: 11px; }
.diff-view-status .count { color: var(--text); font-weight: 600; }
.diff-view-empty { padding: 36px 22px; text-align: center; color: var(--text-2); font-size: 12px; }
.diff-view-empty .title { display: block; margin-bottom: 6px; color: var(--text); font-size: 13px; font-weight: 600; }
.diff-chat-suggestions { display: flex; gap: 6px; margin-top: 10px; flex-wrap: wrap; }
#diff-chat-input { width: 100%; min-height: 80px; padding: 10px 12px; color: var(--text); background: var(--surface-soft); border: 1px solid var(--line-strong); border-radius: 8px; font: inherit; font-size: 12.5px; line-height: 1.5; resize: vertical; }
#diff-chat-input:focus { outline: none; border-color: var(--accent); }
.task-rail { display: grid; gap: 8px; margin-top: 24px; min-height: 0; }
.task-rail-heading { display: flex; align-items: center; gap: 8px; padding: 0 8px; }
.task-rail-heading strong { font-size: 11px; }
.task-rail-count { min-width: 20px; padding: 1px 6px; color: var(--text-2); background: var(--surface-soft); border: 1px solid var(--line); border-radius: 999px; font-size: 10px; text-align: center; }
.task-rail-toggle { margin-left: auto; padding: 3px 0; color: var(--text-3); background: transparent; border: 0; cursor: pointer; font-size: 10px; }
.task-rail-toggle:hover { color: var(--text); }
.task-list { display: grid; gap: 4px; max-height: min(42dvh, 430px); overflow: auto; }
.task-empty { padding: 11px 8px; color: var(--text-3); font-size: 11px; line-height: 1.45; }
.task-item { display: grid; grid-template-columns: 8px minmax(0, 1fr); gap: 8px; width: 100%; padding: 9px 8px; color: var(--text-2); background: transparent; border: 1px solid transparent; border-radius: 9px; text-align: left; cursor: pointer; transition: .2s var(--ease); }
.task-item:hover { color: var(--text); background: var(--surface-soft); }
.task-item.active { color: var(--text); background: var(--surface); border-color: var(--line); box-shadow: 0 1px 2px rgba(0,0,0,.03); }
.task-item-dot { width: 7px; height: 7px; margin-top: 5px; border-radius: 50%; background: var(--text-3); }
.task-item-dot.running { background: var(--warning); box-shadow: 0 0 0 3px color-mix(in srgb, var(--warning) 13%, transparent); }
.task-item-dot.review { background: var(--accent); box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 13%, transparent); }
.task-item-dot.done { background: var(--success); }
.task-item-dot.failed { background: var(--danger); }
.task-item.failed { color: var(--text); background: color-mix(in srgb, var(--danger) 6%, transparent); }
.task-item.completed { color: var(--text-3); }
.task-item-title { overflow: hidden; font-size: 11px; font-weight: 650; text-overflow: ellipsis; white-space: nowrap; }
.task-item-meta { display: flex; justify-content: space-between; gap: 6px; margin-top: 2px; color: var(--text-3); font-size: 9px; }
.field { display: grid; gap: 6px; }
.field label { color: var(--text-2); font-size: 11px; font-weight: 650; }
.field input, .field select, .field textarea {
  width: 100%; min-height: 42px; padding: 10px 11px; color: var(--text); background: var(--surface-soft); border: 1px solid var(--line); border-radius: 10px; outline: 0;
}
.field textarea { min-height: 82px; resize: vertical; }
.field input:focus, .field select:focus, .field textarea:focus { border-color: var(--line-strong); box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 10%, transparent); }
.field-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.dialog-actions { display: flex; justify-content: flex-end; gap: 8px; padding-top: 3px; }
.toast { position: fixed; z-index: 30; top: max(16px, env(safe-area-inset-top)); right: 16px; max-width: min(360px, calc(100% - 32px)); padding: 11px 14px; color: var(--text); background: var(--surface-solid); border: 1px solid var(--line-strong); border-radius: 11px; box-shadow: 0 12px 35px rgba(0,0,0,.15); animation: message-in .25s var(--ease) both; }

@keyframes message-in { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
@keyframes loading { from { opacity: .48; } to { opacity: 1; } }
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: .01ms !important; transition-duration: .01ms !important; scroll-behavior: auto !important; }
}

@media (max-width: 760px) {
  body { overflow: hidden; }
  .app-shell { display: block; }
  .sidebar {
    position: fixed; z-index: 12; left: 0; right: 0; bottom: 0;
    width: 100%; height: calc(62px + env(safe-area-inset-bottom));
    display: block; padding: 6px 12px env(safe-area-inset-bottom);
    border-top: 1px solid var(--line); border-right: 0;
  }
  .brand, .workspace-label, .repo-list, .sidebar-footer, .task-rail { display: none; }
  .side-nav { height: 50px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 5px; margin: 0; }
  .nav-link { min-width: 0; min-height: 50px; flex-direction: column; justify-content: center; gap: 2px; padding: 4px 2px; font-size: 10px; }
  .nav-link span { position: static; width: auto; height: auto; overflow: visible; clip-path: none; }
  .nav-link svg { width: 17px; height: 17px; }
  .workspace { width: 100%; height: calc(100dvh - 62px - env(safe-area-inset-bottom)); }
  .topbar { min-height: 48px; padding: 0 16px; }
  .topbar-title, .topbar-status, .repo-viewer { display: none; }
  .topbar-repo { justify-content: stretch; }
  .repo-picker-label small { display: none; }
  .topbar-repo select { width: auto; flex: 1; }
  .monitor-repo-button { flex: 0 0 auto; }
  .conversation, .content-page { padding: 26px 16px 138px; }
  .content-page { padding-bottom: 36px; }
  .brief-generation-controls { grid-template-columns: 1fr; }
  .brief-generation-controls label { margin-bottom: -4px; }
  .brief-generation-controls [role="status"] { grid-column: 1; }
  .message { gap: 10px; margin-bottom: 22px; }
  .avatar { width: 29px; height: 29px; border-radius: 9px; }
  .message-body { max-width: calc(100% - 39px); }
  .message-card { padding: 15px; border-radius: 5px 15px 15px 15px; }
  .signal-row { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .signal { padding: 9px 8px; }
  .signal strong { font-size: 15px; }
  .metric-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .today-view .repo-metric:nth-child(3) { border-left: 0; }
  .today-view .repo-metric:nth-child(n+3) { border-top: 1px solid var(--line); }
  .issues-heading { align-items: flex-start; flex-direction: column; gap: 7px; }
  .today-view .issue-summary { justify-content: flex-start; flex-wrap: wrap; }
  .repo-control { grid-template-columns: 1fr; gap: 3px; }
  .repo-viewer { display: none; }
  .issue-inbox { max-height: 330px; }
  .issue-row { grid-template-columns: minmax(0, 1fr); }
  .issue-command { justify-self: start; }
  .composer-wrap { left: 0; bottom: calc(62px + env(safe-area-inset-bottom)); padding: 22px 12px 10px; }
  .composer { min-height: 54px; padding-left: 13px; border-radius: 16px; }
  .composer textarea { font-size: 16px; }
  .brief-card { align-items: flex-start; }
  .field-row { grid-template-columns: 1fr; }
  .dialog { margin: auto 14px 12px; width: calc(100% - 28px); max-height: 86dvh; border-radius: 18px; }
  .repair-inspector-header { padding: 19px 16px 14px; }
  .repair-inspector .repair-progress { padding: 0 16px; }
  .repair-inspector .repair-stream { padding: 18px 16px; }
  .repair-inspector .repair-controls { padding: 12px 16px 15px; }
  .repair-controls { grid-template-columns: 1fr; }
  .repair-actions { align-items: stretch; flex-direction: column-reverse; }
  .repair-actions button { width: 100%; }
}

/* The desktop window can be resized below the comfortable two-pane width.
   Keep the task rail usable as the entry point, then give the repair session
   the whole window once it is opened instead of leaving its content offscreen. */
@media (max-width: 980px) {
  .app-shell.repair-open .sidebar { display: none; }
  .app-shell.repair-open .workspace { width: 100%; }
  .app-shell.repair-open .repair-inspector-header { padding-left: 18px; padding-right: 18px; }
  .app-shell.repair-open .repair-inspector .repair-progress { padding-left: 18px; padding-right: 18px; }
  .app-shell.repair-open .repair-inspector .repair-stream { padding-left: 18px; padding-right: 18px; }
  .app-shell.repair-open .repair-inspector .repair-controls { padding-left: 18px; padding-right: 18px; }
}
"""


APP_JS = r"""
(() => {
  document.documentElement.dataset.gheUi = 'loading';
  if (window.__TAURI_INTERNALS__) document.documentElement.classList.add('is-tauri');
  const qs = (selector, root = document) => root.querySelector(selector);
  const qsa = (selector, root = document) => [...root.querySelectorAll(selector)];
  const packagedBootstrap = qs('#desktop-bootstrap');
  if (packagedBootstrap) {
    const status = qs('#desktop-bootstrap-status');
    const retry = qs('#desktop-bootstrap-retry');
    let checking = false;
    const wait = (milliseconds) => new Promise((resolve) => window.setTimeout(resolve, milliseconds));
    const connectToLocalService = async () => {
      if (checking) return;
      checking = true;
      if (retry) {
        retry.disabled = true;
        retry.textContent = '正在连接…';
      }
      if (status) status.textContent = '正在连接本地 GitHub Engineer 服务…';
      try {
        const deadline = Date.now() + 20000;
        let attempt = 0;
        let connected = false;
        while (!connected && Date.now() < deadline) {
          attempt += 1;
          if (status && attempt > 1) status.textContent = `本地服务正在启动（第 ${attempt} 次检查）…`;
          const controller = new AbortController();
          const timeout = window.setTimeout(() => controller.abort(), 2200);
          try {
            await fetch('http://127.0.0.1:8765/ui/', {
              mode: 'no-cors',
              cache: 'no-store',
              signal: controller.signal,
            });
            connected = true;
          } catch (_) {
            const delay = Math.min(2000, 250 * (2 ** Math.min(attempt - 1, 3)));
            if (Date.now() + delay < deadline) await wait(delay);
          } finally {
            window.clearTimeout(timeout);
          }
        }
        if (!connected) throw new Error('service startup timed out');
        window.location.replace('http://127.0.0.1:8765/ui/');
      } catch (_) {
        if (status) status.textContent = '本地服务尚未启动。启动完成后可在这里重试。';
        if (retry) {
          retry.disabled = false;
          retry.textContent = '重新连接';
        }
      } finally {
        checking = false;
        document.documentElement.dataset.gheUi = 'ready';
      }
    };
    retry?.addEventListener('click', connectToLocalService);
    connectToLocalService();
    return;
  }
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
  const githubSetupDialog = qs('#github-setup-dialog');
  const githubSetupStatus = qs('#github-setup-status');
  const githubConnectButton = qs('#github-connect-button');
  const repairSetupDialog = qs('#repair-setup-dialog');
  const repairSetupStatus = qs('#repair-setup-status');
  const repairConnectButton = qs('#repair-connect-button');
  // coding-agent 配置对话框: 让用户选 provider (openai_compatible / anthropic
  // / claude_cli / 自定义 URL) + 填 api_key + 选 model + 测试连接 + 写盘.
  // 区别于老的 #repair-setup-dialog (后者只处理 Claude Code CLI 授权).
  const codingAgentDialog = qs('#coding-agent-setup-dialog');
  const codingAgentForm = qs('#coding-agent-form');
  const codingAgentProvider = qs('#coding-agent-provider');
  const codingAgentBaseUrl = qs('#coding-agent-base-url');
  const codingAgentApiKey = qs('#coding-agent-api-key');
  const codingAgentModel = qs('#coding-agent-model');
  const codingAgentTest = qs('#coding-agent-test');
  const codingAgentSave = qs('#coding-agent-save');
  const codingAgentStatus = qs('#coding-agent-status');
  const codingAgentModels = qs('#coding-agent-models');
  const codingAgentDataBoundary = qs('#coding-agent-data-boundary');
  // 顶部状态栏的 Coding Agent 指示器: 让用户一眼看到当前 provider + model,
  // 不配置时给一个明显的灰色 "未配置" + 配置入口.
  const codingAgentIndicator = qs('#coding-agent-indicator');
  const modeIndicator = qs('#mode-indicator');
  const briefGenerateRepository = qs('#brief-generate-repository');
  const briefGenerateButton = qs('#brief-generate-button');
  const briefGenerateStatus = qs('#brief-generate-status');
  const diffView = qs('#diff-view');
  const diffViewOverview = qs('.diff-view-overview');
  const diffViewEditor = qs('#diff-view-editor');
  const diffViewSidebar = qs('#diff-view-sidebar-list');
  const diffViewStatus = qs('#diff-view-status');
  const diffViewStats = qs('#diff-view-stats');
  const diffViewTitle = qs('#diff-view-title');
  const diffViewSummary = qs('#diff-view-summary');
  const diffViewVerification = qs('#diff-view-verification');
  const diffViewUpgrade = qs('#diff-view-upgrade');
  const diffAcceptAll = qs('#diff-accept-all');
  const diffRejectAll = qs('#diff-reject-all');
  const diffContinueChat = qs('#diff-continue-chat');
  const diffOpenVscode = qs('#diff-open-vscode');
  const diffConnectGithub = qs('#diff-connect-github');
  const diffChatDialog = qs('#diff-chat-dialog');
  const diffChatInput = qs('#diff-chat-input');
  const diffChatSend = qs('#diff-chat-send');
  const monitorForm = qs('#monitor-form');
  const repositoryOnboarding = qs('#repository-onboarding');
  const ownedPickerPanel = qs('#owned-picker-panel');
  const ownedRepoSearch = qs('#owned-repo-search');
  const ownedRepoList = qs('#owned-repo-list');
  const repairDialog = qs('#repair-inspector');
  const repairTaskList = qs('#repair-task-list');
  const repairTaskCount = qs('#repair-task-count');
  const repairTaskToggle = qs('#repair-task-toggle');
  const repairRepository = qs('#repair-repository');
  const repairTitle = qs('#repair-title');
  const repairDelivery = qs('#repair-delivery');
  const repairStream = qs('#repair-stream');
  const repairGuidanceInput = qs('#repair-guidance-input');
  const repairGuidanceSend = qs('#repair-guidance-send');
  const repairSkipSubmit = qs('#repair-skip-submit');
  const repairPublish = qs('#repair-publish');
  const defaultOnboardingMarkup = repositoryOnboarding?.innerHTML || '';
  let pendingDecision = null;
  let currentRepository = root?.dataset.repo || '';
  let currentIssues = [];
  let ownedRepositories = [];
  let pendingIssueTask = null;
  let currentCanModify = false;
  let currentGithubAuthenticated = false;
  let currentGithubAccount = '';
  let currentRepairMode = 'fork_pr';
  let repairCapabilities = null;
  // 缓存后端 render_repair_capabilities 返回的 coding_agent 子字段, 给
  // Issue inbox CTA + 顶部状态栏复用. configured 决定走 4 档 action 中的
  // 哪一档, provider/model 是状态栏文案.
  let currentCodingAgent = {
    configured: false,
    provider: '',
    model: '',
    last_error_kind: '',
  };
  let currentRepairIssue = null;
  let currentRepairRepository = '';
  let currentRepairJob = null;
  let repairPollTimer = null;
  let connectionPollTimer = null;
  let briefGenerationTimer = null;
  let repairJobs = [];
  let showRepairHistory = false;
  let publishGeneration = 0;
  let repairSessionGeneration = 0;

  const normalizedProviderName = (job = null) => String(
    job?.provider
    || job?.coding_agent_provider
    || job?.agent_provider
    || job?.coding_agent?.provider
    || currentCodingAgent?.provider
    || ''
  ).trim().toLowerCase();

  const isDemoRepair = (job = null) => {
    const provider = normalizedProviderName(job);
    return ['fake', 'demo', 'mock', 'test'].includes(provider)
      || provider.startsWith('fake_')
      || provider.startsWith('demo_');
  };

  // Publishing is fail-closed: a task must identify a non-demo provider.
  // This protects historical jobs even before every backend response includes
  // a dedicated demo flag.
  const providerAllowsPublishing = (job = null) => {
    const provider = normalizedProviderName(job);
    return Boolean(provider) && !isDemoRepair(job);
  };

  const repairVerification = (job = null) => {
    const raw = job?.verification ?? job?.test_results ?? job?.test_result;
    const rawStatus = String(
      (raw && typeof raw === 'object' ? raw.status : raw)
      || job?.verification_status
      || job?.test_status
      || ''
    ).trim().toLowerCase();
    let status = 'unverified';
    if (job?.tests_passed === true || ['passed', 'pass', 'success', 'verified', 'ok'].includes(rawStatus)) {
      status = 'passed';
    } else if (job?.tests_passed === false || ['failed', 'fail', 'error'].includes(rawStatus)) {
      status = 'failed';
    }
    const detail = String(
      (raw && typeof raw === 'object' && (raw.summary || raw.message || raw.detail))
      || job?.verification_summary
      || job?.test_summary
      || ''
    ).trim();
    const reason = String(
      (raw && typeof raw === 'object' && raw.reason)
      || job?.verification_reason
      || ''
    ).trim().toLowerCase();
    return { status, detail, reason };
  };

  const missingVerificationTools = (job = null) => {
    const raw = job?.verification;
    const commands = raw && typeof raw === 'object' && Array.isArray(raw.commands)
      ? raw.commands
      : [];
    return commands.flatMap((command) => {
      const stderr = String(command?.stderr_summary || '');
      if (command?.exit_code !== null || !/No such file or directory/i.test(stderr)) return [];
      const executable = String(command?.argv?.[0] || command?.display || '').trim().split(/\s+/)[0];
      return executable ? [executable] : [];
    }).filter((value, index, values) => values.indexOf(value) === index);
  };

  const verificationToolLabel = (tool) => ({
    go: 'Go',
    node: 'Node.js',
    npm: 'npm',
    pnpm: 'pnpm',
    yarn: 'Yarn',
    python: 'Python',
  }[tool] || tool);

  const renderVerification = (job) => {
    const verification = repairVerification(job);
    const missingTools = missingVerificationTools(job);
    if (missingTools.length) {
      const names = missingTools.map(verificationToolLabel).join('、');
      return `<div class="repair-verification" data-status="unverified"><strong>验证环境不完整</strong><span>本机缺少 ${escapeHtml(names)}，代码改动仍可 Review；完成验证前暂不能提交。</span></div>`;
    }
    if (verification.status === 'unverified' && verification.reason === 'dependency_missing') {
      return `<div class="repair-verification" data-status="unverified"><strong>验证环境不完整</strong><span>${escapeHtml(verification.detail || '项目依赖没有安装完整；代码改动仍可 Review，完成验证前暂不能提交。')}</span></div>`;
    }
    const labels = {
      passed: ['验证通过', '已收到明确的测试/验证通过结果。'],
      failed: ['验证失败', '测试或验证没有通过，暂时不能提交修复。'],
      unverified: ['等待验证', '还没有明确的测试结果，暂时不能提交修复。'],
    };
    const [title, fallback] = labels[verification.status];
    return `<div class="repair-verification" data-status="${verification.status}"><strong>${title}</strong><span>${escapeHtml(verification.detail || fallback)}</span></div>`;
  };

  const renderDiffVerification = (job) => {
    const verification = repairVerification(job);
    const raw = job?.verification;
    const commands = raw && typeof raw === 'object' && Array.isArray(raw.commands)
      ? raw.commands
      : [];
    const output = commands.map((command) => [
      command?.display ? `$ ${command.display}` : '',
      command?.stdout_summary || '',
      command?.stderr_summary || '',
    ].filter(Boolean).join('\n')).filter(Boolean).join('\n\n');
    let recovery = '';
    if (verification.status === 'failed') {
      const missingTools = missingVerificationTools(job);
      const modules = Array.from(output.matchAll(/No module named ['"]([^'"]+)['"]/g))
        .map((match) => match[1])
        .filter((value, index, values) => values.indexOf(value) === index);
      const dependencyHint = missingTools.length
        ? `本机没有安装 ${missingTools.map(verificationToolLabel).join('、')}，所以测试没有真正启动；这不表示代码本身失败。你仍可在下方 Review 全部改动。`
        : modules.length
        ? `测试环境缺少依赖：${modules.join('、')}。请先在可信的项目环境中安装依赖，然后重新验证。`
        : '查看失败摘要，修复测试环境或代码后重新验证。';
      const log = output
        ? `<details class="verification-log"><summary>查看失败摘要</summary><pre>${escapeHtml(output.slice(-6000))}</pre></details>`
        : '';
      recovery = `<div class="verification-recovery">${escapeHtml(dependencyHint)}<div class="suggestions"><button class="suggestion primary-suggestion" type="button" data-retry-verification>重新运行验证</button></div>${log}</div>`;
    } else if (verification.status === 'unverified' && verification.reason === 'sandbox_unavailable') {
      recovery = '<div class="verification-recovery">尚未运行测试。继续前会再次确认执行不可信仓库代码的风险。<div class="suggestions"><button class="suggestion primary-suggestion" type="button" data-allow-host-verification>我理解风险，在本机运行测试</button></div></div>';
    } else if (verification.status === 'unverified' && ['no_tests_detected', 'dependency_missing'].includes(verification.reason)) {
      const modules = Array.from(output.matchAll(/No module named ['"]([^'"]+)['"]/g))
        .map((match) => match[1])
        .filter((value, index, values) => values.indexOf(value) === index);
      const hint = verification.reason === 'dependency_missing'
        ? `缺少项目依赖${modules.length ? `：${modules.join('、')}` : ''}。补齐可信项目环境后可以重新验证。`
        : '当前没有识别到测试命令。更新测试配置或检测规则后可以重新检测。';
      const log = output
        ? `<details class="verification-log"><summary>查看验证摘要</summary><pre>${escapeHtml(output.slice(-6000))}</pre></details>`
        : '';
      recovery = `<div class="verification-recovery">${escapeHtml(hint)}<div class="suggestions"><button class="suggestion primary-suggestion" type="button" data-retry-verification>重新检测并验证</button></div>${log}</div>`;
    }
    return `${renderVerification(job)}${recovery}`;
  };

  const providerDataBoundary = (job = null) => {
    const provider = normalizedProviderName(job);
    if (isDemoRepair(job)) {
      return 'fake 只生成演示数据，不会真正理解或修复仓库；演示任务不能提交。';
    }
    if (provider === 'codex_cli' || provider === 'claude_cli' || provider.includes('local') || provider.includes('ollama')) {
      return '当前 Provider 在本机处理仓库内容；是否产生外部请求取决于该本地工具自身的配置。';
    }
    return '使用 API Provider 时，Issue 内容与为定位问题选取的仓库源码片段会发送给所配置的模型服务。请确认仓库数据允许发送。';
  };

  const escapeHtml = (value) => String(value)
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;').replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');

  const scrollToLatest = () => {
    if (scroller) scroller.scrollTo({ top: scroller.scrollHeight, behavior: 'smooth' });
  };

  const showToast = (message) => {
    qs('.toast')?.remove();
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.setAttribute('role', 'status');
    toast.setAttribute('aria-live', 'polite');
    toast.textContent = message;
    document.body.appendChild(toast);
    window.setTimeout(() => toast.remove(), 3200);
  };

  const fetchJson = async (url, options) => {
    const response = await fetch(url, options);
    const raw = await response.text();
    let result = {};
    if (raw) {
      try {
        result = JSON.parse(raw);
      } catch (_) {
        result = { error: response.ok ? '服务返回了无法识别的数据' : raw.slice(0, 240) };
      }
    }
    if (!response.ok) {
      const error = new Error(result.error || `请求失败 (${response.status})`);
      Object.assign(error, result, { status: response.status });
      throw error;
    }
    return result;
  };

  const setBriefGenerationState = (busy, message) => {
    if (briefGenerateButton) {
      briefGenerateButton.disabled = Boolean(busy);
      briefGenerateButton.textContent = busy ? '正在生成…' : '生成新简报';
      briefGenerateButton.toggleAttribute('aria-busy', Boolean(busy));
    }
    if (briefGenerateRepository) briefGenerateRepository.disabled = Boolean(busy);
    if (briefGenerateStatus) briefGenerateStatus.textContent = message || '';
  };

  const pollBriefGeneration = async (jobId) => {
    window.clearTimeout(briefGenerationTimer);
    try {
      const job = await fetchJson(`/api/brief-jobs/${encodeURIComponent(jobId)}`);
      if (job.status === 'completed' && job.url) {
        setBriefGenerationState(false, '简报已生成，正在打开…');
        window.location.assign(job.url);
        return;
      }
      if (job.status === 'failed') {
        setBriefGenerationState(false, job.message || '简报生成失败，请检查配置后重试。');
        return;
      }
      setBriefGenerationState(true, job.message || '正在生成维护简报…');
      briefGenerationTimer = window.setTimeout(() => pollBriefGeneration(jobId), 1200);
    } catch (error) {
      setBriefGenerationState(false, error.message || '暂时无法读取生成进度。');
    }
  };

  const startBriefGeneration = async () => {
    const repository = String(briefGenerateRepository?.value || '').trim();
    if (!repository) {
      setBriefGenerationState(false, '请先选择一个仓库。');
      return;
    }
    setBriefGenerationState(true, '正在创建简报任务…');
    try {
      const job = await fetchJson('/api/briefs/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repository }),
      });
      await pollBriefGeneration(job.id);
    } catch (error) {
      setBriefGenerationState(false, error.message || '简报任务启动失败。');
    }
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
    const githubAuthenticated = Boolean(result.authentication?.authenticated);
    currentGithubAuthenticated = githubAuthenticated;
    currentRepairMode = result.repair_mode || (currentCanModify ? 'owner_pr' : 'fork_pr');
    // 成功拉过数据后, refresh 按钮才有意义
    if (refreshIssues) refreshIssues.hidden = false;
    if (repoPermission) {
      repoPermission.hidden = false;
      repoPermission.className = `repo-permission ${currentCanModify ? 'owner' : 'monitor'}`;
      repoPermission.textContent = currentCanModify
        ? '我的仓库 · 可直接提交修复草稿'
        : (githubAuthenticated
          ? '外部仓库 · 可通过你的副本提交修复'
          : '公开仓库 · 可直接查看（连接 GitHub 后可提 Issue / Fork / PR）');
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
      // 入口层 CTA 文案按 currentCanModify (我的 vs 外部仓库) + 已认证状态分四档.
      // 永远可点: 无 auth 时点 "启用自动修复" 弹设置, 有 auth 时直接进修复流程.
      // 文案目标是让用户**一眼看出产物会去哪里** — 不暗示 "必须升级", 也不隐瞒后果.
      let repairLabel;
      let repairSubLabel = '';
      if (repairCapabilities === null) {
        repairLabel = '开始修复';
      } else if (currentCanModify && currentGithubAuthenticated) {
        repairLabel = '开始修复';
        repairSubLabel = '完成后可提 PR';
      } else if (currentCanModify && !currentGithubAuthenticated) {
        repairLabel = '开始修复';
        repairSubLabel = '先生成本地草稿';
      } else if (!currentCanModify && currentGithubAuthenticated) {
        repairLabel = '开始修复';
        repairSubLabel = '完成后可提 PR';
      } else {
        repairLabel = '开始修复';
        repairSubLabel = '先生成本地草稿';
      }
      // 4 档 action 字段: 拆开 gh / coding_agent 状态, 而不是只看 repairReady.
      //   - fully ready (gh + coding_agent): data-issue-command → 直接进修复
      //   - coding_agent 未配置: data-open-coding-agent-setup → 弹 "配置 Coding Agent" 对话框
      //   - coding_agent 已配置 + gh 未连: data-open-github-setup → 弹 GitHub 连接
      //   - coding_agent 已配置 + gh 已连 + 上次是 api_key invalid: data-open-coding-agent-setup → 让用户修配置
      // 之前只看 repairReady, 外部仓库+gh 已连+coding_agent 未连会误判 "全 ready".
      // 改 provider 抽象后, "Coding Agent" 不再硬绑 Claude Code, 4 档要按后端 coding_agent
      // 字段实际返回的 configured + last_error_kind 走.
      const ghAuth = Boolean(currentGithubAuthenticated);
      const ca = currentCodingAgent || {};
      const caConfigured = Boolean(ca.configured);
      const caHealthy = Boolean(ca.healthy);
      const caLabel = ca.provider ? `${ca.provider} · ${ca.model || '默认 model'}` : 'Coding Agent';
      const apiKeyError = ca.last_error_kind === 'api_key_invalid';
      let repairAction;
      let repairTitle;
      if (caConfigured && caHealthy && ghAuth && !apiKeyError) {
        // 全 ready: 进修复
        repairAction = `data-issue-command="${issue.number}"`;
        repairTitle = '';
        repairSubLabel = repairSubLabel
          ? `${repairSubLabel} · 用 ${caLabel}`
          : `用 ${caLabel}`;
      } else if (!caConfigured) {
        // 没配 coding agent — 弹配置 dialog
        repairAction = 'data-open-coding-agent-setup';
        repairTitle = ' title="先配置 Coding Agent"';
        repairSubLabel = '需要先完成修复设置';
      } else if (!caHealthy || apiKeyError) {
        repairAction = 'data-open-coding-agent-setup';
        repairTitle = ' title="Coding Agent 连接失败，请检查配置"';
        repairSubLabel = '检查修复设置';
      } else if (!ghAuth) {
        // coding agent 已配, 但没连 gh — 弹 gh 连接
        repairAction = 'data-open-github-setup';
        repairTitle = ' title="先连接 GitHub"';
        repairSubLabel = '完成后连接 GitHub 才能提 PR';
      } else {
        repairAction = 'data-open-coding-agent-setup';
        repairTitle = ' title="自动修复环境尚未就绪"';
        repairSubLabel = '需要先完成修复设置';
      }
      const sub = repairSubLabel
        ? `<span class="issue-command-sub">${escapeHtml(repairSubLabel)}</span>`
        : '';
      return `<article class="issue-row">
        <div class="issue-main">
          <a class="issue-title" href="${escapeHtml(issue.url)}" target="_blank" rel="noreferrer"><span class="issue-number">#${issue.number}</span>${escapeHtml(issue.title)}</a>
          <div class="issue-meta">${attention}<span>${relativeTime(issue.updated_at)}</span><span>${issue.comments_count} 条评论</span><span>${assignment}</span>${labels}</div>
        </div>
        <div class="issue-commands">
          <button class="issue-command" type="button" ${repairAction}${repairTitle}>${repairLabel}${sub}</button>
        </div>
      </article>`;
    }).join('');
  };

  const setConnectionPanel = (kind, state, detail = '') => {
    const isAccount = kind === 'account';
    const status = isAccount ? githubSetupStatus : repairSetupStatus;
    const button = isAccount ? githubConnectButton : repairConnectButton;
    if (!status) return;
    const copy = {
      account: {
        ready: ['连接已完成', detail || '私有仓库和提交操作已可用。'],
        optional: ['需要更多功能时再连接', '查看公开仓库不受影响。连接后可使用私有仓库和提交操作。'],
        blocked: ['需要更多功能时再连接', '查看公开仓库不受影响。连接后可使用私有仓库和提交操作。'],
        pending: ['等待你完成确认', detail || '请在刚刚打开的窗口中完成操作；完成后会自动继续。'],
      },
      automatic_repair: {
        ready: ['可以开始自动修复', '连接已完成，失败任务可以重新运行。'],
        blocked: ['首次使用需要完成一次连接', '点击下面的按钮，然后在打开的页面确认即可。'],
        pending: ['等待你完成确认', detail || '请在刚刚打开的窗口中完成操作；完成后会自动继续。'],
      },
    };
    const [title, defaultMessage] = copy[kind][state];
    const message = detail || defaultMessage;
    status.className = `repair-setup-status ${state}`;
    status.innerHTML = `<strong>${escapeHtml(title)}</strong><span>${escapeHtml(message)}</span>`;
    if (button) {
      button.hidden = state === 'ready';
      button.style.display = state === 'ready' ? 'none' : '';
      button.disabled = state === 'pending';
      if (state === 'blocked' || state === 'optional') button.textContent = '开始连接';
      if (state === 'pending') button.textContent = '等待确认…';
    }
    const steps = status.parentElement?.querySelector('.connection-steps');
    if (steps) steps.hidden = state === 'ready';
  };

  const applyConnectionStatus = (result) => {
    const account = result?.account || {};
    const automaticRepair = result?.automatic_repair || {};
    setConnectionPanel('account', account.connected ? 'ready' : 'optional', account.label
      ? `${account.label} 已连接，之后无需为每个仓库重复操作。`
      : '');
    setConnectionPanel('automatic_repair', automaticRepair.ready ? 'ready' : 'blocked');
    if (repoViewer && account.connected && account.label) {
      repoViewer.textContent = account.label;
      repoViewer.title = '账号已连接，点击查看说明';
    }
    return { account, automaticRepair };
  };

  // mode indicator: 顶部状态栏的"匿名 / 完整模式"徽章. 跟随
  // /api/repositories 返回的 authentication 字段更新. 匿名模式不暗示
  // "必须升级" — 它的黄色徽章只是说明 "产物留本地", 完整模式的绿色
  // 徽章说明 "可发 PR", 两种状态都是一等公民.
  const updateModeIndicator = (authenticated, accountLabel = '') => {
    if (!modeIndicator) return;
    if (diffConnectGithub) diffConnectGithub.hidden = Boolean(authenticated);
    if (authenticated) {
      modeIndicator.dataset.mode = 'authenticated';
      modeIndicator.textContent = accountLabel
        ? `完整模式 · @${accountLabel.replace(/^@/, '')}`
        : '完整模式 · 可发 PR';
      modeIndicator.title = '已连接 GitHub：可以 Fork、提 Issue、创建 PR。';
    } else {
      modeIndicator.dataset.mode = 'anonymous';
      modeIndicator.textContent = '匿名浏览 · 产物留本地';
      modeIndicator.title = (
        '匿名模式：可以浏览、克隆、修复公开仓库，所有产物留在本地。' +
        '要对外提交 PR 时再点右上角"连接 GitHub"。'
      );
    }
  };

  // 第一次打开: 弹引导. 之后不再弹.
  // 我们用 localStorage 标记而不是 server 端标志, 原因:
  // 1) 引导是纯 UI 行为, 跟仓库数据无关;
  // 2) 标记只跟"这台浏览器 + 这个 origin"绑定, 换机器/换账号是新人, 应该再看一次.
  const ONBOARDING_FLAG = 'ghe-onboarding-seen';
  const showOnboardingIfFirstTime = () => {
    if (!repositoryOnboarding) return;
    let alreadySeen = false;
    try { alreadySeen = window.localStorage.getItem(ONBOARDING_FLAG) === '1'; } catch (_) { /* private mode */ }
    if (alreadySeen) {
      // “稍后再说”只收起首次欢迎内容，不能把唯一的无仓库空状态也一起
      // 隐藏，否则主区会因为 no-repositories 规则变成一块空白。
      repositoryOnboarding.innerHTML = defaultOnboardingMarkup;
      repositoryOnboarding.hidden = false;
      if (root) root.classList.add('no-repositories');
      document.documentElement.classList.add('no-repositories');
      return;
    }
    // 三个首屏状态来自并行请求，欢迎页必须随最终状态重渲染，不能在
    // 顶栏已经显示“已连接”时仍要求用户重复配置。
    const codingAgentReady = Boolean(currentCodingAgent?.configured && currentCodingAgent?.healthy);
    const githubReady = Boolean(currentGithubAuthenticated);
    const codingAgentLabel = currentCodingAgent?.provider
      ? `${currentCodingAgent.provider} · ${currentCodingAgent.model || '默认 model'}`
      : 'Coding Agent';
    const githubLabel = currentGithubAccount ? `@${currentGithubAccount.replace(/^@/, '')}` : 'GitHub';
    const welcomeTitle = codingAgentReady && githubReady
      ? '准备完成，只差添加仓库'
      : '欢迎使用 GitHub Engineer';
    const welcomeCopy = codingAgentReady && githubReady
      ? `${codingAgentLabel} 和 ${githubLabel} 已连接。添加仓库后即可读取 Issue、生成简报和准备修复草稿。`
      : 'GitHub Engineer 用 AI 帮你自动修 Issue、生成 PR 草稿。完成下面尚未就绪的项目后即可开始。';
    const primaryAction = codingAgentReady
      ? '<button class="primary-button" type="button" data-onboarding-add-repo>添加仓库</button>'
      : '<button class="primary-button" type="button" data-open-coding-agent-setup>配置 Coding Agent</button>';
    const secondaryAction = codingAgentReady
      ? '<button class="soft-button" type="button" data-open-coding-agent-setup>查看 Coding Agent</button>'
      : '<button class="soft-button" type="button" data-onboarding-add-repo>添加仓库</button>';
    const connectionHint = githubReady
      ? `${githubLabel} 已连接：添加仓库后可使用 Fork、Issue 和 Draft PR 功能。`
      : '匿名模式可浏览、克隆和修复公开仓库，产物留本地；连接 GitHub 后可使用 Fork 和 Draft PR。';
    repositoryOnboarding.innerHTML = `
      <div class="onboarding-icon">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M9 12l2 2 4-4"/>
          <circle cx="12" cy="12" r="9"/>
        </svg>
      </div>
      <h1>${escapeHtml(welcomeTitle)}</h1>
      <p>${escapeHtml(welcomeCopy)}</p>
      <ol class="onboarding-steps">
        <li class="onboarding-step">
          <span class="step-number${codingAgentReady ? ' complete' : ''}">${codingAgentReady ? '✓' : '1'}</span>
          <span class="step-text"><strong>${codingAgentReady ? 'Coding Agent 已就绪' : '配置 Coding Agent'}</strong> · ${escapeHtml(codingAgentReady ? codingAgentLabel : '选择 Codex CLI、OpenAI、DeepSeek、Anthropic 或自托管模型')}</span>
        </li>
        <li class="onboarding-step">
          <span class="step-number">2</span>
          <span class="step-text"><strong>添加仓库</strong> · 粘贴 GitHub 仓库地址，或从你的仓库里选</span>
        </li>
        <li class="onboarding-step">
          <span class="step-number${githubReady ? ' complete' : ''}">${githubReady ? '✓' : '3'}</span>
          <span class="step-text"><strong>${githubReady ? 'GitHub 已连接' : '连接 GitHub（可选）'}</strong> · ${escapeHtml(githubReady ? githubLabel : '公开仓库匿名可用；连接后解锁 Fork 和 Draft PR')}</span>
        </li>
      </ol>
      <div class="onboarding-actions">
        ${primaryAction}
        ${secondaryAction}
        <button class="soft-button" type="button" data-onboarding-skip>稍后再说</button>
      </div>
      <div class="onboarding-hint">
        ${escapeHtml(connectionHint)}
      </div>`;
    repositoryOnboarding.hidden = false;
    if (root) root.classList.add('no-repositories');
    document.documentElement.classList.add('no-repositories');
  };
  const markOnboardingSeen = () => {
    try { window.localStorage.setItem(ONBOARDING_FLAG, '1'); } catch (_) { /* ignore */ }
  };

  const pollConnectionStatus = async (desired, attempt = 0) => {
    window.clearTimeout(connectionPollTimer);
    try {
      const result = await fetchJson('/api/connections/status');
      const { account, automaticRepair } = applyConnectionStatus(result);
      const complete = desired === 'account' ? account.connected : automaticRepair.ready;
      if (complete) {
        showToast('连接完成，可以继续');
        await loadRepairCapabilities(true);
        if (desired === 'account') await loadRepositories();
        return;
      }
      if (desired === 'automatic_repair' && automaticRepair.next_connection === 'account') {
        setConnectionPanel('automatic_repair', 'blocked', '还需完成一次确认，然后就可以开始修复。');
        if (repairConnectButton) {
          repairConnectButton.dataset.startConnection = 'account';
          repairConnectButton.textContent = '继续连接';
          repairConnectButton.hidden = false;
          repairConnectButton.disabled = false;
        }
        return;
      }
      const waitingKind = desired === 'account' ? 'account' : 'automatic_repair';
      setConnectionPanel(waitingKind, 'pending');
    } catch (error) {
      if (attempt >= 2) {
        setConnectionPanel(desired, 'blocked', '没有检测到连接结果，可以再试一次。');
      }
    }
    if (attempt < 90) {
      connectionPollTimer = window.setTimeout(
        () => pollConnectionStatus(desired, attempt + 1),
        2000,
      );
    } else {
      setConnectionPanel(desired, 'blocked', '暂时没有检测到结果，可以再试一次。');
    }
  };

  const startConnection = async (connection, desired, button) => {
    const panelKind = desired === 'account' ? 'account' : 'automatic_repair';
    setConnectionPanel(panelKind, 'pending', '正在打开确认窗口…');
    if (button) {
      button.disabled = true;
      button.textContent = '正在打开…';
    }
    try {
      const result = await fetchJson('/api/connections/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ connection }),
      });
      if (!result.started) throw new Error(result.message || '请使用备用方式完成连接。');
      setConnectionPanel(panelKind, 'pending');
      pollConnectionStatus(desired);
    } catch (error) {
      setConnectionPanel(panelKind, 'blocked', error.message || '暂时无法开始连接，请再试一次。');
      if (button) {
        button.disabled = false;
        button.hidden = false;
        button.textContent = '再试一次';
      }
    }
  };

  const loadRepairCapabilities = async (force = false) => {
    try {
      repairCapabilities = await fetchJson(`/api/repair-capabilities${force ? '?refresh=1' : ''}`);
    } catch (error) {
      repairCapabilities = {
        available: false,
        reasons: [error.message || '自动修复环境检查失败'],
      };
    }
    setConnectionPanel(
      'automatic_repair',
      repairCapabilities?.available ? 'ready' : 'blocked',
    );
    // 把后端返回的 coding_agent 字段 (provider / configured / last_error_kind) 缓存到
    // currentCodingAgent, 然后刷新顶部状态栏. 兼容旧 shape: 后端还没切到 provider
    // 抽象时, coding_agent.authenticated 也能用, 视为 "Claude Code" 已配.
    const caPayload = repairCapabilities?.coding_agent || {};
    currentCodingAgent = {
      configured: Boolean(caPayload.configured ?? caPayload.authenticated),
      healthy: Boolean(caPayload.healthy ?? caPayload.authenticated),
      provider: String(caPayload.provider || '').trim(),
      model: String(caPayload.model || '').trim(),
      last_error_kind: String(caPayload.last_error_kind || '').trim(),
    };
    updateCodingAgentIndicator();
    if (root?.classList.contains('no-repositories')) showOnboardingIfFirstTime();
    if (currentIssues.length) renderIssueInbox(currentIssues);
  };

  // 顶部状态栏的 "Coding Agent" 指示器: 跟 mode-indicator 并列.
  // - 未配置: 灰色 "未配置 Coding Agent", 点击弹配置对话框
  // - 已配置且健康: 绿色 (success) "Provider · model", 鼠标悬停显示来源, 点击也弹对话框
  // - 已配置但健康检查失败: 琥珀色并明确要求检查 key/base_url
  // - 已配置但上次失败 (api_key_invalid): 琥珀色 (warning) 提醒
  const updateCodingAgentIndicator = () => {
    if (!codingAgentIndicator) return;
    const ca = currentCodingAgent || {};
    if (!ca.configured) {
      codingAgentIndicator.dataset.state = 'unconfigured';
      codingAgentIndicator.textContent = '未配置 Coding Agent';
      codingAgentIndicator.title = '点击配置 Coding Agent（OpenAI / Anthropic / Claude CLI / 自托管）';
    } else if (!ca.healthy || ca.last_error_kind === 'api_key_invalid') {
      codingAgentIndicator.dataset.state = 'invalid';
      const providerLabel = ca.provider || 'Coding Agent';
      codingAgentIndicator.textContent = `${providerLabel} · 连接失败`;
      codingAgentIndicator.title = 'Provider 健康检查失败，请检查 API key、base_url 和 model';
    } else if (isDemoRepair()) {
      codingAgentIndicator.dataset.state = 'demo';
      codingAgentIndicator.textContent = '演示模式 · fake';
      codingAgentIndicator.title = '仅用于演示流程：不会真正理解或修复代码，也禁止创建 Draft PR';
    } else {
      codingAgentIndicator.dataset.state = 'configured';
      const providerLabel = ca.provider || 'Coding Agent';
      const modelLabel = ca.model || '默认 model';
      codingAgentIndicator.textContent = `${providerLabel} · ${modelLabel}`;
      codingAgentIndicator.title = `已配置：${providerLabel} / ${modelLabel}，点击修改`;
    }
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
      issueInbox.innerHTML = `<div class="issue-error"><strong>Issue 暂时读不到</strong><span>${escapeHtml(error.message || '暂时无法连接 GitHub，请稍后重试。')}</span><div class="error-actions"><button class="soft-button" type="button" data-action="retry-load-issues">重试一次</button><button class="soft-button" type="button" data-open-monitor>换一个仓库</button></div></div>`;
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
      if (repoViewer) {
        repoViewer.textContent = result.viewer ? `@${result.viewer}` : '公开仓库可直接查看 · 更多功能';
        repoViewer.title = result.viewer
          ? '账号已连接，点击查看说明'
          : '公开仓库无需连接；点击了解更多账号功能';
      }
      currentGithubAuthenticated = Boolean(result.viewer);
      currentGithubAccount = String(result.viewer || '');
      setConnectionPanel(
        'account',
        result.viewer ? 'ready' : 'optional',
        result.viewer ? `@${result.viewer} 已连接，之后无需为每个仓库重复操作。` : '',
      );
      // 同步更新顶部 "匿名 / 完整模式" 徽章 — 跟随 viewer 字段
      // (anonymous / authenticated) 走, 不依赖第二个 fetch.
      updateModeIndicator(Boolean(result.viewer), result.viewer || '');
      // Secondary pages share the sidebar and connection indicators but do
      // not render the home-only repository switcher or Issue inbox. Their
      // shared chrome is now current, so leave the home initialization here.
      if (!repoSwitcher) return;
      repoSwitcher.innerHTML = repositories.map((repository) => {
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
        showOnboardingIfFirstTime();
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
      // 恢复上次选择；本地记录失效时使用后端默认仓库，再 fallback 到
      // 列表第一项。桌面应用启动后应直接可用，不能让已经配置完成的用户
      // 每次都停在“未选择仓库”的死首屏。
      let rememberedRepository = '';
      try { rememberedRepository = window.localStorage.getItem('ghe:selected-repository') || ''; } catch (_) {}
      const repositoryNames = new Set(repositories.map((repository) => repository.full_name));
      const selectedRepository = repositoryNames.has(rememberedRepository)
        ? rememberedRepository
        : (repositoryNames.has(result.selected) ? result.selected : repositories[0].full_name);
      currentRepository = selectedRepository;
      repoSwitcher.disabled = false;
      repoSwitcher.value = selectedRepository;
      if (root) {
        root.classList.remove('no-repositories');
        root.dataset.repo = selectedRepository;
      }
      if (repositoryOnboarding) repositoryOnboarding.hidden = true;
      document.documentElement.classList.remove('no-repositories');
      try { window.localStorage.setItem('ghe:selected-repository', selectedRepository); } catch (_) {}
      await loadIssues(selectedRepository);
    } catch (error) {
      if (repoSwitcher) {
        repoSwitcher.innerHTML = '<option value="" selected disabled>无法读取仓库</option>';
        repoSwitcher.disabled = true;
      }
      if (issueSummary) issueSummary.innerHTML = '<span><strong>—</strong> 个待处理</span>';
      if (issueInbox) {
        issueInbox.innerHTML = `<div class="issue-error"><strong>暂时没能读取仓库列表</strong><span>${escapeHtml(error.message || '公开仓库仍可通过地址添加；连接 GitHub 后可以使用账号功能。')}</span><div class="error-actions"><button class="soft-button" type="button" data-open-github-setup>查看连接方式</button></div></div>`;
      }
      if (loadIssuesButton) loadIssuesButton.hidden = true;
      if (refreshIssues) refreshIssues.hidden = true;
      currentRepository = '';
      if (root) root.dataset.repo = '';
      if (activeRepoHeading) {
        activeRepoHeading.textContent = '仓库列表读取失败';
        activeRepoHeading.classList.add('heading-failed');
      }
      if (dailySummary) dailySummary.textContent = '可以稍后重试；公开仓库仍可直接通过地址添加。';
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
      ownedRepoList.innerHTML = `<div class="issue-error"><strong>连接 GitHub 后，可以从你的仓库中选择</strong><span>${escapeHtml(error.message || '如果只是查看公开仓库，也可以直接粘贴仓库地址。')}</span><div class="error-actions"><button class="soft-button" type="button" data-open-github-setup>连接 GitHub</button></div></div>`;
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
      if (ownedRepoSearch) ownedRepoSearch.value = '';
      if (ownedPickerPanel) ownedPickerPanel.hidden = true;
      if (ownedRepoList) ownedRepoList.innerHTML = '';
      ownedRepositories = [];
      showToast(`${result.full_name} 已添加到清单, 开始拉取数据…`);
      // loadRepositories 会恢复刚写入的 selected-repository，并且只拉取
      // 一次该仓库的 Issue。不要在它之后再次 loadIssues，避免首启重复等待
      // 和浪费 GitHub API 配额。
      await loadRepositories();
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

  // Keep this in lock-step with repairProgressLabels so the sidebar
  // task list and the in-session progress timeline speak the same
  // user-facing language. "Draft PR" / "草稿" / "自动修复" were
  // intentionally removed — see renderRepairProgress for context.
  const repairStatusLabels = {
    queued: '进入修复队列',
    cloning: '准备隔离工作区',
    analyzing: '读取 Issue 与代码',
    locating: '定位需要修改的位置',
    coding: 'AI 修改代码',
    verifying: '运行测试与验证',
    review_ready: '整理完整改动',
    publish_queued: '准备提交修复',
    publishing: '正在提交修复',
    completed: '修复已提交',
    failed: '修复已停止',
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
    const historyStatuses = ['completed', 'failed'];
    const activeJobs = jobs.filter((job) => !historyStatuses.includes(job.status));
    const historyJobs = jobs.filter((job) => historyStatuses.includes(job.status));
    if (repairTaskCount) {
      repairTaskCount.textContent = String(activeJobs.length || jobs.length);
      repairTaskCount.title = `${activeJobs.length} 个进行中${historyJobs.length ? `，${historyJobs.length} 个历史任务` : ''}`;
    }
    if (repairTaskToggle) {
      repairTaskToggle.hidden = !historyJobs.length;
      repairTaskToggle.textContent = showRepairHistory ? '收起历史' : `查看历史 (${historyJobs.length})`;
      repairTaskToggle.setAttribute('aria-expanded', String(showRepairHistory));
    }
    if (!jobs.length) {
      repairTaskList.innerHTML = '<div class="task-empty">还没有修复任务。<br>从 Issue 开始一个。</div>';
      return;
    }
    const visibleJobs = (showRepairHistory ? jobs : activeJobs).slice(0, 30);
    if (!visibleJobs.length) {
      repairTaskList.innerHTML = '<div class="task-empty">暂无进行中的任务。<br>历史任务已收起。</div>';
      return;
    }
    repairTaskList.innerHTML = visibleJobs.map((job) => {
      const selected = currentRepairJob?.id === job.id ? ' active' : '';
      const title = job.issue_title || `Issue #${job.issue_number}`;
      const status = repairStatusLabels[job.status] || job.status || '未知状态';
      const failedClass = job.status === 'failed' ? ' failed' : '';
      return `<button class="task-item${selected}${failedClass}" type="button" data-repair-job="${escapeHtml(job.id)}"><span class="task-item-dot ${repairTaskClass(job.status)}"></span><span><span class="task-item-title">${escapeHtml(title)}</span><span class="task-item-meta"><span>${escapeHtml(job.repository || '')} · #${escapeHtml(job.issue_number || '')}</span><span>${escapeHtml(status)}</span></span></span></button>`;
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
    document.querySelector('.app-shell')?.classList.add('repair-open');
    if (scroller) scroller.hidden = true;
  };

  const closeRepairInspector = () => {
    if (!repairDialog) return;
    repairDialog.hidden = true;
    document.querySelector('.app-shell')?.classList.remove('repair-open');
    if (scroller) scroller.hidden = false;
    window.clearTimeout(repairPollTimer);
  };

  const setRepairPhase = (status, job = null) => {
    const order = ['read', 'locate', 'modify', 'verify', 'review'];
    repairDialog?.classList.toggle('repair-failed', status === 'failed');
    const current = status === 'failed'
      ? ''
      : ['queued', 'cloning'].includes(status)
      ? 'read'
      : (['analyzing', 'locating'].includes(status)
        ? 'locate'
        : (status === 'coding'
          ? 'modify'
          : (status === 'verifying' ? 'verify' : 'review')));
    const currentIndex = order.indexOf(current);
    const verification = repairVerification(job);
    qsa('[data-repair-phase]', repairDialog).forEach((element) => {
      const index = order.indexOf(element.dataset.repairPhase);
      element.classList.toggle('active', index === currentIndex);
      const isVerify = element.dataset.repairPhase === 'verify';
      const isComplete = index < currentIndex || status === 'completed';
      element.classList.toggle('complete', isVerify ? (verification.status === 'passed') : isComplete);
      if (isVerify && ['review_ready', 'completed'].includes(status)) {
        element.dataset.verificationState = verification.status;
      } else {
        delete element.dataset.verificationState;
      }
    });
  };

  // 失败 UI 客户端分类. 优先用后端塞的 last_error_diagnosis; 没有时按
  // 同一份 regex 跑一次 (跟 src/main.py 的 _DIAGNOSTIC_PATTERNS 镜像).
  // 维护建议: 后端 regex 改了, 同步改这里; 失配的话也会降级到 unknown.
  // 改 provider 抽象后, kind 集从 7 扩到 12 (claude_not_authenticated 删,
  // 加 api_key_invalid / api_connection_failed / model_not_found /
  // rate_limited / context_too_long / api_timeout / tool_call_failed).
  const CLIENT_DIAGNOSTIC_PATTERNS = [
    // 顺序敏感: 更具体的放前面. api_connection_failed 在 api_key_invalid 前面,
    // 避免 "Connection error: invalid api key" 这种文案被误判为 connection.
    [/connection[\s\S]{0,40}(refused|reset|closed|timeout)|ECONN|ENOTFOUND|getaddrinfo/i,
      'api_connection_failed', '检查 base_url 或网络', '无法连到 LLM 服务端，请检查 base_url 是否正确（OpenAI / DeepSeek / 自托管等）。'],
    [/api[_ ]?key[\s\S]{0,40}(invalid|incorrect|unauthorized|missing|expired)|invalid[_ ]?api[_ ]?key|incorrect api key|unauthorized[\s\S]{0,30}api/i,
      'api_key_invalid', '修改 Coding Agent 配置', 'API key 验证失败。打开 "Coding Agent" 对话框修改 key（key 存在 .ghe/config.yml，权限最低）。'],
    [/model[\s\S]{0,40}(not[_ ]?found|does not exist|invalid[_ ]?model|unknown[_ ]?model)|the model[\s\S]{0,30}does not exist/i,
      'model_not_found', '修改 Coding Agent 配置', '当前 provider 没有这个 model。打开 "Coding Agent" 对话框换成 provider 支持的 model 名。'],
    [/rate[_ ]?limit|too[_ ]?many[_ ]?requests|429[\s:]|quota[_ ]?exceeded/i,
      'rate_limited', '等几秒后重试', 'API 限流。等几秒再试一次，或者换一个 provider / 减少并发。'],
    [/context[\s\S]{0,30}(too[_ ]?long|length[_ ]?exceeded|window[_ ]?exceeded)|maximum[_ ]?context|token[_ ]?limit/i,
      'context_too_long', '缩小任务或换 model', '任务太大超出 context window。把 Issue 描述精简或换一个 context 更大的 model。'],
    [/api[_ ]?timeout|upstream[_ ]?timeout|request[_ ]?timed?[\s_]?out/i,
      'api_timeout', '重试一次', 'LLM 服务端超时。常见原因：网络抖或 model 响应慢，可直接重试。'],
    [/tool[_ ]?call[\s\S]{0,30}(fail|error)|function[_ ]?call[\s\S]{0,30}(fail|error)/i,
      'tool_call_failed', '查看完整日志', 'AI 调用工具失败。看 .ghe/repair-jobs/<id>.log 找具体是哪个 tool。'],
    [/gh[\s\S]*?(not\s+authenticated|auth\s+login)|gh:\s*not\s+logged\s+in/i,
      'gh_not_authenticated', '运行 `gh auth login --web`', 'GitHub CLI 未登录。匿名模式仍可克隆/修复公开仓库，但 Fork 和 PR 需要登录。'],
    [/test(s)?\s+failed|pytest[\s\S]*?fail|failed\s+(\d+\s+)?test|FAIL\s/i,
      'test_failed', '查看测试日志', 'AI 改完代码后，测试未通过。打开 .ghe/repair-jobs/<id>.log 找到失败用例。'],
    [/no\s+(code\s+)?diff|no\s+code\s+change|no\s+change\s+produced|produced\s+no\s+code\s+change|without\s+produc/i,
      'no_diff', 'AI 没生成可提交修改，重跑或调整指令', '编码 Agent 没有产生可提交的代码变更。'],
    [/permission\s+denied|EACCES|operation\s+not\s+permitted/i,
      'permission_denied', '检查目录权限或换路径', '子进程被操作系统拒绝访问。常见原因：workspace_root 路径不可写，或 git/gh 没有执行权限。'],
    [/timeout|timed?\s*out|TimeoutExpired|deadline\s+exceeded/i,
      'timeout', '重试一次或缩小任务范围', 'AI 或 git 子进程超过时间限制未结束。任务规模太大或网络/IO 卡住。'],
  ];
  const diagnoseRepairError = (message) => {
    const text = (message || '').trim();
    for (const [re, kind, action, hint] of CLIENT_DIAGNOSTIC_PATTERNS) {
      if (re.test(text)) return { error_kind: kind, error_action: action, hint };
    }
    return { error_kind: 'unknown', error_action: '查看完整错误日志', hint: '未匹配已知错误模式。打开 .ghe/repair-jobs/<id>.log 查看完整堆栈。' };
  };

  // 失败 UI: 按 error_kind 给不同卡片. 每个 kind 一种主色 + 图标.
  // 新版 12 种 kind, 颜色规则:
  //   - 红色 (danger): 需要用户改配置 / 看日志, 不修就不能继续
  //   - 琥珀 (amber): 临时问题, 等几秒 / 缩小任务就行
  //   - 灰色 (neutral): 不需要动作, 只能重试或自己看
  //   - 蓝 (info, 默认): 中性提示
  const renderFailureDetail = (job) => {
    const diagnosis = job.last_error_diagnosis || diagnoseRepairError(job.message || '');
    const kind = diagnosis.error_kind || 'unknown';
    const meta = {
      api_key_invalid: { icon: '🔑', tone: 'danger', title: 'API key 失效' },
      api_connection_failed: { icon: '🔌', tone: 'danger', title: '连不上 LLM 服务' },
      model_not_found: { icon: '📝', tone: 'danger', title: 'Model 不存在' },
      rate_limited: { icon: '⏱', tone: 'amber', title: 'API 限流' },
      context_too_long: { icon: '📏', tone: 'neutral', title: '任务超出 context' },
      api_timeout: { icon: '⏳', tone: 'amber', title: 'API 超时' },
      tool_call_failed: { icon: '🛠', tone: 'danger', title: '工具调用失败' },
      gh_not_authenticated: { icon: '🔗', tone: 'warning', title: 'GitHub 未连接' },
      test_failed: { icon: '🧪', tone: 'danger', title: '测试失败' },
      no_diff: { icon: '📝', tone: 'warning', title: 'AI 没生成修改' },
      permission_denied: { icon: '🔒', tone: 'danger', title: '权限被拒' },
      timeout: { icon: '⏱', tone: 'warning', title: '超时' },
      unknown: { icon: 'ℹ️', tone: 'neutral', title: '需要进一步查看' },
    }[kind] || { icon: 'ℹ️', tone: 'neutral', title: '未知错误' };
    const copyCommand = (cmd) =>
      `<button class="suggestion soft-suggestion" type="button" data-copy-command="${escapeHtml(cmd)}">复制：${escapeHtml(cmd)}</button>`;
    let cta = '';
    if (kind === 'api_key_invalid' || kind === 'model_not_found') {
      // 弹 Coding Agent 配置对话框, 让用户直接改 provider / key / model.
      cta = '<button class="suggestion soft-suggestion" type="button" data-open-coding-agent-setup>修改 Coding Agent 配置</button>';
    } else if (kind === 'api_connection_failed') {
      // base_url 多半是用户自托管 / 反代, 改 base_url 也走 coding-agent dialog.
      cta = '<button class="suggestion soft-suggestion" type="button" data-open-coding-agent-setup>修改 base_url / provider</button>';
    } else if (kind === 'rate_limited') {
      cta = '<button class="suggestion soft-suggestion" type="button" data-toggle-repair-log>查看详情</button><div class="repair-log" id="repair-log" hidden><pre>正在加载…</pre></div>';
    } else if (kind === 'context_too_long') {
      cta = '<button class="suggestion soft-suggestion" type="button" data-retry-with-instruction>精简 Issue 后重跑</button>';
    } else if (kind === 'api_timeout' || kind === 'tool_call_failed') {
      cta = '<button class="suggestion soft-suggestion" type="button" data-toggle-repair-log>查看日志</button><div class="repair-log" id="repair-log" hidden><pre>正在加载…</pre></div>';
    } else if (kind === 'gh_not_authenticated') {
      cta = '<button class="suggestion soft-suggestion" type="button" data-open-github-setup>立即连接 GitHub</button>';
    } else if (kind === 'test_failed') {
      cta = '<button class="suggestion soft-suggestion" type="button" data-toggle-repair-log>查看日志</button><div class="repair-log" id="repair-log" hidden><pre>正在加载…</pre></div>';
    } else if (kind === 'no_diff') {
      cta = '<button class="suggestion soft-suggestion" type="button" data-retry-with-instruction>调整指令后重跑</button>';
    } else {
      cta = '<button class="suggestion soft-suggestion" type="button" data-toggle-repair-log>查看详情</button><div class="repair-log" id="repair-log" hidden><pre>正在加载…</pre></div>';
    }
    return `<div class="repair-error-card tone-${meta.tone}">
      <strong>${meta.icon} ${escapeHtml(meta.title)}</strong>
      <span>${escapeHtml(diagnosis.error_action || '查看完整错误日志')}</span>
      <small>${escapeHtml(diagnosis.hint || '查看 .ghe/repair-jobs/<id>.log 找具体原因')}</small>
      <div class="suggestions">${cta}</div>
    </div>`;
  };

  const repairEvent = (role, title, body, output = '', tone = '') => `
    <section class="repair-event ${role}">
      <div class="repair-event-avatar">${role === 'user' ? '你' : 'GE'}</div>
      <div class="repair-event-body">
        <div class="repair-event-meta">${role === 'user' ? '你的指导' : escapeHtml(title)}</div>
        <div class="repair-event-card${tone ? ` tone-${tone}` : ''}">${body}${output ? `<div class="repair-output">${escapeHtml(output)}</div>` : ''}</div>
      </div>
    </section>`;

  const repairProgressLabels = {
    queued: '进入修复队列',
    cloning: '准备隔离工作区',
    analyzing: '读取 Issue 与代码',
    locating: '定位需要修改的位置',
    coding: 'AI 修改代码',
    verifying: '运行测试与验证',
    review_ready: '整理完整改动',
    publish_queued: '准备提交修复',
    publishing: '正在提交修复',
    completed: '修复已提交',
    failed: '修复已停止',
  };

  const fallbackRepairProgress = (job) => {
    const flow = ['queued', 'cloning', 'analyzing', 'coding', 'verifying', 'review_ready'];
    const aliases = { locating: 'analyzing', publish_queued: 'review_ready', publishing: 'review_ready', completed: 'review_ready' };
    const normalized = aliases[job?.status] || job?.status || 'queued';
    const currentIndex = Math.max(0, flow.indexOf(normalized));
    return flow.slice(0, currentIndex + 1).map((status, index) => ({
      status,
      message: index === currentIndex ? String(job?.message || '') : '',
      created_at: index === currentIndex ? job?.updated_at : '',
    }));
  };

  const renderRepairProgress = (job) => {
    const history = Array.isArray(job?.progress_history)
      ? job.progress_history.filter((item) => item && typeof item === 'object')
      : [];
    const entries = (history.length ? history : fallbackRepairProgress(job)).slice(-8);
    if (!entries.length) return '';
    const active = !['review_ready', 'completed', 'failed'].includes(job?.status);
    const rows = entries.map((entry, index) => {
      const status = String(entry.status || 'queued');
      const isLast = index === entries.length - 1;
      const state = status === 'failed' ? 'failed' : (isLast && active ? 'current' : 'done');
      const date = entry.created_at ? new Date(entry.created_at) : null;
      const time = date && !Number.isNaN(date.getTime())
        ? date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
        : '';
      return `<div class="repair-progress-item ${state}"><span class="repair-progress-dot"></span><span class="repair-progress-copy"><strong>${escapeHtml(repairProgressLabels[status] || repairStatusLabels[status] || status)}</strong>${entry.message ? `<span>${escapeHtml(entry.message)}</span>` : ''}</span>${time ? `<time class="repair-progress-time">${escapeHtml(time)}</time>` : ''}</div>`;
    }).join('');
    return `<div class="repair-live-progress" aria-label="实时修复过程"><div class="repair-live-progress-heading"><strong>修复过程</strong><span>${active ? '每 3 秒自动更新' : '过程记录'}</span></div><div class="repair-progress-list">${rows}</div></div>`;
  };

  const renderRepairSession = (job = null) => {
    if (!repairDialog || !repairStream || !currentRepairIssue) return;
    const previousJobId = String(currentRepairJob?.id || '');
    const nextJobId = String(job?.id || '');
    if (previousJobId !== nextJobId) {
      repairSessionGeneration += 1;
      publishGeneration += 1;
      cancelDiffLoad(nextJobId);
      window.clearTimeout(repairPollTimer);
      repairPublish?.removeAttribute('aria-busy');
    }
    const destination = '先查看完整改动，满意后再决定是否提交';
    repairRepository.textContent = `${currentRepairRepository || currentRepository} · #${currentRepairIssue.number}`;
    repairTitle.textContent = currentRepairIssue.title;
    repairDelivery.textContent = destination;
    currentRepairJob = job;
    showRepairInspector();
    if (!job) {
      // Opening a new issue can leave the previous repair's diff panel
      // visible. Reset to the conversation so the start card and its CTA are
      // not hidden behind stale diff content.
      hideDiffView();
      setRepairPhase('queued');
      const demoNotice = isDemoRepair()
        ? '<div class="repair-safety-note"><strong>演示模式</strong>fake Provider 只演示工作流，不代表 AI 理解了 Issue 或真正修复了代码；演示结果不能发布。</div>'
        : '';
      repairStream.innerHTML = repairEvent(
        'assistant',
        '修复计划',
        `<strong>${currentCanModify ? '准备修复' : '准备贡献修复'}</strong><br>AI 会读取代码、完成修改并运行验证。完成后你只需要查看改动，再决定是否提交。<div class="repair-safety-note"><strong>数据边界</strong>${escapeHtml(providerDataBoundary())}</div>${demoNotice}<div class="suggestions"><button class="suggestion primary-suggestion" type="button" data-start-repair>开始修复</button><a class="suggestion" href="${escapeHtml(currentRepairIssue.url)}" target="_blank" rel="noreferrer">查看 Issue</a></div>`,
      );
      repairGuidanceInput.disabled = true;
      repairGuidanceSend.disabled = true;
      if (repairSkipSubmit) repairSkipSubmit.hidden = true;
      repairPublish.disabled = true;
      return;
    }
    setRepairPhase(job.status, job);
    // 失败 UI 按 error_kind 分类. 后端在 job JSON 里塞了 last_error_diagnosis
    // (per-job). 优先用后端的, 兜底用客户端 regex 复刻一份.
    const failureAction = repairCapabilities?.available
      ? '<button class="suggestion primary-suggestion" type="button" data-retry-repair>重新运行</button>'
      : '<button class="suggestion primary-suggestion" type="button" data-open-repair-setup>完成自动修复设置</button>';
    const failureDetail = job.status === 'failed'
      ? renderFailureDetail(job)
      : '';
    const failureHelp = job.status === 'failed'
      ? `<div class="repair-error-detail">任务已经停止，也没有向外提交任何内容。完成下面的操作后可以安全地重新运行。</div>${failureDetail}<div class="suggestions">${failureAction}<a class="suggestion" href="${escapeHtml(currentRepairIssue.url)}" target="_blank" rel="noreferrer">查看 Issue</a></div>`
      : '';
    const failureMessage = /without producing a code change/i.test(job.message || '')
      ? '这次没有生成可提交的修改。完成下面的设置后，再重新运行一次。'
      : '这次修复没有完成。请按下面提示处理后重新运行。';
    const displayMessage = job.status === 'failed' ? failureMessage : (job.message || '');
    const verification = repairVerification(job);
    const hostVerificationCta = (
      job.status === 'review_ready'
      && verification.status === 'unverified'
      && verification.reason === 'sandbox_unavailable'
    )
      ? '<div class="repair-safety-note"><strong>需要你的明确许可</strong>本机验证会执行这个仓库里的测试代码，可能包含不可信逻辑。<div class="suggestions"><button class="suggestion primary-suggestion" type="button" data-allow-host-verification>我理解风险，在本机运行测试</button></div></div>'
      : '';
    const events = [
      repairEvent(
        'assistant',
        repairStatusLabels[job.status] || '修复会话',
        `<strong>${escapeHtml(repairStatusLabels[job.status] || job.status)}</strong><br>${escapeHtml(displayMessage)}${renderRepairProgress(job)}${failureHelp}${renderVerification(job)}${hostVerificationCta}${isDemoRepair(job) ? '<div class="repair-safety-note"><strong>演示任务不可提交</strong>演示内容仅供体验界面，不会提交到 GitHub。</div>' : ''}`,
        '',
        job.status === 'failed' ? 'error' : '',
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
        '修复草稿',
        `<strong>修复已经提交</strong><br>是否合并由原仓库管理员决定。<div class="suggestions"><a class="suggestion primary-suggestion" href="${escapeHtml(job.pr_url)}" target="_blank" rel="noreferrer">查看提交结果</a></div>`,
      ));
    }
    repairStream.innerHTML = events.join('');
    renderRepairTaskList(repairJobs);
    const canRevise = job.status === 'review_ready';
    repairGuidanceInput.disabled = !canRevise;
    repairGuidanceSend.disabled = !canRevise;
    if (repairSkipSubmit) repairSkipSubmit.hidden = !canRevise;
    // diff 加载完成后，用户只需决定是否提交整份修复。
    repairPublish.disabled = true;
    const demo = isDemoRepair(job);
    repairPublish.textContent = demo
      ? '演示任务不可提交'
      : (verification.status !== 'passed'
        ? (verification.status === 'failed' ? '修复未通过验证' : '等待验证')
        : (canRevise ? '正在加载改动…' : '提交修复'));
    repairPublish.title = demo
      ? '演示内容不会提交到 GitHub'
      : (verification.status !== 'passed' ? '需要明确的测试或验证通过结果' : '');
    repairStream.scrollTop = repairStream.scrollHeight;
    // 跑完默认弹 diff 视图 (status === review_ready).
    // 失败状态不弹 — 走结构化失败 UI, 不把用户引到空 diff 上去.
    if (job.status === 'review_ready') {
      loadAndRenderDiff(job);
    } else {
      cancelDiffLoad(nextJobId);
      hideDiffView();
    }
  };

  const pollRepairJob = async (jobId, sessionGeneration = repairSessionGeneration) => {
    window.clearTimeout(repairPollTimer);
    try {
      const job = await fetchJson(`/api/repairs/${encodeURIComponent(jobId)}`);
      if (
        sessionGeneration !== repairSessionGeneration
        || String(currentRepairJob?.id || '') !== String(jobId)
      ) return;
      renderRepairSession(job);
      await loadRepairJobs();
      if (sessionGeneration !== repairSessionGeneration) return;
      if (!['review_ready', 'completed', 'failed'].includes(job.status)) {
        repairPollTimer = window.setTimeout(
          () => pollRepairJob(jobId, sessionGeneration),
          3000,
        );
      }
    } catch (error) {
      if (sessionGeneration !== repairSessionGeneration) return;
      if (repairStream) {
        repairStream.innerHTML = repairEvent(
          'assistant',
          '状态读取失败',
          escapeHtml(error.message || '稍后可以重新打开会话检查'),
        );
      }
    }
  };

  // ===========================================================================
  // Diff view (CodeMirror 6 unified-diff renderer)
  //
  // 当 job.status === review_ready 时，自动展示完整 diff，供用户检查后整份提交。
  // 底层仍保留分段数据，用于提交前的完整性确认。代码视图沿用以下
  // 五条避坑经验:
  //
  //   1. importmap 显式 pin 所有 transitive deps (state / view / lezer / crelt /
  //      style-mod / w3c-keyname), 不让 esm.sh 给我们 create 多份 state.
  //   2. 不挂 StateField + line decoration + 大量 scroll: 直接走 paintAllLines
  //      走 DOM, scroll 事件 60ms debounce, 避免 findPos crash.
  //   3. 不挂 Decoration.widget: hunk 头不进 doc, 走右侧 HTML 卡片.
  //   4. 不挂 lang-python: 文本模式足够, 少 80KB bundle.
  //   5. 不开 lineWrapping: 长行靠水平滚动, 避开 docView 重算 crash.
  // ===========================================================================

  let _diffViewLoaded = false;
  let _diffViewPromise = null;
  let _diffViewModule = null;  // { EditorView, EditorState, lineNumbers, highlightActiveLine, highlightActiveLineGutter, Decoration, StateEffect, RangeSetBuilder, StateField }
  let _diffEditorView = null;
  let _diffData = null;        // 当前展示的 diff envelope (从 /api/repairs/<id>/diff)
  let _diffHunkStatuses = {};  // {<gid>: "pending"|"accepted"|"rejected"}
  let _diffActiveHunkId = null;
  let _diffPaintTimer = null;
  let _diffLoadGeneration = 0;
  let _diffLoadController = null;
  let _diffJobId = '';
  let _decisionWriteTail = Promise.resolve();
  const _decisionVersions = new Map();
  const _decisionPendingByJob = new Map();

  const pendingDecisionWrites = (jobId) => Number(_decisionPendingByJob.get(jobId) || 0);

  const cancelDiffLoad = (nextJobId = '') => {
    _diffLoadGeneration += 1;
    _diffLoadController?.abort();
    _diffLoadController = null;
    _diffJobId = String(nextJobId || '');
  };

  const DIFF_IMPORTMAP_ID = 'ghe-diff-importmap';
  const DIFF_IMPORTMAP = {
    imports: {
      "@codemirror/state": "https://cdn.jsdelivr.net/npm/@codemirror/state@6.4.1/+esm",
      "@codemirror/view": "https://cdn.jsdelivr.net/npm/@codemirror/view@6.34.1/+esm",
      "@lezer/highlight": "https://cdn.jsdelivr.net/npm/@lezer/highlight@1.2.0/+esm",
      "@lezer/common": "https://cdn.jsdelivr.net/npm/@lezer/common@1.2.1/+esm",
      "@lezer/lr": "https://cdn.jsdelivr.net/npm/@lezer/lr@1.4.0/+esm",
      "crelt": "https://cdn.jsdelivr.net/npm/crelt@1.0.6/+esm",
      "style-mod": "https://cdn.jsdelivr.net/npm/style-mod@4.1.0/+esm",
      "w3c-keyname": "https://cdn.jsdelivr.net/npm/w3c-keyname@2.2.8/+esm",
    },
  };

  const ensureDiffViewAssets = () => {
    if (_diffViewLoaded || _diffViewPromise) return _diffViewPromise;
    // 1) 注入 importmap. 已经在 main HTML 里就不重复注入.
    if (!document.getElementById(DIFF_IMPORTMAP_ID)) {
      const script = document.createElement('script');
      script.id = DIFF_IMPORTMAP_ID;
      script.type = 'importmap';
      script.textContent = JSON.stringify(DIFF_IMPORTMAP);
      document.head.appendChild(script);
    }
    // 2) 用 type=module 动态 import — importmap 在同一 document 必须先注册,
    //    所以这里串行 await, 不会和 importmap 注入产生竞态.
    _diffViewPromise = import(
      /* @vite-ignore */ './diff-view-client.js'
    ).then((mod) => {
      _diffViewModule = mod;
      _diffViewLoaded = true;
      return mod;
    }).catch((error) => {
      _diffViewPromise = null;
      throw error;
    });
    return _diffViewPromise;
  };

  const hideDiffView = () => {
    if (diffView) diffView.hidden = true;
    if (repairStream) repairStream.hidden = false;
  };

  const showDiffView = () => {
    if (repairStream) repairStream.hidden = true;
    if (diffView) diffView.hidden = false;
  };

  const updateDiffCtaStatus = () => {
    const activeJobId = String(currentRepairJob?.id || '');
    const total = Object.keys(_diffHunkStatuses).length;
    const demo = isDemoRepair(currentRepairJob);
    const providerSafe = providerAllowsPublishing(currentRepairJob);
    const verification = repairVerification(currentRepairJob);
    const missingTools = missingVerificationTools(currentRepairJob);
    const canRequestHostVerification = (
      currentRepairJob?.status === 'review_ready'
      && verification.status === 'unverified'
      && verification.reason === 'sandbox_unavailable'
    );
    const readyToPublish = (
      currentRepairJob?.status === 'review_ready'
      && providerSafe
      && verification.status === 'passed'
      && total > 0
      && _diffJobId === activeJobId
    );
    if (diffViewStatus) {
      if (total === 0) {
        diffViewStatus.textContent = '没有可提交的代码修改';
      } else if (verification.status !== 'passed') {
        diffViewStatus.textContent = '以上是完整代码修改 · 验证通过后可选择提交';
      } else {
        diffViewStatus.textContent = '以上是将要提交的完整修改 · 提交后是否合并由原仓库管理员决定';
      }
    }
    if (repairPublish) {
      repairPublish.disabled = !(readyToPublish || canRequestHostVerification);
      if (demo) {
        repairPublish.textContent = '演示任务不可提交';
        repairPublish.title = '演示内容不会提交到 GitHub';
      } else if (!providerSafe) {
        repairPublish.textContent = '当前任务不可提交';
        repairPublish.title = '任务必须记录一个明确的非演示 Provider';
      } else if (verification.status === 'failed') {
        repairPublish.textContent = missingTools.length
          ? `缺少 ${missingTools.map(verificationToolLabel).join('、')}，暂不能提交`
          : '修复未通过验证';
        repairPublish.title = missingTools.length
          ? '测试工具未安装，代码仍可 Review；完成验证后可以提交'
          : '修复测试或验证未通过';
      } else if (canRequestHostVerification) {
        repairPublish.textContent = '在本机运行测试…';
        repairPublish.title = '将先确认风险，再执行仓库里的测试代码';
      } else if (verification.status !== 'passed') {
        repairPublish.textContent = '等待验证';
        repairPublish.title = '需要明确的测试或验证通过结果';
      } else if (total === 0) {
        repairPublish.textContent = '没有可提交的修改';
        repairPublish.title = '当前任务没有生成代码差异';
      } else if (!currentGithubAuthenticated) {
        repairPublish.textContent = '连接 GitHub 后提交';
        repairPublish.title = '点击连接 GitHub，然后提交这份完整修复';
      } else {
        repairPublish.textContent = '提交修复';
        repairPublish.title = '提交这份完整修复；是否合并由原仓库管理员决定';
      }
    }
  };

  const setHunkStatus = (hunkId, status) => {
    const jobId = String(currentRepairJob?.id || '');
    if (!jobId || _diffJobId !== jobId || !_diffData) return;
    const prev = _diffHunkStatuses[hunkId];
    if (prev === status) return;
    _diffHunkStatuses[hunkId] = status;
    const hunk = (_diffData.files || []).flatMap((f) => f.hunks).find((x) => x.id === hunkId);
    if (!hunk) return;
    // sidebar card update
    const card = diffViewSidebar?.querySelector(`.diff-hunk-card[data-hunk-id="${hunkId}"]`);
    if (card) {
      card.classList.toggle('accepted', status === 'accepted');
      card.classList.toggle('rejected', status === 'rejected');
      const statusEl = card.querySelector('.diff-hunk-card-status');
      if (statusEl) {
        statusEl.className = `diff-hunk-card-status diff-hunk-card-status-${status}`;
        statusEl.textContent = status === 'pending' ? '待处理' : (status === 'accepted' ? '✓ 已接受' : '✕ 已拒绝');
      }
    }
    // editor hunk-line update
    if (_diffEditorView) {
      const lines = _diffEditorView.contentDOM.querySelectorAll('.cm-line.diff-hunk');
      for (const el of lines) {
        const text = el.textContent || '';
        const m = text.match(/@@\s*-\d+[^@]*@@/);
        if (m && m[0] === hunk.header) {
          el.classList.remove('diff-hunk-pending', 'diff-hunk-accepted', 'diff-hunk-rejected');
          el.classList.add('diff-hunk-' + status);
        }
      }
    }
    updateDiffCtaStatus();
    // 写回后端. 即使中途用户连接 GitHub, 之前的 decision 也保留.
    if (currentRepairJob) {
      const key = `${jobId}:${hunkId}`;
      const version = Number(_decisionVersions.get(key) || 0) + 1;
      _decisionVersions.set(key, version);
      _decisionPendingByJob.set(jobId, pendingDecisionWrites(jobId) + 1);
      updateDiffCtaStatus();
      const write = _decisionWriteTail
        .catch(() => {})
        .then(() => fetchJson(`/api/repairs/${encodeURIComponent(jobId)}/hunk-decision`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ hunk_id: String(hunkId), decision: status }),
      }));
      // 所有 hunk 共用一条队列，accept/reject all 也按顺序写回，避免并发
      // 请求在后端乱序落盘。
      _decisionWriteTail = write.catch(() => {});
      write.catch((error) => {
        const isLatest = _decisionVersions.get(key) === version;
        const isActiveJob = _diffJobId === jobId && String(currentRepairJob?.id || '') === jobId;
        if (isLatest && isActiveJob && _diffHunkStatuses[hunkId] === status) {
          _diffHunkStatuses[hunkId] = prev || 'pending';
          showToast(`审核结果保存失败：${error.message || '请重试'}`);
        }
      }).finally(() => {
        _decisionPendingByJob.set(jobId, Math.max(0, pendingDecisionWrites(jobId) - 1));
        if (_diffJobId === jobId && String(currentRepairJob?.id || '') === jobId) {
          renderDiffSidebar();
          updateDiffCtaStatus();
        }
      });
    }
  };

  const confirmFullDiffForSubmission = async (jobId) => {
    const hunks = (_diffData?.files || []).flatMap((file) => file.hunks || []);
    if (!hunks.length || _diffJobId !== jobId) {
      throw new Error('当前没有可提交的修改');
    }
    // “提交修复”代表提交当前看到的整份 patch。后端仍记录完整确认，
    // 但不再让用户逐段维护接受/拒绝状态。
    for (const hunk of hunks) {
      if (_diffHunkStatuses[hunk.id] === 'accepted') continue;
      await fetchJson(`/api/repairs/${encodeURIComponent(jobId)}/hunk-decision`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ hunk_id: String(hunk.id), decision: 'accepted' }),
      });
      _diffHunkStatuses[hunk.id] = 'accepted';
    }
  };

  const renderDiffSidebar = () => {
    if (!diffViewSidebar) return;
    const hunks = (_diffData?.files || []).flatMap((f) =>
      f.hunks.map((h) => ({ ...h, filePath: f.path }))
    );
    if (!hunks.length) {
      diffViewSidebar.innerHTML = '<div class="diff-view-empty"><span class="title">没有生成代码修改</span><span>没有可审核或可提交的 diff；这不代表 Issue 已经修复。</span></div>';
      return;
    }
    diffViewSidebar.innerHTML = hunks.map((h) => {
      const status = _diffHunkStatuses[h.id] || 'pending';
      return `<div class="diff-hunk-card" data-hunk-id="${h.id}" data-hunk-header="${escapeHtml(h.header)}">
        <div class="diff-hunk-card-header">
          <span>${escapeHtml(h.header)}</span>
          <span class="diff-hunk-card-status diff-hunk-card-status-${status}">${status === 'pending' ? '待处理' : (status === 'accepted' ? '✓ 已接受' : '✕ 已拒绝')}</span>
        </div>
        <div class="diff-hunk-card-file">${escapeHtml(h.filePath)}</div>
        <div class="diff-hunk-card-stats"><span class="add">+${h.adds}</span><span class="rem">−${h.rems}</span></div>
        <div class="diff-hunk-card-actions">
          <button class="hunk-btn hunk-btn-accept" type="button" data-hunk-action="accept" data-hunk-id="${h.id}">接受</button>
          <button class="hunk-btn hunk-btn-reject" type="button" data-hunk-action="reject" data-hunk-id="${h.id}">拒绝</button>
        </div>
      </div>`;
    }).join('');
  };

  // 直接 walk cm-line, 不挂 StateField (坑 #2 避坑).
  const paintDiffLines = () => {
    if (!_diffEditorView || !_diffData) return;
    const metaLines = _buildDiffDoc(_diffData).meta;
    const lines = _diffEditorView.contentDOM.querySelectorAll('.cm-line');
    let metaIdx = 0;
    for (const el of lines) {
      if (el.dataset.painted === '1') continue;
      el.dataset.painted = '1';
      const text = el.textContent || '';
      if (text.startsWith('@@')) {
        const m = text.match(/^@@\s*-\d+[^@]*@@/);
        if (m) {
          const h = (_diffData.files || []).flatMap((f) => f.hunks).find((x) => x.header === m[0]);
          if (h) {
            const status = _diffHunkStatuses[h.id] || 'pending';
            el.dataset.hunkId = h.id;
            el.classList.add('diff-hunk', 'diff-hunk-' + status);
            if (h.id === _diffActiveHunkId) el.classList.add('diff-hunk-active');
          }
        }
        while (metaIdx < metaLines.length && metaLines[metaIdx].type !== 'hunk') metaIdx++;
        if (metaIdx < metaLines.length) metaIdx++;
        continue;
      }
      if (text.startsWith('diff --git') || text.startsWith('--- ') || text.startsWith('+++ ')) {
        while (metaIdx < metaLines.length && (metaLines[metaIdx].type === 'diff' || metaLines[metaIdx].type === 'file')) metaIdx++;
        continue;
      }
      while (metaIdx < metaLines.length) {
        const t = metaLines[metaIdx].type;
        if (t === 'add' || t === 'rem' || t === 'ctx') break;
        metaIdx++;
      }
      if (metaIdx >= metaLines.length) break;
      el.classList.add('diff-' + metaLines[metaIdx].type);
      metaIdx++;
    }
  };

  const scheduleDiffPaint = (delay = 60) => {
    if (_diffPaintTimer) clearTimeout(_diffPaintTimer);
    _diffPaintTimer = setTimeout(() => {
      _diffPaintTimer = null;
      if (_diffEditorView) {
        for (const el of _diffEditorView.contentDOM.querySelectorAll('.cm-line')) {
          delete el.dataset.painted;
        }
        paintDiffLines();
      }
    }, delay);
  };

  const _buildDiffDoc = (diffData) => {
    // doc = unified-diff 文本. meta 数组平行 doc 行, 描述每行的 type / hunkId.
    const lines = [];
    const meta = [];
    for (const file of diffData.files || []) {
      lines.push(`diff --git a/${file.path} b/${file.path}`);
      meta.push({ type: 'diff' });
      lines.push(`--- a/${file.path}`);
      meta.push({ type: 'file' });
      lines.push(`+++ b/${file.path}`);
      meta.push({ type: 'file' });
      for (const hunk of file.hunks) {
        lines.push(hunk.header);
        meta.push({ type: 'hunk', hunkId: hunk.id });
        for (const ln of hunk.lines) {
          const prefix = ln.type === 'add' ? '+' : (ln.type === 'remove' ? '-' : ' ');
          lines.push(prefix + (ln.text || ''));
          meta.push({ type: ln.type, hunkId: hunk.id });
        }
      }
    }
    return { doc: lines.join('\n'), meta };
  };

  const mountDiffEditor = async (diffData, isCurrentRequest = () => true) => {
    let mod;
    try {
      mod = await ensureDiffViewAssets();
    } catch (_) {
      if (!isCurrentRequest() || !diffViewEditor) return false;
      // Code review is a core desktop workflow, so a CDN outage must only
      // remove the enhanced editor—not hunk decisions or publish gating.
      // The unified diff is still escaped and rendered locally, while the
      // existing sidebar remains fully interactive.
      const { doc } = _buildDiffDoc(diffData);
      if (_diffEditorView) {
        _diffEditorView.destroy();
        _diffEditorView = null;
      }
      diffViewEditor.innerHTML = `<div class="diff-view-fallback-note" role="status">增强代码视图暂时不可用，已显示离线文本改动。</div><pre class="diff-view-plain">${escapeHtml(doc)}</pre>`;
      return true;
    }
    if (!isCurrentRequest() || !mod || !diffViewEditor) return false;
    // 如果有上一份, 先销毁
    if (_diffEditorView) {
      _diffEditorView.destroy();
      _diffEditorView = null;
    }
    const { doc } = _buildDiffDoc(diffData);
    const state = mod.EditorState.create({
      doc,
      extensions: [
        mod.lineNumbers(),
        mod.EditorState.readOnly.of(true),
        mod.EditorView.theme({
          '&': { color: 'inherit', backgroundColor: 'transparent' },
          '.cm-content': { caretColor: 'transparent' },
          '.cm-gutters': { backgroundColor: 'transparent' },
          '.cm-lineNumbers .cm-gutterElement': { color: 'inherit', fontSize: '10.5px' },
        }, { dark: true }),
      ],
    });
    diffViewEditor.innerHTML = '';
    _diffEditorView = new mod.EditorView({ state, parent: diffViewEditor });
    // 多次 paint, 兜住 CM6 lazy viewport
    scheduleDiffPaint(50);
    scheduleDiffPaint(200);
    scheduleDiffPaint(500);
    // 滚到第一个 hunk
    if (typeof mod.EditorView.scrollIntoView === 'function') {
      try {
        const firstHunk = (diffData.files || [])[0]?.hunks?.[0];
        if (firstHunk) {
          const headerIdx = _buildDiffDoc(diffData).meta.findIndex((m) => m.type === 'hunk' && m.hunkId === firstHunk.id);
          if (headerIdx >= 0) {
            const ln = _diffEditorView.state.doc.line(headerIdx + 1);
            _diffEditorView.dispatch({ effects: mod.EditorView.scrollIntoView(ln.from, { y: 'center' }) });
          }
        }
      } catch (_) { /* ignore */ }
    }
    _diffEditorView.scrollDOM.addEventListener('scroll', () => scheduleDiffPaint(80));
    return true;
  };

  const loadAndRenderDiff = async (job) => {
    if (!diffView) return;
    const jobId = String(job?.id || '');
    if (!jobId) return;
    if (diffViewOverview) diffViewOverview.scrollTop = 0;
    if (diffViewVerification) diffViewVerification.innerHTML = renderDiffVerification(job);
    if (diffViewSummary) {
      diffViewSummary.textContent = job.agent_summary || 'AI 已完成修改。下面是将要提交的完整代码改动。';
    }
    _diffLoadController?.abort();
    const controller = new AbortController();
    _diffLoadController = controller;
    const generation = ++_diffLoadGeneration;
    _diffJobId = jobId;
    const isCurrentRequest = () => (
      generation === _diffLoadGeneration
      && _diffJobId === jobId
      && String(currentRepairJob?.id || '') === jobId
      && !controller.signal.aborted
    );
    try {
      const diff = await fetchJson(`/api/repairs/${encodeURIComponent(jobId)}/diff`, {
        signal: controller.signal,
      });
      if (!isCurrentRequest()) return;
      _diffData = diff;
      // 从 server-side 持久化的 decisions 恢复 (刷新 / 重连都不丢)
      _diffHunkStatuses = {};
      const serverDecisions = diff.decisions || {};
      const allHunks = (diff.files || []).flatMap((f) => f.hunks);
      for (const h of allHunks) {
        _diffHunkStatuses[h.id] = serverDecisions[String(h.id)] || 'pending';
      }
      // 计算 adds/rems
      for (const file of diff.files || []) {
        for (const hunk of file.hunks) {
          hunk.adds = hunk.lines.filter((l) => l.type === 'add').length;
          hunk.rems = hunk.lines.filter((l) => l.type === 'remove').length;
        }
      }
      const totalHunks = allHunks.length;
      const summary = diff.summary || { files: 0, hunks: 0, adds: 0, rems: 0 };
      if (diffViewTitle) diffViewTitle.textContent = '修复内容';
      if (diffViewStats) {
        diffViewStats.innerHTML = `<span>${summary.files} 个文件</span> · <span class="add">新增 ${summary.adds}</span> · <span class="rem">删除 ${summary.rems}</span>`;
      }
      // 空 diff: 显示空态, 不强行让 CodeMirror 渲染 0 行
      if (totalHunks === 0) {
        const workspaceMissing = (
          job.workspace_exists === false
          || job.workspace_missing === true
          || /workspace.*(missing|not found|不存在|丢失)/i.test(String(job.message || ''))
        );
        const emptyTitle = workspaceMissing ? '历史任务的工作区已经不存在' : '这次没有生成代码修改';
        const emptyDetail = workspaceMissing
          ? '本地工作区或修复产物已被清理，无法恢复 diff。请从 Issue 重新发起分析。'
          : '没有可查看或可提交的代码改动。这不代表 Issue 已经修复，请调整说明后重新运行。';
        if (diffViewEditor) diffViewEditor.innerHTML = `<div class="diff-view-empty"><span class="title">${emptyTitle}</span><span>${emptyDetail}</span></div>`;
        if (diffViewSidebar) diffViewSidebar.innerHTML = '';
        _diffEditorView = null;
        updateDiffCtaStatus();
        showDiffView();
        return;
      }
      _diffActiveHunkId = allHunks[0]?.id ?? null;
      renderDiffSidebar();
      const mounted = await mountDiffEditor(diff, isCurrentRequest);
      if (!mounted || !isCurrentRequest()) return;
      updateDiffCtaStatus();
      showDiffView();
    } catch (error) {
      if (error.name === 'AbortError' || !isCurrentRequest()) return;
      _diffData = null;
      _diffHunkStatuses = {};
      updateDiffCtaStatus();
      const workspaceMissing = /(?:workspace|工作区).*(?:missing|not found|不存在|丢失)|\\b404\\b/i.test(String(error.message || ''));
      if (diffViewStats) diffViewStats.textContent = workspaceMissing ? '工作区已不存在' : 'diff 加载失败';
      if (diffViewEditor) {
        diffViewEditor.innerHTML = workspaceMissing
          ? '<div class="diff-view-empty"><span class="title">历史任务的工作区已经不存在</span><span>本地工作区或修复产物已被清理，请从 Issue 重新发起分析。</span></div>'
          : `<div class="diff-view-empty"><span class="title">无法加载 diff</span><span>${escapeHtml(error.message || '稍后重试')}</span></div>`;
      }
      showDiffView();
    } finally {
      if (generation === _diffLoadGeneration) _diffLoadController = null;
    }
  };

  // 模态框: 继续对话
  const openDiffChatDialog = () => {
    if (!diffChatDialog || !diffChatInput) return;
    diffChatInput.value = '';
    diffChatDialog.showModal();
    setTimeout(() => diffChatInput.focus(), 30);
  };
  const closeDiffChatDialog = () => diffChatDialog?.close();
  const sendDiffChat = async () => {
    if (!diffChatDialog || !diffChatInput || !currentRepairJob) return;
    const jobId = String(currentRepairJob.id || '');
    const sessionGeneration = repairSessionGeneration;
    const text = diffChatInput.value.trim();
    if (!text) return;
    diffChatSend.disabled = true;
    diffChatSend.textContent = '发送中…';
    try {
      // 复用现有 /api/repairs/<id>/guidance endpoint, 不另起一个.
      const result = await fetchJson(`/api/repairs/${encodeURIComponent(jobId)}/guidance`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      });
      if (
        sessionGeneration !== repairSessionGeneration
        || String(currentRepairJob?.id || '') !== jobId
      ) return;
      closeDiffChatDialog();
      hideDiffView();
      renderRepairSession(result);
      pollRepairJob(result.id);
      showToast('已记录你的反馈，AI 正在按指导修订');
    } catch (error) {
      if (sessionGeneration === repairSessionGeneration) {
        showToast(error.message || '发送失败');
      }
    } finally {
      if (sessionGeneration === repairSessionGeneration) {
        diffChatSend.disabled = false;
        diffChatSend.textContent = '发送 → 修订';
      }
    }
  };

  // 在 VS Code 打开产物: 复用 prototype 的平台检测.
  // - Tauri 环境: 用 @tauri-apps/api 的 invoke 调 tauri command (未来加).
  // - 浏览器环境: 用 vscode:// URI 协议; macOS / Windows 都支持.
  // - 没 workspace 时: 提示用户.
  const openWorkspaceInVSCode = async () => {
    if (!_diffData) {
      showToast('没有可打开的产物');
      return;
    }
    // 通过 /api/repairs/<id> 拿一下 workspace 路径 (后端 safe filter 不返这个,
    // 所以走专用的路径: 直接 GET /api/repairs/<id>/workspace).
    try {
      const ws = await fetchJson(`/api/repairs/${encodeURIComponent(currentRepairJob.id)}/workspace`);
      const path = ws?.workspace || '';
      if (!path) {
        showToast('这次任务没有可打开的工作目录');
        return;
      }
      const encoded = encodeURIComponent(path);
      const isMac = /Mac/i.test(navigator.platform || '');
      const isWin = /Win/i.test(navigator.platform || '');
      if (isMac || isWin) {
        window.location.href = `vscode://file${path.startsWith('/') ? path : '/' + path}`;
      } else {
        // linux / 其他: 复制路径到剪贴板
        try {
          await navigator.clipboard.writeText(path);
          showToast(`已复制路径: ${path}`);
        } catch (_) {
          showToast(path);
        }
      }
    } catch (error) {
      // 端点不存在时, 退回到本地模式: 让用户知道产物在哪里
      showToast('暂未找到工作目录 API, 可以从终端打开 .ghe/repair-workspaces/');
    }
  };

  // Diff 快捷键统一要求 Alt+Shift，避免单字符键影响语音输入、读屏器
  // 快捷导航或普通页面操作（WCAG 2.1.4）。
  document.addEventListener('keydown', (event) => {
    if (!diffView || diffView.hidden) return;
    const tag = (event.target?.tagName || '').toUpperCase();
    if (tag === 'TEXTAREA' || tag === 'INPUT') return;
    if (!event.altKey || !event.shiftKey || event.metaKey || event.ctrlKey) return;
    const k = (event.key || '').toLowerCase();
    if (k === 'a') {
      event.preventDefault();
      if (diffAcceptAll) diffAcceptAll.click();
    } else if (k === 'r') {
      event.preventDefault();
      if (diffRejectAll) diffRejectAll.click();
    } else if (k === 'c') {
      event.preventDefault();
      if (diffContinueChat) diffContinueChat.click();
    } else if (k === 'j' || k === 'n' || k === 'arrowdown') {
      if (!_diffData) return;
      event.preventDefault();
      const allHunks = (_diffData.files || []).flatMap((f) => f.hunks);
      const idx = allHunks.findIndex((h) => h.id === _diffActiveHunkId);
      if (idx >= 0 && idx < allHunks.length - 1) {
        _diffActiveHunkId = allHunks[idx + 1].id;
        // 重渲染 sidebar active state
        if (diffViewSidebar) {
          for (const c of diffViewSidebar.querySelectorAll('.diff-hunk-card')) {
            c.classList.toggle('active', Number(c.dataset.hunkId) === _diffActiveHunkId);
          }
        }
      }
    } else if (k === 'k' || k === 'p' || k === 'arrowup') {
      if (!_diffData) return;
      event.preventDefault();
      const allHunks = (_diffData.files || []).flatMap((f) => f.hunks);
      const idx = allHunks.findIndex((h) => h.id === _diffActiveHunkId);
      if (idx > 0) {
        _diffActiveHunkId = allHunks[idx - 1].id;
        if (diffViewSidebar) {
          for (const c of diffViewSidebar.querySelectorAll('.diff-hunk-card')) {
            c.classList.toggle('active', Number(c.dataset.hunkId) === _diffActiveHunkId);
          }
        }
      }
    }
  });

  const presentIssueCommand = async (issue, instruction) => {
    repairSessionGeneration += 1;
    publishGeneration += 1;
    cancelDiffLoad('');
    window.clearTimeout(repairPollTimer);
    repairPublish?.removeAttribute('aria-busy');
    currentRepairIssue = issue;
    currentRepairRepository = currentRepository;
    pendingIssueTask = {
      repository: currentRepository,
      issue_number: issue.number,
      instruction: instruction || `自动修复 Issue #${issue.number}`,
    };
    showRepairInspector();
    // 先切换上下文并取消上一任务的异步工作；恢复历史任务的请求只能在
    // 这个 generation 仍然有效时落到 UI。
    renderRepairSession();
    const sessionGeneration = repairSessionGeneration;
    let savedJobId = '';
    try { savedJobId = window.localStorage.getItem(repairStorageKey(currentRepository, issue.number)) || ''; } catch (_) {}
    if (savedJobId) {
      try {
        const job = await fetchJson(`/api/repairs/${encodeURIComponent(savedJobId)}`);
        if (
          sessionGeneration === repairSessionGeneration
          && job.repository === currentRepairRepository
          && Number(job.issue_number) === issue.number
        ) {
          renderRepairSession(job);
          if (!['review_ready', 'completed', 'failed'].includes(job.status)) pollRepairJob(job.id);
          return;
        }
      } catch (_) {}
    }
  };

  const openRepairJob = async (job) => {
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
    appendMessage('assistant', `<h3>${escapeHtml(currentRepository)}#${issue.number} 分析</h3><p><strong>${escapeHtml(issue.title)}</strong></p><div class="decision-summary"><div class="decision-summary-row"><span>状态</span><strong>${changedToday(issue) ? '今天有变化' : relativeTime(issue.updated_at)}</strong></div><div class="decision-summary-row"><span>讨论</span><strong>${issue.comments_count} 条评论 · ${issue.assignees?.length ? `已分配给 ${escapeHtml(issue.assignees.join(', '))}` : '尚未分配'}</strong></div></div><p style="margin-top:12px">需要落地时，可以继续说“修复 #${issue.number}”。修改会先保存为草稿，等你确认后再提交。</p>`);
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

  // ===========================================================================
  // Coding Agent 配置对话框
  // 5 步引导 (用单一 form + stepper 状态机, 不用真路由, 避免 server 端多 page):
  //   1. 选 provider (openai_compatible / anthropic / claude_cli / 自定义 URL)
  //   2. 填 API key (password, 提示 "key 存在 .ghe/config.yml, 权限最低")
  //   3. 选 model (按 provider 给常见 model 列表, 也可手填)
  //   4. 测试连接 (POST /api/coding-agent/test)
  //   5. 完成 (POST /api/coding-agent/configure 写盘)
  // 后端没接好时, save 会失败 — 这时 status 区域显示 404/500, 引导用户重试
  // 或者用 "复制 ghe config 片段" 的备用方式.
  // ===========================================================================

  // 5 步的 stepper 状态: provider → key → model → test → save.
  // 同一组字段全程不变, 进度只是 UI 提示, 不让用户重复输入.
  let codingAgentStepIndex = 0;
  const CODING_AGENT_STEPS = [
    { key: 'provider', label: '选择 provider' },
    { key: 'key', label: '填 API key' },
    { key: 'model', label: '选 model' },
    { key: 'test', label: '测试连接' },
    { key: 'save', label: '完成' },
  ];
  // provider -> 常见 model 列表. 手填路径也保留, 用户可以输 provider 专属 model.
  const CODING_AGENT_MODEL_PRESETS = {
    openai_compatible: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'deepseek-chat', 'qwen-coder', 'custom'],
    anthropic: ['claude-sonnet-4-5', 'claude-haiku-4-5', 'claude-opus-4-1', 'custom'],
    codex_cli: ['codex-default'],
    claude_cli: ['claude-code-default', 'custom'],
    custom: ['custom'],
  };

  const updateCodingAgentStepper = () => {
    if (!codingAgentDialog) return;
    const stepper = codingAgentDialog.querySelector('.coding-agent-stepper');
    if (!stepper) return;
    const dots = stepper.querySelectorAll('[data-coding-agent-step]');
    dots.forEach((dot) => {
      const idx = Number(dot.dataset.codingAgentStep);
      dot.classList.toggle('active', idx === codingAgentStepIndex);
      dot.classList.toggle('complete', idx < codingAgentStepIndex);
    });
    const label = stepper.querySelector('.coding-agent-step-label');
    if (label) label.textContent = CODING_AGENT_STEPS[codingAgentStepIndex]?.label || '';
  };

  // base_url 行只在 openai_compatible / custom 两种 provider 时显示.
  // 切换 provider 时同步显隐 + 清空 model 列表.
  const syncCodingAgentProviderFields = () => {
    if (!codingAgentDialog) return;
    const provider = String(codingAgentProvider?.value || 'openai_compatible');
    const baseUrlRow = codingAgentDialog.querySelector('[data-coding-agent-row="base-url"]');
    if (baseUrlRow) baseUrlRow.hidden = !(provider === 'openai_compatible' || provider === 'custom');
    const apiKeyRow = codingAgentDialog.querySelector('[data-coding-agent-row="api-key"]');
    if (apiKeyRow) apiKeyRow.hidden = (provider === 'codex_cli' || provider === 'claude_cli');
    if (codingAgentModels) {
      const presets = CODING_AGENT_MODEL_PRESETS[provider] || ['custom'];
      codingAgentModels.innerHTML = presets
        .map((m) => `<option value="${escapeHtml(m)}">${escapeHtml(m)}</option>`)
        .join('');
      if (codingAgentModel && !codingAgentModel.value.trim() && presets[0] !== 'custom') {
        codingAgentModel.value = presets[0];
      }
    }
    if (codingAgentDataBoundary) {
      codingAgentDataBoundary.textContent = provider === 'fake'
        ? 'fake 是演示 Provider：不会真正理解或修复仓库，产生的演示变更禁止创建 Draft PR。'
        : (provider === 'codex_cli'
          ? 'Codex CLI 在本机隔离工作区读取和修改代码；它是否向外发送内容取决于 Codex CLI 自身配置。'
          : (provider === 'claude_cli'
          ? 'Claude CLI 在本机工作区读取和修改代码；它是否向外发送内容取决于 Claude CLI 自身配置。'
          : 'API Provider 会接收 Issue 内容与为定位问题选取的仓库源码片段。请确认仓库数据允许发送给该模型服务。'));
    }
  };

  // 打开对话框时, 预填当前 currentCodingAgent 的值 (provider / model),
  // api_key 不预填 (后端不会回传明文, 用户需要重输).
  // prefillReason = 'create' (第一次) / 'fix' (上次失败 api_key_invalid).
  const openCodingAgentSetup = (prefillReason = 'create') => {
    if (!codingAgentDialog) return;
    if (codingAgentForm) codingAgentForm.reset();
    const ca = currentCodingAgent || {};
    if (codingAgentProvider) {
      codingAgentProvider.value = ca.provider || 'openai_compatible';
    }
    if (codingAgentModel && ca.model) codingAgentModel.value = ca.model;
    if (codingAgentApiKey) {
      codingAgentApiKey.value = '';
      codingAgentApiKey.placeholder = prefillReason === 'fix'
        ? '上次的 key 验证失败, 请重输'
        : 'API key 写入 .ghe/config.yml, 不会被回显';
    }
    syncCodingAgentProviderFields();
    codingAgentStepIndex = 0;
    updateCodingAgentStepper();
    if (codingAgentStatus) {
      codingAgentStatus.className = 'repair-setup-status optional';
      codingAgentStatus.innerHTML = '<strong>5 步引导</strong><span>选 provider → 填 key → 选 model → 测连通 → 完成</span>';
    }
    if (codingAgentSave) {
      codingAgentSave.textContent = '下一步';
    }
    codingAgentDialog.showModal();
  };

  // 收集当前 form 字段, 提交给后端 (test / save).
  const collectCodingAgentPayload = () => {
    const provider = String(codingAgentProvider?.value || '').trim();
    const baseUrl = String(codingAgentBaseUrl?.value || '').trim();
    const apiKey = String(codingAgentApiKey?.value || '').trim();
    const model = String(codingAgentModel?.value || '').trim();
    const payload = { provider, model };
    if (baseUrl) payload.base_url = baseUrl;
    // api_key 是 password, 用户没填时不要覆盖后端已存的 (save 时).
    if (apiKey) payload.api_key = apiKey;
    return payload;
  };

  // 字段校验: 缺关键字段时, 走不到对应 step. 这里只做"软校验",
  // 真正的连通性由 /api/coding-agent/test 兜底.
  const validateCodingAgentStep = (step) => {
    if (step === 0) {
      if (!codingAgentProvider?.value) return '请选择一个 provider';
    } else if (step === 1) {
      const provider = String(codingAgentProvider?.value || '');
      const canReuseExistingCredential = Boolean(
        currentCodingAgent?.configured
        && currentCodingAgent.provider === (provider === 'custom' ? 'openai_compatible' : provider)
        && currentCodingAgent.last_error_kind !== 'api_key_invalid'
      );
      if (!['codex_cli', 'claude_cli'].includes(provider)
          && !codingAgentApiKey?.value?.trim()
          && !canReuseExistingCredential) {
        return '请填 API key（Codex CLI / Claude CLI 不需要 key）';
      }
    } else if (step === 2) {
      if (!codingAgentModel?.value?.trim()) return '请选或填一个 model';
    }
    return null;
  };

  // "下一步" / "测试" / "保存" 按钮走同一个 handler, 用 data-action 区分.
  // 不去后端走 provider 校验失败 (例如未接) 时, status 区域显示具体错误,
  // 但不关闭对话框 — 用户可以改完字段再试.
  const advanceCodingAgentStep = async (targetStep, action) => {
    if (codingAgentStatus) {
      codingAgentStatus.className = 'repair-setup-status pending';
      codingAgentStatus.innerHTML = '<strong>正在…</strong><span>请稍等</span>';
    }
    const payload = collectCodingAgentPayload();
    try {
      let result = null;
      if (action === 'test') {
        result = await fetchJson('/api/coding-agent/test', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
      } else if (action === 'save') {
        result = await fetchJson('/api/coding-agent/configure', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        // 写盘成功后: 关闭 dialog, 刷新 repair-capabilities, 状态栏立刻更新.
        if (result) {
          currentCodingAgent = {
            configured: true,
            provider: result.provider || payload.provider,
            model: result.model || payload.model,
            last_error_kind: '',
          };
          updateCodingAgentIndicator();
          codingAgentDialog?.close();
          showToast(`Coding Agent 已配置：${currentCodingAgent.provider} · ${currentCodingAgent.model}`);
          // 重新拉一次 capabilities, 让 Issue inbox 4 档 CTA 立刻生效.
          await loadRepairCapabilities(true);
          if (currentIssues.length) renderIssueInbox(currentIssues);
          return;
        }
      }
      // test 成功的反馈: result.ok / result.error_kind.
      if (action === 'test' && result) {
        if (result.ok) {
          if (codingAgentStatus) {
            codingAgentStatus.className = 'repair-setup-status ready';
            codingAgentStatus.innerHTML = `<strong>连通成功</strong><span>${escapeHtml(result.model || payload.model)} 已响应。</span>`;
          }
        } else {
          const k = result.error_kind || 'unknown';
          const a = result.error_action || '查看详情';
          if (codingAgentStatus) {
            codingAgentStatus.className = 'repair-setup-status blocked';
            codingAgentStatus.innerHTML = `<strong>${escapeHtml(k)}</strong><span>${escapeHtml(a)}</span>`;
          }
        }
      }
      codingAgentStepIndex = targetStep;
      updateCodingAgentStepper();
      // 走到 "完成" 步时, 把 "下一步" 按钮换成 "保存".
      if (targetStep === CODING_AGENT_STEPS.length - 1 && codingAgentSave) {
        codingAgentSave.textContent = '保存';
      } else if (codingAgentSave) {
        codingAgentSave.textContent = '下一步';
      }
    } catch (error) {
      if (codingAgentStatus) {
        codingAgentStatus.className = 'repair-setup-status blocked';
        const title = error.error_kind === 'api_connection_failed' ? '连接测试失败' : '请求失败';
        const detail = error.error_action || error.message || '后端没接好, 请稍后重试或检查后端';
        codingAgentStatus.innerHTML = `<strong>${escapeHtml(title)}</strong><span>${escapeHtml(detail)}</span>`;
      }
    }
  };

  document.addEventListener('click', (event) => {
    const connectionButton = event.target.closest('[data-start-connection]');
    if (connectionButton) {
      const desired = connectionButton === repairConnectButton ? 'automatic_repair' : 'account';
      startConnection(connectionButton.dataset.startConnection, desired, connectionButton);
      return;
    }
    // onboarding "以后再说" 按钮 — 写入 localStorage 标记并收起引导.
    if (event.target.closest('[data-onboarding-skip]')) {
      markOnboardingSeen();
      showOnboardingIfFirstTime();
      showToast('已收起欢迎引导。添加仓库后即可开始。');
      return;
    }
    if (event.target.closest('[data-onboarding-start]')) {
      // "添加仓库" 主按钮也算 "seen", 这样下次回到页面不会强制弹引导.
      markOnboardingSeen();
      return;
    }
    // onboarding "添加仓库" — 复用已有 monitor dialog, 顺便 mark seen.
    if (event.target.closest('[data-onboarding-add-repo]')) {
      markOnboardingSeen();
      if (monitorDialog) monitorDialog.showModal();
      return;
    }
    // Coding Agent 配置对话框: 入口有 4 处
    // 1) Issue inbox CTA 4 档里的 "未配置" 档 (渲染时就挂了 data-open-coding-agent-setup)
    // 2) 失败 UI 里 api_key_invalid / model_not_found / api_connection_failed 的 CTA
    // 3) 顶部状态栏的 coding-agent-indicator (unconfigured / invalid 状态)
    // 4) onboarding 第一步的 "配置 Coding Agent" 按钮
    // 都用 openCodingAgentSetup 走, 用 currentCodingAgent.last_error_kind 决定 prefillReason.
    if (event.target.closest('[data-open-coding-agent-setup]')) {
      const prefill = (currentCodingAgent?.last_error_kind === 'api_key_invalid'
        || currentCodingAgent?.last_error_kind === 'model_not_found'
        || currentCodingAgent?.last_error_kind === 'api_connection_failed')
        ? 'fix'
        : 'create';
      openCodingAgentSetup(prefill);
      // 点过 Coding Agent 入口也视为"看过 onboarding", 别反复弹.
      markOnboardingSeen();
      return;
    }
    if (event.target.closest('[data-close-coding-agent-setup]') && codingAgentDialog) {
      codingAgentDialog.close();
      return;
    }
    // Coding Agent stepper 的 "测试" 按钮: 单独走, 不进 stepper 推进.
    if (event.target.closest('[data-coding-agent-test]')) {
      const err = validateCodingAgentStep(2);
      if (err) {
        if (codingAgentStatus) {
          codingAgentStatus.className = 'repair-setup-status blocked';
          codingAgentStatus.innerHTML = `<strong>字段不全</strong><span>${escapeHtml(err)}</span>`;
        }
        return;
      }
      advanceCodingAgentStep(3, 'test');
      return;
    }
    // Coding Agent stepper 的 "下一步" / "保存" 按钮: 根据当前 step 走 test 或 save.
    if (event.target.closest('[data-coding-agent-save]')) {
      // step 0 / 1 / 2 是字段不全校验, step 3 (test) 跳到 step 4 (save),
      // step 4 直接 POST configure.
      if (codingAgentStepIndex < 3) {
        const err = validateCodingAgentStep(codingAgentStepIndex);
        if (err) {
          if (codingAgentStatus) {
            codingAgentStatus.className = 'repair-setup-status blocked';
            codingAgentStatus.innerHTML = `<strong>字段不全</strong><span>${escapeHtml(err)}</span>`;
          }
          return;
        }
        codingAgentStepIndex += 1;
        updateCodingAgentStepper();
        if (codingAgentSave) codingAgentSave.textContent = '测试连接';
        return;
      }
      if (codingAgentStepIndex === 3) {
        // 在测试步点 "下一步" = 直接测一次, 然后跳到完成步.
        advanceCodingAgentStep(4, 'test').then(() => {
          if (codingAgentSave) codingAgentSave.textContent = '保存';
        });
        return;
      }
      // 完成步: 实际写盘.
      advanceCodingAgentStep(4, 'save');
      return;
    }
    if (event.target.closest('[data-open-repair-setup]') && repairSetupDialog) {
      repairSetupDialog.showModal();
      return;
    }
    if (event.target.closest('[data-close-repair-setup]') && repairSetupDialog) {
      repairSetupDialog.close();
      return;
    }
    if (event.target.closest('[data-copy-claude-login]')) {
      const command = currentCodingAgent?.provider === 'claude_cli'
        ? 'claude auth login'
        : 'codex login';
      navigator.clipboard?.writeText(command)
        .then(() => showToast('已复制。请在终端粘贴运行，然后回到这里重新检查'))
        .catch(() => showToast(command));
      return;
    }
    if (event.target.closest('[data-recheck-repair]')) {
      loadRepairCapabilities(true).then(() => {
        if (repairCapabilities?.available) showToast('自动修复已准备好');
      });
      return;
    }
    if (event.target.closest('[data-retry-repair]') && currentRepairJob) {
      const retryJob = currentRepairJob;
      pendingIssueTask = {
        repository: retryJob.repository,
        issue_number: Number(retryJob.issue_number),
        instruction: `重新运行 Issue #${retryJob.issue_number} 修复；先确认失败原因，再完成最小修改和测试`,
      };
      renderRepairSession();
      return;
    }
    if (event.target.closest('[data-allow-host-verification]') && currentRepairJob) {
      const button = event.target.closest('[data-allow-host-verification]');
      button.disabled = true;
      button.textContent = '正在启动验证…';
      fetchJson(`/api/repairs/${encodeURIComponent(currentRepairJob.id)}/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ allow_host_verification: true }),
      }).then((result) => {
        renderRepairSession(result);
        pollRepairJob(result.id);
      }).catch((error) => {
        showToast(error.message || '本机验证启动失败');
        button.disabled = false;
        button.textContent = '我理解风险，在本机运行测试';
      });
      return;
    }
    if (event.target.closest('[data-retry-verification]') && currentRepairJob) {
      if (!window.confirm('将再次在本机执行这个仓库的测试代码。确认已经处理失败原因并继续吗？')) return;
      const button = event.target.closest('[data-retry-verification]');
      button.disabled = true;
      button.textContent = '正在重新验证…';
      fetchJson(`/api/repairs/${encodeURIComponent(currentRepairJob.id)}/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ allow_host_verification: true }),
      }).then((result) => {
        renderRepairSession(result);
        pollRepairJob(result.id);
      }).catch((error) => {
        showToast(error.message || '重新验证启动失败');
        button.disabled = false;
        button.textContent = '重新运行验证';
      });
      return;
    }
    // 失败 UI 的细粒度操作: 复制命令 / 展开日志 / 调整指令后重跑
    const copyCommand = event.target.closest('[data-copy-command]');
    if (copyCommand) {
      const cmd = copyCommand.dataset.copyCommand || '';
      navigator.clipboard?.writeText(cmd)
        .then(() => showToast(`已复制：${cmd}`))
        .catch(() => showToast(cmd));
      return;
    }
    const toggleLog = event.target.closest('[data-toggle-repair-log]');
    if (toggleLog) {
      const logBox = toggleLog.parentElement?.querySelector('.repair-log');
      if (!logBox) return;
      const willShow = logBox.hidden;
      logBox.hidden = !willShow;
      toggleLog.textContent = willShow ? '收起日志' : '查看日志';
      if (willShow && !logBox.dataset.loaded && currentRepairJob) {
        const pre = logBox.querySelector('pre');
        if (pre) pre.textContent = '正在加载…';
        // 通过受 job id 限制的后端端点读取日志尾部；请求失败时再降级为
        // 本地路径提示。
        fetch(`/api/repairs/${encodeURIComponent(currentRepairJob.id)}/log`)
          .then((r) => r.ok ? r.text() : Promise.reject(new Error('日志不可用')))
          .then((text) => {
            if (pre) pre.textContent = text || '（空）';
            logBox.dataset.loaded = '1';
          })
          .catch(() => {
            if (pre) pre.textContent = '请打开 .ghe/repair-jobs/' + (currentRepairJob.id || '') + '.log 查看完整输出。';
            logBox.dataset.loaded = '1';
          });
      }
      return;
    }
    const retryWithInstruction = event.target.closest('[data-retry-with-instruction]');
    if (retryWithInstruction && currentRepairJob) {
      const extra = window.prompt('给 AI 一点补充说明（例如：忽略 README 修改，只改 src/）', '');
      const retryJob = currentRepairJob;
      pendingIssueTask = {
        repository: retryJob.repository,
        issue_number: Number(retryJob.issue_number),
        instruction: `重新运行 Issue #${retryJob.issue_number} 修复；${extra || '避免上次的失败原因'}`,
      };
      renderRepairSession();
      return;
    }
    // diff view 按钮: accept-all / reject-all / 继续对话
    if (event.target.closest('[data-diff-accept-all]') || (event.target === diffAcceptAll)) {
      if (_diffData) {
        const hunks = (_diffData.files || []).flatMap((f) => f.hunks);
        for (const h of hunks) setHunkStatus(h.id, 'accepted');
        showToast(`已接受全部 ${hunks.length} 个 hunk`);
      }
      return;
    }
    if (event.target.closest('[data-diff-reject-all]') || (event.target === diffRejectAll)) {
      if (_diffData) {
        const hunks = (_diffData.files || []).flatMap((f) => f.hunks);
        for (const h of hunks) setHunkStatus(h.id, 'rejected');
        showToast(`已全部回滚 (${hunks.length} 个 hunk)`);
      }
      return;
    }
    if (event.target.closest('[data-diff-continue-chat]') || (event.target === diffContinueChat)) {
      openDiffChatDialog();
      return;
    }
    // diff view 关闭按钮
    if (event.target.closest('[data-close-diff-chat]')) {
      closeDiffChatDialog();
      return;
    }
    // diff 继续对话 suggestion chip
    const diffSuggestion = event.target.closest('[data-diff-suggestion]');
    if (diffSuggestion && diffChatInput) {
      diffChatInput.value = diffSuggestion.dataset.diffSuggestion || diffSuggestion.textContent.trim();
      diffChatInput.focus();
      return;
    }
    // diff view 右上角 "在 VS Code 打开产物"
    if (event.target.closest('[data-diff-open-vscode]') || (event.target === diffOpenVscode)) {
      openWorkspaceInVSCode();
      return;
    }
    // diff view sidebar 单 hunk accept / reject
    const hunkAction = event.target.closest('[data-hunk-action]');
    if (hunkAction) {
      const hid = Number(hunkAction.dataset.hunkId);
      const action = hunkAction.dataset.hunkAction;
      if (Number.isFinite(hid) && (action === 'accept' || action === 'reject')) {
        setHunkStatus(hid, action === 'accept' ? 'accepted' : 'rejected');
      }
      return;
    }
    // diff view sidebar 卡片点击 = 跳到那个 hunk
    const hunkCard = event.target.closest('.diff-hunk-card');
    if (hunkCard && !event.target.closest('[data-hunk-action]')) {
      const hid = Number(hunkCard.dataset.hunkId);
      if (Number.isFinite(hid)) {
        _diffActiveHunkId = hid;
        // 移除旧 active, 加新 active
        if (diffViewSidebar) {
          for (const c of diffViewSidebar.querySelectorAll('.diff-hunk-card')) {
            c.classList.toggle('active', Number(c.dataset.hunkId) === hid);
          }
        }
        // 滚到该 hunk 头
        if (_diffEditorView && _diffData) {
          const h = (_diffData.files || []).flatMap((f) => f.hunks).find((x) => x.id === hid);
          if (h && typeof _diffViewModule?.EditorView?.scrollIntoView === 'function') {
            try {
              const meta = _buildDiffDoc(_diffData).meta;
              const idx = meta.findIndex((m) => m.type === 'hunk' && m.hunkId === hid);
              if (idx >= 0) {
                const ln = _diffEditorView.state.doc.line(idx + 1);
                _diffEditorView.dispatch({ effects: _diffViewModule.EditorView.scrollIntoView(ln.from, { y: 'center' }) });
              }
            } catch (_) { /* ignore */ }
          }
        }
      }
      return;
    }
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
    if (event.target.closest('[data-toggle-repair-history]')) {
      showRepairHistory = !showRepairHistory;
      renderRepairTaskList(repairJobs);
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
      const sessionGeneration = repairSessionGeneration;
      const taskPayload = { ...pendingIssueTask };
      button.disabled = true;
      button.textContent = '正在启动…';
      fetchJson('/api/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(taskPayload),
      }).then((result) => {
        try {
          window.localStorage.setItem(
            repairStorageKey(result.repository, result.issue_number),
            result.id,
          );
        } catch (_) {}
        if (sessionGeneration !== repairSessionGeneration) return;
        renderRepairSession(result);
        pollRepairJob(result.id);
        loadRepairJobs();
        pendingIssueTask = null;
      }).catch((error) => {
        if (sessionGeneration !== repairSessionGeneration) return;
        showToast(error.message || '自动修复启动失败');
        button.disabled = false;
        button.textContent = '分析并准备修复';
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
    if (event.target.closest('[data-open-monitor]') && monitorDialog) {
      monitorDialog.showModal();
      // onboarding 上的 "添加仓库" 按钮也算 "已看过", 下次不再弹.
      markOnboardingSeen();
    }
    if (event.target.closest('[data-open-github-setup]') && githubSetupDialog) {
      // 升级路径: 升级前接受的 hunk 已经写到了后端, 不会丢.
      // 检测这次点击是不是从 diff view 触发的 (button id = "diff-connect-github" 也在该 view 里).
      const fromDiffView = diffView && !diffView.hidden;
      if (fromDiffView) {
        const acceptedBefore = Object.values(_diffHunkStatuses).filter((s) => s === 'accepted').length;
        if (acceptedBefore > 0 && diffViewUpgrade) {
          diffViewUpgrade.hidden = false;
          diffViewUpgrade.textContent = `已升级到完整模式 · 之前接受的 ${acceptedBefore} 个 hunk 已保留`;
          setTimeout(() => { if (diffViewUpgrade) diffViewUpgrade.hidden = true; }, 6000);
        }
      }
      githubSetupDialog.showModal();
    }
    if (event.target.closest('[data-close-github-setup]') && githubSetupDialog) githubSetupDialog.close();
    if (event.target.closest('[data-copy-github-login]')) {
      const command = 'gh auth login --web --git-protocol https';
      navigator.clipboard?.writeText(command)
        .then(() => showToast('已复制。请在终端粘贴运行并完成浏览器授权'))
        .catch(() => showToast(command));
    }
    if (event.target.closest('[data-open-owned]') && monitorDialog) {
      monitorDialog.showModal();
      loadOwnedRepositoryChoices();
      markOnboardingSeen();
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

  // Coding Agent 配置对话框: provider 切换时同步 base_url / api_key 行的显隐,
  // 以及 model 预设列表. change 事件不冒泡, 挂直绑.
  if (codingAgentProvider) {
    codingAgentProvider.addEventListener('change', syncCodingAgentProviderFields);
  }

  if (repoSwitcher) {
    repoSwitcher.addEventListener('change', () => {
      const repository = repoSwitcher.value;
      if (!repository) return;  // 用户选了 "— 请选择 —" 不动
      try { window.localStorage.setItem('ghe:selected-repository', repository); } catch (_) {}
      // topbar 下拉 = 用户明确选了 repo, 视为「开始用这个」, 立刻 loadIssues.
      loadIssues(repository);
    });
  }

  // 等首轮状态都落定后再标记 ready，避免“匿名/已连接”状态和首次引导
  // 在慢请求下短暂互相矛盾。
  Promise.allSettled([
    loadRepairCapabilities(),
    loadRepositories(),
    loadRepairJobs(),
  ]).finally(() => {
    document.documentElement.dataset.gheUi = 'ready';
  });

  // sidebar pill 左键 = 选中 + loadIssues (主区切换).
  // 中键 / 右键「在新标签打开」保留默认行为 (跳 /ui/brief/{repo}).
  document.addEventListener('click', (event) => {
    const pill = event.target.closest('[data-select-repo]');
    if (!pill) return;
    // Brief / decision pages do not have an Issue inbox. Their repository
    // pills are normal links and must navigate to the repository brief.
    if (!issueInbox || !issueSummary) return;
    if (event.button !== 0) return;        // 中键右键放行
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;  // 修饰键放行
    event.preventDefault();
    const repository = pill.dataset.selectRepo;
    if (!repository) return;
    try { window.localStorage.setItem('ghe:selected-repository', repository); } catch (_) {}
    if (repoSwitcher) repoSwitcher.value = repository;  // 同步 topbar
    loadIssues(repository);
  });
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
      const jobId = String(currentRepairJob.id || '');
      const sessionGeneration = repairSessionGeneration;
      repairGuidanceSend.disabled = true;
      repairGuidanceSend.textContent = '发送中…';
      try {
        const result = await fetchJson(`/api/repairs/${encodeURIComponent(jobId)}/guidance`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message }),
        });
        if (
          sessionGeneration !== repairSessionGeneration
          || String(currentRepairJob?.id || '') !== jobId
        ) return;
        repairGuidanceInput.value = '';
        renderRepairSession(result);
        pollRepairJob(result.id);
      } catch (error) {
        if (sessionGeneration !== repairSessionGeneration) return;
        showToast(error.message || '指导发送失败');
      } finally {
        if (
          sessionGeneration === repairSessionGeneration
          && String(currentRepairJob?.id || '') === jobId
        ) {
          repairGuidanceSend.textContent = '让 AI 调整';
          if (currentRepairJob?.status === 'review_ready') repairGuidanceSend.disabled = false;
        }
      }
    });
  }

  if (diffChatSend) {
    diffChatSend.addEventListener('click', sendDiffChat);
  }
  if (diffChatInput) {
    diffChatInput.addEventListener('keydown', (event) => {
      if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
        event.preventDefault();
        sendDiffChat();
      }
    });
  }

  if (repairPublish) {
    repairPublish.addEventListener('click', async () => {
      if (!currentRepairJob || currentRepairJob.status !== 'review_ready') return;
      const jobId = String(currentRepairJob.id || '');
      const currentVerification = repairVerification(currentRepairJob);
      if (
        currentVerification.status === 'unverified'
        && currentVerification.reason === 'sandbox_unavailable'
      ) {
        if (!window.confirm('本机验证会执行这个仓库里的测试代码，可能包含不可信逻辑。确认继续吗？')) return;
        repairPublish.disabled = true;
        repairPublish.textContent = '正在启动验证…';
        try {
          const result = await fetchJson(`/api/repairs/${encodeURIComponent(jobId)}/verify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ allow_host_verification: true }),
          });
          renderRepairSession(result);
          pollRepairJob(result.id);
        } catch (error) {
          showToast(error.message || '本机验证启动失败');
          updateDiffCtaStatus();
        }
        return;
      }
      if (!providerAllowsPublishing(currentRepairJob)) {
        updateDiffCtaStatus();
        showToast(isDemoRepair(currentRepairJob)
          ? '演示内容不能提交到 GitHub'
          : '当前任务来源未确认，暂时不能提交');
        return;
      }
      if (repairVerification(currentRepairJob).status !== 'passed') {
        updateDiffCtaStatus();
        showToast('修复通过测试或验证后才能提交');
        return;
      }
      if (!currentGithubAuthenticated) {
        if (githubSetupDialog) githubSetupDialog.showModal();
        return;
      }
      if (!_diffData || _diffJobId !== jobId || !Object.keys(_diffHunkStatuses).length) {
        updateDiffCtaStatus();
        showToast('完整改动还没有加载完成，请稍后再试');
        return;
      }
      const generation = ++publishGeneration;
      const isCurrentPublish = () => (
        generation === publishGeneration
        && String(currentRepairJob?.id || '') === jobId
      );
      repairPublish.disabled = true;
      repairPublish.setAttribute('aria-busy', 'true');
      repairPublish.textContent = '正在准备提交…';
      try {
        await confirmFullDiffForSubmission(jobId);
        if (!isCurrentPublish()) return;
        const confirmation = await fetchJson(
          `/api/repairs/${encodeURIComponent(jobId)}/confirm-token`,
        );
        // 切到另一个任务后，不再为旧任务触发外部发布动作。
        if (!isCurrentPublish()) return;
        if (!confirmation.token) throw new Error('服务没有返回有效的确认令牌，请重试');
        // 发布是唯一会对 GitHub 产生外部写入的动作。令牌只在这次点击中
        // 存活，不缓存、不复用，并按后端契约通过 X-Confirm 回传。
        const result = await fetchJson(`/api/repairs/${encodeURIComponent(jobId)}/publish`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Confirm': confirmation.token,
          },
          body: '{}',
        });
        if (!isCurrentPublish()) return;
        renderRepairSession(result);
        pollRepairJob(result.id);
        showToast('修复已提交，等待仓库管理员处理');
      } catch (error) {
        if (!isCurrentPublish()) return;
        showToast(error.message || '修复提交失败，请重试');
        updateDiffCtaStatus();
      } finally {
        if (isCurrentPublish()) repairPublish.removeAttribute('aria-busy');
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

  if (briefGenerateButton) {
    briefGenerateButton.addEventListener('click', startBriefGeneration);
  }

  window.setInterval(() => {
    if (currentRepository && !document.hidden) loadIssues(currentRepository);
  }, 300000);
  window.setInterval(() => {
    if (!document.hidden) loadRepairJobs();
  }, 5000);
})();
"""

DIFF_VIEW_CLIENT_JS = r"""// CodeMirror 6 entry point for GitHubEngineer's diff view.
//
// This file exists so the importmap (injected by ``app.js``) is in scope
// when the module is evaluated.  We re-export only the symbols the
// diff renderer actually uses; keeping the surface narrow avoids
// pulling in @codemirror/commands / @codemirror/search and the rest
// of the bundle we do not need.
//
// Why we ship this as a separate module instead of inlining in app.js:
//   - The 5 prototype traps (see README §6) all stem from importmap
//     timing.  An ``<script type="importmap">`` must be in the
//     document **before** any module script that uses bare specifiers
//     is fetched.  A separate module loaded via ``import()`` after the
//     importmap is in the DOM is the cleanest way to honour that.
//   - The file size is small (~3 KB) so loading on first diff view is
//     a one-time cost; a cached CodeMirror is not worth the complexity
//     for a sub-page that may never open.

export {
  EditorView,
  lineNumbers,
  highlightActiveLine,
  highlightActiveLineGutter,
  Decoration,
} from "@codemirror/view";

export {
  EditorState,
  StateField,
  StateEffect,
  RangeSetBuilder,
} from "@codemirror/state";
"""


_ICON = {
    "assistant": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M12 3v3M5.6 5.6l2.1 2.1M3 12h3m-.4 6.4 2.1-2.1M12 18v3m6.4-2.6-2.1-2.1M18 12h3m-2.6-6.4-2.1 2.1"/><circle cx="12" cy="12" r="4"/></svg>',
    "briefs": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M6 3h9l3 3v15H6z"/><path d="M14 3v4h4M9 12h6M9 16h6"/></svg>',
    "decisions": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M5 4h14v16H5z"/><path d="m8 10 2 2 5-5M8 16h8"/></svg>',
}


def render_shell(
    *, title: str, body: str, repos: list[str], active: str = "assistant", context: str = "维护者助理"
) -> str:
    """Wrap a page in the responsive native-style application shell."""

    def nav_item(key: str, href: str, label: str) -> str:
        current = " active" if active == key else ""
        return (
            f'<a class="nav-link{current}" href="{href}" title="{escape(label)}" aria-label="{escape(label)}">'
            f'{_ICON[key]}<span>{escape(label)}</span></a>'
        )

    repo_items = "".join(
        '<a class="repo-pill" href="/ui/brief/{repo}" data-select-repo="{repo}">'
        '<span class="repo-dot"></span><span class="repo-name">{label}</span></a>'.format(
            repo=escape(repo, quote=True), label=escape(repo)
        )
        for repo in repos
    )
    if not repo_items:
        repo_items = '<div class="repo-pill"><span class="repo-name">尚未配置仓库</span></div>'
    repo_switcher = (
        '<div class="topbar-repo">'
        '<label class="repo-picker-label" for="repo-switcher"><strong>当前仓库</strong><small>点击切换</small></label>'
        '<span class="repo-access-dot" id="repo-access-dot"></span>'
        '<select id="repo-switcher" aria-label="切换仓库"><option>正在读取仓库…</option></select>'
        '<button id="repo-viewer" class="repo-viewer" type="button" data-open-github-setup></button>'
        '<button class="monitor-repo-button" type="button" data-open-monitor>+ 添加仓库</button>'
        '</div>'
        if active == "assistant"
        else ""
    )

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta name="theme-color" content="#f4f4f1">
  <title>{escape(title)}</title>
  <link rel="stylesheet" href="/ui/app.css">
</head>
<body>
<a class="skip-link" href="#main-workspace">跳到主要内容</a>
<div class="app-shell">
  <aside class="sidebar">
    <a class="brand" href="/ui/" aria-label="GitHub Engineer 首页">
      <span class="brand-mark">{_ICON['assistant']}</span>
      <span class="brand-title">GitHub Engineer</span>
    </a>
    <div class="workspace-label">工作区</div>
    <div class="repo-list">{repo_items}</div>
    <nav class="side-nav" aria-label="主要导航">
      {nav_item('assistant', '/ui/', '助理')}
      {nav_item('briefs', '/ui/briefs', '简报')}
      {nav_item('decisions', '/ui/decisions', '决策')}
    </nav>
    <section class="task-rail" aria-labelledby="task-rail-title">
      <div class="task-rail-heading"><strong id="task-rail-title">需要处理</strong><span class="task-rail-count" id="repair-task-count">0</span><button class="task-rail-toggle" id="repair-task-toggle" type="button" data-toggle-repair-history hidden aria-expanded="false">查看历史</button></div>
      <div class="task-list" id="repair-task-list"><div class="task-empty">还没有修复任务。<br>从 Issue 开始一个。</div></div>
    </section>
    <div class="sidebar-footer"><span class="online">本地服务在线</span></div>
  </aside>
  <main class="workspace" id="main-workspace" tabindex="-1">
    <header class="topbar">
      <div class="topbar-title"><span>{escape(context)}</span><span class="topbar-kicker">GitHub 同步 · 人工确认</span></div>
      {repo_switcher}
      <span class="mode-indicator" id="mode-indicator" data-mode="anonymous" title="匿名模式：可浏览、克隆、修复公开仓库；产物留本地。要对外提交 PR 时再连接 GitHub。">匿名浏览</span>
      <button class="coding-agent-indicator" id="coding-agent-indicator" type="button" data-state="unconfigured" data-open-coding-agent-setup title="Coding Agent 状态">未配置 Coding Agent</button>
      <div class="topbar-status">GitHub Engineer v1.0</div>
    </header>
    <div class="workspace-scroll">{body}</div>
    <section class="repair-inspector" id="repair-inspector" hidden aria-label="修复任务详情">
      <div class="repair-inspector-header">
        <div><div class="repair-inspector-kicker" id="repair-repository">修复会话</div><h2 id="repair-title">Issue 修复</h2><p id="repair-delivery"></p></div>
        <div class="repair-inspector-header-actions">
          <button class="soft-button" type="button" data-close-repair>关闭</button>
        </div>
      </div>
      <div class="repair-progress" aria-label="修复进度">
        <span data-repair-phase="read">读取代码</span>
        <span data-repair-phase="locate">定位</span>
        <span data-repair-phase="modify">修改</span>
        <span data-repair-phase="verify">验证</span>
        <span data-repair-phase="review">查看改动</span>
      </div>
      <div class="repair-stream" id="repair-stream" aria-live="polite"></div>
      <section class="diff-view" id="diff-view" hidden aria-label="代码修改预览">
        <div class="diff-view-meta">
          <strong id="diff-view-title">代码修改</strong>
          <span class="diff-view-stats" id="diff-view-stats">正在加载…</span>
        </div>
        <div class="diff-view-overview">
          <div class="diff-view-verification" id="diff-view-verification" aria-live="polite"></div>
          <p class="diff-view-summary" id="diff-view-summary">正在整理修复说明…</p>
        </div>
        <div class="diff-view-body">
          <div class="diff-view-code-heading"><strong>代码改动</strong><span>滚动查看全部文件</span></div>
          <div class="diff-view-editor" id="diff-view-editor"></div>
        </div>
        <footer class="diff-view-cta">
          <span class="diff-view-status" id="diff-view-status">正在加载完整改动…</span>
        </footer>
      </section>
      <div class="repair-controls">
        <textarea id="repair-guidance-input" rows="2" aria-label="告诉 AI 需要调整的地方" placeholder="需要调整？直接告诉 AI（可选）" disabled></textarea>
        <div class="repair-actions">
          <button class="soft-button" id="repair-guidance-send" type="button" disabled>让 AI 调整</button>
          <button class="soft-button" id="repair-skip-submit" type="button" data-close-repair hidden>暂不提交</button>
          <button class="primary-button" id="repair-publish" type="button" disabled>提交修复</button>
        </div>
      </div>
    </section>
  </main>
</div>
<dialog class="dialog" id="decision-dialog">
  <div class="dialog-header">
    <div><h2>告诉我你的决定</h2><p>这条记忆会影响之后的维护建议。</p></div>
    <button class="icon-button" type="button" aria-label="关闭" data-close-dialog>×</button>
  </div>
  <form class="decision-form" id="decision-form">
    <div class="field-row">
      <div class="field"><label for="decision-status">决定</label><select id="decision-status" name="status"><option value="accepted">接受</option><option value="deferred">延后</option><option value="rejected">拒绝</option></select></div>
      <div class="field"><label for="decision-issue">Issue 编号（可选）</label><input id="decision-issue" name="issue_number" type="number" min="1" placeholder="例如 42"></div>
    </div>
    <div class="field"><label for="decision-theme">主题（可选）</label><input id="decision-theme" name="theme" placeholder="例如 OAuth 重构"></div>
    <div class="field"><label for="decision-reason">原因</label><textarea id="decision-reason" name="reason" required placeholder="为什么接受、延后或拒绝？"></textarea></div>
    <div class="dialog-actions"><button class="soft-button" type="button" data-close-dialog>取消</button><button class="primary-button" type="submit">记录决策</button></div>
  </form>
</dialog>
<dialog class="dialog monitor-dialog" id="monitor-dialog">
  <div class="dialog-header">
    <div><h2>添加仓库</h2><p>粘贴地址，或者从你的 GitHub 仓库中选择。</p></div>
    <button class="icon-button" type="button" aria-label="关闭" data-close-monitor>×</button>
  </div>
  <form class="decision-form" id="monitor-form">
    <div class="field"><label for="monitor-repository">仓库地址</label><input id="monitor-repository" name="repository" required placeholder="https://github.com/owner/repository"></div>
    <div class="dialog-actions"><button class="primary-button" type="submit">添加到清单</button></div>
  </form>
  <div class="picker-divider"><span>或者</span></div>
  <div class="owned-picker">
    <button class="soft-button owned-picker-trigger" type="button" data-load-owned>从我的仓库选择</button>
    <div class="owned-picker-panel" id="owned-picker-panel" hidden>
      <div class="field"><label for="owned-repo-search">搜索我的仓库</label><input id="owned-repo-search" type="search" placeholder="输入仓库名称"></div>
      <div class="owned-repo-list" id="owned-repo-list"></div>
    </div>
  </div>
</dialog>
<dialog class="dialog" id="github-setup-dialog">
  <div class="dialog-header">
    <div><h2>连接账号</h2><p>只在需要更多账号功能时连接一次。</p></div>
    <button class="icon-button" type="button" aria-label="关闭" data-close-github-setup>×</button>
  </div>
  <div class="github-setup">
    <div class="repair-setup-status optional" id="github-setup-status">
      <strong>查看公开仓库无需连接</strong><span>需要私有仓库或提交操作时，再完成下面一步。</span>
    </div>
    <ol class="connection-steps">
      <li>点击“开始连接”</li>
      <li>在打开的页面完成确认</li>
      <li>返回应用，系统会自动继续</li>
    </ol>
    <div class="github-setup-actions">
      <button class="primary-button" id="github-connect-button" type="button" data-start-connection="account">开始连接</button>
      <button class="soft-button" type="button" data-close-github-setup>暂时不用</button>
    </div>
    <details class="connection-help">
      <summary>遇到问题？查看备用方式</summary>
      <div class="connection-help-body">
        <p>在终端运行下面的命令，完成后回到这里重新打开连接页。</p>
        <code>gh auth login --web --git-protocol https</code>
        <div class="github-setup-actions">
          <button class="soft-button" type="button" data-copy-github-login>复制备用命令</button>
          <a class="soft-button" href="https://cli.github.com/" target="_blank" rel="noreferrer">安装所需组件</a>
        </div>
      </div>
    </details>
  </div>
</dialog>
<dialog class="dialog" id="repair-setup-dialog">
  <div class="dialog-header">
    <div><h2>准备自动修复</h2><p>首次使用只需完成一次连接。</p></div>
    <button class="icon-button" type="button" aria-label="关闭" data-close-repair-setup>×</button>
  </div>
  <div class="github-setup">
    <div class="repair-setup-status blocked" id="repair-setup-status">
      <strong>正在确认是否可以开始</strong><span>通常只需要几秒钟。</span>
    </div>
    <ol class="connection-steps">
      <li>点击“开始连接”</li>
      <li>在打开的页面完成确认</li>
      <li>返回应用，系统会自动继续</li>
    </ol>
    <div class="github-setup-actions">
      <button class="primary-button" id="repair-connect-button" type="button" data-start-connection="automatic_repair">开始连接</button>
      <button class="soft-button" type="button" data-close-repair-setup>稍后再说</button>
    </div>
    <details class="connection-help">
      <summary>遇到问题？查看备用方式</summary>
      <div class="connection-help-body">
        <p>在终端运行下面的命令，完成后点击“重新检查”。</p>
        <code>codex login（Codex）或 claude auth login（Claude）</code>
        <div class="github-setup-actions">
          <button class="soft-button" type="button" data-copy-claude-login>复制备用命令</button>
          <button class="soft-button" type="button" data-recheck-repair>重新检查</button>
        </div>
      </div>
    </details>
    <p class="github-setup-note">修复会在隔离目录中进行；对外提交前仍会等待你的确认。</p>
  </div>
</dialog>
<dialog class="dialog" id="coding-agent-setup-dialog">
  <div class="dialog-header">
    <div><h2>配置 Coding Agent</h2><p>选 LLM provider、填 key、选 model，然后测连通。</p></div>
    <button class="icon-button" type="button" aria-label="关闭" data-close-coding-agent-setup>×</button>
  </div>
  <div class="coding-agent-setup">
    <div class="coding-agent-stepper" aria-label="5 步引导">
      <span class="coding-agent-step-dot" data-coding-agent-step="0"></span>
      <span class="coding-agent-step-dot" data-coding-agent-step="1"></span>
      <span class="coding-agent-step-dot" data-coding-agent-step="2"></span>
      <span class="coding-agent-step-dot" data-coding-agent-step="3"></span>
      <span class="coding-agent-step-dot" data-coding-agent-step="4"></span>
      <span class="coding-agent-step-label">选择 provider</span>
    </div>
    <div class="repair-setup-status optional" id="coding-agent-status">
      <strong>5 步引导</strong><span>选 provider → 填 key → 选 model → 测连通 → 完成</span>
    </div>
    <form class="decision-form" id="coding-agent-form" autocomplete="off">
      <div class="field" data-coding-agent-row="provider">
        <label for="coding-agent-provider">Provider</label>
        <select id="coding-agent-provider" name="provider">
          <option value="fake" disabled>fake（演示模式，不可发布）</option>
          <option value="openai_compatible">OpenAI-compatible（OpenAI / DeepSeek / Ollama / 自托管）</option>
          <option value="anthropic">Anthropic（claude-sonnet / claude-haiku / claude-opus）</option>
          <option value="codex_cli">Codex CLI（用本地 ChatGPT 登录态）</option>
          <option value="claude_cli">Claude Code CLI（用本地登录态）</option>
          <option value="custom">自定义 URL</option>
        </select>
        <small class="field-hint">不限于 Claude Code；OpenAI / Anthropic / DeepSeek / Ollama / 自托管都支持。</small>
      </div>
      <div class="field" data-coding-agent-row="base-url">
        <label for="coding-agent-base-url">Base URL</label>
        <input id="coding-agent-base-url" name="base_url" type="url" placeholder="https://api.openai.com/v1">
        <small class="field-hint">OpenAI-compatible / 自定义 provider 必填，Anthropic / Codex CLI / Claude CLI 不需要。</small>
      </div>
      <div class="field" data-coding-agent-row="api-key">
        <label for="coding-agent-api-key">API key</label>
        <input id="coding-agent-api-key" name="api_key" type="password" placeholder="sk-...">
        <small class="field-hint">写入 <code>.ghe/config.yml</code>，不会被回显。Codex CLI / Claude CLI 不需要。</small>
      </div>
      <div class="field-row" data-coding-agent-row="model">
        <div class="field">
          <label for="coding-agent-model">Model</label>
          <input id="coding-agent-model" name="model" list="coding-agent-models" placeholder="例如 gpt-4o">
          <datalist id="coding-agent-models"></datalist>
        </div>
        <div class="field coding-agent-test-col">
          <label>&nbsp;</label>
          <button class="soft-button" type="button" id="coding-agent-test" data-coding-agent-test>测试连接</button>
        </div>
      </div>
      <p class="github-setup-note" id="coding-agent-data-boundary">API Provider 会接收 Issue 内容与为定位问题选取的仓库源码片段。请确认仓库数据允许发送给该模型服务。</p>
      <p class="github-setup-note">修复在隔离目录运行，不会自动提交；验证完成后，你可以查看完整改动再决定是否提交。</p>
      <div class="dialog-actions">
        <button class="soft-button" type="button" data-close-coding-agent-setup>取消</button>
        <button class="primary-button" type="button" id="coding-agent-save" data-coding-agent-save>下一步</button>
      </div>
    </form>
  </div>
</dialog>
<script src="/ui/app.js" defer></script>
</body>
</html>"""
