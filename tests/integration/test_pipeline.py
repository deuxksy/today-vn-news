"""
전체 파이프라인 통합 테스트 (실제 API 사용)
"""

import pytest
from today_vn_news.scraper import scrape_and_save
from today_vn_news.translator import translate_and_save
from today_vn_news.engine import synthesize_video
from today_vn_news.uploader import upload_video


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
class TestFullPipelineRealAPI:
    """전체 파이프라인 통합 테스트 (모든 실제 API)"""

    async def test_complete_pipeline_without_upload(
        self, test_timestamp, test_data_dir
    ):
        """전체 파이프라인 테스트 (업로드 제외)"""
        from today_vn_news.tts import yaml_to_tts

        # 1단계: 스크래핑 (실제 웹사이트)
        raw_yaml_path = test_data_dir / f"{test_timestamp}_raw.yaml"
        scraped_data = scrape_and_save("2026-02-10", str(raw_yaml_path))
        assert scraped_data is not None
        assert raw_yaml_path.exists()

        # 2단계: 번역 (실제 Gemma API)
        yaml_path = test_data_dir / f"{test_timestamp}.yaml"
        success = translate_and_save(
            scraped_data, "2026년 2월 10일 16:00", str(yaml_path)
        )
        assert success
        assert yaml_path.exists()

        # 3단계: TTS (실제 edge-tts)
        await yaml_to_tts(str(yaml_path))
        mp3_path = test_data_dir / f"{test_timestamp}.mp3"
        assert mp3_path.exists()

        # 4단계: 영상 합성 (실제 FFmpeg)
        result = synthesize_video(test_timestamp, str(test_data_dir))
        assert result
        video_path = test_data_dir / f"{test_timestamp}_final.mp4"
        assert video_path.exists()


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.upload
@pytest.mark.asyncio
class TestFullPipelineWithUpload:
    """전체 파이프라인 + 업로드 테스트 (실제 유튜브 업로드)"""

    async def test_complete_pipeline_with_upload(self, test_timestamp, test_data_dir):
        """전체 파이프라인 + 유튜브 업로드"""

        # 1-4단계 실행
        await self._run_pipeline_without_upload(test_timestamp, test_data_dir)

        # 5단계: 유튜브 업로드 (실제 업로드)
        result = upload_video(test_timestamp, str(test_data_dir))
        assert result

    async def _run_pipeline_without_upload(self, test_timestamp, test_data_dir):
        """파이프라인 1-4단계 실행 (내부 메서드)"""
        # 1단계: 스크래핑 (실제 웹사이트)
        raw_yaml_path = test_data_dir / f"{test_timestamp}_raw.yaml"
        scraped_data = scrape_and_save("2026-02-10", str(raw_yaml_path))
        assert scraped_data is not None
        assert raw_yaml_path.exists()

        # 2단계: 번역 (실제 Gemma API)
        yaml_path = test_data_dir / f"{test_timestamp}.yaml"
        success = translate_and_save(
            scraped_data, "2026년 2월 10일 16:00", str(yaml_path)
        )
        assert success
        assert yaml_path.exists()

        # 3단계: TTS (실제 edge-tts)
        from today_vn_news.tts import yaml_to_tts

        await yaml_to_tts(str(yaml_path))
        mp3_path = test_data_dir / f"{test_timestamp}.mp3"
        assert mp3_path.exists()

        # 4단계: 영상 합성 (실제 FFmpeg)
        result = synthesize_video(test_timestamp, str(test_data_dir))
        assert result
        video_path = test_data_dir / f"{test_timestamp}_final.mp4"
        assert video_path.exists()
