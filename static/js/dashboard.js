const state = { data: null, filter: "all", refreshing: false, timer: null };
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

const statusClass = (status) => (status || "UNKNOWN").toLowerCase();
const escapeHtml = (value) => String(value ?? "").replace(/[&<>'"]/g, (character) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
}[character]));

function flattenSections(sections) {
  return Object.values(sections || {}).flat();
}

function setSectionState(section, results) {
  const element = $(`#${section}-state`);
  if (!element) return;
  const statuses = results.map((item) => item.status);
  const status = statuses.includes("CRITICAL") ? "CRITICAL" : statuses.includes("WARNING") ? "WARNING" : statuses.includes("UNKNOWN") ? "UNKNOWN" : "HEALTHY";
  element.textContent = results.length ? status : "Not configured";
  element.className = `section-state ${statusClass(status)}`;
}

function renderOverview(data) {
  const checks = flattenSections(data.sections);
  const counts = checks.reduce((acc, check) => ({ ...acc, [check.status]: (acc[check.status] || 0) + 1 }), {});
  const status = data.overall_status;
  const orbit = $("#health-orbit");
  orbit.className = `health-orbit ${statusClass(status)}`;
  $("#overall-status").textContent = status;
  const copy = {
    HEALTHY: ["All systems operational", "Every configured check is reporting within its expected operating range."],
    WARNING: ["Attention recommended", "One or more checks are approaching a threshold or could not be fully verified."],
    CRITICAL: ["Intervention required", "A critical dependency is unavailable or outside its configured threshold."],
    UNKNOWN: ["Status incomplete", "The monitor could not determine a complete infrastructure state."],
  }[status] || ["Collecting telemetry", "Waiting for the first monitoring cycle to complete."];
  $("#health-headline").textContent = copy[0];
  $("#health-summary").textContent = copy[1];
  $("#healthy-count").textContent = counts.HEALTHY || 0;
  $("#warning-count").textContent = counts.WARNING || 0;
  $("#critical-count").textContent = counts.CRITICAL || 0;
  $("#check-total").textContent = `${checks.length} check${checks.length === 1 ? "" : "s"}`;
  Object.entries(data.sections).forEach(([section, results]) => {
    const count = $(`#${section}-count`);
    if (count) count.textContent = results.length;
    setSectionState(section, results);
  });
}

function metricPercent(check) {
  const value = check.details?.utilization_percent;
  return Number.isFinite(value) ? Math.max(0, Math.min(100, value)) : null;
}

function renderSystem(results = []) {
  const grid = $("#system-grid");
  grid.classList.remove("skeleton-grid");
  if (!results.length) {
    grid.innerHTML = '<div class="empty-row">No system metrics available.</div>';
    return;
  }
  grid.innerHTML = results.map((check) => {
    const percent = metricPercent(check);
    const details = check.details || {};
    const supplemental = details.available_gib !== undefined ? `${details.available_gib} GiB available` : details.path ? `Path ${details.path}` : check.name === "Load Average" ? "1 / 5 / 15 minute" : "Live host reading";
    const threshold = details.warning_threshold !== undefined ? `Warn at ${details.warning_threshold}%` : "";
    return `<article class="metric-card ${statusClass(check.status)}">
      <div class="metric-header"><span>${escapeHtml(check.name)}</span><span class="status-badge ${statusClass(check.status)}">${escapeHtml(check.status)}</span></div>
      <div class="metric-value">${escapeHtml(check.summary)}</div>
      ${percent !== null ? `<div class="meter"><i style="width:${percent}%"></i></div>` : '<div class="meter"><i style="width:100%;opacity:.35"></i></div>'}
      <div class="metric-meta"><span>${escapeHtml(supplemental)}</span><span>${escapeHtml(threshold)}</span></div>
    </article>`;
  }).join("");
}

function renderCheckList(containerId, results = [], icon) {
  const container = $(containerId);
  if (!results.length) {
    container.innerHTML = '<div class="empty-row">No checks configured for this section.</div>';
    return;
  }
  container.innerHTML = results.map((check) => {
    const detail = check.details || {};
    const target = detail.host ? `${detail.host}${detail.port ? `:${detail.port}` : ""}` : detail.url || (detail.expected_status ? `Expected ${detail.expected_status}` : "Configured target");
    return `<div class="check-row">
      <div class="check-ident"><span class="check-icon ${statusClass(check.status)}">${icon}</span><div class="check-name"><strong>${escapeHtml(check.name)}</strong><small>${escapeHtml(target)}</small></div></div>
      <span class="check-summary">${escapeHtml(check.summary)}</span><span class="mini-status ${statusClass(check.status)}" title="${escapeHtml(check.status)}"></span>
    </div>`;
  }).join("");
}

function renderDiagnostics(data) {
  const entries = [];
  Object.entries(data.sections || {}).forEach(([section, results]) => results.forEach((check) => {
    if (check.diagnostics?.length) entries.push({ section, check });
  }));
  $("#diagnostic-count").textContent = `${entries.length} observation${entries.length === 1 ? "" : "s"}`;
  const container = $("#diagnostics-list");
  if (!entries.length) {
    container.className = "diagnostics-empty";
    container.innerHTML = '<span class="empty-icon">✓</span><div><strong>No active incidents</strong><p>Diagnostic guidance will appear here when a check needs attention.</p></div>';
    return;
  }
  container.className = "diagnostic-items";
  container.innerHTML = entries.map(({ section, check }) => `<div class="diagnostic-item"><strong>${escapeHtml(section.toUpperCase())} · ${escapeHtml(check.name)}</strong>${check.diagnostics.map((line) => `<p>${escapeHtml(line)}</p>`).join("")}</div>`).join("");
}

function applyFilter() {
  const filter = state.filter;
  $$('[data-section]').forEach((element) => {
    const section = element.dataset.section;
    const show = filter === "all" || section === filter || (filter === "system" && section === "diagnostics");
    element.classList.toggle("hidden", !show);
  });
  $("#overview").classList.toggle("hidden", filter !== "all");
}

function render(data) {
  state.data = data;
  renderOverview(data);
  renderSystem(data.sections.system || []);
  renderCheckList("#network-list", data.sections.network || [], "⌬");
  renderCheckList("#services-list", data.sections.services || [], "◇");
  renderCheckList("#processes-list", data.sections.processes || [], "≋");
  renderDiagnostics(data);
  const timestamp = new Date(data.timestamp);
  $("#last-updated").textContent = Number.isNaN(timestamp.getTime()) ? data.timestamp : timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  applyFilter();
}

async function refresh() {
  if (state.refreshing) return;
  state.refreshing = true;
  const button = $("#refresh-button");
  button.disabled = true;
  button.classList.add("spinning");
  $("#error-banner").classList.add("hidden");
  try {
    const response = await fetch("/api/health", { headers: { Accept: "application/json" } });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || `Request failed with HTTP ${response.status}`);
    render(data);
    window.clearTimeout(state.timer);
    state.timer = window.setTimeout(refresh, Math.max(5000, data.refresh_interval_seconds * 1000));
  } catch (error) {
    const banner = $("#error-banner");
    banner.textContent = `Dashboard update failed: ${error.message}`;
    banner.classList.remove("hidden");
    state.timer = window.setTimeout(refresh, 10000);
  } finally {
    state.refreshing = false;
    button.disabled = false;
    button.classList.remove("spinning");
  }
}

$("#refresh-button").addEventListener("click", refresh);
$$('.nav-item').forEach((button) => button.addEventListener("click", () => {
  $$('.nav-item').forEach((item) => item.classList.remove("active"));
  button.classList.add("active");
  state.filter = button.dataset.filter;
  applyFilter();
  window.scrollTo({ top: 0, behavior: "smooth" });
}));

refresh();
