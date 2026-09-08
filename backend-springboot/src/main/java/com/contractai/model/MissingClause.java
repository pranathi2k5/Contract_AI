package com.contractai.model;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;

import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "missing_clauses")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class MissingClause {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "analysis_id", nullable = false)
    private AnalysisResult analysis;

    @Column(name = "clause_name", nullable = false, length = 255)
    private String clauseName;

    @Column(nullable = false, length = 20)
    private String importance;

    @Column(columnDefinition = "TEXT")
    private String description;

    @Column(name = "template_text", columnDefinition = "TEXT")
    private String templateText;

    @Column(name = "max_similarity_score", precision = 5, scale = 4)
    private Double maxSimilarityScore;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private OffsetDateTime createdAt;
}
