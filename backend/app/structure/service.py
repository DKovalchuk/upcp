from sqlalchemy.orm import Session

from app.shared.errors import Conflict, NotFound
from app.shared.text import slugify
from app.structure.models import Component, Module


class ComponentService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, *, project_id: str, name: str, slug: str | None = None, description: str | None = None, status: str = "active") -> Component:
        final_slug = slug or slugify(name)
        existing = self._session.query(Component).filter_by(project_id=project_id, slug=final_slug).first()
        if existing:
            raise Conflict(f"slug '{final_slug}' already exists in project")
        comp = Component(project_id=project_id, name=name, slug=final_slug, description=description, status=status)
        self._session.add(comp)
        self._session.flush()
        return comp

    def get(self, component_id: str) -> Component:
        comp = self._session.get(Component, component_id)
        if not comp:
            raise NotFound(f"component '{component_id}' not found")
        return comp

    def update(self, component_id: str, **fields: str | None) -> Component:
        comp = self.get(component_id)
        if "slug" in fields and fields["slug"] is not None:
            existing = self._session.query(Component).filter(
                Component.project_id == comp.project_id,
                Component.slug == fields["slug"],
                Component.id != component_id,
            ).first()
            if existing:
                raise Conflict(f"slug '{fields['slug']}' already exists in project")
        for key, value in fields.items():
            if value is not None:
                setattr(comp, key, value)
        self._session.flush()
        return comp

    def delete(self, component_id: str) -> None:
        comp = self.get(component_id)
        self._session.delete(comp)
        self._session.flush()

    def list_components(self, project_id: str, *, offset: int = 0, limit: int = 20) -> tuple[list[Component], int]:
        q = self._session.query(Component).filter_by(project_id=project_id)
        total = q.count()
        items = q.offset(offset).limit(limit).all()
        return items, total


class ModuleService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, *, component_id: str, name: str, slug: str | None = None, description: str | None = None, status: str = "active") -> Module:
        final_slug = slug or slugify(name)
        existing = self._session.query(Module).filter_by(component_id=component_id, slug=final_slug).first()
        if existing:
            raise Conflict(f"slug '{final_slug}' already exists in component")
        mod = Module(component_id=component_id, name=name, slug=final_slug, description=description, status=status)
        self._session.add(mod)
        self._session.flush()
        return mod

    def get(self, module_id: str) -> Module:
        mod = self._session.get(Module, module_id)
        if not mod:
            raise NotFound(f"module '{module_id}' not found")
        return mod

    def update(self, module_id: str, **fields: str | None) -> Module:
        mod = self.get(module_id)
        if "slug" in fields and fields["slug"] is not None:
            existing = self._session.query(Module).filter(
                Module.component_id == mod.component_id,
                Module.slug == fields["slug"],
                Module.id != module_id,
            ).first()
            if existing:
                raise Conflict(f"slug '{fields['slug']}' already exists in component")
        for key, value in fields.items():
            if value is not None:
                setattr(mod, key, value)
        self._session.flush()
        return mod

    def delete(self, module_id: str) -> None:
        mod = self.get(module_id)
        self._session.delete(mod)
        self._session.flush()

    def list_modules(self, component_id: str, *, offset: int = 0, limit: int = 20) -> tuple[list[Module], int]:
        q = self._session.query(Module).filter_by(component_id=component_id)
        total = q.count()
        items = q.offset(offset).limit(limit).all()
        return items, total
