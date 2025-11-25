from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.integrations.alchemy import get_db
from app.models import Users

router = APIRouter(prefix="/accounts", tags=["Accounts"])

@router.get('/')
async def get_user_data(request: Request, db: Session = Depends(get_db)): 
    user_id = request.state.user.get('id')
    user = db.query(Users).filter(Users.id == user_id).first()

    if not user:
        raise HTTPException(status_code = 404, detail = { 'message': "Usuario no encontrado", 'logged': False })
    
    userData = { 
        'id': user.id,
        'role': user.role,
        'email': user.email,
        'username': user.username,
        'isVerified': user.isVerified,
        'profilePic': user.profilePic or user.googlePic
    }    
    return ({ 'logged': True, 'userData': userData })







