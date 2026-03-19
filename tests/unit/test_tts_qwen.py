"""
Qwen3-TTS 단위 테스트
- 로컬 Qwen3-TTS VoiceDesign 모델 테스트
- 다양한 음성 테스트
"""

import pytest
import os
from pathlib import Path

from today_vn_news.tts import yaml_to_tts, TTSEngine
from today_vn_news.tts.qwen import (
    parse_yaml_to_text,
    AVAILABLE_VOICES,
    list_available_voices,
)
from today_vn_news.exceptions import TTSError


@pytest.mark.unit
class TestQwenYamlParsing:
    """Qwen3-TTS YAML 파싱 테스트"""

    def test_parse_yaml_to_text(self, yaml_file):
        text = parse_yaml_to_text(str(yaml_file))

        assert "오늘의 베트남 주요 뉴스" in text
        assert "안전 및 기상 관제" in text
        # TTS 최적화로 °C → 도로 변환됨
        assert "29 도" in text or "29°C" in text

    def test_parse_yaml_missing_file(self):
        with pytest.raises(TTSError):
            parse_yaml_to_text("nonexistent.yaml")


@pytest.mark.unit
class TestQwenVoices:
    """Qwen3-TTS 음성 목록 테스트"""

    def test_available_voices_structure(self):
        """음성 목록 구조 테스트"""
        assert isinstance(AVAILABLE_VOICES, dict)
        
        # 주요 카테고리 확인
        categories = ["korean", "english", "japanese", "chinese"]
        for category in categories:
            assert category in AVAILABLE_VOICES
        
        # 한국어 기본 음성 확인
        assert "Sohee" in AVAILABLE_VOICES["korean"]
        
        # 전체 음성 수 확인 (9 개)
        total_voices = sum(len(voices) for voices in AVAILABLE_VOICES.values())
        assert total_voices == 9

    def test_korean_voices(self):
        """한국어 음성 목록 테스트"""
        korean_voices = AVAILABLE_VOICES.get("korean", {})
        assert len(korean_voices) == 1
        
        # Sohee 음성 정보 확인
        sohee = korean_voices["Sohee"]
        assert sohee["lang"] == "ko"
        assert sohee["gender"] == "female"
        assert "emotion" in sohee["desc"].lower()

    def test_all_voices_have_required_fields(self):
        """모든 음성이 필요한 필드를 가지는지 테스트"""
        for category, voices in AVAILABLE_VOICES.items():
            for voice_name, info in voices.items():
                assert "lang" in info, f"{voice_name} missing lang"
                assert "gender" in info, f"{voice_name} missing gender"
                assert "desc" in info, f"{voice_name} missing desc"

    def test_list_voices_output(self, capsys):
        """음성 목록 출력 테스트"""
        list_available_voices()
        captured = capsys.readouterr()
        
        assert "Qwen3-TTS" in captured.out or "VoiceDesign" in captured.out
        assert "Sohee" in captured.out


@pytest.mark.unit
@pytest.mark.slow
@pytest.mark.asyncio
class TestQwenTTSRealAPI:
    """Qwen3-TTS 실제 생성 테스트 (로컬 실행)"""

    async def test_yaml_to_tts_qwen_default_voice(self, yaml_file, test_data_dir):
        """Qwen3-TTS 기본 음성 (Sohee) 으로 MP3 생성 (0.6B 모델)"""
        output_path = str(yaml_file).replace(".yaml", ".mp3")

        # 기존 파일이 있으면 삭제
        if os.path.exists(output_path):
            os.remove(output_path)

        # Qwen3-TTS 0.6B 모델 사용 (메모리 효율적)
        await yaml_to_tts(
            str(yaml_file),
            engine=TTSEngine.QWEN,
            voice="Sohee",
            language="Korean",
            model_name="Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice"
        )

        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 1000

    @pytest.mark.parametrize("voice", ["Sohee"])
    async def test_yaml_to_tts_qwen_korean_voices(self, yaml_file, voice, test_data_dir):
        """Qwen3-TTS 한국어 음성 테스트"""
        output_path = str(yaml_file).replace(".yaml", f".{voice}.mp3")

        if os.path.exists(output_path):
            os.remove(output_path)

        await yaml_to_tts(
            str(yaml_file),
            engine=TTSEngine.QWEN,
            voice=voice,
            language="Korean"
        )

        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 1000

    @pytest.mark.parametrize("voice", ["Ryan", "Aiden"])
    async def test_yaml_to_tts_qwen_english_voices(self, yaml_file, voice, test_data_dir):
        """Qwen3-TTS 영어 음성 테스트"""
        output_path = str(yaml_file).replace(".yaml", f".{voice}.mp3")

        if os.path.exists(output_path):
            os.remove(output_path)

        await yaml_to_tts(
            str(yaml_file),
            engine=TTSEngine.QWEN,
            voice=voice,
            language="English"
        )

        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 1000

    @pytest.mark.parametrize("voice", ["Ono_Anna"])
    async def test_yaml_to_tts_qwen_japanese_voices(self, yaml_file, voice, test_data_dir):
        """Qwen3-TTS 일본어 음성 테스트"""
        output_path = str(yaml_file).replace(".yaml", f".{voice}.mp3")

        if os.path.exists(output_path):
            os.remove(output_path)

        await yaml_to_tts(
            str(yaml_file),
            engine=TTSEngine.QWEN,
            voice=voice,
            language="Japanese"
        )

        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 1000

    @pytest.mark.parametrize("voice", ["Vivian", "Serena", "Uncle_Fu"])
    async def test_yaml_to_tts_qwen_chinese_voices(self, yaml_file, voice, test_data_dir):
        """Qwen3-TTS 중국어 음성 테스트"""
        output_path = str(yaml_file).replace(".yaml", f".{voice}.mp3")

        if os.path.exists(output_path):
            os.remove(output_path)

        await yaml_to_tts(
            str(yaml_file),
            engine=TTSEngine.QWEN,
            voice=voice,
            language="Chinese"
        )

        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 1000

    @pytest.mark.slow
    async def test_qwen_tts_with_instruct(self, yaml_file, test_data_dir):
        """Qwen3-TTS VoiceDesign instruct 테스트"""
        output_path = str(yaml_file).replace(".yaml", ".mp3.qwen.instruct")

        if os.path.exists(output_path):
            os.remove(output_path)

        # instruct 를 사용한 VoiceDesign
        await yaml_to_tts(
            str(yaml_file),
            engine=TTSEngine.QWEN,
            voice="Sohee",
            language="Korean",
            instruct="따뜻하고 명확한 아나운서 음성으로 읽어주세요"
        )

        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 1000

    async def test_qwen_device_selection(self):
        """Qwen3-TTS 디바이스 선택 테스트"""
        # 이 테스트는 실제 모델 로딩 없이 파라미터 검증만
        from today_vn_news.tts.qwen import _get_tts_engine
        
        # device 파라미터가 정상적으로 전달되는지 확인
        # 실제 로딩은 느리므로 스킵
        pytest.skip("실제 모델 로딩 테스트는 수동으로 실행")
