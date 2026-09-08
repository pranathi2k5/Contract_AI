package com.contractai.service;

import com.contractai.dto.ContractUploadResponse;
import com.contractai.exception.ResourceNotFoundException;
import com.contractai.model.Contract;
import com.contractai.model.User;
import com.contractai.repository.ContractRepository;
import com.contractai.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class ContractService {

    private final ContractRepository contractRepository;
    private final UserRepository userRepository;

    @Value("${app.upload.dir}")
    private String uploadDir;

    public ContractUploadResponse uploadContract(MultipartFile file, String title, String userRole, String userEmail) {
        User user = userRepository.findByEmail(userEmail)
                .orElseThrow(() -> new ResourceNotFoundException("User not found"));

        try {
            Path uploadPath = Paths.get(uploadDir);
            if (!Files.exists(uploadPath)) {
                Files.createDirectories(uploadPath);
            }

            String originalFilename = file.getOriginalFilename();
            String fileType = originalFilename != null && originalFilename.toLowerCase().endsWith(".pdf") ? "PDF" : "DOCX";
            String uniqueFileName = UUID.randomUUID() + "_" + originalFilename;
            Path filePath = uploadPath.resolve(uniqueFileName);

            file.transferTo(filePath.toFile());

            Contract contract = Contract.builder()
                    .user(user)
                    .title(title)
                    .fileName(originalFilename)
                    .fileType(fileType)
                    .filePath(filePath.toString())
                    .userRole(userRole)
                    .status("UPLOADED")
                    .build();

            contract = contractRepository.save(contract);

            return ContractUploadResponse.builder()
                    .contractId(contract.getId())
                    .fileName(contract.getFileName())
                    .status(contract.getStatus())
                    .build();
        } catch (IOException e) {
            throw new RuntimeException("Could not store file", e);
        }
    }

    public List<Contract> getContracts(String userEmail) {
        User user = userRepository.findByEmail(userEmail)
                .orElseThrow(() -> new ResourceNotFoundException("User not found"));
        return contractRepository.findByUserId(user.getId());
    }

    public Contract getContractById(UUID id, String userEmail) {
        User user = userRepository.findByEmail(userEmail)
                .orElseThrow(() -> new ResourceNotFoundException("User not found"));
        return contractRepository.findByIdAndUserId(id, user.getId())
                .orElseThrow(() -> new ResourceNotFoundException("Contract not found"));
    }

    public void deleteContract(UUID id, String userEmail) {
        Contract contract = getContractById(id, userEmail);
        try {
            Files.deleteIfExists(Paths.get(contract.getFilePath()));
        } catch (IOException ignored) {}
        contractRepository.delete(contract);
    }
}
