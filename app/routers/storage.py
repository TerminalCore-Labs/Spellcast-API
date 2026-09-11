from fastapi import APIRouter, HTTPException, Request, Depends
from app.integrations.alchemy import get_db
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.models.user import Users
from app.models.grimoire import Spell, SpellGrimoire, Grimoire
from app.integrations.boto3 import generate_presigned_url, delete_file
import uuid

router = APIRouter(prefix="/storage", tags=["Storage"])

class FileUploadRequest(BaseModel):
    filename: str
    content_type: str  # ej: "image/png"

@router.post("/presigned-upload")
async def get_presigned_upload_url(data: FileUploadRequest):
    key = f"{data.content_type}/{uuid.uuid4()}-{data.filename}"
    try:
        url = generate_presigned_url(key, content_type=data.content_type)
        return {"upload_url": url, "key": key}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{key}")
async def delete_from_s3(request: Request, key: str, db: Session= Depends(get_db)):
    user_id = request.state.user.get('id')
    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    grimoire = db.query(Grimoire).filter(Grimoire.user_id == user_id).first()
    if not grimoire:
        raise HTTPException(status_code=404, detail="Current user doesn't have a Grimoire")
    spell_grimoire = db.query(SpellGrimoire).filter(SpellGrimoire.grimoire_id == grimoire.id).all() 
    spells = db.query(Spell).filter(Spell.id.in_([spell.spell_id for spell in spell_grimoire])).all()
    if not any(key in spell.file_path for spell in spells):
        raise HTTPException(status_code=404, detail="Spell doesn't belong to the current user")
    try:
        delete_file(key)
        return {"message": "Archivo eliminado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))