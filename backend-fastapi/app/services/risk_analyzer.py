import json
import logging
import re
import unicodedata

from app.config import settings
from app.ml.sbert_model import SBERTModelUnavailableError, sbert_model

logger = logging.getLogger(__name__)

SEVERITY_BASE_RISKS = {
    "CRITICAL": 90.0,
    "HIGH": 70.0,
    "MEDIUM": 45.0,
    "LOW": 15.0,
}
SIMILARITY_THRESHOLD = 0.66
SEVERITY_THRESHOLDS = (
    (80, "CRITICAL"),
    (60, "HIGH"),
    (30, "MEDIUM"),
    (0, "LOW"),
)
ROLE_PARTIES = {
    "Receiver": re.compile(
        r"\b(?:employee|customer|client|tenant|recipient|receiving party|receiver)\b",
        re.IGNORECASE,
    ),
    "Sender": re.compile(
        r"\b(?:employer|company|vendor|landlord|provider|disclosing party|sending party|sender)\b",
        re.IGNORECASE,
    ),
}
ROLE_ACTIONS = {
    "INDEMNITY": re.compile(r"\b(?:indemnif\w*|hold harmless)\b", re.IGNORECASE),
    "FINANCIAL_LIABILITY": re.compile(r"\b(?:liabilit\w*|liable)\b", re.IGNORECASE),
    "RESTRAINT": re.compile(r"\b(?:non[- ]compete|not compete|non[- ]solicit\w*)\b", re.IGNORECASE),
    "INTELLECTUAL_PROPERTY": re.compile(r"\b(?:assign\w*|transfer\w*)\b", re.IGNORECASE),
    "TERMINATION": re.compile(r"\bterminat\w*\b", re.IGNORECASE),
    "PAYMENT": re.compile(
        r"\b(?:pay\w*|penalt\w*|liquidated damages|withhold\w*|deduct\w*|offset\w*)\b",
        re.IGNORECASE,
    ),
}
RULE_RISK_SIGNALS = {
    "INDEMNITY": re.compile(r"\b(?:indemnif\w*|hold harmless)\b", re.IGNORECASE),
    "FINANCIAL_LIABILITY": re.compile(
        r"\b(?:unlimited|uncapped|without (?:a |any )?(?:monetary )?limit\w*|"
        r"without (?:a )?(?:liability )?cap|no (?:maximum )?(?:aggregate )?"
        r"(?:liability )?(?:limit|cap))\b",
        re.IGNORECASE,
    ),
    "RESTRAINT": re.compile(
        r"\b(?:non[- ]compete|not compete|non[- ]solicit\w*|prohibited from competing|"
        r"competing (?:work|business|activities))\b",
        re.IGNORECASE,
    ),
    "INTELLECTUAL_PROPERTY": re.compile(
        r"\b(?:assign\w*|transfer\w*)\b.{0,100}\b(?:all|every|present and future|permanent\w*)\b|"
        r"\b(?:all|present and future|permanent\w*)\b.{0,100}"
        r"\b(?:inventions?|intellectual property)\b",
        re.IGNORECASE,
    ),
    "TERMINATION": re.compile(
        r"\b(?:immediately|without (?:any )?(?:advance )?notice|no (?:advance )?notice|"
        r"without severance|no severance|cure period)\b",
        re.IGNORECASE,
    ),
    "PAYMENT": re.compile(
        r"\b(?:late fees?|penalt\w*|liquidated damages|disproportionate|withhold\w*|"
        r"withheld|withholding|deduct\w*|offset\w*)\b",
        re.IGNORECASE,
    ),
    "CONFIDENTIALITY": re.compile(
        r"\b(?:indefinit\w*|forever|perpetual(?:ly)?|without exceptions?|no end date)\b",
        re.IGNORECASE,
    ),
    "RENEWAL": re.compile(
        r"\b(?:automatically renew\w*|renew\w* automatically|automatic renewal|"
        r"auto[- ]renew\w*|cancellation window)\b",
        re.IGNORECASE,
    ),
    "UNILATERAL_CHANGE": re.compile(
        r"\b(?:unilaterally|(?:change|modify|amend|revise|adjust)\w*.{0,50}"
        r"(?:sole discretion|without .{0,50}\b(?:approval|consent)\b)|"
        r"(?:sole discretion|without .{0,50}\b(?:approval|consent)\b).{0,50}"
        r"(?:change|modify|amend|revise|adjust)\w*)\b",
        re.IGNORECASE,
    ),
    "AMBIGUITY": re.compile(
        r"\b(?:promptly|as soon as practicable|reasonable time|as necessary|"
        r"to the satisfaction of|in its sole discretion|including but not limited to)\b",
        re.IGNORECASE,
    ),
}


class RiskAnalyzer:
    def __init__(self):
        with open(settings.RISK_PATTERNS_PATH, "r", encoding="utf-8") as patterns_file:
            self.risk_knowledge_base = json.load(patterns_file)
        self._validate_knowledge_base()

    def _validate_knowledge_base(self):
        if not isinstance(self.risk_knowledge_base, list) or not self.risk_knowledge_base:
            raise ValueError("The SBERT risk knowledge base must contain at least one pattern.")

        for index, pattern in enumerate(self.risk_knowledge_base):
            if not isinstance(pattern, dict):
                raise ValueError(f"Risk knowledge-base entry {index} must be an object.")
            if not all(pattern.get(field) for field in ("pattern", "category", "risk_level", "risk_to")):
                raise ValueError(f"Risk knowledge-base entry {index} is missing required fields.")
            if pattern["risk_level"] not in SEVERITY_BASE_RISKS:
                raise ValueError(f"Risk knowledge-base entry {index} has an unsupported risk level.")
            if pattern["risk_to"] not in {"Sender", "Receiver", "Both"}:
                raise ValueError(f"Risk knowledge-base entry {index} has an unsupported risk target.")

    @staticmethod
    def _severity(score):
        for threshold, level in SEVERITY_THRESHOLDS:
            if score >= threshold:
                return level
        return "LOW"

    @staticmethod
    def _analysis_units(clauses):
        units = []
        for clause in clauses:
            text = str(clause.get("clause_text") or "").strip()
            parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text)
            for part in parts:
                sentence = part.strip()
                if sentence:
                    units.append({
                        **clause,
                        "clause_text": sentence,
                        "matching_text": RiskAnalyzer._normalize_for_matching(sentence),
                    })
        return units

    @staticmethod
    def _normalize_for_matching(text):
        text = unicodedata.normalize("NFKC", text)
        text = re.sub(r"\s*([ƟƩŌ])\s*", r"\1", text)
        text = text.translate(str.maketrans({"Ɵ": "ti", "Ʃ": "tt", "Ō": "ft"}))
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _identified_party_role(text, category):
        action_categories = ([category] if category in ROLE_ACTIONS else []) + [
            name for name in ROLE_ACTIONS if name != category
        ]
        action_and_category = None
        for action_category in action_categories:
            action = ROLE_ACTIONS[action_category].search(text)
            if action is not None:
                action_and_category = (action, action_category)
                break
        if action_and_category is None:
            return None

        action, action_category = action_and_category
        if action_category == "TERMINATION":
            nearby_text = text[action.end():action.end() + 100]
            party_offset = action.end()
        else:
            nearby_text = text[max(0, action.start() - 100):action.start()]
            party_offset = max(0, action.start() - 100)

        matches = []
        for role, party_pattern in ROLE_PARTIES.items():
            matches.extend(
                (party_offset + match.start(), role)
                for match in party_pattern.finditer(nearby_text)
            )
        if not matches:
            return None

        if action_category == "TERMINATION":
            return min(matches)[1]
        return max(matches)[1]

    @staticmethod
    def _rule_signal(text, category):
        signal = RULE_RISK_SIGNALS.get(category)
        return len(list(signal.finditer(text))) if signal is not None else 0

    def _role_candidate(self, text, similarity_row, user_type):
        candidates = []
        for index, pattern in enumerate(self.risk_knowledge_base):
            if pattern["risk_to"] not in {user_type, "Both"}:
                continue
            similarity = max(0.0, min(1.0, float(similarity_row[index])))
            rule_signal = self._rule_signal(text, pattern["category"])
            if similarity < SIMILARITY_THRESHOLD and not rule_signal:
                continue
            identified_role = self._identified_party_role(text, pattern["category"])
            if (
                identified_role is not None
                and pattern["risk_to"] != "Both"
                and identified_role != user_type
            ):
                continue
            candidates.append({
                "risk_category": pattern["category"],
                "risk_level": pattern["risk_level"],
                "confidence": max(similarity, 1.0 if rule_signal else 0.0),
                "risk_to": pattern["risk_to"],
                "pattern": pattern,
            })
        return max(
            candidates,
            key=lambda item: SEVERITY_BASE_RISKS[item["risk_level"]] * item["confidence"],
            default=None,
        )

    @staticmethod
    def _contribution(clause_text, category, severity, explanation, contribution_type="clause"):
        excerpt = clause_text if len(clause_text) <= 320 else f"{clause_text[:317].rstrip()}..."
        return {
            "clause_text": excerpt,
            "category": category,
            "risk_level": severity,
            "contribution_score": SEVERITY_BASE_RISKS[severity],
            "explanation": explanation,
            "contribution_type": contribution_type,
        }

    def analyze(self, clauses, missing_clauses=None, contract_type="", user_type="Receiver"):
        if user_type not in {"Sender", "Receiver"}:
            raise ValueError("User type must be Sender or Receiver.")

        analysis_units = self._analysis_units(clauses or [])
        patterns = [entry["pattern"] for entry in self.risk_knowledge_base]
        warnings = []
        sbert_ran = False
        similarities = [[0.0] * len(patterns) for _ in analysis_units]
        if analysis_units:
            try:
                similarities = sbert_model.semantic_scores(
                    [clause["matching_text"] for clause in analysis_units],
                    patterns,
                )
                if similarities is None or len(similarities) != len(analysis_units):
                    raise RuntimeError(
                        "SBERT did not return a similarity score for every extracted clause."
                    )
                sbert_ran = True
            except SBERTModelUnavailableError as exc:
                warnings.append(f"{exc} Explicit clause signals were used instead.")

        contributions_by_role = {"Sender": [], "Receiver": []}
        clause_results_by_role = {"Sender": [], "Receiver": []}
        for clause, row in zip(analysis_units, similarities):
            if len(row) != len(self.risk_knowledge_base):
                raise RuntimeError("SBERT returned an incomplete risk-pattern similarity row.")

            for role in ("Sender", "Receiver"):
                candidate = self._role_candidate(clause["matching_text"], row, role)
                if candidate is None:
                    continue
                pattern = candidate["pattern"]
                category = candidate["risk_category"]
                level = candidate["risk_level"]
                explanation = (
                    f"This clause may expose the {role.lower()} to "
                    f"{level.lower()} {category.replace('_', ' ').lower()} risk."
                )
                contribution = self._contribution(
                    clause["clause_text"],
                    category,
                    level,
                    explanation,
                )
                contributions_by_role[role].append(contribution)
                if role != user_type:
                    continue
                recommendation = pattern.get(
                    "recommendation",
                    "Review and negotiate this clause with a qualified legal professional.",
                )
                clause_results_by_role[role].append({
                    **contribution,
                    "clause_type": clause.get("clause_type", "GENERAL"),
                    "risk_category": category,
                    "risk_level": level,
                    "severity": level,
                    "confidence": round(candidate["confidence"], 2),
                    "explanation": explanation,
                    "role_impact": pattern.get(
                        "impact",
                        f"This {category.replace('_', ' ').lower()} provision may expose the {role}.",
                    ),
                    "suggestion": recommendation,
                    "title": clause.get("clause_type", "Clause").replace("_", " ").title(),
                    "recommendation": recommendation,
                })

        for missing in missing_clauses or []:
            severity = str(missing.get("importance", "")).upper()
            if severity not in SEVERITY_BASE_RISKS:
                continue
            clause_name = str(missing.get("clause_name") or "Unnamed safeguard")
            explanation = (
                f"The contract analysis did not find the {clause_name} safeguard; "
                "its absence may leave either party without the protection it provides."
            )
            for role in ("Sender", "Receiver"):
                contributions_by_role[role].append(self._contribution(
                    clause_name,
                    "MISSING_SAFEGUARD",
                    severity,
                    explanation,
                    contribution_type="missing_safeguard",
                ))

        role_scores = {}
        for role in ("Sender", "Receiver"):
            role_contributions = contributions_by_role[role]
            overall = self.compute_overall_score(
                [entry["risk_level"] for entry in role_contributions]
            )
            role_scores[role] = {
                "overall_risk_score": overall["score"],
                "risk_level": overall["level"],
                "contributions": role_contributions,
            }
        overall = role_scores[user_type]
        return {
            "overall_risk_score": overall["overall_risk_score"],
            "risk_level": overall["risk_level"],
            "risk_clauses": clause_results_by_role[user_type],
            "role_risk_scores": role_scores,
            "sbert_ran": sbert_ran,
            "llm_ran": False,
            "warnings": warnings,
        }

    @staticmethod
    def compute_overall_score(clause_risks):
        clause_risks = list(clause_risks)
        if not clause_risks:
            score = 0.0
        else:
            score = round(
                sum(
                    SEVERITY_BASE_RISKS[risk_level]
                    for risk_level in clause_risks
                ) / len(clause_risks),
                1,
            )
        return {
            "score": score,
            "level": RiskAnalyzer._severity(score),
            "risky_clauses_included": len(clause_risks),
        }


risk_analyzer = RiskAnalyzer()
