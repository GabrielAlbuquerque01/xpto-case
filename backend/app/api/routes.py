from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.repositories.classifications_repository import ClassificationRepository
from app.db.session import get_db
from app.pipelines.classify import run_classification_pipeline
from app.schemas.classification import (
    ClassificationRequest,
    ClassificationResponse,
    GetClassificationResponse,
    MetricsDistributionResponse,
    MetricsSummaryResponse,
)

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/models")
def list_models():
    return {"models": ["local_lr", "openai"]}


@router.post("/classify", response_model=ClassificationResponse)
def classify(req: ClassificationRequest, db: Session = Depends(get_db)):
    try:
        return run_classification_pipeline(
            db=db,
            text=req.text,
            model_type=req.model_type,
            save_prediction=req.save_prediction,
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predictions", response_model=list[GetClassificationResponse])
def list_predictions(db: Session = Depends(get_db), limit: int = 100):
    repo = ClassificationRepository(db)
    predictions = repo.list_classifications(limit=limit)

    return [
        GetClassificationResponse(
            id=p.id,
            text=p.text,
            model_type=p.model_type,
            macro=p.macro_category.name,
            micro=p.detail_category.name,
            macro_confidence=p.macro_confidence,
            micro_confidence=p.detail_confidence,
            is_ambiguous=p.is_ambiguous,
            created_at=p.created_at,
        )
        for p in predictions
    ]


@router.get("/metrics/summary", response_model=MetricsSummaryResponse)
def metrics_summary(db: Session = Depends(get_db)):
    repo = ClassificationRepository(db)
    return repo.get_summary_metrics()


@router.get("/metrics/distributions", response_model=MetricsDistributionResponse)
def metrics_distributions(db: Session = Depends(get_db)):
    repo = ClassificationRepository(db)
    return repo.get_distribution_metrics()