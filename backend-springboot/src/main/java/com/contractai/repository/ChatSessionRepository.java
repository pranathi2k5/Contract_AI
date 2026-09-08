package com.contractai.repository;

import com.contractai.model.ChatSession;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface ChatSessionRepository extends JpaRepository<ChatSession, UUID> {
    List<ChatSession> findByUserId(UUID userId);
    Optional<ChatSession> findByUserIdAndContractId(UUID userId, UUID contractId);
}
