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
        raise ValueError(
            "O modelo informado não possui método predict_proba(). "
            "Para retornar confiança, o classificador final precisa suportar isso."
        )


def predict_top_candidates(model: Any, text: str, top_n: int = 3) -> list[dict]:
    _validate_model_supports_proba(model)

    probas = model.predict_proba([text])[0]
    classes = list(model.classes_)

    ranked = sorted(
        zip(classes, probas),
        key=lambda item: item[1],
        reverse=True
    )[:top_n]

    return [
        {"label": str(label), "confidence": float(confidence)}
        for label, confidence in ranked
    ]


def _predict_with_confidence(model: Any, text: str) -> tuple[str, float, list[dict]]:
    candidates = predict_top_candidates(model, text=text, top_n=3)
    best = candidates[0]
    return best["label"], best["confidence"], candidates


def classify_with_local_model(text: str, model_type: str) -> dict:
    models = get_local_models()

    if model_type not in models:
        raise ValueError(f"Modelo local inválido: {model_type}")

    cleaned_text = text.strip()
    if not cleaned_text:
        raise ValueError("O texto não pode estar vazio.")

    macro_model = models[model_type]["macro"]
    specialist_models = models[model_type]["specialists"]

    macro_pred, macro_confidence, macro_candidates = _predict_with_confidence(macro_model, cleaned_text)

    detail_model = specialist_models.get(macro_pred)
    if detail_model is None:
        available_macros = sorted(specialist_models.keys())
        raise ValueError(
            f"Não existe modelo especialista para a macro prevista '{macro_pred}'. "
            f"Macros disponíveis: {available_macros}"
        )

    detail_pred, detail_confidence, detail_candidates = _predict_with_confidence(detail_model, cleaned_text)

    return {
        "macro": macro_pred,
        "macro_confidence": macro_confidence,
        "micro": detail_pred,
        "micro_confidence": detail_confidence,
        "model": model_type,
        "is_ambiguous": bool(macro_confidence < 0.60 or detail_confidence < 0.60),
        "metadata": {
            "macro_candidates": macro_candidates,
            "micro_candidates": detail_candidates,
        },
    }


def get_local_candidates_for_text(text: str) -> dict:
    cleaned_text = text.strip()
    if not cleaned_text:
        raise ValueError("O texto não pode estar vazio.")

    models = get_local_models()
    macro_model = models["local_lr"]["macro"]
    specialist_models = models["local_lr"]["specialists"]

    macro_candidates = predict_top_candidates(macro_model, cleaned_text, top_n=3)

    micro_candidates_by_macro = {}
    for candidate in macro_candidates[:2]:
        macro_label = candidate["label"]
        detail_model = specialist_models.get(macro_label)
        if detail_model is not None:
            micro_candidates_by_macro[macro_label] = predict_top_candidates(detail_model, cleaned_text, top_n=3)

    return {
        "macro_candidates": macro_candidates,
        "micro_candidates_by_macro": micro_candidates_by_macro,
    }