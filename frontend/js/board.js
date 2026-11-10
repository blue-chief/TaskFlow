function getProjectId() {
    return new URLSearchParams(window.location.search).get("id");
}

function escapeHtml(str) {
    if (!str) return "";
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

function buildQuery() {
    const params = new URLSearchParams();
    const search = document.getElementById("searchInput")?.value.trim();
    const status = document.getElementById("statusFilter")?.value;
    const priority = document.getElementById("priorityFilter")?.value;
    if (search) params.set("search", search);
    if (status) params.set("status", status);
    if (priority) params.set("priority", priority);
    return params.toString();
}

async function loadBoard() {
    const projectId = getProjectId();
    const errorBanner = document.getElementById("errorBanner");
    if (!projectId) {
        window.location.href = "projects.html";
        return;
    }

    try {
        const query = buildQuery();
        const tasksUrl = query ? `/tasks?project_id=${projectId}&${query}` : `/tasks?project_id=${projectId}`;
        const [projectRes, tasksRes] = await Promise.all([
            apiFetch(`/projects/${projectId}`),
            apiFetch(tasksUrl),
        ]);

        if (!projectRes.ok) {
            const err = await projectRes.json().catch(() => ({}));
            throw new Error(err.detail || "Could not load this project.");
        }
        if (!tasksRes.ok) {
            const err = await tasksRes.json().catch(() => ({}));
            throw new Error(err.detail || "Could not load tasks for this project.");
        }

        const project = await projectRes.json();
        document.getElementById("projectName").textContent = project.name;
        if (errorBanner) errorBanner.classList.add("hidden");

        renderBoard(await tasksRes.json());
    } catch (err) {
        if (errorBanner) {
            errorBanner.textContent = err.message || "Could not load this project.";
            errorBanner.classList.remove("hidden");
        }
    }
}

async function updateTaskStatus(taskId, newStatus, currentCard = null) {
    try {
        const res = await apiFetch(`/tasks/${taskId}/status`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ status: newStatus }),
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || "Could not update task status.");
        }
        const readableStatus = newStatus.replace("_", " ");
        showToast(`✓ Task moved to ${readableStatus}`);
        loadBoard();
    } catch (err) {
        showToast(err.message, "error");
        loadBoard();
    }
}

function renderBoard(tasks) {
    const columns = { todo: [], in_progress: [], completed: [], cancelled: [] };
    for (const task of tasks) {
        if (columns[task.status]) {
            columns[task.status].push(task);
        } else {
            columns.todo.push(task);
        }
    }

    // Update column counters and task cards
    for (const [status, list] of Object.entries(columns)) {
        const counterEl = document.getElementById(`count-${status}`);
        if (counterEl) counterEl.textContent = list.length;

        const col = document.getElementById(`col-${status}`);
        if (!col) continue;

        col.innerHTML = list.length
            ? list.map(t => {
                const assigneeInitial = t.assigned_to?.username ? t.assigned_to.username.charAt(0).toUpperCase() : "?";
                const assigneeName = t.assigned_to ? `@${escapeHtml(t.assigned_to.username)}` : "Unassigned";
                const dueDateFormatted = t.due_date ? new Date(t.due_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) : "";

                return `
                <div class="task-card" draggable="true" data-task-id="${t.id}" data-task-status="${t.status}">
                    <a href="task.html?id=${t.id}" class="task-card-link">
                        <p class="task-title">${escapeHtml(t.title)}</p>
                        <div class="task-badges">
                            <span class="priority-pill ${t.priority || 'low'}">
                                ● ${t.priority || 'low'}
                            </span>
                        </div>
                        <div class="task-footer">
                            <span class="assignee-chip">
                                <span class="assignee-avatar">${assigneeInitial}</span>
                                <span>${assigneeName}</span>
                            </span>
                            ${dueDateFormatted ? `<span title="Due date">📅 ${dueDateFormatted}</span>` : ""}
                        </div>
                    </a>
                    <div class="task-quick-move">
                        <select class="quick-status-select" data-task-id="${t.id}" title="Move status">
                            <option value="todo" ${t.status === 'todo' ? 'selected' : ''}>To do</option>
                            <option value="in_progress" ${t.status === 'in_progress' ? 'selected' : ''}>In progress</option>
                            <option value="completed" ${t.status === 'completed' ? 'selected' : ''}>Completed</option>
                            <option value="cancelled" ${t.status === 'cancelled' ? 'selected' : ''}>Cancelled</option>
                        </select>
                    </div>
                </div>
                `;
            }).join("")
            : `<div class="empty-state">No tasks here</div>`;
    }

    // Wire quick-status dropdowns
    document.querySelectorAll(".quick-status-select").forEach(select => {
        select.addEventListener("change", (e) => {
            const taskId = e.target.getAttribute("data-task-id");
            const newStatus = e.target.value;
            updateTaskStatus(taskId, newStatus);
        });
    });

    // Wire HTML5 Drag & Drop on cards and columns
    setupDragAndDrop();
}

function setupDragAndDrop() {
    const cards = document.querySelectorAll(".task-card");
    const columns = document.querySelectorAll(".column-tasks");

    cards.forEach(card => {
        card.addEventListener("dragstart", (e) => {
            card.classList.add("dragging");
            e.dataTransfer.effectAllowed = "move";
            e.dataTransfer.setData("text/plain", JSON.stringify({
                id: card.getAttribute("data-task-id"),
                status: card.getAttribute("data-task-status")
            }));
        });

        card.addEventListener("dragend", () => {
            card.classList.remove("dragging");
        });
    });

    columns.forEach(col => {
        col.addEventListener("dragover", (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = "move";
            col.classList.add("drag-over");
        });

        col.addEventListener("dragleave", (e) => {
            if (!col.contains(e.relatedTarget)) {
                col.classList.remove("drag-over");
            }
        });

        col.addEventListener("drop", (e) => {
            e.preventDefault();
            col.classList.remove("drag-over");
            const rawData = e.dataTransfer.getData("text/plain");
            if (!rawData) return;

            try {
                const { id, status: oldStatus } = JSON.parse(rawData);
                const targetStatus = col.getAttribute("data-status");
                if (targetStatus && targetStatus !== oldStatus) {
                    updateTaskStatus(id, targetStatus);
                }
            } catch (err) {
                console.error("Drop parsing error", err);
            }
        });
    });
}

document.addEventListener("DOMContentLoaded", () => {
    if (!isLoggedIn()) {
        window.location.href = "login.html";
        return;
    }

    loadBoard();

    // Search and filters
    const searchInput = document.getElementById("searchInput");
    const statusFilter = document.getElementById("statusFilter");
    const priorityFilter = document.getElementById("priorityFilter");

    let debounceTimer;
    if (searchInput) {
        searchInput.addEventListener("input", () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(loadBoard, 250);
        });
    }

    // Keyboard shortcut: '/' focuses search
    document.addEventListener("keydown", (e) => {
        if (e.key === "/" && document.activeElement !== searchInput && !["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)) {
            e.preventDefault();
            searchInput?.focus();
            searchInput?.select();
        }
    });

    if (statusFilter) statusFilter.addEventListener("change", loadBoard);
    if (priorityFilter) priorityFilter.addEventListener("change", loadBoard);

    // New task form toggle & submit
    const addTaskBtn = document.getElementById("addTaskBtn");
    const newTaskForm = document.getElementById("newTaskForm");
    const taskTitleInput = document.getElementById("taskTitle");
    const errorBanner = document.getElementById("errorBanner");

    if (addTaskBtn && newTaskForm) {
        addTaskBtn.addEventListener("click", () => {
            newTaskForm.classList.toggle("hidden");
            if (!newTaskForm.classList.contains("hidden")) {
                taskTitleInput?.focus();
            }
        });

        newTaskForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const projectId = getProjectId();
            const title = taskTitleInput.value.trim();
            if (!title) return;

            try {
                const res = await apiFetch(`/projects/${projectId}/tasks`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ title, status: "todo", priority: "low" }),
                });

                if (res.ok) {
                    taskTitleInput.value = "";
                    newTaskForm.classList.add("hidden");
                    if (errorBanner) errorBanner.classList.add("hidden");
                    showToast("✓ Task added to board");
                    loadBoard();
                } else {
                    const err = await res.json().catch(() => ({}));
                    if (errorBanner) {
                        errorBanner.textContent = err.detail || "Could not add task.";
                        errorBanner.classList.remove("hidden");
                    }
                }
            } catch (err) {
                if (errorBanner) {
                    errorBanner.textContent = err.message || "Could not add task.";
                    errorBanner.classList.remove("hidden");
                }
            }
        });
    }
});
