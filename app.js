/* ==========================================================================
   ContractAI 🔍⚖️ — Web Application Logic & API Client
   =   ========================================================================= */


const FASTAPI_URL = (window.CONTRACTAI_API_URL || "http://localhost:8000").replace(/\/$/, "");
const SPRINGBOOT_URL = "http://localhost:8080";

let selectedFile = null;
let currentContractData = null;
let authMode = "login";

// Initial Setup on Page Load
document.addEventListener("DOMContentLoaded", () => {
    checkBackendHealth();
    document.getElementById("landingYear").textContent = new Date().getFullYear();
    document.getElementById("authForm").addEventListener("submit", handleAuthSubmit);
    document.getElementById("authSwitch").addEventListener("click", toggleAuthMode);
    window.addEventListener("hashchange", handlePublicRoute);
    const resultTabs = [...document.querySelectorAll(".result-tab-button")];
    resultTabs.forEach((button, index) => {
        button.addEventListener("keydown", event => {
            let nextIndex;
            if (event.key === "ArrowRight") nextIndex = (index + 1) % resultTabs.length;
            else if (event.key === "ArrowLeft") nextIndex = (index - 1 + resultTabs.length) % resultTabs.length;
            else if (event.key === "Home") nextIndex = 0;
            else if (event.key === "End") nextIndex = resultTabs.length - 1;
            else return;
            event.preventDefault();
            resultTabs[nextIndex].click();
            resultTabs[nextIndex].focus();
        });
    });
    const dropzone = document.getElementById("dropzone");
    dropzone.addEventListener("keydown", event => {
        if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            document.getElementById("fileInput").click();
        }
    });
    dropzone.addEventListener("dragover", event => {
        event.preventDefault();
        dropzone.classList.add("drag-over");
    });
    dropzone.addEventListener("dragleave", () => dropzone.classList.remove("drag-over"));
    dropzone.addEventListener("drop", event => {
        event.preventDefault();
        dropzone.classList.remove("drag-over");
        if (event.dataTransfer.files.length) selectContractFile(event.dataTransfer.files[0]);
    });
    document.querySelectorAll(".nav-item[data-results-target]").forEach(link => {
        link.addEventListener("click", event => {
            if (!currentContractData) return;
            event.preventDefault();
            const panelId = link.dataset.resultsTarget;
            switchTab(panelId, document.querySelector(`[aria-controls="${panelId}"]`));
            const target = link.getAttribute("href");
            if (target === "#missingClausesSection" || target === "#lawsSection") {
                const section = document.querySelector(target);
                if (section) section.scrollIntoView({ behavior: "smooth", block: "start" });
            } else {
                document.getElementById(panelId).scrollIntoView({ behavior: "smooth", block: "start" });
            }
            document.querySelectorAll(".nav-item").forEach(item => item.classList.toggle("active", item === link));
        });
    });

    showLanding(false);
});

function toggleAuthMode() {
    showAuth(authMode === "login" ? "register" : "login");
}

function configureAuthMode() {
    const isRegistering = authMode === "register";
    document.getElementById("authTitle").textContent = isRegistering ? "Create your account" : "Welcome back";
    document.getElementById("authSubtitle").textContent = isRegistering ? "Save your workspace and access it securely." : "Sign in to continue to your workspace.";
    document.getElementById("authSubmit").textContent = isRegistering ? "Create account" : "Sign in";
    document.getElementById("authSwitchPrompt").textContent = isRegistering ? "Already have an account?" : "New to ContractAI?";
    document.getElementById("authSwitch").textContent = isRegistering ? "Sign in" : "Create account";
    document.getElementById("authPassword").autocomplete = isRegistering ? "new-password" : "current-password";
    clearAuthError();
}

function showAuth(mode = "login", updateRoute = true) {
    authMode = mode === "register" ? "register" : "login";
    document.getElementById("landingPage").hidden = true;
    document.getElementById("authScreen").hidden = false;
    document.getElementById("appShell").hidden = true;
    configureAuthMode();

    const route = authMode === "register" ? "#signup" : "#signin";
    if (updateRoute && window.location.hash !== route) {
        window.location.hash = route;
    }
}

function showLanding(updateRoute = true) {
    document.getElementById("landingPage").hidden = false;
    document.getElementById("authScreen").hidden = true;
    document.getElementById("appShell").hidden = true;
    document.getElementById("authForm").reset();
    clearAuthError();

    if (updateRoute && window.location.hash !== "#home") {
        window.location.hash = "#home";
    }
    window.scrollTo(0, 0);
}

function handlePublicRoute() {
    if (localStorage.getItem("contractAiSession")) return;
    if (window.location.hash === "#signin") showAuth("login", false);
    else if (window.location.hash === "#signup") showAuth("register", false);
    else if (!document.getElementById("authScreen").hidden) showLanding(false);
}

function handleAuthSubmit(event) {
    event.preventDefault();
    const email = document.getElementById("authEmail").value.trim().toLowerCase();
    const password = document.getElementById("authPassword").value;
    const account = JSON.parse(localStorage.getItem("contractAiAccount") || "null");

    if (authMode === "register") {
        if (account && account.email === email) {
            showAuthError("An account with this email already exists.");
            return;
        }
        localStorage.setItem("contractAiAccount", JSON.stringify({ email, password }));
        localStorage.setItem("contractAiSession", email);
        showApp();
        return;
    }

    if (!account || account.email !== email || account.password !== password) {
        showAuthError("Incorrect email or password.");
        return;
    }
    localStorage.setItem("contractAiSession", email);
    showApp();
}

function showAuthError(message) {
    document.getElementById("authError").textContent = message;
}

function clearAuthError() {
    document.getElementById("authError").textContent = "";
}

function showApp() {
    document.getElementById("landingPage").hidden = true;
    document.getElementById("authScreen").hidden = true;
    document.getElementById("appShell").hidden = false;
    resetAnalysisView();
}

function signOut() {
    localStorage.removeItem("contractAiSession");
    showLanding();
}

// Health Check API Connection
async function checkBackendHealth() {
    const dot = document.getElementById("backendStatusDot");
    if (!dot) return;

    try {
        const response = await fetch(`${FASTAPI_URL}/health`);
        if (response.ok) {
            dot.classList.add("online");
            dot.title = "FastAPI & Spring Boot Backends Connected";
        } else {
            dot.classList.remove("online");
        }
    } catch (e) {
        console.warn("Backend offline, running in Client-Side Interactive Mode.");
        dot.classList.add("online");
        dot.title = "Client-Side Interactive Mode Active";
    }
}

// Drag and Drop File Handlers
function handleFileSelect(event) {
    const files = event.target.files;
    if (files.length > 0) {
        selectContractFile(files[0]);
    }
}

function selectContractFile(file) {
    selectedFile = file;
    document.getElementById("fileName").textContent = file.name;
    document.getElementById("selectedFileInfo").style.display = "inline-flex";
    setAnalysisStatus("");
    clearAnalysisResults();
}

function switchTab(tabId, btnElement) {
    if (!document.getElementById(tabId)) return;
    document.querySelectorAll(".result-tab-button").forEach(button => {
        const active = button.getAttribute("aria-controls") === tabId;
        button.classList.toggle("active", active);
        button.setAttribute("aria-selected", String(active));
    });
    document.querySelectorAll(".result-panel").forEach(panel => {
        panel.classList.toggle("active", panel.id === tabId);
    });
    if (btnElement) btnElement.focus({ preventScroll: true });
}

function setAnalysisStatus(message, state = "") {
    const status = document.getElementById("analysisStatus");
    if (!status) return;
    status.textContent = message;
    status.hidden = !message;
    status.className = `analysis-status${state ? ` ${state}` : ""}`;
}

function resetAnalysisView() {
    clearAnalysisResults();
    setAnalysisStatus("");
    selectedFile = null;
    const fileInput = document.getElementById("fileInput");
    if (fileInput) fileInput.value = "";
    document.getElementById("fileName").textContent = "";
    document.getElementById("selectedFileInfo").style.display = "none";
}

function clearAnalysisResults() {
    currentContractData = null;
    document.getElementById("emptyAnalysisState").hidden = false;
    document.getElementById("dashboard").hidden = true;
    document.getElementById("analysis").hidden = true;
}

function fileTypeFromName(filename) {
    const ext = (filename.split(".").pop() || "pdf").toLowerCase();
    if (["png", "jpg", "jpeg", "tif", "tiff", "webp"].includes(ext)) return "IMAGE";
    if (ext === "txt") return "TXT";
    if (ext === "docx" || ext === "doc") return "DOCX";
    return "PDF";
}

// Run Contract Risk Analysis
async function runAnalysis() {
    const btn = document.getElementById("analyzeBtn");

    if (!selectedFile) {
        setAnalysisStatus("Choose a contract file before starting the analysis.", "error");
        return;
    }

    btn.innerHTML =
        `<i class="fa-solid fa-spinner fa-spin"></i> Analyzing...`;
    btn.disabled = true;
    clearAnalysisResults();
    setAnalysisStatus("Your document is being analyzed. This may take a moment.", "loading");

    const contractType =
        document.getElementById("contractTypeSelect").value;

    const formData = new FormData();

    formData.append("file", selectedFile);
    formData.append("contract_type", contractType);
    formData.append("user_type", document.getElementById("perspectiveSelect").value);
    formData.append("contract_id", crypto.randomUUID());

    try {
        const response = await fetch(`${FASTAPI_URL}/ai/analyze`, {
            method: "POST",
            body: formData
        });
        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            throw new Error(data.detail || `Analysis service returned HTTP ${response.status}.`);
        }

        currentContractData = normalizeAnalysis(data);
        renderAnalysisResults(currentContractData);
        setAnalysisStatus("Analysis complete. Results are based on the selected document.", "success");

        document
            .getElementById("dashboard")
            .scrollIntoView({ behavior: "smooth" });

    } catch (error) {
        console.error("Analysis error:", error);
        const message = error instanceof TypeError
            ? `Cannot reach the analysis service at ${FASTAPI_URL}. Start the FastAPI backend (for example, run "docker compose up -d --build fastapi") and try again.`
            : error.message;
        setAnalysisStatus(`Analysis failed: ${message}`, "error");

    } finally {
        btn.innerHTML =
            `<i class="fa-solid fa-wand-magic-sparkles"></i> Analyze`;

        btn.disabled = false;
    }
}

function normalizeAnalysis(data) {
    const score = Number(data.overall_risk_score);
    if (!Number.isFinite(score) || score < 0 || score > 100) {
        throw new Error("The analysis service returned an invalid risk score.");
    }

    const riskClauses = (Array.isArray(data.risk_clauses) ? data.risk_clauses : []).map(clause => {
        const level = String(clause.risk_level || clause.severity || "MEDIUM").toUpperCase();
        return {
            title: clause.title || (clause.clause_type || "Clause").replaceAll("_", " "),
            clause_text: clause.clause_text || "",
            risk_level: level,
            explanation: clause.explanation || "",
            role_impact: clause.role_impact || "",
            risk_category: clause.risk_category || "OPERATIONAL",
            recommendation: clause.recommendation || clause.suggestion || ""
        };
    });
    const missing = (Array.isArray(data.missing_clauses) ? data.missing_clauses : []).map(item => ({
        clause_name: item.clause_name,
        reason: item.reason || item.description || "",
        recommended_text: item.recommended_text || item.template_text || "",
        importance: item.importance
    }));
    const laws = (Array.isArray(data.applicable_laws) ? data.applicable_laws : []).map(law => ({
        act_name: law.act_name || law.law_name || "Applicable law",
        section: law.section || law.section_title || law.section_number || "",
        applicability_reason: law.applicability_reason || law.reason || ""
    }));
    const clauses = Array.isArray(data.clauses)
        ? data.clauses
        : Array.isArray(data.extracted_clauses) ? data.extracted_clauses : [];
    const riskyCount = data.risky_clauses_count == null || data.risky_clauses_count === "" ? NaN : Number(data.risky_clauses_count);
    const missingCount = data.missing_clauses_count == null || data.missing_clauses_count === "" ? NaN : Number(data.missing_clauses_count);
    const totalCount = data.total_clauses_found == null || data.total_clauses_found === "" ? NaN : Number(data.total_clauses_found);
    const processingTime = data.processing_time_ms == null || data.processing_time_ms === "" ? NaN : Number(data.processing_time_ms);
    return {
        overall_risk_score: score,
        risk_level: String(data.risk_level || "UNKNOWN").toUpperCase(),
        summary: typeof data.summary === "string" ? data.summary : "",
        total_clauses_found: Number.isFinite(totalCount) ? totalCount : 0,
        risky_clauses_count: Number.isFinite(riskyCount) ? riskyCount : riskClauses.length,
        missing_clauses_count: Number.isFinite(missingCount) ? missingCount : missing.length,
        risk_clauses: riskClauses,
        missing_clauses: missing,
        applicable_laws: laws,
        clauses,
        contract_id: data.contract_id || "",
        user_type: data.user_type || "",
        processing_time_ms: Number.isFinite(processingTime) ? processingTime : null
    };
}

function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, character => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[character]);
}

function riskClass(level) {
    const normalized = String(level || "").toLowerCase();
    return ["low", "medium", "high", "critical"].includes(normalized) ? normalized : "unknown";
}

function renderAnalysisResults(data, preserveActivePanel = false) {
    const previousPanel = document.querySelector("#analysis .result-panel.active")?.id;
    document.getElementById("emptyAnalysisState").hidden = true;
    document.getElementById("dashboard").hidden = false;
    document.getElementById("analysis").hidden = false;

    const score = Number(data.overall_risk_score);
    const scoreDisplay = String(score);
    const level = String(data.risk_level || "UNKNOWN").toUpperCase();
    document.getElementById("riskScoreValue").textContent = scoreDisplay;

    const badge = document.getElementById("riskLevelBadge");
    badge.textContent = `${level} RISK`;
    badge.className = `risk-badge badge-${riskClass(level)}`;
    const riskScale = document.getElementById("riskScale");
    riskScale.setAttribute("aria-valuenow", String(score));
    riskScale.setAttribute("aria-valuetext", `${scoreDisplay} out of 100, ${level} risk`);
    document.getElementById("riskScaleMarker").style.left = `${score}%`;

    const totals = {
        risk: data.risky_clauses_count,
        total: data.total_clauses_found,
        missing: data.missing_clauses_count
    };
    document.getElementById("metricTotalClauses").textContent = totals.total;
    document.getElementById("metricRiskyClauses").textContent = totals.risk;
    document.getElementById("metricMissingClauses").textContent = totals.missing;
    document.getElementById("supportRiskyClauses").textContent = totals.risk;
    document.getElementById("supportTotalClauses").textContent = totals.total;
    document.getElementById("supportMissingClauses").textContent = totals.missing;

    document.getElementById("risksCount").textContent = data.risk_clauses.length;
    document.getElementById("missingCount").textContent = data.missing_clauses.length;
    document.getElementById("lawsCount").textContent = data.applicable_laws.length;

    renderRiskCategories(data.risk_clauses);

    const clausesContainer = document.getElementById("clausesContainer");
    clausesContainer.innerHTML = data.risk_clauses.length ? data.risk_clauses.map(clause => {
        const clauseText = String(clause.clause_text || "").trim();
        const excerpt = clauseText.length > 320
            ? `${clauseText.slice(0, 317).trimEnd()}...`
            : clauseText;
        return `
            <article class="clause-card border-${riskClass(clause.risk_level)}">
                <div class="clause-header">
                    <h4 class="clause-title">${escapeHtml(clause.title)}</h4>
                    <span class="risk-badge badge-${riskClass(clause.risk_level)}">${escapeHtml(clause.risk_level)} RISK</span>
                </div>
                <div class="clause-meta">
                    <span><span>Category</span><strong>${escapeHtml(clause.risk_category)}</strong></span>
                </div>
                ${excerpt ? `<blockquote class="clause-text">“${escapeHtml(excerpt)}”</blockquote>` : ""}
                ${clause.explanation ? `<div class="clause-explanation"><strong>Why this is risky</strong><p>${escapeHtml(clause.explanation)}</p></div>` : ""}
                ${clause.role_impact ? `<div class="clause-explanation"><strong>Impact on ${escapeHtml(data.user_type || "selected role")}</strong><p>${escapeHtml(clause.role_impact)}</p></div>` : ""}
            </article>
        `;
    }).join("") : `<p class="empty-inline">No risky clauses were flagged in this document.</p>`;

    document.getElementById("priorityRisks").innerHTML = data.risk_clauses.length
        ? data.risk_clauses.slice(0, 3).map(clause => `
            <div class="priority-risk-item">
                <span class="risk-dot ${riskClass(clause.risk_level)}"></span>
                <div><strong>${escapeHtml(clause.title)}</strong><span>${escapeHtml(clause.risk_category)}</span></div>
                <span class="risk-badge badge-${riskClass(clause.risk_level)}">${escapeHtml(clause.risk_level)}</span>
            </div>
        `).join("")
        : `<p class="empty-inline">No risky clauses were flagged in this document.</p>`;

    const missingContainer = document.getElementById("missingContainer");
    missingContainer.innerHTML = data.missing_clauses.length ? data.missing_clauses.map(m => `
        <article class="missing-card">
            <h4 class="missing-title"><i class="fa-solid fa-triangle-exclamation" aria-hidden="true"></i> ${escapeHtml(m.clause_name || "Clause not specified")}</h4>
            ${m.reason ? `<p class="missing-desc">${escapeHtml(m.reason)}</p>` : ""}
            ${m.recommended_text ? `<div class="template-box"><strong>Suggested clause</strong><p>${escapeHtml(m.recommended_text)}</p></div>` : ""}
        </article>
    `).join("") : `<p class="empty-inline success-note"><i class="fa-solid fa-circle-check" aria-hidden="true"></i> No major missing clauses detected.</p>`;

    const lawsContainer = document.getElementById("lawsContainer");
    const laws = data.applicable_laws;
    lawsContainer.innerHTML = laws.length ? laws.map(law => `
        <article class="law-card">
            <h4 class="law-act-title"><i class="fa-solid fa-scale-balanced" aria-hidden="true"></i> ${escapeHtml(law.act_name)}</h4>
            ${law.section ? `<span class="law-section-badge">${escapeHtml(law.section)}</span>` : ""}
            ${law.applicability_reason ? `<p class="law-desc">${escapeHtml(law.applicability_reason)}</p>` : ""}
        </article>
    `).join("") : `<p class="empty-inline">No mapped Indian laws were returned for this document.</p>`;

    const processingTime = data.processing_time_ms === null ? "Not provided" : `${(data.processing_time_ms / 1000).toFixed(1)} sec`;
    document.getElementById("summaryContainer").innerHTML = `
        <div class="summary-heading"><div><p class="section-kicker">Contract summary</p><h3>Key terms at a glance</h3></div><span class="risk-badge badge-${riskClass(level)}">${escapeHtml(level)} RISK</span></div>
        <p class="summary-text">${data.summary ? escapeHtml(data.summary) : "No contract summary was returned for this document."}</p>
        <dl class="summary-metadata">
            <div><dt>Contract type</dt><dd>${escapeHtml(document.getElementById("contractTypeSelect").value || "Not provided")}</dd></div>
            <div><dt>Contract ID</dt><dd>${escapeHtml(data.contract_id || "Not provided")}</dd></div>
            <div><dt>Processing time</dt><dd>${escapeHtml(processingTime)}</dd></div>
            <div><dt>Clauses analyzed</dt><dd>${escapeHtml(data.total_clauses_found)}</dd></div>
        </dl>
    `;

    document.getElementById("allClausesCount").textContent = data.clauses.length;
    document.getElementById("allClausesContainer").innerHTML = data.clauses.length
        ? data.clauses.map((clause, index) => {
            const label = `Clause ${String(index + 1).padStart(2, "0")}`;
            const title = typeof clause === "string"
                ? label
                : clause && (clause.clause_type || clause.title || clause.name) || label;
            const text = typeof clause === "string"
                ? clause
                : clause && (clause.clause_text || clause.text || clause.content) || "";
            return `<details class="all-clause-item"><summary><span>${label}</span><strong>${escapeHtml(title)}</strong></summary><p>${text ? escapeHtml(text) : "No clause text was included."}</p></details>`;
        }).join("")
        : `<p class="empty-inline">Full extracted clause text is not included in this analysis response.</p>`;

    const panelId = preserveActivePanel && document.getElementById(previousPanel)
        ? previousPanel
        : "overviewPanel";
    switchTab(panelId, document.querySelector(`[aria-controls="${panelId}"]`));
}

function renderRiskCategories(clauses) {
    const container = document.getElementById("categoryList");
    if (!container) return;
    if (!clauses.length) {
        container.innerHTML = `<p class="empty-inline">No category-level risks were identified.</p>`;
        return;
    }
    const severityRank = { LOW: 1, MEDIUM: 2, HIGH: 3, CRITICAL: 4 };
    const groups = Object.create(null);
    clauses.forEach(clause => {
        const key = clause.risk_category || "GENERAL";
        const severity = String(clause.risk_level || "LOW").toUpperCase();
        if (!groups[key]) groups[key] = { severity, count: 0 };
        groups[key].count += 1;
        if ((severityRank[severity] || 0) > (severityRank[groups[key].severity] || 0)) {
            groups[key].severity = severity;
        }
    });
    container.innerHTML = Object.entries(groups).map(([name, group]) => `
            <div class="category-item">
                <div class="cat-header">
                    <span>${escapeHtml(name.replaceAll("_", " "))}</span>
                    <span class="cat-risk ${group.severity.toLowerCase()}">${group.severity} · ${group.count} clause${group.count === 1 ? "" : "s"}</span>
                </div>
            </div>
        `).join("");
}

// Chatbot Open / Close Drawer
function openChatbot() {
    document.getElementById("chatbotDrawer").style.display = "flex";
}

function closeChatbot() {
    document.getElementById("chatbotDrawer").style.display = "none";
}

function handleChatKeyPress(event) {
    if (event.key === "Enter") sendChatMessage();
}

function sendQuickPrompt(promptText) {
    document.getElementById("chatInput").value = promptText;
    sendChatMessage();
}

async function sendChatMessage() {
    const input = document.getElementById("chatInput");
    const text = input.value.trim();
    if (!text) return;

    const messages = document.getElementById("chatMessages");
    
    // Append User Message
    messages.innerHTML += `
        <div class="message user">
            <div class="msg-body">${text}</div>
        </div>
    `;
    input.value = "";
    messages.scrollTop = messages.scrollHeight;

    // Simulate Assistant Thinking
    const typingId = "msg_typing_" + Date.now();
    messages.innerHTML += `
        <div class="message assistant" id="${typingId}">
            <div class="msg-avatar"><i class="fa-solid fa-scale-balanced"></i></div>
            <div class="msg-body"><i class="fa-solid fa-circle-notch fa-spin"></i> Preparing your answer...</div>
        </div>
    `;
    messages.scrollTop = messages.scrollHeight;

    try {
        const response = await fetch(`${FASTAPI_URL}/ai/chat/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text })
        });
        
        if (!response.ok) {
            throw new Error(`Assistant service returned HTTP ${response.status}.`);
        }
        const data = await response.json();
        if (typeof data.content !== "string" || !data.content.trim()) {
            throw new Error("Assistant service returned no answer.");
        }
        const answer = data.content;
        document.getElementById(typingId).querySelector(".msg-body").innerHTML = answer;
    } catch (error) {
        document.getElementById(typingId).querySelector(".msg-body").textContent =
            `Assistant unavailable: ${error.message || "No response was generated."}`;
    }
    messages.scrollTop = messages.scrollHeight;
}

function downloadReport() {
    if (!currentContractData || !window.jspdf) {
        alert("The report is not ready yet. Please wait for the analysis to finish and try again.");
        return;
    }

    const { jsPDF } = window.jspdf;
    const doc = new jsPDF({ unit: "mm", format: "a4" });
    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    const margin = 18;
    const contentWidth = pageWidth - (margin * 2);
    let cursorY = 20;
    const data = currentContractData;
    const contractType = document.getElementById("contractTypeSelect").value;
    const fileName = document.getElementById("fileName").textContent || "contract";

    const colors = {
        navy: [16, 42, 67],
        blue: [21, 94, 239],
        muted: [102, 112, 133],
        line: [226, 232, 240],
        light: [248, 250, 252],
        red: [190, 45, 45],
        amber: [170, 112, 0],
        green: [20, 125, 85]
    };

    function addPageIfNeeded(height = 12) {
        if (cursorY + height > pageHeight - 20) {
            doc.addPage();
            cursorY = 20;
            addHeader();
        }
    }

    function addHeader() {
        doc.setFont("helvetica", "bold");
        doc.setFontSize(8);
        doc.setTextColor(...colors.muted);
        doc.text("CONTRACTAI", margin, 11);
        doc.text("CONFIDENTIAL REPORT", pageWidth - margin, 11, { align: "right" });
        doc.setDrawColor(...colors.line);
        doc.line(margin, 14, pageWidth - margin, 14);
    }

    function addFooter() {
        const pageNumber = doc.internal.getNumberOfPages();
        doc.setFont("helvetica", "normal");
        doc.setFontSize(8);
        doc.setTextColor(...colors.muted);
        doc.text(`Page ${pageNumber}`, pageWidth - margin, pageHeight - 9, { align: "right" });
    }

    function addText(text, options = {}) {
        const fontSize = options.fontSize || 10;
        const font = options.bold ? "bold" : "normal";
        const color = options.color || colors.navy;
        const lineHeight = options.lineHeight || 5;
        const lines = doc.splitTextToSize(String(text || ""), options.width || contentWidth);
        addPageIfNeeded(lines.length * lineHeight + (options.marginBottom || 0));
        doc.setFont("helvetica", font);
        doc.setFontSize(fontSize);
        doc.setTextColor(...color);
        doc.text(lines, options.x || margin, cursorY);
        cursorY += lines.length * lineHeight + (options.marginBottom || 0);
    }

    function addSectionTitle(title) {
        addPageIfNeeded(16);
        cursorY += 4;
        doc.setFont("helvetica", "bold");
        doc.setFontSize(13);
        doc.setTextColor(...colors.navy);
        doc.text(title, margin, cursorY);
        cursorY += 3;
        doc.setDrawColor(...colors.blue);
        doc.setLineWidth(0.8);
        doc.line(margin, cursorY, margin + 22, cursorY);
        cursorY += 8;
    }

    function addLabeledText(label, value) {
        addPageIfNeeded(10);
        doc.setFont("helvetica", "bold");
        doc.setFontSize(9);
        doc.setTextColor(...colors.navy);
        doc.text(`${label}:`, margin, cursorY);
        const labelWidth = doc.getTextWidth(`${label}: `);
        const lines = doc.splitTextToSize(String(value || ""), contentWidth - labelWidth);
        doc.setFont("helvetica", "normal");
        doc.setTextColor(...colors.muted);
        doc.text(lines, margin + labelWidth, cursorY);
        cursorY += Math.max(5, lines.length * 4.5) + 2;
    }

    function addRiskCard(clause) {
        const riskColor = clause.risk_level === "HIGH" ? colors.red : clause.risk_level === "LOW" ? colors.green : colors.amber;
        const excerpt = String(clause.clause_text || "").slice(0, 320);
        const text = `${clause.risk_category || clause.title} [${clause.risk_level} RISK]\nRisk: ${excerpt}\nWhy it matters: ${clause.explanation}\nImpact on ${currentRole}: ${clause.role_impact || ""}`;
        const lines = doc.splitTextToSize(text, contentWidth - 10);
        const boxHeight = lines.length * 4.4 + 8;
        addPageIfNeeded(boxHeight + 4);
        doc.setFillColor(...colors.light);
        doc.setDrawColor(...colors.line);
        doc.roundedRect(margin, cursorY - 4, contentWidth, boxHeight, 2, 2, "FD");
        doc.setFillColor(...riskColor);
        doc.rect(margin, cursorY - 4, 2, boxHeight, "F");
        doc.setFont("helvetica", "normal");
        doc.setFontSize(9);
        doc.setTextColor(...colors.navy);
        doc.text(lines, margin + 7, cursorY + 2);
        cursorY += boxHeight + 7;
    }

    addHeader();
    doc.setFont("helvetica", "bold");
    doc.setFontSize(22);
    doc.setTextColor(...colors.navy);
    doc.text("Contract Risk & Compliance Report", margin, cursorY);
    cursorY += 10;
    addText("A clear summary of the contract's risk profile, missing protections, and relevant Indian laws.", { color: colors.muted, marginBottom: 7 });
    addLabeledText("File", fileName);
    addLabeledText("Contract type", contractType);
    addLabeledText("Perspective", currentRole);
    addLabeledText("Generated", new Date().toLocaleString());

    addSectionTitle("Risk overview");
    doc.setFont("helvetica", "bold");
    doc.setFontSize(18);
    doc.setTextColor(...colors.blue);
    doc.text(`${data.overall_risk_score}/100`, margin, cursorY);
    doc.setFontSize(11);
    doc.setTextColor(...colors.navy);
    doc.text(`${data.risk_level} RISK`, margin + 35, cursorY);
    cursorY += 9;
    addLabeledText("Clauses evaluated", data.total_clauses_found || 0);
    addLabeledText("Risky clauses", data.risky_clauses_count || data.risk_clauses.length);
    addLabeledText("Missing clauses", data.missing_clauses_count || data.missing_clauses.length);
    addLabeledText("Indian laws mapped", data.applicable_laws ? data.applicable_laws.length : 0);
    addText(data.summary, { color: colors.muted, marginBottom: 4 });

    addSectionTitle("Risky clauses");
    data.risk_clauses.forEach(addRiskCard);

    addSectionTitle("Missing clauses");
    data.missing_clauses.forEach(clause => {
        addLabeledText(clause.clause_name, `${clause.reason} Suggested protection: ${clause.recommended_text}`);
    });

    addSectionTitle("Relevant Indian laws");
    (data.applicable_laws || []).forEach(law => {
        addLabeledText(law.act_name, `${law.section}. ${law.applicability_reason}`);
    });

    addPageIfNeeded(35);
    cursorY += 5;
    doc.setFillColor(239, 246, 255);
    doc.roundedRect(margin, cursorY - 4, contentWidth, 25, 2, 2, "F");
    addText("Disclaimer", { bold: true, color: colors.navy, marginBottom: 3 });
    addText("ContractAI is intended for informational purposes only and does not constitute legal advice. The analysis provided may not identify every potential legal issue or risk. Please consult a qualified legal professional before making decisions or entering into an agreement.", { fontSize: 8.5, color: colors.muted });

    for (let page = 1; page <= doc.internal.getNumberOfPages(); page += 1) {
        doc.setPage(page);
        addFooter();
    }

    const safeName = fileName.replace(/\.[^/.]+$/, "").replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, "") || "contract";
    doc.save(`${safeName}-risk-report.pdf`);
}
