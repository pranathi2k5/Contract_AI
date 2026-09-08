class ClauseRisk {
  final String title;
  final String text;
  final String riskLevel; // HIGH, MEDIUM, LOW
  final String explanation;
  final String recommendation;

  ClauseRisk({
    required this.title,
    required this.text,
    required this.riskLevel,
    required this.explanation,
    required this.recommendation,
  });
}

class MissingClause {
  final String clauseName;
  final String reason;
  final String recommendedText;

  MissingClause({
    required this.clauseName,
    required this.reason,
    required this.recommendedText,
  });
}

class IndianLawMapping {
  final String actName;
  final String section;
  final String applicabilityReason;

  IndianLawMapping({
    required this.actName,
    required this.section,
    required this.applicabilityReason,
  });
}

class ContractAnalysisResult {
  final String contractId;
  final int overallRiskScore;
  final String riskLevel;
  final String summary;
  final List<ClauseRisk> riskClauses;
  final List<MissingClause> missingClauses;
  final List<IndianLawMapping> applicableLaws;

  ContractAnalysisResult({
    required this.contractId,
    required this.overallRiskScore,
    required this.riskLevel,
    required this.summary,
    required this.riskClauses,
    required this.missingClauses,
    required this.applicableLaws,
  });
}
