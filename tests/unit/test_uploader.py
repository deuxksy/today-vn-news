"""
유튜브 업로더 단위 테스트 (실제 API 사용)
"""

import pytest
import os
from today_vn_news.uploader import upload_video


@pytest.mark.unit
@pytest.mark.slow
@pytest.mark.upload
class TestUploaderRealAPI:
    """업로더 테스트 (실제 YouTube API)"""

    def test_upload_video_real_api(self, test_data_dir, test_timestamp):
        """실제 YouTube에 업로드"""
        # 영상 파일 생성 (테스트용)
        video_file = test_data_dir / f"{test_timestamp}_final.mp4"
        video_file.write_bytes(b"TEST_VIDEO_HEADER")

        result = upload_video(test_timestamp, str(test_data_dir))

        assert result
        # 실제로 유튜브에 업로드됨!

    def test_upload_video_missing_file(self, test_data_dir):
        result = upload_video("nonexistent", str(test_data_dir))
        assert result == False
