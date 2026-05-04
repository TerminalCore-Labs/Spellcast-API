from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.integrations.alchemy import get_db
from app.models.user import Users, UserSubscription
from app.interfaces.editor import Node
from app.integrations.fernet import decrypt_str
from app.helpers.azure import build_ssml, remove_file, build_audio_timeline
from app.config import DEFAULT_VOICE
from app.utils.parser import parser_nodes
import os, httpx
import tempfile

router = APIRouter(prefix="/tts", tags=["tts"])

@router.post('/')
async def text_to_speech(body: Node, own_credentials: bool=False, db: Session = Depends(get_db), request: Request=None): 
    user_id = request.state.user.get('id')
    user= db.query(Users).filter(Users.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    segments = parser_nodes(body)
            
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

    # endpoint = f"https://{service_region}.tts.speech.microsoft.com/cognitiveservices/v1"
    
    # headers = {
    #     "Ocp-Apim-Subscription-Key": azure_api_key,
    #     "Content-Type": "application/ssml+xml",
    #     "X-Microsoft-OutputFormat": "audio-16khz-32kbitrate-mono-mp3",
    #     "User-Agent": "fastapi-tts"
    # }

    # print("--- SSML GENERADO ---")
    # print(ssml)
    # print("---------------------")

    ssml = build_ssml(segments).strip()
    temp_path, timeline= build_audio_timeline(text=ssml, key=azure_api_key, region=service_region)
    
    # async with httpx.AsyncClient(timeout=None) as client:
    #     response = await client.post(endpoint, headers= headers, content=ssml)
    #     if response.status_code != 200:
    #         print(f"DEBUG AZURE ERROR: {response.text}")
    #         raise HTTPException(status_code=response.status_code, detail= response.text)
    
    # tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
    # tmp_file.write(response.content)
    # tmp_file.flush()
    # tmp_file.close()

    file_stream = open(temp_path, mode='rb')
    
    def iterfile():
        try:
            yield from file_stream
        finally: 
            file_stream.close()
            remove_file(temp_path)
    
    return StreamingResponse(  
        iterfile(), media_type='audio/mpeg',
        headers={"Content-Disposition": 'attachment; filename="tts.mp3"',
                 "X-Timeline": str(timeline)
                 }
            )
    
