package com.contractai.service;

import com.contractai.dto.ChatRequest;
import com.contractai.dto.ChatResponse;
import com.contractai.model.ChatMessage;
import com.contractai.model.ChatSession;
import com.contractai.model.User;
import com.contractai.repository.ChatMessageRepository;
import com.contractai.repository.ChatSessionRepository;
import com.contractai.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class ChatService {

    private final ChatSessionRepository chatSessionRepository;
    private final ChatMessageRepository chatMessageRepository;
    private final UserRepository userRepository;
    private final AiServiceClient aiServiceClient;

    public ChatResponse sendMessage(ChatRequest request, String userEmail) {
        User user = userRepository.findByEmail(userEmail)
                .orElseThrow(() -> new RuntimeException("User not found"));

        ChatSession session;
        if (request.getSessionId() != null) {
            session = chatSessionRepository.findById(request.getSessionId())
                    .orElseThrow(() -> new RuntimeException("Session not found"));
        } else {
            session = ChatSession.builder()
                    .user(user)
                    .title("New Chat")
                    .build();
            session = chatSessionRepository.save(session);
        }

        ChatMessage userMsg = ChatMessage.builder()
                .session(session)
                .role("user")
                .content(request.getMessage())
                .build();
        chatMessageRepository.save(userMsg);

        Map<String, Object> aiResponse = aiServiceClient.chat(request.getMessage(), "context");
        String aiReply = aiResponse != null && aiResponse.containsKey("reply") ? aiResponse.get("reply").toString() : "I'm a placeholder reply.";

        ChatMessage botMsg = ChatMessage.builder()
                .session(session)
                .role("assistant")
                .content(aiReply)
                .sources("[]")
                .build();
        chatMessageRepository.save(botMsg);

        return ChatResponse.builder()
                .response(botMsg.getContent())
                .sessionId(session.getId())
                .sources(botMsg.getSources())
                .build();
    }

    public List<ChatSession> getChatHistory(String userEmail) {
        User user = userRepository.findByEmail(userEmail)
                .orElseThrow(() -> new RuntimeException("User not found"));
        return chatSessionRepository.findByUserId(user.getId());
    }

    public List<ChatMessage> getChatMessages(UUID sessionId, String userEmail) {
        return chatMessageRepository.findBySessionIdOrderByCreatedAtAsc(sessionId);
    }
}
