package com.contractai.model;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;

import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "applicable_laws")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ApplicableLaw {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "analysis_id", nullable = false)
    private AnalysisResult analysis;

    @Column(name = "clause_id")
    private UUID clauseId;

    @Column(name = "clause_text", columnDefinition = "TEXT")
    private String clauseText;

    @Column(name = "law_name", nullable = false, length = 500)
    private String lawName;

    @Column(name = "act_name", nullable = false, length = 500)
    private String actName;

    @Column(name = "section_number", length = 100)
    private String sectionNumber;

    @Column(name = "section_title", length = 500)
    private String sectionTitle;

    @Column(name = "relevance_score", precision = 5, scale = 2)
    private Double relevanceScore;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String reason;

    @Column(length = 500)
    private String source;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private OffsetDateTime createdAt;
}
