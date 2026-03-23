# Pushover 알림 시스템 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 베트남 뉴스 파이프라인 완료 후 Pushover API로 모바일 알림 전송

**Architecture:** PipelineStatus로 파이프라인 상태 추적 → PushoverNotifier로 알림 전송 → main.py finally 블록에서 무조건 실행

**Tech Stack:** Python 3.13, requests, dataclasses, pytest

---

## 파일 구조

```
today_vn_news/
├── notifications/                    # 신규 패키지
│   ├── __init__.py                   # from .pipeline_status import PipelineStatus
│   ├── pipeline_status.py            # PipelineStatus 클래스 + STEP_* 상수
│   └── pushover.py                   # PushoverNotifier 클래스
├── main.py                           # 수정: PipelineStatus 추적 + finally 알림
└── .env.example                      # 수정: PUSHOVER_* 추가

tests/unit/
└── test_notifications/               # 신규 테스트 패키지
    ├── __init__.py
    ├── test_pipeline_status.py       # PipelineStatus 단위 테스트
    └── test_pushover.py              # PushoverNotifier 단위 테스트
```

---

## Task 1: PipelineStatus 클래스 구현

**Files:**
- Create: `today_vn_news/notifications/__init__.py`
- Create: `today_vn_news/notifications/pipeline_status.py`
- Create: `tests/unit/test_notifications/__init__.py`
- Create: `tests/unit/test_notifications/test_pipeline_status.py`

---

- [ ] **Step 1: 테스트 디렉토리 생성**

```bash
mkdir -p tests/unit/test_notifications
mkdir -p today_vn_news/notifications
```

---

- [ ] **Step 2: notifications/__init__.py 작성**

```python
# today_vn_news/notifications/__init__.py
from .pipeline_status import PipelineStatus, ALL_STEPS, STEP_SCRAPE, STEP_TRANSLATE, STEP_TTS, STEP_VIDEO, STEP_UPLOAD, STEP_ARCHIVE

__all__ = ["PipelineStatus", "ALL_STEPS", "STEP_SCRAPE", "STEP_TRANSLATE", "STEP_TTS", "STEP_VIDEO", "STEP_UPLOAD", "STEP_ARCHIVE"]
```

---

- [ ] **Step 3: test_notifications/__init__.py 작성**

```python
# tests/unit/test_notifications/__init__.py
"""알림 모듈 테스트"""
```

---

- [ ] **Step 4: test_pipeline_status.py - 빈 steps 테스트 작성**

```python
# tests/unit/test_notifications/test_pipeline_status.py
import pytest
from today_vn_news.notifications import PipelineStatus, STEP_SCRAPE, STEP_TRANSLATE


class TestPipelineStatusSuccess:
    """PipelineStatus.success 프로퍼티 테스트"""

    def test_empty_steps_returns_false(self):
        """빈 steps 딕셔너리일 때 success는 False"""
        status = PipelineStatus()
        assert status.success is False

    def test_all_steps_true_no_errors_returns_true(self):
        """모든 단계 성공, 에러 없으면 success는 True"""
        status = PipelineStatus()
        status.steps[STEP_SCRAPE] = True
        status.steps[STEP_TRANSLATE] = True
        assert status.success is True

    def test_partial_success_with_error_returns_false(self):
        """일부 성공이어도 에러 있으면 success는 False"""
        status = PipelineStatus()
        status.steps[STEP_SCRAPE] = True
        status.errors[STEP_TRANSLATE] = "API error"
        assert status.success is False

    def test_all_steps_true_with_error_returns_false(self):
        """모든 단계 성공해도 에러 있으면 success는 False"""
        status = PipelineStatus()
        status.steps[STEP_SCRAPE] = True
        status.steps[STEP_TRANSLATE] = True
        status.errors["upload"] = "Quota exceeded"
        assert status.success is False
```

---

- [ ] **Step 5: 테스트 실행 - 실패 확인**

```bash
uv run pytest tests/unit/test_notifications/test_pipeline_status.py -v
```

Expected: FAIL (ModuleNotFoundError)

---

- [ ] **Step 6: pipeline_status.py - STEP 상수 및 클래스 구현**

```python
# today_vn_news/notifications/pipeline_status.py
from dataclasses import dataclass, field
from typing import Optional

# 단계 키 상수
STEP_SCRAPE = "scrape"
STEP_TRANSLATE = "translate"
STEP_TTS = "tts"
STEP_VIDEO = "video"
STEP_UPLOAD = "upload"
STEP_ARCHIVE = "archive"

ALL_STEPS = [STEP_SCRAPE, STEP_TRANSLATE, STEP_TTS, STEP_VIDEO, STEP_UPLOAD, STEP_ARCHIVE]


@dataclass
class PipelineStatus:
    """파이프라인 실행 상태 추적

    steps 딕셔너리 키 규칙:
    - "scrape": 뉴스 수집 단계
    - "translate": 번역 단계
    - "tts": TTS 음성 생성 단계
    - "video": 영상 합성 단계
    - "upload": YouTube 업로드 단계
    - "archive": Media 저장 단계
    """
    steps: dict[str, bool] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)
    youtube_url: Optional[str] = None

    @property
    def success(self) -> bool:
        """전체 성공 여부 (빈 steps 딕셔너리는 실패로 처리)"""
        return bool(self.steps) and all(self.steps.values()) and not self.errors

    @property
    def failed_step(self) -> Optional[str]:
        """첫 번째 실패 단계 반환"""
        for step in ALL_STEPS:
            if step in self.steps and not self.steps[step]:
                return step
            if step in self.errors:
                return step
        return None

    @property
    def completed_steps(self) -> list[str]:
        """성공한 단계 목록 (순서 보장)"""
        return [step for step in ALL_STEPS if self.steps.get(step, False)]
```

---

- [ ] **Step 7: 테스트 실행 - 통과 확인**

```bash
uv run pytest tests/unit/test_notifications/test_pipeline_status.py -v
```

Expected: PASS

---

- [ ] **Step 8: failed_step 테스트 추가**

```python
# tests/unit/test_notifications/test_pipeline_status.py 파일 끝에 추가

class TestPipelineStatusFailedStep:
    """PipelineStatus.failed_step 프로퍼티 테스트"""

    def test_no_failure_returns_none(self):
        """실패 없으면 None 반환"""
        status = PipelineStatus()
        status.steps[STEP_SCRAPE] = True
        assert status.failed_step is None

    def test_first_failed_step_returned(self):
        """첫 번째 실패 단계 반환"""
        status = PipelineStatus()
        status.steps[STEP_SCRAPE] = True
        status.errors[STEP_TRANSLATE] = "API error"
        assert status.failed_step == STEP_TRANSLATE

    def test_completed_steps_empty_on_all_fail(self):
        """전체 실패 시 completed_steps는 빈 리스트"""
        status = PipelineStatus()
        status.errors[STEP_SCRAPE] = "Network error"
        assert status.completed_steps == []
```

---

- [ ] **Step 9: 테스트 실행 - 통과 확인**

```bash
uv run pytest tests/unit/test_notifications/test_pipeline_status.py -v
```

Expected: PASS

---

- [ ] **Step 10: 커밋**

```bash
git add today_vn_news/notifications/ tests/unit/test_notifications/
git commit -m "feat(notifications): PipelineStatus 클래스 구현

- STEP_* 상수 정의 (scrape, translate, tts, video, upload, archive)
- PipelineStatus 데이터클래스 구현
- success, failed_step, completed_steps 프로퍼티
- 빈 steps 딕셔너리 처리 로직 포함

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 2: PushoverNotifier 클래스 구현

**Files:**
- Create: `today_vn_news/notifications/pushover.py`
- Create: `tests/unit/test_notifications/test_pushover.py`

---

- [ ] **Step 1: test_pushover.py - from_env_or_none 테스트 작성**

```python
# tests/unit/test_notifications/test_pushover.py
import os
import pytest
from unittest.mock import Mock, patch
from today_vn_news.notifications.pushover import PushoverNotifier
from today_vn_news.notifications import PipelineStatus, STEP_SCRAPE


class TestPushoverNotifierCreation:
    """PushoverNotifier 인스턴스 생성 테스트"""

    def test_from_env_or_none_returns_none_when_missing(self, monkeypatch):
        """환경 변수 없으면 None 반환"""
        monkeypatch.delenv("PUSHOVER_TOKEN", raising=False)
        monkeypatch.delenv("PUSHOVER_USER", raising=False)

        result = PushoverNotifier.from_env_or_none()
        assert result is None

    def test_from_env_or_none_returns_instance_when_set(self, monkeypatch):
        """환경 변수 있으면 인스턴스 반환"""
        monkeypatch.setenv("PUSHOVER_TOKEN", "test_token_123456789012345678")
        monkeypatch.setenv("PUSHOVER_USER", "test_user_123456789012345678")

        result = PushoverNotifier.from_env_or_none()
        assert result is not None
        assert result.token == "test_token_123456789012345678"
        assert result.user == "test_user_123456789012345678"

    def test_from_env_raises_when_missing(self, monkeypatch):
        """from_env는 환경 변수 없으면 ValueError"""
        monkeypatch.delenv("PUSHOVER_TOKEN", raising=False)
        monkeypatch.delenv("PUSHOVER_USER", raising=False)

        with pytest.raises(ValueError, match="PUSHOVER_TOKEN and PUSHOVER_USER required"):
            PushoverNotifier.from_env()
```

---

- [ ] **Step 2: 테스트 실행 - 실패 확인**

```bash
uv run pytest tests/unit/test_notifications/test_pushover.py -v
```

Expected: FAIL (ModuleNotFoundError)

---

- [ ] **Step 3: pushover.py - 클래스 기본 구조 구현**

```python
# today_vn_news/notifications/pushover.py
import os
from typing import Optional
import requests

from today_vn_news.logger import logger
from today_vn_news.notifications.pipeline_status import PipelineStatus

# Emergency priority 기본값
DEFAULT_RETRY = 300      # 5분마다 재시도
DEFAULT_EXPIRE = 3600    # 1시간 후 만료

# 메시지 길이 제한 (Pushover API 스펙)
MAX_MESSAGE_LENGTH = 1024
MAX_TITLE_LENGTH = 250
MAX_URL_LENGTH = 512


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
```

---

- [ ] **Step 4: 테스트 실행 - 통과 확인**

```bash
uv run pytest tests/unit/test_notifications/test_pushover.py::TestPushoverNotifierCreation -v
```

Expected: PASS

---

- [ ] **Step 5: test_pushover.py - send_notification 테스트 추가**

```python
# tests/unit/test_notifications/test_pushover.py 파일 끝에 추가

class TestPushoverNotifierSend:
    """PushoverNotifier.send_notification 테스트"""

    def test_send_notification_success(self, monkeypatch):
        """API 성공 시 True 반환"""
        monkeypatch.setenv("PUSHOVER_TOKEN", "test_token")
        monkeypatch.setenv("PUSHOVER_USER", "test_user")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": 1}

        with patch("requests.post", return_value=mock_response) as mock_post:
            notifier = PushoverNotifier.from_env()
            status = PipelineStatus()
            status.steps[STEP_SCRAPE] = True

            result = notifier.send_notification(status)

            assert result is True
            mock_post.assert_called_once()
            # API 호출 파라미터 검증
            call_data = mock_post.call_args[1]["data"]
            assert call_data["token"] == "test_token"
            assert data_data["user"] == "test_user"

    def test_send_notification_rate_limit_returns_false(self, monkeypatch):
        """HTTP 429 Rate Limit 시 False 반환"""
        monkeypatch.setenv("PUSHOVER_TOKEN", "test_token")
        monkeypatch.setenv("PUSHOVER_USER", "test_user")

        mock_response = Mock()
        mock_response.status_code = 429

        with patch("requests.post", return_value=mock_response):
            notifier = PushoverNotifier.from_env()
            status = PipelineStatus()

            result = notifier.send_notification(status)
            assert result is False

    def test_send_notification_api_error_returns_false(self, monkeypatch):
        """API 에러 시 False 반환 (예외 없음)"""
        monkeypatch.setenv("PUSHOVER_TOKEN", "test_token")
        monkeypatch.setenv("PUSHOVER_USER", "test_user")

        with patch("requests.post", side_effect=Exception("Network error")):
            notifier = PushoverNotifier.from_env()
            status = PipelineStatus()

            result = notifier.send_notification(status)
            assert result is False

    def test_send_notification_emergency_includes_retry_expire(self, monkeypatch):
        """Emergency priority(2) 시 retry, expire 파라미터 포함"""
        monkeypatch.setenv("PUSHOVER_TOKEN", "test_token")
        monkeypatch.setenv("PUSHOVER_USER", "test_user")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": 1}

        with patch("requests.post", return_value=mock_response) as mock_post:
            notifier = PushoverNotifier.from_env()
            status = PipelineStatus()
            status.errors[STEP_SCRAPE] = "Network error"  # 전체 실패 = Emergency

            result = notifier.send_notification(status)

            call_data = mock_post.call_args[1]["data"]
            assert call_data["priority"] == 2
            assert call_data["retry"] == DEFAULT_RETRY
            assert call_data["expire"] == DEFAULT_EXPIRE
```

---

- [ ] **Step 6: 테스트 실행 - 실패 확인**

```bash
uv run pytest tests/unit/test_notifications/test_pushover.py::TestPushoverNotifierSend -v
```

Expected: FAIL (AttributeError: 'PushoverNotifier' object has no attribute 'send_notification')

---

- [ ] **Step 7: pushover.py - send_notification 구현**

```python
# today_vn_news/notifications/pushover.py 파일 끝에 추가

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

    def _format_message(self, status: PipelineStatus) -> tuple:
        """메시지 포맷팅 및 우선순위 결정"""
        if status.success:
            title = "✅ 뉴스 영상 완료"
            message = f"완료 단계: {', '.join(status.completed_steps)}"
            priority = 0
            url = status.youtube_url

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
```

---

- [ ] **Step 8: 테스트 실행 - 통과 확인**

```bash
uv run pytest tests/unit/test_notifications/test_pushover.py -v
```

Expected: PASS

---

- [ ] **Step 9: 커밋**

```bash
git add today_vn_news/notifications/pushover.py tests/unit/test_notifications/test_pushover.py
git commit -m "feat(notifications): PushoverNotifier 클래스 구현

- from_env_or_none() 선택적 환경 변수 로드
- send_notification() silent failure 지원
- _send() Pushover API 호출 (길이 검증, Rate Limit 처리)
- _format_message() 우선순위별 메시지 포맷팅
- Emergency priority 시 retry, expire 파라미터 포함

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 3: main.py 통합

**Files:**
- Modify: `today_vn_news/main.py`
- Modify: `.env.example`

---

- [ ] **Step 1: main.py import 추가**

```python
# today_vn_news/main.py 상단 import 섹션에 추가
from today_vn_news.notifications import PipelineStatus, STEP_SCRAPE, STEP_TRANSLATE, STEP_TTS, STEP_VIDEO, STEP_UPLOAD, STEP_ARCHIVE
from today_vn_news.notifications.pushover import PushoverNotifier
```

---

- [ ] **Step 2: main() 함수에 PipelineStatus 초기화 추가**

```python
# today_vn_news/main.py main() 함수 시작 부분에 추가
async def main():
    # ... 기존 코드 ...

    # 파이프라인 상태 추적
    status = PipelineStatus()

    # 기존 코드 계속...
```

---

- [ ] **Step 3: 각 단계에 status.steps 기록 추가**

main() 함수의 각 단계 성공 후 `status.steps[STEP_*] = True` 추가:

```python
# 1단계: 스크래핑 성공 후
scraped_data = scrape_and_save(today_iso, raw_yaml_path)
status.steps[STEP_SCRAPE] = True

# 2단계: 번역 성공 후
if not save_translated_yaml(yaml_data, today_display, yaml_path):
    ...
status.steps[STEP_TRANSLATE] = True

# 3단계: TTS 성공 후
await yaml_to_tts(...)
status.steps[STEP_TTS] = True
```

---

- [ ] **Step 4: process_video_pipeline() 수정**

```python
# today_vn_news/main.py process_video_pipeline() 함수 수정

async def process_video_pipeline(
    yymmdd_hhmm: str,
    data_dir: str,
    config: VideoConfig,
    status: PipelineStatus  # 추가
) -> bool:
    resolver = VideoSourceResolver(config)
    archiver = MediaArchiver(config)

    try:
        # 1. 영상 소스 해결
        print("\n[*] 영상 소스 확인 중...")
        source_path, _ = resolver.resolve(yymmdd_hhmm)

        # 2. 영상 합성
        print("\n[*] 영상 합성 시작...")
        synthesize_video(
            base_name=yymmdd_hhmm,
            data_dir=data_dir,
            source_path=str(source_path)
        )
        status.steps[STEP_VIDEO] = True

        # 3. Media에 저장
        local_final = f"{data_dir}/{yymmdd_hhmm}_final.mp4"
        local_audio = f"{data_dir}/{yymmdd_hhmm}.mp3"
        media_path_final = None

        # 3-1. MP3 음성 저장
        if os.path.exists(local_audio):
            try:
                print("\n[*] Media에 MP3 음성 저장 중...")
                audio_media_path = archiver.archive_audio(local_audio, yymmdd_hhmm)
                print(f"[+] Media MP3 저장 완료: {audio_media_path}")
            except Exception as e:
                print(f"[!] Media MP3 저장 실패 (로컬 유지): {e}")

        # 3-2. MP4 영상 저장
        if os.path.exists(local_final):
            try:
                print("\n[*] Media에 영상 저장 중...")
                media_path_final = archiver.archive(local_final, yymmdd_hhmm)
                print(f"[+] Media 저장 완료: {media_path_final}")
                status.steps[STEP_ARCHIVE] = True
            except Exception as e:
                print(f"[!] Media 저장 실패 (로컬 유지): {e}")

        # 4. 유튜브 업로드
        upload_target = media_path_final if media_path_final and os.path.exists(media_path_final) else local_final

        if os.path.exists(upload_target):
            print("\n[*] 유튜브 업로드 시작...")
            if media_path_final and os.path.exists(media_path_final):
                success = upload_video(yymmdd_hhmm, data_dir, video_path=str(media_path_final))
            else:
                success = upload_video(yymmdd_hhmm, data_dir)

            if success:
                status.steps[STEP_UPLOAD] = True
                # YouTube URL 저장 (uploader.py에서 반환받도록 수정 필요하면 별도 처리)

            return success
        else:
            print("\n[!] 업로드할 최종 영상이 없습니다.")
            return False

    except Exception as e:
        print(f"\n[!] 파이프라인 오류: {e}")
        return False

    finally:
        resolver.cleanup_temporary()
```

---

- [ ] **Step 5: main() 함수에 try-except-finally 추가**

```python
# today_vn_news/main.py main() 함수 수정

async def main():
    # ... 기존 초기화 코드 ...

    status = PipelineStatus()

    try:
        # 1단계: 스크래핑
        print("\n[*] 1단계: 뉴스 스크래핑 시작...")
        raw_yaml_path = f"{data_dir}/{yymmdd_hhmm}_raw.yaml"
        scraped_data = scrape_and_save(today_iso, raw_yaml_path)
        status.steps[STEP_SCRAPE] = True

        # 2단계: 번역
        print("\n[*] 2단계: 뉴스 번역 시작 (병렬 처리)...")
        # ... 기존 번역 코드 ...
        status.steps[STEP_TRANSLATE] = True

        # 3단계: TTS
        print("\n[*] 3단계: TTS 음성 변환 시작...")
        await yaml_to_tts(yaml_path, engine=tts_engine, voice=tts_voice, language=tts_language, instruct=tts_instruct)
        status.steps[STEP_TTS] = True

        # 4-6단계: 영상 파이프라인
        success = await process_video_pipeline(
            yymmdd_hhmm=yymmdd_hhmm,
            data_dir=data_dir,
            config=config,
            status=status
        )

        if success:
            print("\n🎉 모든 파이프라인 작업이 성공적으로 완료되었습니다!")
        else:
            print("\n⚠️ 파이프라인 작업에서 문제가 발생했습니다.")

    except Exception as e:
        # 현재 실행 중인 단계 확인 후 에러 기록
        if STEP_SCRAPE not in status.steps:
            status.errors[STEP_SCRAPE] = str(e)
        elif STEP_TRANSLATE not in status.steps:
            status.errors[STEP_TRANSLATE] = str(e)
        elif STEP_TTS not in status.steps:
            status.errors[STEP_TTS] = str(e)

        print(f"\n[!] 파이프라인 오류: {e}")

    finally:
        # 7단계: Pushover 알림 (무조건 실행)
        notifier = PushoverNotifier.from_env_or_none()
        if notifier:
            print("\n[*] 알림 전송 중...")
            notifier.send_notification(status)

        print("=" * 40)
```

---

- [ ] **Step 6: .env.example 수정**

```bash
# .env.example 파일 끝에 추가

# Pushover 알림 (선택 - 미설정 시 알림 skip)
PUSHOVER_TOKEN=your_app_token_here
PUSHOVER_USER=your_user_key_here
```

---

- [ ] **Step 7: 통합 테스트 실행**

```bash
uv run pytest tests/unit/ -v
```

Expected: PASS

---

- [ ] **Step 8: 커밋**

```bash
git add main.py .env.example
git commit -m "feat(main): Pushover 알림 통합

- PipelineStatus로 파이프라인 상태 추적
- 각 단계 성공 시 status.steps 기록
- finally 블록에서 무조건 알림 전송
- .env.example에 PUSHOVER_* 추가

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 4: 최종 검증

---

- [ ] **Step 1: 전체 테스트 실행**

```bash
uv run pytest -v
```

Expected: PASS

---

- [ ] **Step 2: 린트 검사**

```bash
uv run ruff check today_vn_news/ tests/
```

Expected: No errors

---

- [ ] **Step 3: 최종 커밋**

```bash
git add -A
git commit -m "feat: Pushover 알림 시스템 완성

파이프라인 완료 후 모바일 알림 전송 기능 구현

구현 내용:
- PipelineStatus: 파이프라인 상태 추적
- PushoverNotifier: Pushover API 연동
- main.py: finally 블록에서 무조건 알림 실행

특징:
- 알림 실패가 파이프라인에 영향 없음 (silent failure)
- 우선순위별 차등 알림 (Normal/High/Emergency)
- 선택적 환경 변수 (미설정 시 skip)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 실행 옵션

**Plan complete and saved to `docs/superpowers/plans/2026-03-24-pushover-notification.md`.**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
