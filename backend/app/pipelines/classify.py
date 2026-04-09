from sqlalchemy.orm import Session

from app.db.repositories.categories_repository import CategoryRepository
from app.db.repositories.classifications_repository import ClassificationRepository
from app.db.repositories.classifiers_repository import ClassifierRepository
from app.services.llm_classifier import classify_with_openai
from app.services.local_classifier import classify_with_local_model


def run_classification_pipeline(db: Session, text: str, classifier: str,) -> dict:
    cleaned_text = text.strip()

    if not cleaned_text:
        raise ValueError("O texto não pode estar vazio.")

    classifier_repo = ClassifierRepository(db)
    classifier_obj = classifier_repo.get_by_name(classifier)

    if not classifier_obj:
        raise ValueError(f"Classificador inválido: {classifier}")

    if classifier_obj.name == "local_lr":
        result = classify_with_local_model(cleaned_text, classifier_obj.name)
    elif classifier_obj.name == "openai":
        result = classify_with_openai(db, cleaned_text)
    else:
        raise ValueError(f"Classificador ainda não suportado: {classifier_obj.name}")

    response = {
        "classifier": result["classifier"],
        "macro": result["macro"],
        "detail": result["detail"],
        "macro_confidence": result["macro_confidence"],
        "detail_confidence": result["detail_confidence"],
    }

    category_repo = CategoryRepository(db)
    classification_repo = ClassificationRepository(db)

    macro = category_repo.get_or_create_macro(result["macro"])
    detail = category_repo.get_or_create_detail(result["detail"], macro.id)

    classification_repo.create_classification(
        text=cleaned_text,
        classifier_id=classifier_obj.id,
        macro_category_id=macro.id,
        detail_category_id=detail.id,
        macro_confidence=result["macro_confidence"],
        detail_confidence=result["detail_confidence"],
    )

    db.commit()

    return response