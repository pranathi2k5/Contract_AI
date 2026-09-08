package com.contractai.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Map;
import java.util.List;
import com.contractai.model.RiskClause;
import com.contractai.model.MissingClause;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DashboardResponse {
    private Double overallRiskScore;
    private String riskLevel;
    private Map<String, Long> riskDistribution;
    private Integer totalClauses;
    private List<RiskClause> riskyClauses;
    private List<MissingClause> missingClauses;
    private String summary;
}
