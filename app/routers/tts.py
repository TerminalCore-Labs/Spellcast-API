from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.integrations.alchemy import get_db
from app.models.user import Users, UserSubscription
from app.interfaces.editor import Node
from app.integrations.fernet import decrypt_str
from app.helpers.azure import build_ssml, remove_file, build_audio_timeline, build_audio_apirest
from app.config import DEFAULT_VOICE
from app.utils.parser import parser_nodes
import os, httpx, io, json

router = APIRouter(prefix="/tts", tags=["tts"])

@router.post('/')
async def text_to_speech(body: Node, own_credentials: bool=True, with_timeline: bool=False, db: Session = Depends(get_db), request: Request=None): 
    user_id = request.state.user.get('id')
    user= db.query(Users).filter(Users.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

            
    if user.subscription.plan == 'subscriber' and own_credentials==False:
        azure_api_key =os.getenv("AZURE_API_KEY")
        service_region = "brazilsouth"
    elif user.subscription.plan == 'subscriber' and own_credentials==True:
        credentials = db.query(UserSubscription).filter(UserSubscription.user_id == user_id).first().credential

        azure_api_key = credentials.azure_key
        service_region = credentials.region
        azure_api_key = decrypt_str(azure_api_key)
    elif user.subscription.plan == 'freemium' and own_credentials==True:
        credentials = db.query(UserSubscription).filter(UserSubscription.user_id == user_id).first().credential

        azure_api_key = credentials.azure_key
        service_region = credentials.region
        azure_api_key = decrypt_str(azure_api_key)
    else:
        raise HTTPException(status_code=403, detail="Process error. Please contact support.")


    segments = parser_nodes(body)
    if with_timeline:
        ssml = build_ssml(segments).strip()
        temp_path, timeline= await run_in_threadpool(build_audio_timeline, text=ssml, key=azure_api_key, region=service_region)
        file_stream = open(temp_path, mode='rb')
        def iterfile():
            try:
                yield from file_stream
            finally: 
                file_stream.close()
                remove_file(temp_path)
    else:
        ssml = build_ssml(segments)
        audio_bytes = await build_audio_apirest(ssml=ssml, azure_api_key=azure_api_key, service_region=service_region)
        file_stream = io.BytesIO(audio_bytes)

        def iterfile():
            yield from file_stream 
    
    headers={"Content-Disposition": 'attachment; filename="tts.mp3"'}
    
    if with_timeline:
        json_timeline = json.dumps(timeline, ensure_ascii=False)
        headers["X-Timeline"] = json_timeline.encode('utf-8').decode('latin-1')
        headers["Access-Control-Expose-Headers"] = "X-Timeline"
    
    return StreamingResponse(  
        iterfile(), media_type='audio/mpeg',
        headers=headers
            )
    
