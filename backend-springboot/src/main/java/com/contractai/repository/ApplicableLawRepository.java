package com.contractai.repository;

import com.contractai.model.ApplicableLaw;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.UUID;

public interface ApplicableLawRepository extends JpaRepository<ApplicableLaw, UUID> {
    List<ApplicableLaw> findByAnalysisId(UUID analysisId);
}
