package com.contractai.service;

import com.contractai.dto.AnalysisResponse;
import com.contractai.dto.DashboardResponse;
import com.contractai.exception.ResourceNotFoundException;
import com.contractai.model.*;
import com.contractai.repository.*;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.OffsetDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class AnalysisService {

    private final ContractRepository contractRepository;
    private final AnalysisResultRepository analysisResultRepository;
    private final RiskClauseRepository riskClauseRepository;
    private final MissingClauseRepository missingClauseRepository;
    private final ApplicableLawRepository applicableLawRepository;
    private final AiServiceClient aiServiceClient;

    public AnalysisResponse triggerAnalysis(UUID contractId, String userEmail) {
        Contract contract = contractRepository.findById(contractId)
                .orElseThrow(() -> new ResourceNotFoundException("Contract not found"));

        contract.setStatus("PROCESSING");
        contractRepository.save(contract);

        try {
            Map<String, Object> aiResponse = aiServiceClient.analyzeContract(
                    contract.getFilePath(),
                    contract.getFileType(),
                    contract.getContractType(),
                    contract.getId().toString()
            );

            if (aiResponse.get("summary") != null) {
                contract.setExtractedText(String.valueOf(aiResponse.get("summary")));
            }

            AnalysisResult result = AnalysisResult.builder()
                    .contract(contract)
                    .overallRiskScore(toDouble(aiResponse.get("overall_risk_score"), 0.0))
                    .riskLevel(stringOrDefault(aiResponse.get("risk_level"), "LOW"))
                    .summary(stringOrDefault(aiResponse.get("summary"), ""))
                    .contractTypeDetected(contract.getContractType())
                    .totalClausesFound(toInt(aiResponse.get("total_clauses_found"), 0))
                    .riskyClausesCount(toInt(aiResponse.get("risky_clauses_count"), 0))
                    .missingClausesCount(toInt(aiResponse.get("missing_clauses_count"), 0))
                    .modelUsed("sbert-minilm")
                    .processingTimeMs(toInt(aiResponse.get("processing_time_ms"), 0))
                    .build();
            analysisResultRepository.save(result);

            contract.setStatus("ANALYZED");
            contract.setAnalyzedAt(OffsetDateTime.now());
            contractRepository.save(contract);

            return getAnalysisResults(contractId, userEmail);

        } catch (Exception e) {
            contract.setStatus("FAILED");
            contractRepository.save(contract);
            throw new RuntimeException("Analysis failed: " + e.getMessage());
        }
    }

    public AnalysisResponse getAnalysisResults(UUID contractId, String userEmail) {
        AnalysisResult result = analysisResultRepository.findByContractId(contractId)
                .orElseThrow(() -> new ResourceNotFoundException("Analysis result not found"));

        List<RiskClause> riskClauses = riskClauseRepository.findByAnalysisId(result.getId());
        List<MissingClause> missingClauses = missingClauseRepository.findByAnalysisId(result.getId());
        List<ApplicableLaw> applicableLaws = applicableLawRepository.findByAnalysisId(result.getId());

        return AnalysisResponse.builder()
                .result(result)
                .riskClauses(riskClauses)
                .missingClauses(missingClauses)
                .applicableLaws(applicableLaws)
                .build();
    }

    public DashboardResponse getDashboardData(UUID contractId, String userEmail) {
        AnalysisResponse analysis = getAnalysisResults(contractId, userEmail);
        AnalysisResult result = analysis.getResult();

        Map<String, Long> riskDist = new HashMap<>();
        for (RiskClause rc : analysis.getRiskClauses()) {
            riskDist.put(rc.getRiskCategory(), riskDist.getOrDefault(rc.getRiskCategory(), 0L) + 1);
        }

        return DashboardResponse.builder()
                .overallRiskScore(result.getOverallRiskScore())
                .riskLevel(result.getRiskLevel())
                .riskDistribution(riskDist)
                .totalClauses(result.getTotalClausesFound())
                .riskyClauses(analysis.getRiskClauses())
                .missingClauses(analysis.getMissingClauses())
                .summary(result.getSummary())
                .build();
    }

    private double toDouble(Object value, double fallback) {
        if (value instanceof Number) {
            return ((Number) value).doubleValue();
        }
        if (value != null) {
            try {
                return Double.parseDouble(String.valueOf(value));
            } catch (NumberFormatException ignored) {
                return fallback;
            }
        }
        return fallback;
    }

    private int toInt(Object value, int fallback) {
        return (int) Math.round(toDouble(value, fallback));
    }

    private String stringOrDefault(Object value, String fallback) {
        return value == null ? fallback : String.valueOf(value);
    }
}
