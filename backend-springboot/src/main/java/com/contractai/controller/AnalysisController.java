package com.contractai.controller;

import com.contractai.dto.AnalysisResponse;
import com.contractai.dto.DashboardResponse;
import com.contractai.service.AnalysisService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/api/contracts/{id}")
@RequiredArgsConstructor
public class AnalysisController {

    private final AnalysisService analysisService;

    @PostMapping("/analyze")
    public ResponseEntity<AnalysisResponse> analyzeContract(@PathVariable UUID id, Authentication authentication) {
        return ResponseEntity.ok(analysisService.triggerAnalysis(id, authentication.getName()));
    }

    @GetMapping("/analysis")
    public ResponseEntity<AnalysisResponse> getAnalysis(@PathVariable UUID id, Authentication authentication) {
        return ResponseEntity.ok(analysisService.getAnalysisResults(id, authentication.getName()));
    }

    @GetMapping("/dashboard")
    public ResponseEntity<DashboardResponse> getDashboard(@PathVariable UUID id, Authentication authentication) {
        return ResponseEntity.ok(analysisService.getDashboardData(id, authentication.getName()));
    }
}
