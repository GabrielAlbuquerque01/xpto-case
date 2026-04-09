from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from sqlalchemy.orm import Session

from app.core.config import OPENAI_API_KEY, OPENAI_MODEL
from app.db.repositories.categories_repository import CategoryRepository


class LLMSecondaryPrediction(BaseModel):
    macro: str
    detail: str


class LLMClassificationOutput(BaseModel):
    macro: str = Field(description="Classe macro principal")
    detail: str = Field(description="Classe detalhada principal, compatível com a macro principal")
    secondary_predictions: list[LLMSecondaryPrediction] = Field(default_factory=list)


def validate_llm_output(data: LLMClassificationOutput, hierarchy: dict):
    macro_labels = hierarchy["macro_labels"]
    macro_to_detail = hierarchy["macro_to_detail"]

    if data.macro not in macro_labels:
        raise ValueError(f"Macro inválida: {data.macro}")

    if data.detail not in macro_to_detail.get(data.macro, []):
        raise ValueError(f"Detail inválida para macro {data.macro}: {data.detail}")

    for item in data.secondary_predictions:
        if item.macro not in macro_labels:
            raise ValueError(f"Macro secundária inválida: {item.macro}")
        if item.detail not in macro_to_detail.get(item.macro, []):
            raise ValueError(f"Detail secundária inválida para macro {item.macro}: {item.detail}")


def classify_with_openai(db: Session, text: str) -> dict:
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY não configurada.")

    category_repo = CategoryRepository(db)
    hierarchy = category_repo.get_hierarchy()

    if not hierarchy["macro_labels"]:
        raise ValueError("Nenhuma categoria cadastrada no banco.")

    llm = ChatOpenAI(
        model=OPENAI_MODEL,
        api_key=OPENAI_API_KEY,
        temperature=0,
    )

    structured_llm = llm.with_structured_output(LLMClassificationOutput)

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "Você é um classificador hierárquico rigoroso. "
            "Escolha apenas classes válidas. "
            "A classe detalhada principal deve pertencer à macro principal. "
            "Se houver ambiguidade, registre alternativas em secondary_predictions. "
            "Nunca invente classes."
        ),
        (
            "human",
            """Classes macro válidas:
{macro_labels}

Hierarquia macro -> detail:
{macro_to_detail}

Texto:
{text}"""
        )
    ])

    chain = prompt | structured_llm

    result = chain.invoke({
        "macro_labels": hierarchy["macro_labels"],
        "macro_to_detail": hierarchy["macro_to_detail"],
        "text": text,
    })

    validate_llm_output(result, hierarchy)

    return {
        "classifier": "openai",
        "macro": result.macro,
        "detail": result.detail,
        "macro_confidence": 1.0,
        "detail_confidence": 1.0,
        "secondary_predictions": [
            {"macro": item.macro, "detail": item.detail}
            for item in result.secondary_predictions
        ],
    }