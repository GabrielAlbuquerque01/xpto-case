from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.db.models.classification import Classification
from app.db.models.category import MacroCategory, DetailCategory
from app.db.models.classifier import Classifier


class ClassificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_classification(self, text: str, classifier_id: int, macro_category_id: int, detail_category_id: int, macro_confidence: float, detail_confidence: float,):
        classification = Classification(
            text=text,
            classifier_id=classifier_id,
            macro_category_id=macro_category_id,
            detail_category_id=detail_category_id,
            macro_confidence=macro_confidence,
            detail_confidence=detail_confidence,
        )
        self.db.add(classification)
        self.db.flush()
        self.db.refresh(classification)
        return classification

    def list_classifications(self, limit: int = 100):
        stmt = (
            select(Classification)
            .options(
                joinedload(Classification.classifier),
                joinedload(Classification.macro_category),
                joinedload(Classification.detail_category),
            )
            .order_by(Classification.created_at.desc())
            .limit(limit)
        )
        return self.db.execute(stmt).scalars().all()

    def get_summary_metrics(self) -> dict:
        total = self.db.scalar(select(func.count(Classification.id))) or 0

        by_classifier = self.db.execute(
            select(Classifier.name, func.count(Classification.id))
            .join(Classification, Classification.classifier_id == Classifier.id)
            .group_by(Classifier.name)
            .order_by(func.count(Classification.id).desc())
        ).all()

        avg_macro_conf = self.db.scalar(
            select(func.avg(Classification.macro_confidence))
        ) or 0.0

        avg_detail_conf = self.db.scalar(
            select(func.avg(Classification.detail_confidence))
        ) or 0.0

        return {
            "total_predictions": int(total),
            "avg_macro_confidence": float(avg_macro_conf),
            "avg_detail_confidence": float(avg_detail_conf),
            "by_classifier": [
                {"label": label, "value": int(value)}
                for label, value in by_classifier
            ],
        }

    def get_distribution_metrics(self) -> dict:
        macro_dist = self.db.execute(
            select(MacroCategory.name, func.count(Classification.id))
            .join(Classification, Classification.macro_category_id == MacroCategory.id)
            .group_by(MacroCategory.name)
            .order_by(func.count(Classification.id).desc(), MacroCategory.name.asc())
        ).all()

        detail_dist = self.db.execute(
            select(DetailCategory.name, func.count(Classification.id))
            .join(Classification, Classification.detail_category_id == DetailCategory.id)
            .group_by(DetailCategory.name)
            .order_by(func.count(Classification.id).desc(), DetailCategory.name.asc())
        ).all()

        daily_volume = self.db.execute(
            select(
                func.date_trunc("day", Classification.created_at).label("day"),
                func.count(Classification.id)
            )
            .group_by("day")
            .order_by("day")
        ).all()

        return {
            "macro_distribution": [
                {"label": label, "value": int(value)}
                for label, value in macro_dist
            ],
            "detail_distribution": [
                {"label": label, "value": int(value)}
                for label, value in detail_dist
            ],
            "daily_volume": [
                {
                    "date": day.isoformat() if hasattr(day, "isoformat") else str(day),
                    "value": int(value),
                }
                for day, value in daily_volume
            ],
        }