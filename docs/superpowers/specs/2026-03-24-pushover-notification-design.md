# Pushover 알림 시스템 설계 문서

**작성일**: 2026-03-24
**버전**: 0.2.0
**상태**: 설계 제안 (수정됨)

---

## 1. 개요

### 1.1 목적
베트남 뉴스 자동화 파이프라인의 실행 결과를 Pushover API를 통해 모바일 알림으로 전송합니다.

### 1.2 요구사항
- 파이프라인 6단계 완료 후 무조건 알림 전송 (finally 블록)
- 2~6단계는 전단계 성공 시에만 실행 (순차적 의존)
- 전체/부분 성공, 실패 여부에 따른 차별화된 알림
- 알림 실패가 파이프라인을 중단시키지 않아야 함

---

## 2. 아키텍처

### 2.1 파이프라인 구조

```
1(수집) → 2(번역) → 3(TTS) → 4(영상) → 5(Youtube) → 6(archive)
                                              ↓
                                          finally → 7(알림)
```

### 2.2 실행 흐름

```python
import logging
from today_vn_news.logger import logger

# 단계 키 상수
STEP_SCRAPE = "scrape"
STEP_TRANSLATE = "translate"
STEP_TTS = "tts"
STEP_VIDEO = "video"
STEP_UPLOAD = "upload"
STEP_ARCHIVE = "archive"

try:
    # 1단계: 수집
    scrape_and_save(...)
    status.steps[STEP_SCRAPE] = True

    # 2단계: 번역 (1단계 성공 시)
    translate_and_save(...)
    status.steps[STEP_TRANSLATE] = True

    # 3단계: TTS (2단계 성공 시)
    yaml_to_tts(...)
    status.steps[STEP_TTS] = True

    # 4단계: 영상 (3단계 성공 시)
    synthesize_video(...)
    status.steps[STEP_VIDEO] = True

    # 5단계: YouTube (4단계 성공 시)
    upload_video(...)
    status.steps[STEP_UPLOAD] = True

    # 6단계: archive (5단계 성공 & 파일 존재 시)
    video_path_for_archive = f"{data_dir}/{yymmdd_hhmm}_final.mp4"
    if os.path.exists(video_path_for_archive):
        archiver.archive(video_path_for_archive, yymmdd_hhmm)
        status.steps[STEP_ARCHIVE] = True

except Exception as e:
    # 현재 실행 중인 단계 확인 후 에러 기록
    current_step = next((s for s in [STEP_SCRAPE, STEP_TRANSLATE, STEP_TTS, STEP_VIDEO, STEP_UPLOAD, STEP_ARCHIVE] if s not in status.steps), "unknown")
    status.errors[current_step] = str(e)
    logger.error(f"파이프라인 실패 ({current_step}): {e}")

finally:
    # 7단계: 알림 (무조건 실행)
    notifier = PushoverNotifier.from_env_or_none()
    if notifier:
        notifier.send_notification(status)
```

---

## 3. 컴포넌트 설계

### 3.1 PipelineStatus 클래스

**위치**: `today_vn_news/notifications/pipeline_status.py`

```python
from dataclasses import dataclass, field

# 단계 키 상수 (PushoverNotifier와 공유)
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
    youtube_url: str | None = None

    @property
    def success(self) -> bool:
        """전체 성공 여부 (빈 steps 딕셔너리는 실패로 처리)"""
        return bool(self.steps) and all(self.steps.values()) and not self.errors

    @property
    def failed_step(self) -> str | None:
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

### 3.2 PushoverNotifier 클래스

**위치**: `today_vn_news/notifications/pushover.py`

```python
import os
import requests
from today_vn_news.logger import logger
from today_vn_news.notifications.pipeline_status import PipelineStatus

# Emergency priority 기본값
DEFAULT_RETRY = 300      # 5분마다 재시도 (Pushover 권장 최소값: 30초)
DEFAULT_EXPIRE = 3600    # 1시간 후 만료 (Pushover 최대값: 10800초 = 3시간)

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
    def from_env_or_none(cls) -> "PushoverNotifier | None":
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

    def _send(self, title: str, message: str, priority: int, url: str | None) -> bool:
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
            first_error = status.errors.get("scrape", "알 수 없는 오류")
            message = f"사유: {first_error}"
            priority = 2
            url = None

        return title, message, priority, url
```

---

## 4. 알림 포맷 및 우선순위

### 4.1 우선순위 체계 및 필수 파라미터

| 상태 | 우선순위 | 제목 | 필수 파라미터 | quiet hours |
|------|----------|------|---------------|-------------|
| 전체 성공 | 0 (Normal) | ✅ 뉴스 영상 완료 | - | 영향받음 |
| 부분 성공 | 1 (High) | ⚠️ 파이프라인 부분 실패 | - | **우회** |
| 전체 실패 | 2 (Emergency) | ❌ 파이프라인 실패 | `retry`, `expire` | **우회** |

### 4.2 Emergency Priority 파라미터

```python
# Pushover API 스펙 준수
DEFAULT_RETRY = 300      # 5분마다 재시도 (최소 30초)
DEFAULT_EXPIRE = 3600    # 1시간 후 만료 (최대 10800초 = 3시간)
```

---

## 5. 환경 설정

### 5.1 .env.example 추가

```bash
# Pushover 알림 (선택 - 미설정 시 알림 skip)
PUSHOVER_TOKEN=your_app_token_here
PUSHOVER_USER=your_user_key_here
```

### 5.2 환경 변수 검증

- `PUSHOVER_TOKEN`: Pushover 애플리케이션 토큰 (30자, 영숫자)
- `PUSHOVER_USER`: Pushover 사용자 키 (30자, 영숫자)
- **선택적**: 미설정 시 `from_env_or_none()`이 `None` 반환하여 알림 skip

---

## 6. 파일 구조

```
today_vn_news/
├── notifications/
│   ├── __init__.py
│   ├── pipeline_status.py   # PipelineStatus 클래스 + STEP 상수
│   └── pushover.py          # PushoverNotifier 클래스
├── exceptions.py             # (변경 없음)
└── .env.example              # PUSHOVER_* 추가

tests/unit/
└── test_notifications/
    ├── __init__.py
    ├── test_pushover.py       # PushoverNotifier 테스트
    └── test_pipeline_status.py # PipelineStatus 테스트
```

---

## 7. 구현 시나리오

### 7.1 시나리오 1: 전체 성공
```
[단계]
1. 수집 → 성공
2. 번역 → 성공
3. TTS → 성공
4. 영상 → 성공
5. YouTube → 성공 (URL: https://youtu.be/abc123)
6. Archive → 성공

[알림]
제목: ✅ 뉴스 영상 완료
내용: 완료 단계: scrape, translate, tts, video, upload, archive
URL: https://youtu.be/abc123
우선순위: 0 (Normal)
```

### 7.2 시나리오 2: 부분 실패
```
[단계]
1. 수집 → 성공
2. 번역 → 성공
3. TTS → 성공
4. 영상 → 성공
5. YouTube → 실패 (API quota exceeded)
6. Archive → 건너뜀 (파일 없음)

[알림]
제목: ⚠️ 파이프라인 부분 실패
내용: 성공: scrape, translate, tts, video
     실패: upload - API quota exceeded
우선순위: 1 (High, quiet hours 우회)
```

### 7.3 시나리오 3: 초기 실패
```
[단계]
1. 수집 → 실패 (Network error)
2~6단계 → 실행 안 됨

[알림]
제목: ❌ 파이프라인 실패
내용: 사유: Network error
우선순위: 2 (Emergency)
파라미터: retry=300, expire=3600
```

### 7.4 시나리오 4: 알림 전송 실패
```
[상황]
- 파이프라인은 성공했으나 Pushover API 호출 실패
- 예: HTTP 429 (Rate Limit), 네트워크 오류, 잘못된 토큰

[동작]
1. PushoverNotifier.send_notification()이 False 반환
2. logger.error()로 에러 기록
3. 파이프라인은 정상 종료 (예외 전파 없음)
4. 사용자에게 별도 안내 없음 (silent failure)

[로그 예시]
ERROR: Pushover 알림 실패: HTTP 429 - Rate Limit 초과
INFO: 🎉 모든 파이프라인 작업이 성공적으로 완료되었습니다!
```

---

## 8. 테스트 전략

### 8.1 단위 테스트

#### PipelineStatus 테스트
- 전체 성공 시 `success=True`
- 빈 steps 딕셔너리일 때 `success=False`
- 부분 성공 시 `completed_steps`, `failed_step` 정확성
- 전체 실패 시 빈 `completed_steps`

#### PushoverNotifier 테스트
- API 호출 파라미터 검증 (mock 사용)
- 메시지 포맷 검증
- 메시지 길이 초과 시 자르기 동작
- API 실패 시 예외 없이 `False` 반환
- HTTP 429 (Rate Limit) 특수 처리
- 환경 변수 누락 시 `from_env_or_none()`이 `None` 반환
- Emergency priority 시 `retry`, `expire` 파라미터 포함

### 8.2 Mock 전략
```python
@pytest.fixture
def mock_pushover_response(monkeypatch):
    def mock_post(url, data, **kwargs):
        return Mock(status_code=200, json={"status": 1})
    monkeypatch.setattr("requests.post", mock_post)

@pytest.fixture
def mock_pushover_rate_limit(monkeypatch):
    def mock_post(url, data, **kwargs):
        return Mock(status_code=429)
    monkeypatch.setattr("requests.post", mock_post)
```

### 8.3 통합 테스트
- 실제 파이프라인 실행 후 finally에서 알림 전송 확인
- API 키 없으면 skip (`from_env_or_none()` 사용)

---

## 9. 제약사항

### 9.1 API 제약

| 항목 | 제한 | 처리 방식 |
|------|------|-----------|
| 메시지 길이 | 1,024자 | 초과 시 자르기 |
| 제목 길이 | 250자 | 초과 시 자르기 |
| URL 길이 | 512자 | 초과 시 자르기 |
| Rate Limit | 월 10,000건 | HTTP 429 시 False 반환 |
| 동시 요청 | 2개 | 순차 실행으로 자동 준수 |

### 9.2 실패 처리

| 에러 유형 | HTTP 상태 | 처리 방식 |
|-----------|-----------|-----------|
| 정상 | 200 | `status=1` 확인 후 성공 |
| Rate Limit | 429 | 로그 경고, False 반환 |
| 잘못된 요청 | 4xx | 로그 에러, False 반환 |
| 서버 오류 | 5xx | 로그 에러, False 반환 |
| 네트워크 오류 | - | 예외 catch, False 반환 |

**공통 원칙**: 알림 실패가 파이프라인을 중단시키지 않음 (silent failure)

---

## 10. 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| 0.1.0 | 2026-03-24 | 초기 설계 |
| 0.2.0 | 2026-03-24 | 리뷰 피드백 반영 (11개 문제점 수정) |

### 0.2.0 수정 사항
1. **PipelineStatus.success**: 빈 딕셔너리 체크 로직 추가
2. **에러 키 네이밍**: STEP_* 상수 정의
3. **_send 메서드**: 구현 추가 (길이 검증 포함)
4. **from_env_or_none**: 선택적 동작 지원 메서드 추가
5. **Emergency priority**: `retry`, `expire` 파라미터 추가
6. **priority별 파라미터**: 표로 정리 (4.1 섹션)
7. **메시지 길이 검증**: 자르기 로직 추가 (_send 메서드)
8. **Rate Limit 처리**: HTTP 429 특수 처리 (9.2 섹션)
9. **Archive 변수명**: `video_path_for_archive`로 구체화
10. **알림 실패 시나리오**: 7.4 섹션 추가
11. **로거 임포트**: `from today_vn_news.logger import logger` 추가

---

## 11. 향후 확장 가능성

- 다른 알림 채널 지원 (Slack, Discord, Telegram)
- 알림 템플릿/사운드 커스터마이징
- 재시도 로직 (Emergency priority 2의 retry/expire 활용)
- 알림 대상 그룹핑
