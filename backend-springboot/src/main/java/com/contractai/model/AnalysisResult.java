package com.contractai.model;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;

import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "analysis_results")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AnalysisResult {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "contract_id", nullable = false)
    private Contract contract;

    @Column(name = "overall_risk_score", nullable = false, precision = 5, scale = 2)
    private Double overallRiskScore;

    @Column(name = "risk_level", nullable = false, length = 20)
    private String riskLevel;

    @Column(columnDefinition = "TEXT")
    private String summary;

    @Column(name = "contract_type_detected", length = 100)
    private String contractTypeDetected;

    @Column(name = "total_clauses_found")
    private Integer totalClausesFound;

    @Column(name = "risky_clauses_count")
    private Integer riskyClausesCount;

    @Column(name = "missing_clauses_count")
    private Integer missingClausesCount;

    @Column(name = "model_used", length = 200)
    private String modelUsed;

    @Column(name = "processing_time_ms")
    private Integer processingTimeMs;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private OffsetDateTime createdAt;
}
