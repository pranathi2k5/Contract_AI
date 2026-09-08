package com.contractai.service;

import com.contractai.dto.AnalysisResponse;
import com.lowagie.text.Document;
import com.lowagie.text.Paragraph;
import com.lowagie.text.pdf.PdfWriter;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.io.ByteArrayOutputStream;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class ReportService {

    private final AnalysisService analysisService;

    public byte[] generatePdfReport(UUID contractId, String userEmail) {
        AnalysisResponse analysis = analysisService.getAnalysisResults(contractId, userEmail);

        try (ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            Document document = new Document();
            PdfWriter.getInstance(document, out);
            document.open();

            document.add(new Paragraph("Contract Analysis Report"));
            document.add(new Paragraph("Contract ID: " + contractId));
            document.add(new Paragraph("Risk Level: " + analysis.getResult().getRiskLevel()));
            document.add(new Paragraph("Summary: " + analysis.getResult().getSummary()));

            document.add(new Paragraph("\nRisky Clauses:"));
            analysis.getRiskClauses().forEach(rc -> {
                try {
                    document.add(new Paragraph("- " + rc.getClauseType() + " (" + rc.getSeverity() + ")"));
                } catch (Exception e) {}
            });

            document.close();
            return out.toByteArray();
        } catch (Exception e) {
            throw new RuntimeException("Could not generate PDF", e);
        }
    }
}
