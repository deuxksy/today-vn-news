"""
TTS 모듈 단위 테스트 (실제 API 사용)
"""

import pytest
import os
from today_vn_news.tts import parse_yaml_to_text, yaml_to_tts


@pytest.mark.unit
class TestYamlParsing:
    """YAML 파싱 테스트 (메모리 연산)"""

    def test_parse_yaml_to_text(self, yaml_file):
        text = parse_yaml_to_text(str(yaml_file))

        assert "오늘의 베트남 주요 뉴스" in text
        assert "안전 및 기상 관제" in text
        assert "29°C" in text

    def test_parse_yaml_empty_file(self, test_data_dir, test_timestamp):
        empty_yaml = test_data_dir / f"{test_timestamp}_empty.yaml"
        empty_yaml.write_text("metadata: {}\nsections: []")

        text = parse_yaml_to_text(str(empty_yaml))
        assert len(text) > 0

    def test_parse_yaml_missing_file(self):
        text = parse_yaml_to_text("nonexistent.yaml")
        assert text == ""


@pytest.mark.unit
@pytest.mark.slow
@pytest.mark.asyncio
class TestTTSRealAPI:
    """TTS 생성 테스트 (실제 edge-tts API)"""

    async def test_yaml_to_tts_real_api(self, yaml_file):
        """실제 edge-tts로 MP3 생성"""
        output_path = str(yaml_file).replace(".yaml", ".mp3")

        # 기존 파일이 있으면 삭제
        if os.path.exists(output_path):
            os.remove(output_path)

        await yaml_to_tts(str(yaml_file))

        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 1000
