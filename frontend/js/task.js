function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

function getTaskId() {
    return new URLSearchParams(window.location.search).get("id");
}

async function loadTask() {
    const errorBanner = document.getElementById("errorBanner");
    try {
        const response = await apiFetch(`/tasks/${getTaskId()}`);
        if (!response.ok) throw new Error("Task not found");
        renderTask(await response.json());
    } catch (err) {
        errorBanner.textContent = err.message;
        errorBanner.classList.remove("hidden");
    }
}

function renderTask(task) {
    document.getElementById("taskDetail").innerHTML = `
        <span class="status-badge ${task.status}">${task.status.replace("_", " ")}</span>
        <h1>${escapeHtml(task.title)}</h1>
        ${task.description ? `<p>${escapeHtml(task.description)}</p>` : ""}
        <div class="task-controls">
            <select id="statusSelect">
                ${["todo", "in_progress", "completed", "cancelled"].map(s =>
                    `<option value="${s}" ${s === task.status ? "selected" : ""}>${s.replace("_", " ")}</option>`
                ).join("")}
            </select>
            <select id="prioritySelect">
                ${["low", "medium", "high", "urgent"].map(p =>
                    `<option value="${p}" ${p === task.priority ? "selected" : ""}>${p}</option>`
                ).join("")}
            </select>
            <select id="assigneeSelect"><option value="">Unassigned</option></select>
            <input type="date" id="dueDateInput" value="${task.due_date || ""}">
        </div>
    `;

    document.getElementById("statusSelect").addEventListener("change", async (e) => {
        await apiFetch(`/tasks/${task.id}/status`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ status: e.target.value }),
        });
        loadTask();
    });

    document.getElementById("prioritySelect").addEventListener("change", async (e) => {
        await apiFetch(`/tasks/${task.id}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ priority: e.target.value }),
        });
        loadTask();
    });

    document.getElementById("dueDateInput").addEventListener("change", async (e) => {
        await apiFetch(`/tasks/${task.id}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ due_date: e.target.value }),
        });
        loadTask();
    });
}


document.addEventListener("DOMContentLoaded", () => {
    if (!isLoggedIn()) { window.location.href = "login.html"; return; }
    loadTask();
});

async function loadComments() {
    const response = await apiFetch(`/tasks/${getTaskId()}/comments`);
    if (!response.ok) return;
    const comments = await response.json();
    document.getElementById("commentsList").innerHTML = comments.length
        ? comments.map(c => `
            <div class="comment-card">
                <p class="comment-meta">${escapeHtml(c.author.username)} · ${new Date(c.created_at).toLocaleString()}</p>
                <p>${escapeHtml(c.content)}</p>
            </div>
        `).join("")
        : `<p class="empty-state">No comments yet.</p>`;
}

document.getElementById("commentForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const content = document.getElementById("commentContent").value.trim();
    const response = await apiFetch(`/tasks/${getTaskId()}/comments`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content }),
    });
    if (response.ok) {
        document.getElementById("commentContent").value = "";
        loadComments();
    }
});

document.addEventListener("DOMContentLoaded", loadComments);


async function loadActivity() {
    const response = await apiFetch(`/tasks/${getTaskId()}/activity`);
    if (!response.ok) return;
    const activities = await response.json();
    document.getElementById("activityList").innerHTML = activities.length
        ? activities.map(a => `
            <div class="activity-item">${escapeHtml(a.user.username)} ${escapeHtml(a.description)} · ${new Date(a.created_at).toLocaleString()}</div>
        `).join("")
        : `<p class="empty-state">No activity yet.</p>`;
}

document.addEventListener("DOMContentLoaded", loadActivity);

// after renderTask() builds the DOM, populate and wire the assignee dropdown
// using the project's member list (same endpoint Day 71 already uses):
async function populateAssigneeOptions(task) {
    const response = await apiFetch(`/projects/${task.project_id}/members`);
    if (!response.ok) return;
    const members = await response.json();
    const select = document.getElementById("assigneeSelect");
    select.innerHTML = `<option value="">Unassigned</option>` + members.map(m =>
        `<option value="${m.id}" ${task.assigned_to?.id === m.id ? "selected" : ""}>${escapeHtml(m.username)}</option>`
    ).join("");

    select.addEventListener("change", async (e) => {
        if (!e.target.value) return; // unassigning isn't wired server-side in this roadmap — assign-only
        await apiFetch(`/tasks/${task.id}/assign?assignee_id=${e.target.value}`, { method: "PATCH" });
        loadTask();
    });
}
