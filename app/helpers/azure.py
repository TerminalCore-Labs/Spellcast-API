import azure.cognitiveservices.speech as speechsdk
from app.config import DEFAULT_VOICE
import unicodedata
import tempfile
import os
import time

# def build_ssml(text: str, voice: str) -> str:
#     return f"""
#     <speak version='1.0' xml:lang='es-ES'>
#     <voice xml:lang='es-ES' xml:gender='Male' name='{voice}'>
#         {text}
#     </voice>
#     </speak>
#     """

class TimelineManager:
    def __init__(self):
        self.timeline = []
        self.current_words = []
        self.start_tick = 0

    def on_word_boundary(self, event):
        try:
            word = event.text.strip()
            if not word: return

            print(f"DEBUG - Palabra recibida: [{word}]")
            
            if not self.current_words:
                self.start_tick = event.audio_offset
            
            self.current_words.append(word)

            cuts = ('.', '!', '?', ';')
            
            if any(c in word for c in cuts):
                print(f"--- MATCH DETECTADO ---:", word)
                duration_ticks = int(event.duration.total_seconds()* 10_000_000)
                end_tick = event.audio_offset + duration_ticks
                self.close_phrase(end_tick)
        except Exception as e:
            print('error en evento', e)
                
    def close_phrase(self, end_tick):
        if not self.current_words:
            return

        full_text = " ".join(self.current_words).strip()
        print('texto completo:', full_text)
        new_dict = {
            "text": full_text,
            "start": (self.start_tick) // 10000,
            "end": (end_tick)// 10000
        }
        self.timeline.append(new_dict)

        self.current_words.clear()
        print('suma luego de limpiar: ', len(self.current_words))
        self.start_tick = 0
        print(f"--- FRASE GUARDADA: [{full_text[:15]}...] | Total: {len(self.timeline)}")

    def get_final_timeline(self, final_duration_ticks):
        if self.current_words and any(w.strip() for w in self.current_words):
            self.close_phrase(final_duration_ticks)
        print(f"DEBUG TIMELINE: {self.timeline}")
        return self.timeline

def remove_file(path):
    try:
        os.remove(path)
        print('Archivo temporal eliminado correctamente')
    except Exception as e: 
        print(f'Error eliminando archivo temporal: {e}')

def build_audio_timeline(text, key, region):
    manager = TimelineManager()

    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
    temp_path = tmp_file.name
    tmp_file.close()

    speech_config = speechsdk.SpeechConfig(subscription=key, region=region)   
    audio_config = speechsdk.audio.AudioConfig(filename=temp_path)
    synthesizer= speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    #callback:
    synthesizer.synthesis_word_boundary.connect(manager.on_word_boundary)
    result = synthesizer.speak_ssml_async(text).get()
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        total_ticks = int(result.audio_duration.total_seconds() * 10_000_000)
        timeline = manager.get_final_timeline(total_ticks)

        return temp_path, timeline
    else:
        print(f"Error en síntesis: {result.reason}")
        return None, []

def build_ssml(segmentos: list):
    ssml = ("<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' "
            "xmlns:mstts='http://www.w3.org/2001/mstts' xml:lang='es-ES'>"
            )
    for segmento in segmentos:
        voice_name = segmento["voice"]
        if voice_name in ["default", None]:
            voice_name = DEFAULT_VOICE
        text = segmento["text"]
        style = segmento["inflection"]

        if style != "default":
            block = f'<voice name="{voice_name}"><mstts:express-as style="{style}">{text}</mstts:express-as></voice>'
        else:
            block = f'<voice name="{voice_name}">{text}</voice>'

        ssml+=block

    ssml+= "</speak>"

    return ssml
        



