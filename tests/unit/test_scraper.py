"""

스크래핑 모듈 단위 테스트 (실제 API 사용)
"""

import pytest
from datetime import datetime
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

# 오늘 날짜 (YYYY-MM-DD 형식)
TODAY = datetime.now().strftime("%Y-%m-%d")


@pytest.mark.unit
@pytest.mark.slow
class TestScraperNhanDan:
    """Nhân Dân (정부 기관지) 스크래핑 테스트"""

    def test_scrape_nhandan_real_api(self):
        """실제 Nhân Dân 웹사이트 스크래핑 테스트"""
        articles = scrape_nhandan(TODAY)

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
        articles = scrape_suckhoedoisong(TODAY)

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
        articles = scrape_tuoitre(TODAY)

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
        articles = scrape_vietnamnet(TODAY)

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
        articles = scrape_vnexpress(TODAY)

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
        articles = scrape_thanhnien_rss(TODAY)

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
        articles = scrape_vietnamnet_ttt(TODAY)

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
        articles = scrape_vnexpress_tech(TODAY)

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
        articles = scrape_saigontimes(TODAY)

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


@pytest.mark.unit
@pytest.mark.slow
class TestScraperFullSaveYaml:
    """전체 스크래핑 및 YAML 저장 테스트 (파일명 규칙 준수)"""

    def test_scrape_and_save_with_timestamp(self, test_data_dir):
        """모든 소스 스크래핑 후 YYYYMMDD_HHMM_raw.yaml 형식으로 저장"""
        from today_vn_news.scraper import scrape_and_save
        from datetime import datetime
        from pathlib import Path

        # 파일명 규칙: YYYYMMDD_HHMM_raw.yaml
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        raw_yaml_path = test_data_dir / f"{timestamp}_raw.yaml"

        # 전체 스크래핑 실행
        scraped_data = scrape_and_save(TODAY, str(raw_yaml_path))

        # 검증
        assert scraped_data is not None
        assert isinstance(scraped_data, dict)
        assert raw_yaml_path.exists()

        # 파일명 규칙 검증
        assert raw_yaml_path.name.endswith("_raw.yaml")
        assert len(raw_yaml_path.stem) == 17  # YYYYMMDD_HHMM (15) + _raw (4) - raw = 14?

        # YAML 내용 확인
        yaml_content = Path(raw_yaml_path).read_text(encoding="utf-8")
        assert "metadata:" in yaml_content
        assert "sections:" in yaml_content
        print(f"\n[테스트] YAML 저장 완료: {raw_yaml_path.name}")
        print(f"[테스트] 파일 크기: {len(yaml_content)} bytes")
