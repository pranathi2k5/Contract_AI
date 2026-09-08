package com.contractai.controller;

import com.contractai.dto.ContractUploadResponse;
import com.contractai.model.Contract;
import com.contractai.service.ContractService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/contracts")
@RequiredArgsConstructor
public class ContractController {

    private final ContractService contractService;

    @PostMapping("/upload")
    public ResponseEntity<ContractUploadResponse> uploadContract(
            @RequestParam("file") MultipartFile file,
            @RequestParam("title") String title,
            @RequestParam("userRole") String userRole,
            Authentication authentication) {
        return ResponseEntity.ok(contractService.uploadContract(file, title, userRole, authentication.getName()));
    }

    @GetMapping
    public ResponseEntity<List<Contract>> getContracts(Authentication authentication) {
        return ResponseEntity.ok(contractService.getContracts(authentication.getName()));
    }

    @GetMapping("/{id}")
    public ResponseEntity<Contract> getContractById(@PathVariable UUID id, Authentication authentication) {
        return ResponseEntity.ok(contractService.getContractById(id, authentication.getName()));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteContract(@PathVariable UUID id, Authentication authentication) {
        contractService.deleteContract(id, authentication.getName());
        return ResponseEntity.noContent().build();
    }
}
