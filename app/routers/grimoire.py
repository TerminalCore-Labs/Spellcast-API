from sqlalchemy.orm import Session
from app.models.grimoire import Grimoire, SpellGrimoire
from app.models.user import Users
from fastapi import APIRouter, Depends, Request, HTTPException
from app.integrations.alchemy import get_db

router = APIRouter(prefix="/grimoires", tags=["Grimoires"])

@router.post("/")
async def create_grimoire(request: Request, db: Session = Depends(get_db)):
    user_id = request.state.user.get('id')
    user= db.query(Users).filter(Users.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    body = await request.json()
    spell_id = body.get('spell_id')

    # Grimoire.user_id is unique — reuse the existing row for this user instead of
    # crashing on a duplicate-key insert (Grimoire itself has no spell_id column;
    # the spell/grimoire association lives in the SpellGrimoire junction table).
    grimoire = db.query(Grimoire).filter(Grimoire.user_id == user_id).first()
    if not grimoire:
        grimoire = Grimoire(user_id=user_id)
        db.add(grimoire)
        db.commit()
        db.refresh(grimoire)

    if spell_id:
        spell_grimoire = SpellGrimoire(
            spell_id = spell_id,
            grimoire_id = grimoire.id
        )
        db.add(spell_grimoire)
        db.commit()

    return()

@router.get("/")
def get_grimoires(request: Request, db: Session = Depends(get_db)):
    user_id = request.state.user.get('id')
    user= db.query(Users).filter(Users.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    grimoire = db.query(Grimoire).filter(Grimoire.user_id == user_id).first()
    if not grimoire:
        return None
    return grimoire
