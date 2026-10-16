from typing import List, Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class AnalysisResultBase(BaseModel):
    overall_risk_score: float
    risk_level: str
    summary: Optional[str] = None
    contract_type_detected: Optional[str] = None
    total_clauses_found: int = 0
    risky_clauses_count: int = 0
    missing_clauses_count: int = 0

class AnalysisResultCreate(AnalysisResultBase):
    contract_id: UUID
    model_used: Optional[str] = None
    processing_time_ms: Optional[int] = None

class RiskClauseSchema(BaseModel):
    clause_text: str
    clause_type: str
    risk_score: float
    risk_category: str
    severity: str
    explanation: Optional[str] = None
    suggestion: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class MissingClauseSchema(BaseModel):
    clause_name: str
    importance: str
    description: Optional[str] = None
    template_text: Optional[str] = None
    max_similarity_score: float
    
    model_config = ConfigDict(from_attributes=True)

class ApplicableLawSchema(BaseModel):
    clause_text: Optional[str] = None
    law_name: str
    act_name: str
    section_number: Optional[str] = None
    section_title: Optional[str] = None
    relevance_score: float
    reason: str
    source: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class FullAnalysisResponse(AnalysisResultBase):
    id: UUID
    contract_id: UUID
    risk_clauses: List[RiskClauseSchema] = []
    missing_clauses: List[MissingClauseSchema] = []
    applicable_laws: List[ApplicableLawSchema] = []
    
    model_config = ConfigDict(from_attributes=True)

class ChatMessageRequest(BaseModel):
    message: str
    contract_context: Optional[str] = None

class ChatMessageResponse(BaseModel):
    role: str
    content: str
    sources: Optional[List[dict]] = None
