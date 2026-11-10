function escapeHtml(str) {
    if (!str) return "";
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

async function loadMembers() {
    const projectId = new URLSearchParams(window.location.search).get("id");
    if (!projectId) return;

    const response = await apiFetch(`/projects/${projectId}/members`);
    if (!response.ok) return;

    const members = await response.json();
    const listEl = document.getElementById("membersList");
    if (!listEl) return;

    if (!members || members.length === 0) {
        listEl.innerHTML = `<span style="color:var(--text-muted); font-size:0.875rem;">No members listed</span>`;
        return;
    }

    listEl.innerHTML = members.map(m => {
        const username = m.username || `User #${m.user_id}`;
        const initial = username.charAt(0).toUpperCase();
        return `
            <span class="member-chip">
                <span class="assignee-avatar">${initial}</span>
                <span>${escapeHtml(username)}</span>
                <span class="role-badge">${escapeHtml(m.role)}</span>
            </span>
        `;
    }).join("");
}

document.addEventListener("DOMContentLoaded", () => {
    loadMembers();

    const addMemberForm = document.getElementById("addMemberForm");
    if (addMemberForm) {
        addMemberForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const projectId = new URLSearchParams(window.location.search).get("id");
            const memberInput = document.getElementById("memberUsername");
            const username = memberInput.value.trim();
            const errorBanner = document.getElementById("errorBanner");

            if (!username) return;

            try {
                const response = await apiFetch(`/projects/${projectId}/members`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ username }),
                });

                if (response.ok) {
                    memberInput.value = "";
                    if (errorBanner) errorBanner.classList.add("hidden");
                    showToast(`✓ Invited @${username} to this project`);
                    loadMembers();
                } else {
                    const err = await response.json().catch(() => ({}));
                    if (errorBanner) {
                        errorBanner.textContent = err.detail || "Could not add member";
                        errorBanner.classList.remove("hidden");
                    }
                }
            } catch (err) {
                if (errorBanner) {
                    errorBanner.textContent = err.message || "Could not add member";
                    errorBanner.classList.remove("hidden");
                }
            }
        });
    }
});
