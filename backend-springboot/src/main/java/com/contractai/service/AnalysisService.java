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

        // Dummy text extraction for now
        String text = "Sample extracted contract text";
        contract.setExtractedText(text);

        try {
            Map<String, Object> aiResponse = aiServiceClient.analyzeContract(text, contract.getContractType(), contract.getUserRole());
            
            // In a real scenario, map the aiResponse fields to the models
            AnalysisResult result = AnalysisResult.builder()
                    .contract(contract)
                    .overallRiskScore(25.0)
                    .riskLevel("LOW")
                    .summary("Sample AI summary")
                    .contractTypeDetected("NDA")
                    .totalClausesFound(10)
                    .riskyClausesCount(1)
                    .missingClausesCount(0)
                    .modelUsed("gpt-4")
                    .processingTimeMs(2000)
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
}
