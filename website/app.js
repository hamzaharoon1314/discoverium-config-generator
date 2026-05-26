/* ── STATE ── */
let allApps = [];
let currentRepo = null;
let activeFilter = 'all';

/* ── ROUTING ── */
function goHome() {
  showPage('home');
  setBreadcrumb([]);
  history.pushState({page:'home'}, '', '#');
}

function goRepo(repoId) {
  currentRepo = repoId;
  showPage('repo');
  loadRepo(repoId);
  const [author, repoName] = parseRepoId(repoId);
  setBreadcrumb([
    { label: 'repos', action: goHome },
    { label: repoName, current: true }
  ]);
  history.pushState({page:'repo', repo: repoId}, '', '#repo/' + encodeURIComponent(repoId));
}

window.addEventListener('popstate', (e) => {
  const s = e.state;
  if (!s || s.page === 'home') { showPage('home'); setBreadcrumb([]); }
  else if (s.page === 'repo') { goRepo(s.repo); }
});

/* ── INIT ── */
window.addEventListener('DOMContentLoaded', () => {
  const hash = location.hash;
  if (hash.startsWith('#repo/')) {
    const repoId = decodeURIComponent(hash.slice(6));
    goRepo(repoId);
  } else {
    loadHome();
  }
});

/* ── HELPERS ── */
function parseRepoId(id) {
  const sep = id.indexOf('__');
  if (sep === -1) return [id, id];
  return [id.slice(0, sep), id.slice(sep + 2)];
}

function showPage(name) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById('page-' + name).classList.add('active');
}

function setBreadcrumb(crumbs) {
  const el = document.getElementById('breadcrumb');
  if (!crumbs.length) { el.innerHTML = ''; return; }
  el.innerHTML = crumbs.map((c, i) => {
    if (c.current) return `<span class="crumb current">${esc(c.label)}</span>`;
    return `<span class="crumb" onclick="${c.action.name}()">${esc(c.label)}</span><span class="sep">/</span>`;
  }).join('');
}

function esc(str) {
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function showToast(msg) {
  const t = document.getElementById('toast');
  document.getElementById('toast-msg').textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2200);
}

function appIcon(name) {
  const icons = {
    youtube: '▶', music: '♫', instagram: '📸', reddit: '🔺', twitter: '𝕏',
    tiktok: '♪', facebook: '𝔣', discord: '🎮', twitch: '📡', telegram: '✈',
    spotify: '🎵', netflix: '🎬', lightroom: '🌅', strava: '🏃', duolingo: '🦉',
    protonmail: '📧', protonvpn: '🔒', tumblr: '📝', soundcloud: '☁', viber: '📱',
    photomath: '✖', pixiv: '🖼', bilibili: '📺', adguard: '🛡',
  };
  const key = Object.keys(icons).find(k => name.toLowerCase().includes(k));
  return key ? icons[key] : '📦';
}

/* ── HOME ── */
async function loadHome() {
  const container = document.getElementById('repo-container');
  try {
    // FORCE fresh data by appending a timestamp and disabling cache
    const res = await fetch(`./public/data/repos.json?t=${Date.now()}`, { cache: 'no-store' });
    
    if (!res.ok) throw new Error('Failed to fetch repos.json');
    const repos = await res.json();
    document.getElementById('repo-count').textContent = repos.length;
    renderRepos(repos);
  } catch (err) {
    container.innerHTML = `<div class="error-msg">⚠ Could not load repos.json — ${esc(err.message)}</div>`;
  }
}

function renderRepos(repos) {
  const container = document.getElementById('repo-container');
  if (!repos.length) {
    container.innerHTML = '<div class="empty">No repositories found.</div>';
    return;
  }
  container.innerHTML = `<div class="repo-grid">${repos.map(id => {
    const [author, name] = parseRepoId(id);
    const displayName = name.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
    return `
      <div class="repo-card" onclick="goRepo('${esc(id)}')">
        <div class="repo-card-icon">📦</div>
        <div class="repo-card-author">${esc(author)}</div>
        <div class="repo-card-name">${esc(displayName)}</div>
        <div class="repo-card-meta">
          <span class="repo-tag">github</span>
          <span class="repo-tag">non-root</span>
          <span class="repo-arrow">→</span>
        </div>
      </div>`;
  }).join('')}</div>`;
}

/* ── REPO PAGE ── */
async function loadRepo(repoId) {
  const [author, repoName] = parseRepoId(repoId);
  const displayName = repoName.replace(/-/g, ' ');

  document.getElementById('repo-author-display').textContent = author;
  document.getElementById('repo-name-display').textContent = displayName;
  document.getElementById('repo-gh-link').href = `https://github.com/${author}/${repoName}`;
  document.getElementById('stat-apps').textContent = '—';
  document.getElementById('stat-unique').textContent = '—';
  document.getElementById('filter-chips').innerHTML = '';
  document.getElementById('search-input').value = '';
  activeFilter = 'all';
  allApps = [];

  const container = document.getElementById('app-container');
  container.innerHTML = `<div class="loader"><div class="spinner"></div><span class="loader-text">loading packages...</span></div>`;

  try {
    // FORCE fresh data for the specific repo's metadata
    const res = await fetch(`./public/data/repos/${repoId}/metadata/repo.json?t=${Date.now()}`, { cache: 'no-store' });
    
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const apps = await res.json();
    allApps = apps;

    const unique = new Set(apps.map(a => a.package_id)).size;
    document.getElementById('stat-apps').textContent = apps.length;
    document.getElementById('stat-unique').textContent = unique;
    document.getElementById('app-count').textContent = apps.length;

    buildFilterChips(apps);
    renderApps(apps);
  } catch (err) {
    container.innerHTML = `<div class="error-msg">⚠ Could not load metadata — ${esc(err.message)}</div>`;
  }
}

function buildFilterChips(apps) {
  const tags = {};
  apps.forEach(app => {
    const suffix = app.asset_name.replace(/^.*?-([a-z0-9-]+)\.apk$/i, '$1');
    if (app.asset_name.includes('revanced-extended')) tags['rvx-extended'] = (tags['rvx-extended']||0)+1;
    else if (app.asset_name.includes('revanced')) tags['revanced'] = (tags['revanced']||0)+1;
    if (app.asset_name.includes('morphe')) tags['morphe'] = (tags['morphe']||0)+1;
    if (app.asset_name.includes('anddea')) tags['anddea'] = (tags['anddea']||0)+1;
    if (app.asset_name.includes('piko')) tags['piko'] = (tags['piko']||0)+1;
    if (app.asset_name.includes('derevanced')) tags['derevanced'] = (tags['derevanced']||0)+1;
    if (app.asset_name.includes('beta')) tags['beta'] = (tags['beta']||0)+1;
  });

  const el = document.getElementById('filter-chips');
  const all = `<span class="chip active" data-filter="all" onclick="setFilter(this,'all')">All</span>`;
  const rest = Object.entries(tags).sort((a,b)=>b[1]-a[1]).map(([k,v]) =>
    `<span class="chip" data-filter="${esc(k)}" onclick="setFilter(this,'${esc(k)}')">${esc(k)} <span style="opacity:.5">${v}</span></span>`
  ).join('');
  el.innerHTML = all + rest;
}

function setFilter(el, filter) {
  document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
  el.classList.add('active');
  activeFilter = filter;
  filterApps();
}

function filterApps() {
  const q = document.getElementById('search-input').value.toLowerCase();
  let filtered = allApps;

  if (activeFilter !== 'all') {
    filtered = filtered.filter(a => a.asset_name.includes(activeFilter));
  }

  if (q) {
    filtered = filtered.filter(a =>
      a.app_name.toLowerCase().includes(q) ||
      a.package_id.toLowerCase().includes(q) ||
      a.asset_name.toLowerCase().includes(q)
    );
  }

  document.getElementById('app-count').textContent = filtered.length;
  renderApps(filtered);
}

function renderApps(apps) {
  const container = document.getElementById('app-container');
  if (!apps.length) {
    container.innerHTML = '<div class="empty">No packages match your search.</div>';
    return;
  }

  container.innerHTML = `<div class="app-grid">${apps.map((app, i) => {
    const hasStore = app.play_store_url && app.play_store_url.trim();
    const discoveriumFilename = app.discoverium_file ? app.discoverium_file.split('/').pop() : null;
    const dataAttrs = `data-repo="${esc(currentRepo)}" data-pkg="${esc(app.package_id)}" data-disc="${esc(discoveriumFilename || '')}"`;

    return `
      <div class="app-card">
        <div class="app-card-header">
          <div class="app-icon">${appIcon(app.app_name)}</div>
          <div>
            <div class="app-name">${esc(app.app_name)}</div>
            <span class="app-version">v${esc(app.version_name)}</span>
          </div>
        </div>
        <div class="app-details">
          <div class="app-detail-row">
            <span class="app-detail-label">pkg</span>
            <span class="app-detail-value pkg">${esc(app.package_id)}</span>
          </div>
          <div class="app-detail-row">
            <span class="app-detail-label">asset</span>
            <span class="app-detail-value">${esc(app.asset_name)}</span>
          </div>
          ${app.sha256 ? `<div class="app-detail-row">
            <span class="app-detail-label">sha256</span>
            <span class="app-detail-value" style="font-size:0.6rem;opacity:0.6">${esc(app.sha256.slice(0,32))}…</span>
          </div>` : ''}
        </div>
        <div class="app-divider"></div>
        <div class="app-actions">
          <button class="btn btn-obtainium" ${dataAttrs} onclick="addToObtainium(this)">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 5v14M5 12l7 7 7-7"/></svg>
            Obtainium
          </button>
          <button class="btn btn-copy" ${dataAttrs} onclick="copyJson(this)">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
            Copy JSON
          </button>
          ${hasStore ? `<a class="btn btn-store" href="${esc(app.play_store_url)}" target="_blank" rel="noopener">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m3 3 18 9-18 9V3z"/></svg>
            Play Store
          </a>` : ''}
        </div>
      </div>`;
  }).join('')}</div>`;
}

/* ── FETCH DISCOVERIUM JSON ── */
async function fetchDiscoveriumJson(repoId, filename) {
  // FORCE fresh data for the Discoverium configs
  const url = `./public/data/repos/${repoId}/discoverium/${filename}?t=${Date.now()}`;
  const res = await fetch(url, { cache: 'no-store' });
  
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  return res.json();
}

/* ── ADD TO OBTAINIUM ── */
async function addToObtainium(btn) {
  const repo = btn.dataset.repo;
  const disc = btn.dataset.disc;
  if (!disc) { showToast('⚠ No discoverium file available'); return; }

  const orig = btn.innerHTML;
  btn.innerHTML = '<span class="spinner" style="width:12px;height:12px;border-width:1.5px;display:inline-block"></span> Loading…';
  btn.disabled = true;

  try {
    const json = await fetchDiscoveriumJson(repo, disc);
    const encoded = encodeURIComponent(JSON.stringify(json));
    const link = `obtainium://app/${encoded}`;
    window.location.href = link;
    showToast('Opening Obtainium…');
  } catch (err) {
    showToast('⚠ Failed: ' + err.message);
  } finally {
    btn.innerHTML = orig;
    btn.disabled = false;
  }
}

/* ── COPY JSON ── */
async function copyJson(btn) {
  const repo = btn.dataset.repo;
  const disc = btn.dataset.disc;
  if (!disc) { showToast('⚠ No JSON available'); return; }

  const orig = btn.innerHTML;
  btn.innerHTML = '…';
  btn.disabled = true;

  try {
    const json = await fetchDiscoveriumJson(repo, disc);
    await navigator.clipboard.writeText(JSON.stringify(json, null, 2));
    btn.innerHTML = '✓ Copied!';
    btn.classList.add('copied');
    showToast('JSON copied to clipboard');
    setTimeout(() => {
      btn.innerHTML = orig;
      btn.classList.remove('copied');
      btn.disabled = false;
    }, 1800);
  } catch (err) {
    showToast('⚠ Copy failed: ' + err.message);
    btn.innerHTML = orig;
    btn.disabled = false;
  }
}