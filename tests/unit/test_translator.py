"""
번역 모듈 단위 테스트 (실제 API 사용 + Mock)
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from today_vn_news.translator import translate_weather_condition, translate_and_save, translate_articles
from today_vn_news.exceptions import TranslationError
import os

# 동적 날짜 설정
TODAY = datetime.now().strftime("%Y-%m-%d")
TODAY_KO = datetime.now().strftime("%Y년 %m월 %d일")


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
        # scraper.py에서 반환하는 데이터 구조 (소스명을 키로 하는 딕셔너리)
        scraped_data = {
            "VnExpress": [
                {
                    "title": "Tiêu đề",
                    "content": "Nội dung tiếng Việt",
                    "url": "https://example.com",
                    "date": TODAY,
                }
            ]
        }

        yaml_path = test_data_dir / f"{test_timestamp}.yaml"
        success = translate_and_save(scraped_data, TODAY_KO, str(yaml_path))

        assert success
        assert yaml_path.exists()


@pytest.mark.unit
class TestTranslationMock:
    """번역 모듈 Mock 테스트 (실제 API 호출 없음)"""

    def test_translate_weather_condition_dict_lookup(self):
        """기상 상태 사전 번역 테스트"""
        result = translate_weather_condition("Nhiều mây, không mưa")
        assert "흐림" in result or "구름" in result

    def test_translate_weather_condition_empty(self):
        """빈 문자열 처리 테스트"""
        result = translate_weather_condition("")
        assert result == ""

    @patch('today_vn_news.translator.get_genai_client')
    def test_translate_articles_mock_api(self, mock_get_client):
        """Gemma API Mock을 활용한 번역 테스트"""
        mock_response = MagicMock()
        mock_response.text = """items:
  - title: 테스트 기사 제목
    content: 테스트 기사 내용 요약입니다. 두 번째 줄입니다. 세 번째 줄입니다.
    url: https://example.com"""

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_get_client.return_value = (mock_client, "test-model")

        articles = [{"title": "Test Title", "content": "Test Content", "url": "https://example.com"}]
        result = translate_articles(articles, "Test Source", "2026-02-27")

        assert result is not None
        assert len(result) > 0
        assert result[0]["title"] == "테스트 기사 제목"
        assert result[0]["url"] == "https://example.com"

    @patch('today_vn_news.translator.get_genai_client')
    def test_translate_articles_mock_api_error(self, mock_get_client):
        """API 에러 발생 시 TranslationError 테스트"""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("API Error")
        mock_get_client.return_value = (mock_client, "test-model")

        articles = [{"title": "Test Title", "content": "Test Content", "url": "https://example.com"}]

        with pytest.raises(TranslationError):
            translate_articles(articles, "Test Source", "2026-02-27")

    @patch('today_vn_news.translator.get_genai_client')
    def test_translate_articles_mock_invalid_yaml(self, mock_get_client):
        """잘못된 YAML 응답 파싱 테스트"""
        mock_response = MagicMock()
        mock_response.text = "invalid yaml content"

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_get_client.return_value = (mock_client, "test-model")

        articles = [{"title": "Test Title", "content": "Test Content", "url": "https://example.com"}]

        with pytest.raises(TranslationError):
            translate_articles(articles, "Test Source", "2026-02-27")

    @patch('today_vn_news.translator.genai.Client')
    def test_call_gemma_api_with_model_name(self, mock_client_class):
        """_call_gemma_api가 model_name 인자를 올바르게 전달"""
        mock_response = MagicMock()
        mock_response.text = "test response"

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        from today_vn_news.translator import _call_gemma_api
        result = _call_gemma_api(mock_client, "custom-model", "test prompt")

        mock_client.models.generate_content.assert_called_once_with(
            model="custom-model",
            contents="test prompt"
        )
        assert result == mock_response


@pytest.mark.unit
class TestGetGenaiClient:
    """get_genai_client 헬퍼 함수 테스트"""

    @patch.dict(os.environ, {"APERTURE_BASE_URL": "https://ai.test.ts.net", "APERTURE_MODEL": "test-model"})
    @patch('today_vn_news.translator.genai.Client')
    def test_get_genai_client_aperture(self, mock_client_class):
        """Aperture 설정 시 올바른 클라이언트와 모델 반환"""
        from today_vn_news.translator import get_genai_client

        client, model = get_genai_client()

        mock_client_class.assert_called_once_with(
            api_key="ts",
            http_options={"base_url": "https://ai.test.ts.net"}
        )
        assert model == "test-model"

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key", "GEMINI_MODEL": "gemini-model"}, clear=True)
    @patch('today_vn_news.translator.genai.Client')
    def test_get_genai_client_fallback(self, mock_client_class):
        """APERTURE_BASE_URL 없으면 Google AI Studio fallback"""
        from today_vn_news.translator import get_genai_client

        # APERTURE_BASE_URL 제거 보장
        os.environ.pop("APERTURE_BASE_URL", None)

        client, model = get_genai_client()

        mock_client_class.assert_called_once_with(api_key="test-key")
        assert model == "gemini-model"

    @patch.dict(os.environ, {}, clear=True)
    def test_get_genai_client_no_key_raises(self):
        """API 키 없으면 TranslationError 발생"""
        from today_vn_news.translator import get_genai_client

        with pytest.raises(TranslationError):
            get_genai_client()
