"""
TTS (Text-to-Speech) 패키지
- edge: Microsoft Edge TTS (클라우드 API)
- qwen: Qwen3-TTS (로컬 실행, VoiceDesign)
"""

from enum import Enum
from typing import Optional, Literal


class TTSEngine(Enum):
    """TTS 엔진 종류"""
    EDGE = "edge"      # Microsoft Edge TTS (클라우드)
    QWEN = "qwen"      # Qwen3-TTS (로컬)


# Qwen3-TTS 음성 목록 가져오기
def get_available_voices(engine: TTSEngine = TTSEngine.QWEN):
    """
    사용 가능한 음성 목록 반환
    
    Args:
        engine: TTS 엔진 (기본값: TTSEngine.QWEN)
    
    Returns:
        음성 목록 딕셔너리
    """
    if engine == TTSEngine.QWEN:
        from .qwen import AVAILABLE_VOICES
        return AVAILABLE_VOICES
    elif engine == TTSEngine.EDGE:
        # Edge TTS 음성은 동적으로 조회
        return {"ko-KR-SunHiNeural": "Korean Female", "ko-KR-BongJinNeural": "Korean Male"}
    else:
        return {}


def list_voices(engine: TTSEngine = TTSEngine.QWEN):
    """
    사용 가능한 음성 목록 출력
    
    Args:
        engine: TTS 엔진 (기본값: TTSEngine.QWEN)
    """
    if engine == TTSEngine.QWEN:
        from .qwen import list_available_voices
        list_available_voices()
    elif engine == TTSEngine.EDGE:
        print("Edge TTS 음성 목록:")
        print("  - ko-KR-SunHiNeural (Korean Female)")
        print("  - ko-KR-BongJinNeural (Korean Male)")
        print("  - en-US-JennyNeural (English Female)")
        print("  - en-US-GuyNeural (English Male)")
        print("  - 등 (전체 목록: https://speech.microsoft.com/portal/voicegallery)")


# 공통 유틸리티 함수 (두 엔진 모두 사용)
def parse_yaml_to_text(yaml_path: str) -> str:
    """
    YAML 파일을 읽어 TTS 용 텍스트 스트립트로 변환
    
    Args:
        yaml_path: YAML 파일 경로
    
    Returns:
        TTS 변환용 텍스트
    """
    # edge 모듈의 함수를 사용 (qwen 도 동일한 구현 사용)
    from .edge import parse_yaml_to_text as edge_parse
    return edge_parse(yaml_path)


# 동적 임포트를 위한 래퍼 함수
async def yaml_to_tts(
    yaml_path: str,
    engine: TTSEngine = TTSEngine.EDGE,
    **kwargs
):
    """
    YAML 파일을 읽어서 MP3 생성
    
    Args:
        yaml_path: YAML 파일 경로
        engine: 사용할 TTS 엔진 (기본값: TTSEngine.EDGE)
        **kwargs: 각 TTS 엔진별 추가 인수
            For Qwen3-TTS:
                - voice: 화자 이름 (기본값: Sohee)
                - language: 언어 (기본값: Korean)
                - instruct: 음성 스타일 설명 (CustomVoice)
                - model_name: 모델 이름 (기본값: Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice)
                - device: 디바이스 (기본값: auto)
    
    Returns:
        생성된 MP3 파일 경로
    
    Examples:
        # Edge TTS 사용 (기본)
        await yaml_to_tts("data/20260319_1200.yaml")
        
        # Edge TTS with custom voice
        await yaml_to_tts("data/20260319_1200.yaml", engine=TTSEngine.EDGE, voice="ko-KR-SunHiNeural")
        
        # Qwen3-TTS 사용 (기본 음성: Sohee)
        await yaml_to_tts("data/20260319_1200.yaml", engine=TTSEngine.QWEN, voice="Sohee")
        
        # Qwen3-TTS VoiceDesign (음성 스타일 지정)
        await yaml_to_tts("data/20260319_1200.yaml", engine=TTSEngine.QWEN, 
                         voice="Sohee", instruct="따뜻한 아나운서 음성으로 읽어주세요")
    """
    if engine == TTSEngine.EDGE:
        from .edge import yaml_to_tts as edge_tts
        # Edge TTS는 voice만 허용
        edge_kwargs = {k: v for k, v in kwargs.items() if k in ('voice',)}
        return await edge_tts(yaml_path, **edge_kwargs)
    elif engine == TTSEngine.QWEN:
        from .qwen import yaml_to_tts as qwen_tts
        # Qwen TTS는 voice, language, instruct, model_name, device 허용
        qwen_kwargs = {k: v for k, v in kwargs.items()
                       if k in ('voice', 'language', 'instruct', 'model_name', 'device')}
        return await qwen_tts(yaml_path, **qwen_kwargs)
    else:
        raise ValueError(f"지원하지 않는 TTS 엔진: {engine}")


# 편의를 위한 별칭
yaml_to_tts_edge = lambda path, **kw: yaml_to_tts(path, engine=TTSEngine.EDGE, **kw)
yaml_to_tts_qwen = lambda path, **kw: yaml_to_tts(path, engine=TTSEngine.QWEN, **kw)


__all__ = [
    "TTSEngine",
    "yaml_to_tts",
    "yaml_to_tts_edge",
    "yaml_to_tts_qwen",
    "parse_yaml_to_text",
    "get_available_voices",
    "list_voices",
]
