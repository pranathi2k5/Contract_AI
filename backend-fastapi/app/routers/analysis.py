from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import time
from app.database import get_db
from app.models.schemas import FullAnalysisResponse
from app.services.document_parser import document_parser
from app.services.clause_extractor import clause_extractor
from app.services.risk_analyzer import risk_analyzer
from app.services.missing_clause_detector import missing_clause_detector
from app.services.law_mapper import law_mapper
from app.services.summary_generator import summary_generator

router = APIRouter(prefix="/ai", tags=["analysis"])

@router.post("/analyze", response_model=dict)
async def analyze_contract(file_path: str, file_type: str, contract_type: str, contract_id: str, db: AsyncSession = Depends(get_db)):
    start_time = time.time()
    try:
        # 1. Parse document text
        text = document_parser.parse_document(file_path, file_type)
        if not text:
            raise HTTPException(status_code=400, detail="Could not parse document.")
            
        # 2. Extract and classify clauses
        clauses = clause_extractor.extract_clauses(text)
        
        # 3. Score risks
        risk_result = risk_analyzer.analyze(clauses)
        
        # 4. Detect missing clauses
        missing = missing_clause_detector.detect(clauses, contract_type)
        
        # 5. Map applicable Indian laws
        laws = law_mapper.map_laws(clauses)
        
        # 6. Generate summary
        summary = summary_generator.generate_summary(text)
        
        # 7. Mock Saving to Postgres (would use DB session here)
        processing_time = int((time.time() - start_time) * 1000)
        
        return {
            "status": "success",
            "contract_id": contract_id,
            "overall_risk_score": risk_result["overall_risk_score"],
            "risk_level": risk_result["risk_level"],
            "summary": summary,
            "total_clauses_found": len(clauses),
            "risky_clauses_count": len(risk_result["risk_clauses"]),
            "missing_clauses_count": len(missing),
            "risk_clauses": risk_result["risk_clauses"],
            "missing_clauses": missing,
            "applicable_laws": laws,
            "processing_time_ms": processing_time
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
