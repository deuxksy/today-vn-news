#!/usr/bin/env python3
"""실제 Pushover API 호출 테스트 스크립트

사용법:
  1. .env 파일에 PUSHOVER_TOKEN과 PUSHOVER_USER 설정
  2. python scripts/test_pushover_real.py 실행
"""
import os
import sys
import requests
from dotenv import load_dotenv

# PipelineStatus 단순 구현 (의존성 없이)
class PipelineStatus:
    def __init__(self):
        self.steps = {}
        self.errors = {}
        self.youtube_url = None

# STEP 상수
STEP_SCRAPE = "scrape"
STEP_TRANSLATE = "translate"
STEP_TTS = "tts"
STEP_VIDEO = "video"
STEP_UPLOAD = "upload"
STEP_ARCHIVE = "archive"
ALL_STEPS = [STEP_SCRAPE, STEP_TRANSLATE, STEP_TTS, STEP_VIDEO, STEP_UPLOAD, STEP_ARCHIVE]

# PushoverNotifier 단순 구현 (requests만 사용)
class PushoverNotifier:
    API_URL = "https://api.pushover.net/1/messages.json"
    MAX_MESSAGE_LENGTH = 1024
    MAX_TITLE_LENGTH = 250
    MAX_URL_LENGTH = 512
    DEFAULT_RETRY = 300
    DEFAULT_EXPIRE = 3600

    def __init__(self, token: str, user: str):
        self.token = token
        self.user = user

    def send_notification(self, status: PipelineStatus) -> bool:
        try:
            title, message, priority, url = self._format_message(status)
            return self._send(title, message, priority, url)
        except Exception as e:
            print(f"❌ 예외 발생: {e}")
            return False

    def _send(self, title: str, message: str, priority: int, url: str | None) -> bool:
        title = title[:self.MAX_TITLE_LENGTH]
        message = message[:self.MAX_MESSAGE_LENGTH]
        if url:
            url = url[:self.MAX_URL_LENGTH]

        data = {
            "token": self.token,
            "user": self.user,
            "title": title,
            "message": message,
            "priority": priority,
        }

        if url:
            data["url"] = url

        if priority == 2:
            data["retry"] = self.DEFAULT_RETRY
            data["expire"] = self.DEFAULT_EXPIRE

        print(f"API 호출: title={title[:30]}..., priority={priority}")
        response = requests.post(self.API_URL, data=data, timeout=10)

        if response.status_code == 429:
            print(f"❌ Rate Limit 초과 (HTTP 429)")
            return False

        if response.status_code != 200:
            print(f"❌ API 실패: HTTP {response.status_code}")
            return False

        result = response.json()
        if result.get("status") != 1:
            print(f"❌ API 에러: {result.get('errors', [])}")
            return False

        print(f"✅ 알림 전송 성공")
        return True

    def _format_message(self, status: PipelineStatus) -> tuple:
        completed_steps = [s for s in ALL_STEPS if status.steps.get(s, False)]

        if status.steps and all(status.steps.values()) and not status.errors:
            title = "✅ 뉴스 영상 완료"
            message = f"완료 단계: {', '.join(completed_steps)}"
            priority = 0
            url = status.youtube_url
        elif completed_steps:
            failed = next((s for s in ALL_STEPS if s in status.errors), ALL_STEPS[0])
            title = "⚠️ 파이프라인 부분 실패"
            message = f"성공: {', '.join(completed_steps)}\n"
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


def test_all_scenarios():
    """세 가지 시나리오 테스트"""
    load_dotenv()

    # 환경 변수 확인
    token = os.getenv("PUSHOVER_TOKEN")
    user = os.getenv("PUSHOVER_USER")

    if not token or not user:
        print("❌ 환경 변수 미설정")
        print("\n.env 파일에 다음을 추가하세요:")
        print("PUSHOVER_TOKEN=your_app_token_here")
        print("PUSHOVER_USER=your_user_key_here")
        return

    print("=" * 50)
    print("📱 Pushover 실제 API 호출 테스트")
    print("=" * 50)
    print(f"Token: {token[:10]}...")
    print(f"User: {user[:10]}...")
    print()

    notifier = PushoverNotifier(token, user)

    # 시나리오 1: 전체 성공
    print("\n[테스트 1/3] 전체 성공 시나리오")
    status_success = PipelineStatus()
    for step in ALL_STEPS:
        status_success.steps[step] = True
    status_success.youtube_url = "https://youtu.be/dQw4w9WgXcQ"

    result = notifier.send_notification(status_success)
    print(f"결과: {'✅ 성공' if result else '❌ 실패'}")

    # 10초 대기 (너무 빠른 연속 호출 방지)
    import time
    time.sleep(10)

    # 시나리오 2: 부분 실패
    print("\n[테스트 2/3] 부분 실패 시나리오")
    status_partial = PipelineStatus()
    status_partial.steps[STEP_SCRAPE] = True
    status_partial.steps[STEP_TRANSLATE] = True
    status_partial.steps[STEP_TTS] = True
    status_partial.steps[STEP_VIDEO] = True
    status_partial.errors[STEP_UPLOAD] = "API quota exceeded"

    result = notifier.send_notification(status_partial)
    print(f"결과: {'✅ 성공' if result else '❌ 실패'}")

    time.sleep(10)

    # 시나리오 3: 전체 실패
    print("\n[테스트 3/3] 전체 실패 시나리오")
    status_total = PipelineStatus()
    status_total.errors[STEP_SCRAPE] = "Network error: Connection refused"

    result = notifier.send_notification(status_total)
    print(f"결과: {'✅ 성공' if result else '❌ 실패'}")

    print("\n" + "=" * 50)
    print("🎉 모든 테스트 완료")
    print("=" * 50)


if __name__ == "__main__":
    test_all_scenarios()
