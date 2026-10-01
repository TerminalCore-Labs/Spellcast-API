from uuid import uuid4
from app.integrations.alchemy import Base
from sqlalchemy import Column,ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.models.spell import SpellGrimoire

class Grimoire(Base):
    __tablename__ = "grimoire"
    __table_args__ = {"schema": "spellcast"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("accounts.users.id"), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("Users", uselist=False)


Grimoire.spellgrimoire = relationship(
    SpellGrimoire,
    back_populates="grimoire",
    uselist=False
)

