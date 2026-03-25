"""영상 소스 우선순위 체인 관리"""

import os
import shutil
import time
from pathlib import Path

from today_vn_news.config import VideoConfig
from today_vn_news.exceptions import MediaMountError, MediaCopyError, VideoSourceError
from today_vn_news.logger import logger


class VideoSourceResolver:
    """영상 소스 우선순위 체인 관리

    우선순위:
    1. Media/{{YYMMDD}}.mp4
    2. Media/latest.mp4
    3. Local data/{{base_name}}.mov
    4. Local data/{{base_name}}.mp4
    5. Default Image
    """

    def __init__(self, config: VideoConfig):
        """초기화

        Args:
            config: 비디오 설정
        """
        self.config = config
        self.temp_copies: list[Path] = []  # 정리할 임시 파일 추적

    def resolve(self, base_name: str) -> tuple[Path, bool]:
        """우선순위에 따라 영상 소스 반환

        Args:
            base_name: YYMMDD (예: 260325) 또는 YYMMDD_HHMM (예: 260322_1230)

        Returns:
            (source_path, is_temporary_copy)
            - source_path: 사용할 영상 경로 (로컬 data/ 기준)
            - is_temporary_copy: Media에서 복사한 임시 파일인지 여부

        Raises:
            VideoSourceError: 모든 소스 실패 시
        """
        # base_name에서 YYMMDD 추출 (Media/{{YYMMDD}}.mp4용)
        # 새로운 형식: YYMMDD (6자리), 기존 형식: YYMMDD_HHMM (10자리)
        if len(base_name) == 6:
            yymmdd = base_name  # YYMMDD (6자리)
        else:
            yymmdd = base_name[:6]  # YYMMDDHHMM에서 앞 6자 (기존 호환)

        # 1. Media/{{YYMMDD}}.mp4 확인
        media_source = Path(self.config.media_mount_path) / f"{yymmdd}.mp4"
        if media_source.exists():
            logger.info(f"Media 소스 발견: {media_source}")
            return self._copy_to_local(media_source), True

        # 2. Media/latest.mp4 확인
        media_latest = Path(self.config.media_mount_path) / "latest.mp4"
        if media_latest.exists():
            logger.info(f"Media latest 소스 사용: {media_latest}")
            return self._copy_to_local(media_latest), True

        # 3. Local data/{{base_name}}.mov 확인
        data_dir = Path(self.config.local_data_dir)
        local_mov = data_dir / f"{base_name}.mov"
        if local_mov.exists():
            logger.info(f"로컬 MOV 소스 사용: {local_mov}")
            return local_mov, False

        # 4. Local data/{{base_name}}.mp4 확인
        local_mp4 = data_dir / f"{base_name}.mp4"
        if local_mp4.exists():
            logger.info(f"로컬 MP4 소스 사용: {local_mp4}")
            return local_mp4, False

        # 5. 기본 이미지
        default_image = Path(self.config.default_image)
        if default_image.exists():
            logger.info(f"기본 이미지 사용: {default_image}")
            return default_image, False

        # 모두 실패
        raise VideoSourceError(f"영상 소스를 찾을 수 없음 (base_name: {base_name})")

    def _copy_to_local(self, source: Path) -> Path:
        """Media에서 로컬 data/로 임시 복사

        Args:
            source: Media 소스 경로

        Returns:
            로컬 복사본 경로

        Raises:
            MediaMountError: Media 마운트 안됨
            MediaCopyError: 복사 실패
        """
        data_dir = Path(self.config.local_data_dir)
        data_dir.mkdir(parents=True, exist_ok=True)

        # 임시 파일명: timestamp_원본파일명
        timestamp = int(time.time())
        temp_name = f"temp_{timestamp}_{source.name}"
        temp_path = data_dir / temp_name

        try:
            shutil.copy2(source, temp_path)
            logger.debug(f"Media → 로컬 복사 완료: {source} → {temp_path}")
            self.temp_copies.append(temp_path)
            return temp_path
        except FileNotFoundError:
            raise MediaMountError(f"Media 소스 없음 또는 접근 불가: {source}")
        except OSError as e:
            raise MediaCopyError(f"Media 복사 실패: {e}")

    def cleanup_temporary(self) -> None:
        """임시 복사본 정리"""
        for temp_path in self.temp_copies:
            try:
                if temp_path.exists():
                    os.remove(temp_path)
                    logger.debug(f"임시 파일 삭제: {temp_path}")
            except OSError as e:
                logger.warning(f"임시 파일 삭제 실패 (무시): {temp_path} - {e}")

        self.temp_copies.clear()
