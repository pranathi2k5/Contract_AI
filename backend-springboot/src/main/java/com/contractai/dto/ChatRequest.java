package com.contractai.dto;

import lombok.Data;
import java.util.UUID;

@Data
public class ChatRequest {
    private String message;
    private UUID contractId;
    private UUID sessionId;
}
