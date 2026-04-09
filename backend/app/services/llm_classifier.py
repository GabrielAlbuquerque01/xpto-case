import json
import re

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from sqlalchemy.orm import Session

from app.core.config import OPENAI_API_KEY, OPENAI_MODEL
from app.db.repositories.categories_repository import CategoryRepository
from app.prompts.classification_prompt import build_classification_prompt


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


def clamp_confidence(value, default: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(1.0, parsed))


def validate_llm_labels(macro: str, detail: str, hierarchy: dict):
    macro_labels = hierarchy["macro_labels"]
    macro_to_detail = hierarchy["macro_to_detail"]

    if macro not in macro_labels:
        raise ValueError(
            f"Macro inválida retornada pelo modelo: '{macro}'. Permitidas: {macro_labels}"
        )

    allowed_details = macro_to_detail.get(macro, [])
    if detail not in allowed_details:
        raise ValueError(
            f"Detail inválido para a macro '{macro}': '{detail}'. Permitidas: {allowed_details}"
        )


def classify_with_openai(db: Session, text: str) -> dict:
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY não configurada.")

    category_repo = CategoryRepository(db)
    hierarchy = category_repo.get_hierarchy()

    if not hierarchy["macro_labels"]:
        raise ValueError("Nenhuma categoria cadastrada no banco.")

    prompt_text = build_classification_prompt(
        text=text,
        macro_labels=hierarchy["macro_labels"],
        macro_to_detail=hierarchy["macro_to_detail"],
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

    if "macro" not in data or "detail" not in data:
        raise ValueError(f"JSON incompleto retornado pela OpenAI: {data}")

    macro = str(data["macro"]).strip()
    detail = str(data["detail"]).strip()
    validate_llm_labels(macro, detail, hierarchy)

    macro_confidence = clamp_confidence(data.get("macro_confidence"), default=0.75)
    detail_confidence = clamp_confidence(data.get("detail_confidence"), default=0.75)

    return {
        "classifier": "openai",
        "macro": macro,
        "detail": detail,
        "macro_confidence": macro_confidence,
        "detail_confidence": detail_confidence,
    }