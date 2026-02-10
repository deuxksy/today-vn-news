"""
번역 모듈 단위 테스트 (실제 API 사용)
"""

import pytest
from today_vn_news.translator import translate_weather_condition, translate_and_save


@pytest.mark.unit
class TestWeatherTranslation:
    """기상 번역 테스트"""

    @pytest.mark.parametrize(
        "vn_input,expected",
        [
            ("Mây thay đổi, trời nắng", "구름 낌, 맑음"),
            ("Trời mưa", "비"),
            ("Nhiều mây", "흐림"),
        ],
    )
    def test_translate_weather_condition(self, vn_input, expected):
        result = translate_weather_condition(vn_input)
        assert result == expected


@pytest.mark.unit
@pytest.mark.slow
class TestTranslationRealAPI:
    """번역 테스트 (실제 Gemma API)"""

    def test_translate_weather_with_gemma(self):
        """실제 Gemma API로 날씨 번역 테스트"""
        condition = "Mưa rào, sấm chớp"
        result = translate_weather_condition(condition)

        assert result is not None
        assert len(result) > 0

    def test_translate_and_save_real_api(self, test_data_dir, test_timestamp):
        """실제 Gemma API로 뉴스 번역 테스트"""
        scraped_data = {
            "sections": [
                {
                    "items": [
                        {
                            "title": "Tiêu đề",
                            "content": "Nội dung tiếng Việt",
                            "url": "https://example.com",
                        }
                    ]
                }
            ]
        }

        yaml_path = test_data_dir / f"{test_timestamp}.yaml"
        success = translate_and_save(scraped_data, "2026년 2월 10일", str(yaml_path))

        assert success
        assert yaml_path.exists()
