from sqlalchemy.orm import Session

from app.db.repositories.categories_repository import CategoryRepository
from app.db.repositories.classifications_repository import ClassificationRepository
from app.services.llm_classifier import classify_with_openai
from app.services.local_classifier import classify_with_local_model


VALID_MODELS = {"local_lr", "openai"}


def run_classification_pipeline(
    db: Session,
    text: str,
    model_type: str,
    save_prediction: bool = True
) -> dict:
    cleaned_text = text.strip()

    if not cleaned_text:
        raise ValueError("O texto não pode estar vazio.")

    if model_type not in VALID_MODELS:
        raise ValueError(f"Modelo inválido: {model_type}")

    if model_type == "local_lr":
        result = classify_with_local_model(cleaned_text, model_type)
    else:
        result = classify_with_openai(db, cleaned_text)

    response = {
        "macro": result["macro"],
        "macro_confidence": result.get("macro_confidence", 1.0),
        "micro": result["micro"],
        "micro_confidence": result.get("micro_confidence", 1.0),
        "model": result["model"],
        "is_ambiguous": result.get("is_ambiguous", False),
        "metadata": result.get("metadata"),
    }

    if save_prediction:
        category_repo = CategoryRepository(db)
        classification_repo = ClassificationRepository(db)

        macro = category_repo.get_or_create_macro(result["macro"])
        detail = category_repo.get_or_create_detail(result["micro"], macro.id)

        classification_repo.create_classification(
            text=cleaned_text,
            model_type=result["model"],
            macro_category_id=macro.id,
            detail_category_id=detail.id,
            macro_confidence=result.get("macro_confidence", 1.0),
            detail_confidence=result.get("micro_confidence", 1.0),
            is_ambiguous=result.get("is_ambiguous", False),
            metadata_json=result.get("metadata"),
        )

        db.commit()

    return response