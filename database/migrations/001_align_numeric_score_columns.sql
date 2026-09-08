-- Apply this migration to an existing PostgreSQL database before deploying
-- the Spring Boot application with spring.jpa.hibernate.ddl-auto=validate.

ALTER TABLE analysis_results
    ALTER COLUMN overall_risk_score TYPE NUMERIC(5, 2)
    USING overall_risk_score::NUMERIC(5, 2);

ALTER TABLE risk_clauses
    ALTER COLUMN risk_score TYPE NUMERIC(5, 2)
    USING risk_score::NUMERIC(5, 2);

ALTER TABLE missing_clauses
    ALTER COLUMN max_similarity_score TYPE NUMERIC(5, 4)
    USING max_similarity_score::NUMERIC(5, 4);

ALTER TABLE applicable_laws
    ALTER COLUMN relevance_score TYPE NUMERIC(5, 2)
    USING relevance_score::NUMERIC(5, 2);