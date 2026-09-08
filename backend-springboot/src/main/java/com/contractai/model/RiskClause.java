package com.contractai.model;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;

import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "risk_clauses")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RiskClause {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "analysis_id", nullable = false)
    private AnalysisResult analysis;

    @Column(name = "clause_id")
    private UUID clauseId;

    @Column(name = "clause_text", nullable = false, columnDefinition = "TEXT")
    private String clauseText;

    @Column(name = "clause_type", nullable = false, length = 100)
    private String clauseType;

    @Column(name = "risk_score", nullable = false, precision = 5, scale = 2)
    private Double riskScore;

    @Column(name = "risk_category", nullable = false, length = 50)
    private String riskCategory;

    @Column(nullable = false, length = 20)
    private String severity;

    @Column(columnDefinition = "TEXT")
    private String explanation;

    @Column(columnDefinition = "TEXT")
    private String suggestion;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private OffsetDateTime createdAt;
}
