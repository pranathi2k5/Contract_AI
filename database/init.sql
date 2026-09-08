-- ============================================================
-- ContractAI Database Schema
-- PostgreSQL 16
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============ USERS & AUTH ============
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);

-- ============ CONTRACTS ============
CREATE TABLE contracts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500),
    file_name VARCHAR(500) NOT NULL,
    file_type VARCHAR(20) NOT NULL CHECK (file_type IN ('PDF', 'DOCX', 'IMAGE')),
    file_path VARCHAR(1000) NOT NULL,
    extracted_text TEXT,
    contract_type VARCHAR(100), -- 'employment', 'nda', 'sales', 'service', 'rental_lease'
    user_role VARCHAR(20) NOT NULL DEFAULT 'SENDER' CHECK (user_role IN ('SENDER', 'RECEIVER')),
    status VARCHAR(30) DEFAULT 'UPLOADED' CHECK (status IN ('UPLOADED', 'PROCESSING', 'ANALYZED', 'FAILED')),
    party_a VARCHAR(500),
    party_b VARCHAR(500),
    uploaded_at TIMESTAMPTZ DEFAULT NOW(),
    analyzed_at TIMESTAMPTZ
);

CREATE INDEX idx_contracts_user ON contracts(user_id);
CREATE INDEX idx_contracts_status ON contracts(status);
CREATE INDEX idx_contracts_type ON contracts(contract_type);

-- ============ CLAUSE TYPES (reference table) ============
CREATE TABLE clause_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) UNIQUE NOT NULL,
    description TEXT,
    is_mandatory BOOLEAN DEFAULT FALSE,
    category VARCHAR(100),
    applicable_contract_types TEXT[] DEFAULT '{}'
);

-- Seed clause types
INSERT INTO clause_types (name, description, is_mandatory, category, applicable_contract_types) VALUES
('Indemnification', 'Clause protecting one party from losses caused by the other party', TRUE, 'liability', '{"employment","nda","sales","service","rental_lease"}'),
('Termination', 'Conditions under which the contract can be ended', TRUE, 'termination', '{"employment","nda","sales","service","rental_lease"}'),
('Confidentiality', 'Obligations to protect confidential information', TRUE, 'obligation', '{"employment","nda","service"}'),
('Non-Compete', 'Restrictions on competing activities after contract ends', FALSE, 'restriction', '{"employment","nda"}'),
('Non-Solicitation', 'Restrictions on soliciting employees or clients', FALSE, 'restriction', '{"employment","nda"}'),
('Limitation of Liability', 'Caps on the amount of damages a party can claim', TRUE, 'liability', '{"sales","service","rental_lease"}'),
('Force Majeure', 'Excuses performance due to extraordinary events', TRUE, 'termination', '{"employment","sales","service","rental_lease"}'),
('Governing Law', 'Specifies which jurisdiction laws govern the contract', TRUE, 'jurisdiction', '{"employment","nda","sales","service","rental_lease"}'),
('Dispute Resolution', 'Mechanism for resolving disputes (arbitration, mediation, litigation)', TRUE, 'jurisdiction', '{"employment","nda","sales","service","rental_lease"}'),
('Payment Terms', 'Terms and schedule for payments', TRUE, 'financial', '{"sales","service","rental_lease"}'),
('Warranty', 'Guarantees about the quality or condition of goods/services', TRUE, 'obligation', '{"sales","service"}'),
('Intellectual Property', 'Ownership and rights over IP created during the contract', TRUE, 'obligation', '{"employment","nda","service"}'),
('Assignment', 'Rights to transfer obligations to a third party', FALSE, 'obligation', '{"employment","sales","service","rental_lease"}'),
('Entire Agreement', 'States that the written contract is the complete agreement', FALSE, 'general', '{"employment","nda","sales","service","rental_lease"}'),
('Severability', 'If one clause is invalid, the rest of the contract remains valid', FALSE, 'general', '{"employment","nda","sales","service","rental_lease"}'),
('Notice', 'How parties must communicate formal notices', FALSE, 'obligation', '{"employment","sales","service","rental_lease"}'),
('Insurance', 'Requirements for insurance coverage', FALSE, 'obligation', '{"service","rental_lease"}'),
('Renewal', 'Terms for contract renewal or extension', FALSE, 'termination', '{"employment","service","rental_lease"}'),
('Data Protection', 'Obligations regarding personal data handling (DPDP Act)', TRUE, 'compliance', '{"employment","nda","service"}'),
('Penalty Clause', 'Penalties for breach or non-performance', FALSE, 'financial', '{"sales","service","rental_lease"}'),
('Security Deposit', 'Deposit amount and refund conditions', TRUE, 'financial', '{"rental_lease"}'),
('Maintenance and Repairs', 'Responsibilities for property maintenance', TRUE, 'obligation', '{"rental_lease"}'),
('Subletting', 'Rights or restrictions on subletting the property', FALSE, 'restriction', '{"rental_lease"}'),
('Delivery Terms', 'Terms for delivery of goods', TRUE, 'obligation', '{"sales"}'),
('Return and Refund', 'Policy for returns and refunds', TRUE, 'financial', '{"sales"}'),
('Scope of Work', 'Detailed description of services to be provided', TRUE, 'obligation', '{"service"}'),
('Service Level Agreement', 'Performance standards and metrics', FALSE, 'obligation', '{"service"}'),
('Probation Period', 'Trial period terms for employment', TRUE, 'obligation', '{"employment"}'),
('Leave Policy', 'Types and duration of leaves available', TRUE, 'obligation', '{"employment"}'),
('Compensation and Benefits', 'Salary, bonuses, and benefits details', TRUE, 'financial', '{"employment"}');

-- ============ EXTRACTED CLAUSES ============
CREATE TABLE clauses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id UUID NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,
    clause_type_id UUID REFERENCES clause_types(id),
    clause_text TEXT NOT NULL,
    section_number VARCHAR(50),
    confidence_score DECIMAL(5,4) DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_clauses_contract ON clauses(contract_id);
CREATE INDEX idx_clauses_type ON clauses(clause_type_id);

-- ============ ANALYSIS RESULTS ============
CREATE TABLE analysis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id UUID NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,
    overall_risk_score DECIMAL(5,2) NOT NULL DEFAULT 0.0,
    risk_level VARCHAR(20) NOT NULL DEFAULT 'LOW' CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    summary TEXT,
    contract_type_detected VARCHAR(100),
    total_clauses_found INTEGER DEFAULT 0,
    risky_clauses_count INTEGER DEFAULT 0,
    missing_clauses_count INTEGER DEFAULT 0,
    model_used VARCHAR(200),
    processing_time_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_analysis_contract ON analysis_results(contract_id);

-- ============ RISK CLAUSES ============
CREATE TABLE risk_clauses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID NOT NULL REFERENCES analysis_results(id) ON DELETE CASCADE,
    clause_id UUID REFERENCES clauses(id) ON DELETE SET NULL,
    clause_text TEXT NOT NULL,
    clause_type VARCHAR(100) NOT NULL,
    risk_score DECIMAL(5,2) NOT NULL DEFAULT 0.0,
    risk_category VARCHAR(50) NOT NULL CHECK (risk_category IN ('FINANCIAL', 'LEGAL', 'OPERATIONAL', 'COMPLIANCE')),
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    explanation TEXT,
    suggestion TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_risk_clauses_analysis ON risk_clauses(analysis_id);

-- ============ MISSING CLAUSES ============
CREATE TABLE missing_clauses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID NOT NULL REFERENCES analysis_results(id) ON DELETE CASCADE,
    clause_name VARCHAR(255) NOT NULL,
    importance VARCHAR(20) NOT NULL CHECK (importance IN ('CRITICAL', 'IMPORTANT', 'RECOMMENDED')),
    description TEXT,
    template_text TEXT,
    max_similarity_score DECIMAL(5,4) DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_missing_clauses_analysis ON missing_clauses(analysis_id);

-- ============ APPLICABLE LAWS (clause-level mapping) ============
CREATE TABLE applicable_laws (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID NOT NULL REFERENCES analysis_results(id) ON DELETE CASCADE,
    clause_id UUID REFERENCES clauses(id) ON DELETE SET NULL,
    clause_text TEXT,
    law_name VARCHAR(500) NOT NULL,
    act_name VARCHAR(500) NOT NULL,
    section_number VARCHAR(100),
    section_title VARCHAR(500),
    relevance_score DECIMAL(5,2) DEFAULT 0.0,
    reason TEXT NOT NULL,
    source VARCHAR(500),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_applicable_laws_analysis ON applicable_laws(analysis_id);

-- ============ CHAT SESSIONS & MESSAGES ============
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    contract_id UUID REFERENCES contracts(id) ON DELETE SET NULL,
    title VARCHAR(500) DEFAULT 'New Chat',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_chat_sessions_user ON chat_sessions(user_id);

CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    sources JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_chat_messages_session ON chat_messages(session_id);

-- ============ TRIGGER: Update timestamps ============
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_chat_sessions_updated_at
    BEFORE UPDATE ON chat_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
