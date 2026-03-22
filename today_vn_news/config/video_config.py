from dataclasses import dataclass
from pathlib import Path
import yaml
from today_vn_news.logger import logger
from today_vn_news.exceptions import TodayVnNewsError


@dataclass
class VideoConfig:
    """영상 소스 설정"""

    # Media 설정
    media_mount_path: str = "/Volumes/Media"
    media_date_format: str = "YYMMDD"
    auto_copy_latest: bool = True

    # 저장 설정
    archive_format: str = "{YYMM}/{DD}_{hhmm}.mp4"

    # Fallback
    local_data_dir: str = "data"
    default_image: str = "assets/default_bg.png"

    @classmethod
    def from_yaml(cls, path: str = "config.yaml") -> "VideoConfig":
        """
        YAML 설정 로딩

        Args:
            path: 설정 파일 경로

        Returns:
            VideoConfig: 로드된 설정 (파일 없으면 기본값)

        Raises:
            TodayVnNewsError: YAML 파싱 실패 (파일 있지만 잘못됨)

        Note:
            파일 없으면 경고 로그 후 기본값 반환 (조용히 진행)
        """
        config_path = Path(path)

        if not config_path.exists():
            logger.warning(f"설정 파일 없음 ({path}), 기본값 사용")
            return cls()

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            video_config = data.get("video", {})
            return cls(
                media_mount_path=video_config.get("media", {}).get("mount_path", "/Volumes/Media"),
                media_date_format=video_config.get("media", {}).get("date_format", "YYMMDD"),
                auto_copy_latest=video_config.get("media", {}).get("auto_copy_latest", True),
                archive_format=video_config.get("archive", {}).get("format", "{YYMM}/{DD}_{hhmm}.mp4"),
                local_data_dir=video_config.get("fallback", {}).get("local_data_dir", "data"),
                default_image=video_config.get("fallback", {}).get("default_image", "assets/default_bg.png")
            )
        except yaml.YAMLError as e:
            logger.error(f"YAML 파싱 실패: {e}")
            raise TodayVnNewsError(f"설정 파일 파싱 실패: {e}")
