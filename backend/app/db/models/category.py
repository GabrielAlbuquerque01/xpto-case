from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.models.base import Base

class MacroCategory(Base):
    __tablename__ = "macro_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True, index=True)

    detail_categories = relationship("DetailCategory", back_populates="macro_category", cascade="all, delete-orphan")
    classifications = relationship("Classification", back_populates="macro_category")

class DetailCategory(Base):
    __tablename__ = "detail_categories"
    __table_args__ = (UniqueConstraint("name", "macro_category_id", name="uq_detail_name_macro"),)

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    macro_category_id = Column(Integer, ForeignKey("macro_categories.id", ondelete="CASCADE"), nullable=False)

    macro_category = relationship("MacroCategory", back_populates="detail_categories")
    classifications = relationship("Classification", back_populates="detail_category")