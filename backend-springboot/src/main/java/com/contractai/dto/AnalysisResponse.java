package com.contractai.dto;

import com.contractai.model.AnalysisResult;
import com.contractai.model.ApplicableLaw;
import com.contractai.model.MissingClause;
import com.contractai.model.RiskClause;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AnalysisResponse {
    private AnalysisResult result;
    private List<RiskClause> riskClauses;
    private List<MissingClause> missingClauses;
    private List<ApplicableLaw> applicableLaws;
}
