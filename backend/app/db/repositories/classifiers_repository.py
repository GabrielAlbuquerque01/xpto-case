from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.classifier import Classifier


class ClassifierRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_name(self, name: str):
        stmt = select(Classifier).where(Classifier.name == name)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_all(self):
        stmt = select(Classifier).order_by(Classifier.name.asc())
        return self.db.execute(stmt).scalars().all()

    def create(self, name: str, description: str | None = None):
        classifier = Classifier(name=name, description=description)
        self.db.add(classifier)
        self.db.flush()
        return classifier

    def get_or_create(self, name: str, description: str | None = None):
        existing = self.get_by_name(name)
        if existing:
            return existing
        return self.create(name=name, description=description)