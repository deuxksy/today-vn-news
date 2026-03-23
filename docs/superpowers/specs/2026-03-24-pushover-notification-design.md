# Pushover 알림 시스템 설계 문서

**작성일**: 2026-03-24
**버전**: 0.1.0
**상태**: 설계 제안

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
try:
    # 1단계: 수집
    scrape_and_save(...)

    # 2단계: 번역 (1단계 성공 시)
    translate_and_save(...)

    # 3단계: TTS (2단계 성공 시)
    yaml_to_tts(...)

    # 4단계: 영상 (3단계 성공 시)
    synthesize_video(...)

    # 5단계: YouTube (4단계 성공 시)
    upload_video(...)

    # 6단계: archive (5단계 성공 & 파일 존재 시)
    if os.path.exists(local_final):
        archiver.archive(...)

except Exception as e:
    # 에러 기록
    ...

finally:
    # 7단계: 알림 (무조건 실행)
    notifier.send_notification(status)
```

---

## 3. 컴포넌트 설계

### 3.1 PipelineStatus 클래스

**위치**: `today_vn_news/notifications/pipeline_status.py`

```python
@dataclass
class PipelineStatus:
    """파이프라인 실행 상태 추적"""
    steps: dict[str, bool] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)
    youtube_url: str | None = None

    @property
    def success(self) -> bool:
        """전체 성공 여부"""
        return all(self.steps.values()) and not self.errors

    @property
    def failed_step(self) -> str | None:
        """첫 번째 실패 단계 반환"""
        for step, success in self.steps.items():
            if not success:
                return step
        return None

    @property
    def completed_steps(self) -> list[str]:
        """성공한 단계 목록"""
        return [step for step, success in self.steps.items() if success]
```

### 3.2 PushoverNotifier 클래스

**위치**: `today_vn_news/notifications/pushover.py`

```python
class PushoverNotifier:
    """Pushover 알림 전송"""

    API_URL = "https://api.pushover.net/1/messages.json"

    def __init__(self, token: str, user: str):
        self.token = token
        self.user = user

    @classmethod
    def from_env(cls) -> "PushoverNotifier":
        """환경 변수에서 로드"""
        token = os.getenv("PUSHOVER_TOKEN")
        user = os.getenv("PUSHOVER_USER")
        if not token or not user:
            raise ValueError("PUSHOVER_TOKEN and PUSHOVER_USER required")
        return cls(token, user)

    def send_notification(self, status: PipelineStatus) -> bool:
        """알림 전송 (실패해도 예외 없이 False 반환)"""
        try:
            title, message, priority, url = self._format_message(status)
            return self._send(title, message, priority, url)
        except Exception as e:
            logger.error(f"Pushover 알림 실패: {e}")
            return False
```

---

## 4. 알림 포맷 및 우선순위

### 4.1 우선순위 체계

| 상태 | 우선순위 | 제목 | 메시지 내용 |
|------|----------|------|-----------|
| 전체 성공 | 0 (Normal) | ✅ 뉴스 영상 완료 | 완료 단계: [목록] + YouTube URL |
| 부분 성공 | 1 (High) | ⚠️ 파이프라인 부분 실패 | 성공: [목록], 실패: [단계] - [사유] |
| 전체 실패 | 2 (Emergency) | ❌ 파이프라인 실패 | 사유: [첫 번째 에러] |

### 4.2 메시지 포맷팅 로직

```python
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

## 5. 환경 설정

### 5.1 .env.example 추가

```bash
# Pushover 알림 (선택)
PUSHOVER_TOKEN=your_app_token_here
PUSHOVER_USER=your_user_key_here
```

### 5.2 환경 변수 검증

- `PUSHOVER_TOKEN`: Pushover 애플리케이션 토큰 (30자, 영숫자)
- `PUSHOVER_USER`: Pushover 사용자 키 (30자, 영숫자)
- 둘 다 필수는 아님 (미설정 시 알림 skip)

---

## 6. 파일 구조

```
today_vn_news/
├── notifications/
│   ├── __init__.py
│   ├── pipeline_status.py   # PipelineStatus 클래스
│   └── pushover.py          # PushoverNotifier 클래스
├── exceptions.py             # NotificationError 추가 (선택)
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
```

---

## 8. 테스트 전략

### 8.1 단위 테스트

#### PipelineStatus 테스트
- 전체 성공 시 `success=True`
- 부분 성공 시 `completed_steps`, `failed_step` 정확성
- 전체 실패 시 빈 `completed_steps`

#### PushoverNotifier 테스트
- API 호출 파라미터 검증 (mock 사용)
- 메시지 포맷 검증
- API 실패 시 예외 없이 `False` 반환
- 환경 변수 누락 시 `ValueError` 발생

### 8.2 Mock 전략
```python
@pytest.fixture
def mock_pushover_response(monkeypatch):
    def mock_post(url, data, **kwargs):
        return Mock(status_code=200, json={"status": 1})
    monkeypatch.setattr("requests.post", mock_post)
```

### 8.3 통합 테스트
- 실제 파이프라인 실행 후 finally에서 알림 전송 확인
- API 키 없으면 skip

---

## 9. 제약사항

### 9.1 API 제약
- **메시지 길이**: 최대 1,024자
- **제목 길이**: 최대 250자
- **URL 길이**: 최대 512자
- **Rate Limit**: 월 10,000건 무료, 동시 2개 요청 제한

### 9.2 실패 처리
- Pushover API 호출 실패 시 파이프라인 계속 진행
- `logger.error()`로 에러 기록만 수행
- 사용자에게는 별도 안내 없음 (silent failure)

---

## 10. 향후 확장 가능성

- 다른 알림 채널 지원 (Slack, Discord, Telegram)
- 알림 템플릿/사운드 커스터마이징
- 재시도 로직 (Emergency priority 2의 retry/expire 활용)
- 알림 대상 그룹핑
