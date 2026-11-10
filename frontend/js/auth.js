function showError(message) {
    const errorBanner = document.getElementById("errorBanner");
    if (!errorBanner) return;
    errorBanner.textContent = message;
    errorBanner.classList.remove("hidden");
}

function escapeHtml(str) {
    if (!str) return "";
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

async function verifyToken(token) {
    const result = document.getElementById("verifyResult");
    const manualSection = document.getElementById("manualTokenSection");
    if (!result) return;

    result.innerHTML = `<span style="color:var(--text-dim);">Contacting server to verify token...</span>`;

    try {
        const response = await fetch(`${API_BASE}/auth/verify-email`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ token: token.trim() }),
        });

        const data = await response.json().catch(() => ({}));

        if (response.ok) {
            result.innerHTML = `
                <div style="background: #ECFDF5; border: 1px solid #A7F3D0; color: #047857; border-radius: var(--radius-md); padding: 1rem; margin-top: 1rem;">
                    <strong>Success!</strong> Email verified. You can now log in to TaskFlow.
                </div>
                <p style="margin-top: 1.5rem;">
                    <a href="login.html" class="btn btn-primary" style="display:inline-block; text-decoration:none;">Go to Log in</a>
                </p>
            `;
            if (manualSection) manualSection.classList.add("hidden");
        } else {
            result.innerHTML = `
                <div style="background: #FFF1F2; border: 1px solid #FECDD3; color: #BE123C; border-radius: var(--radius-md); padding: 1rem; margin-top: 1rem;">
                    <strong>Verification Failed:</strong> ${escapeHtml(data.detail || "This link is invalid or has expired.")}
                </div>
                <p style="margin-top: 1rem;">
                    <a href="resend-verification.html" style="color:var(--accent); text-decoration:none; font-weight:600;">Request a new verification email &rarr;</a>
                </p>
            `;
            if (manualSection) manualSection.classList.remove("hidden");
        }
    } catch (err) {
        result.innerHTML = `
            <div style="background: #FFF1F2; border: 1px solid #FECDD3; color: #BE123C; border-radius: var(--radius-md); padding: 1rem; margin-top: 1rem;">
                <strong>Connection Error:</strong> Could not connect to the backend server at <code>${API_BASE}</code>.<br>
                Please ensure the FastAPI server is running on port 8000.
            </div>
        `;
        if (manualSection) manualSection.classList.remove("hidden");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    // 1. Email Verification Page
    const verifyResult = document.getElementById("verifyResult");
    if (verifyResult) {
        const token = new URLSearchParams(window.location.search).get("token");
        if (token) {
            verifyToken(token);
        } else {
            verifyResult.innerHTML = `
                <div style="background: rgba(242,184,75,0.15); border: 1px solid rgba(242,184,75,0.4); color: var(--progress); border-radius: 8px; padding: 1rem;">
                    No verification token was detected in the URL.
                </div>
            `;
            const manualSection = document.getElementById("manualTokenSection");
            if (manualSection) manualSection.classList.remove("hidden");
        }

        const manualForm = document.getElementById("manualVerifyForm");
        if (manualForm) {
            manualForm.addEventListener("submit", (e) => {
                e.preventDefault();
                const manualToken = document.getElementById("manualTokenInput").value.trim();
                if (manualToken) verifyToken(manualToken);
            });
        }
    }

    // 2. Login Form
    const loginForm = document.getElementById("loginForm");
    if (loginForm) {
        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const username = document.getElementById("username").value.trim();
            const password = document.getElementById("password").value;

            try {
                const response = await fetch(`${API_BASE}/auth/login`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ username, password }),
                });
                if (!response.ok) {
                    const err = await response.json().catch(() => ({}));
                    if (err.detail?.code === "email_not_verified") {
                        showError(`${err.detail.message} `);
                        const errorBanner = document.getElementById("errorBanner");
                        if (errorBanner) {
                            const resendLink = document.createElement("a");
                            resendLink.href = `resend-verification.html?email=${encodeURIComponent(username)}`;
                            resendLink.textContent = "Resend verification email";
                            resendLink.style.display = "block";
                            resendLink.style.marginTop = "0.5rem";
                            errorBanner.appendChild(resendLink);
                        }
                        return;
                    }
                    throw new Error(err.detail || "Login failed");
                }
                const data = await response.json();
                setToken(data.access_token);
                window.location.href = "projects.html";
            } catch (err) {
                showError(err.message);
            }
        });
    }

    // 3. Register Form
    const registerForm = document.getElementById("registerForm");
    if (registerForm) {
        registerForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const username = document.getElementById("username").value.trim();
            const email = document.getElementById("email").value.trim();
            const password = document.getElementById("password").value;

            try {
                const response = await fetch(`${API_BASE}/users/register`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ username, email, password }),
                });
                if (!response.ok) {
                    const err = await response.json().catch(() => ({}));
                    const msg = typeof err.detail === "string" ? err.detail : (err.detail?.[0]?.msg || "Registration failed");
                    throw new Error(msg);
                }
                window.location.href = `check-email.html?email=${encodeURIComponent(email)}`;
            } catch (err) {
                showError(err.message);
            }
        });
    }

    // 4. Resend Verification Form
    const resendForm = document.getElementById("resendForm");
    if (resendForm) {
        const prefill = new URLSearchParams(window.location.search).get("email");
        if (prefill) document.getElementById("resendEmail").value = prefill;

        resendForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const email = document.getElementById("resendEmail").value.trim();
            await fetch(`${API_BASE}/auth/resend-verification`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email }),
            });
            document.getElementById("resendResult").textContent =
                "If that email is registered and unverified, a new link is on its way.";
        });
    }

    // 5. Forgot Password Form
    const forgotForm = document.getElementById("forgotForm");
    if (forgotForm) {
        forgotForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const email = document.getElementById("forgotEmail").value.trim();
            await fetch(`${API_BASE}/auth/forgot-password`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email }),
            });
            document.getElementById("forgotResult").textContent =
                "If that email is registered, we've sent password reset instructions.";
        });
    }

    // 6. Reset Password Form
    const resetForm = document.getElementById("resetForm");
    if (resetForm) {
        resetForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const token = new URLSearchParams(window.location.search).get("token");
            const newPassword = document.getElementById("newPassword").value;

            const response = await fetch(`${API_BASE}/auth/reset-password`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ token, new_password: newPassword }),
            });
            if (response.ok) {
                window.location.href = "login.html";
            } else {
                const err = await response.json().catch(() => ({}));
                showError(err.detail || "This link is invalid or has expired.");
            }
        });
    }
});
