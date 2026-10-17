import json
import os
import sys
from types import SimpleNamespace

import pytest
import requests
from starlette.datastructures import UploadFile as StarletteUploadFile
from fastapi.testclient import TestClient

from app.main import app
from app.services.risk_analyzer import RiskAnalyzer
from app.services.chatbot_service import chatbot_service
from app.services.rag_service import LEGAL_DISCLAIMER
from app.ml.legalbert_model import get_legalbert_model
from app.ml.sbert_model import SBERTModel, SBERTModelUnavailableError
from app.config import settings
from app.routers import analysis as analysis_router

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolate_legal_corpus_for_api_tests(monkeypatch):
    monkeypatch.setattr(
        analysis_router.law_mapper,
        "map_laws_with_status",
        lambda clauses: {
            "matches": [],
            "legal_corpus_status": {"status": "empty", "sections": 0},
            "legal_disclaimer": LEGAL_DISCLAIMER,
        },
    )


def _mock_receiver_risk_scores(analyzer, texts, concepts, sender_similarity=0.1):
    rows = []
    for text in texts:
        row = [0.1] * len(concepts)
        lowered = text.lower()
        category = (
            "INDEMNITY" if "indemnif" in lowered
            else "RESTRAINT" if "non-compete" in lowered
            else "FINANCIAL_LIABILITY" if "liability" in lowered
            else None
        )
        if category:
            for index, entry in enumerate(analyzer.risk_knowledge_base):
                if entry["category"] == category:
                    row[index] = 0.92 if entry["risk_to"] == "Receiver" else sender_similarity
        rows.append(row)
    return rows


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_allows_live_server_and_rejects_unconfigured_origins():
    for origin in ("http://localhost:5500", "http://127.0.0.1:5500"):
        allowed = client.options(
            "/ai/analyze",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
            },
        )
        assert allowed.status_code == 200
        assert allowed.headers["access-control-allow-origin"] == origin

    blocked = client.options(
        "/ai/analyze",
        headers={
            "Origin": "https://unconfigured.example",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert blocked.status_code == 400
    assert "access-control-allow-origin" not in blocked.headers


def test_upload_is_written_in_bounded_chunks(tmp_path, monkeypatch):
    monkeypatch.setenv("CONTRACTAI_UPLOAD_DIR", str(tmp_path))
    payload = b"x" * (2 * 1024 * 1024 + 17)
    read_sizes = []
    parsed_file_sizes = []
    original_read = StarletteUploadFile.read

    async def tracked_read(upload, size=-1):
        read_sizes.append(size)
        return await original_read(upload, size)

    monkeypatch.setattr(StarletteUploadFile, "read", tracked_read)
    monkeypatch.setattr(
        analysis_router.document_parser,
        "parse_document",
        lambda path, file_type: parsed_file_sizes.append(os.path.getsize(path))
        or "Agreement text.",
    )
    monkeypatch.setattr(analysis_router.clause_extractor, "extract_clauses", lambda text: [])
    monkeypatch.setattr(analysis_router.missing_clause_detector, "detect", lambda *args: [])
    monkeypatch.setattr(
        analysis_router.risk_analyzer,
        "analyze",
        lambda *args, **kwargs: {
            "overall_risk_score": 0,
            "risk_level": "LOW",
            "risk_clauses": [],
            "role_risk_scores": {
                "Sender": {"overall_risk_score": 0, "risk_level": "LOW", "contributions": []},
                "Receiver": {"overall_risk_score": 0, "risk_level": "LOW", "contributions": []},
            },
            "sbert_ran": False,
            "llm_ran": False,
            "warnings": [],
        },
    )
    monkeypatch.setattr(analysis_router.law_mapper, "map_laws", lambda clauses: [])
    monkeypatch.setattr(analysis_router.summary_generator, "generate_summary", lambda text: "")

    response = client.post(
        "/ai/analyze",
        data={
            "contract_type": "Service",
            "contract_id": "chunked-upload",
            "user_type": "Receiver",
        },
        files={"file": ("agreement.txt", payload, "text/plain")},
    )

    assert response.status_code == 200
    assert parsed_file_sizes == [len(payload)]
    assert read_sizes == [1024 * 1024] * 4
    assert list(tmp_path.iterdir()) == []


def test_chat_reports_unavailable_ollama_as_service_error(monkeypatch):
    request_details = {}
    monkeypatch.setattr(settings, "LLM_PROVIDER", "ollama")
    monkeypatch.setattr(settings, "LLM_TIMEOUT_SECONDS", 15)

    def unavailable_ollama(url, **kwargs):
        request_details.update(url=url, **kwargs)
        raise requests.ConnectionError("connection refused")

    monkeypatch.setattr(
        "app.services.chatbot_service.requests.post",
        unavailable_ollama,
    )

    response = client.post("/ai/chat/", json={"message": "Hello"})

    assert response.status_code == 503
    assert "Ollama" in response.json()["detail"]
    assert request_details["timeout"] == 15
    assert request_details["url"].endswith("/api/generate")


def test_chat_returns_a_valid_ollama_response(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "ollama")
    response_body = {"response": "Hello there."}
    monkeypatch.setattr(
        "app.services.chatbot_service.requests.post",
        lambda *args, **kwargs: SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: response_body,
        ),
    )

    response = client.post("/ai/chat/", json={"message": "Hello"})

    assert response.status_code == 200
    assert response.json()["content"] == "Hello there."
    assert "legal information only" not in response.json()["content"].lower()
    assert response.json()["role"] == "assistant"
    assert response.json()["sources"] == []


def test_chat_returns_gemini_response_with_contract_context_and_sources(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-key")
    posted = {}

    def mock_retrieval(query):
        assert query == "What is the notice period?"
        return {
            "status": "ready",
            "matches": [{
                "act_name": "Verified Act",
                "section_number": "1",
                "section_title": "Verified section",
                "source_url": "https://www.indiacode.nic.in/verified.pdf",
                "relevance_score": 0.8,
                "retrieved_text": "Official section text.",
            }],
        }

    def gemini_post(url, **kwargs):
        posted.update(url=url, **kwargs)
        return SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: {"candidates": [{
                "content": {"parts": [{"text": "The supplied contract states 30 days."}]}
            }]},
        )

    monkeypatch.setattr("app.routers.chatbot.rag_service.query", mock_retrieval)
    monkeypatch.setattr("app.services.chatbot_service.requests.post", gemini_post)
    response = client.post(
        "/ai/chat/",
        json={"message": "What is the notice period?", "contract_context": "Notice is 30 days."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "assistant"
    assert body["content"] == "The supplied contract states 30 days."
    assert body["sources"][0]["section_number"] == "1"
    assert body["sources"][0]["retrieved_text"] == "Official section text."
    assert "Notice is 30 days." in posted["json"]["contents"][0]["parts"][0]["text"]
    assert "Official section text." in posted["json"]["contents"][0]["parts"][0]["text"]
    assert posted["url"].endswith(
        f"/models/{settings.GEMINI_MODEL}:generateContent"
    )
    assert posted["headers"] == {"x-goog-api-key": "test-key"}
    assert "test-key" not in posted["url"]
    assert "AI-generated explanation" not in body["content"]
    assert "Retrieved statutory evidence" not in body["content"]
    assert "legal information only" not in body["content"].lower()


def test_general_legal_question_is_answered_without_contract_or_rag(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-key")
    prompts = []
    monkeypatch.setattr(
        "app.routers.chatbot.rag_service.query",
        lambda query: {"status": "no_relevant_match", "matches": []},
    )

    def generate_general_answer(url, **kwargs):
        prompts.append(kwargs["json"]["contents"][0]["parts"][0]["text"])
        return SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: {"candidates": [{
                "content": {"parts": [{
                    "text": "A non-compete is a term restricting certain competitive work."
                }]}
            }]},
        )

    monkeypatch.setattr(
        "app.services.chatbot_service.requests.post",
        generate_general_answer,
    )
    response = client.post("/ai/chat/", json={"message": "What is a non-compete?"})

    assert response.status_code == 200
    body = response.json()
    assert "restricting certain competitive work" in body["content"]
    assert "general" in prompts[0].lower()
    assert "CONTRACT TEXT:\nNone provided." in prompts[0]
    assert "RETRIEVED LEGAL EVIDENCE:\nNone retrieved." in prompts[0]
    assert body["content"] == (
        "A non-compete is a term restricting certain competitive work."
    )
    assert body["sources"] == []


def test_contract_question_uses_uploaded_contract_when_no_law_is_retrieved(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-key")
    prompts = []
    monkeypatch.setattr(
        "app.routers.chatbot.rag_service.query",
        lambda query: {"status": "empty", "matches": []},
    )

    def generate_contract_answer(url, **kwargs):
        prompts.append(kwargs["json"]["contents"][0]["parts"][0]["text"])
        return SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: {"candidates": [{
                "content": {"parts": [{
                    "text": "The supplied agreement says the notice period is 30 days."
                }]}
            }]},
        )

    monkeypatch.setattr(
        "app.services.chatbot_service.requests.post",
        generate_contract_answer,
    )
    response = client.post(
        "/ai/chat/",
        json={
            "message": "What notice period does my contract specify?",
            "contract_context": "The employee must give 30 days' written notice.",
        },
    )

    assert response.status_code == 200
    assert response.json()["content"] == (
        "The supplied agreement says the notice period is 30 days."
    )
    assert "The employee must give 30 days' written notice." in prompts[0]
    assert response.json()["sources"] == []


def test_chat_ignores_irrelevant_or_unverified_rag_results(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-key")
    prompts = []
    monkeypatch.setattr(
        "app.routers.chatbot.rag_service.query",
        lambda query: {
            "status": "ready",
            "matches": [
                {
                    "act_name": "Unverified source",
                    "section_number": "1",
                    "section_title": "Section title",
                    "source_url": "https://example.com/fake",
                    "relevance_score": 0.99,
                    "retrieved_text": "Unverified legal text.",
                },
                {
                    "act_name": "Verified Act",
                    "section_number": "7",
                    "section_title": "Relevant",
                    "source_url": "https://www.indiacode.nic.in/act.pdf",
                    "relevance_score": 0.2,
                    "retrieved_text": "Low relevance text.",
                },
            ],
        },
    )

    def generate_answer(url, **kwargs):
        prompts.append(kwargs["json"]["contents"][0]["parts"][0]["text"])
        return SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: {"candidates": [{
                "content": {"parts": [{"text": "Here is general information."}]}
            }]},
        )

    monkeypatch.setattr("app.services.chatbot_service.requests.post", generate_answer)
    response = client.post("/ai/chat/", json={"message": "What does this legal term mean?"})

    assert response.status_code == 200
    assert "Unverified legal text." not in prompts[0]
    assert "Low relevance text." not in prompts[0]
    assert response.json()["content"] == "Here is general information."
    assert response.json()["sources"] == []


def test_chat_fails_explicitly_when_gemini_key_is_missing(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")

    response = client.post("/ai/chat/", json={"message": "What does this contract say?"})

    assert response.status_code == 503
    assert "GEMINI_API_KEY" in response.json()["detail"]


def test_chat_fails_explicitly_on_gemini_timeout(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(
        "app.services.chatbot_service.requests.post",
        lambda *args, **kwargs: (_ for _ in ()).throw(requests.Timeout()),
    )

    response = client.post("/ai/chat/", json={"message": "Question"})

    assert response.status_code == 503
    assert "timed out" in response.json()["detail"]


def test_non_compete_definition_falls_back_locally_on_gemini_timeout(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(
        "app.routers.chatbot.rag_service.query",
        lambda query: {"status": "no_relevant_match", "matches": []},
    )
    monkeypatch.setattr(
        "app.services.chatbot_service.requests.post",
        lambda *args, **kwargs: (_ for _ in ()).throw(requests.Timeout()),
    )

    response = client.post("/ai/chat/", json={"message": "What's a non-compete?"})

    assert response.status_code == 200
    assert response.json()["sources"] == []
    assert "A non-compete is a contract term" in response.json()["content"]
    assert "depends on the jurisdiction and circumstances" in response.json()["content"]
    assert "not legal advice" not in response.json()["content"].lower()


@pytest.mark.parametrize(
    ("status_code", "error_body", "expected_detail"),
    [
        (
            404,
            {"error": {"message": "Model gemini-3.8-flash not found."}},
            "model is unsupported",
        ),
        (
            429,
            {"error": {"status": "RESOURCE_EXHAUSTED", "message": "Quota exceeded."}},
            "quota or rate limit",
        ),
        (
            500,
            {"error": {"message": "Internal server error."}},
            "provider error",
        ),
    ],
)
def test_chat_reports_gemini_http_errors_without_exposing_api_key(
    monkeypatch, caplog, status_code, error_body, expected_detail
):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-secret")

    def provider_failure(*args, **kwargs):
        response = requests.Response()
        response.status_code = status_code
        response._content = json.dumps(error_body).encode()
        raise requests.HTTPError(response=response)

    monkeypatch.setattr("app.services.chatbot_service.requests.post", provider_failure)
    response = client.post("/ai/chat/", json={"message": "Question"})

    assert response.status_code == 503
    assert expected_detail in response.json()["detail"]
    assert "test-secret" not in response.text
    assert "test-secret" not in caplog.text


@pytest.mark.parametrize(
    ("severity", "expected_score"),
    [
        ("CRITICAL", 90.0),
        ("HIGH", 70.0),
        ("MEDIUM", 45.0),
        ("LOW", 15.0),
    ],
)
def test_overall_score_uses_severity_base_values(severity, expected_score):
    result = RiskAnalyzer.compute_overall_score([severity])

    assert result["score"] == expected_score


def test_overall_score_averages_confirmed_risk_clause_severity():
    mixed_risks = RiskAnalyzer.compute_overall_score(["HIGH", "MEDIUM"])

    assert mixed_risks["score"] == 57.5


def test_overall_score_averages_risky_clauses_without_counting_safe_clauses():
    one_severe_clause = ["HIGH"]

    assert RiskAnalyzer.compute_overall_score(one_severe_clause)["score"] == 70.0
    assert RiskAnalyzer.compute_overall_score([])["score"] == 0.0


def test_adding_safe_clauses_does_not_dilute_detected_risk(monkeypatch):
    analyzer = RiskAnalyzer()
    indemnity_pattern_indexes = {
        index
        for index, pattern in enumerate(analyzer.risk_knowledge_base)
        if pattern["category"] == "INDEMNITY"
    }
    monkeypatch.setattr(
        "app.services.risk_analyzer.sbert_model.semantic_scores",
        lambda texts, patterns: [
            [0.92 if index in indemnity_pattern_indexes else 0.1
             for index, _ in enumerate(patterns)]
            if "indemnify" in text.lower()
            else [0.1] * len(patterns)
            for text in texts
        ],
    )
    risky_clause = {
        "clause_text": "The Employee shall indemnify the Company for all claims."
    }
    safe_clauses = [
        {"clause_text": f"The parties agree to cooperate in good faith on item {index}."}
        for index in range(10)
    ]

    short_contract = analyzer.analyze([risky_clause], user_type="Receiver")
    longer_contract = analyzer.analyze(
        [risky_clause, *safe_clauses],
        user_type="Receiver",
    )

    assert short_contract["overall_risk_score"] == longer_contract["overall_risk_score"]
    assert short_contract["overall_risk_score"] == 90.0


def test_empty_extraction_returns_a_neutral_score(monkeypatch):
    analyzer = RiskAnalyzer()
    monkeypatch.setattr(
        "app.services.risk_analyzer.sbert_model.semantic_scores",
        lambda texts, patterns: [],
    )

    result = analyzer.analyze([], user_type="Receiver")

    assert result["overall_risk_score"] == 0.0
    assert result["risk_level"] == "LOW"
    assert result["risk_clauses"] == []


def test_risk_scores_are_derived_without_chat_provider_calls(monkeypatch):
    analyzer = RiskAnalyzer()
    monkeypatch.setattr(
        "app.services.risk_analyzer.sbert_model.semantic_scores",
        lambda texts, patterns: [[0.1] * len(patterns) for _ in texts],
    )
    monkeypatch.setattr(
        chatbot_service,
        "generate",
        lambda *args, **kwargs: pytest.fail("Risk scoring must not call the chatbot provider."),
    )
    result = analyzer.analyze(
        [{"clause_text": "Invoices are settled as specified in the attached schedule."}],
        user_type="Receiver",
    )

    assert result["llm_ran"] is False
    assert result["overall_risk_score"] == 0


def test_legalbert_disabled_by_default():
    assert settings.ENABLE_LEGALBERT is False
    assert get_legalbert_model() is None


def test_risk_scores_differ_by_document_content(monkeypatch):
    analyzer = RiskAnalyzer()
    monkeypatch.setattr(
        "app.services.risk_analyzer.sbert_model.semantic_scores",
        lambda texts, patterns: _mock_receiver_risk_scores(analyzer, texts, patterns),
    )

    low_risk = analyzer.analyze(
        [{
            "clause_text": "The parties will cooperate in good faith to complete the project on schedule.",
            "clause_type": "GENERAL",
            "confidence": 0.9,
        }],
        missing_clauses=[],
    )

    high_risk = analyzer.analyze(
        [
            {
                "clause_text": "Employee shall accept unlimited liability and a 24-month non-compete across India.",
                "clause_type": "LIABILITY",
                "confidence": 0.4,
            },
            {
                "clause_text": "Late payment attracts liquidated damages and time is of the essence.",
                "clause_type": "PAYMENT",
                "confidence": 0.5,
            },
        ],
        missing_clauses=[{"importance": "CRITICAL"}],
    )

    assert high_risk["overall_risk_score"] > low_risk["overall_risk_score"]
    assert high_risk["overall_risk_score"] > 25
    assert len(high_risk["risk_clauses"]) >= 1


def test_unavailable_sbert_uses_explicit_risk_rules(monkeypatch):
    analyzer = RiskAnalyzer()

    def fail_scoring(texts, concepts):
        raise SBERTModelUnavailableError("SBERT is unavailable.")

    monkeypatch.setattr(
        "app.services.risk_analyzer.sbert_model.semantic_scores",
        fail_scoring,
    )

    result = analyzer.analyze(
        [{
            "clause_text": "The Employee must pay disproportionate penalties for late payment.",
            "clause_type": "PAYMENT",
        }],
        missing_clauses=[],
        contract_type="Vendor",
    )

    assert result["overall_risk_score"] > 0
    assert result["sbert_ran"] is False
    assert any("SBERT" in warning for warning in result["warnings"])


def test_upload_returns_dynamic_score_without_sbert(tmp_path, monkeypatch):
    monkeypatch.setenv("CONTRACTAI_UPLOAD_DIR", str(tmp_path))

    def fail_scoring(texts, concepts):
        raise SBERTModelUnavailableError("SBERT is unavailable.")

    monkeypatch.setattr(
        "app.services.risk_analyzer.sbert_model.semantic_scores",
        fail_scoring,
    )
    response = client.post(
        "/ai/analyze",
        data={
            "contract_type": "Employment",
            "contract_id": "no-sbert",
            "user_type": "Receiver",
        },
        files={"file": ("employment.txt", b"The Employee shall indemnify the Company.", "text/plain")},
    )

    assert response.status_code == 200
    assert response.json()["overall_risk_score"] > 0
    assert response.json()["analysis_metrics"]["sbert_ran"] is False


def test_distinct_contract_text_produces_distinct_risk_results(tmp_path, monkeypatch):
    monkeypatch.setenv("CONTRACTAI_UPLOAD_DIR", str(tmp_path))
    analyzer = analysis_router.risk_analyzer
    semantic_score_calls = []

    def score_uploaded_clauses(texts, patterns):
        semantic_score_calls.extend(texts)
        return _mock_receiver_risk_scores(analyzer, texts, patterns)

    monkeypatch.setattr(
        "app.services.risk_analyzer.sbert_model.semantic_scores",
        score_uploaded_clauses,
    )
    monkeypatch.setattr(analysis_router.missing_clause_detector, "detect", lambda *args: [])
    monkeypatch.setattr(analysis_router.law_mapper, "map_laws", lambda clauses: [])
    monkeypatch.setattr(analysis_router.summary_generator, "generate_summary", lambda text: "")
    contracts = {
        "employment.txt": (
            "EMPLOYMENT AGREEMENT\n\n"
            "The Employee shall indemnify the Company for any and all claims without limitation.\n\n"
            "The Employee shall not compete with the Company for two years after termination."
        ),
        "service.txt": (
            "SERVICE AGREEMENT\n\n"
            "The parties will cooperate in good faith to complete the services.\n\n"
            "Either party may terminate this agreement by giving thirty days written notice."
        ),
    }
    results = {}

    for filename, contract_text in contracts.items():
        response = client.post(
            "/ai/analyze",
            data={
                "contract_type": "Employment" if filename.startswith("employment") else "Service",
                "contract_id": filename,
                "user_type": "Receiver",
            },
            files={"file": (filename, contract_text, "text/plain")},
        )
        assert response.status_code == 200
        results[filename] = response.json()

    employment_result = results["employment.txt"]
    service_result = results["service.txt"]
    assert employment_result["overall_risk_score"] > service_result["overall_risk_score"]
    assert employment_result["risk_clauses"] != service_result["risk_clauses"]
    assert employment_result["user_type"] == service_result["user_type"] == "Receiver"
    assert all(
        clause["clause_text"] in employment_result["extracted_text"]
        for clause in employment_result["risk_clauses"]
    )
    assert not service_result["risk_clauses"]
    assert employment_result["analysis_metrics"]["sbert_ran"] is True
    assert service_result["analysis_metrics"]["sbert_ran"] is True
    assert semantic_score_calls
    assert "risk_score_basis" not in employment_result
    assert all("risk_score" not in clause for clause in employment_result["risk_clauses"])


def test_role_changes_score_for_obligations_assigned_to_that_party(monkeypatch):
    analyzer = RiskAnalyzer()
    monkeypatch.setattr(
        "app.services.risk_analyzer.sbert_model.semantic_scores",
        lambda texts, patterns: _mock_receiver_risk_scores(
            analyzer,
            texts,
            patterns,
        ),
    )
    clauses = [{
        "clause_text": "The Employee shall indemnify the Company for any and all claims without limitation.",
        "clause_type": "INDEMNITY",
        "confidence": 0.8,
    }]

    receiver_result = analyzer.analyze(clauses, missing_clauses=[], user_type="Receiver")
    sender_result = analyzer.analyze(clauses, missing_clauses=[], user_type="Sender")

    assert receiver_result["overall_risk_score"] > sender_result["overall_risk_score"]
    assert receiver_result["risk_clauses"][0]["role_impact"]
    assert "risk_score" not in receiver_result["risk_clauses"][0]
    assert "cosine similarity" not in receiver_result["risk_clauses"][0]["explanation"].lower()
    assert not sender_result["risk_clauses"]
    assert receiver_result["role_risk_scores"]["Receiver"]["overall_risk_score"] > (
        receiver_result["role_risk_scores"]["Sender"]["overall_risk_score"]
    )
    assert receiver_result["role_risk_scores"]["Receiver"]["contributions"][0]["clause_text"]


def test_balanced_clause_has_equal_sender_and_receiver_exposure(monkeypatch):
    analyzer = RiskAnalyzer()
    monkeypatch.setattr(
        "app.services.risk_analyzer.sbert_model.semantic_scores",
        lambda texts, patterns: [[0.1] * len(patterns) for _ in texts],
    )
    result = analyzer.analyze(
        [{"clause_text": "Confidentiality duties continue indefinitely without exceptions."}],
        user_type="Receiver",
    )

    assert result["role_risk_scores"]["Sender"]["overall_risk_score"] == 45.0
    assert result["role_risk_scores"]["Receiver"]["overall_risk_score"] == 45.0
    sender_contribution = result["role_risk_scores"]["Sender"]["contributions"][0]
    receiver_contribution = result["role_risk_scores"]["Receiver"]["contributions"][0]
    assert sender_contribution["category"] == receiver_contribution["category"]
    assert sender_contribution["risk_level"] == receiver_contribution["risk_level"]
    assert sender_contribution["contribution_score"] == receiver_contribution["contribution_score"]


def test_missing_safeguard_contributes_to_both_roles():
    result = RiskAnalyzer().analyze(
        [],
        missing_clauses=[{"clause_name": "Limitation of Liability", "importance": "HIGH"}],
    )

    for role in ("Sender", "Receiver"):
        assert result["role_risk_scores"][role]["overall_risk_score"] == 70.0
        assert result["role_risk_scores"][role]["contributions"][0]["contribution_type"] == (
            "missing_safeguard"
        )


def test_opposite_party_similarity_does_not_create_false_role_risk(monkeypatch):
    analyzer = RiskAnalyzer()
    monkeypatch.setattr(
        "app.services.risk_analyzer.sbert_model.semantic_scores",
        lambda texts, patterns: _mock_receiver_risk_scores(
            analyzer,
            texts,
            patterns,
            sender_similarity=0.95,
        ),
    )
    clauses = [{
        "clause_text": "The Employee shall indemnify the Company for any and all claims without limitation.",
        "clause_type": "INDEMNITY",
    }]

    receiver_result = analyzer.analyze(clauses, user_type="Receiver")
    sender_result = analyzer.analyze(clauses, user_type="Sender")

    assert receiver_result["overall_risk_score"] > sender_result["overall_risk_score"]
    assert receiver_result["risk_clauses"]
    assert not sender_result["risk_clauses"]


def test_risky_clause_is_a_bounded_excerpt_and_score_aggregates_all_clauses(monkeypatch):
    analyzer = RiskAnalyzer()
    monkeypatch.setattr(
        "app.services.risk_analyzer.sbert_model.semantic_scores",
        lambda texts, patterns: _mock_receiver_risk_scores(analyzer, texts, patterns),
    )
    risky_sentence = (
        "The Employee shall indemnify the Company for any and all claims without limitation. "
        + "Additional contract text that is not part of the flagged excerpt. " * 20
    )

    result = analyzer.analyze(
        [
            {"clause_text": risky_sentence, "clause_type": "INDEMNITY"},
            {"clause_text": "The parties will cooperate in good faith to complete the project."},
        ],
        user_type="Receiver",
    )

    assert len(result["risk_clauses"][0]["clause_text"]) <= 320
    assert "Additional contract text" not in result["risk_clauses"][0]["clause_text"]
    assert "risk_score" not in result["risk_clauses"][0]
    assert 0 <= result["overall_risk_score"] <= 100
    assert result["overall_risk_score"] == 90.0


def test_scores_follow_detected_severity_and_fall_when_a_risky_clause_is_removed(monkeypatch):
    analyzer = RiskAnalyzer()
    monkeypatch.setattr(
        "app.services.risk_analyzer.sbert_model.semantic_scores",
        lambda texts, patterns: [[0.1] * len(patterns) for _ in texts],
    )
    low_clause = {
        "clause_text": "The parties will cooperate in good faith to complete the project."
    }
    medium_clause = {
        "clause_text": "Confidentiality duties continue indefinitely without exceptions."
    }
    high_clause = {
        "clause_text": "The Employee is subject to a five-year non-compete after employment ends."
    }

    low = analyzer.analyze([low_clause], user_type="Receiver")
    medium = analyzer.analyze([medium_clause], user_type="Receiver")
    high = analyzer.analyze([high_clause], user_type="Receiver")
    with_both_risks = analyzer.analyze(
        [high_clause, medium_clause],
        user_type="Receiver",
    )
    after_removing_high_risk = analyzer.analyze(
        [medium_clause],
        user_type="Receiver",
    )

    assert low["overall_risk_score"] < 30
    assert low["risk_level"] == "LOW"
    assert 30 <= medium["overall_risk_score"] < 60
    assert medium["risk_level"] == "MEDIUM"
    assert 60 <= high["overall_risk_score"] < 80
    assert high["risk_level"] == "HIGH"
    assert with_both_risks["overall_risk_score"] > after_removing_high_risk["overall_risk_score"]
    assert with_both_risks["overall_risk_score"] <= 100


def test_keyword_and_semantic_matches_contribute_only_one_clause_risk(monkeypatch):
    analyzer = RiskAnalyzer()
    monkeypatch.setattr(
        "app.services.risk_analyzer.sbert_model.semantic_scores",
        lambda texts, patterns: [[0.95] * len(patterns) for _ in texts],
    )
    indemnity = (
        "The Employee must indemnify the Company for claims without a monetary limit."
    )
    combined_risks = (
        "The Employee must indemnify the Company for claims without a monetary limit "
        "and accepts uncapped liability for any loss."
    )

    single_risk = analyzer.analyze(
        [{"clause_text": indemnity}],
        user_type="Receiver",
    )
    multiple_signals_in_one_clause = analyzer.analyze(
        [{"clause_text": combined_risks}],
        user_type="Receiver",
    )

    assert multiple_signals_in_one_clause["overall_risk_score"] == single_risk["overall_risk_score"]


def test_existing_risk_categories_match_explicit_signals_below_sbert_threshold(monkeypatch):
    analyzer = RiskAnalyzer()
    examples = [
        ("The Employee must indemnify the Company for any claim without a monetary limit.", "INDEMNITY"),
        ("The Employee accepts uncapped liability for every loss arising from the work.", "FINANCIAL_LIABILITY"),
        ("The Employee may not compete or engage in competing business worldwide for five years.", "RESTRAINT"),
        ("The Company may terminate the Employee without advance notice or severance.", "TERMINATION"),
        ("The Company may amend compensation without the Employee's approval.", "UNILATERAL_CHANGE"),
        ("The Employee must protect Company information forever with no exceptions.", "CONFIDENTIALITY"),
        ("The agreement renews automatically for another five-year term.", "RENEWAL"),
        ("The Employee accepts withholding of earned compensation at the Company's discretion.", "PAYMENT"),
        ("The Employee assigns all present and future inventions and intellectual property permanently.", "INTELLECTUAL_PROPERTY"),
    ]
    category_by_text = {text: category for text, category in examples}

    def score_matching_categories(texts, patterns):
        return [
            [
                0.4 if pattern["category"] == category_by_text[text] else 0.1
                for pattern in analyzer.risk_knowledge_base
            ]
            for text in texts
        ]

    monkeypatch.setattr(
        "app.services.risk_analyzer.sbert_model.semantic_scores",
        score_matching_categories,
    )

    result = analyzer.analyze(
        [{"clause_text": text} for text, _ in examples],
        missing_clauses=[],
        user_type="Receiver",
    )

    assert {clause["risk_category"] for clause in result["risk_clauses"]} == {
        category for _, category in examples
    }
    assert len(result["risk_clauses"]) == len(examples)
    assert result["overall_risk_score"] > 0


def test_payment_signal_wins_over_unilateral_semantic_match(monkeypatch):
    analyzer = RiskAnalyzer()
    text = "The Employee accepts withholding of earned compensation at the Company's sole discretion."

    def score_categories(texts, patterns):
        return [[
            0.4 if pattern["category"] == "PAYMENT"
            else 0.9 if pattern["category"] == "UNILATERAL_CHANGE"
            else 0.1
            for pattern in analyzer.risk_knowledge_base
        ]]

    monkeypatch.setattr(
        "app.services.risk_analyzer.sbert_model.semantic_scores",
        score_categories,
    )

    result = analyzer.analyze([{"clause_text": text}], user_type="Receiver")

    assert result["risk_clauses"][0]["risk_category"] == "PAYMENT"


def test_severe_explicit_risks_are_role_specific_without_score_saturation(monkeypatch):
    analyzer = RiskAnalyzer()
    risky_clauses = [
        ("The Employee must indemnify the Company for any claim without a monetary limit.", "INDEMNITY"),
        ("The Employee accepts uncapped liability for all employment-related losses.", "FINANCIAL_LIABILITY"),
        ("The Employee may not compete anywhere worldwide for five years after employment.", "RESTRAINT"),
        ("The Company may terminate the Employee immediately without notice or severance.", "TERMINATION"),
        ("The Company may amend compensation without the Employee's approval.", "UNILATERAL_CHANGE"),
        ("The Employee's confidentiality duties continue forever without exceptions.", "CONFIDENTIALITY"),
        ("This agreement renews automatically for another five-year term.", "RENEWAL"),
        ("The Company may withhold the Employee's earned salary at its discretion.", "PAYMENT"),
        ("The Employee assigns all present and future inventions and intellectual property permanently.", "INTELLECTUAL_PROPERTY"),
        ("The Company must indemnify the Employee for any claim without a monetary limit.", "INDEMNITY"),
        ("The Company accepts uncapped liability for all losses.", "FINANCIAL_LIABILITY"),
        ("The Employee may terminate the agreement immediately without advance notice.", "TERMINATION"),
        ("The Company must pay disproportionate penalties under this agreement.", "PAYMENT"),
    ]
    category_by_text = {text: category for text, category in risky_clauses}

    def low_semantic_scores(texts, patterns):
        return [
            [
                0.4 if pattern["category"] == category_by_text.get(text) else 0.1
                for pattern in analyzer.risk_knowledge_base
            ]
            for text in texts
        ]

    monkeypatch.setattr(
        "app.services.risk_analyzer.sbert_model.semantic_scores",
        low_semantic_scores,
    )
    clauses = [{"clause_text": text} for text, _ in risky_clauses]
    clauses.extend(
        {"clause_text": f"The parties will cooperate to complete routine task number {index}."}
        for index in range(20)
    )

    receiver = analyzer.analyze(clauses, user_type="Receiver")
    sender = analyzer.analyze(clauses, user_type="Sender")

    assert receiver["overall_risk_score"] > 0
    assert sender["overall_risk_score"] > 0
    assert receiver["overall_risk_score"] < 100
    assert sender["overall_risk_score"] < 100
    assert receiver["risk_clauses"]
    assert sender["risk_clauses"]
    assert receiver["risk_clauses"] != sender["risk_clauses"]
    assert receiver["sbert_ran"] is sender["sbert_ran"] is True


def test_pdf_glyph_normalization_is_used_for_matching_and_preserves_display_text(monkeypatch):
    analyzer = RiskAnalyzer()
    original = "Conﬁden Ɵality obligations survive indeﬁnitely."
    normalized_inputs = []

    def low_similarity(texts, patterns):
        normalized_inputs.extend(texts)
        return [[0.1] * len(patterns) for _ in texts]

    monkeypatch.setattr(
        "app.services.risk_analyzer.sbert_model.semantic_scores",
        low_similarity,
    )

    result = analyzer.analyze([{"clause_text": original}], user_type="Receiver")

    assert normalized_inputs == ["Confidentiality obligations survive indefinitely."]
    assert result["risk_clauses"][0]["clause_text"] == original
    assert result["risk_clauses"][0]["risk_category"] == "CONFIDENTIALITY"


def test_financial_liability_signal_matches_limitation_variant(monkeypatch):
    analyzer = RiskAnalyzer()
    text = "The Employee is responsible for all losses and damages without limitation."
    monkeypatch.setattr(
        "app.services.risk_analyzer.sbert_model.semantic_scores",
        lambda texts, patterns: [[0.1] * len(patterns)],
    )

    result = analyzer.analyze([{"clause_text": text}], user_type="Receiver")

    assert result["risk_clauses"][0]["risk_category"] == "FINANCIAL_LIABILITY"


def test_upload_role_is_applied_to_same_contract(tmp_path, monkeypatch):
    monkeypatch.setenv("CONTRACTAI_UPLOAD_DIR", str(tmp_path))
    analyzer = analysis_router.risk_analyzer
    monkeypatch.setattr(
        "app.services.risk_analyzer.sbert_model.semantic_scores",
        lambda texts, patterns: _mock_receiver_risk_scores(analyzer, texts, patterns),
    )
    monkeypatch.setattr(analysis_router.missing_clause_detector, "detect", lambda *args: [])
    monkeypatch.setattr(analysis_router.law_mapper, "map_laws", lambda clauses: [])
    monkeypatch.setattr(analysis_router.summary_generator, "generate_summary", lambda text: "")
    contract_text = "The Employee shall indemnify the Company for all claims without limitation."
    results = {}

    for role in ("Receiver", "Sender"):
        response = client.post(
            "/ai/analyze",
            data={
                "contract_type": "Employment",
                "contract_id": f"role-{role}",
                "user_type": role,
            },
            files={"file": ("employment.txt", contract_text, "text/plain")},
        )
        assert response.status_code == 200
        results[role] = response.json()

    assert results["Receiver"]["overall_risk_score"] > results["Sender"]["overall_risk_score"]
    assert results["Receiver"]["risk_clauses"] != results["Sender"]["risk_clauses"]
    assert results["Receiver"]["user_type"] == "Receiver"
    assert results["Sender"]["user_type"] == "Sender"
    assert set(results["Receiver"]["role_risk_scores"]) == {"Sender", "Receiver"}
    assert results["Receiver"]["overall_risk_score"] == (
        results["Receiver"]["role_risk_scores"]["Receiver"]["overall_risk_score"]
    )
    assert results["Receiver"]["legal_corpus_status"]["status"] == "empty"


def test_sbert_model_caches_static_pattern_embeddings(monkeypatch):
    encode_calls = []

    class Similarities:
        def cpu(self):
            return self

        def tolist(self):
            return [[0.8, 0.2]]

    class FakeModel:
        def encode(self, texts, **kwargs):
            encode_calls.append(tuple(texts))
            return texts

    fake_util = SimpleNamespace(cos_sim=lambda texts, patterns: Similarities())
    monkeypatch.setitem(
        sys.modules,
        "sentence_transformers",
        SimpleNamespace(util=fake_util),
    )
    model = SBERTModel()
    model._model = FakeModel()

    model.semantic_scores(["first clause"], ["risk pattern a", "risk pattern b"])
    model.semantic_scores(["second clause"], ["risk pattern a", "risk pattern b"])

    assert encode_calls == [
        ("risk pattern a", "risk pattern b"),
        ("first clause",),
        ("second clause",),
    ]
