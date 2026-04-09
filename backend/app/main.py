from contextlib import asynccontextmanager

from fastapi import FastAPI

import app.db.models
from app.api.routes import router
from app.core.constants import MACRO_MICRO_MAP
from app.db.models.base import Base
from app.db.repositories.categories_repository import CategoryRepository
from app.db.session import SessionLocal, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        repo = CategoryRepository(db)
        for macro_name, micro_names in MACRO_MICRO_MAP.items():
            macro = repo.get_or_create_macro(macro_name)
            for micro_name in micro_names:
                repo.get_or_create_detail(micro_name, macro.id)
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