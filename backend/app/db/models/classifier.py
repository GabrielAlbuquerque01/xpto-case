from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Float, Boolean, JSON, func
from sqlalchemy.orm import relationship

from app.db.models.base import Base


class Classifier(Base):
    __tablename__ = "classifiers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)

    classifications = relationship("Classification", back_populates="classifier")