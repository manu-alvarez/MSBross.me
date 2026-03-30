import pytest
from unittest.mock import AsyncMock
from app.application.use_cases.chat_use_case import ChatUseCase
from app.domain.entities import AIResponse

@pytest.mark.asyncio
async def test_chat_use_case_execute_text():
    # Arrange (Mocks)
    mock_llm = AsyncMock()
    mock_llm.process_chat.return_value = ("Respuesta simulada", None, "happy")
    
    mock_audio = AsyncMock()
    mock_audio.generate_speech.return_value = "/temp_audio/mock.mp3"
    
    use_case = ChatUseCase(llm_adapter=mock_llm, audio_adapter=mock_audio)
    
    # Act
    result = await use_case.execute_text("Comando de prueba")
    
    # Assert
    assert isinstance(result, AIResponse)
    assert result.response == "Respuesta simulada"
    assert result.emotion == "happy"
    assert result.audio_url == "/temp_audio/mock.mp3"
    assert result.transcript == "Comando de prueba"
    
    mock_llm.process_chat.assert_called_once()
    mock_audio.generate_speech.assert_called_once_with("Respuesta simulada")
