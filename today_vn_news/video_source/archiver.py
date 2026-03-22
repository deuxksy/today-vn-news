"""MediaArchiver: 최종 영상을 Media로 복사/저장"""

import os
import shutil
from pathlib import Path
from today_vn_news.logger import logger
from today_vn_news.config import VideoConfig
from today_vn_news.exceptions import MediaArchiveError


class MediaArchiver:
    """최종 영상을 Media로 복사/저장"""

    def __init__(self, config: VideoConfig):
        self.config = config

    def archive(self, local_final: str, base_name: str) -> Path:
        """
        로컬 _final.mp4를 Media/{{YYMM}}/{{DD}}_{{hhmm}}.mp4로 복사

        Args:
            local_final: 로컬 _final.mp4 경로
            base_name: YYMMDD_HHMM (예: 260322_1230)

        Returns:
            media_path: Media 저장소 경로

        Raises:
            MediaArchiveError: 복사 실패 시
        """
        # base_name 파싱: YYMMDD_HHMM → YYMMDD, DD, HHMM
        yymmdd = base_name[:6]  # YYMMDD
        dd = base_name[4:6]    # DD (YYMMDD에서 인덱스 4-5)
        hhmm = base_name[7:11]  # HHMM (_ 제외, 인덱스 7-10)
        yymm = yymmdd[:4]      # YYMM

        # 대상 경로: Media/{{YYMM}}/{{DD}}_{{hhmm}}.mp4
        media_base = Path(self.config.media_mount_path)
        archive_dir = media_base / yymm
        archive_name = f"{dd}_{hhmm}.mp4"
        media_path = archive_dir / archive_name

        try:
            # 폴더 생성
            archive_dir.mkdir(parents=True, exist_ok=True)

            # 복사 (shutil.copy2로 원본 보존)
            shutil.copy2(local_final, media_path)
            logger.info(f"Media 저장 완료: {media_path}")
            return media_path

        except FileNotFoundError:
            raise MediaArchiveError(f"Media 경로 없음 또는 접근 불가: {media_base}")
        except OSError as e:
            raise MediaArchiveError(f"Media 복사 실패: {e}")
