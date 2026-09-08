package com.contractai.repository;

import com.contractai.model.MissingClause;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.UUID;

public interface MissingClauseRepository extends JpaRepository<MissingClause, UUID> {
    List<MissingClause> findByAnalysisId(UUID analysisId);
}
