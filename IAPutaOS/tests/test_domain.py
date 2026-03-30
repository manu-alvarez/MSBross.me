import pytest
from app.domain.entities import UserMessage, AIResponse

def test_user_message_creation():
    msg = UserMessage(text="Hola mundo")
    assert msg.text == "Hola mundo"

def test_ai_response_defaults():
    resp = AIResponse(transcript="Hola", response="Qué tal")
    assert resp.transcript == "Hola"
    assert resp.response == "Qué tal"
    assert resp.emotion == "neutral"
    assert resp.audio_url is None
    assert resp.vision_url is None
