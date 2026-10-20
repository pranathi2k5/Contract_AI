import re
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException
from app.config import settings
from app.models.schemas import ChatMessageRequest, ChatMessageResponse
from app.services.chatbot_service import ChatbotUnavailableError, chatbot_service
from app.services.rag_service import rag_service

router = APIRouter(prefix="/ai/chat", tags=["chat"])
MIN_LEGAL_RELEVANCE = 0.45
OFFICIAL_INDIA_CODE_HOSTS = {"indiacode.nic.in", "www.indiacode.nic.in"}
NON_COMPETE_DEFINITION = (
    "A non-compete is a contract term that restricts someone from working for, "
    "starting, or otherwise engaging with a competing business, often for a stated "
    "time, place, or type of work. Whether a particular restriction is enforceable "
    "depends on the jurisdiction and circumstances."
)
GENERAL_DEFINITIONS = {
    "employment agreement": (
        "An employment agreement is a contract between an employer and an employee "
        "that sets out terms such as the role, pay, working conditions, and how the "
        "employment relationship may end."
    ),
    "non-compete": NON_COMPETE_DEFINITION,
}
FINANCIAL_QUESTION = re.compile(
    r"\b(?:financial\s+liabilit(?:y|ies)|total\s+(?:financial\s+)?liabilit(?:y|ies)|"
    r"(?:liabilit(?:y|ies)|monetary\s+obligations?)\s+(?:under|in)\s+"
    r"(?:this|the|my|our)\s+(?:agreement|contract)|"
    r"how much.{0,40}\b(?:owe|pay|liable|liabilit(?:y|ies)))\b",
    re.IGNORECASE,
)
CONTRACT_REFERENCE = re.compile(
    r"\b(?:my|this|that|the|our)\s+(?:uploaded\s+)?(?:contract|agreement)\b|"
    r"\b(?:under|in|of)\s+(?:my|this|that|the|our)\s+(?:contract|agreement)\b",
    re.IGNORECASE,
)
FINANCIAL_CLAUSE = re.compile(
    r"\b(?:payment|payable|owe|fee|charge|cost|expense|reimburs|repay|"
    r"penalt|liquidated damages|indemnif|liabilit|damages|termination|"
    r"interest|refund|deposit|fine|compensation|tax|invoice|salary|wage|"
    r"obligation|uncapped|unlimited)\b",
    re.IGNORECASE,
)
CONDITIONAL_AMOUNT = re.compile(
    r"\b(?:if|in the event|subject to|breach|default|penalt|liquidated damages|"
    r"indemnif|may be charged|may be assessed|up to|not exceed|not exceeding|"
    r"without limitation|uncapped|unlimited|interest|refundable|"
    r"greater of|lesser of|higher of|lower of|whichever is|alternatively)\b",
    re.IGNORECASE,
)
UNCAPPED_LIABILITY = re.compile(
    r"\b(?:without limitation|uncapped|unlimited|no cap)\b",
    re.IGNORECASE,
)
MONEY = re.compile(
    r"(?:(?P<prefix>₹|Rs\.?|INR|USD|\$|EUR|€|GBP|£|rupees?|dollars?|euros?|pounds?)\s*"
    r"(?P<amount>\d[\d,]*(?:\.\d{1,2})?)"
    r"(?:\s*(?P<scale>lakhs?|crores?|millions?|thousands?))?"
    r"|(?P<amount_after>\d[\d,]*(?:\.\d{1,2})?)"
    r"(?:\s*(?P<scale_after>lakhs?|crores?|millions?|thousands?))?\s*"
    r"(?P<suffix>INR|USD|EUR|GBP|rupees?|dollars?|euros?|pounds?))",
    re.IGNORECASE,
)
CURRENCY_NAMES = {
    "₹": "INR", "rs": "INR", "rs.": "INR", "inr": "INR", "rupee": "INR", "rupees": "INR",
    "$": "USD", "usd": "USD", "dollar": "USD", "dollars": "USD",
    "€": "EUR", "eur": "EUR", "euro": "EUR", "euros": "EUR",
    "£": "GBP", "gbp": "GBP", "pound": "GBP", "pounds": "GBP",
}
CURRENCY_SYMBOLS = {"INR": "₹", "USD": "$", "EUR": "€", "GBP": "£"}
SCALES = {
    "thousand": Decimal("1000"),
    "lakh": Decimal("100000"),
    "million": Decimal("1000000"),
    "crore": Decimal("10000000"),
}


def _simple_general_definition(message):
    match = re.fullmatch(
        r"\s*(?:what(?:'s|s|’s| is)\s+(?:an?\s+)?|define\s+(?:an?\s+)?)"
        r"(?P<term>employment agreement|non[- ]compete)[?.!]*\s*",
        message,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    term = match.group("term").lower().replace("non compete", "non-compete")
    return GENERAL_DEFINITIONS.get(term)


def _financial_clauses(contract_text):
    sections = re.split(
        r"\n\s*\n|(?=^\s*(?:(?:clause|section|article)\s+)?"
        r"\d+(?:\.\d+)*[.)]?\s+[A-Z])",
        contract_text,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    return [
        section.strip()
        for section in sections
        if section.strip() and FINANCIAL_CLAUSE.search(section)
    ]


def _currency_and_amount(match):
    raw_currency = match.group("prefix") or match.group("suffix")
    raw_amount = match.group("amount") or match.group("amount_after")
    scale = match.group("scale") or match.group("scale_after") or ""
    try:
        amount = Decimal(raw_amount.replace(",", ""))
    except InvalidOperation:
        return None
    scale_key = scale.lower().rstrip("s")
    amount *= SCALES.get(scale_key, Decimal(1))
    currency = CURRENCY_NAMES.get(raw_currency.lower().rstrip("."), CURRENCY_NAMES.get(raw_currency.lower()))
    if not currency:
        return None
    return currency, amount


def _format_money(currency, amount):
    formatted = f"{amount:,.2f}".rstrip("0").rstrip(".")
    return f"{CURRENCY_SYMBOLS[currency]}{formatted}"


def _payment_frequency(clause):
    checks = (
        (r"\b(?:per\s+month|monthly|each month)\b", "month"),
        (r"\b(?:per\s+quarter|quarterly|each quarter)\b", "quarter"),
        (r"\b(?:per\s+year|per annum|annually|annual|yearly|each year)\b", "year"),
        (r"\b(?:per\s+week|weekly|each week)\b", "week"),
        (r"\b(?:per\s+day|daily|each day)\b", "day"),
    )
    for pattern, frequency in checks:
        if re.search(pattern, clause, re.IGNORECASE):
            return frequency
    return None


def _amount_frequency(clause, amount_match):
    before = clause[max(0, amount_match.start() - 80):amount_match.start()]
    after = clause[amount_match.end():amount_match.end() + 80]
    if (
        re.search(r"\b(?:total|aggregate|contract price|entire amount)\b", before, re.IGNORECASE)
        and re.search(r"\binstallments?\b", after, re.IGNORECASE)
    ):
        return None
    return _payment_frequency(f"{before} {after}")


def _recurring_total(amount, frequency, clause):
    duration = re.search(
        r"\b(?:for|over|throughout|term of)\s+(\d+)\s*(months?|years?|weeks?|days?)\b"
        r"|\b(\d+)\s*[- ]\s*(months?|years?|weeks?|days?)\b",
        clause,
        re.IGNORECASE,
    )
    if not duration:
        return None
    count = int(duration.group(1) or duration.group(3))
    unit = (duration.group(2) or duration.group(4)).lower().rstrip("s")
    periods = {
        ("month", "month"): count,
        ("month", "year"): count * 12,
        ("quarter", "month"): count // 3 if count % 3 == 0 else None,
        ("quarter", "year"): count * 4,
        ("year", "year"): count,
        ("year", "month"): count // 12 if count % 12 == 0 else None,
        ("week", "week"): count,
        ("day", "day"): count,
    }.get((frequency, unit))
    return amount * periods if periods else None


def _financial_liability_answer(contract_text):
    clauses = _financial_clauses(contract_text)
    if not clauses:
        return (
            "I couldn't identify payment, penalty, indemnity, or other monetary "
            "liability clauses in the extracted contract text, so I can't determine "
            "a total. The extracted text may be incomplete."
        )

    entries = []
    totals = {}
    unresolved = "[Contract text truncated for context size.]" in contract_text
    for clause in clauses:
        amounts = []
        for match in MONEY.finditer(clause):
            parsed = _currency_and_amount(match)
            if parsed:
                amounts.append((match, parsed))
        snippet = re.sub(r"\s+", " ", clause).strip()
        if len(snippet) > 1000:
            snippet = snippet[:997].rstrip() + "..."
            unresolved = True
        if not amounts:
            entries.append(
                ("The amount is not stated in this provision", snippet)
            )
            unresolved = True
            continue

        frequency = _payment_frequency(clause)
        conditional = bool(CONDITIONAL_AMOUNT.search(clause))
        for match, (currency, amount) in amounts:
            amount_frequency = _amount_frequency(clause, match)
            if conditional:
                label = (
                    "Conditional or capped amount (including refundable or "
                    "alternative amounts), not "
                    f"included in a fixed total: {_format_money(currency, amount)}"
                )
                unresolved = True
            elif frequency and not amount_frequency:
                label = (
                    f"Amount stated: {_format_money(currency, amount)}. Recurring "
                    "payment terms are present, but their relationship to this "
                    "amount is unclear; it is not totaled"
                )
                unresolved = True
            elif amount_frequency:
                recurring_total = _recurring_total(amount, amount_frequency, clause)
                if recurring_total is None:
                    label = (
                        f"Recurring amount: {_format_money(currency, amount)} per "
                        f"{amount_frequency}; the duration is not clear, so it is not totaled"
                    )
                    unresolved = True
                else:
                    label = (
                        f"Recurring amount: {_format_money(currency, amount)} per "
                        f"{amount_frequency}; stated-term amount: {_format_money(currency, recurring_total)}"
                    )
                    totals[currency] = totals.get(currency, Decimal(0)) + recurring_total
            else:
                label = f"Stated amount: {_format_money(currency, amount)}"
                totals[currency] = totals.get(currency, Decimal(0)) + amount
            entries.append((label, snippet))

    has_uncapped = bool(UNCAPPED_LIABILITY.search(contract_text))
    if has_uncapped:
        entries.append(("Uncapped or unlimited liability is mentioned; no amount can be calculated for it", ""))
        unresolved = True

    response_lines = [
        "From the extracted agreement text, I found these monetary provisions:"
    ]
    for label, clause in entries:
        response_lines.append(f"- {label}.")
        if clause:
            response_lines.append(f'  Contract text: "{clause}"')

    if totals:
        subtotals = "; ".join(
            _format_money(currency, amount)
            for currency, amount in sorted(totals.items())
        )
        if unresolved:
            response_lines.append(
                f"Known fixed/stated subtotal: {subtotals}. A complete total cannot "
                "be determined because some obligations are conditional, uncapped, "
                "unquantified, or lack a stated duration."
            )
        elif len(totals) > 1:
            response_lines.append(
                f"Calculated stated amounts by currency: {subtotals}. They cannot "
                "be combined without an exchange rate."
            )
        else:
            response_lines.append(
                f"Calculated total of the stated obligations identified: {subtotals}."
            )
    else:
        response_lines.append(
            "A defensible total cannot be determined from the extracted text because "
            "the amounts, conditions, or payment duration are not sufficiently specified."
        )

    response_lines.append(
        "This covers only provisions identified in the extracted text and may not "
        "represent the contract's complete liability. It sums the stated amounts "
        "found; it does not determine which named party is you."
    )
    return "\n".join(response_lines)


def _verified_legal_matches(legal_result):
    if not isinstance(legal_result, dict) or legal_result.get("status") != "ready":
        return []
    matches = legal_result.get("matches")
    if not isinstance(matches, list):
        return []

    verified = []
    for match in matches:
        if not isinstance(match, dict):
            continue
        required_text = ("act_name", "section_number", "section_title", "retrieved_text")
        if not all(
            isinstance(match.get(field), str) and match[field].strip()
            for field in required_text
        ):
            continue
        source_url = match.get("source_url")
        if not isinstance(source_url, str):
            continue
        parsed_url = urlparse(source_url)
        if parsed_url.scheme != "https" or parsed_url.hostname not in OFFICIAL_INDIA_CODE_HOSTS:
            continue
        score = match.get("relevance_score")
        if (
            isinstance(score, bool)
            or not isinstance(score, (int, float))
            or score < MIN_LEGAL_RELEVANCE
        ):
            continue
        verified.append(match)
    return verified


@router.post("/", response_model=ChatMessageResponse)
def chat(req: ChatMessageRequest):
    contract_context = (req.contract_context or "").strip()
    legal_result = rag_service.query(req.message)
    legal_matches = _verified_legal_matches(legal_result)
    legal_context = "\n\n".join(
        f"Act: {match['act_name']}\n"
        f"Section: {match['section_number']} — {match['section_title']}\n"
        f"Official source: {match['source_url']}\n"
        f"Retrieved statutory text:\n{match['retrieved_text']}"
        for match in legal_matches
    )
    contract_question = bool(
        FINANCIAL_QUESTION.search(req.message) or CONTRACT_REFERENCE.search(req.message)
    )
    if contract_question and not contract_context:
        if FINANCIAL_QUESTION.search(req.message):
            resp_text = (
                "I don't have extracted contract text available for this chat. Please "
                "upload or reselect the agreement and run its analysis before asking "
                "about its financial liability."
            )
        else:
            resp_text = (
                "I don't have extracted contract text available for this chat. Please "
                "upload or reselect the agreement and run its analysis before asking "
                "about its terms."
            )
        return ChatMessageResponse(role="assistant", content=resp_text, sources=[
            {
                "act_name": match["act_name"],
                "section_number": match["section_number"],
                "section_title": match["section_title"],
                "source_url": match["source_url"],
                "relevance_score": match["relevance_score"],
                "retrieved_text": match["retrieved_text"],
                "version": match.get("version", ""),
                "effective_date": match.get("effective_date", ""),
            }
            for match in legal_matches
        ])

    model_context = contract_context
    if len(model_context) > 24000 and FINANCIAL_QUESTION.search(req.message):
        relevant_clauses = _financial_clauses(model_context)
        if relevant_clauses:
            model_context = "\n\n".join(relevant_clauses)
    if len(model_context) > 24000:
        model_context = model_context[:24000] + "\n[Contract text truncated for context size.]"
    try:
        resp_text = chatbot_service.chat(model_context, legal_context, req.message)
    except ChatbotUnavailableError as exc:
        if settings.LLM_PROVIDER.strip().lower() == "gemini":
            if (
                exc.temporary
                and FINANCIAL_QUESTION.search(req.message)
                and contract_context
            ):
                resp_text = _financial_liability_answer(contract_context)
            elif not contract_context and not legal_matches:
                resp_text = _simple_general_definition(req.message)
                if resp_text is None:
                    raise HTTPException(status_code=503, detail=str(exc)) from exc
            else:
                raise HTTPException(status_code=503, detail=str(exc)) from exc
        else:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
    sources = [
        {
            "act_name": match["act_name"],
            "section_number": match["section_number"],
            "section_title": match["section_title"],
            "source_url": match["source_url"],
            "relevance_score": match["relevance_score"],
            "retrieved_text": match["retrieved_text"],
            "version": match.get("version", ""),
            "effective_date": match.get("effective_date", ""),
        }
        for match in legal_matches
    ]
    return ChatMessageResponse(
        role="assistant",
        content=resp_text,
        sources=sources,
    )

@router.get("/context/{contract_id}")
async def get_context(contract_id: str):
    return {"contract_id": contract_id, "context": None, "available": False}
