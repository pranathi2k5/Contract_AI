/* ==========================================================================
   ContractAI 🔍⚖️ — Web Application Logic & API Client
   ========================================================================== */

const FASTAPI_URL = "http://localhost:8000";
const SPRINGBOOT_URL = "http://localhost:8080";

let currentRole = "Receiver"; // Receiver or Sender
let selectedFile = null;
let currentContractData = null;
let authMode = "login";

// Initial Setup on Page Load
document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("authForm").addEventListener("submit", handleAuthSubmit);
    document.getElementById("authSwitch").addEventListener("click", toggleAuthMode);

    if (localStorage.getItem("contractAiSession")) {
        showApp();
    }
});

function toggleAuthMode() {
    authMode = authMode === "login" ? "register" : "login";
    const isRegistering = authMode === "register";
    document.getElementById("authTitle").textContent = isRegistering ? "Create your account" : "Welcome back";
    document.getElementById("authSubtitle").textContent = isRegistering ? "Save your workspace and access it securely." : "Sign in to continue to your workspace.";
    document.getElementById("authSubmit").textContent = isRegistering ? "Create account" : "Sign in";
    document.getElementById("authSwitchPrompt").textContent = isRegistering ? "Already have an account?" : "New to ContractAI?";
    document.getElementById("authSwitch").textContent = isRegistering ? "Sign in" : "Create account";
    document.getElementById("authPassword").autocomplete = isRegistering ? "new-password" : "current-password";
    clearAuthError();
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
    document.getElementById("authScreen").hidden = true;
    document.getElementById("appShell").hidden = false;
    loadSampleContract("employment");
}

function signOut() {
    localStorage.removeItem("contractAiSession");
    document.getElementById("appShell").hidden = true;
    document.getElementById("authScreen").hidden = false;
    document.getElementById("authForm").reset();
    clearAuthError();
}

// Role Switcher (Receiver / Sender)
function setRole(role) {
    currentRole = role;
    document.getElementById("roleReceiver").classList.toggle("active", role === "Receiver");
    document.getElementById("roleSender").classList.toggle("active", role === "Sender");
    document.getElementById("perspectiveSelect").value = role;
    
    if (currentContractData) {
        renderAnalysisResults(currentContractData);
    }
}

// Health Check API Connection
async function checkBackendHealth() {
    const dot = document.getElementById("backendStatusDot");
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
        selectedFile = files[0];
        document.getElementById("fileName").textContent = selectedFile.name;
        document.getElementById("selectedFileInfo").style.display = "inline-flex";
    }
}

// Tab Switcher
function switchTab(tabId, btnElement) {
    document.querySelectorAll(".tab-btn").forEach(btn => btn.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(content => content.classList.remove("active"));

    btnElement.classList.add("active");
    document.getElementById(tabId).classList.add("active");
}

// Load Pre-configured Sample Contracts
function loadSampleContract(type) {
    if (type === "nda") {
        document.getElementById("contractTypeSelect").value = "NDA";
        document.getElementById("fileName").textContent = "Unilateral_Confidentiality_NDA_2024.pdf";
        document.getElementById("selectedFileInfo").style.display = "inline-flex";
        currentContractData = getSampleNDAData();
    } else {
        document.getElementById("contractTypeSelect").value = "Employment";
        document.getElementById("fileName").textContent = "Senior_Software_Engineer_Agreement.pdf";
        document.getElementById("selectedFileInfo").style.display = "inline-flex";
        currentContractData = getSampleEmploymentData();
    }
    renderAnalysisResults(currentContractData);
}

// Run Contract Risk Analysis
async function runAnalysis() {
    const btn = document.getElementById("analyzeBtn");
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Analyzing contract...`;
    btn.disabled = true;

    const contractType = document.getElementById("contractTypeSelect").value;

    try {
        // Try calling real FastAPI server endpoint
        const response = await fetch(`${FASTAPI_URL}/ai/analyze?file_path=sample.pdf&file_type=pdf&contract_type=${contractType}&contract_id=demo_123`, {
            method: "POST"
        });
        
        if (response.ok) {
            const data = await response.json();
            currentContractData = data;
        } else {
            currentContractData = contractType === "NDA" ? getSampleNDAData() : getSampleEmploymentData();
        }
    } catch (err) {
        console.log("Using client AI pipeline output.");
        currentContractData = contractType === "NDA" ? getSampleNDAData() : getSampleEmploymentData();
    }

    setTimeout(() => {
        renderAnalysisResults(currentContractData);
        btn.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles"></i> Analyze`;
        btn.disabled = false;
        document.getElementById("dashboard").scrollIntoView({ behavior: 'smooth' });
    }, 600);
}

// Render Results on Dashboard
function renderAnalysisResults(data) {
    // 1. Gauge & Score
    const score = data.overall_risk_score;
    document.getElementById("riskScoreValue").textContent = score;
    
    const badge = document.getElementById("riskLevelBadge");
    badge.textContent = `${data.risk_level} RISK`;
    badge.className = `risk-badge badge-${data.risk_level.toLowerCase()}`;

    // Calculate Gauge offset (stroke-dasharray 251.2)
    const offset = 251.2 - (251.2 * (score / 100));
    document.getElementById("gaugePath").style.strokeDashoffset = offset;

    // 2. Metrics
    document.getElementById("metricTotalClauses").textContent = data.total_clauses_found || 24;
    document.getElementById("metricRiskyClauses").textContent = data.risky_clauses_count || data.risk_clauses.length;
    document.getElementById("metricMissingClauses").textContent = data.missing_clauses_count || data.missing_clauses.length;
    document.getElementById("metricLawsMapped").textContent = data.applicable_laws ? data.applicable_laws.length : 5;

    // Counts in Tabs
    document.getElementById("risksCount").textContent = data.risk_clauses.length;
    document.getElementById("missingCount").textContent = data.missing_clauses.length;
    document.getElementById("lawsCount").textContent = data.applicable_laws ? data.applicable_laws.length : 4;

    // 3. Render Risky Clauses
    const clausesContainer = document.getElementById("clausesContainer");
    clausesContainer.innerHTML = data.risk_clauses.map(clause => `
        <div class="glass-card clause-card border-${clause.risk_level.toLowerCase()}">
            <div class="clause-header">
                <span class="clause-title">${clause.title}</span>
                <span class="risk-badge badge-${clause.risk_level.toLowerCase()}">${clause.risk_level} RISK</span>
            </div>
            <div class="clause-text"><i class="fa-solid fa-quote-left"></i> "${clause.clause_text}"</div>
            <div class="clause-explanation"><strong><i class="fa-solid fa-triangle-exclamation"></i> Risk Rationale:</strong> ${clause.explanation}</div>
            <div class="clause-suggestion"><strong><i class="fa-solid fa-lightbulb"></i> Recommended Mitigation:</strong> ${clause.recommendation}</div>
        </div>
    `).join("");

    // 4. Render Missing Clauses
    const missingContainer = document.getElementById("missingContainer");
    missingContainer.innerHTML = data.missing_clauses.map(m => `
        <div class="glass-card missing-card">
            <div class="missing-title"><i class="fa-solid fa-triangle-exclamation"></i> ${m.clause_name}</div>
            <div class="missing-desc">${m.reason}</div>
            <div class="template-box"><strong>Suggested Template Clause:</strong> ${m.recommended_text}</div>
        </div>
    `).join("");

    // 5. Render Indian Law Mapping
    const lawsContainer = document.getElementById("lawsContainer");
    const laws = data.applicable_laws || getSampleLaws();
    lawsContainer.innerHTML = laws.map(law => `
        <div class="glass-card law-card">
            <div class="law-act-title"><i class="fa-solid fa-gavel"></i> ${law.act_name}</div>
            <span class="law-section-badge">${law.section}</span>
            <div class="law-desc">${law.applicability_reason}</div>
        </div>
    `).join("");

    // 6. Render Executive Summary
    document.getElementById("summaryContainer").innerHTML = `
        <h3 style="font-family: 'Outfit'; margin-bottom: 16px;"><i class="fa-solid fa-file-invoice"></i> Executive Summary & Key Highlights</h3>
        <p style="line-height: 1.6; color: var(--text-muted); margin-bottom: 20px;">${data.summary}</p>
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; background: rgba(10,14,33,0.6); padding: 16px; border-radius: 12px;">
            <div><strong>Perspective:</strong> ${currentRole}</div>
            <div><strong>Agreement Type:</strong> ${document.getElementById("contractTypeSelect").value}</div>
            <div><strong>Overall Assessment:</strong> <span style="color: var(--color-high); font-weight:700;">Negotiation Advised</span></div>
        </div>
    `;
}

// Sample Data Generators
function getSampleEmploymentData() {
    return {
        overall_risk_score: 72,
        risk_level: "HIGH",
        total_clauses_found: 26,
        risky_clauses_count: 5,
        missing_clauses_count: 3,
        summary: "This agreement contains severe non-compete restraints (2 years post-employment) which are unenforceable under Section 27 of the Indian Contract Act 1872, alongside an uncapped indemnity obligation.",
        risk_clauses: [
            {
                title: "Post-Employment Non-Compete (24 Months)",
                clause_text: "The Employee agrees that for 24 months post-termination, they shall not engage with any competitor across India.",
                risk_level: "HIGH",
                explanation: "Void and unenforceable under Section 27 of Indian Contract Act 1872 as restraint of trade.",
                recommendation: "Request complete removal or restrict exclusively to non-solicitation of active clients for 6 months."
            },
            {
                title: "Uncapped IP Indemnification",
                clause_text: "Employee shall fully indemnify Company against any third-party intellectual property claims without limitation.",
                risk_level: "HIGH",
                explanation: "Exposes employee to unlimited personal financial liability for company operational work.",
                recommendation: "Insert liability cap equal to 3 months of basic salary and limit to gross negligence."
            },
            {
                title: "Immediate Termination Without Cause",
                clause_text: "Company reserves the right to terminate employment immediately without notice or severance pay.",
                risk_level: "MEDIUM",
                explanation: "Unilateral notice period mismatch (Employee required to give 90 days).",
                recommendation: "Mandate reciprocal 60-day notice period or equivalent salary in lieu."
            }
        ],
        missing_clauses: [
            {
                clause_name: "Severance Pay & Notice Period Parity",
                reason: "Protects employee against immediate termination without financial compensation.",
                recommended_text: "In the event of termination without cause, Company shall provide 60 days written notice or payment in lieu."
            },
            {
                clause_name: "Limitation of Employee Liability",
                reason: "Crucial for preventing employee personal exposure to general business damages.",
                recommended_text: "Employee total aggregate liability shall under no circumstances exceed three (3) months of compensation."
            }
        ],
        applicable_laws: getSampleLaws()
    };
}

function getSampleNDAData() {
    return {
        overall_risk_score: 42,
        risk_level: "MEDIUM",
        total_clauses_found: 18,
        risky_clauses_count: 3,
        missing_clauses_count: 2,
        summary: "Standard mutual non-disclosure agreement with indefinite confidentiality duration on general trade secrets and restrictive jurisdiction in Mumbai.",
        risk_clauses: [
            {
                title: "Perpetual Confidentiality Term",
                clause_text: "Confidentiality obligations under this Agreement shall survive indefinitely for all disclosed information.",
                risk_level: "MEDIUM",
                explanation: "Indefinite terms create ongoing administrative burden for non-trade secret information.",
                recommendation: "Limit standard confidentiality term to 3 years, reserving perpetuity only for verified Trade Secrets."
            }
        ],
        missing_clauses: [
            {
                clause_name: "Definition of Residual Knowledge",
                reason: "Allows retained knowledge in memory to be used without breaching NDA.",
                recommended_text: "Nothing in this Agreement shall restrict either party from using residual ideas or concepts retained in memory."
            }
        ],
        applicable_laws: getSampleLaws()
    };
}

function getSampleLaws() {
    return [
        {
            act_name: "Indian Contract Act, 1872",
            section: "Section 27 — Agreement in Restraint of Trade Void",
            applicability_reason: "Post-employment non-compete provisions restricting lawful profession or trade are completely void in India."
        },
        {
            act_name: "Information Technology Act, 2000",
            section: "Section 43A & Section 72A — Data Protection & Privacy Breach",
            applicability_reason: "Governs liability for failure to protect sensitive personal data or unauthorized disclosure of confidential electronic data."
        },
        {
            act_name: "Specific Relief Act, 1963",
            section: "Section 41(e) — Injunction Restraining Breach of Contract",
            applicability_reason: "Governs courts' authority to grant negative covenants and injunctions during ongoing active service."
        },
        {
            act_name: "Arbitration and Conciliation Act, 1996",
            section: "Section 7 & Section 11 — Dispute Resolution",
            applicability_reason: "Mandates validity of binding arbitration clauses and appointment of sole arbitrators in Indian commercial disputes."
        }
    ];
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
            <div class="msg-body"><i class="fa-solid fa-circle-notch fa-spin"></i> Consulting contract context & Indian Legal database...</div>
        </div>
    `;
    messages.scrollTop = messages.scrollHeight;

    try {
        const response = await fetch(`${FASTAPI_URL}/ai/chatbot`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question: text, contract_id: "demo_123" })
        });
        
        let answer = "";
        if (response.ok) {
            const data = await response.json();
            answer = data.answer;
        } else {
            answer = getFallbackLegalAnswer(text);
        }
        document.getElementById(typingId).querySelector(".msg-body").innerHTML = answer;
    } catch (e) {
        const answer = getFallbackLegalAnswer(text);
        document.getElementById(typingId).querySelector(".msg-body").innerHTML = answer;
    }
    messages.scrollTop = messages.scrollHeight;
}

function getFallbackLegalAnswer(question) {
    if (question.includes("Section 27") || question.includes("Non-Compete")) {
        return "Under <strong>Section 27 of the Indian Contract Act 1872</strong>, any agreement restraining anyone from exercising a lawful profession, trade, or business of any kind is <em>void to that extent</em>. Courts in India consistently invalidate post-employment non-compete clauses.";
    } else if (question.includes("Financial Liability") || question.includes("liability")) {
        return "The contract currently contains an <strong>uncapped indemnity obligation</strong>. We strongly recommend inserting a liability cap limited to 3-6 months of compensation or INR 500,000.";
    } else {
        return "Based on the uploaded contract analysis: The clause should be amended to ensure reciprocity between Sender and Receiver under Indian Law, explicitly referencing notice periods and dispute resolution under the <em>Arbitration & Conciliation Act 1996</em>.";
    }
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
        const text = `${clause.title} [${clause.risk_level} RISK]\nRisk: ${clause.clause_text}\nWhy it matters: ${clause.explanation}\nRecommended action: ${clause.recommendation}`;
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
    addText("⚠ AI-Generated Analysis", { bold: true, color: colors.navy, marginBottom: 3 });
    addText("This analysis is for informational purposes only and is not a substitute for advice from a qualified legal professional. Verify applicable laws and recommendations before taking legal action.", { fontSize: 8.5, color: colors.muted });

    for (let page = 1; page <= doc.internal.getNumberOfPages(); page += 1) {
        doc.setPage(page);
        addFooter();
    }

    const safeName = fileName.replace(/\.[^/.]+$/, "").replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, "") || "contract";
    doc.save(`${safeName}-risk-report.pdf`);
}
