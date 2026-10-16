import logging
import os
import time
import uuid
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from app.services.document_parser import document_parser
from app.services.clause_extractor import clause_extractor
from app.services.risk_analyzer import risk_analyzer
from app.services.missing_clause_detector import missing_clause_detector
from app.services.law_mapper import law_mapper
from app.services.summary_generator import summary_generator

router = APIRouter(prefix="/ai", tags=["analysis"])
logger = logging.getLogger(__name__)


@router.post("/analyze")
async def analyze_contract(
    file: UploadFile = File(...),
    contract_type: str = Form(...),
    contract_id: str = Form(...),
    user_type: Optional[str] = Form(None),
):
    start_time = time.time()
    received_user_type = user_type
    logger.warning(
        "ROLE_DEBUG_REQUEST: contract_id=%s received_role=%r",
        contract_id,
        received_user_type if received_user_type is not None else "<missing>",
    )
    if user_type is None:
        user_type = "Receiver"
    if user_type not in {"Sender", "Receiver"}:
        raise HTTPException(status_code=422, detail="User type must be Sender or Receiver.")

    upload_dir = os.environ.get("CONTRACTAI_UPLOAD_DIR", "/app/uploads")
    os.makedirs(upload_dir, exist_ok=True)

    safe_filename = os.path.basename(file.filename or "contract.pdf")
    file_path = os.path.join(upload_dir, f"{uuid.uuid4()}_{safe_filename}")

    try:
        with open(file_path, "wb") as buffer:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                buffer.write(chunk)

        file_ext = os.path.splitext(safe_filename)[1].lower()

        if file_ext == ".pdf":
            file_type = "PDF"
        elif file_ext == ".docx":
            file_type = "DOCX"
        elif file_ext in [".png", ".jpg", ".jpeg"]:
            file_type = "IMAGE"
        elif file_ext == ".txt":
            file_type = "TXT"
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type"
            )

        try:
            text = document_parser.parse_document(file_path, file_type)
        except (OSError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=f"Document extraction failed: {exc}") from exc

        if not text.strip():
            raise HTTPException(status_code=422, detail="Document extraction failed: no text found in the uploaded file.")

        clauses = clause_extractor.extract_clauses(text)
        missing = missing_clause_detector.detect(
            clauses,
            contract_type
        )
        try:
            logger.warning(
                "ROLE_DEBUG_ANALYSIS: contract_id=%s role_passed_to_risk_analyzer=%r clauses=%d",
                contract_id,
                user_type,
                len(clauses),
            )
            risk_result = risk_analyzer.analyze(
                clauses,
                missing_clauses=missing,
                contract_type=contract_type,
                user_type=user_type,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        law_result = law_mapper.map_laws_with_status(clauses)
        laws = law_result["matches"]

        summary = summary_generator.generate_summary(text)
        metrics = {
            "extracted_text_chars": len(text),
            "clauses_count": len(clauses),
            "risky_clauses_count": len(risk_result["risk_clauses"]),
            "sbert_ran": risk_result["sbert_ran"],
            "llm_ran": risk_result["llm_ran"],
            "warnings": risk_result["warnings"],
        }
        logger.warning(
            "Contract analysis complete: contract_id=%s user_type=%s text_chars=%d clauses=%d risky_clauses=%d "
            "sbert_ran=%s llm_ran=%s final_score=%.1f",
            contract_id,
            user_type,
            metrics["extracted_text_chars"],
            metrics["clauses_count"],
            metrics["risky_clauses_count"],
            metrics["sbert_ran"],
            metrics["llm_ran"],
            risk_result["overall_risk_score"],
        )

        return {
            "status": "success",
            "contract_id": contract_id,
            "user_type": user_type,
            "extracted_text": text,
            "overall_risk_score": risk_result["overall_risk_score"],
            "risk_level": risk_result["risk_level"],
            "role_risk_scores": risk_result["role_risk_scores"],
            "summary": summary,
            "total_clauses_found": len(clauses),
            "risky_clauses_count": len(risk_result["risk_clauses"]),
            "missing_clauses_count": len(missing),
            "risk_clauses": risk_result["risk_clauses"],
            "missing_clauses": missing,
            "applicable_laws": laws,
            "legal_corpus_status": law_result["legal_corpus_status"],
            "legal_disclaimer": law_result["legal_disclaimer"],
            "analysis_metrics": metrics,
            "processing_time_ms": int(
                (time.time() - start_time) * 1000
            )
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)