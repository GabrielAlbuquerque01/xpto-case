# from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func
# from sqlalchemy.orm import relationship
# from db.models.base import Base


# class Classifier(Base):
#     __tablename__ = "classifiers"

#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(Text, nullable=False)

#     classifications = relationship("Classification", back_populates="classifier")
