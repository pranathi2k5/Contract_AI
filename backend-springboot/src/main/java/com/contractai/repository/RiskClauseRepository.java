package com.contractai.repository;

import com.contractai.model.RiskClause;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.UUID;

public interface RiskClauseRepository extends JpaRepository<RiskClause, UUID> {
    List<RiskClause> findByAnalysisId(UUID analysisId);
}
