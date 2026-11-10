const API_BASE = window.location.port === "8000" 
    ? window.location.origin 
    : `${window.location.protocol}//${window.location.hostname || "127.0.0.1"}:8000`;

function getToken() { return localStorage.getItem("token"); }
function setToken(t) { localStorage.setItem("token", t); }
function clearToken() { localStorage.removeItem("token"); }
function isLoggedIn() { return !!getToken(); }

async function apiFetch(path, options = {}) {
    const headers = { ...(options.headers || {}) };
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
    if (response.status === 401) {
        clearToken();
    }
    return response;
}

function showToast(message, type = "success") {
    let container = document.getElementById("toastContainer");
    if (!container) {
        container = document.createElement("div");
        container.id = "toastContainer";
        document.body.appendChild(container);
    }
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    const icon = type === "success" ? "✓" : (type === "error" ? "✕" : "ℹ");
    toast.innerHTML = `<span style="font-weight:800; font-size:1.05rem;">${icon}</span> <span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
        if (toast.parentElement) toast.remove();
    }, 3000);
}

function renderNavLinks() {
    // Inject brand icon into any .brand link that doesn't have it
    document.querySelectorAll(".brand").forEach(brandEl => {
        if (!brandEl.querySelector(".brand-icon")) {
            brandEl.innerHTML = `<span class="brand-icon">TF</span> TaskFlow`;
        }
    });

    const nav = document.getElementById("navLinks");
    if (!nav) return;
    if (isLoggedIn()) {
        nav.innerHTML = `
            <a href="projects.html" class="nav-link">Projects</a>
            <button id="logoutBtn" class="btn btn-secondary btn-sm" style="margin-left:0.5rem;">Log out</button>
        `;
        document.getElementById("logoutBtn")?.addEventListener("click", () => {
            clearToken();
            showToast("Logged out successfully");
            setTimeout(() => { window.location.href = "login.html"; }, 300);
        });
    } else {
        nav.innerHTML = `
            <a href="login.html" class="nav-link">Log in</a>
            <a href="register.html" class="btn btn-primary btn-sm" style="margin-left:0.5rem;">Register</a>
        `;
    }
}

document.addEventListener("DOMContentLoaded", renderNavLinks);
