package com.contractai.repository;

import com.contractai.model.Contract;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface ContractRepository extends JpaRepository<Contract, UUID> {
    List<Contract> findByUserId(UUID userId);
    Optional<Contract> findByIdAndUserId(UUID id, UUID userId);
}
