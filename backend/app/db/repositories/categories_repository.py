from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.models.category import MacroCategory, DetailCategory


class CategoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_macro_by_name(self, name: str):
        stmt = select(MacroCategory).where(MacroCategory.name == name)
        return self.db.execute(stmt).scalar_one_or_none()

    def create_macro(self, name: str):
        macro = MacroCategory(name=name)
        self.db.add(macro)
        self.db.flush()
        return macro

    def get_or_create_macro(self, name: str):
        macro = self.get_macro_by_name(name)
        if macro:
            return macro
        return self.create_macro(name)

    def get_detail_by_name_and_macro(self, name: str, macro_id: int):
        stmt = select(DetailCategory).where(
            DetailCategory.name == name,
            DetailCategory.macro_category_id == macro_id
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create_detail(self, name: str, macro_id: int):
        detail = DetailCategory(name=name, macro_category_id=macro_id)
        self.db.add(detail)
        self.db.flush()
        return detail

    def get_or_create_detail(self, name: str, macro_id: int):
        detail = self.get_detail_by_name_and_macro(name, macro_id)
        if detail:
            return detail
        return self.create_detail(name, macro_id)

    def get_hierarchy(self):
        macros = (
            self.db.query(MacroCategory)
            .options(joinedload(MacroCategory.detail_categories))
            .order_by(MacroCategory.name)
            .all()
        )

        return {
            "macro_labels": [macro.name for macro in macros],
            "macro_to_micro": {
                macro.name: sorted([detail.name for detail in macro.detail_categories])
                for macro in macros
            }
        }