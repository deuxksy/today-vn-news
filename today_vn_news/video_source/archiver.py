"""MediaArchiver: 최종 영상을 Media로 복사/저장"""

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
        로컬 _final.mp4를 Media/{{YYMM}}/{{DD}}_{{hhmm}}.mp4로 이동

        Args:
            local_final: 로컬 _final.mp4 경로
            base_name: YYMMDD (예: 260319)

        Returns:
            media_path: Media 저장소 경로

        Raises:
            MediaArchiveError: 이동 실패 시
        """
        # base_name 포맷: YYMMDD (6자리)
        # 현재 시간에서 hhmm 추출
        from datetime import datetime
        hhmm = datetime.now().strftime("%H%M")

        if len(base_name) != 6:
            raise ValueError(f"잘못된 base_name 포맷: {base_name} (YYMMDD 6자리 필요)")

        yymm = base_name[:4]  # YYMM
        dd = base_name[4:6]    # DD

        # 대상 경로: Media/{{YYMM}}/{{DD}}_{{hhmm}}.mp4
        media_base = Path(self.config.media_mount_path)
        archive_dir = media_base / yymm
        archive_name = f"{dd}_{hhmm}.mp4"
        media_path = archive_dir / archive_name

        try:
            # 폴더 생성
            archive_dir.mkdir(parents=True, exist_ok=True)

            # 이동 (shutil.move로 원본 삭제)
            shutil.move(local_final, media_path)
            logger.info(f"Media 이동 완료: {media_path}")
            return media_path

        except FileNotFoundError:
            raise MediaArchiveError(f"Media 경로 없음 또는 접근 불가: {media_base}")
        except OSError as e:
            raise MediaArchiveError(f"Media 이동 실패: {e}")

    def archive_audio(self, local_audio: str, base_name: str) -> Path:
        """
        로컬 MP3를 Media/{{YYMM}}/{{DD}}_{{hhmm}}.mp3로 이동

        Args:
            local_audio: 로컬 MP3 경로
            base_name: YYMMDD (예: 260319)

        Returns:
            media_path: Media 저장소 경로

        Raises:
            MediaArchiveError: 이동 실패 시
        """
        # base_name 포맷: YYMMDD (6자리)
        # 현재 시간에서 hhmm 추출
        from datetime import datetime
        hhmm = datetime.now().strftime("%H%M")

        if len(base_name) != 6:
            raise ValueError(f"잘못된 base_name 포맷: {base_name} (YYMMDD 6자리 필요)")

        yymm = base_name[:4]  # YYMM
        dd = base_name[4:6]    # DD

        # 대상 경로: Media/{{YYMM}}/{{DD}}_{{hhmm}}.mp3
        media_base = Path(self.config.media_mount_path)
        archive_dir = media_base / yymm
        archive_name = f"{dd}_{hhmm}.mp3"
        media_path = archive_dir / archive_name

        try:
            # 폴더 생성
            archive_dir.mkdir(parents=True, exist_ok=True)

            # 파일 존재 확인
            if not Path(local_audio).exists():
                raise MediaArchiveError(f"MP3 파일 존재하지 않음: {local_audio}")

            # 이동 (shutil.move로 원본 삭제)
            shutil.move(local_audio, media_path)
            logger.info(f"Media MP3 이동 완료: {media_path}")
            return media_path

        except FileNotFoundError:
            raise MediaArchiveError(f"Media 경로 없음 또는 접근 불가: {media_base}")
        except OSError as e:
            raise MediaArchiveError(f"Media MP3 이동 실패: {e}")

    def resolve_existing(self, yymmdd: str) -> str | None:
        """YYMMDD에 해당하는 Media 경로 확인

        Args:
            yymmdd: YYMMDD 타임스탬프 (6자리)

        Returns:
            Media 파일 경로 또는 None
        """
        yymm = yymmdd[:4]  # YYMM
        dd = yymmdd[4:6]   # DD

        media_dir = Path(self.config.media_mount_path) / yymm

        if media_dir.exists():
            # 해당 일(DD)로 시작하는 MP4 파일 찾기
            pattern = f"{dd}_*.mp4"
            mp4_files = list(media_dir.glob(pattern))
            if mp4_files:
                # 시간순 정렬 후 가장 최신 파일 반환
                return str(sorted(mp4_files)[-1])
        return None
