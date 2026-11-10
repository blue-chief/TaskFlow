function escapeHtml(str) {
    if (!str) return "";
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

function getTaskId() {
    return new URLSearchParams(window.location.search).get("id");
}

async function loadTask() {
    const taskId = getTaskId();
    const errorBanner = document.getElementById("errorBanner");
    if (!taskId) {
        window.location.href = "projects.html";
        return;
    }

    try {
        const response = await apiFetch(`/tasks/${taskId}`);
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || "Task not found");
        }
        const task = await response.json();
        if (errorBanner) errorBanner.classList.add("hidden");

        const backLink = document.getElementById("backToProject");
        if (backLink && task.project_id) {
            backLink.href = `project.html?id=${task.project_id}`;
        }

        renderTask(task);
    } catch (err) {
        if (errorBanner) {
            errorBanner.textContent = err.message || "Could not load task.";
            errorBanner.classList.remove("hidden");
        }
    }
}

function renderTask(task) {
    const formattedDate = task.due_date ? task.due_date.split("T")[0] : "";
    const taskDetail = document.getElementById("taskDetail");
    if (!taskDetail) return;

    taskDetail.innerHTML = `
        <div class="task-detail-header">
            <span class="status-badge ${task.status}">
                ● ${task.status.replace("_", " ")}
            </span>
            <span style="font-size:0.8rem; font-weight:700; color:var(--text-dim);">
                TASK #${task.id}
            </span>
        </div>

        <h1 style="margin: 0.5rem 0 0.75rem; font-size:1.65rem;">${escapeHtml(task.title)}</h1>
        <p style="color:var(--text-secondary); margin:0 0 1.25rem; font-size:0.95rem; line-height:1.6;">
            ${task.description ? escapeHtml(task.description) : "<span style='color:var(--text-dim); font-style:italic;'>No description provided.</span>"}
        </p>

        <div class="task-controls-grid">
            <div class="task-control-box">
                <label>Status</label>
                <select id="statusSelect">
                    ${["todo", "in_progress", "completed", "cancelled"].map(s =>
                        `<option value="${s}" ${s === task.status ? "selected" : ""}>${s.replace("_", " ")}</option>`
                    ).join("")}
                </select>
            </div>
            <div class="task-control-box">
                <label>Priority</label>
                <select id="prioritySelect">
                    ${["low", "medium", "high", "urgent"].map(p =>
                        `<option value="${p}" ${p === task.priority ? "selected" : ""}>${p}</option>`
                    ).join("")}
                </select>
            </div>
            <div class="task-control-box">
                <label>Assignee</label>
                <select id="assigneeSelect"><option value="">Loading collaborators...</option></select>
            </div>
            <div class="task-control-box">
                <label>Due Date</label>
                <input type="date" id="dueDateInput" value="${formattedDate}">
            </div>
        </div>
    `;

    // Status change listener
    document.getElementById("statusSelect").addEventListener("change", async (e) => {
        const res = await apiFetch(`/tasks/${task.id}/status`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ status: e.target.value }),
        });
        if (res.ok) {
            showToast(`✓ Status updated to ${e.target.value.replace("_", " ")}`);
            loadTask();
            loadActivity();
        }
    });

    // Priority change listener
    document.getElementById("prioritySelect").addEventListener("change", async (e) => {
        const res = await apiFetch(`/tasks/${task.id}/priority`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ priority: e.target.value }),
        });
        if (res.ok) {
            showToast(`✓ Priority updated to ${e.target.value}`);
            loadTask();
            loadActivity();
        }
    });

    // Due date listener
    document.getElementById("dueDateInput").addEventListener("change", async (e) => {
        const dueDate = e.target.value ? new Date(e.target.value).toISOString() : null;
        const res = await apiFetch(`/tasks/${task.id}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ due_date: dueDate }),
        });
        if (res.ok) {
            showToast("✓ Due date updated");
            loadTask();
            loadActivity();
        }
    });

    // Populate assignee dropdown
    populateAssignees(task);
}

async function populateAssignees(task) {
    const assigneeSelect = document.getElementById("assigneeSelect");
    if (!assigneeSelect || !task.project_id) return;

    try {
        const res = await apiFetch(`/projects/${task.project_id}/members`);
        if (!res.ok) return;

        const members = await res.json();
        assigneeSelect.innerHTML = `<option value="">Unassigned</option>` +
            members.map(m => {
                const isSelected = task.assigned_to_id === m.user_id ? "selected" : "";
                const name = m.username ? `@${m.username}` : `User #${m.user_id}`;
                return `<option value="${m.user_id}" ${isSelected}>${escapeHtml(name)}</option>`;
            }).join("");

        assigneeSelect.addEventListener("change", async (e) => {
            const assigneeId = e.target.value ? Number(e.target.value) : null;
            const url = assigneeId !== null
                ? `/tasks/${task.id}/assign?assignee_id=${assigneeId}`
                : `/tasks/${task.id}/assign`;
            const assignRes = await apiFetch(url, { method: "PATCH" });
            if (assignRes.ok) {
                showToast("✓ Assignee updated");
                loadTask();
                loadActivity();
            }
        });
    } catch (err) {
        console.error("Could not load project members for assignment", err);
    }
}

async function loadComments() {
    const taskId = getTaskId();
    const list = document.getElementById("commentsList");
    if (!taskId || !list) return;

    try {
        const res = await apiFetch(`/tasks/${taskId}/comments`);
        if (!res.ok) return;

        const comments = await res.json();
        if (!comments || comments.length === 0) {
            list.innerHTML = `<p class="empty-state" style="padding:1.5rem 0;">No comments yet. Start the conversation!</p>`;
            return;
        }

        list.innerHTML = comments.map(c => {
            const author = c.author?.username || `User #${c.user_id || 'unknown'}`;
            const initial = author.replace("@", "").charAt(0).toUpperCase();
            const dateStr = c.created_at ? new Date(c.created_at).toLocaleString() : "";
            const body = c.body || c.content || "";

            return `
                <div class="comment-card">
                    <div class="comment-header">
                        <span style="display:flex; align-items:center; gap:0.45rem;">
                            <span class="assignee-avatar">${initial}</span>
                            <span class="comment-author">${escapeHtml(author)}</span>
                        </span>
                        <span class="comment-date">${escapeHtml(dateStr)}</span>
                    </div>
                    <p class="comment-body">${escapeHtml(body)}</p>
                </div>
            `;
        }).join("");
    } catch (err) {
        console.error("Could not load comments", err);
    }
}

async function loadActivity() {
    const taskId = getTaskId();
    const list = document.getElementById("activityList");
    if (!taskId || !list) return;

    try {
        const res = await apiFetch(`/tasks/${taskId}/activity`);
        if (!res.ok) return;

        const activities = await res.json();
        if (!activities || activities.length === 0) {
            list.innerHTML = `<p class="empty-state" style="padding:1.5rem 0;">No activity recorded yet.</p>`;
            return;
        }

        list.innerHTML = activities.map(a => {
            const dateStr = a.created_at ? new Date(a.created_at).toLocaleString() : "";
            const author = a.user?.username || (a.user_id ? `User #${a.user_id}` : "System");
            return `
                <div class="activity-item">
                    <span class="activity-icon">📌</span>
                    <div>
                        <strong>${escapeHtml(author)}</strong> ${escapeHtml(a.action || "updated this task")}
                        <span style="color:var(--text-dim); font-size:0.75rem; margin-left:0.5rem;">${escapeHtml(dateStr)}</span>
                    </div>
                </div>
            `;
        }).join("");
    } catch (err) {
        console.error("Could not load activity", err);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    if (!isLoggedIn()) {
        window.location.href = "login.html";
        return;
    }

    loadTask();
    loadComments();
    loadActivity();

    const commentForm = document.getElementById("commentForm");
    const commentInput = document.getElementById("commentContent");

    if (commentForm && commentInput) {
        commentForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const taskId = getTaskId();
            const content = commentInput.value.trim();
            if (!content) return;

            const res = await apiFetch(`/tasks/${taskId}/comments`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ body: content }),
            });

            if (res.ok) {
                commentInput.value = "";
                showToast("✓ Comment posted");
                loadComments();
                loadActivity();
            }
        });
    }
});
