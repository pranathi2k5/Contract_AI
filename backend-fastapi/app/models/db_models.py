import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, Integer, Numeric, ForeignKey, DateTime, JSON, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    contracts = relationship("Contract", back_populates="user", cascade="all, delete")

class Contract(Base):
    __tablename__ = 'contracts'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = Column(String(500))
    file_name = Column(String(500), nullable=False)
    file_type = Column(String(20), nullable=False)
    file_path = Column(String(1000), nullable=False)
    extracted_text = Column(Text)
    contract_type = Column(String(100))
    user_role = Column(String(20), default='SENDER', nullable=False)
    status = Column(String(30), default='UPLOADED')
    party_a = Column(String(500))
    party_b = Column(String(500))
    uploaded_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    analyzed_at = Column(DateTime(timezone=True))

    user = relationship("User", back_populates="contracts")
    clauses = relationship("Clause", back_populates="contract", cascade="all, delete")
    analysis_results = relationship("AnalysisResult", back_populates="contract", cascade="all, delete")

class ClauseType(Base):
    __tablename__ = 'clause_types'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), unique=True, nullable=False)
    description = Column(Text)
    is_mandatory = Column(Boolean, default=False)
    category = Column(String(100))
    applicable_contract_types = Column(ARRAY(String))

class Clause(Base):
    __tablename__ = 'clauses'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey('contracts.id', ondelete='CASCADE'), nullable=False)
    clause_type_id = Column(UUID(as_uuid=True), ForeignKey('clause_types.id'))
    clause_text = Column(Text, nullable=False)
    section_number = Column(String(50))
    confidence_score = Column(Numeric(5, 4), default=0.0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    contract = relationship("Contract", back_populates="clauses")
    clause_type = relationship("ClauseType")

class AnalysisResult(Base):
    __tablename__ = 'analysis_results'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey('contracts.id', ondelete='CASCADE'), nullable=False)
    overall_risk_score = Column(Numeric(5, 2), default=0.0, nullable=False)
    risk_level = Column(String(20), default='LOW', nullable=False)
    summary = Column(Text)
    contract_type_detected = Column(String(100))
    total_clauses_found = Column(Integer, default=0)
    risky_clauses_count = Column(Integer, default=0)
    missing_clauses_count = Column(Integer, default=0)
    model_used = Column(String(200))
    processing_time_ms = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    contract = relationship("Contract", back_populates="analysis_results")
    risk_clauses = relationship("RiskClause", back_populates="analysis_result", cascade="all, delete")
    missing_clauses = relationship("MissingClause", back_populates="analysis_result", cascade="all, delete")
    applicable_laws = relationship("ApplicableLaw", back_populates="analysis_result", cascade="all, delete")

class RiskClause(Base):
    __tablename__ = 'risk_clauses'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey('analysis_results.id', ondelete='CASCADE'), nullable=False)
    clause_id = Column(UUID(as_uuid=True), ForeignKey('clauses.id', ondelete='SET NULL'))
    clause_text = Column(Text, nullable=False)
    clause_type = Column(String(100), nullable=False)
    risk_score = Column(Numeric(5, 2), default=0.0, nullable=False)
    risk_category = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    explanation = Column(Text)
    suggestion = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    analysis_result = relationship("AnalysisResult", back_populates="risk_clauses")
    clause = relationship("Clause")

class MissingClause(Base):
    __tablename__ = 'missing_clauses'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey('analysis_results.id', ondelete='CASCADE'), nullable=False)
    clause_name = Column(String(255), nullable=False)
    importance = Column(String(20), nullable=False)
    description = Column(Text)
    template_text = Column(Text)
    max_similarity_score = Column(Numeric(5, 4), default=0.0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    analysis_result = relationship("AnalysisResult", back_populates="missing_clauses")

class ApplicableLaw(Base):
    __tablename__ = 'applicable_laws'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey('analysis_results.id', ondelete='CASCADE'), nullable=False)
    clause_id = Column(UUID(as_uuid=True), ForeignKey('clauses.id', ondelete='SET NULL'))
    clause_text = Column(Text)
    law_name = Column(String(500), nullable=False)
    act_name = Column(String(500), nullable=False)
    section_number = Column(String(100))
    section_title = Column(String(500))
    relevance_score = Column(Numeric(5, 2), default=0.0)
    reason = Column(Text, nullable=False)
    source = Column(String(500))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    analysis_result = relationship("AnalysisResult", back_populates="applicable_laws")
    clause = relationship("Clause")

class ChatSession(Base):
    __tablename__ = 'chat_sessions'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    contract_id = Column(UUID(as_uuid=True), ForeignKey('contracts.id', ondelete='SET NULL'))
    title = Column(String(500), default='New Chat')
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

class ChatMessage(Base):
    __tablename__ = 'chat_messages'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('chat_sessions.id', ondelete='CASCADE'), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    sources = Column(JSONB, default=list)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
