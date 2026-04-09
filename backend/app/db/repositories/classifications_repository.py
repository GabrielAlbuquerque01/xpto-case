from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.db.models.classification import Classification
from app.db.models.category import MacroCategory, DetailCategory


class ClassificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_classification(
        self,
        text: str,
        model_type: str,
        macro_category_id: int,
        detail_category_id: int,
        macro_confidence: float,
        detail_confidence: float,
        is_ambiguous: bool = False,
        metadata_json: dict | None = None,
    ):
        classification = Classification(
            text=text,
            model_type=model_type,
            macro_category_id=macro_category_id,
            detail_category_id=detail_category_id,
            macro_confidence=macro_confidence,
            detail_confidence=detail_confidence,
            is_ambiguous=is_ambiguous,
            metadata_json=metadata_json,
        )
        self.db.add(classification)
        self.db.flush()
        self.db.refresh(classification)
        return classification

    def list_classifications(self, limit: int = 100):
        stmt = (
            select(Classification)
            .options(
                joinedload(Classification.macro_category),
                joinedload(Classification.detail_category)
            )
            .order_by(Classification.created_at.desc())
            .limit(limit)
        )
        return self.db.execute(stmt).scalars().all()

    def get_summary_metrics(self) -> dict:
        total = self.db.scalar(select(func.count(Classification.id))) or 0
        by_model = self.db.execute(
            select(Classification.model_type, func.count(Classification.id))
            .group_by(Classification.model_type)
            .order_by(func.count(Classification.id).desc())
        ).all()
        ambiguous = self.db.scalar(
            select(func.count(Classification.id)).where(Classification.is_ambiguous.is_(True))
        ) or 0
        avg_macro_conf = self.db.scalar(select(func.avg(Classification.macro_confidence))) or 0.0
        avg_detail_conf = self.db.scalar(select(func.avg(Classification.detail_confidence))) or 0.0

        return {
            "total_predictions": int(total),
            "ambiguous_predictions": int(ambiguous),
            "ambiguity_rate": float(ambiguous / total) if total else 0.0,
            "avg_macro_confidence": float(avg_macro_conf),
            "avg_micro_confidence": float(avg_detail_conf),
            "by_model": [
                {"label": model_type, "value": int(count)}
                for model_type, count in by_model
            ],
        }

    def get_distribution_metrics(self) -> dict:
        macro_dist = self.db.execute(
            select(MacroCategory.name, func.count(Classification.id))
            .join(Classification, Classification.macro_category_id == MacroCategory.id)
            .group_by(MacroCategory.name)
            .order_by(func.count(Classification.id).desc(), MacroCategory.name.asc())
        ).all()

        micro_dist = self.db.execute(
            select(DetailCategory.name, func.count(Classification.id))
            .join(Classification, Classification.detail_category_id == DetailCategory.id)
            .group_by(DetailCategory.name)
            .order_by(func.count(Classification.id).desc(), DetailCategory.name.asc())
        ).all()

        daily_volume = self.db.execute(
            select(
                func.date_trunc('day', Classification.created_at).label('day'),
                func.count(Classification.id)
            )
            .group_by('day')
            .order_by('day')
        ).all()

        return {
            "macro_distribution": [
                {"label": label, "value": int(value)}
                for label, value in macro_dist
            ],
            "micro_distribution": [
                {"label": label, "value": int(value)}
                for label, value in micro_dist
            ],
            "daily_volume": [
                {"date": day.isoformat() if hasattr(day, 'isoformat') else str(day), "value": int(value)}
                for day, value in daily_volume
            ],
        }