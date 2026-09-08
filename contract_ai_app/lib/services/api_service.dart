import '../models/contract_model.dart';

class ApiService {
  static const String baseUrlFastAPI = 'http://localhost:8000';
  static const String baseUrlSpringBoot = 'http://localhost:8080';

  // Demo contract data provider
  static Future<ContractAnalysisResult> getAnalysisResult(String contractType, String role) async {
    await Future.delayed(const Duration(milliseconds: 600));

    return ContractAnalysisResult(
      contractId: 'contract_${DateTime.now().millisecondsSinceEpoch}',
      overallRiskScore: contractType == 'NDA' ? 42 : 72,
      riskLevel: contractType == 'NDA' ? 'MEDIUM' : 'HIGH',
      summary: 'Analysis completed for $contractType Agreement from $role perspective. Severe non-compete restraint detected alongside uncapped liability.',
      riskClauses: [
        ClauseRisk(
          title: 'Post-Employment Non-Compete (24 Months)',
          text: 'Employee shall not engage with any competitor in India for 24 months.',
          riskLevel: 'HIGH',
          explanation: 'Void under Section 27 of Indian Contract Act 1872.',
          recommendation: 'Request complete removal or non-solicitation only.',
        ),
        ClauseRisk(
          title: 'Uncapped IP Indemnification',
          text: 'Employee agrees to fully indemnify company without limit.',
          riskLevel: 'HIGH',
          explanation: 'Exposes employee to unlimited personal liability.',
          recommendation: 'Cap liability at 3 months basic salary.',
        ),
        ClauseRisk(
          title: 'Unilateral Notice Period Mismatch',
          text: 'Company may terminate immediately; Employee requires 90 days notice.',
          riskLevel: 'MEDIUM',
          explanation: 'Unfair notice period balance favoring employer.',
          recommendation: 'Mandate reciprocal 60-day notice period.',
        ),
      ],
      missingClauses: [
        MissingClause(
          clauseName: 'Severance Pay & Notice Parity',
          reason: 'Protects against immediate termination without financial compensation.',
          recommendedText: 'In event of termination without cause, Company shall provide 60 days notice or pay in lieu.',
        ),
        MissingClause(
          clauseName: 'Limitation of Employee Liability',
          reason: 'Prevents personal exposure to general business damages.',
          recommendedText: 'Aggregate liability shall not exceed 3 months compensation.',
        ),
      ],
      applicableLaws: [
        IndianLawMapping(
          actName: 'Indian Contract Act, 1872',
          section: 'Section 27 — Restraint of Trade Void',
          applicability_reason: 'Post-employment non-compete covenants are completely void in India.',
        ),
        IndianLawMapping(
          actName: 'Information Technology Act, 2000',
          section: 'Section 43A & 72A — Data Protection',
          applicability_reason: 'Governs liability for failure to protect sensitive data.',
        ),
        IndianLawMapping(
          actName: 'Specific Relief Act, 1963',
          section: 'Section 41(e) — Injunction Restraining Breach',
          applicability_reason: 'Governs negative covenants during active employment.',
        ),
      ],
    );
  }
}
