"""
스크래핑 모듈 단위 테스트 (실제 API 사용)
"""

import pytest
from today_vn_news.scraper import (
    scrape_nhandan,
    scrape_vnexpress,
    scrape_weather_hochiminh,
    scrape_air_quality,
)


@pytest.mark.unit
@pytest.mark.slow
class TestScraperNCHMF:
    """NCHMF 기상 스크래핑 테스트 (실제 API)"""

    def test_scrape_nchmf_real_api(self):
        """실제 NCHMF API 호출 테스트"""
        result = scrape_weather_hochiminh()

        assert result is not None
        assert "temp" in result or result is None
        assert "condition" in result or result is None
        assert "humidity" in result or result is None


@pytest.mark.unit
@pytest.mark.slow
class TestScraperIQAir:
    """IQAir 공기질 스크래핑 테스트 (실제 API)"""

    def test_scrape_iqair_real_api(self):
        """실제 IQAir API 호출 테스트"""
        result = scrape_air_quality()

        assert result is not None
        assert "aqi" in result or result is None
        assert "status" in result or result is None


@pytest.mark.unit
@pytest.mark.slow
class TestScraperVnExpress:
    """VnExpress 스크래핑 테스트 (실제 API)"""

    def test_scrape_vnexpress_real_api(self):
        """실제 VnExpress 웹사이트 스크래핑 테스트"""
        articles = scrape_vnexpress("2026-02-10", 2)

        assert isinstance(articles, list)
        for article in articles:
            assert "title" in article
            assert "content" in article
            assert "url" in article
