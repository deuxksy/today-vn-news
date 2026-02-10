"""
영상 합성 엔진 단위 테스트 (실제 API 사용)
"""

import pytest
import asyncio
from today_vn_news.engine import get_hw_encoder_config, synthesize_video


@pytest.mark.unit
class TestEncoderConfig:
    """하드웨어 인코더 설정 테스트 (시스템 확인)"""

    @pytest.mark.parametrize(
        "platform,expected_encoder",
        [
            ("darwin", "h264_videotoolbox"),
            ("linux", "libx264"),
        ],
    )
    def test_get_hw_encoder_config(self, monkeypatch, platform, expected_encoder):
        """실제 시스템 환경 확인"""
        monkeypatch.setattr("sys.platform", platform)
        if platform == "linux":
            monkeypatch.setattr("os.path.exists", lambda x: False)

        result = get_hw_encoder_config()
        encoder_name, _, _ = result

        assert encoder_name == expected_encoder


@pytest.mark.unit
@pytest.mark.slow
@pytest.mark.asyncio
class TestVideoSynthesisRealFFmpeg:
    """영상 합성 테스트 (실제 FFmpeg 실행)"""

    async def test_synthesize_video_real_ffmpeg(self, yaml_file):
        """실제 FFmpeg로 영상 합성"""
        from today_vn_news.tts import yaml_to_tts

        # 먼저 TTS 실행
        await yaml_to_tts(str(yaml_file))

        test_timestamp = yaml_file.stem
        result = synthesize_video(test_timestamp, str(yaml_file.parent))

        assert result
        final_video = yaml_file.parent / f"{test_timestamp}_final.mp4"
        assert final_video.exists()
        assert final_video.stat().st_size > 10000
