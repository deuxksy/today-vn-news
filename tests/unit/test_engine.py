"""
영상 합성 엔진 단위 테스트 (실제 API 사용)
"""

import pytest
import asyncio
import os
import tempfile
from pathlib import Path
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


@pytest.mark.unit
class TestVideoSourcePath:
    """source_path 파라미터 테스트"""

    def test_synthesize_video_with_source_path(self, tmp_path, sample_audio):
        """source_path 파라미터로 소스 영상 지정"""
        # 테스트용 소스 영상 생성 (1초짜리 검은색 영상)
        source_video = tmp_path / "test_source.mp4"

        # FFmpeg로 테스트 영상 생성
        import subprocess
        subprocess.run([
            "ffmpeg", "-f", "lavfi", "-i", "color=c=black:s=1280x720:d=1",
            "-pix_fmt", "yuv420p", "-y", str(source_video)
        ], capture_output=True, check=True)

        # 오디오 파일 복사
        audio_path = tmp_path / "260322_1230.mp3"
        import shutil
        shutil.copy(sample_audio, audio_path)

        # source_path 파라미터로 합성 실행
        result = synthesize_video("260322_1230", str(tmp_path), source_path=str(source_video))

        assert result is True
        final_video = tmp_path / "260322_1230_final.mp4"
        assert final_video.exists()

    def test_synthesize_video_without_source_path(self, tmp_path, sample_audio):
        """source_path None이면 기존 로직대로 .mov/.mp4 확인"""
        # 기존 방식대로 .mp4 파일 직접 생성
        video_mp4 = tmp_path / "260322_1230.mp4"

        # FFmpeg로 테스트 영상 생성
        import subprocess
        subprocess.run([
            "ffmpeg", "-f", "lavfi", "-i", "color=c=black:s=1280x720:d=1",
            "-pix_fmt", "yuv420p", "-y", str(video_mp4)
        ], capture_output=True, check=True)

        # 오디오 파일 복사
        audio_path = tmp_path / "260322_1230.mp3"
        import shutil
        shutil.copy(sample_audio, audio_path)

        # source_path=None으로 실행 (기존 로직)
        result = synthesize_video("260322_1230", str(tmp_path), source_path=None)

        assert result is True
        final_video = tmp_path / "260322_1230_final.mp4"
        assert final_video.exists()
