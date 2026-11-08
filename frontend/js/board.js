function getProjectId() {
    return new URLSearchParams(window.location.search).get("id");
}

function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

function buildQuery() {
    const params = new URLSearchParams();
    const search = document.getElementById("searchInput").value.trim();
    const status = document.getElementById("statusFilter").value;
    const priority = document.getElementById("priorityFilter").value;
    if (search) params.set("search", search);
    if (status) params.set("status", status);
    if (priority) params.set("priority", priority);
    return params;
}

async function loadBoard() {
    const projectId = getProjectId();
    const errorBanner = document.getElementById("errorBanner");
    try {
        const [projectRes, tasksRes] = await Promise.all([
            apiFetch(`/projects/${projectId}`),
            apiFetch(`/tasks?project_id=${projectId}&${buildQuery()}`),
        ]);
        if (!projectRes.ok || !tasksRes.ok) throw new Error("Server error");

        const project = await projectRes.json();
        document.getElementById("projectName").textContent = project.name;

        renderBoard(await tasksRes.json());
    } catch (err) {
        errorBanner.textContent = "Could not load this project.";
        errorBanner.classList.remove("hidden");
    }
}

function renderBoard(tasks) {
    const columns = { todo: [], in_progress: [], completed: [], cancelled: [] };
    for (const task of tasks) columns[task.status]?.push(task);

    for (const [status, list] of Object.entries(columns)) {
        const col = document.getElementById(`col-${status}`);
        col.innerHTML = list.length
            ? list.map(t => `
                <a class="task-card" href="task.html?id=${t.id}">
                    <p class="task-title"><span class="priority-dot ${t.priority}"></span>${escapeHtml(t.title)}</p>
                    <p class="task-meta">${t.assigned_to ? "@" + escapeHtml(t.assigned_to.username) : "Unassigned"}${t.due_date ? " · " + t.due_date : ""}</p>
                </a>
            `).join("")
            : `<p class="empty-state">No tasks</p>`;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    if (!isLoggedIn()) { window.location.href = "login.html"; return; }
    loadBoard();

    document.getElementById("taskFilters").addEventListener("submit", (e) => e.preventDefault());
    document.getElementById("searchInput").addEventListener("input", debounce(loadBoard, 300));
    document.getElementById("statusFilter").addEventListener("change", loadBoard);
    document.getElementById("priorityFilter").addEventListener("change", loadBoard);

    document.getElementById("addTaskBtn").addEventListener("click", () => {
        document.getElementById("newTaskForm").classList.toggle("hidden");
    });

    document.getElementById("newTaskForm").addEventListener("submit", async (e) => {
        e.preventDefault();
        const title = document.getElementById("taskTitle").value.trim();
        const response = await apiFetch("/tasks", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ title, project_id: parseInt(getProjectId(), 10) }),
        });
        if (response.ok) {
            document.getElementById("taskTitle").value = "";
            loadBoard();
        }
    });
});

function debounce(fn, delay) {
    let timer;
    return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), delay); };
}

// board.js — add state + button
let currentSkip = 0;
const PAGE_SIZE = 50;

async function loadMoreTasks() {
    currentSkip += PAGE_SIZE;
    const response = await apiFetch(`/tasks?project_id=${getProjectId()}&skip=${currentSkip}&limit=${PAGE_SIZE}&${buildQuery()}`);
    const more = await response.json();
    appendToColumns(more); // same grouping logic as renderBoard(), appending instead of replacing
}