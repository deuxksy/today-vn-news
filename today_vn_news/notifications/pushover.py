# today_vn_news/notifications/pushover.py
import os
from typing import Optional
import requests

from today_vn_news.logger import logger
from today_vn_news.notifications.pipeline_status import PipelineStatus
from today_vn_news.notifications import STEP_SCRAPE

# Emergency priority 기본값
DEFAULT_RETRY = 300      # 5분마다 재시도
DEFAULT_EXPIRE = 3600    # 1시간 후 만료

# 메시지 길이 제한 (Pushover API 스펙)
MAX_MESSAGE_LENGTH = 1024
MAX_TITLE_LENGTH = 250
MAX_URL_LENGTH = 512

# YouTube 재생목록 URL (업로드 URL fallback)
PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLzMxB6D1eypIA_JNasD_MNISMEUtMbHvK"


class PushoverNotifier:
    """Pushover 알림 전송"""

    API_URL = "https://api.pushover.net/1/messages.json"

    def __init__(self, token: str, user: str):
        self.token = token
        self.user = user

    @classmethod
    def from_env(cls) -> "PushoverNotifier":
        """환경 변수에서 로드 (필수)

        Raises:
            ValueError: PUSHOVER_TOKEN 또는 PUSHOVER_USER가 없을 때
        """
        token = os.getenv("PUSHOVER_TOKEN")
        user = os.getenv("PUSHOVER_USER")
        if not token or not user:
            raise ValueError("PUSHOVER_TOKEN and PUSHOVER_USER required")
        return cls(token, user)

    @classmethod
    def from_env_or_none(cls) -> Optional["PushoverNotifier"]:
        """환경 변수에서 로드 (선택적)

        Returns:
            PushoverNotifier: 환경 변수가 있으면 인스턴스 반환
            None: 환경 변수가 없으면 None 반환 (알림 skip)
        """
        token = os.getenv("PUSHOVER_TOKEN")
        user = os.getenv("PUSHOVER_USER")
        if not token or not user:
            logger.info("Pushover 환경 변수 없음 - 알림 skip")
            return None
        return cls(token, user)

    def send_notification(self, status: PipelineStatus) -> bool:
        """알림 전송 (실패해도 예외 없이 False 반환)"""
        try:
            title, message, priority, url = self._format_message(status)
            return self._send(title, message, priority, url)
        except Exception as e:
            logger.error(f"Pushover 알림 실패: {e}")
            return False

    def _send(self, title: str, message: str, priority: int, url: Optional[str]) -> bool:
        """Pushover API 호출"""
        # 메시지 길이 검증 및 자르기
        title = title[:MAX_TITLE_LENGTH]
        message = message[:MAX_MESSAGE_LENGTH]
        if url:
            url = url[:MAX_URL_LENGTH]

        data = {
            "token": self.token,
            "user": self.user,
            "title": title,
            "message": message,
            "priority": priority,
        }

        # URL 추가 (성공 시에만)
        if url:
            data["url"] = url

        # Emergency priority 필수 파라미터
        if priority == 2:
            data["retry"] = DEFAULT_RETRY
            data["expire"] = DEFAULT_EXPIRE

        response = requests.post(self.API_URL, data=data, timeout=10)

        if response.status_code == 429:
            logger.warning("Pushover Rate Limit 초과 (HTTP 429)")
            return False

        if response.status_code != 200:
            logger.error(f"Pushover API 실패: HTTP {response.status_code}")
            return False

        result = response.json()
        if result.get("status") != 1:
            logger.error(f"Pushover API 에러: {result.get('errors', [])}")
            return False

        logger.info("Pushover 알림 전송 성공")
        return True

    def _format_message(self, status: PipelineStatus) -> tuple[str, str, int, str | None]:
        """메시지 포맷팅 및 우선순위 결정"""
        if status.success:
            title = "✅ 뉴스 영상 완료"
            message = f"완료 단계: {', '.join(status.completed_steps)}"
            priority = 0
            url = status.youtube_url or PLAYLIST_URL

        elif status.completed_steps:
            failed = status.failed_step
            title = "⚠️ 파이프라인 부분 실패"
            message = f"성공: {', '.join(status.completed_steps)}\n"
            message += f"실패: {failed} - {status.errors.get(failed, 'Unknown')}"
            priority = 1
            url = None

        else:
            title = "❌ 파이프라인 실패"
            first_error = status.errors.get(STEP_SCRAPE, "알 수 없는 오류")
            message = f"사유: {first_error}"
            priority = 2
            url = None

        return title, message, priority, url
