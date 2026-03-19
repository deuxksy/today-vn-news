"""
TTS 모듈 단위 테스트
- edge-tts (클라우드 API)
- Qwen3-TTS (로컬 실행)
"""

import pytest
import os
from today_vn_news.tts import parse_yaml_to_text, yaml_to_tts, TTSEngine
from today_vn_news.exceptions import TTSError


@pytest.mark.unit
class TestYamlParsing:
    """YAML 파싱 테스트 (메모리 연산)"""

    def test_parse_yaml_to_text(self, yaml_file):
        text = parse_yaml_to_text(str(yaml_file))

        assert "오늘의 베트남 주요 뉴스" in text
        assert "안전 및 기상 관제" in text
        # TTS 최적화로 °C → 도로 변환됨
        assert "29 도" in text or "29°C" in text

    def test_parse_yaml_empty_file(self, test_data_dir, test_timestamp):
        empty_yaml = test_data_dir / f"{test_timestamp}_empty.yaml"
        empty_yaml.write_text("metadata: {}\nsections: []")

        text = parse_yaml_to_text(str(empty_yaml))
        assert len(text) > 0

    def test_parse_yaml_missing_file(self):
        with pytest.raises(TTSError):
            parse_yaml_to_text("nonexistent.yaml")


@pytest.mark.unit
@pytest.mark.slow
@pytest.mark.asyncio
class TestTTSEdgeAPI:
    """Edge TTS 테스트 (클라우드 API)"""

    async def test_yaml_to_tts_edge_real_api(self, yaml_file):
        """실제 edge-tts 로 MP3 생성"""
        output_path = str(yaml_file).replace(".yaml", ".mp3")

        # 기존 파일이 있으면 삭제
        if os.path.exists(output_path):
            os.remove(output_path)

        await yaml_to_tts(str(yaml_file), engine=TTSEngine.EDGE, voice="ko-KR-SunHiNeural")

        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 1000


@pytest.mark.unit
@pytest.mark.slow
@pytest.mark.asyncio
class TestTTSQwenLocal:
    """Qwen3-TTS 테스트 (로컬 실행)"""

    async def test_yaml_to_tts_qwen_real_api(self, yaml_file):
        """실제 Qwen3-TTS 로 MP3 생성 (로컬)"""
        output_path = str(yaml_file).replace(".yaml", ".mp3.qwen")

        # 기존 파일이 있으면 삭제
        if os.path.exists(output_path):
            os.remove(output_path)

        # Qwen3-TTS 는 로컬 실행 (macOS Metal 또는 GPU 권장)
        # qwen3-tts-rs CLI 사용 - 소문자 스피커 이름
        await yaml_to_tts(str(yaml_file), engine=TTSEngine.QWEN, voice="sohee", language="korean")

        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 1000
