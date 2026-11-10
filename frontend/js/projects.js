function escapeHtml(str) {
    if (!str) return "";
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

async function loadProjects() {
    const errorBanner = document.getElementById("errorBanner");
    try {
        const response = await apiFetch("/projects");
        if (!response.ok) throw new Error(`Server responded ${response.status}`);
        if (errorBanner) errorBanner.classList.add("hidden");
        renderProjects(await response.json());
    } catch (err) {
        if (errorBanner) {
            errorBanner.textContent = "Could not load projects.";
            errorBanner.classList.remove("hidden");
        }
    }
}

function renderProjects(projects) {
    const grid = document.getElementById("projectsGrid");
    if (!grid) return;

    if (!projects || projects.length === 0) {
        grid.innerHTML = `
            <div class="empty-state" style="grid-column: 1 / -1; background: var(--surface); border: 1px dashed var(--border); border-radius: var(--radius-lg); padding: 3rem 1.5rem;">
                <div style="font-size: 2.5rem; margin-bottom: 0.75rem;">📋</div>
                <h3 style="font-size: 1.15rem; margin-bottom: 0.35rem;">No projects yet</h3>
                <p style="color: var(--text-muted); max-width: 360px; margin: 0 auto 1.5rem;">
                    Projects help you group tasks, organize Kanban workflows, and collaborate with your team.
                </p>
                <button onclick="document.getElementById('newProjectBtn').click()" class="btn btn-primary">
                    Create your first project
                </button>
            </div>
        `;
        return;
    }

    grid.innerHTML = projects.map(p => `
        <a class="project-card" href="project.html?id=${p.id}">
            <div>
                <div class="project-card-header">
                    <div class="project-icon-badge">📁</div>
                    <h3>${escapeHtml(p.name)}</h3>
                </div>
                <p style="font-size:0.875rem; color:var(--text-muted); margin:0.35rem 0 0;">
                    TaskFlow Kanban Workspace
                </p>
            </div>
            <div class="project-card-meta">
                <span class="project-cta">Open Board &rarr;</span>
                <span style="font-weight:600; color:var(--text-dim);">ID #${p.id}</span>
            </div>
        </a>
    `).join("");
}

document.addEventListener("DOMContentLoaded", () => {
    if (!isLoggedIn()) {
        window.location.href = "login.html";
        return;
    }
    loadProjects();

    const newProjectBtn = document.getElementById("newProjectBtn");
    const newProjectForm = document.getElementById("newProjectForm");
    const errorBanner = document.getElementById("errorBanner");
    const projectNameInput = document.getElementById("projectName");

    if (newProjectBtn && newProjectForm) {
        newProjectBtn.addEventListener("click", () => {
            newProjectForm.classList.toggle("hidden");
            if (!newProjectForm.classList.contains("hidden")) {
                projectNameInput?.focus();
            }
        });

        newProjectForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const name = projectNameInput.value.trim();
            if (!name) return;

            try {
                const response = await apiFetch("/projects", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ name }),
                });

                if (response.ok) {
                    projectNameInput.value = "";
                    newProjectForm.classList.add("hidden");
                    if (errorBanner) errorBanner.classList.add("hidden");
                    showToast("✓ Project created successfully!");
                    loadProjects();
                } else {
                    const err = await response.json().catch(() => ({}));
                    if (errorBanner) {
                        errorBanner.textContent = err.detail || "Could not create project.";
                        errorBanner.classList.remove("hidden");
                    }
                }
            } catch (err) {
                if (errorBanner) {
                    errorBanner.textContent = err.message || "Could not create project.";
                    errorBanner.classList.remove("hidden");
                }
            }
        });
    }
});
