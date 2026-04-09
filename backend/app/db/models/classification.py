from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Float, Boolean, JSON, func
from sqlalchemy.orm import relationship

from app.db.models.base import Base


class Classification(Base):
    __tablename__ = "classifications"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    classifier_id = Column(Integer, ForeignKey("classifiers.id", ondelete="RESTRICT"), nullable=False)

    macro_category_id = Column(Integer, ForeignKey("macro_categories.id", ondelete="RESTRICT"), nullable=False)
    detail_category_id = Column(Integer, ForeignKey("detail_categories.id", ondelete="RESTRICT"), nullable=False)

    macro_confidence = Column(Float, nullable=False, default=0.0)
    detail_confidence = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    macro_category = relationship("MacroCategory", back_populates="classifications")
    detail_category = relationship("DetailCategory", back_populates="classifications")
    classifier = relationship("Classifier", back_populates="classifications")