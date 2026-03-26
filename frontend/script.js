/* ═══════════════════════════════════════════════════════════════
   ResearchMind — script.js
   Connects the frontend to the FastAPI backend
   ═══════════════════════════════════════════════════════════════ */

const API = window.location.origin;
const POLL_INTERVAL = 2000; // ms

// ── DOM refs ─────────────────────────────────────────────────
const searchForm      = document.getElementById('searchForm');
const queryInput      = document.getElementById('queryInput');
const searchBtn       = document.getElementById('searchBtn');
const heroSection     = document.getElementById('heroSection');
const progressSection = document.getElementById('progressSection');
const pipeline        = document.getElementById('pipeline');
const reportSection   = document.getElementById('reportSection');
const reportCard      = document.getElementById('reportCard');
const newSearchBtn    = document.getElementById('newSearchBtn');
const errorBanner     = document.getElementById('errorBanner');
const errorText       = document.getElementById('errorText');
const errorRetry      = document.getElementById('errorRetry');

let currentTaskId = null;
let pollTimer     = null;

// ── Agent icons ──────────────────────────────────────────────
const AGENT_ICONS = {
    'Search Agent':      '&#x1F50D;',
    'Analysis Agent':    '&#x1F52C;',
    'Summary Agent':     '&#x1F4DD;',
    'Synthesis Agent':   '&#x1F9EC;',
    'Opportunity Agent': '&#x1F4A1;',
    'Report Agent':      '&#x1F4C4;',
};

const STATUS_LABELS = {
    pending: 'Waiting',
    running: 'Running',
    done:    'Complete',
    error:   'Failed',
};

// ── Bootstrap ────────────────────────────────────────────────
searchForm.addEventListener('submit', (e) => {
    e.preventDefault();
    startResearch(queryInput.value.trim());
});

document.querySelectorAll('.chip').forEach((chip) => {
    chip.addEventListener('click', () => {
        queryInput.value = chip.dataset.query;
        startResearch(chip.dataset.query);
    });
});

newSearchBtn.addEventListener('click', resetUI);
errorRetry.addEventListener('click', resetUI);

// ── Start Research ───────────────────────────────────────────
async function startResearch(query) {
    if (!query) return;

    // UI state
    searchBtn.classList.add('loading');
    searchBtn.disabled = true;
    hideError();
    reportSection.classList.add('hidden');
    progressSection.classList.remove('hidden');

    // Build pipeline cards
    renderPipelineCards();

    try {
        const res = await fetch(`${API}/api/research`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query }),
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || `Server error ${res.status}`);
        }

        const data = await res.json();
        currentTaskId = data.task_id;

        // Start polling
        pollTimer = setInterval(() => pollStatus(currentTaskId), POLL_INTERVAL);
    } catch (err) {
        showError(err.message);
        searchBtn.classList.remove('loading');
        searchBtn.disabled = false;
    }
}

// ── Poll task status ─────────────────────────────────────────
async function pollStatus(taskId) {
    try {
        const res = await fetch(`${API}/api/research/${taskId}`);
        if (!res.ok) throw new Error(`Status poll failed: ${res.status}`);

        const task = await res.json();

        // Update pipeline cards
        updatePipelineCards(task.agents);

        if (task.status === 'completed') {
            clearInterval(pollTimer);
            pollTimer = null;
            searchBtn.classList.remove('loading');
            searchBtn.disabled = false;
            renderReport(task);
        } else if (task.status === 'failed') {
            clearInterval(pollTimer);
            pollTimer = null;
            searchBtn.classList.remove('loading');
            searchBtn.disabled = false;
            showError(task.error || 'Research pipeline failed.');
        }
    } catch (err) {
        console.error('Poll error:', err);
    }
}

// ── Render 6 pipeline cards ──────────────────────────────────
function renderPipelineCards() {
    const labels = [
        'Search Agent', 'Analysis Agent', 'Summary Agent',
        'Synthesis Agent', 'Opportunity Agent', 'Report Agent',
    ];

    pipeline.innerHTML = labels.map((label, i) => `
        <div class="agent-card" id="agent-${i + 1}">
            <div class="agent-card__step">Step ${i + 1} / 6</div>
            <div class="agent-card__label">${AGENT_ICONS[label] || ''} ${label}</div>
            <span class="agent-card__status status--pending">${STATUS_LABELS.pending}</span>
            <div class="agent-card__detail"></div>
        </div>
    `).join('');
}

// ── Update cards from task.agents array ──────────────────────
function updatePipelineCards(agents) {
    if (!agents) return;
    agents.forEach((a) => {
        const card = document.getElementById(`agent-${a.step}`);
        if (!card) return;

        // Remove old state classes
        card.classList.remove('agent-card--pending', 'agent-card--running', 'agent-card--done', 'agent-card--error');
        card.classList.add(`agent-card--${a.status}`);

        const badge = card.querySelector('.agent-card__status');
        badge.className = `agent-card__status status--${a.status}`;

        if (a.status === 'running') {
            badge.innerHTML = `<span class="dot-spin"></span> ${STATUS_LABELS.running}`;
        } else {
            badge.textContent = STATUS_LABELS[a.status] || a.status;
        }

        const detail = card.querySelector('.agent-card__detail');
        detail.textContent = a.detail || '';
    });
}

// ── Render the final report ──────────────────────────────────
function renderReport(task) {
    const r = task.result;
    if (!r) {
        reportCard.innerHTML = '<p>No report data received.</p>';
        reportSection.classList.remove('hidden');
        return;
    }

    const papersCount   = r.papers ? r.papers.length : 0;
    const analysesCount = r.analyses ? r.analyses.length : 0;
    const summariesCount = r.summaries ? r.summaries.length : 0;

    let html = '';

    // ── Meta chips
    html += `<div class="report-meta">
        <span class="meta-chip">&#x1F4CC; ${escHtml(r.topic)}</span>
        <span class="meta-chip">&#x1F4DA; ${papersCount} papers</span>
        <span class="meta-chip">&#x1F52C; ${analysesCount} analyses</span>
        <span class="meta-chip">&#x1F4DD; ${summariesCount} summaries</span>
    </div>`;

    // ── Paper Summaries
    if (r.summaries && r.summaries.length) {
        html += `<h2>Paper Summaries</h2>`;
        r.summaries.forEach((s, i) => {
            html += renderCollapsible(
                `${i + 1}. ${escHtml(s.paper_title || 'Untitled')}`,
                `<p><strong>Authors:</strong> ${escHtml((s.paper_authors || []).join(', ') || 'Unknown')}</p>
                 <p><strong>Year:</strong> ${escHtml(s.paper_year || 'N/A')}</p>
                 ${mdToHtml(s.summary_text || 'No summary available.')}`,
                i === 0, // first one open
            );
        });
    }

    // ── Synthesis
    const synthesis = r.synthesis || {};
    const synthText = synthesis.final_synthesis || synthesis.initial_synthesis || '';
    if (synthText) {
        html += `<h2>Cross-Paper Synthesis</h2>`;
        html += mdToHtml(synthText);

        if (synthesis.self_reflection) {
            html += renderCollapsible(
                'View Self-Reflection',
                mdToHtml(synthesis.self_reflection),
                false,
            );
        }
    }

    // ── Opportunities
    const opp = r.opportunities || {};
    if (opp.opportunities_text) {
        html += `<h2>Research Gaps &amp; Future Directions</h2>`;
        html += mdToHtml(opp.opportunities_text);
    }

    // ── References
    if (r.papers && r.papers.length) {
        html += `<h2>References</h2><ol>`;
        r.papers.forEach((p) => {
            const authors = (p.authors || ['Unknown']).join(', ');
            html += `<li>${escHtml(authors)} (${escHtml(p.year || 'N/A')}). <em>${escHtml(p.title)}</em>. <a href="${escHtml(p.url || '#')}" target="_blank" rel="noopener">${escHtml(p.source || 'Link')}</a></li>`;
        });
        html += `</ol>`;
    }

    reportCard.innerHTML = html;
    reportSection.classList.remove('hidden');

    // Smooth scroll to report
    reportSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

    // Wire up collapsibles
    reportCard.querySelectorAll('.collapsible__header').forEach((hdr) => {
        hdr.addEventListener('click', () => {
            hdr.parentElement.classList.toggle('open');
        });
    });
}

// ── Helpers ──────────────────────────────────────────────────

function renderCollapsible(title, bodyHtml, startOpen = false) {
    return `
    <div class="collapsible ${startOpen ? 'open' : ''}">
        <div class="collapsible__header">
            <span class="collapsible__title">${title}</span>
            <span class="collapsible__arrow">&#x25BC;</span>
        </div>
        <div class="collapsible__body">${bodyHtml}</div>
    </div>`;
}

/** Very light markdown → HTML (bold, italic, headings, lists, line breaks). */
function mdToHtml(md) {
    if (!md) return '';
    let s = escHtml(md);

    // Headings (### → <h3>, ## → <h2>)  — processed first
    s = s.replace(/^### (.+)$/gm, '<h3>$1</h3>');
    s = s.replace(/^## (.+)$/gm, '<h2>$1</h2>');

    // Bold / italic
    s = s.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    s = s.replace(/\*(.+?)\*/g, '<em>$1</em>');

    // Unordered lists (lines starting with - or *)
    s = s.replace(/^[\-\*] (.+)$/gm, '<li>$1</li>');
    s = s.replace(/((?:<li>.*<\/li>\n?)+)/g, '<ul>$1</ul>');

    // Numbered lists
    s = s.replace(/^\d+\.\s(.+)$/gm, '<li>$1</li>');
    // wrap consecutive <li> not inside <ul> into <ol>
    s = s.replace(/(<li>(?:(?!<\/?[uo]l>).)*<\/li>\n?)+/g, (m) => {
        if (m.includes('<ul>') || m.includes('<ol>')) return m;
        return '<ol>' + m + '</ol>';
    });

    // Line breaks (double newline → paragraph)
    s = s.replace(/\n{2,}/g, '</p><p>');
    s = '<p>' + s + '</p>';

    // Clean up empty <p> tags
    s = s.replace(/<p>\s*<\/p>/g, '');

    return s;
}

function escHtml(str) {
    if (typeof str !== 'string') return '';
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function showError(msg) {
    errorText.textContent = msg;
    errorBanner.classList.remove('hidden');
}

function hideError() {
    errorBanner.classList.add('hidden');
}

function resetUI() {
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
    currentTaskId = null;
    searchBtn.classList.remove('loading');
    searchBtn.disabled = false;
    queryInput.value = '';
    progressSection.classList.add('hidden');
    reportSection.classList.add('hidden');
    hideError();
    heroSection.scrollIntoView({ behavior: 'smooth' });
}
