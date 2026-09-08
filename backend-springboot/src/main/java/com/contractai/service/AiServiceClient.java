package com.contractai.service;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;

import java.util.Map;

@Service
@RequiredArgsConstructor
public class AiServiceClient {

    private final WebClient webClient;

    public Map<String, Object> analyzeContract(String contractText, String contractType, String userRole) {
        return webClient.post()
                .uri("/ai/analyze")
                .bodyValue(Map.of(
                        "contractText", contractText,
                        "contractType", contractType != null ? contractType : "unknown",
                        "userRole", userRole
                ))
                .retrieve()
                .bodyToMono(Map.class)
                .block();
    }

    public Map<String, Object> chat(String message, String context) {
        return webClient.post()
                .uri("/ai/chat")
                .bodyValue(Map.of(
                        "message", message,
                        "context", context != null ? context : ""
                ))
                .retrieve()
                .bodyToMono(Map.class)
                .block();
    }
}
