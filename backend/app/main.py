from contextlib import asynccontextmanager

from fastapi import FastAPI

import app.db.models
from app.api.routes import router
from app.core.constants import MACRO_DETAIL_MAP, CLASSIFIERS_DESCRIPTIONS
from app.db.models.base import Base
from app.db.repositories.categories_repository import CategoryRepository
from app.db.repositories.classifiers_repository import ClassifierRepository
from app.db.session import SessionLocal, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        classifier_repo = ClassifierRepository(db)
        for classifier_name, classifier_description in CLASSIFIERS_DESCRIPTIONS.items():
            classifier_repo.get_or_create(name=classifier_name, description=classifier_description)

        category_repo = CategoryRepository(db)
        for macro_name, detail_names in MACRO_DETAIL_MAP.items():
            macro = category_repo.get_or_create_macro(macro_name)
            for detail_name in detail_names:
                category_repo.get_or_create_detail(detail_name, macro.id)

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    yield


app = FastAPI(
    title="XPTO Case - Classificação de Texto",
    lifespan=lifespan,
)

app.include_router(router)