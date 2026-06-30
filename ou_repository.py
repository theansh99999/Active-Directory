from models import db, OrganizationalUnit, User, Group, Computer

class OURepository:
    """Repository for handling Organizational Unit database operations."""

    @staticmethod
    def get_by_id(ou_id: int) -> OrganizationalUnit:
        return OrganizationalUnit.query.get(ou_id)

    @staticmethod
    def get_all() -> list[OrganizationalUnit]:
        return OrganizationalUnit.query.all()

    @staticmethod
    def find_by_name_and_parent(name: str, parent_id: int | None) -> OrganizationalUnit | None:
        return OrganizationalUnit.query.filter_by(name=name, parent_id=parent_id).first()

    @staticmethod
    def create(ou: OrganizationalUnit) -> OrganizationalUnit:
        db.session.add(ou)
        db.session.commit()
        return ou

    @staticmethod
    def update(ou: OrganizationalUnit) -> OrganizationalUnit:
        db.session.commit()
        return ou

    @staticmethod
    def delete(ou: OrganizationalUnit) -> None:
        db.session.delete(ou)
        db.session.commit()

    @staticmethod
    def get_children(ou_id: int) -> list[OrganizationalUnit]:
        return OrganizationalUnit.query.filter_by(parent_id=ou_id).all()
