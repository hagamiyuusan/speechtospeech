from groq import AsyncGroq
from base.base_voice import IVoice
from fastapi import UploadFile
import io
class STT(IVoice):
    def __init__(self, api_key: str):
        self.client = AsyncGroq(api_key=api_key)

    async def generate_audio(self, input: UploadFile):
        # Read the file content
        file_content = await input.read()
        
        try:
            # Create a named BytesIO object with the correct file extension
            audio_file = io.BytesIO(file_content)
            audio_file.name = "audio.mp3" 
            
            response = await self.client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3",
                prompt="his audio contains a conversation about ASEAN which contains multiple languages. Please transcribe accurately.",
                response_format="verbose_json"
            )
            print(response)
            return {"text": response.text.strip(), "language": response.language}
        except Exception as e:
            raise RuntimeError(f"Transcription failed: {str(e)}")

