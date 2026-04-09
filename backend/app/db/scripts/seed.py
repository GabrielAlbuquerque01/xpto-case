import app.db.models
from app.db.session import SessionLocal
from app.db.repositories.categories_repository import CategoryRepository
from app.core.constants import MACRO_MICRO_MAP


def run_seed_categories():
    db = SessionLocal()
    try:
        repo = CategoryRepository(db)

        for macro_name, micro_names in MACRO_MICRO_MAP.items():
            macro = repo.get_or_create_macro(macro_name)

            for micro_name in micro_names:
                repo.get_or_create_detail(micro_name, macro.id)

        db.commit()
        return {"message": "Categorias cadastradas com sucesso."}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    result = run_seed_categories()
    print(result)