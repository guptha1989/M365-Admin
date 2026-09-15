/**
 * M365 Administration & AI Governance Platform - Frontend SPA Controller
 */

const API_BASE = '/api/v1';

document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

function initApp() {
    setupNavigation();
    setupModals();
    checkHealth();
    loadModule('ai-governance');
}

// System Health Check
async function checkHealth() {
    const dbBadge = document.getElementById('db-badge');
    const envBadge = document.getElementById('env-badge');
    try {
        const res = await fetch(`${API_BASE}/health`);
        const data = await res.json();
        
        if (envBadge) {
            envBadge.innerText = `ENV: ${data.environment} (Cap: ${data.max_sync_objects || 'Full'})`;
            envBadge.className = `badge badge-env env-${data.environment.toLowerCase()}`;
        }
        if (dbBadge) {
            if (data.db_connected) {
                dbBadge.innerText = 'SQL Express / DB: Connected';
                dbBadge.className = 'badge badge-db db-connected';
            } else {
                dbBadge.innerText = 'DB: Offline';
                dbBadge.className = 'badge badge-db db-offline';
            }
        }
    } catch (e) {
        console.warn('Backend health check error:', e);
        if (dbBadge) {
            dbBadge.innerText = 'DB: Offline';
            dbBadge.className = 'badge badge-db db-offline';
        }
    }
}

// Global Modal and Inspector Setup
window.closeItemDetailModal = function() {
    const itemDetailModal = document.getElementById('item-detail-modal');
    if (itemDetailModal) {
        itemDetailModal.style.display = 'none';
    }
};

function setupModals() {
    const itemDetailModal = document.getElementById('item-detail-modal');
    const apiHubModal = document.getElementById('api-hub-modal');
    const exportModal = document.getElementById('export-modal');
    const teamsModal = document.getElementById('teams-config-modal');

    // Item Detail Modal Close
    document.getElementById('btn-close-item-detail-modal')?.addEventListener('click', () => {
        window.closeItemDetailModal();
    });

    // API Hub Modal
    document.getElementById('btn-open-api-hub')?.addEventListener('click', () => {
        if (apiHubModal) {
            apiHubModal.style.display = 'flex';
            setupAPITabs();
            loadAllAPIIntegrations();
        }
    });
    document.getElementById('btn-close-api-hub')?.addEventListener('click', () => {
        if (apiHubModal) apiHubModal.style.display = 'none';
    });

    // Export Data Modal
    document.getElementById('btn-export-data')?.addEventListener('click', () => {
        if (exportModal) exportModal.style.display = 'flex';
    });
    document.getElementById('btn-close-export-modal')?.addEventListener('click', () => {
        if (exportModal) exportModal.style.display = 'none';
    });

    // Teams Modal
    document.getElementById('btn-open-teams-config')?.addEventListener('click', async () => {
        if (teamsModal) {
            teamsModal.style.display = 'flex';
            const res = await fetch(`${API_BASE}/teams/config`);
            const data = await res.json();
            document.getElementById('teams-governance-phase').value = data.active_governance_phase || 'PHASE_1_REPORTING';
            document.getElementById('teams-webhook-url').value = data.webhook_url || '';
            document.getElementById('teams-channel-name').value = data.channel_name || 'General Admin Channel';
            document.getElementById('teams-daily-digest-enabled').checked = data.daily_digest_enabled;
            document.getElementById('teams-digest-time').value = data.daily_digest_time || '09:00';
        }
    });
    document.getElementById('btn-close-teams-modal')?.addEventListener('click', () => {
        if (teamsModal) teamsModal.style.display = 'none';
    });

    document.getElementById('btn-trigger-teams-digest')?.addEventListener('click', async () => {
        await triggerTeamsDigestNow();
    });

    // Backdrop click listener for all modal overlays
    document.querySelectorAll('.modal-overlay').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        });
    });

    // Press Escape key listener to close any active modal
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' || e.key === 'Esc') {
            document.querySelectorAll('.modal-overlay').forEach(modal => {
                modal.style.display = 'none';
            });
        }
    });
}

// ----------------------------------------------------
// UNIVERSAL ITEM DETAIL INSPECTOR MODAL
// ----------------------------------------------------
function showItemDetailModal(title, itemData) {
    const modal = document.getElementById('item-detail-modal');
    const titleEl = document.getElementById('item-detail-title');
    const bodyEl = document.getElementById('item-detail-body');
    if (!modal || !bodyEl) return;

    titleEl.innerText = title || '🔍 Item Properties Inspector';

    let propertiesRows = '';
    let badgeSummaryHtml = '';

    for (const [key, rawVal] of Object.entries(itemData)) {
        let valStr = '';
        if (rawVal === null || rawVal === undefined) {
            valStr = '<span style="color: var(--text-muted); font-style: italic;">null</span>';
        } else if (typeof rawVal === 'boolean') {
            valStr = rawVal ? '✅ True' : '❌ False';
        } else if (typeof rawVal === 'object') {
            valStr = `<pre style="margin:0; background:#0f172a; padding:6px; border-radius:4px; font-size:0.8rem; overflow-x:auto;">${JSON.stringify(rawVal, null, 2)}</pre>`;
        } else {
            valStr = String(rawVal);
        }

        const keyUpper = key.toUpperCase();
        if (keyUpper.includes('STATUS') || keyUpper.includes('SEVERITY') || keyUpper.includes('RISK') || keyUpper.includes('DEPARTMENT') || keyUpper.includes('CATEGORY')) {
            badgeSummaryHtml += `<span class="badge" style="background: rgba(59, 130, 246, 0.2); font-size: 0.8rem; margin-right: 6px; margin-bottom: 6px; display: inline-block;"><strong>${cleanKeyLabel(key)}:</strong> ${rawVal}</span>`;
        }

        propertiesRows += `
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                <td style="font-weight: 600; width: 35%; color: var(--text-secondary); padding: 8px; vertical-align: top;">${cleanKeyLabel(key)}</td>
                <td style="padding: 8px; vertical-align: top; word-break: break-word;">${valStr}</td>
            </tr>
        `;
    }

    const formattedJson = JSON.stringify(itemData, null, 2);

    bodyEl.innerHTML = `
        ${badgeSummaryHtml ? `<div style="margin-bottom: 1rem; padding: 8px; background: rgba(15, 23, 42, 0.6); border-radius: 6px;">${badgeSummaryHtml}</div>` : ''}

        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            <h4 style="margin: 0; color: var(--accent-blue);">All Available Fields (${Object.keys(itemData).length})</h4>
            <button class="btn btn-secondary btn-sm" onclick="navigator.clipboard.writeText(decodeURIComponent('${encodeURIComponent(formattedJson)}')); alert('📋 JSON payload copied to clipboard!');">📋 Copy JSON</button>
        </div>

        <table style="width: 100%; border-collapse: collapse; margin-bottom: 1.5rem; font-size: 0.9rem;">
            <tbody>${propertiesRows}</tbody>
        </table>

        <details style="margin-top: 1rem;">
            <summary style="cursor: pointer; font-weight: 600; color: var(--text-muted); font-size: 0.85rem; padding: 4px 0;">🔍 Raw JSON Payload View</summary>
            <pre style="background: #090d16; padding: 12px; border-radius: 6px; font-size: 0.8rem; overflow-x: auto; color: #a5f3fc; border: 1px solid #1e293b; margin-top: 6px;">${formattedJson}</pre>
        </details>
    `;

    modal.style.display = 'flex';
}

function cleanKeyLabel(key) {
    return key
        .replace(/([A-Z])/g, ' $1')
        .replace(/_/g, ' ')
        .replace(/^./, str => str.toUpperCase())
        .trim();
}

// ----------------------------------------------------
// FULL-FIELD EXPORT UTILITIES (CSV / JSON)
// ----------------------------------------------------
function exportDatasetToCSV(data, fileName = 'M365_Admin_Export') {
    if (!data || !data.length) {
        alert('No data available for export.');
        return;
    }
    const keys = Array.from(new Set(data.flatMap(obj => Object.keys(obj))));
    const csvRows = [];

    csvRows.push(keys.map(k => `"${k.replace(/"/g, '""')}"`).join(','));

    data.forEach(item => {
        const rowValues = keys.map(key => {
            let val = item[key];
            if (val === null || val === undefined) val = '';
            else if (typeof val === 'object') val = JSON.stringify(val);
            else val = String(val);
            return `"${val.replace(/"/g, '""')}"`;
        });
        csvRows.push(rowValues.join(','));
    });

    const csvContent = 'data:text/csv;charset=utf-8,\uFEFF' + csvRows.join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `${fileName}_${new Date().toISOString().slice(0,10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function exportDatasetToJSON(data, fileName = 'M365_Admin_Export') {
    if (!data || !data.length) {
        alert('No data available for export.');
        return;
    }
    const jsonStr = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${fileName}_${new Date().toISOString().slice(0,10)}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

// ----------------------------------------------------
// UNIVERSAL INTERACTIVE DATA TABLE & FILTER SUITE
// ----------------------------------------------------
function renderInteractiveTable(container, options) {
    const {
        data = [],
        columns = [],
        title = '',
        subtitle = '',
        exportFileName = 'M365_Admin_Export',
        filterFields = [],
        tableId = 'tbl_' + Math.random().toString(36).substr(2, 7)
    } = options;

    const targetEl = typeof container === 'string' ? document.getElementById(container) : container;
    if (!targetEl) return;

    // Dynamic Column Registration: Automatically extract all keys present in dataset
    if (data && data.length > 0) {
        const existingKeys = new Set(columns.map(c => c.key));
        const allItemKeys = new Set();
        data.forEach(item => {
            if (item && typeof item === 'object') {
                Object.keys(item).forEach(k => allItemKeys.add(k));
            }
        });
        allItemKeys.forEach(k => {
            if (!existingKeys.has(k)) {
                columns.push({
                    key: k,
                    label: cleanKeyLabel(k),
                    visible: false
                });
            }
        });
    }

    let visibleCols = columns.filter(c => c.visible !== false).map(c => c.key);
    let currentSearch = '';
    let currentFilters = {};
    let sortKey = columns[0]?.key || '';
    let sortAsc = true;

    function getFilteredData() {
        return data.filter(item => {
            if (currentSearch) {
                const searchLower = currentSearch.toLowerCase();
                const matchAny = Object.values(item).some(val => 
                    val !== null && val !== undefined && String(val).toLowerCase().includes(searchLower)
                );
                if (!matchAny) return false;
            }
            for (const [fKey, fVal] of Object.entries(currentFilters)) {
                if (fVal && String(item[fKey]) !== String(fVal)) {
                    return false;
                }
            }
            return true;
        }).sort((a, b) => {
            let valA = a[sortKey] ?? '';
            let valB = b[sortKey] ?? '';
            if (typeof valA === 'string') valA = valA.toLowerCase();
            if (typeof valB === 'string') valB = valB.toLowerCase();
            if (valA < valB) return sortAsc ? -1 : 1;
            if (valA > valB) return sortAsc ? 1 : -1;
            return 0;
        });
    }

    function renderDOM() {
        const filtered = getFilteredData();
        const activeCols = columns.filter(c => visibleCols.includes(c.key));

        const headerHtml = activeCols.map(c => `
            <th style="cursor: pointer; user-select: none;" data-sort="${c.key}">
                ${c.label} ${sortKey === c.key ? (sortAsc ? '▲' : '▼') : ''}
            </th>
        `).join('');

        const rowsHtml = filtered.length > 0 ? filtered.map((item, idx) => `
            <tr class="interactive-row" data-idx="${idx}" style="cursor: pointer;" title="Click to inspect all item details">
                ${activeCols.map(c => {
                    let cellVal = item[c.key];
                    let formatted = c.format ? c.format(cellVal, item) : (cellVal !== undefined && cellVal !== null ? String(cellVal) : '');
                    return `<td>${formatted}</td>`;
                }).join('')}
            </tr>
        `).join('') : `<tr><td colspan="${activeCols.length || 1}" style="text-align: center; color: var(--text-muted); padding: 2rem;">No matching items found.</td></tr>`;

        const countEl = document.getElementById(`count_${tableId}`);
        if (countEl) countEl.innerText = `Showing ${filtered.length} of ${data.length} items`;

        const thead = document.getElementById(`thead_${tableId}`);
        const tbody = document.getElementById(`tbody_${tableId}`);
        if (thead) thead.innerHTML = `<tr>${headerHtml}</tr>`;
        if (tbody) tbody.innerHTML = rowsHtml;

        document.querySelectorAll(`#tbody_${tableId} .interactive-row`).forEach(rowEl => {
            rowEl.addEventListener('click', () => {
                const idx = rowEl.getAttribute('data-idx');
                const clickedItem = filtered[idx];
                if (clickedItem) {
                    showItemDetailModal(`🔍 ${title || 'Item'} Detail Inspector`, clickedItem);
                }
            });
        });

        document.querySelectorAll(`#thead_${tableId} th`).forEach(thEl => {
            thEl.addEventListener('click', () => {
                const key = thEl.getAttribute('data-sort');
                if (sortKey === key) {
                    sortAsc = !sortAsc;
                } else {
                    sortKey = key;
                    sortAsc = true;
                }
                renderDOM();
            });
        });
    }

    let filterDropdownsHtml = filterFields.map(fKey => {
        const colDef = columns.find(c => c.key === fKey) || { label: cleanKeyLabel(fKey) };
        const uniqueVals = Array.from(new Set(data.map(i => i[fKey]).filter(v => v !== undefined && v !== null))).sort();
        if (!uniqueVals.length) return '';
        return `
            <div style="display: flex; flex-direction: column; gap: 2px;">
                <label style="font-size: 0.72rem; color: var(--text-muted); text-transform: uppercase;">Filter ${colDef.label}:</label>
                <select class="form-control field-filter-select" data-field="${fKey}" style="padding: 4px 8px; font-size: 0.85rem; height: 32px;">
                    <option value="">All ${colDef.label}s</option>
                    ${uniqueVals.map(v => `<option value="${v}">${v}</option>`).join('')}
                </select>
            </div>
        `;
    }).join('');

    const colCheckboxesHtml = columns.map(c => `
        <label style="display: flex; align-items: center; gap: 8px; padding: 6px 10px; cursor: pointer; font-size: 0.85rem; color: #201F1E; border-bottom: 1px solid #F3F2F1;">
            <input type="checkbox" class="col-toggle-cb" data-key="${c.key}" ${visibleCols.includes(c.key) ? 'checked' : ''} style="width: auto;" />
            <span>${c.label}</span>
        </label>
    `).join('');

    targetEl.innerHTML = `
        <div class="card" style="padding: 0; overflow: hidden; margin-top: 1rem; border: 1px solid var(--border-color);">
            ${title ? `<div style="padding: 1rem 1.2rem; border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center; background: #F8F9FA;">
                <div>
                    <h3 style="margin: 0; font-size: 1.1rem; color: #201F1E;">${title}</h3>
                    ${subtitle ? `<p style="margin: 2px 0 0 0; color: var(--text-secondary); font-size: 0.85rem;">${subtitle}</p>` : ''}
                </div>
                <div style="font-size: 0.85rem; color: var(--text-muted);" id="count_${tableId}">Showing ${data.length} of ${data.length} items</div>
            </div>` : ''}

            <div style="background: var(--card-bg); padding: 0.8rem 1.2rem; border-bottom: 1px solid var(--border-color); display: flex; flex-wrap: wrap; gap: 12px; align-items: flex-end; justify-content: space-between;">
                
                <div style="display: flex; flex-wrap: wrap; gap: 10px; align-items: flex-end; flex: 1;">
                    <div style="display: flex; flex-direction: column; gap: 2px; min-width: 220px;">
                        <label style="font-size: 0.72rem; color: var(--text-muted); text-transform: uppercase;">🔍 Global Search:</label>
                        <input type="text" class="form-control search-input" placeholder="Search across all fields..." style="padding: 4px 8px; font-size: 0.85rem; height: 32px;" />
                    </div>

                    ${filterDropdownsHtml}

                    <button class="btn btn-secondary btn-reset-tbl" style="height: 32px; padding: 4px 10px; font-size: 0.8rem; margin-bottom: 0;">🔄 Reset</button>
                </div>

                <div style="display: flex; gap: 8px; align-items: center; position: relative;">
                    <div style="position: relative;">
                        <button class="btn btn-secondary btn-toggle-cols-menu" style="height: 32px; padding: 4px 10px; font-size: 0.8rem;">⚙️ Select Fields ▾</button>
                        <div class="cols-dropdown-menu" style="display: none; position: absolute; right: 0; top: 36px; background: #FFFFFF; border: 1px solid #EDEBE9; border-radius: 6px; box-shadow: 0 4px 16px rgba(0,0,0,0.15); z-index: 100; min-width: 240px; max-height: 320px; overflow-y: auto;">
                            <div style="font-weight: 600; font-size: 0.8rem; padding: 8px 10px; background: #F3F2F1; color: #201F1E; border-bottom: 1px solid #EDEBE9;">Show/Hide Columns</div>
                            ${colCheckboxesHtml}
                        </div>
                    </div>

                    <button class="btn btn-primary btn-exp-csv" style="height: 32px; padding: 4px 12px; font-size: 0.8rem;">📥 Download All Fields (CSV)</button>
                    <button class="btn btn-secondary btn-exp-json" style="height: 32px; padding: 4px 10px; font-size: 0.8rem;">JSON</button>
                </div>

            </div>

            <div class="table-container" style="border: none; border-radius: 0;">
                <table class="data-table" id="tbl_${tableId}">
                    <thead id="thead_${tableId}"></thead>
                    <tbody id="tbody_${tableId}"></tbody>
                </table>
            </div>
        </div>
    `;

    const searchInput = targetEl.querySelector('.search-input');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            currentSearch = e.target.value;
            renderDOM();
        });
    }

    targetEl.querySelectorAll('.field-filter-select').forEach(sel => {
        sel.addEventListener('change', (e) => {
            const fKey = sel.getAttribute('data-field');
            currentFilters[fKey] = e.target.value;
            renderDOM();
        });
    });

    const resetBtn = targetEl.querySelector('.btn-reset-tbl');
    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            currentSearch = '';
            currentFilters = {};
            if (searchInput) searchInput.value = '';
            targetEl.querySelectorAll('.field-filter-select').forEach(sel => sel.value = '');
            renderDOM();
        });
    }

    const colsBtn = targetEl.querySelector('.btn-toggle-cols-menu');
    const colsMenu = targetEl.querySelector('.cols-dropdown-menu');
    if (colsBtn && colsMenu) {
        colsBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            colsMenu.style.display = colsMenu.style.display === 'none' ? 'block' : 'none';
        });
        document.addEventListener('click', () => colsMenu.style.display = 'none');
        colsMenu.addEventListener('click', (e) => e.stopPropagation());
    }

    targetEl.querySelectorAll('.col-toggle-cb').forEach(cb => {
        cb.addEventListener('change', (e) => {
            const k = cb.getAttribute('data-key');
            if (e.target.checked) {
                if (!visibleCols.includes(k)) visibleCols.push(k);
            } else {
                visibleCols = visibleCols.filter(col => col !== k);
            }
            renderDOM();
        });
    });

    const expCsvBtn = targetEl.querySelector('.btn-exp-csv');
    if (expCsvBtn) {
        expCsvBtn.addEventListener('click', () => {
            const currentFiltered = getFilteredData();
            exportDatasetToCSV(currentFiltered, exportFileName);
        });
    }

    const expJsonBtn = targetEl.querySelector('.btn-exp-json');
    if (expJsonBtn) {
        expJsonBtn.addEventListener('click', () => {
            const currentFiltered = getFilteredData();
            exportDatasetToJSON(currentFiltered, exportFileName);
        });
    }

    renderDOM();
}

// ----------------------------------------------------
// FAILED UPDATES REPORT RENDER
// ----------------------------------------------------
async function renderFailedUpdates(container) {
    const res = await fetch(`${API_BASE}/reports/failed-updates`);
    const data = await res.json();
    const items = data.failed_updates || [];

    const criticalCount = data.critical_failures_count || items.filter(i => i.severity === 'CRITICAL').length;
    const osFailures = data.categories_breakdown?.['Windows OS'] || items.filter(i => i.category === 'Windows OS').length;
    const m365Failures = data.categories_breakdown?.['M365 Apps'] || items.filter(i => i.category === 'M365 Apps').length;
    const defenderFailures = data.categories_breakdown?.['Defender Security'] || items.filter(i => i.category === 'Defender Security').length;

    const cardsHtml = `
        <div class="grid-cards" style="margin-bottom: 1.5rem;">
            <div class="card" style="border-left: 4px solid var(--accent-red);">
                <div class="card-title">⚠️ Total Failed Updates</div>
                <h3 style="font-size: 2rem; margin: 0.5rem 0; color: var(--accent-red);">${data.total_failed_updates}</h3>
                <p style="color: var(--text-secondary); font-size: 0.85rem;">Active update installation errors</p>
            </div>
            <div class="card" style="border-left: 4px solid #f87171;">
                <div class="card-title">🚨 Critical Failures</div>
                <h3 style="font-size: 2rem; margin: 0.5rem 0; color: #f87171;">${criticalCount}</h3>
                <p style="color: var(--text-secondary); font-size: 0.85rem;">Requiring immediate remediation</p>
            </div>
            <div class="card">
                <div class="card-title">💻 Windows OS Updates</div>
                <h3 style="font-size: 2rem; margin: 0.5rem 0;">${osFailures}</h3>
                <p style="color: var(--text-secondary); font-size: 0.85rem;">Win11/Win10 OS cumulative updates</p>
            </div>
            <div class="card">
                <div class="card-title">📦 M365 & Defender</div>
                <h3 style="font-size: 2rem; margin: 0.5rem 0; color: var(--accent-blue);">${m365Failures + defenderFailures}</h3>
                <p style="color: var(--text-secondary); font-size: 0.85rem;">Apps Click-to-Run & Security Signatures</p>
            </div>
        </div>
    `;

    container.innerHTML = cardsHtml + `<div id="failed-updates-tbl-container"></div>`;

    renderInteractiveTable(document.getElementById('failed-updates-tbl-container'), {
        title: 'Failed Update Telemetry & Device Audit',
        subtitle: 'Click any row to inspect all item properties, error tracebacks, and remediation steps. Select fields or filter by severity/department.',
        data: items,
        exportFileName: 'M365_Failed_Updates_Report',
        filterFields: ['severity', 'category', 'status', 'department'],
        columns: [
            { key: 'id', label: 'ID', format: val => `<strong>${val}</strong>` },
            { key: 'deviceName', label: 'Device Name', format: val => `<span style="font-weight:600;">${val}</span>` },
            { key: 'userPrincipalName', label: 'User Principal Name' },
            { key: 'updateType', label: 'Update Type' },
            { key: 'updateId', label: 'Update Package / KB' },
            { key: 'errorCode', label: 'Error Code', format: val => `<code style="color: #f87171;">${val}</code>` },
            { key: 'severity', label: 'Severity', format: val => `<span class="badge" style="background: ${val === 'CRITICAL' ? '#dc2626' : (val === 'HIGH' ? '#f59e0b' : '#3b82f6')}; color: white;">${val}</span>` },
            { key: 'category', label: 'Category' },
            { key: 'status', label: 'Status', format: val => `<span class="badge" style="background: rgba(239, 68, 68, 0.2); color: #f87171;">${val}</span>` },
            { key: 'lastAttempt', label: 'Last Attempt' }
        ]
    });
}

// Navigation & Routing with Collapsible/Expandable Categories
function setupNavigation() {
    const categoryHeaders = document.querySelectorAll('.nav-category-header');
    const navItems = document.querySelectorAll('.nav-item');

    // Handle Category Header Expand / Collapse toggle
    categoryHeaders.forEach(header => {
        header.addEventListener('click', (e) => {
            e.preventDefault();
            const parentCat = header.closest('.nav-category');
            if (parentCat) {
                parentCat.classList.toggle('collapsed');
            }
            
            navItems.forEach(n => n.classList.remove('active'));
            header.classList.add('active');

            const module = header.getAttribute('data-module');
            if (module) loadModule(module);
        });
    });

    // Handle Sub-item Navigation
    const subItems = document.querySelectorAll('.nav-subitems .nav-item');
    subItems.forEach(sub => {
        sub.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            const parentCat = sub.closest('.nav-category');
            if (parentCat) {
                parentCat.classList.remove('collapsed');
            }

            navItems.forEach(n => n.classList.remove('active'));
            sub.classList.add('active');

            const module = sub.getAttribute('data-module');
            if (module) loadModule(module);
        });
    });
}

// Module Content Loader
async function loadModule(moduleName) {
    const container = document.getElementById('module-container');
    const titleEl = document.getElementById('page-title');
    const subTitleEl = document.getElementById('page-subtitle');

    container.innerHTML = `<div style="padding: 2rem; text-align: center;">⚡ Loading ${moduleName}...</div>`;

    try {
        switch (moduleName) {
            // CATEGORY 1: REPORTING
            case 'reporting-overview':
                titleEl.innerText = "Category 1: Reporting Dashboard";
                subTitleEl.innerText = "Executive telemetry across Mailbox Inbox Rules, Retention Policies, and Litigation Holds.";
                await renderReportingOverview(container);
                break;
            case 'mailbox-reports':
                titleEl.innerText = "Reporting: Mailbox Reports";
                subTitleEl.innerText = "Inbox rules (Forwarding/Domains), Retention policies by department, and Litigation Hold audit.";
                await renderMailboxReports(container);
                break;
            case 'inbox-rules-report':
                titleEl.innerText = "Reporting: Inbox Rule Report";
                subTitleEl.innerText = "Detailed report of user inbox rules, auto-forwarding categories (Internal vs External), target domain filters, and security risk indicators.";
                await renderInboxRulesReport(container);
                break;
            case 'failed-updates':
                titleEl.innerText = "Reporting: Failed Updates Report";
                subTitleEl.innerText = "Comprehensive audit of M365 Apps, Windows OS, Defender, and Intune update errors across tenant devices.";
                await renderFailedUpdates(container);
                break;

            // CATEGORY 2: AZURE AD
            case 'azure-ad-overview':
            case 'azure-ad-inactive':
                titleEl.innerText = "Azure AD: Inactive Users";
                subTitleEl.innerText = "Inactivity analysis based on last 60 days, 90 days, and 120 days of inactivity.";
                await renderAzureADInactive(container);
                break;
            case 'azure-ad-licenses':
                titleEl.innerText = "Azure AD: Licenses Summary";
                subTitleEl.innerText = "Used vs Available licenses categorized by Paid and Trial subscriptions.";
                await renderAzureADLicenses(container);
                break;
            case 'azure-ad-risky':
            case 'security-overview':
            case 'security-risky-users':
                titleEl.innerText = "Azure AD & Security: Risky Users Summary";
                subTitleEl.innerText = "Categorized risk levels (High, Medium, Low), risk states, and security detection details.";
                await renderAzureADRiskyUsers(container);
                break;

            // CATEGORY 3: MAILFLOW
            case 'mailflow-overview':
            case 'mailflow-volume':
                titleEl.innerText = "Mailflow: Email Volume (Sent / Received)";
                subTitleEl.innerText = "Email throughput in last 30, 90, and 120 days, sender-wise and recipient-wise.";
                await renderMailflowVolume(container);
                break;
            case 'mailflow-connectors':
                titleEl.innerText = "Mailflow: Connectors Summary";
                subTitleEl.innerText = "Inbound & Outbound connector configurations, status, and TLS details.";
                await renderMailflowConnectors(container);
                break;
            case 'mailflow-transport-rules':
                titleEl.innerText = "Mailflow: Transport Rule Summary";
                subTitleEl.innerText = "Exchange mail flow rules, actions, and match conditions.";
                await renderMailflowTransportRules(container);
                break;
            case 'mailflow-autoforward':
                titleEl.innerText = "Mailflow: Auto-Forwarding Details";
                subTitleEl.innerText = "External auto-forwarding rules based on sender and recipient.";
                await renderMailflowAutoForward(container);
                break;

            // CATEGORY 4: COLLABORATION
            case 'collaboration-overview':
            case 'teams-call-quality':
                titleEl.innerText = "Collaboration: Teams Call Quality Report";
                subTitleEl.innerText = "Audio quality ratings, jitter, packet loss %, and network subnet metrics.";
                await renderTeamsCallQuality(container);
                break;
            case 'sp-onedrive-trend':
                titleEl.innerText = "Collaboration: SharePoint & OneDrive 60-Day Trend";
                subTitleEl.innerText = "Site storage usage trends, active user counts, and 60-day activity.";
                await renderSPOneDriveTrend(container);
                break;
            case 'external-sharing-audit':
                titleEl.innerText = "Collaboration: External Sharing & DLP Audit";
                subTitleEl.innerText = "External access links, guest permissions, and sensitive data DLP detection.";
                await renderExternalSharingAudit(container);
                break;
            case 'inactive-files':
                titleEl.innerText = "Collaboration: Inactive Files & Libraries";
                subTitleEl.innerText = "Unaccessed files, folders, and libraries based on last accessed attribute.";
                await renderInactiveFiles(container);
                break;
            case 'file-type-data':
                titleEl.innerText = "Collaboration: File Type Data & URLs";
                subTitleEl.innerText = "Library file extension breakdown (.xlsx, .pdf, .docx) with direct SharePoint file URLs.";
                await renderFileTypeData(container);
                break;

            // CATEGORY 5: AUDITING
            case 'auditing-overview':
            case 'app-audit-log':
                titleEl.innerText = "Auditing: App Action Audit Log";
                subTitleEl.innerText = "Complete history of administrative changes made by users inside this application.";
                await renderAppAuditLogs(container);
                break;

            // CATEGORY 7: MANAGEMENT
            case 'management-overview':
            case 'mgmt-distribution-groups':
                titleEl.innerText = "Management: Distribution Group Module";
                subTitleEl.innerText = "Naming convention department mapping, member additions, attribute changes, and settings.";
                await renderMgmtDistributionGroups(container);
                break;
            case 'mgmt-mailboxes':
                titleEl.innerText = "Management: User Mailbox Module";
                subTitleEl.innerText = "Mailbox creation, Full Access / Send As permissions, calendar permissions, and settings.";
                await renderMgmtMailboxes(container);
                break;
            case 'mgmt-shared-mailboxes':
                titleEl.innerText = "Management: Shared Mailbox Management";
                subTitleEl.innerText = "Creation, naming convention mapping to teams/departments, member additions, permissions & settings.";
                await renderMgmtSharedMailboxes(container);
                break;
            case 'mgmt-room-mailboxes':
                titleEl.innerText = "Management: Room Mailbox Module";
                subTitleEl.innerText = "Room creation, booking details per room, calendar booking permissions, and delegate settings.";
                await renderMgmtRoomMailboxes(container);
                break;
            case 'mgmt-inbox-rules':
                titleEl.innerText = "Management: Inbox Rule Management";
                subTitleEl.innerText = "Create, status-toggle, and delete user and shared mailbox inbox rules with automated audit logging.";
                await renderMgmtInboxRules(container);
                break;

            // CATEGORY 8: AI & SYSTEM INTEGRATIONS
            case 'ai-governance':
                titleEl.innerText = "AI Governance Feed";
                subTitleEl.innerText = "Actionable LLM recommendations, license savings, and threat mitigation.";
                await renderAIGovernance(container);
                break;
            case 'policy-dashboard':
                titleEl.innerText = "Policy Dashboard & Tenant Conditions";
                subTitleEl.innerText = "View, manage, and update rule conditions and compliance thresholds across all dashboards and reports.";
                await renderPolicyDashboard(container);
                break;
            case 'teams-integration':
                titleEl.innerText = "Microsoft Teams Bot & Daily Digest";
                subTitleEl.innerText = "Interactive Teams command center, daily proactive AI recommendation cards, and bot simulation.";
                await renderTeamsIntegration(container);
                break;
            case 'outages':
                titleEl.innerText = "M365 Outage Dashboard & Map";
                subTitleEl.innerText = "Live M365 Service Health API parser with regional outage tracking.";
                await renderOutages(container);
                break;
            case 'legal-hold':
                titleEl.innerText = "Legal Hold Case Management";
                subTitleEl.innerText = "Legal hold creation requests, custodian tracking, and In-Place hold details.";
                await renderLegalHold(container);
                break;
            case 'api-hub-open':
                const modal = document.getElementById('api-hub-modal');
                if (modal) modal.style.display = 'flex';
                await renderAIGovernance(container);
                break;
            default:
                container.innerHTML = `<div>Module ${moduleName} ready.</div>`;
        }
    } catch (err) {
        console.error(`Failed to load module ${moduleName}:`, err);
        container.innerHTML = `
            <div class="card" style="border-left: 4px solid var(--accent-red); margin-top: 1rem;">
                <h4 style="color: var(--accent-red); margin-top: 0;">⚠️ Error Loading Module (${moduleName})</h4>
                <p style="color: var(--text-secondary);">${err.message || 'Failed to fetch data from API endpoint.'}</p>
                <button class="btn btn-secondary" onclick="loadModule('${moduleName}')">🔄 Retry</button>
            </div>
        `;
    }
}

// 1. AI Governance Module Render
let currentAIRecsData = [];

async function renderAIGovernance(container) {
    try {
        const [recsRes, teamsRes] = await Promise.all([
            fetch(`${API_BASE}/ai-governance/recommendations`),
            fetch(`${API_BASE}/teams/config`)
        ]);
        const recs = await recsRes.json();
        currentAIRecsData = recs;
        const teamsConfig = await teamsRes.json();

        const currentPhase = teamsConfig.active_governance_phase || 'PHASE_1_REPORTING';
        const phaseLabels = {
            'PHASE_1_REPORTING': 'Phase 1: Reporting Only (Manual Execution)',
            'PHASE_2_SEMI_AUTOMATED': 'Phase 2: Semi-Automated (Prompt & Review Approval)',
            'PHASE_3_FULLY_AUTOMATED': 'Phase 3: Fully Automated (Policy-Driven Execution)'
        };

        const costItems = recs.filter(r => r.recommendation_type === 'COST_SAVING' || r.potential_savings_usd > 0);
        const securityItems = recs.filter(r => r.recommendation_type === 'SECURITY' || r.potential_savings_usd === 0);
        const totalSavings = costItems.reduce((acc, curr) => acc + (curr.potential_savings_usd || 0), 0);

        // Get unique benefit categories
        const allCategories = Array.from(new Set(recs.map(r => r.benefit_category || cleanKeyLabel(r.category)))).filter(Boolean).sort();

        container.innerHTML = `
            <!-- Top KPI Summary Header -->
            <div class="grid-cards" style="margin-bottom: 1.5rem;">
                <div class="card" style="border-left: 4px solid var(--accent-green);">
                    <div class="card-title">💰 Projected Annual Savings</div>
                    <h2 style="font-size: 2.2rem; margin: 0.4rem 0; color: var(--accent-green);">+$${totalSavings.toLocaleString()}<span style="font-size: 1rem; color: var(--text-secondary);">/yr</span></h2>
                    <p style="color: var(--text-secondary); font-size: 0.85rem; margin: 0;">Across ${costItems.length} cost optimization actions</p>
                </div>
                <div class="card" style="border-left: 4px solid var(--accent-blue);">
                    <div class="card-title">🛡️ Security & Threat Protections</div>
                    <h2 style="font-size: 2.2rem; margin: 0.4rem 0; color: var(--accent-blue);">${securityItems.length} Active Protections</h2>
                    <p style="color: var(--text-secondary); font-size: 0.85rem; margin: 0;">Categorized by risk & compliance benefits</p>
                </div>
                <div class="card" style="border-left: 4px solid var(--accent-purple); display: flex; flex-direction: column; justify-content: space-between;">
                    <div>
                        <div class="card-title">⚙️ Active Tenant Governance Mode</div>
                        <div style="font-size: 1.05rem; font-weight: 600; margin-top: 0.5rem; color: #a78bfa;">${phaseLabels[currentPhase]}</div>
                    </div>
                    <button class="btn btn-secondary btn-sm" id="btn-quick-teams-config" style="align-self: flex-start; margin-top: 10px;">⚙️ Change Phase Mode</button>
                </div>
            </div>

            <!-- Recommendation Control & Filter Bar -->
            <div style="background: var(--card-bg); padding: 1rem 1.2rem; border-radius: 10px; border: 1px solid var(--border-color); margin-bottom: 1.5rem; display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 12px;">
                <div style="display: flex; gap: 8px; flex-wrap: wrap;" id="ai-tab-buttons">
                    <button class="btn btn-primary ai-tab-btn active" data-tab="ALL">All Insights (${recs.length})</button>
                    <button class="btn btn-secondary ai-tab-btn" data-tab="COST">💰 Cost Saving Items (${costItems.length})</button>
                    <button class="btn btn-secondary ai-tab-btn" data-tab="SECURITY">🛡️ Security Recommendations (${securityItems.length})</button>
                </div>
                <div style="display: flex; gap: 10px; align-items: center;">
                    <select id="ai-category-filter" class="form-control" style="height: 34px; padding: 4px 10px; font-size: 0.85rem; min-width: 220px;">
                        <option value="">All Benefit Categories</option>
                        ${allCategories.map(c => `<option value="${c}">${c}</option>`).join('')}
                    </select>
                    <button class="btn btn-primary" onclick="refreshAI()" style="height: 34px; padding: 4px 12px; font-size: 0.85rem;">🔄 Refresh Insights</button>
                </div>
            </div>

            <!-- Content Area for Split Recommendation Sections -->
            <div id="ai-recommendations-content-area"></div>
        `;

        document.getElementById('btn-quick-teams-config')?.addEventListener('click', () => {
            const modal = document.getElementById('teams-config-modal');
            if (modal) modal.style.display = 'flex';
        });

        let activeTab = 'ALL';
        let activeCategory = '';

        const tabBtns = document.querySelectorAll('.ai-tab-btn');
        tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                tabBtns.forEach(b => {
                    b.classList.remove('active', 'btn-primary');
                    b.classList.add('btn-secondary');
                });
                btn.classList.remove('btn-secondary');
                btn.classList.add('active', 'btn-primary');
                activeTab = btn.getAttribute('data-tab');
                renderFilteredAIRecs(activeTab, activeCategory, currentPhase);
            });
        });

        const catSelect = document.getElementById('ai-category-filter');
        catSelect?.addEventListener('change', (e) => {
            activeCategory = e.target.value;
            renderFilteredAIRecs(activeTab, activeCategory, currentPhase);
        });

        renderFilteredAIRecs('ALL', '', currentPhase);

    } catch (e) {
        container.innerHTML = `<div class="card" style="color: var(--accent-red);">Failed to load AI recommendations: ${e.message}</div>`;
    }
}

function renderFilteredAIRecs(tab, categoryFilter, currentPhase) {
    const area = document.getElementById('ai-recommendations-content-area');
    if (!area) return;

    let items = currentAIRecsData;

    if (tab === 'COST') {
        items = items.filter(r => r.recommendation_type === 'COST_SAVING' || r.potential_savings_usd > 0);
    } else if (tab === 'SECURITY') {
        items = items.filter(r => r.recommendation_type === 'SECURITY' || r.potential_savings_usd === 0);
    }

    if (categoryFilter) {
        items = items.filter(r => (r.benefit_category || cleanKeyLabel(r.category)) === categoryFilter);
    }

    const costItems = items.filter(r => r.recommendation_type === 'COST_SAVING' || r.potential_savings_usd > 0);
    const securityItems = items.filter(r => r.recommendation_type === 'SECURITY' || r.potential_savings_usd === 0);

    let html = '';

    if (tab === 'ALL' || tab === 'COST') {
        if (costItems.length > 0) {
            const sectionSavings = costItems.reduce((acc, curr) => acc + (curr.potential_savings_usd || 0), 0);
            html += `
                <div style="margin-bottom: 2.5rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid var(--accent-green); padding-bottom: 8px; margin-bottom: 1rem;">
                        <h3 style="margin: 0; color: var(--accent-green); display: flex; align-items: center; gap: 8px;">
                            <span>💰 Cost Saving Recommendations</span>
                            <span class="badge" style="background: rgba(16, 185, 129, 0.2); color: #34d399; font-size: 0.85rem;">+$${sectionSavings.toLocaleString()}/yr Projected Savings</span>
                        </h3>
                        <span style="font-size: 0.85rem; color: var(--text-muted);">${costItems.length} Cost Reduction Items</span>
                    </div>
                    <div class="grid-cards">
                        ${costItems.map(r => renderRecommendationCard(r, currentPhase, 'COST')).join('')}
                    </div>
                </div>
            `;
        } else if (tab === 'COST') {
            html += `<div class="card" style="text-align: center; color: var(--text-muted); padding: 2rem;">No cost saving recommendations match your current filter.</div>`;
        }
    }

    if (tab === 'ALL' || tab === 'SECURITY') {
        if (securityItems.length > 0) {
            html += `
                <div style="margin-bottom: 2rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid var(--accent-blue); padding-bottom: 8px; margin-bottom: 1rem;">
                        <h3 style="margin: 0; color: var(--accent-blue); display: flex; align-items: center; gap: 8px;">
                            <span>🛡️ Security & Threat Protections</span>
                            <span class="badge" style="background: rgba(59, 130, 246, 0.2); color: #60a5fa; font-size: 0.85rem;">${securityItems.length} Security Protections</span>
                        </h3>
                        <span style="font-size: 0.85rem; color: var(--text-muted);">Grouped by Threat & Compliance Benefits</span>
                    </div>
                    <div class="grid-cards">
                        ${securityItems.map(r => renderRecommendationCard(r, currentPhase, 'SECURITY')).join('')}
                    </div>
                </div>
            `;
        } else if (tab === 'SECURITY') {
            html += `<div class="card" style="text-align: center; color: var(--text-muted); padding: 2rem;">No security recommendations match your current filter.</div>`;
        }
    }

    if (!costItems.length && !securityItems.length) {
        html = `<div class="card" style="text-align: center; color: var(--text-muted); padding: 2.5rem;">No recommendations found for the selected criteria.</div>`;
    }

    area.innerHTML = html;
}

function renderRecommendationCard(r, currentPhase, type) {
    const status = r.status || 'REPORTED';
    let actionBtnHtml = '';

    if (status === 'PENDING_APPROVAL') {
        actionBtnHtml = `
            <div style="display: flex; gap: 8px; margin-top: 10px;">
                <button class="btn btn-primary btn-sm" onclick="approveRecommendationAction(${r.id})">✅ Approve Action</button>
                <button class="btn btn-secondary btn-sm" onclick="rejectRecommendationAction(${r.id})">❌ Dismiss</button>
            </div>
        `;
    } else if (status === 'APPROVED' || status === 'AUTOMATED_EXECUTED') {
        actionBtnHtml = `<span class="badge" style="background: var(--accent-green); color: #000; padding: 4px 8px; border-radius: 4px;">✅ Executed (${r.executed_by || 'Auto'})</span>`;
    } else if (status === 'REJECTED') {
        actionBtnHtml = `<span class="badge" style="background: var(--text-muted); padding: 4px 8px; border-radius: 4px;">Dismissed</span>`;
    } else {
        actionBtnHtml = `<button class="btn btn-secondary btn-sm" onclick="approveRecommendationAction(${r.id})">⚡ Manual Execute</button>`;
    }

    const bCategory = r.benefit_category || cleanKeyLabel(r.category);
    const secBenefit = r.security_benefit || (r.description.includes('Benefit:') ? r.description.split('Benefit:')[1] : null);

    let cardHeaderBadge = '';
    if (r.potential_savings_usd > 0) {
        cardHeaderBadge = `<span class="savings-tag" style="background: rgba(16, 185, 129, 0.2); color: #34d399; font-weight: 700; padding: 4px 8px; border-radius: 4px; font-size: 0.85rem;">+$${r.potential_savings_usd.toLocaleString()}/yr Projected</span>`;
    } else {
        cardHeaderBadge = `<span class="badge" style="background: rgba(59, 130, 246, 0.2); color: #60a5fa; font-weight: 600; padding: 4px 8px; border-radius: 4px; font-size: 0.8rem;">🛡️ ${bCategory}</span>`;
    }

    let benefitBoxHtml = '';
    if (type === 'SECURITY' && secBenefit) {
        benefitBoxHtml = `
            <div style="margin: 0.8rem 0; padding: 8px 12px; background: rgba(30, 58, 138, 0.35); border-left: 3px solid #3b82f6; border-radius: 4px; font-size: 0.85rem; color: #bfdbfe;">
                <strong>🛡️ Security Benefit:</strong> ${secBenefit}
            </div>
        `;
    } else if (type === 'COST') {
        benefitBoxHtml = `
            <div style="margin: 0.8rem 0; padding: 8px 12px; background: rgba(6, 78, 59, 0.35); border-left: 3px solid #10b981; border-radius: 4px; font-size: 0.85rem; color: #a7f3d0;">
                <strong>💰 Projected Savings Category:</strong> ${bCategory}
            </div>
        `;
    }

    return `
        <div class="card card-impact-${r.impact_level.toLowerCase()}" style="display: flex; flex-direction: column; justify-content: space-between;">
            <div>
                <div class="card-header" style="align-items: flex-start; gap: 8px;">
                    <span class="card-title" style="font-size: 0.98rem; font-weight: 600;">#${r.id} - ${r.title}</span>
                    ${cardHeaderBadge}
                </div>
                <p style="color: var(--text-secondary); font-size: 0.88rem; margin-bottom: 0.5rem; line-height: 1.4;">${r.description}</p>
                ${benefitBoxHtml}
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--border-color); padding-top: 8px; margin-top: 8px;">
                <span style="font-size: 0.78rem; color: var(--text-muted);">Target: <strong>${r.target_object || 'Tenant'}</strong> | Mode: <em>${r.automation_phase || currentPhase}</em></span>
                ${actionBtnHtml}
            </div>
        </div>
    `;
}

async function refreshAI() {
    await fetch(`${API_BASE}/ai-governance/recommendations/refresh`, { method: 'POST' });
    loadModule('ai-governance');
}

async function approveRecommendationAction(recId) {
    const res = await fetch(`${API_BASE}/ai-governance/recommendations/${recId}/approve`, { method: 'POST' });
    const data = await res.json();
    alert(data.message || 'Action executed successfully.');
    loadModule('ai-governance');
}

async function rejectRecommendationAction(recId) {
    const res = await fetch(`${API_BASE}/ai-governance/recommendations/${recId}/reject`, { method: 'POST' });
    const data = await res.json();
    alert(data.message || 'Recommendation dismissed.');
    loadModule('ai-governance');
}

// 2. Admin Reports Render
async function renderAdminReports(container) {
    const res = await fetch(`${API_BASE}/admin-reports/summary`);
    const data = await res.json();

    container.innerHTML = `
        <div class="grid-cards" style="margin-bottom: 1.5rem;">
            <div class="card">
                <div class="card-title">License Consumption</div>
                <h2 style="font-size: 2.2rem; margin: 0.5rem 0;">${data.licenses?.total_licenses_assigned || 0} / ${data.licenses?.total_licenses_purchased || 0}</h2>
                <p style="color: var(--text-secondary);">Licenses Assigned across Tenant</p>
            </div>
            <div class="card">
                <div class="card-title">Teams Call Quality Score</div>
                <h2 style="font-size: 2.2rem; margin: 0.5rem 0; color: var(--accent-green);">${data.teams_call_quality?.overall_audio_quality_score || 0}%</h2>
                <p style="color: var(--text-secondary);">Poor Calls: ${data.teams_call_quality?.poor_call_percentage || 0}%</p>
            </div>
            <div class="card">
                <div class="card-title">Active Vulnerabilities</div>
                <h2 style="font-size: 2.2rem; margin: 0.5rem 0; color: var(--accent-red);">${data.intune_defender_vulnerabilities?.length || 0} CVEs</h2>
                <p style="color: var(--text-secondary);">Azure Intune vs M365 Defender</p>
            </div>
        </div>
        <div id="admin-reports-table-container"></div>
    `;

    renderInteractiveTable('admin-reports-table-container', {
        data: data.intune_defender_vulnerabilities || [],
        title: '🛡️ Defender CVE Vulnerability Breakdown',
        subtitle: 'Click any row to inspect all CVE details and raw JSON payload',
        exportFileName: 'Defender_CVE_Vulnerabilities',
        filterFields: ['severity', 'patchAvailable'],
        columns: [
            { key: 'cveId', label: 'CVE ID', format: v => `<strong>${v}</strong>` },
            { key: 'severity', label: 'Severity', format: v => `<span style="color: ${v === 'CRITICAL' ? 'var(--accent-red)' : 'var(--accent-amber)'}">${v}</span>` },
            { key: 'title', label: 'Title' },
            { key: 'affectedDevices', label: 'Affected Devices', format: v => `${v} devices` },
            { key: 'patchAvailable', label: 'Patch Status', format: v => v ? '✅ Patch Available' : '❌ Pending' }
        ]
    });
}

// 3. Exchange Management Render
async function renderExchangeMgmt(container) {
    const res = await fetch(`${API_BASE}/exchange/licenses`);
    const data = await res.json();

    container.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <h3>Exchange User Licenses (${data.total_users_analyzed} Users Analyzed)</h3>
            <span class="badge" style="background: var(--accent-green); font-size: 0.85rem;">🟢 LIVE Microsoft Graph API</span>
        </div>
        <div id="exchange-mgmt-table-container"></div>
    `;

    renderInteractiveTable('exchange-mgmt-table-container', {
        data: data.users || [],
        title: 'Exchange User License Retention Inventory',
        subtitle: 'Click any user row to view all attributes',
        exportFileName: 'Exchange_User_Licenses',
        filterFields: ['RBIusertype', 'department', 'assignedLicense'],
        columns: [
            { key: 'userPrincipalName', label: 'User Principal Name', format: v => `<strong>${v}</strong>` },
            { key: 'department', label: 'Department' },
            { key: 'RBIusertype', label: 'RBI User Type', format: v => `<span class="badge" style="background: rgba(59, 130, 246, 0.2);">${v}</span>` },
            { key: 'assignedLicense', label: 'Assigned License' },
            { key: 'userPrincipalName', label: 'Actions', format: (v) => `<button class="btn btn-secondary" style="padding: 0.25rem 0.5rem; font-size: 0.75rem;" onclick="event.stopPropagation(); triggerLicenseUpgrade('${v}')">Upgrade/Downgrade</button>` }
        ]
    });
}

async function filterRetention(rbiType) {
    const res = await fetch(`${API_BASE}/exchange/retention-dashboard?rbi_user_type=${rbiType}`);
    const data = await res.json();
    alert(`Filtered retention view for RBIusertype='${rbiType || 'ALL'}': ${data.matching_users_count} matching users.`);
}

function triggerLicenseUpgrade(upn) {
    alert(`Initiating License Action for user ${upn} via AI Orchestrator.`);
}

// 4. Mailbox Management Render
async function renderMailboxes(container) {
    const res = await fetch(`${API_BASE}/mailboxes/summary`);
    const data = await res.json();

    container.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <h3>User Mailboxes Inventory (${data.total_mailboxes} Mailboxes)</h3>
            <span class="badge" style="background: var(--accent-green); font-size: 0.85rem;">🟢 LIVE Microsoft Graph API</span>
        </div>
        <div id="mailboxes-table-container"></div>
    `;

    renderInteractiveTable('mailboxes-table-container', {
        data: data.mailboxes || [],
        title: 'Mailboxes Inventory',
        subtitle: 'Click any mailbox row to inspect all fields',
        exportFileName: 'Mailboxes_Inventory',
        filterFields: ['type', 'department', 'litigationHold'],
        columns: [
            { key: 'upn', label: 'Mailbox UPN', format: v => `<strong>${v}</strong>` },
            { key: 'displayName', label: 'Display Name' },
            { key: 'type', label: 'Type', format: v => `<span class="badge" style="background: rgba(139, 92, 246, 0.2);">${v}</span>` },
            { key: 'department', label: 'Department' },
            { key: 'litigationHold', label: 'Litigation Hold', format: v => v ? '🔒 Enabled' : 'Off' },
            { key: 'storageUsedGB', label: 'Storage (GB)', format: v => `${v} GB` },
            { key: 'upn', label: 'Actions', format: (v) => `<button class="btn btn-secondary" style="padding: 0.25rem 0.5rem; font-size: 0.75rem;" onclick="event.stopPropagation(); toggleLitHold('${v}')">Toggle Hold</button>` }
        ]
    });
}

async function toggleLitHold(upn) {
    await fetch(`${API_BASE}/mailboxes/action`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({user_principal_name: upn, action_type: 'enable_litigation_hold'})
    });
    alert(`Litigation Hold toggle command executed via PowerShell microservice for ${upn}.`);
    loadModule('mailboxes');
}

// 5. Distribution Groups Render
async function renderDistributionGroups(container) {
    const res = await fetch(`${API_BASE}/distribution-groups/list`);
    const data = await res.json();

    container.innerHTML = `
        <h3>Categorized Distribution Groups (${data.total_groups})</h3>
        <div id="dist-groups-table-container"></div>
    `;

    renderInteractiveTable('dist-groups-table-container', {
        data: data.groups || [],
        title: 'Distribution Groups List',
        subtitle: 'Click any group row to view full details',
        exportFileName: 'Distribution_Groups',
        filterFields: ['department', 'isCompliantNaming'],
        columns: [
            { key: 'displayName', label: 'Group Display Name', format: v => `<strong>${v}</strong>` },
            { key: 'email', label: 'Email Address' },
            { key: 'department', label: 'Mapped Department' },
            { key: 'memberCount', label: 'Members', format: v => `${v} members` },
            { key: 'isCompliantNaming', label: 'Naming Compliant', format: v => v ? '✅ Compliant' : '⚠️ Non-Standard' }
        ]
    });
}

// 6. Mailflow Render
async function renderMailflow(container) {
    const res = await fetch(`${API_BASE}/mailflow/dashboard`);
    const data = await res.json();

    container.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
            <h3>1-Year Mailflow Historical Dashboard</h3>
            <button class="btn btn-primary" onclick="triggerMailflowSync()">⚡ Run 1-Year Aggregation Background Job</button>
        </div>

        <div class="grid-cards" style="margin-bottom: 1.5rem;">
            <div class="card">
                <div class="card-title">Top Recipient</div>
                <h3>${data.top_recipients?.[0]?.recipient || 'N/A'}</h3>
                <p style="color: var(--text-secondary);">${(data.top_recipients?.[0]?.totalMessages || 0).toLocaleString()} messages processed</p>
            </div>
            <div class="card">
                <div class="card-title">Auto-Forwarding Risk Domains</div>
                <h3>${data.auto_forwarding_by_domain?.length || 0} External Domains</h3>
                <p style="color: var(--accent-red);">High Risk Domains Flagged</p>
            </div>
        </div>

        <div id="mailflow-table-container"></div>
    `;

    renderInteractiveTable('mailflow-table-container', {
        data: data.transport_rules || [],
        title: 'Active Transport Rules',
        subtitle: 'Click any transport rule row to inspect rule configuration details',
        exportFileName: 'Active_Transport_Rules',
        filterFields: ['state'],
        columns: [
            { key: 'ruleName', label: 'Rule Name', format: v => `<strong>${v}</strong>` },
            { key: 'state', label: 'Status', format: v => `<span style="color: var(--accent-green);">${v}</span>` },
            { key: 'matchesLast30Days', label: 'Matches (30d)', format: v => `${v} matches` }
        ]
    });
}

async function triggerMailflowSync() {
    const res = await fetch(`${API_BASE}/mailflow/sync-1year-mailflow`, { method: 'POST' });
    const data = await res.json();
    alert(`Background Job #${data.job_id} enqueued successfully in SQL Express queue!`);
}

// 7. SharePoint & OneDrive Render
async function renderSharePoint(container) {
    const res = await fetch(`${API_BASE}/sharepoint/reports`);
    const data = await res.json();

    container.innerHTML = `
        <h3>SharePoint Site Usage & Last-Access Stale File Cleanup</h3>
        <div id="sharepoint-table-container"></div>
    `;

    renderInteractiveTable('sharepoint-table-container', {
        data: data.site_usage_summary?.sites || [],
        title: 'SharePoint Sites Usage Summary',
        subtitle: 'Click any site row to inspect storage, permissions, and DLP attributes',
        exportFileName: 'SharePoint_Sites_Usage',
        filterFields: ['externalSharing'],
        columns: [
            { key: 'siteName', label: 'Site Name', format: v => `<strong>${v}</strong>` },
            { key: 'storageUsedGB', label: 'Storage Used (GB)', format: v => `${v} GB` },
            { key: 'externalSharing', label: 'External Sharing', format: v => `<span style="color: ${v === 'Anyone' ? 'var(--accent-red)' : 'var(--text-primary)'}">${v}</span>` },
            { key: 'sensitiveDataFiles', label: 'Sensitive DLP Files', format: v => `${v} files` }
        ]
    });
}

// 8. Azure AD Render
async function renderAzureAD(container) {
    const res = await fetch(`${API_BASE}/azure-ad/summary`);
    const data = await res.json().then(d => d.azure_ad_governance);

    container.innerHTML = `
        <div class="grid-cards" style="margin-bottom: 1.5rem;">
            <div class="card">
                <div class="card-title">AD Connect Sync</div>
                <h3 style="color: var(--accent-green);">${data.ad_connect_sync_status}</h3>
                <p style="color: var(--text-secondary);">${data.sync_errors_count} sync errors active</p>
            </div>
            <div class="card">
                <div class="card-title">Risky Users</div>
                <h3 style="color: var(--accent-red);">${data.risky_users.length} Users Flagged</h3>
                <p style="color: var(--text-secondary);">High severity risk state</p>
            </div>
        </div>

        <div id="azuread-table-container"></div>
    `;

    renderInteractiveTable('azuread-table-container', {
        data: data.app_registrations_summary || [],
        title: 'App Registrations Token Expiry & Permission Governance',
        subtitle: 'Click any App Registration row to view permissions & secret expiry payload',
        exportFileName: 'App_Registrations_Governance',
        filterFields: ['owner', 'warning'],
        columns: [
            { key: 'appName', label: 'App Name', format: v => `<strong>${v}</strong>` },
            { key: 'appId', label: 'App ID', format: v => `<code>${v}</code>` },
            { key: 'owner', label: 'Owner' },
            { key: 'tokenExpiry', label: 'Token Expiry' },
            { key: 'warning', label: 'Status', format: v => v ? `<span style="color: var(--accent-amber)">⚠️ ${v}</span>` : 'OK' }
        ]
    });
}

// 9. Outages Render
async function renderOutages(container) {
    const res = await fetch(`${API_BASE}/reports/outages`);
    const data = await res.json();
    const incidents = data.incidents || data.services || [];
    const isLive = data.data_source === "LIVE_MICROSOFT_GRAPH_API";

    container.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <h3>M365 Service Health Status (${incidents.length} Incidents)</h3>
            <span class="badge" style="background: ${isLive ? 'var(--accent-green)' : 'var(--accent-blue)'}; font-size: 0.85rem;">
                ${isLive ? '🟢 LIVE Microsoft Graph API' : 'ℹ️ System Status'}
            </span>
        </div>
        <div id="outages-table-container"></div>
    `;

    renderInteractiveTable('outages-table-container', {
        data: incidents,
        title: 'M365 Service Health & Outages Telemetry',
        subtitle: 'Click any incident row to read the full status description & advisory notes',
        exportFileName: 'M365_Service_Health_Outages',
        filterFields: ['status', 'severity'],
        columns: [
            { key: 'service', label: 'Service Name', format: (v, item) => `<strong>${v || item.serviceName || 'N/A'}</strong>` },
            { key: 'status', label: 'Status', format: v => `<span style="color: ${v === 'ServiceRestored' || v === 'NormalService' ? 'var(--accent-green)' : 'var(--accent-amber)'}">${v}</span>` },
            { key: 'id', label: 'Incident ID', format: (v, item) => `<code>${v || item.incidentId || 'N/A'}</code>` },
            { key: 'title', label: 'Region / Description', format: (v, item) => item.impactedRegion || v || item.description || 'All systems operational.' },
            { key: 'severity', label: 'Severity', format: v => `<span class="badge" style="background: ${v === 'HIGH' || v === 'CRITICAL' ? 'var(--accent-red)' : 'var(--accent-blue)'};">${v || 'MEDIUM'}</span>` },
            { key: 'startTime', label: 'Start Time', format: v => v ? new Date(v).toLocaleString() : 'N/A' }
        ]
    });
}

// 10. Legal Hold Render
async function renderLegalHold(container) {
    const res = await fetch(`${API_BASE}/legal-hold/cases`);
    const cases = await res.json();

    container.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
            <h3>Active Legal Hold Cases (${cases.length})</h3>
            <button class="btn btn-primary" onclick="showNewHoldForm()">+ Create Legal Hold Request</button>
        </div>
        <div id="legal-hold-table-container"></div>
    `;

    renderInteractiveTable('legal-hold-table-container', {
        data: cases,
        title: 'Legal Hold Cases Inventory',
        subtitle: 'Click any legal hold case to inspect custodian details and litigation scope',
        exportFileName: 'Legal_Hold_Cases',
        filterFields: ['hold_type', 'status', 'requested_by'],
        columns: [
            { key: 'case_number', label: 'Case Number', format: v => `<strong>${v}</strong>` },
            { key: 'case_name', label: 'Case Name' },
            { key: 'custodian_email', label: 'Custodian UPN' },
            { key: 'hold_type', label: 'Hold Type' },
            { key: 'status', label: 'Status', format: v => `<span style="color: var(--accent-green)">${v}</span>` },
            { key: 'requested_by', label: 'Requested By' }
        ]
    });
}

function showNewHoldForm() {
    const name = prompt("Enter Case Name:");
    const email = prompt("Enter Custodian Email UPN:");
    if (name && email) {
        fetch(`${API_BASE}/legal-hold/create`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({case_name: name, custodian_email: email, hold_type: 'LitigationHold', reason: 'Audit Request'})
        }).then(() => loadModule('legal-hold'));
    }
}

// 11. Teams Integration Render & Bot Simulator
async function renderTeamsIntegration(container) {
    const res = await fetch(`${API_BASE}/teams/config`);
    const config = await res.json();

    const phaseLabels = {
        'PHASE_1_REPORTING': 'Phase 1: Reporting Only',
        'PHASE_2_SEMI_AUTOMATED': 'Phase 2: Semi-Automated',
        'PHASE_3_FULLY_AUTOMATED': 'Phase 3: Fully Automated'
    };

    container.innerHTML = `
        <div class="grid-cards" style="grid-template-columns: 1fr 1fr; margin-bottom: 1.5rem;">
            <div class="card">
                <div class="card-title">💬 Teams Integration Configuration</div>
                <p style="font-size: 0.9rem; color: var(--text-secondary); margin: 0.5rem 0;">Active Webhook & Proactive Daily Digest settings.</p>
                <div style="margin-top: 1rem; font-size: 0.9rem; line-height: 1.6;">
                    <div><strong>Webhook URL:</strong> <code style="word-break: break-all;">${config.webhook_url || 'Not set (Simulated Mode)'}</code></div>
                    <div><strong>Channel Name:</strong> ${config.channel_name}</div>
                    <div><strong>Daily Digest:</strong> ${config.daily_digest_enabled ? '✅ Enabled' : '❌ Disabled'} (${config.daily_digest_time})</div>
                    <div><strong>Active Governance Phase:</strong> <span class="badge" style="background: var(--accent-blue);">${phaseLabels[config.active_governance_phase] || config.active_governance_phase}</span></div>
                </div>
                <div style="margin-top: 1rem; display: flex; gap: 10px;">
                    <button class="btn btn-primary" onclick="triggerTeamsDigestNow()">🚀 Trigger Daily Digest Now</button>
                    <button class="btn btn-secondary" onclick="document.getElementById('teams-config-modal').style.display='flex'">⚙️ Configure Settings</button>
                </div>
            </div>

            <div class="card">
                <div class="card-title">🤖 Teams Bot Interaction Simulator</div>
                <p style="font-size: 0.9rem; color: var(--text-secondary); margin-bottom: 1rem;">Test asking questions or giving commands to the bot directly from this console.</p>
                
                <div class="form-group">
                    <input type="text" id="teams-bot-input" class="form-control" placeholder="Type a command (e.g. 'recommendations', 'licenses', 'outages', 'help')" value="recommendations">
                </div>
                <button class="btn btn-accent btn-block" onclick="sendSimulatedTeamsBotCommand()">Send Command to Bot</button>

                <div id="teams-bot-response" style="margin-top: 1rem; padding: 1rem; background: var(--bg-dark); border-radius: 8px; font-family: monospace; font-size: 0.85rem; max-height: 250px; overflow-y: auto;">
                    <em>Bot response will appear here...</em>
                </div>
            </div>
        </div>
    `;
}

async function triggerTeamsDigestNow() {
    const res = await fetch(`${API_BASE}/teams/daily-digest/trigger`, { method: 'POST' });
    const data = await res.json();
    alert(data.message || 'Daily digest triggered successfully!');
}

async function sendSimulatedTeamsBotCommand() {
    const input = document.getElementById('teams-bot-input').value;
    const outputEl = document.getElementById('teams-bot-response');
    if (!input) return;

    outputEl.innerHTML = `<em>Processing command '${input}'...</em>`;

    try {
        const res = await fetch(`${API_BASE}/teams/webhook`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                text: input,
                user_principal_name: 'admin@contoso.com',
                user_name: 'System Admin'
            })
        });
        const data = await res.json();
        const result = data.result || {};
        
        let outputText = result.text || JSON.stringify(result, null, 2);
        if (result.card) {
            outputText += "\n\n[Adaptive Card Delivered]\n" + JSON.stringify(result.card, null, 2);
        }

        outputEl.innerHTML = `<pre style="white-space: pre-wrap; margin: 0; color: var(--text-primary);">${outputText}</pre>`;
    } catch (e) {
        outputEl.innerHTML = `<span style="color: var(--accent-red)">Error: ${e.message}</span>`;
    }
}

// Modal Controllers & API Integration Hub
function setupModals() {
    const apiHubModal = document.getElementById('api-hub-modal');
    const exportModal = document.getElementById('export-modal');
    const teamsModal = document.getElementById('teams-config-modal');

    // Open API Hub Modal
    document.getElementById('btn-open-api-hub')?.addEventListener('click', () => {
        if (apiHubModal) {
            apiHubModal.style.display = 'flex';
            setupAPITabs();
            loadAllAPIIntegrations();
        }
    });

    document.getElementById('btn-close-api-hub')?.addEventListener('click', () => {
        if (apiHubModal) apiHubModal.style.display = 'none';
    });

    document.getElementById('btn-export-data')?.addEventListener('click', () => {
        exportModal.style.display = 'flex';
    });
    document.getElementById('btn-close-export-modal')?.addEventListener('click', () => {
        exportModal.style.display = 'none';
    });

    // Teams Modal
    document.getElementById('btn-open-teams-config')?.addEventListener('click', async () => {
        teamsModal.style.display = 'flex';
        const res = await fetch(`${API_BASE}/teams/config`);
        const data = await res.json();
        document.getElementById('teams-governance-phase').value = data.active_governance_phase || 'PHASE_1_REPORTING';
        document.getElementById('teams-webhook-url').value = data.webhook_url || '';
        document.getElementById('teams-channel-name').value = data.channel_name || 'General Admin Channel';
        document.getElementById('teams-daily-digest-enabled').checked = data.daily_digest_enabled;
        document.getElementById('teams-digest-time').value = data.daily_digest_time || '09:00';
    });
    document.getElementById('btn-close-teams-modal')?.addEventListener('click', () => {
        teamsModal.style.display = 'none';
    });

    document.getElementById('btn-trigger-teams-digest')?.addEventListener('click', async () => {
        await triggerTeamsDigestNow();
    });

    // API Integration Form Submissions
    setupAPIFormHandlers();

    // Teams Form Handler
    document.getElementById('teams-config-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const phase = document.getElementById('teams-governance-phase').value;
        const webhook = document.getElementById('teams-webhook-url').value;
        const channel = document.getElementById('teams-channel-name').value;
        const digestEnabled = document.getElementById('teams-daily-digest-enabled').checked;
        const digestTime = document.getElementById('teams-digest-time').value;

        await fetch(`${API_BASE}/teams/config`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                active_governance_phase: phase,
                webhook_url: webhook,
                channel_name: channel,
                daily_digest_enabled: digestEnabled,
                daily_digest_time: digestTime
            })
        });

        alert('Microsoft Teams & Phase Governance settings updated successfully!');
        teamsModal.style.display = 'none';
        loadModule('ai-governance');
    });

    // Export Form Handler
    document.getElementById('export-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const module = document.getElementById('export-module').value;
        const days = parseInt(document.getElementById('export-window').value);
        const format = document.getElementById('export-format').value;

        const res = await fetch(`${API_BASE}/ai-governance/export`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({module, days, format})
        });

        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `m365_report_${module}_${days}d.${format}`;
        a.click();
        exportModal.style.display = 'none';
    });

    // Auto-Switch Failover Test Button
    document.getElementById('btn-run-sim-failover')?.addEventListener('click', runFailoverSimulation);
}

// API Hub Tab Router
function setupAPITabs() {
    const tabs = document.querySelectorAll('.api-hub-tabs .tab-btn');
    tabs.forEach(tab => {
        tab.onclick = () => {
            tabs.forEach(t => t.classList.remove('active'));
            document.querySelectorAll('#api-hub-modal .tab-content').forEach(c => c.classList.remove('active'));
            
            tab.classList.add('active');
            const target = tab.getAttribute('data-tab');
            const contentEl = document.getElementById(target);
            if (contentEl) contentEl.classList.add('active');
        };
    });
}

// Setup Form Handlers for LLM, Azure, Maps, and Custom APIs
function setupAPIFormHandlers() {
    // 1. LLM API Form
    document.getElementById('api-llm-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const provider = document.getElementById('llm-provider-select').value;
        const key = document.getElementById('llm-key-input').value;
        const model = document.getElementById('llm-model-input').value;
        const endpoint = document.getElementById('llm-endpoint-input').value;
        const priority = parseInt(document.getElementById('llm-priority-input').value) || 1;

        try {
            await saveAPIIntegration({
                api_category: 'LLM',
                provider_name: provider,
                api_key: key,
                model_name: model,
                endpoint_url: endpoint,
                priority: priority,
                is_active: true
            });

            alert(`Encrypted LLM Integration '${provider.toUpperCase()}' saved! Priority: ${priority}`);
            document.getElementById('llm-key-input').value = '';
            loadAllAPIIntegrations();
        } catch (err) {
            alert(`Failed to save LLM integration: ${err.message}`);
        }
    });

    // 2. Azure API Form
    document.getElementById('api-azure-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const provider = document.getElementById('azure-service-select').value;
        const key = document.getElementById('azure-key-input').value;
        const endpoint = document.getElementById('azure-endpoint-input').value;
        const model = document.getElementById('azure-model-input').value;

        try {
            await saveAPIIntegration({
                api_category: 'AZURE',
                provider_name: provider,
                api_key: key,
                endpoint_url: endpoint,
                model_name: model,
                priority: 1,
                is_active: true
            });

            alert(`Azure Service '${provider.toUpperCase()}' saved!`);
            document.getElementById('azure-key-input').value = '';
            loadAllAPIIntegrations();
        } catch (err) {
            alert(`Failed to save Azure integration: ${err.message}`);
        }
    });

    // 3. Maps API Form
    document.getElementById('api-maps-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const provider = document.getElementById('maps-provider-select').value;
        const key = document.getElementById('maps-key-input').value;
        const endpoint = document.getElementById('maps-endpoint-input').value;

        try {
            await saveAPIIntegration({
                api_category: 'MAPS',
                provider_name: provider,
                api_key: key,
                endpoint_url: endpoint,
                priority: 1,
                is_active: true
            });

            alert(`Maps API Integration '${provider.toUpperCase()}' saved!`);
            document.getElementById('maps-key-input').value = '';
            loadAllAPIIntegrations();
        } catch (err) {
            alert(`Failed to save Maps integration: ${err.message}`);
        }
    });

    // 4. Custom API Form
    document.getElementById('api-custom-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const category = document.getElementById('custom-category-select').value;
        const name = document.getElementById('custom-name-input').value;
        const key = document.getElementById('custom-key-input').value;
        const endpoint = document.getElementById('custom-endpoint-input').value;
        const headers = document.getElementById('custom-headers-input').value;

        try {
            await saveAPIIntegration({
                api_category: category,
                provider_name: name,
                api_key: key,
                endpoint_url: endpoint,
                extra_headers_json: headers,
                priority: 1,
                is_active: true
            });

            alert(`Custom Integration '${name}' saved successfully!`);
            document.getElementById('custom-name-input').value = '';
            document.getElementById('custom-key-input').value = '';
            loadAllAPIIntegrations();
        } catch (err) {
            alert(`Failed to save custom integration: ${err.message}`);
        }
    });
}

// API Integration Helpers
async function saveAPIIntegration(payload) {
    const res = await fetch(`${API_BASE}/integrations`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) {
        throw new Error(data.detail || data.message || 'Failed to save integration');
    }
    return data;
}

async function deleteAPIIntegration(id) {
    if (!confirm('Are you sure you want to delete this API integration profile?')) return;
    try {
        await fetch(`${API_BASE}/integrations/${id}`, { method: 'DELETE' });
        loadAllAPIIntegrations();
    } catch (e) {
        alert('Error deleting integration: ' + e.message);
    }
}

async function loadAllAPIIntegrations() {
    try {
        const res = await fetch(`${API_BASE}/integrations`);
        const items = await res.json();
        window.allLoadedAPIIntegrations = items;

        renderProviderCategoryList(items.filter(i => i.api_category === 'LLM'), 'llm-providers-list');
        renderProviderCategoryList(items.filter(i => i.api_category === 'AZURE'), 'azure-providers-list');
        renderProviderCategoryList(items.filter(i => i.api_category === 'MAPS'), 'maps-providers-list');
        renderProviderCategoryList(items.filter(i => i.api_category !== 'LLM' && i.api_category !== 'AZURE' && i.api_category !== 'MAPS'), 'custom-providers-list');
    } catch (e) {
        console.warn('Error loading API integrations:', e);
    }
}

function triggerEditAPIIntegration(id) {
    const item = (window.allLoadedAPIIntegrations || []).find(i => i.id === id);
    if (!item) return;
    const cat = item.api_category;
    if (cat === 'LLM') {
        document.querySelector('.tab-btn[data-tab="tab-llm"]')?.click();
        const sel = document.getElementById('llm-provider-select');
        if (sel) sel.value = item.provider_name;
        const model = document.getElementById('llm-model-input');
        if (model) model.value = item.model_name || '';
        const ep = document.getElementById('llm-endpoint-input');
        if (ep) ep.value = item.endpoint_url || '';
        const prio = document.getElementById('llm-priority-input');
        if (prio) prio.value = item.priority || 1;
        document.getElementById('llm-key-input')?.focus();
    } else if (cat === 'AZURE') {
        document.querySelector('.tab-btn[data-tab="tab-azure"]')?.click();
        const sel = document.getElementById('azure-service-select');
        if (sel) sel.value = item.provider_name;
        const ep = document.getElementById('azure-endpoint-input');
        if (ep) ep.value = item.endpoint_url || '';
        const model = document.getElementById('azure-model-input');
        if (model) model.value = item.model_name || '';
        document.getElementById('azure-key-input')?.focus();
    } else if (cat === 'MAPS') {
        document.querySelector('.tab-btn[data-tab="tab-maps"]')?.click();
        const sel = document.getElementById('maps-provider-select');
        if (sel) sel.value = item.provider_name;
        const ep = document.getElementById('maps-endpoint-input');
        if (ep) ep.value = item.endpoint_url || '';
        document.getElementById('maps-key-input')?.focus();
    } else {
        document.querySelector('.tab-btn[data-tab="tab-custom"]')?.click();
        const catSel = document.getElementById('custom-category-select');
        if (catSel) catSel.value = item.api_category;
        const name = document.getElementById('custom-name-input');
        if (name) name.value = item.provider_name || '';
        const ep = document.getElementById('custom-endpoint-input');
        if (ep) ep.value = item.endpoint_url || '';
        document.getElementById('custom-key-input')?.focus();
    }
}

function renderProviderCategoryList(items, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (!items || items.length === 0) {
        container.innerHTML = '<div style="font-size: 0.85rem; color: var(--text-muted); font-style: italic;">No configured integrations in this category yet. Use the form above to add one.</div>';
        return;
    }

    container.innerHTML = items.map(item => `
        <div class="provider-card">
            <div class="provider-card-header">
                <span class="provider-name-tag">${item.provider_name}</span>
                <span class="priority-tag">Priority #${item.priority}</span>
            </div>
            <div class="provider-detail-line">Model: ${item.model_name || 'default'}</div>
            <div class="provider-detail-line">Endpoint: ${item.endpoint_url || 'Default Cloud'}</div>
            <div class="provider-detail-line">Key Status: ${item.has_key ? '🔒 Encrypted' : '⚠️ None'}</div>
            ${item.error_count > 0 ? `<div class="provider-detail-line" style="color: var(--accent-red)">Failures: ${item.error_count} (${item.last_error || ''})</div>` : ''}
            <div style="display: flex; justify-content: flex-end; gap: 8px; margin-top: 8px;">
                <button class="btn btn-primary" style="padding: 2px 8px; font-size: 0.75rem;" onclick="triggerEditAPIIntegration(${item.id})">✏️ Edit</button>
                <button class="btn btn-secondary" style="padding: 2px 8px; font-size: 0.75rem;" onclick="deleteAPIIntegration(${item.id})">🗑️ Delete</button>
            </div>
        </div>
    `).join('');
}

// Live Auto-Switch Failover Simulator Terminal Runner
async function runFailoverSimulation() {
    const terminal = document.getElementById('sim-terminal-output');
    const prompt = document.getElementById('sim-prompt-input').value;
    const errorCheckboxes = document.querySelectorAll('.sim-err-chk:checked');
    const simulatedErrors = Array.from(errorCheckboxes).map(c => c.value);

    terminal.innerHTML = `⚡ [FAILOVER SIMULATOR] Initiating LLM Request Orchestration...\n`;
    terminal.innerHTML += `📥 Prompt: "${prompt}"\n`;
    if (simulatedErrors.length > 0) {
        terminal.innerHTML += `⚠️ Simulating API Rate-Limit / Timeout Errors on: [${simulatedErrors.join(', ')}]\n`;
    }
    terminal.innerHTML += `----------------------------------------------------------------------\n`;

    try {
        const res = await fetch(`${API_BASE}/integrations/llm/execute-failover`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                prompt: prompt,
                simulate_errors: simulatedErrors
            })
        });

        const data = await res.json();

        if (data.failover_logs && data.failover_logs.length > 0) {
            data.failover_logs.forEach((log, idx) => {
                if (log.status === 'FAILED') {
                    terminal.innerHTML += `❌ Step ${idx + 1}: Provider '${log.provider.toUpperCase()}' FAILED -> ${log.error}\n`;
                    terminal.innerHTML += `   └─ AUTO-SWITCHING TO NEXT BACKUP PROVIDER...\n`;
                } else if (log.status === 'SUCCESS') {
                    terminal.innerHTML += `✅ Step ${idx + 1}: Provider '${log.provider.toUpperCase()}' SUCCESS! (Priority #${log.priority}, Model: ${log.model})\n`;
                } else {
                    terminal.innerHTML += `ℹ️ Step ${idx + 1}: ${log.details}\n`;
                }
            });
        }

        terminal.innerHTML += `----------------------------------------------------------------------\n`;
        terminal.innerHTML += `🎯 FINAL RESULT: Served via '${data.active_provider.toUpperCase()}' (Model: ${data.model_used})\n`;
        terminal.innerHTML += `💬 Payload Output:\n${data.response}\n`;
    } catch (e) {
        terminal.innerHTML += `❌ Simulator exception: ${e.message}\n`;
    }
}

// Category Overview Render Functions
async function renderReportingOverview(container) {
    const [reportsRes, outagesRes, mailflowRes, azureAdRes] = await Promise.all([
        fetch(`${API_BASE}/admin-reports/summary`),
        fetch(`${API_BASE}/outages/service-health`),
        fetch(`${API_BASE}/mailflow/dashboard`),
        fetch(`${API_BASE}/azure-ad/summary`)
    ]);

    const reportsData = reportsRes.ok ? await reportsRes.json() : {};
    const outagesData = outagesRes.ok ? await outagesRes.json() : { services: [] };
    const mailflowData = mailflowRes.ok ? await mailflowRes.json() : { top_recipients: [{recipient: 'N/A'}] };
    const azureAdData = azureAdRes.ok ? await azureAdRes.json().then(d => d.azure_ad_governance) : {};

    const activeOutages = outagesData.services ? outagesData.services.filter(s => s.status !== 'NormalService').length : 0;

    container.innerHTML = `
        <div style="background: var(--gradient-brand); padding: 1.5rem; border-radius: 12px; margin-bottom: 1.5rem;">
            <h2 style="margin: 0 0 6px 0;">📊 Part 1: Reporting Category Dashboard</h2>
            <p style="margin: 0; opacity: 0.9; font-size: 0.95rem;">Centralized enterprise telemetry combining Admin Reports, 1-Year Mailflow Store, Service Outages, and Azure AD Security Audits.</p>
        </div>

        <div class="grid-cards" style="grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));">
            <div class="card" onclick="loadModule('admin-reports')" style="cursor: pointer;">
                <div class="card-title">📈 Admin Reports Summary</div>
                <h3 style="margin: 0.5rem 0; font-size: 1.8rem;">${reportsData.licenses?.total_licenses_assigned || 0} / ${reportsData.licenses?.total_licenses_purchased || 0}</h3>
                <p style="color: var(--text-secondary); font-size: 0.85rem;">Active Licenses | Teams Score: <strong style="color: var(--accent-green);">${reportsData.teams_call_quality?.overall_audio_quality_score || 0}%</strong></p>
                <button class="btn btn-secondary btn-block" style="margin-top: 1rem;">View Admin Reports →</button>
            </div>

            <div class="card" onclick="loadModule('mailflow')" style="cursor: pointer;">
                <div class="card-title">🔄 1-Year Mailflow Telemetry</div>
                <h3 style="margin: 0.5rem 0; font-size: 1.8rem;">${mailflowData.auto_forwarding_by_domain?.length || 0} External Domains</h3>
                <p style="color: var(--accent-red); font-size: 0.85rem;">Auto-Forwarding Risk | Top: ${mailflowData.top_recipients?.[0]?.recipient || 'N/A'}</p>
                <button class="btn btn-secondary btn-block" style="margin-top: 1rem;">View Mailflow Telemetry →</button>
            </div>

            <div class="card" onclick="loadModule('outages')" style="cursor: pointer;">
                <div class="card-title">⚠️ Service Health & Outage Map</div>
                <h3 style="margin: 0.5rem 0; font-size: 1.8rem; color: ${activeOutages > 0 ? 'var(--accent-amber)' : 'var(--accent-green)'};">${activeOutages === 0 ? 'All Normal' : `${activeOutages} Incidents`}</h3>
                <p style="color: var(--text-secondary); font-size: 0.85rem;">Live M365 Service Announcement Parser & Region Map</p>
                <button class="btn btn-secondary btn-block" style="margin-top: 1rem;">View Outage Dashboard →</button>
            </div>

            <div class="card" onclick="loadModule('azure-ad')" style="cursor: pointer;">
                <div class="card-title">🔑 Security & Azure AD Audits</div>
                <h3 style="margin: 0.5rem 0; font-size: 1.8rem; color: var(--accent-red);">${azureAdData.risky_users?.length || 0} Risky Users</h3>
                <p style="color: var(--text-secondary); font-size: 0.85rem;">AD Connect: <strong>${azureAdData.ad_connect_sync_status || 'OK'}</strong></p>
                <button class="btn btn-secondary btn-block" style="margin-top: 1rem;">View Azure AD Audits →</button>
            </div>
        </div>
    `;
}

async function renderManagementOverview(container) {
    const [exchangeRes, mailboxesRes, distGroupsRes, sharepointRes] = await Promise.all([
        fetch(`${API_BASE}/exchange/licenses`),
        fetch(`${API_BASE}/mailboxes/summary`),
        fetch(`${API_BASE}/distribution-groups/list`),
        fetch(`${API_BASE}/sharepoint/reports`)
    ]);

    const exchangeData = exchangeRes.ok ? await exchangeRes.json() : { users: [] };
    const mailboxesData = mailboxesRes.ok ? await mailboxesRes.json() : { mailboxes: [] };
    const distGroupsData = distGroupsRes.ok ? await distGroupsRes.json() : { groups: [] };
    const sharepointData = sharepointRes.ok ? await sharepointRes.json() : { site_usage_summary: { sites: [] } };

    container.innerHTML = `
        <div style="background: linear-gradient(135deg, #06B6D4 0%, #3B82F6 100%); padding: 1.5rem; border-radius: 12px; margin-bottom: 1.5rem;">
            <h2 style="margin: 0 0 6px 0;">⚙️ Part 2: Management Category Dashboard</h2>
            <p style="margin: 0; opacity: 0.9; font-size: 0.95rem;">Automated license upgrading/downgrading, RBIusertype retention policies, Mailbox/DL governance, and SharePoint stale site cleanup.</p>
        </div>

        <div class="grid-cards" style="grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));">
            <div class="card" onclick="loadModule('exchange-mgmt')" style="cursor: pointer;">
                <div class="card-title">✉️ Exchange & Licenses (RBIusertype)</div>
                <h3 style="margin: 0.5rem 0; font-size: 1.8rem;">${exchangeData.total_users_analyzed || 0} Users</h3>
                <p style="color: var(--text-secondary); font-size: 0.85rem;">Retention Policies mapped to VIP, Standard, & Frontline</p>
                <button class="btn btn-secondary btn-block" style="margin-top: 1rem;">View License & Retention →</button>
            </div>

            <div class="card" onclick="loadModule('mailboxes')" style="cursor: pointer;">
                <div class="card-title">📬 Mailbox Management</div>
                <h3 style="margin: 0.5rem 0; font-size: 1.8rem;">${mailboxesData.mailboxes?.length || 0} Mailboxes</h3>
                <p style="color: var(--text-secondary); font-size: 0.85rem;">User, Shared, Room & Litigation Hold toggles</p>
                <button class="btn btn-secondary btn-block" style="margin-top: 1rem;">Manage Mailboxes →</button>
            </div>

            <div class="card" onclick="loadModule('distribution-groups')" style="cursor: pointer;">
                <div class="card-title">👥 Distribution Group Categorization</div>
                <h3 style="margin: 0.5rem 0; font-size: 1.8rem;">${distGroupsData.groups?.length || 0} Groups</h3>
                <p style="color: var(--text-secondary); font-size: 0.85rem;">Department Mapping & Naming Convention Compliance</p>
                <button class="btn btn-secondary btn-block" style="margin-top: 1rem;">View Distribution Groups →</button>
            </div>

            <div class="card" onclick="loadModule('sharepoint')" style="cursor: pointer;">
                <div class="card-title">📁 SharePoint & OneDrive Cleanup</div>
                <h3 style="margin: 0.5rem 0; font-size: 1.8rem;">${sharepointData.site_usage_summary?.sites?.length || 0} Sites</h3>
                <p style="color: var(--text-secondary); font-size: 0.85rem;">Stale file cleanup & Sensitive DLP sharing audits</p>
                <button class="btn btn-secondary btn-block" style="margin-top: 1rem;">View SharePoint & OneDrive →</button>
            </div>
        </div>
    `;
}

// ----------------------------------------------------
// CATEGORY 1: REPORTING RENDER FUNCTIONS
// ----------------------------------------------------
async function renderMailboxReports(container) {
    const res = await fetch(`${API_BASE}/reports/mailbox-reports`);
    const data = await res.json();

    container.innerHTML = `
        <div style="margin-bottom: 2rem;">
            <h3>📊 Mailbox Reports</h3>
            <div id="inbox-rules-tbl-container" style="margin-top: 1rem;"></div>
            <div id="retention-tbl-container" style="margin-top: 1.5rem;"></div>
            <div id="litigation-tbl-container" style="margin-top: 1.5rem;"></div>
        </div>
    `;

    renderInteractiveTable('inbox-rules-tbl-container', {
        data: data.inbox_rules || [],
        title: '📥 Inbox Rules Report',
        subtitle: 'Forwarding Category & Domain Filtered - Click row to inspect rule details',
        exportFileName: 'Inbox_Rules_Report',
        filterFields: ['forwarding_category', 'forwarding_domain', 'department', 'is_enabled'],
        columns: [
            { key: 'mailbox', label: 'Mailbox', format: v => `<strong>${v}</strong>` },
            { key: 'rule_name', label: 'Rule Name' },
            { key: 'forwarding_category', label: 'Forwarding Category', format: v => `<span class="badge" style="background: ${v === 'External' ? 'var(--accent-red)' : 'var(--accent-blue)'};">${v}</span>` },
            { key: 'forwarding_domain', label: 'Forwarding Domain', format: v => `<code>${v}</code>` },
            { key: 'department', label: 'Department' },
            { key: 'is_enabled', label: 'Status', format: v => `<span class="badge" style="background: ${v ? 'var(--accent-green)' : 'var(--text-muted)'};">${v ? 'Active' : 'Disabled'}</span>` }
        ]
    });

    renderInteractiveTable('retention-tbl-container', {
        data: data.retention_policies || [],
        title: '📅 Retention Policy Report',
        subtitle: 'Policy-wise & Department-wise breakdown - Click row to inspect policy details',
        exportFileName: 'Retention_Policy_Report',
        filterFields: ['department', 'action'],
        columns: [
            { key: 'policy_name', label: 'Policy Name', format: v => `<strong>${v}</strong>` },
            { key: 'department', label: 'Department Attribute', format: v => `<span class="badge" style="background: var(--accent-purple);">${v}</span>` },
            { key: 'retention_period', label: 'Retention Period' },
            { key: 'action', label: 'Action' },
            { key: 'assigned_mailboxes_count', label: 'Assigned Mailboxes', format: v => `<strong>${v} Mailboxes</strong>` }
        ]
    });

    renderInteractiveTable('litigation-tbl-container', {
        data: data.litigation_holds || [],
        title: '⚖️ Litigation Hold Report',
        subtitle: 'Click row to inspect litigation hold details',
        exportFileName: 'Litigation_Hold_Report',
        filterFields: ['department', 'litigation_hold_enabled', 'hold_owner'],
        columns: [
            { key: 'displayName', label: 'Mailbox Display Name', format: (v, item) => `<strong>${v}</strong> (${item.mailbox})` },
            { key: 'department', label: 'Department' },
            { key: 'litigation_hold_enabled', label: 'Litigation Hold Status', format: v => `<span class="badge" style="background: ${v ? 'var(--accent-green)' : 'var(--accent-amber)'};">${v ? 'Enabled' : 'Disabled'}</span>` },
            { key: 'hold_duration', label: 'Duration' },
            { key: 'hold_owner', label: 'Enabled By' },
            { key: 'storage_used_gb', label: 'Storage Used', format: v => `${v} GB` }
        ]
    });
}

// ----------------------------------------------------
// CATEGORY 2: AZURE AD RENDER FUNCTIONS
// ----------------------------------------------------
async function renderAzureADInactive(container, days = 90) {
    const res = await fetch(`${API_BASE}/reports/azure-ad/inactive?days=${days}`);
    const data = await res.json();

    container.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
            <h3>🔑 Azure AD Inactive Users</h3>
            <div style="display: flex; gap: 8px;">
                <button class="btn ${days === 60 ? 'btn-primary' : 'btn-secondary'}" onclick="renderAzureADInactive(document.getElementById('module-container'), 60)">60 Days Inactive</button>
                <button class="btn ${days === 90 ? 'btn-primary' : 'btn-secondary'}" onclick="renderAzureADInactive(document.getElementById('module-container'), 90)">90 Days Inactive</button>
                <button class="btn ${days === 120 ? 'btn-primary' : 'btn-secondary'}" onclick="renderAzureADInactive(document.getElementById('module-container'), 120)">120 Days Inactive</button>
            </div>
        </div>
        <p style="color: var(--text-secondary);">Showing users with no login activity for at least <strong>${days} days</strong>.</p>
        <div id="azuread-inactive-table-container"></div>
    `;

    renderInteractiveTable('azuread-inactive-table-container', {
        data: data || [],
        title: `Azure AD Inactive Users (${days} Days Threshold)`,
        subtitle: 'Click any user row to inspect full Azure AD user profile and attributes',
        exportFileName: `AzureAD_Inactive_Users_${days}Days`,
        filterFields: ['department', 'RBIusertype', 'assignedLicense'],
        columns: [
            { key: 'displayName', label: 'User', format: v => `<strong>${v}</strong>` },
            { key: 'userPrincipalName', label: 'UPN' },
            { key: 'department', label: 'Department' },
            { key: 'RBIusertype', label: 'RBI User Type', format: v => `<span class="badge" style="background: var(--accent-blue);">${v}</span>` },
            { key: 'assignedLicense', label: 'Assigned License' },
            { key: 'lastLoginDate', label: 'Last Login' },
            { key: 'inactiveDays', label: 'Inactivity Period', format: v => `<span class="badge" style="background: ${v > 100 ? 'var(--accent-red)' : 'var(--accent-amber)'};">${v} Days Inactive</span>` }
        ]
    });
}

async function renderAzureADLicenses(container) {
    const res = await fetch(`${API_BASE}/reports/azure-ad/licenses-summary`);
    const data = await res.json();

    container.innerHTML = `
        <div>
            <div class="grid-cards" style="margin-bottom: 1.5rem;">
                <div class="card">
                    <div class="card-title">Total Purchased</div>
                    <h2 style="margin: 0.5rem 0;">${data.total_purchased} Units</h2>
                </div>
                <div class="card">
                    <div class="card-title">Total Consumed</div>
                    <h2 style="margin: 0.5rem 0; color: var(--accent-blue);">${data.total_used} Units</h2>
                </div>
                <div class="card">
                    <div class="card-title">Total Available</div>
                    <h2 style="margin: 0.5rem 0; color: var(--accent-green);">${data.total_available} Units</h2>
                </div>
            </div>

            <div id="azuread-licenses-table-container"></div>
        </div>
    `;

    renderInteractiveTable('azuread-licenses-table-container', {
        data: data.categories || [],
        title: '💳 License Breakdown (Used / Available & Paid / Trial)',
        subtitle: 'Click any license SKU to view full licensing parameters',
        exportFileName: 'AzureAD_License_Breakdown',
        filterFields: ['category', 'licenseType'],
        columns: [
            { key: 'name', label: 'License SKU Name', format: v => `<strong>${v}</strong>` },
            { key: 'category', label: 'Category' },
            { key: 'licenseType', label: 'License Type', format: v => `<span class="badge" style="background: ${v === 'Trial' ? 'var(--accent-amber)' : 'var(--accent-green)'};">${v}</span>` },
            { key: 'usedUnits', label: 'Used Units' },
            { key: 'totalUnits', label: 'Total Purchased' },
            { key: 'availableUnits', label: 'Available Units', format: v => `<strong style="color: var(--accent-blue);">${v}</strong>` },
            { key: 'costPerUnitUsd', label: 'Cost / Unit (USD)', format: v => `$${v}/mo` }
        ]
    });
}

async function renderAzureADRiskyUsers(container) {
    const res = await fetch(`${API_BASE}/security-identity`);
    const data = await res.json();
    let riskyUsers = data.azure_ad_insights?.risky_users || [];

    container.innerHTML = `<div id="azuread-risky-table-container"></div>`;

    renderInteractiveTable('azuread-risky-table-container', {
        data: riskyUsers,
        title: '🚨 Azure Risky Users Summary',
        subtitle: 'User accounts flagged by Azure AD Identity Protection - Click row for full risk telemetry',
        exportFileName: 'AzureAD_Risky_Users',
        filterFields: ['riskLevel', 'riskState'],
        columns: [
            { key: 'userPrincipalName', label: 'User Principal Name', format: v => `<strong>${v}</strong>` },
            { key: 'riskLevel', label: 'Risk Level', format: v => `<span class="badge" style="background: ${v === 'HIGH' ? 'var(--accent-red)' : 'var(--accent-amber)'};">${v}</span>` },
            { key: 'riskState', label: 'Risk State' },
            { key: 'riskDetail', label: 'Risk Detail' },
            { key: 'lastUpdated', label: 'Last Detection' }
        ]
    });
}

// ----------------------------------------------------
// CATEGORY 3: MAILFLOW RENDER FUNCTIONS
// ----------------------------------------------------
async function renderMailflowVolume(container, windowDays = 30) {
    const res = await fetch(`${API_BASE}/reports/mailflow/volume?window_days=${windowDays}`);
    const data = await res.json();

    container.innerHTML = `
        <div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                <h3>📈 Mailflow: Emails Sent / Received Volume</h3>
                <div style="display: flex; gap: 8px;">
                    <button class="btn ${windowDays === 30 ? 'btn-primary' : 'btn-secondary'}" onclick="renderMailflowVolume(document.getElementById('module-container'), 30)">Last 30 Days</button>
                    <button class="btn ${windowDays === 90 ? 'btn-primary' : 'btn-secondary'}" onclick="renderMailflowVolume(document.getElementById('module-container'), 90)">Last 90 Days</button>
                    <button class="btn ${windowDays === 120 ? 'btn-primary' : 'btn-secondary'}" onclick="renderMailflowVolume(document.getElementById('module-container'), 120)">Last 120 Days</button>
                </div>
            </div>

            <div class="grid-cards" style="margin-bottom: 1.5rem;">
                <div class="card">
                    <div class="card-title">Total Sent Volume</div>
                    <h2 style="margin: 0.5rem 0; color: var(--accent-blue);">${(data.total_emails_sent || 0).toLocaleString()} Emails</h2>
                </div>
                <div class="card">
                    <div class="card-title">Total Received Volume</div>
                    <h2 style="margin: 0.5rem 0; color: var(--accent-purple);">${(data.total_emails_received || 0).toLocaleString()} Emails</h2>
                </div>
            </div>

            <div id="mailflow-senders-table-container" style="margin-bottom: 1.5rem;"></div>
            <div id="mailflow-recipients-table-container"></div>
        </div>
    `;

    renderInteractiveTable('mailflow-senders-table-container', {
        data: data.senders || [],
        title: `📤 Sender-Wise Telemetry (${windowDays} Days)`,
        subtitle: 'Click any sender row to inspect message count and payload details',
        exportFileName: `Mailflow_Senders_${windowDays}Days`,
        filterFields: ['department'],
        columns: [
            { key: 'sender', label: 'Sender Email', format: v => `<strong>${v}</strong>` },
            { key: 'department', label: 'Department' },
            { key: 'emails_sent', label: 'Emails Sent', format: v => (v || 0).toLocaleString() },
            { key: 'bytes_mb', label: 'Total Payload', format: v => `${v} MB` }
        ]
    });

    renderInteractiveTable('mailflow-recipients-table-container', {
        data: data.recipients || [],
        title: `📥 Recipient-Wise Telemetry (${windowDays} Days)`,
        subtitle: 'Click any recipient row to inspect message count and payload details',
        exportFileName: `Mailflow_Recipients_${windowDays}Days`,
        filterFields: ['department'],
        columns: [
            { key: 'recipient', label: 'Recipient Email', format: v => `<strong>${v}</strong>` },
            { key: 'department', label: 'Department' },
            { key: 'emails_received', label: 'Emails Received', format: v => (v || 0).toLocaleString() },
            { key: 'bytes_mb', label: 'Total Payload', format: v => `${v} MB` }
        ]
    });
}

async function renderMailflowConnectors(container) {
    const res = await fetch(`${API_BASE}/reports/exchange-mailflow?window_days=30`);
    const data = await res.json();
    let connectors = data.mailflow_analytics?.connectors || [];

    container.innerHTML = `<div id="connectors-table-container"></div>`;

    renderInteractiveTable('connectors-table-container', {
        data: connectors,
        title: '🔌 Exchange Connectors Summary',
        subtitle: 'Click any connector row to view configuration details',
        exportFileName: 'Exchange_Connectors',
        filterFields: ['type', 'status'],
        columns: [
            { key: 'name', label: 'Connector Name', format: v => `<strong>${v}</strong>` },
            { key: 'type', label: 'Connector Type', format: v => `<span class="badge" style="background: var(--accent-blue);">${v}</span>` },
            { key: 'status', label: 'Status', format: v => `<span class="badge" style="background: ${v === 'Active' ? 'var(--accent-green)' : 'var(--accent-amber)'};">${v}</span>` }
        ]
    });
}

async function renderMailflowTransportRules(container) {
    const res = await fetch(`${API_BASE}/reports/exchange-mailflow?window_days=30`);
    const data = await res.json();
    let rules = data.mailflow_analytics?.transport_rules || [];

    container.innerHTML = `<div id="transport-rules-table-container"></div>`;

    renderInteractiveTable('transport-rules-table-container', {
        data: rules,
        title: '⚙️ Transport Rules Summary',
        subtitle: 'Click any transport rule to view details',
        exportFileName: 'Transport_Rules_Summary',
        filterFields: ['enabled'],
        columns: [
            { key: 'priority', label: 'Priority', format: v => `<strong>Rule #${v}</strong>` },
            { key: 'rule_name', label: 'Rule Name' },
            { key: 'action', label: 'Execution Action', format: v => `<code>${v}</code>` },
            { key: 'enabled', label: 'State', format: v => `<span class="badge" style="background: ${v ? 'var(--accent-green)' : 'var(--text-muted)'};">${v ? 'Enabled' : 'Disabled'}</span>` }
        ]
    });
}

async function renderMailflowAutoForward(container) {
    const res = await fetch(`${API_BASE}/reports/exchange-mailflow?window_days=30`);
    const data = await res.json();
    let forwards = data.mailflow_analytics?.domain_auto_forwarding || [];

    container.innerHTML = `<div id="auto-forward-table-container"></div>`;

    renderInteractiveTable('auto-forward-table-container', {
        data: forwards,
        title: '🔀 External Auto-Forwarding Details (Sender & Recipient Wise)',
        subtitle: 'Click any auto-forwarding rule to view risk audit payload',
        exportFileName: 'Auto_Forwarding_Details',
        filterFields: ['status'],
        columns: [
            { key: 'source_mailbox', label: 'Source Sender Mailbox', format: v => `<strong>${v}</strong>` },
            { key: 'forward_target', label: 'Forwarding Recipient Target', format: v => `<code>${v}</code>` },
            { key: 'status', label: 'Security Risk Audit', format: v => `<span class="badge" style="background: ${v === 'FLAGGED_RISK' ? 'var(--accent-red)' : 'var(--accent-green)'};">${v}</span>` }
        ]
    });
}

// ----------------------------------------------------
// CATEGORY 4: COLLABORATION RENDER FUNCTIONS
// ----------------------------------------------------
async function renderTeamsCallQuality(container) {
    const res = await fetch(`${API_BASE}/reports/collaboration`);
    const data = await res.json();
    let cqd = data.teams_call_quality || {};

    container.innerHTML = `
        <div>
            <div class="grid-cards" style="margin-bottom: 1.5rem;">
                <div class="card">
                    <div class="card-title">Overall Audio Quality</div>
                    <h2 style="margin: 0.5rem 0; color: var(--accent-green);">${cqd.overall_audio_quality_score}%</h2>
                </div>
                <div class="card">
                    <div class="card-title">Poor Call Percentage</div>
                    <h2 style="margin: 0.5rem 0; color: var(--accent-amber);">${cqd.poor_call_percentage}%</h2>
                </div>
                <div class="card">
                    <div class="card-title">Analyzed Calls</div>
                    <h2 style="margin: 0.5rem 0;">${(cqd.total_calls_analyzed || 0).toLocaleString()}</h2>
                </div>
            </div>

            <div id="teams-call-quality-table-container"></div>
        </div>
    `;

    renderInteractiveTable('teams-call-quality-table-container', {
        data: cqd.issues_by_network || [],
        title: '📞 Network Subnet Audio Quality Telemetry',
        subtitle: 'Click any subnet row to inspect jitter and packet loss telemetry',
        exportFileName: 'Teams_Call_Quality_Subnets',
        filterFields: ['location'],
        columns: [
            { key: 'subnet', label: 'Subnet', format: v => `<code>${v}</code>` },
            { key: 'location', label: 'Location' },
            { key: 'jitter_ms', label: 'Jitter (ms)', format: v => `${v} ms` },
            { key: 'packet_loss_pct', label: 'Packet Loss %', format: v => `<span class="badge" style="background: ${v > 2 ? 'var(--accent-red)' : 'var(--accent-green)'};">${v}%</span>` }
        ]
    });
}

async function renderSPOneDriveTrend(container) {
    const res = await fetch(`${API_BASE}/reports/collaboration`);
    const data = await res.json();
    let sites = data.sharepoint_analytics?.sites || [];

    container.innerHTML = `<div id="sp-trend-table-container"></div>`;

    renderInteractiveTable('sp-trend-table-container', {
        data: sites,
        title: '📊 SharePoint & OneDrive 60-Day Usage Trend',
        subtitle: 'Click any site row to view usage trends & site properties',
        exportFileName: 'SharePoint_OneDrive_Trend',
        filterFields: ['externalSharing'],
        columns: [
            { key: 'siteName', label: 'Site Name', format: v => `<strong>${v}</strong>` },
            { key: 'url', label: 'URL', format: v => `<a href="${v}" target="_blank" onclick="event.stopPropagation();">${v}</a>` },
            { key: 'storageUsedGB', label: 'Storage Used', format: v => `${v} GB` },
            { key: 'lastAccessedDaysAgo', label: 'Last Activity', format: v => `${v} days ago` },
            { key: 'externalSharing', label: 'External Sharing', format: v => `<span class="badge" style="background: ${v === 'Disabled' ? 'var(--accent-green)' : 'var(--accent-amber)'};">${v}</span>` }
        ]
    });
}

async function renderExternalSharingAudit(container) {
    const res = await fetch(`${API_BASE}/reports/collaboration`);
    const data = await res.json();
    let sites = data.sharepoint_analytics?.external_sharing_sites || [];

    container.innerHTML = `<div id="ext-sharing-table-container"></div>`;

    renderInteractiveTable('ext-sharing-table-container', {
        data: sites,
        title: '🔒 External Sharing Details & Sensitive Data DLP Audit',
        subtitle: 'Click any external sharing site to view DLP audit details',
        exportFileName: 'External_Sharing_Audit',
        filterFields: ['externalSharing'],
        columns: [
            { key: 'siteName', label: 'Site Name', format: v => `<strong>${v}</strong>` },
            { key: 'url', label: 'URL', format: v => `<a href="${v}" target="_blank" onclick="event.stopPropagation();">${v}</a>` },
            { key: 'externalSharing', label: 'Sharing Policy', format: v => `<span class="badge" style="background: var(--accent-amber);">${v}</span>` },
            { key: 'sensitiveDataFiles', label: 'Sensitive DLP Items Flagged', format: v => `<strong style="color: var(--accent-red);">${v} PII/PCI Files</strong>` }
        ]
    });
}

async function renderInactiveFiles(container) {
    const res = await fetch(`${API_BASE}/reports/collaboration/file-types-and-inactive`);
    const data = await res.json();
    let libs = data.libraries || [];

    container.innerHTML = `<div id="inactive-files-table-container"></div>`;

    renderInteractiveTable('inactive-files-table-container', {
        data: libs,
        title: '📁 Inactive Files, Folders, and Libraries (Last Accessed Attribute)',
        subtitle: 'Click any library row to view complete inactive library metadata',
        exportFileName: 'Inactive_Libraries_Report',
        filterFields: ['site'],
        columns: [
            { key: 'site', label: 'Site Name', format: v => `<strong>${v}</strong>` },
            { key: 'libraryName', label: 'Library Name' },
            { key: 'url', label: 'Library URL', format: v => `<a href="${v}" target="_blank" onclick="event.stopPropagation();">${v}</a>` },
            { key: 'inactiveFilesCount', label: 'Inactive Items Count', format: v => `<strong>${v} Files</strong>` },
            { key: 'lastAccessedDaysAgo', label: 'Last Accessed', format: v => `<span class="badge" style="background: var(--accent-amber);">${v} Days Unaccessed</span>` }
        ]
    });
}

async function renderFileTypeData(container) {
    const res = await fetch(`${API_BASE}/reports/collaboration/file-types-and-inactive`);
    const data = await res.json();
    let libs = data.libraries || [];

    let rows = [];
    libs.forEach(l => {
        (l.fileTypes || []).forEach(ft => {
            rows.push({
                site: l.site,
                libraryName: l.libraryName,
                extension: ft.extension,
                count: ft.count,
                sizeMB: ft.sizeMB,
                sampleUrl: ft.sampleUrl
            });
        });
    });

    container.innerHTML = `<div id="file-type-table-container"></div>`;

    renderInteractiveTable('file-type-table-container', {
        data: rows,
        title: '📄 File Type Data per Library with Direct File URLs',
        subtitle: 'Click any file type row to view full object properties',
        exportFileName: 'File_Types_Per_Library',
        filterFields: ['site', 'extension'],
        columns: [
            { key: 'libraryName', label: 'Library / Site', format: (v, item) => `<strong>${v}</strong> (${item.site})` },
            { key: 'extension', label: 'File Extension', format: v => `<span class="badge" style="background: var(--accent-blue);">${v}</span>` },
            { key: 'count', label: 'File Count', format: v => `${v} Files` },
            { key: 'sizeMB', label: 'Total Size', format: v => `${v} MB` },
            { key: 'sampleUrl', label: 'Sample Direct File URL', format: v => `<a href="${v}" target="_blank" onclick="event.stopPropagation();" style="color: var(--accent-green); text-decoration: underline;">🔗 ${v}</a>` }
        ]
    });
}

// ----------------------------------------------------
// CATEGORY 5: AUDITING RENDER FUNCTIONS
// ----------------------------------------------------
async function renderAppAuditLogs(container) {
    const res = await fetch(`${API_BASE}/auditing/logs`);
    const data = await res.json();

    container.innerHTML = `<div id="app-audit-logs-table-container"></div>`;

    renderInteractiveTable('app-audit-logs-table-container', {
        data: data || [],
        title: '📋 App Action Audit Log (Changes Made by Us in App)',
        subtitle: 'Click any log entry to view exact execution details and parameters',
        exportFileName: 'App_Action_Audit_Logs',
        filterFields: ['action', 'module'],
        columns: [
            { key: 'user_principal_name', label: 'User Principal Name', format: v => `<strong>${v}</strong>` },
            { key: 'action', label: 'Action Type', format: v => `<span class="badge" style="background: var(--accent-blue);">${v}</span>` },
            { key: 'module', label: 'Module' },
            { key: 'details', label: 'Change Details' },
            { key: 'timestamp', label: 'Timestamp', format: v => new Date(v).toLocaleString() }
        ]
    });
}

// ----------------------------------------------------
// CATEGORY 7: MANAGEMENT SUB-MODULE RENDER FUNCTIONS
// ----------------------------------------------------
async function renderMgmtDistributionGroups(container) {
    const res = await fetch(`${API_BASE}/reports/management/distribution-groups`);
    const groups = await res.json();

    container.innerHTML = `
        <div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                <h3>👥 Distribution Group Module</h3>
                <button class="btn btn-primary" onclick="alert('Create DL Form: Naming convention template active.')">➕ Create Distribution Group</button>
            </div>
            <div id="mgmt-dist-groups-table-container"></div>
        </div>
    `;

    renderInteractiveTable('mgmt-dist-groups-table-container', {
        data: groups,
        title: 'DL Categorization based on Naming Convention & Department Mapping',
        subtitle: 'Click any DL row to view complete group details & member list',
        exportFileName: 'Management_Distribution_Groups',
        filterFields: ['mappedDepartment', 'mappedTeam', 'namingConventionMatch'],
        columns: [
            { key: 'groupName', label: 'Group Name', format: v => `<strong>${v}</strong>` },
            { key: 'primarySmtpAddress', label: 'Primary SMTP Address' },
            { key: 'mappedDepartment', label: 'Naming Dept / Team', format: (v, item) => `<span class="badge" style="background: ${item.namingConventionMatch ? 'var(--accent-green)' : 'var(--accent-amber)'};">${v} / ${item.mappedTeam}</span>` },
            { key: 'memberCount', label: 'Members', format: v => `<strong>${v} Members</strong>` },
            { key: 'groupName', label: 'Actions', format: (v, item) => `
                <button class="btn btn-secondary" onclick="event.stopPropagation(); alert('Manage members for ${v}: ' + ${JSON.stringify(item.members || [])}.join(', '))">👥 Members</button>
                <button class="btn btn-secondary" onclick="event.stopPropagation(); alert('Edit settings for ${v}')">⚙️ Settings</button>
            ` }
        ]
    });
}

async function renderMgmtSharedMailboxes(container) {
    const res = await fetch(`${API_BASE}/reports/management/shared-mailboxes`);
    const mailboxes = await res.json();

    container.innerHTML = `
        <div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                <h3>🤝 Shared Mailbox Management</h3>
                <button class="btn btn-primary" onclick="alert('Shared Mailbox Creation Wizard')">➕ Create Shared Mailbox</button>
            </div>
            <div id="mgmt-shared-mailboxes-table-container"></div>
        </div>
    `;

    renderInteractiveTable('mgmt-shared-mailboxes-table-container', {
        data: mailboxes,
        title: 'Shared Mailbox Categorization based on Naming Convention & Department Mapping',
        subtitle: 'Click any shared mailbox row to view full permissions & delegation',
        exportFileName: 'Management_Shared_Mailboxes',
        filterFields: ['mappedDepartment', 'calendarPermissions'],
        columns: [
            { key: 'displayName', label: 'Shared Mailbox', format: v => `<strong>${v}</strong>` },
            { key: 'primarySmtpAddress', label: 'SMTP Address' },
            { key: 'mappedDepartment', label: 'Dept / Team', format: (v, item) => `<span class="badge" style="background: var(--accent-green);">${v} / ${item.mappedTeam}</span>` },
            { key: 'fullAccessMembers', label: 'Full Access Members', format: v => Array.isArray(v) ? v.join(', ') : v },
            { key: 'calendarPermissions', label: 'Calendar Permissions' },
            { key: 'displayName', label: 'Management Actions', format: v => `
                <button class="btn btn-secondary" onclick="event.stopPropagation(); alert('Edit member additions for ${v}')">👥 Add Members</button>
                <button class="btn btn-secondary" onclick="event.stopPropagation(); alert('Modify attributes for ${v}')">⚙️ Attributes</button>
            ` }
        ]
    });
}

async function renderMgmtRoomMailboxes(container) {
    const res = await fetch(`${API_BASE}/reports/management/room-mailboxes`);
    const rooms = await res.json();

    container.innerHTML = `
        <div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                <h3>🏢 Room Mailbox Module</h3>
                <button class="btn btn-primary" onclick="alert('Room Mailbox Creation Form')">➕ Create Room Mailbox</button>
            </div>
            <div id="mgmt-room-mailboxes-table-container"></div>
        </div>
    `;

    renderInteractiveTable('mgmt-room-mailboxes-table-container', {
        data: rooms,
        title: 'Room Booking Details, Permissions Management, & Calendar Settings Data',
        subtitle: 'Click any room mailbox to view booking schedule details & policies',
        exportFileName: 'Management_Room_Mailboxes',
        filterFields: ['location', 'bookingPolicy'],
        columns: [
            { key: 'displayName', label: 'Room Mailbox', format: v => `<strong>${v}</strong>` },
            { key: 'location', label: 'Location & Capacity', format: (v, item) => `${v} (Cap: ${item.capacity})` },
            { key: 'bookingPolicy', label: 'Booking Policy', format: v => `<span class="badge" style="background: var(--accent-purple);">${v}</span>` },
            { key: 'calendarBookingPermissions', label: 'Calendar Booking Permissions' },
            { key: 'recentBookings', label: 'Schedule Status', format: v => `${v ? v.length : 0} Bookings Scheduled` },
            { key: 'displayName', label: 'Actions', format: (v, item) => `
                <button class="btn btn-secondary" onclick="event.stopPropagation(); alert('Room Booking Details for ${v}:\\n' + JSON.stringify(${JSON.stringify(item.recentBookings || [])}, null, 2))">📅 Booking Details</button>
                <button class="btn btn-secondary" onclick="event.stopPropagation(); alert('Manage permissions & settings for ${v}')">⚙️ Settings</button>
            ` }
        ]
    });
}

async function renderInboxRulesReport(container) {
    const res = await fetch(`${API_BASE}/mailboxes/inbox-rules`);
    const rules = await res.json();

    const total = rules.length;
    const externalRules = rules.filter(r => r.forwarding_category === 'External');
    const internalRules = rules.filter(r => r.forwarding_category === 'Internal');
    const disabledCount = rules.filter(r => !r.is_enabled).length;

    const alertBanner = externalRules.length > 0 ? `
        <div class="card" style="background: rgba(220, 38, 38, 0.1); border-left: 4px solid var(--accent-red); margin-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
            <div>
                <h4 style="color: #ef4444; margin: 0 0 4px 0;">🚨 Security Alert: ${externalRules.length} External Forwarding Rule(s) Detected</h4>
                <p style="margin: 0; color: var(--text-secondary); font-size: 0.9rem;">Auto-forwarding rules sending emails to external recipient domains pose potential data exfiltration and compliance risks.</p>
            </div>
            <button class="btn btn-danger" style="background: #d13438; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; white-space: nowrap;" onclick="loadModule('mgmt-inbox-rules')">🛡️ Remediate in Management →</button>
        </div>
    ` : '';

    container.innerHTML = `
        <div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                <h3>📥 Exchange Inbox Rule Report (Forwarding & Security Audit)</h3>
                <button class="btn btn-primary" onclick="loadModule('mgmt-inbox-rules')">⚡ Go to Inbox Rule Management →</button>
            </div>

            ${alertBanner}

            <div class="grid-cards" style="margin-bottom: 1.5rem;">
                <div class="card">
                    <div class="card-title">📥 Total Inbox Rules</div>
                    <h3 style="font-size: 1.8rem; margin: 0.5rem 0;">${total}</h3>
                    <p style="color: var(--text-secondary); font-size: 0.85rem;">Scanned across all tenant mailboxes</p>
                </div>
                <div class="card" style="border-left: 4px solid var(--accent-red);">
                    <div class="card-title">⚠️ External Forwarding Rules</div>
                    <h3 style="font-size: 1.8rem; margin: 0.5rem 0; color: var(--accent-red);">${externalRules.length}</h3>
                    <p style="color: var(--text-secondary); font-size: 0.85rem;">Forwarding emails to non-tenant domains</p>
                </div>
                <div class="card" style="border-left: 4px solid var(--accent-blue);">
                    <div class="card-title">🏢 Internal Auto-Redirect Rules</div>
                    <h3 style="font-size: 1.8rem; margin: 0.5rem 0;">${internalRules.length}</h3>
                    <p style="color: var(--text-secondary); font-size: 0.85rem;">Internal forwarding within tenant domain</p>
                </div>
                <div class="card">
                    <div class="card-title">⏸️ Disabled Rules</div>
                    <h3 style="font-size: 1.8rem; margin: 0.5rem 0;">${disabledCount}</h3>
                    <p style="color: var(--text-secondary); font-size: 0.85rem;">Rules configured but currently inactive</p>
                </div>
            </div>

            <div id="inbox-rules-report-table-container"></div>
        </div>
    `;

    renderInteractiveTable('inbox-rules-report-table-container', {
        data: rules,
        title: 'Detailed Rule Inventory',
        subtitle: 'Click any rule row to view complete rule parameters & audit info',
        exportFileName: 'Inbox_Rules_Audit_Inventory',
        filterFields: ['forwarding_category', 'forwarding_domain', 'department', 'is_enabled', 'risk_level'],
        columns: [
            { key: 'mailbox', label: 'Mailbox', format: v => `<strong>${v}</strong>` },
            { key: 'rule_name', label: 'Rule Name' },
            { key: 'forwarding_category', label: 'Category', format: v => `<span class="badge" style="background: ${v === 'External' ? 'var(--accent-red)' : 'var(--accent-blue)'};">${v}</span>` },
            { key: 'forwarding_domain', label: 'Target Domain', format: v => `<code>${v || 'N/A'}</code>` },
            { key: 'forward_to', label: 'Forwarding Destination', format: v => v || 'N/A' },
            { key: 'department', label: 'Department', format: v => v || 'General' },
            { key: 'is_enabled', label: 'Status', format: v => `<span class="badge" style="background: ${v ? 'var(--accent-green)' : 'var(--text-muted)'};">${v ? 'Active' : 'Disabled'}</span>` },
            { key: 'risk_level', label: 'Risk Level', format: (v, item) => `<span class="badge" style="background: ${v === 'CRITICAL' || v === 'HIGH' || item.forwarding_category === 'External' ? 'var(--accent-red)' : 'var(--accent-green)'};">${v || (item.forwarding_category === 'External' ? 'HIGH' : 'LOW')}</span>` }
        ]
    });
}

async function renderMgmtInboxRules(container) {
    const res = await fetch(`${API_BASE}/mailboxes/inbox-rules`);
    const rules = await res.json();

    container.innerHTML = `
        <div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; flex-wrap: wrap; gap: 10px;">
                <h3>⚡ Exchange Inbox Rule Management & Remediation</h3>
                <div style="display: flex; gap: 10px;">
                    <button class="btn btn-danger" style="background: #d13438; color: white; border: none; border-radius: 4px; padding: 8px 16px; cursor: pointer;" onclick="handlePurgeExternalInboxRules()">🛡️ Purge All External Rules</button>
                    <button class="btn btn-primary" onclick="showCreateInboxRuleModal()">➕ Create Inbox Rule</button>
                </div>
            </div>

            <div class="card" style="background: rgba(59, 130, 246, 0.1); border-left: 4px solid var(--accent-blue); margin-bottom: 1.5rem;">
                <h4 style="margin: 0 0 4px 0; color: #3b82f6;">⚙️ Exchange Inbox Rule Governance Engine</h4>
                <p style="margin: 0; color: var(--text-secondary); font-size: 0.9rem;">Provision new inbox rules for user or shared mailboxes, status-toggle active/disabled rules, delete rules, or trigger tenant-wide external auto-forwarding rule purges with full SQL audit logging.</p>
            </div>

            <div id="create-inbox-rule-card" class="card" style="display: none; margin-bottom: 1.5rem; border: 2px solid var(--accent-blue);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h4>➕ Create New Mailbox Inbox Rule</h4>
                    <button class="btn btn-secondary btn-sm" onclick="document.getElementById('create-inbox-rule-card').style.display='none'">✕ Close</button>
                </div>
                <form id="create-rule-form" onsubmit="submitCreateInboxRule(event)">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 1rem;">
                        <div>
                            <label style="font-weight: 600; display: block; margin-bottom: 5px;">Mailbox (User UPN / Shared Mailbox)</label>
                            <input type="email" id="rule-upn" required placeholder="e.g. user001@contoso.com" class="form-control" style="width: 100%;" />
                        </div>
                        <div>
                            <label style="font-weight: 600; display: block; margin-bottom: 5px;">Rule Display Name</label>
                            <input type="text" id="rule-name" required placeholder="e.g. Auto Forward Invoices" class="form-control" style="width: 100%;" />
                        </div>
                    </div>
                    <div style="margin-bottom: 1rem;">
                        <label style="font-weight: 600; display: block; margin-bottom: 5px;">Forwarding Destination Email Address</label>
                        <input type="email" id="rule-target" required placeholder="e.g. external.audit@partner.com or team@contoso.com" class="form-control" style="width: 100%;" />
                    </div>
                    <div style="margin-bottom: 1rem;">
                        <label style="display: flex; align-items: center; gap: 8px; font-weight: 500;">
                            <input type="checkbox" id="rule-stop-processing" checked />
                            Stop processing more rules on this mailbox
                        </label>
                    </div>
                    <button type="submit" class="btn btn-primary">Save & Apply Rule</button>
                </form>
            </div>

            <div id="mgmt-inbox-rules-table-container"></div>
        </div>
    `;

    renderInteractiveTable('mgmt-inbox-rules-table-container', {
        data: rules,
        title: 'Manage Active & Inactive Rules Across Mailboxes',
        subtitle: 'Click any rule row to view complete parameters & remediation options',
        exportFileName: 'Management_Inbox_Rules',
        filterFields: ['forwarding_category', 'is_enabled'],
        columns: [
            { key: 'mailbox', label: 'Mailbox UPN', format: v => `<strong>${v}</strong>` },
            { key: 'rule_name', label: 'Rule Name' },
            { key: 'forwarding_category', label: 'Category', format: v => `<span class="badge" style="background: ${v === 'External' ? 'var(--accent-red)' : 'var(--accent-blue)'};">${v}</span>` },
            { key: 'forward_to', label: 'Forwarding Target', format: (v, item) => `<code>${v || item.forwarding_domain}</code>` },
            { key: 'is_enabled', label: 'Status', format: v => `<span class="badge" style="background: ${v ? 'var(--accent-green)' : 'var(--text-muted)'};">${v ? 'Active' : 'Disabled'}</span>` },
            { key: 'mailbox', label: 'Actions', format: (v, item) => `
                <button class="btn btn-secondary btn-sm" onclick="event.stopPropagation(); handleToggleInboxRule('${v}', '${item.rule_name}')">
                    ${item.is_enabled ? '⏸️ Disable' : '▶️ Enable'}
                </button>
                <button class="btn btn-danger btn-sm" style="background: #d13438; color: white; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; margin-left: 4px;" onclick="event.stopPropagation(); handleDeleteInboxRule('${v}', '${item.rule_name}')">
                    🗑️ Delete
                </button>
            ` }
        ]
    });
}

function showCreateInboxRuleModal() {
    const card = document.getElementById('create-inbox-rule-card');
    if (card) {
        card.style.display = card.style.display === 'none' ? 'block' : 'none';
        card.scrollIntoView({ behavior: 'smooth' });
    }
}

async function submitCreateInboxRule(e) {
    e.preventDefault();
    const upn = document.getElementById('rule-upn').value.trim();
    const ruleName = document.getElementById('rule-name').value.trim();
    const forwardTo = document.getElementById('rule-target').value.trim();
    const stopProcessing = document.getElementById('rule-stop-processing').checked;

    try {
        const res = await fetch(`${API_BASE}/mailboxes/inbox-rules/create`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_principal_name: upn,
                rule_name: ruleName,
                forward_to: forwardTo,
                stop_processing_more_rules: stopProcessing,
                is_enabled: true
            })
        });
        const data = await res.json();
        if (res.ok) {
            alert(`✅ Inbox Rule '${ruleName}' created successfully for ${upn}!`);
            renderMgmtInboxRules(document.getElementById('module-container'));
        } else {
            alert(`❌ Error creating rule: ${data.detail || 'API failure'}`);
        }
    } catch (err) {
        alert(`❌ Network error: ${err.message}`);
    }
}

async function handleToggleInboxRule(upn, ruleName) {
    if (!confirm(`Are you sure you want to toggle status for rule '${ruleName}' on mailbox ${upn}?`)) return;
    try {
        const res = await fetch(`${API_BASE}/mailboxes/inbox-rules/action`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_principal_name: upn,
                rule_name: ruleName,
                action: 'TOGGLE'
            })
        });
        const data = await res.json();
        if (res.ok) {
            alert(`✅ Rule '${ruleName}' status updated!`);
            renderMgmtInboxRules(document.getElementById('module-container'));
        } else {
            alert(`❌ Error: ${data.detail || 'Action failed'}`);
        }
    } catch (err) {
        alert(`❌ Network error: ${err.message}`);
    }
}

async function handleDeleteInboxRule(upn, ruleName) {
    if (!confirm(`⚠️ Are you sure you want to DELETE rule '${ruleName}' from mailbox ${upn}? This action cannot be undone.`)) return;
    try {
        const res = await fetch(`${API_BASE}/mailboxes/inbox-rules/action`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_principal_name: upn,
                rule_name: ruleName,
                action: 'DELETE'
            })
        });
        const data = await res.json();
        if (res.ok) {
            alert(`✅ Inbox rule '${ruleName}' deleted successfully!`);
            renderMgmtInboxRules(document.getElementById('module-container'));
        } else {
            alert(`❌ Error: ${data.detail || 'Deletion failed'}`);
        }
    } catch (err) {
        alert(`❌ Network error: ${err.message}`);
    }
}

async function handlePurgeExternalInboxRules() {
    if (!confirm(`⚠️ SECURITY WARNING: Are you sure you want to purge ALL external forwarding rules across the tenant? This will delete all rules redirecting emails outside contoso.com.`)) return;
    try {
        const res = await fetch(`${API_BASE}/mailboxes/inbox-rules/action`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_principal_name: 'tenant_wide',
                rule_name: 'all_external',
                action: 'PURGE_EXTERNAL'
            })
        });
        const data = await res.json();
        if (res.ok) {
            alert(`🛡️ Security Purge Complete! ${data.purged_count} external rules were removed.`);
            renderMgmtInboxRules(document.getElementById('module-container'));
        } else {
            alert(`❌ Error: ${data.detail || 'Purge failed'}`);
        }
    } catch (err) {
        alert(`❌ Network error: ${err.message}`);
    }
}

// ----------------------------------------------------
// POLICY DASHBOARD MODULE RENDER
// ----------------------------------------------------
async function renderPolicyDashboard(container) {
    try {
        const res = await fetch(`${API_BASE}/ai-governance/policies`);
        const policies = await res.json();

        const activeCount = policies.filter(p => p.is_enabled).length;
        const totalCount = policies.length;
        const moduleCategories = Array.from(new Set(policies.map(p => p.category))).sort();

        let html = `
            <!-- Top Summary KPI Cards -->
            <div class="grid-cards" style="margin-bottom: 1.5rem;">
                <div class="card" style="border-left: 4px solid #0078D4;">
                    <div class="card-title">📜 Configured Tenant Policies</div>
                    <h2 style="font-size: 2.2rem; margin: 0.4rem 0; color: #0078D4;">${activeCount} <span style="font-size: 1rem; color: #605E5C;">/ ${totalCount} Active</span></h2>
                    <p style="color: #605E5C; font-size: 0.85rem; margin: 0;">Active automated governance & compliance conditions</p>
                </div>
                <div class="card" style="border-left: 4px solid #107C41;">
                    <div class="card-title">⚡ Governance Enforcement Phase</div>
                    <h2 style="font-size: 1.6rem; margin: 0.4rem 0; color: #107C41;">Phase 2 & 3 Enabled</h2>
                    <p style="color: #605E5C; font-size: 0.85rem; margin: 0;">Automated remediation & semi-automated approval active</p>
                </div>
                <div class="card" style="border-left: 4px solid #5C2D91;">
                    <div class="card-title">🛡️ Covered Dashboards & Reports</div>
                    <h2 style="font-size: 2.2rem; margin: 0.4rem 0; color: #5C2D91;">${moduleCategories.length} Modules</h2>
                    <p style="color: #605E5C; font-size: 0.85rem; margin: 0;">Every report & dashboard has customizable conditions</p>
                </div>
            </div>

            <!-- Policy Controls & Category Filter Bar -->
            <div style="background: #FFFFFF; padding: 1rem 1.2rem; border-radius: 4px; border: 1px solid #EDEBE9; margin-bottom: 1.5rem; display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="display: flex; gap: 8px; flex-wrap: wrap;" id="policy-cat-tabs">
                    <button class="btn btn-primary pol-tab-btn active" data-cat="ALL">All Categories (${totalCount})</button>
                    ${moduleCategories.map(c => `<button class="btn btn-secondary pol-tab-btn" data-cat="${c}">${c.toUpperCase()}</button>`).join('')}
                </div>
                <div style="display: flex; gap: 10px; align-items: center;">
                    <input type="text" id="policy-search-input" class="form-control" placeholder="🔍 Search policy conditions..." style="height: 34px; padding: 4px 10px; font-size: 0.85rem; min-width: 220px;" />
                </div>
            </div>

            <!-- Policy Cards Grid -->
            <div id="policies-grid-container" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 1.25rem;"></div>
        `;

        container.innerHTML = html;

        function renderPolicyCards(filterCat = 'ALL', searchStr = '') {
            const grid = document.getElementById('policies-grid-container');
            if (!grid) return;

            let filtered = policies;
            if (filterCat !== 'ALL') {
                filtered = filtered.filter(p => p.category.toLowerCase() === filterCat.toLowerCase());
            }
            if (searchStr) {
                const s = searchStr.toLowerCase();
                filtered = filtered.filter(p => 
                    p.policy_name.toLowerCase().includes(s) || 
                    (p.description && p.description.toLowerCase().includes(s)) ||
                    p.category.toLowerCase().includes(s)
                );
            }

            if (!filtered.length) {
                grid.innerHTML = `<div class="card" style="grid-column: 1 / -1; text-align: center; color: #605E5C; padding: 2.5rem;">No policy rules match your search or filter.</div>`;
                return;
            }

            grid.innerHTML = filtered.map(pol => {
                let parsedCriteria = {};
                try {
                    parsedCriteria = pol.criteria_json ? JSON.parse(pol.criteria_json) : {};
                } catch(e) { parsedCriteria = {}; }

                const formattedCriteria = Object.entries(parsedCriteria).map(([k, v]) => `
                    <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.82rem; padding: 4px 0; border-bottom: 1px dashed #EDEBE9;">
                        <span style="color: #605E5C; font-weight: 500;">${cleanKeyLabel(k)}:</span>
                        <input type="text" class="form-control policy-crit-input" data-cat="${pol.category}" data-key="${k}" value="${v}" style="width: 140px; padding: 2px 6px; font-size: 0.8rem; height: 26px; text-align: right;" />
                    </div>
                `).join('');

                const phaseBadges = {
                    'PHASE_1_REPORTING': '<span class="badge" style="background:#EFF6FC; color:#0078D4; border:1px solid #0078D4;">Phase 1: Reporting</span>',
                    'PHASE_2_SEMI_AUTOMATED': '<span class="badge" style="background:#FFF4CE; color:#797775; border:1px solid #F2C80F;">Phase 2: Semi-Automated</span>',
                    'PHASE_3_FULLY_AUTOMATED': '<span class="badge" style="background:#DFF6DD; color:#107C41; border:1px solid #107C41;">Phase 3: Fully Automated</span>'
                };

                return `
                    <div class="card" style="display: flex; flex-direction: column; justify-content: space-between; border-top: 4px solid ${pol.is_enabled ? '#107C41' : '#A19F9D'};">
                        <div>
                            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.6rem;">
                                <div>
                                    <span style="font-size: 0.75rem; font-weight: 700; color: #0078D4; text-transform: uppercase;">${pol.category.toUpperCase()} MODULE</span>
                                    <h3 style="font-size: 1.05rem; font-weight: 600; color: #201F1E; margin: 2px 0 0 0;">${pol.policy_name}</h3>
                                </div>
                                <label class="m365-toggle-switch" title="Toggle Policy Status">
                                    <input type="checkbox" class="policy-enable-toggle" data-cat="${pol.category}" ${pol.is_enabled ? 'checked' : ''} />
                                    <span class="toggle-slider"></span>
                                </label>
                            </div>
                            <p style="font-size: 0.83rem; color: #605E5C; margin-bottom: 1rem; line-height: 1.4;">${pol.description || 'No description configured.'}</p>
                            
                            <div style="background: #F8F9FA; padding: 0.75rem; border-radius: 4px; border: 1px solid #EDEBE9; margin-bottom: 1rem;">
                                <div style="font-size: 0.78rem; font-weight: 700; color: #323130; text-transform: uppercase; margin-bottom: 6px;">⚙️ Condition Rules & Thresholds:</div>
                                ${formattedCriteria || '<div style="font-size: 0.8rem; color:#a19f9d;">No editable threshold rules configured.</div>'}
                            </div>
                        </div>

                        <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #EDEBE9; padding-top: 0.75rem; margin-top: 0.5rem;">
                            <div>${phaseBadges[pol.phase_level] || pol.phase_level}</div>
                            <button class="btn btn-primary btn-save-policy" data-cat="${pol.category}" style="padding: 4px 10px; font-size: 0.8rem;">💾 Save Rule</button>
                        </div>
                    </div>
                `;
            }).join('');

            grid.querySelectorAll('.btn-save-policy').forEach(btn => {
                btn.addEventListener('click', async () => {
                    const cat = btn.getAttribute('data-cat');
                    const targetPol = policies.find(p => p.category === cat);
                    if (!targetPol) return;

                    const isEnabled = grid.querySelector(`.policy-enable-toggle[data-cat="${cat}"]`)?.checked ?? targetPol.is_enabled;
                    
                    let updatedCriteria = {};
                    grid.querySelectorAll(`.policy-crit-input[data-cat="${cat}"]`).forEach(input => {
                        const key = input.getAttribute('data-key');
                        let val = input.value;
                        if (val === 'true') val = true;
                        else if (val === 'false') val = false;
                        else if (!isNaN(val) && val.trim() !== '') val = Number(val);
                        updatedCriteria[key] = val;
                    });

                    btn.innerText = "⏳ Saving...";
                    btn.disabled = true;

                    try {
                        const payload = {
                            category: targetPol.category,
                            policy_name: targetPol.policy_name,
                            phase_level: targetPol.phase_level,
                            is_enabled: isEnabled,
                            description: targetPol.description,
                            criteria_json: JSON.stringify(updatedCriteria)
                        };

                        const saveRes = await fetch(`${API_BASE}/ai-governance/policies`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(payload)
                        });

                        if (saveRes.ok) {
                            btn.innerText = "✅ Saved!";
                            setTimeout(() => { btn.innerText = "💾 Save Rule"; btn.disabled = false; }, 1800);
                        } else {
                            alert("Failed to update policy rule conditions.");
                            btn.innerText = "💾 Save Rule";
                            btn.disabled = false;
                        }
                    } catch(err) {
                        alert(`Error saving policy: ${err.message}`);
                        btn.innerText = "💾 Save Rule";
                        btn.disabled = false;
                    }
                });
            });
        }

        const tabBtns = container.querySelectorAll('.pol-tab-btn');
        let currentTab = 'ALL';
        tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                tabBtns.forEach(b => {
                    b.classList.remove('active', 'btn-primary');
                    b.classList.add('btn-secondary');
                });
                btn.classList.remove('btn-secondary');
                btn.classList.add('active', 'btn-primary');
                currentTab = btn.getAttribute('data-cat');
                renderPolicyCards(currentTab, document.getElementById('policy-search-input')?.value || '');
            });
        });

        document.getElementById('policy-search-input')?.addEventListener('input', (e) => {
            renderPolicyCards(currentTab, e.target.value);
        });

        renderPolicyCards('ALL', '');

    } catch (e) {
        container.innerHTML = `<div class="card" style="color: var(--accent-red); padding: 1.5rem;">Failed to load policy dashboard: ${e.message}</div>`;
    }
}



