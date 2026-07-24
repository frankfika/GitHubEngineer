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
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: none; }

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
.brand h1 { display: block; margin: 0; color: var(--text); font-size: 13px; letter-spacing: -.01em; }
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
.repo-viewer { color: var(--text-3); font-size: 10px; white-space: nowrap; }
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
.onboarding-icon { display: grid; place-items: center; width: 48px; height: 48px; margin-bottom: 16px; color: var(--text-2); background: var(--surface-soft); border: 1px solid var(--line); border-radius: 15px; font-size: 25px; font-weight: 300; }
.repository-onboarding h1 { margin: 0; font-size: 25px; letter-spacing: -.03em; }
.repository-onboarding p { max-width: 420px; margin: 8px 0 0; color: var(--text-2); }
.onboarding-actions { display: flex; gap: 8px; margin-top: 20px; }
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
.repair-kicker { margin-bottom: 3px; color: var(--text-3); font-size: 10px; font-weight: 650; letter-spacing: .04em; }
.repair-progress { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1px; padding: 0 20px; border-bottom: 1px solid var(--line); }
.repair-progress span { position: relative; padding: 10px 4px 11px; color: var(--text-3); font-size: 10px; text-align: center; }
.repair-progress span::after { content: ""; position: absolute; left: 0; right: 0; bottom: -1px; height: 2px; background: transparent; }
.repair-progress span.active { color: var(--text); font-weight: 650; }
.repair-progress span.active::after { background: var(--accent); }
.repair-progress span.complete { color: var(--success); }
.repair-stream { min-height: 0; overflow: auto; padding: 20px; background: color-mix(in srgb, var(--surface-soft) 40%, transparent); }
.repair-event { display: grid; grid-template-columns: 28px minmax(0, 1fr); gap: 10px; margin-bottom: 16px; }
.repair-event.user { grid-template-columns: minmax(0, 1fr) 28px; }
.repair-event-avatar { display: grid; place-items: center; width: 28px; height: 28px; color: var(--surface-solid); background: var(--accent); border-radius: 9px; font-size: 9px; font-weight: 700; }
.repair-event.user .repair-event-avatar { grid-column: 2; color: var(--text); background: var(--surface-solid); border: 1px solid var(--line); }
.repair-event-body { min-width: 0; }
.repair-event.user .repair-event-body { grid-row: 1; text-align: right; }
.repair-event-meta { margin-bottom: 4px; color: var(--text-3); font-size: 9px; }
.repair-event-card { display: inline-block; max-width: 100%; padding: 11px 13px; color: var(--text-2); background: var(--surface-solid); border: 1px solid var(--line); border-radius: 5px 13px 13px; text-align: left; overflow-wrap: anywhere; }
.repair-event.user .repair-event-card { color: var(--surface-solid); background: var(--accent); border: 0; border-radius: 13px 5px 13px 13px; }
.repair-event-card strong { color: var(--text); }
.repair-event.user .repair-event-card strong { color: inherit; }
.repair-output { margin-top: 9px; padding: 9px 10px; color: var(--text-2); background: var(--surface-soft); border: 1px solid var(--line); border-radius: 8px; font: 10px/1.5 "SF Mono", ui-monospace, monospace; white-space: pre-wrap; }
.repair-controls { display: grid; gap: 9px; padding: 13px 16px 15px; border-top: 1px solid var(--line); background: var(--surface-solid); }
.repair-controls textarea { width: 100%; min-height: 52px; max-height: 110px; resize: none; padding: 10px 11px; color: var(--text); background: var(--surface-soft); border: 1px solid var(--line); border-radius: 10px; outline: 0; }
.repair-controls textarea:focus { border-color: var(--line-strong); }
.repair-controls textarea:disabled { opacity: .55; }
.repair-actions { display: flex; justify-content: flex-end; gap: 8px; }
.repair-actions .primary-button:disabled, .repair-actions .soft-button:disabled { cursor: not-allowed; opacity: .45; }
.task-rail { display: grid; gap: 8px; margin-top: 24px; min-height: 0; }
.task-rail-heading { display: flex; align-items: center; justify-content: space-between; padding: 0 8px; }
.task-rail-heading strong { font-size: 11px; }
.task-rail-count { min-width: 20px; padding: 1px 6px; color: var(--text-2); background: var(--surface-soft); border: 1px solid var(--line); border-radius: 999px; font-size: 10px; text-align: center; }
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
.toast { position: fixed; z-index: 30; top: 16px; right: 16px; max-width: min(360px, calc(100% - 32px)); padding: 11px 14px; color: var(--text); background: var(--surface-solid); border: 1px solid var(--line-strong); border-radius: 11px; box-shadow: 0 12px 35px rgba(0,0,0,.15); animation: message-in .25s var(--ease) both; }

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
  .repair-actions { align-items: stretch; flex-direction: column; }
  .repair-actions button { width: 100%; }
}
"""


APP_JS = r"""
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
    if (repoPermission) {
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

  const loadIssues = async (repository, force = false) => {
    if (!issueInbox || !issueSummary || !repository) return;
    currentRepository = repository;
    if (root) root.dataset.repo = repository;
    if (activeRepoHeading) activeRepoHeading.textContent = `正在读取 ${repository}`;
    if (dailySummary) dailySummary.textContent = '正在同步仓库动态…';
    const sidebarRepoName = qs('.repo-name');
    const sidebarRepoLink = qs('.repo-pill');
    if (sidebarRepoName) sidebarRepoName.textContent = repository;
    if (sidebarRepoLink) sidebarRepoLink.href = `/ui/brief/${repository}`;
    currentIssues = [];
    issueSummary.innerHTML = '<span><strong>—</strong> 正在同步 GitHub Issue…</span>';
    issueInbox.innerHTML = '<div class="issue-loading"><span></span><span></span><span></span></div>';
    try {
      const encoded = repository.split('/').map(encodeURIComponent).join('/');
      const result = await fetchJson(`/api/repositories/${encoded}/issues${force ? '?refresh=1' : ''}`);
      currentIssues = result.issues || [];
      renderRepositoryMetrics(result);
      renderIssueInbox(currentIssues);
    } catch (error) {
      issueSummary.innerHTML = '<span><strong>同步失败</strong></span>';
      issueInbox.innerHTML = `<div class="issue-error"><strong>Issue 暂时读不到</strong><span>${escapeHtml(error.message || '请检查 GitHub 登录')}</span></div>`;
    }
  };

  const loadRepositories = async () => {
    if (!repoSwitcher) return;
    try {
      const result = await fetchJson('/api/repositories');
      const repositories = result.repositories || [];
      if (ownedRepoCount) ownedRepoCount.textContent = String(repositories.length);
      repoViewer.textContent = result.viewer ? `@${result.viewer}` : '';
      repoSwitcher.innerHTML = repositories.map((repository) => {
        const suffix = repository.access === 'monitor'
          ? ' · 外部 · 可贡献'
          : (repository.private ? ' · 私有' : '');
        return `<option value="${escapeHtml(repository.full_name)}">${escapeHtml(repository.full_name)}${suffix}</option>`;
      }).join('');
      let remembered = '';
      try { remembered = window.localStorage.getItem('ghe:selected-repository') || ''; } catch (_) {}
      const available = new Set(repositories.map((repository) => repository.full_name));
      const selected = available.has(remembered)
        ? remembered
        : (available.has(result.selected) ? result.selected : repositories[0]?.full_name);
      if (!selected) {
        currentRepository = '';
        repoSwitcher.innerHTML = '<option>还没有添加仓库</option>';
        repoSwitcher.disabled = true;
        if (root) root.classList.add('no-repositories');
        if (repositoryOnboarding) repositoryOnboarding.hidden = false;
        document.documentElement.classList.add('no-repositories');
        return;
      }
      repoSwitcher.disabled = false;
      if (root) root.classList.remove('no-repositories');
      if (repositoryOnboarding) repositoryOnboarding.hidden = true;
      document.documentElement.classList.remove('no-repositories');
      repoSwitcher.value = selected;
      await loadIssues(selected);
    } catch (error) {
      repoSwitcher.innerHTML = '<option>无法读取仓库</option>';
      repoSwitcher.disabled = true;
      issueSummary.innerHTML = '<span><strong>需要连接 GitHub</strong></span>';
      issueInbox.innerHTML = `<div class="issue-error"><strong>仓库列表读取失败</strong><span>${escapeHtml(error.message || '请运行 gh auth login')}</span></div>`;
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
      showToast(`${result.full_name} 已添加到清单`);
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
      try { window.localStorage.setItem('ghe:selected-repository', repository); } catch (_) {}
      loadIssues(repository);
    });
    loadRepairCapabilities();
    loadRepositories();
    loadRepairJobs();
  }
  document.documentElement.dataset.gheUi = 'ready';

  if (refreshIssues) {
    refreshIssues.addEventListener('click', () => loadIssues(currentRepository, true));
  }

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
        '<a class="repo-pill" href="/ui/brief/{repo}">'
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
        '<span id="repo-viewer" class="repo-viewer"></span>'
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
<div class="app-shell">
  <aside class="sidebar">
    <a class="brand" href="/ui/" aria-label="GitHub Engineer 首页">
      <span class="brand-mark">{_ICON['assistant']}</span>
      <h1>GitHub Engineer</h1>
    </a>
    <div class="workspace-label">工作区</div>
    <div class="repo-list">{repo_items}</div>
    <nav class="side-nav" aria-label="主要导航">
      {nav_item('assistant', '/ui/', '助理')}
      {nav_item('briefs', '/ui/briefs', '简报')}
      {nav_item('decisions', '/ui/decisions', '决策')}
    </nav>
    <section class="task-rail" aria-labelledby="task-rail-title">
      <div class="task-rail-heading"><strong id="task-rail-title">修复任务</strong><span class="task-rail-count" id="repair-task-count">0</span></div>
      <div class="task-list" id="repair-task-list"><div class="task-empty">还没有修复任务。<br>从 Issue 开始一个。</div></div>
    </section>
    <div class="sidebar-footer"><span class="online">本地服务在线</span></div>
  </aside>
  <main class="workspace">
    <header class="topbar">
      <div class="topbar-title"><span>{escape(context)}</span><span class="topbar-kicker">GitHub 同步 · 人工确认</span></div>
      {repo_switcher}
      <div class="topbar-status">GitHub Engineer v1.0</div>
    </header>
    <div class="workspace-scroll">{body}</div>
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
<section class="repair-inspector" id="repair-inspector" hidden aria-label="修复任务详情">
  <div class="repair-inspector-header">
    <div><div class="repair-inspector-kicker" id="repair-repository">修复会话</div><h2 id="repair-title">Issue 修复</h2><p id="repair-delivery"></p></div>
    <button class="soft-button" type="button" data-close-repair>返回对话</button>
  </div>
  <div class="repair-progress" aria-label="修复进度">
    <span data-repair-phase="prepare">准备</span>
    <span data-repair-phase="code">编码</span>
    <span data-repair-phase="review">检查</span>
    <span data-repair-phase="publish">PR</span>
  </div>
  <div class="repair-stream" id="repair-stream" aria-live="polite"></div>
  <div class="repair-controls">
    <textarea id="repair-guidance-input" rows="2" placeholder="代码完成后，可以继续给 AI 指导…" disabled></textarea>
    <div class="repair-actions">
      <button class="soft-button" id="repair-guidance-send" type="button" disabled>发送指导</button>
      <button class="primary-button" id="repair-publish" type="button" disabled>确认创建 Draft PR</button>
    </div>
  </div>
</section>
<script src="/ui/app.js" defer></script>
</body>
</html>"""
