from app.integrations.alchemy import engine, Base
from sqlalchemy import Column, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
from uuid import uuid4

class Spell(Base):
    __tablename__ = "spell"
    __table_args__ = {"schema": "spellcast"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    # `type`/`file_path` are agnostic to what's actually uploaded (see routers/spell.py's
    # presigned-URL flow) -- this table never persists a PDF binary itself, so there is
    # nothing PDF-specific to solve here (TCORE-90: the original PDF, when a user keeps
    # one, lives client-side only, in Spellcast-Client's own IndexedDB store).
    type = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    visibility = Column(String, nullable=False, server_default="private")
    transcribed_from = Column(UUID(as_uuid=True), ForeignKey("spellcast.spell.id", ondelete="SET NULL"), nullable=True)
    root_spell_id = Column(UUID(as_uuid=True), nullable=True)
    review_status = Column(String, nullable=False, server_default="none")
    description = Column(Text, nullable=True)
    author = Column(String, nullable=True)
    tags = Column(JSONB, nullable=False, server_default="[]")
    language = Column(String, nullable=True)

class SpellReview(Base):
    __tablename__ = "spellreview"
    __table_args__ = {"schema": "spellcast"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    spell_id = Column(UUID(as_uuid=True), ForeignKey("spellcast.spell.id"), nullable=False)
    submitted_by = Column(UUID(as_uuid=True), ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=True)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=True)
    status = Column(String, nullable=False, server_default='pending')
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)

    spell = relationship("Spell")
Spell.spellreview = relationship(
    SpellReview,
    back_populates="spell",
    uselist=False
)

class SpellGrimoire(Base):
    __tablename__ = "spellgrimoire"
    __table_args__ = {"schema": "spellcast"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    spell_id = Column(UUID(as_uuid=True), ForeignKey("spellcast.spell.id"), nullable=True)
    grimoire_id = Column(UUID(as_uuid=True), ForeignKey("spellcast.grimoire.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    spell = relationship("Spell")
    grimoire = relationship("Grimoire")

# Note: back_populates below don't actually correspond to any back_populates on the
# `spell`/`grimoire` relationships declared inside SpellGrimoire above (those have none) —
# this mismatch predates the Document->Spell rename (TCORE-78) and is not something this
# rename introduced or attempted to fix.
Spell.spellgrimoire = relationship(
    SpellGrimoire,
    back_populates="spell",
    uselist=False
)