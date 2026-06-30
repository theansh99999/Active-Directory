from models import OrganizationalUnit
from ou_repository import OURepository

class OUServiceError(Exception):
    pass

class OUService:
    """Service layer for Organizational Unit business logic."""

    @staticmethod
    def create_ou(name: str, description: str, parent_id: int | None) -> OrganizationalUnit:
        # Check duplicate
        existing = OURepository.find_by_name_and_parent(name, parent_id)
        if existing:
            raise OUServiceError(f"An OU named '{name}' already exists under the selected parent.")

        ou = OrganizationalUnit(name=name, description=description, parent_id=parent_id)
        return OURepository.create(ou)

    @staticmethod
    def update_ou(ou_id: int, name: str, description: str, parent_id: int | None) -> OrganizationalUnit:
        ou = OURepository.get_by_id(ou_id)
        if not ou:
            raise OUServiceError("OU not found.")

        # Check duplicate if name or parent changed
        if ou.name != name or ou.parent_id != parent_id:
            existing = OURepository.find_by_name_and_parent(name, parent_id)
            if existing and existing.id != ou.id:
                raise OUServiceError(f"An OU named '{name}' already exists under the selected parent.")

        # Check circular hierarchy
        if parent_id is not None:
            if parent_id == ou.id:
                raise OUServiceError("An OU cannot be its own parent.")
            
            # Walk up to check if any ancestor is the current OU
            current_parent = OURepository.get_by_id(parent_id)
            while current_parent:
                if current_parent.id == ou.id:
                    raise OUServiceError("Cannot move an OU to become a child of its own descendant.")
                if current_parent.parent_id:
                    current_parent = OURepository.get_by_id(current_parent.parent_id)
                else:
                    break

        ou.name = name
        ou.description = description
        ou.parent_id = parent_id
        return OURepository.update(ou)

    @staticmethod
    def delete_ou(ou_id: int) -> None:
        ou = OURepository.get_by_id(ou_id)
        if not ou:
            raise OUServiceError("OU not found.")
        
        if ou.children:
            raise OUServiceError("Cannot delete OU because it contains child OUs. Move or delete them first.")
        if ou.users:
            raise OUServiceError("Cannot delete OU because it contains users. Move them first.")
        if ou.groups:
            raise OUServiceError("Cannot delete OU because it contains groups. Move them first.")
        if ou.computers:
            raise OUServiceError("Cannot delete OU because it contains computers. Move them first.")

        OURepository.delete(ou)

    @staticmethod
    def get_tree() -> list[dict]:
        ous = OURepository.get_all()
        ou_map = {ou.id: {
            "id": ou.id,
            "name": ou.name,
            "description": ou.description,
            "created_at": ou.created_at.isoformat() if ou.created_at else None,
            "updated_at": ou.updated_at.isoformat() if hasattr(ou, 'updated_at') and ou.updated_at else None,
            "children": []
        } for ou in ous}

        roots = []
        for ou in ous:
            if ou.parent_id:
                if ou.parent_id in ou_map:
                    ou_map[ou.parent_id]["children"].append(ou_map[ou.id])
            else:
                roots.append(ou_map[ou.id])
        return roots

    @staticmethod
    def get_ou_objects(ou_id: int) -> dict:
        ou = OURepository.get_by_id(ou_id)
        if not ou:
            raise OUServiceError("OU not found.")
        
        return {
            "users": [{"id": u.id, "username": u.username, "email": u.email} for u in ou.users],
            "groups": [{"id": g.id, "name": g.name} for g in ou.groups],
            "computers": [{"id": c.id, "name": c.name, "status": c.status} for c in ou.computers],
            "children": [{"id": c.id, "name": c.name} for c in ou.children]
        }
