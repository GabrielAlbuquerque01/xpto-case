from functools import lru_cache
from typing import Any

import joblib

from app.core.config import ARTIFACTS_DIR


MACRO_MODEL_FILENAME = "modelo_macro.joblib"
SPECIALISTS_FILENAME = "modelos_especialistas.joblib"


@lru_cache
def get_local_models() -> dict[str, Any]:
    macro_model = joblib.load(ARTIFACTS_DIR / MACRO_MODEL_FILENAME)
    specialist_models = joblib.load(ARTIFACTS_DIR / SPECIALISTS_FILENAME)

    if not isinstance(specialist_models, dict):
        raise ValueError(
            "O artefato 'modelos_especialistas.joblib' deve ser um dicionário "
            "no formato {macro: modelo_especialista}."
        )

    return {
        "local_lr": {
            "macro": macro_model,
            "specialists": specialist_models,
        }
    }


def _validate_model_supports_proba(model: Any) -> None:
    if not hasattr(model, "predict"):
        raise ValueError("O modelo informado não possui método predict().")
    if not hasattr(model, "predict_proba"):
        raise ValueError("O modelo informado não possui método predict_proba().")


def _predict_with_confidence(model: Any, text: str) -> tuple[str, float]:
    _validate_model_supports_proba(model)
    probas = model.predict_proba([text])[0]
    classes = list(model.classes_)
    best_idx = probas.argmax()
    return str(classes[best_idx]), float(probas[best_idx])


def classify_with_local_model(text: str, classifier: str) -> dict:
    models = get_local_models()

    if classifier not in models:
        raise ValueError(f"Classificador local inválido: {classifier}")

    cleaned_text = text.strip()
    if not cleaned_text:
        raise ValueError("O texto não pode estar vazio.")

    macro_model = models[classifier]["macro"]
    specialist_models = models[classifier]["specialists"]

    macro_pred, macro_confidence = _predict_with_confidence(macro_model, cleaned_text)

    detail_model = specialist_models.get(macro_pred)
    if detail_model is None:
        available_macros = sorted(specialist_models.keys())
        raise ValueError(
            f"Não existe modelo especialista para a macro prevista '{macro_pred}'. "
            f"Macros disponíveis: {available_macros}"
        )

    detail_pred, detail_confidence = _predict_with_confidence(detail_model, cleaned_text)

    return {
        "classifier": classifier,
        "macro": macro_pred,
        "detail": detail_pred,
        "macro_confidence": macro_confidence,
        "detail_confidence": detail_confidence,
    }