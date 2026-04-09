import json
import re

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from sqlalchemy.orm import Session

from app.core.config import OPENAI_API_KEY, OPENAI_MODEL
from app.db.repositories.categories_repository import CategoryRepository
from app.prompts.classification_prompt import build_classification_prompt
from app.services.local_classifier import get_local_candidates_for_text


def extract_first_json_object(text: str) -> dict:
    stripped = text.strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", stripped, re.DOTALL)
    if not match:
        raise ValueError(f"Resposta inválida da OpenAI: {text}")

    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON inválido retornado pela OpenAI: {text}") from exc


def clamp_confidence(value: float | int | str | None, default: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(1.0, parsed))


def validate_llm_labels(macro: str, micro: str, hierarchy: dict):
    macro_labels = hierarchy["macro_labels"]
    macro_to_micro = hierarchy["macro_to_micro"]

    if macro not in macro_labels:
        raise ValueError(
            f"Macro inválida retornada pelo modelo: '{macro}'. Permitidas: {macro_labels}"
        )

    allowed_micros = macro_to_micro.get(macro, [])
    if micro not in allowed_micros:
        raise ValueError(
            f"Micro inválida para a macro '{macro}': '{micro}'. Permitidas: {allowed_micros}"
        )


def classify_with_openai(db: Session, text: str) -> dict:
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY não configurada.")

    category_repo = CategoryRepository(db)
    hierarchy = category_repo.get_hierarchy()

    if not hierarchy["macro_labels"]:
        raise ValueError("Nenhuma categoria cadastrada no banco.")

    local_candidates = get_local_candidates_for_text(text)
    prompt_text = build_classification_prompt(
        text=text,
        macro_labels=hierarchy["macro_labels"],
        macro_to_micro=hierarchy["macro_to_micro"],
        local_candidates=local_candidates,
    )

    llm = ChatOpenAI(
        model=OPENAI_MODEL,
        api_key=OPENAI_API_KEY,
        temperature=0,
    )

    prompt = ChatPromptTemplate.from_template("{prompt}")
    chain = prompt | llm
    response = chain.invoke({"prompt": prompt_text})
    data = extract_first_json_object(response.content)

    if "macro" not in data or "micro" not in data:
        raise ValueError(f"JSON incompleto retornado pela OpenAI: {data}")

    macro = str(data["macro"]).strip()
    micro = str(data["micro"]).strip()
    validate_llm_labels(macro, micro, hierarchy)

    macro_confidence = clamp_confidence(data.get("macro_confidence"), default=0.75)
    micro_confidence = clamp_confidence(data.get("micro_confidence"), default=0.75)
    is_ambiguous = bool(data.get("is_ambiguous", False)) or macro_confidence < 0.60 or micro_confidence < 0.60
    justification = str(data.get("justification", "")).strip() or None

    return {
        "macro": macro,
        "micro": micro,
        "macro_confidence": macro_confidence,
        "micro_confidence": micro_confidence,
        "model": "openai",
        "is_ambiguous": is_ambiguous,
        "metadata": {
            "justification": justification,
            "macro_candidates": local_candidates.get("macro_candidates", []),
            "micro_candidates_by_macro": local_candidates.get("micro_candidates_by_macro", {}),
            "raw_llm_response": data,
        },
    }