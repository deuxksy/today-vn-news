"""

스크래핑 모듈 단위 테스트 (실제 API 사용)
"""

import pytest
from today_vn_news.scraper import (
    scrape_nhandan,
    scrape_suckhoedoisong,
    scrape_tuoitre,
    scrape_vietnamnet,
    scrape_vnexpress,
    scrape_weather_hochiminh,
    scrape_air_quality,
    scrape_thanhnien_rss,
    scrape_thanhnien,
    scrape_vietnamnet_ttt,
    scrape_vnexpress_tech,
    scrape_saigontimes,
    scrape_earthquake,
)


@pytest.mark.unit
@pytest.mark.slow
class TestScraperNhanDan:
    """Nhân Dân (정부 기관지) 스크래핑 테스트"""

    def test_scrape_nhandan_real_api(self):
        """실제 Nhân Dân 웹사이트 스크래핑 테스트"""
        articles = scrape_nhandan("2026-02-10")

        assert isinstance(articles, list)
        for article in articles:
            assert "title" in article
            assert "content" in article
            assert "url" in article


@pytest.mark.unit
@pytest.mark.slow
class TestScraperSucKhoeDoiSong:
    """Sức khỏe & Đời sống (보건부) 스크래핑 테스트"""

    def test_scrape_suckhoedoisong_real_api(self):
        """실제 Sức khỏe & Đời sống 웹사이트 스크래핑 테스트"""
        articles = scrape_suckhoedoisong("2026-02-10")

        assert isinstance(articles, list)
        for article in articles:
            assert "title" in article
            assert "content" in article
            assert "url" in article


@pytest.mark.unit
@pytest.mark.slow
class TestScraperTuoiTre:
    """Tuổi Trẻ (시정 소식) 스크래핑 테스트"""

    def test_scrape_tuoitre_real_api(self):
        """실제 Tuổi Trẻ 웹사이트 스크래핑 테스트"""
        articles = scrape_tuoitre("2026-02-10")

        assert isinstance(articles, list)
        for article in articles:
            assert "title" in article
            assert "content" in article
            assert "url" in article


@pytest.mark.unit
@pytest.mark.slow
class TestScraperVietnamNet:
    """VietnamNet (종합 뉴스) 스크래핑 테스트"""

    def test_scrape_vietnamnet_real_api(self):
        """실제 VietnamNet 웹사이트 스크래핑 테스트"""
        articles = scrape_vietnamnet("2026-02-10")

        assert isinstance(articles, list)
        for article in articles:
            assert "title" in article
            assert "content" in article
            assert "url" in article


@pytest.mark.unit
@pytest.mark.slow
class TestScraperVnExpress:
    """VnExpress (종합 뉴스) 스크래핑 테스트"""

    def test_scrape_vnexpress_real_api(self):
        """실제 VnExpress 웹사이트 스크래핑 테스트"""
        articles = scrape_vnexpress("2026-02-10")

        assert isinstance(articles, list)
        for article in articles:
            assert "title" in article
            assert "content" in article
            assert "url" in article


@pytest.mark.unit
@pytest.mark.slow
class TestScraperThanhNien:
    """Thanh Niên (사회/청년) 스크래핑 테스트"""

    def test_scrape_thanhnien_real_api(self):
        """실제 Thanh Niên RSS 스크래핑 테스트"""
        articles = scrape_thanhnien_rss("2026-02-10")

        assert isinstance(articles, list)
        for article in articles:
            assert "title" in article
            assert "content" in article
            assert "url" in article


@pytest.mark.unit
@pytest.mark.slow
class TestScraperVietnamNetTTT:
    """VietnamNet 정보통신 스크래핑 테스트"""

    def test_scrape_vietnamnet_ttt_real_api(self):
        """실제 VietnamNet 정보통신 웹사이트 스크래핑 테스트"""
        articles = scrape_vietnamnet_ttt("2026-02-10")

        assert isinstance(articles, list)
        for article in articles:
            assert "title" in article
            assert "content" in article
            assert "url" in article


@pytest.mark.unit
@pytest.mark.slow
class TestScraperVnExpressTech:
    """VnExpress IT/과학 스크래핑 테스트"""

    def test_scrape_vnexpress_tech_real_api(self):
        """실제 VnExpress IT/과학 웹사이트 스크래핑 테스트"""
        articles = scrape_vnexpress_tech("2026-02-10")

        assert isinstance(articles, list)
        for article in articles:
            assert "title" in article
            assert "content" in article
            assert "url" in article


@pytest.mark.unit
@pytest.mark.slow
class TestScraperSaigonTimes:
    """The Saigon Times (경제) 스크래핑 테스트"""

    def test_scrape_saigontimes_real_api(self):
        """실제 The Saigon Times 웹사이트 스크래핑 테스트"""
        articles = scrape_saigontimes("2026-02-10")

        assert isinstance(articles, list)
        for article in articles:
            assert "title" in article
            assert "content" in article
            assert "url" in article


@pytest.mark.unit
@pytest.mark.slow
class TestScraperNCHMF:
    """NCHMF 기상 스크래핑 테스트 (실제 API)"""

    def test_scrape_weather_hochiminh_real_api(self):
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

    def test_scrape_air_quality_real_api(self):
        """실제 IQAir API 호출 테스트"""
        result = scrape_air_quality()

        assert result is not None
        assert "aqi" in result or result is None
        assert "status" in result or result is None


@pytest.mark.unit
@pytest.mark.slow
class TestScraperEarthquake:
    """IGP-VAST 지진 스크래핑 테스트 (실제 API)"""

    def test_scrape_earthquake_real_api(self):
        """실제 IGP-VAST 지진 API 호출 테스트"""
        earthquakes = scrape_earthquake()

        assert isinstance(earthquakes, list)
        for earthquake in earthquakes:
            assert "title" in earthquake
            assert "content" in earthquake
            assert "url" in earthquake
