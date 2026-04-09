from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.db.models.classification import Classification
from app.db.models.classifier import Classifier
from app.db.models.category import MacroCategory, DetailCategory


class ClassificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_classification(
        self,
        text: str,
        classifier_id: int,
        macro_category_id: int,
        detail_category_id: int,
        macro_confidence: float,
        detail_confidence: float,
        secondary_predictions: list[dict],
    ):
        classification = Classification(
            text=text,
            classifier_id=classifier_id,
            macro_category_id=macro_category_id,
            detail_category_id=detail_category_id,
            macro_confidence=macro_confidence,
            detail_confidence=detail_confidence,
            secondary_predictions=secondary_predictions,
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

    def get_summary_metrics(self):
        total_predictions = self.db.scalar(
            select(func.count(Classification.id))
        ) or 0

        avg_macro_confidence = self.db.scalar(
            select(func.avg(Classification.macro_confidence))
        ) or 0.0

        avg_detail_confidence = self.db.scalar(
            select(func.avg(Classification.detail_confidence))
        ) or 0.0

        by_classifier_rows = self.db.execute(
            select(Classifier.name, func.count(Classification.id))
            .join(Classification, Classification.classifier_id == Classifier.id)
            .group_by(Classifier.name)
            .order_by(func.count(Classification.id).desc())
        ).all()

        return {
            "total_predictions": total_predictions,
            "avg_macro_confidence": float(avg_macro_confidence),
            "avg_detail_confidence": float(avg_detail_confidence),
            "by_classifier": [
                {"label": name, "value": count}
                for name, count in by_classifier_rows
            ],
        }

    def get_distribution_metrics(self):
        macro_rows = self.db.execute(
            select(MacroCategory.name, func.count(Classification.id))
            .join(Classification, Classification.macro_category_id == MacroCategory.id)
            .group_by(MacroCategory.name)
            .order_by(func.count(Classification.id).desc())
        ).all()

        detail_rows = self.db.execute(
            select(DetailCategory.name, func.count(Classification.id))
            .join(Classification, Classification.detail_category_id == DetailCategory.id)
            .group_by(DetailCategory.name)
            .order_by(func.count(Classification.id).desc())
        ).all()

        daily_rows = self.db.execute(
            select(
                func.date(Classification.created_at),
                func.count(Classification.id)
            )
            .group_by(func.date(Classification.created_at))
            .order_by(func.date(Classification.created_at))
        ).all()

        return {
            "macro_distribution": [
                {"label": name, "value": count}
                for name, count in macro_rows
            ],
            "detail_distribution": [
                {"label": name, "value": count}
                for name, count in detail_rows
            ],
            "daily_volume": [
                {"date": str(date_), "value": count}
                for date_, count in daily_rows
            ],
        }