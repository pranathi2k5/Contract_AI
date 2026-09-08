package com.contractai.controller;

import com.contractai.dto.ChatRequest;
import com.contractai.dto.ChatResponse;
import com.contractai.model.ChatMessage;
import com.contractai.model.ChatSession;
import com.contractai.service.ChatService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/chat")
@RequiredArgsConstructor
public class ChatController {

    private final ChatService chatService;

    @PostMapping
    public ResponseEntity<ChatResponse> chat(@RequestBody ChatRequest request, Authentication authentication) {
        return ResponseEntity.ok(chatService.sendMessage(request, authentication.getName()));
    }

    @GetMapping("/history")
    public ResponseEntity<List<ChatSession>> getChatHistory(Authentication authentication) {
        return ResponseEntity.ok(chatService.getChatHistory(authentication.getName()));
    }

    @GetMapping("/history/{sessionId}")
    public ResponseEntity<List<ChatMessage>> getChatMessages(@PathVariable UUID sessionId, Authentication authentication) {
        return ResponseEntity.ok(chatService.getChatMessages(sessionId, authentication.getName()));
    }
}
