const API_BASE = '/api';

// State
let state = {
    token: localStorage.getItem('dashboard_token') || '',
    currentType: 'food', // food | nonfood
    currentView: 'orders', // orders | templates
    orders: [],
    orderDetails: {},
    templates: [],
    health: 'checking' // checking | ok | error
};

// DOM Elements
const els = {
    loginView: document.getElementById('login-view'),
    dashboardView: document.getElementById('dashboard-view'),
    tokenInput: document.getElementById('token-input'),
    loginBtn: document.getElementById('login-btn'),
    loginError: document.getElementById('login-error'),
    logoutBtn: document.getElementById('logout-btn'),

    healthDot: document.getElementById('health-dot'),
    healthText: document.getElementById('health-text'),

    typeToggles: document.querySelectorAll('.toggle-btn'),
    navItems: document.querySelectorAll('.nav-item'),

    ordersPanel: document.getElementById('orders-panel'),
    templatesPanel: document.getElementById('templates-panel'),
    ordersContainer: document.getElementById('orders-state-container'),
    templatesContainer: document.getElementById('templates-state-container'),

    refreshOrdersBtn: document.getElementById('refresh-orders-btn'),
    refreshTemplatesBtn: document.getElementById('refresh-templates-btn'),

    drawer: document.getElementById('order-drawer'),
    drawerOverlay: document.querySelector('.drawer-overlay'),
    closeDrawerBtn: document.querySelector('.close-drawer-btn'),
    drawerTitle: document.getElementById('drawer-title'),
    drawerBody: document.getElementById('drawer-body'),
};

// Initialization
function init() {
    bindEvents();
    if (state.token) {
        showDashboard();
    } else {
        showLogin();
    }
}

// Event Binding
function bindEvents() {
    els.loginBtn.addEventListener('click', handleLogin);
    els.tokenInput.addEventListener('keypress', e => {
        if (e.key === 'Enter') handleLogin();
    });
    els.logoutBtn.addEventListener('click', handleLogout);

    els.typeToggles.forEach(btn => {
        btn.addEventListener('click', (e) => {
            els.typeToggles.forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            state.currentType = e.target.dataset.type;
            refreshCurrentView();
        });
    });

    els.navItems.forEach(btn => {
        btn.addEventListener('click', (e) => {
            els.navItems.forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            state.currentView = e.target.dataset.view;
            updateViewVisibility();
            refreshCurrentView();
        });
    });

    els.refreshOrdersBtn.addEventListener('click', fetchOrders);
    els.refreshTemplatesBtn.addEventListener('click', fetchTemplates);

    els.closeDrawerBtn.addEventListener('click', closeDrawer);
    els.drawerOverlay.addEventListener('click', closeDrawer);
}

// API Helpers
async function apiFetch(endpoint) {
    const headers = {
        'Authorization': `Bearer ${state.token}`,
        'X-Dashboard-Token': state.token
    };

    try {
        const res = await fetch(`${API_BASE}${endpoint}`, { headers });
        if (res.status === 401 || res.status === 403) {
            handleLogout();
            throw new Error('Unauthorized');
        }
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        return await res.json();
    } catch (error) {
        console.error('API Fetch Error:', error);
        throw error;
    }
}

// Handlers
async function handleLogin() {
    const token = els.tokenInput.value.trim();
    if (!token) return;

    state.token = token;
    localStorage.setItem('dashboard_token', token);

    try {
        els.loginBtn.textContent = 'Äang kiá»ƒm tra...';
        els.loginBtn.disabled = true;

        await checkHealth();
        showDashboard();
    } catch (err) {
        els.loginError.classList.remove('hidden');
        localStorage.removeItem('dashboard_token');
        state.token = '';
    } finally {
        els.loginBtn.textContent = 'XÃ¡c nháº­n';
        els.loginBtn.disabled = false;
    }
}

function handleLogout() {
    state.token = '';
    localStorage.removeItem('dashboard_token');
    showLogin();
}

// View Management
function showLogin() {
    els.dashboardView.classList.add('hidden');
    els.dashboardView.classList.remove('active');
    els.loginView.classList.remove('hidden');
    els.loginView.classList.add('active');
    els.tokenInput.value = '';
    els.loginError.classList.add('hidden');
}

function showDashboard() {
    els.loginView.classList.add('hidden');
    els.loginView.classList.remove('active');
    els.dashboardView.classList.remove('hidden');
    els.dashboardView.classList.add('active');

    checkHealth().catch(() => {});
    if (!window.dashboardHealthTimer) {
        window.dashboardHealthTimer = setInterval(() => checkHealth().catch(() => {}), 30000);
    }

    refreshCurrentView();
}

function updateViewVisibility() {
    els.ordersPanel.classList.toggle('hidden', state.currentView !== 'orders');
    els.ordersPanel.classList.toggle('active', state.currentView === 'orders');

    els.templatesPanel.classList.toggle('hidden', state.currentView !== 'templates');
    els.templatesPanel.classList.toggle('active', state.currentView === 'templates');
}

function refreshCurrentView() {
    if (state.currentView === 'orders') fetchOrders();
    else if (state.currentView === 'templates') fetchTemplates();
}

// Data Fetching
async function checkHealth() {
    try {
        const data = await apiFetch('/health');
        updateHealthStatus(data.mongo_ok ? 'ok' : 'error', data.mongo_ok ? 'MongoDB hoáº¡t Ä‘á»™ng' : 'MongoDB lá»—i');
    } catch (err) {
        updateHealthStatus('error', 'Máº¥t káº¿t ná»‘i');
        throw err;
    }
}

function updateHealthStatus(status, text) {
    els.healthDot.className = `dot ${status}`;
    els.healthText.textContent = text;
}

function renderState(container, state, message = '') {
    if (state === 'loading') {
        container.innerHTML = `<div class="state-message"><div>Äang táº£i dá»¯ liá»‡u...</div></div>`;
    } else if (state === 'empty') {
        container.innerHTML = `<div class="state-message"><div>KhÃ´ng cÃ³ dá»¯ liá»‡u.</div></div>`;
    } else if (state === 'error') {
        container.innerHTML = `<div class="state-message"><div style="color: var(--danger)">Lá»—i: ${message}</div></div>`;
    }
}

async function fetchOrders() {
    renderState(els.ordersContainer, 'loading');
    try {
        const data = await apiFetch(`/orders?type=${state.currentType}&limit=30`);
        const orders = Array.isArray(data) ? data : (data.orders || []);
        state.orders = orders;
        renderOrders(orders);
    } catch (err) {
        renderState(els.ordersContainer, 'error', err.message);
    }
}

async function fetchTemplates() {
    renderState(els.templatesContainer, 'loading');
    try {
        const data = await apiFetch(`/templates?type=${state.currentType}`);
        const templates = Array.isArray(data) ? data : (data.templates || []);
        state.templates = templates;
        renderTemplates(templates);
    } catch (err) {
        renderState(els.templatesContainer, 'error', err.message);
    }
}

// Rendering
function renderOrders(orders) {
    if (!orders || orders.length === 0) {
        renderState(els.ordersContainer, 'empty');
        return;
    }

    let html = `
        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th>NgÃ y</th>
                        <th>Sá»‘ máº·t hÃ ng</th>
                        <th>Cáº­p nháº­t</th>
                    </tr>
                </thead>
                <tbody>
    `;

    orders.forEach(order => {
        const dateStr = order.date || order.created_at || 'N/A';
        const itemCount = order.item_count ?? 0;
        const updatedAt = order.updated_at || 'â€”';

        const safeDate = escapeHtml(String(dateStr));

        html += `
            <tr class="clickable" data-order-date="${safeDate}">
                <td><strong>${safeDate}</strong></td>
                <td>${itemCount}</td>
                <td>${escapeHtml(String(updatedAt))}</td>
            </tr>
        `;
    });

    html += `</tbody></table></div>`;
    els.ordersContainer.innerHTML = html;
    els.ordersContainer.querySelectorAll('[data-order-date]').forEach(row => {
        row.addEventListener('click', () => openOrderDrawer(row.dataset.orderDate));
    });
}

function renderTemplates(templates) {
    if (!templates || templates.length === 0) {
        renderState(els.templatesContainer, 'empty');
        return;
    }

    let html = `
        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th>TÃªn Máº«u</th>
                        <th>MÃ´ táº£</th>
                        <th>Sá»‘ lÆ°á»£ng máº·t hÃ ng</th>
                    </tr>
                </thead>
                <tbody>
    `;

    templates.forEach(tpl => {
        const name = escapeHtml(tpl.name || 'N/A');
        const updatedAt = escapeHtml(tpl.updated_at || 'â€”');
        const itemCount = tpl.item_count ?? 0;

        html += `
            <tr>
                <td><strong>${name}</strong></td>
                <td>${updatedAt}</td>
                <td>${itemCount}</td>
            </tr>
        `;
    });

    html += `</tbody></table></div>`;
    els.templatesContainer.innerHTML = html;
}

// Drawer
async function openOrderDrawer(orderDate) {
    const cacheKey = `${state.currentType}:${orderDate}`;
    let order = state.orderDetails[cacheKey];
    if (!order) {
        els.drawerTitle.textContent = `Äang táº£i Ä‘Æ¡n ${orderDate}`;
        els.drawerBody.innerHTML = '<div class="state-message"><div>Äang táº£i chi tiáº¿t...</div></div>';
        els.drawer.classList.add('open');
        try {
            const data = await apiFetch(`/orders/${encodeURIComponent(orderDate)}?type=${state.currentType}`);
            order = data.order;
            state.orderDetails[cacheKey] = order;
        } catch (err) {
            els.drawerBody.innerHTML = `<div class="state-message"><div style="color: var(--danger)">KhÃ´ng táº£i Ä‘Æ°á»£c chi tiáº¿t: ${escapeHtml(err.message)}</div></div>`;
            return;
        }
    }

    els.drawerTitle.textContent = `Chi tiáº¿t Ä‘Æ¡n hÃ ng`;

    const items = order.items || [];
    let itemsHtml = items.length > 0 ? `<div class="items-list">` : '<p class="detail-value">KhÃ´ng cÃ³ máº·t hÃ ng</p>';

    items.forEach(item => {
        const name = escapeHtml(item.name || item.product_name || item.code || 'N/A');
        const qty = item.qty ?? item.quantity ?? 0;
        const unit = item.unit || '';
        itemsHtml += `
            <div class="item-row">
                <span class="item-name">${name}</span>
                <span class="item-qty">${escapeHtml(String(qty))} ${escapeHtml(unit)}</span>
            </div>
        `;
    });

    if (items.length > 0) itemsHtml += `</div>`;

    const dateStr = order.date || order.created_at || 'N/A';
    const updatedAt = order.updated_at || 'â€”';

    els.drawerBody.innerHTML = `
        <div class="detail-section">
            <div class="detail-label">MÃ£ Ä‘Æ¡n</div>
            <div class="detail-value">${escapeHtml(orderDate)}</div>
        </div>
        <div class="detail-section">
            <div class="detail-label">Cáº­p nháº­t</div>
            <div class="detail-value">${escapeHtml(updatedAt)}</div>
        </div>
        <div class="detail-section">
            <div class="detail-label">Danh sÃ¡ch máº·t hÃ ng (${items.length})</div>
            ${itemsHtml}
        </div>
    `;

    els.drawer.classList.add('open');
}

function escapeHtml(value) {
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function closeDrawer() {
    els.drawer.classList.remove('open');
}

// Boot
document.addEventListener('DOMContentLoaded', init);
