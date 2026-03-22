# 영상 소스 우선순위 시스템 설계문서

**작성일:** 2026-03-22
**버전:** 0.2.0
**상태:** Revision (Draft)

## 1. 개요

### 1.1 목적

베트남 뉴스 자동화 파이프라인의 영상 소스 처리 방식을 개선하여 Media 마운트된 공유 저장소의 영상을 우선 사용하고, 최종 산출물을 체계적으로 저장/관리한다.

### 1.2 배경

**현재 문제:**
- 영상 소스가 로컬 data/에 종속되어 유연성 부족
- 최종 산출물(_final.mp4)이 로컬에만 저장되어 관리 어려움
- 사용자가 직접 소스 영상을 준비해도 활용 불가

**개선 효과:**
- Media 공유 저장소의 최신 소스 영상 자동 활용
- 최종 산출물의 중앙화된 저장 (Media/{{YYMM}}/{{DD}}_{{hhmm}}.mp4)
- 로컬은 작업 공간으로만 활용 (임시 파일)

---

## 2. 아키텍처

### 2.1 계층 구조

```
┌─────────────────────────────────────────────────────────────┐
│                    main.py (진입점)                          │
│                  - 설정 로딩 (config.yaml)                   │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│          VideoSourceResolver (새로운 모듈)                   │
│  - 우선순위 체인 관리                                          │
│  - 파일 존재 확인 및 선택                                      │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼ (선택된 소스 → 로컬 임시 복사)
┌─────────────────────────────────────────────────────────────┐
│              engine.py (FFmpeg 합성)                         │
│  - 로컬 data/에서 작업                                       │
│  - 소스 영상 + TTS(mp3) → _final.mp4 생성                    │
└───────────────────────────┬─────────────────────────────────┘
                            │
         ┌──────────────────┴──────────────────┐
         │                                     │
┌────────▼─────────┐               ┌───────────▼──────────┐
│  MediaArchiver    │               │  uploader.py         │
│  (새로운 모듈)     │               │  (로컬에서 실행)      │
│  - _final.mp4를   │               │  - YouTube 업로드    │
│    Media/{{YYMM}}/│               │  (이동 전에 실행)      │
│    {{DD}}_{{hhmm}}.mp4│           └──────────────────────┘
│    로 이동/저장    │
└──────────────────┘
```

### 2.2 데이터 흐름 (260322_1230 예시)

```
1. 소스 영상 획득
   Media/260322.mp4 확인 → 로컬 임시 복사
   └─> 없으면 Media/latest.mp4 확인 → 로컬 임시 복사
   └─> 없으면 Local data/260322_1230.mov 사용

2. 합성 (로컬)
   data/260322_1230.yaml → TTS → data/260322_1230.mp3
   data/260322_1230.mp3 + 소스 영상 → data/260322_1230_final.mp4

3. 저장 (데이터 보존 우선)
   data/260322_1230_final.mp4 → Media/2603/22_1230.mp4
   └─> 폴더 자동 생성: Media/2603/
   └─> 원본 유지: shutil.copy (move 아님)

4. 업로드
   data/260322_1230_final.mp4 → YouTube 업로드

5. 정리
   Media에서 복사한 임시 소스 삭제
   로컬 _final.mp4 삭제 (선택적, 성공 시)
```

---

## 3. 컴포넌트 명세

### 3.1 VideoSourceResolver

**파일:** `today_vn_news/video_source/resolver.py`

```python
class VideoSourceResolver:
    """영상 소스 우선순위 체인 관리"""

    def __init__(self, config: VideoConfig):
        self.config = config
        self.temp_copies: list[str] = []  # 정리할 임시 파일 추적

    def resolve(self, base_name: str) -> tuple[str, bool]:
        """
        우선순위에 따라 영상 소스 반환

        Args:
            base_name: YYMMDD_HHMM (예: 260322_1230)
                       기존 코드와 형식 통일

        Returns:
            (source_path, is_temporary_copy)
            - source_path: 사용할 영상 경로
            - is_temporary_copy: Media에서 복사한 임시 파일인지 여부

        Raises:
            VideoSourceError: 모든 소스 실패 시
        """

    def _cleanup_temporary(self) -> None:
        """임시 복사본 정리"""
```

**우선순위 체인:**
1. `Media/{{YYMMDD}}.mp4` (예: Media/260322.mp4)
2. `Media/latest.mp4`
3. `Local data/{{YYMMDD}}_{{hhmm}}.mov` (예: data/260322_1230.mov)
4. `Local data/{{YYMMDD}}_{{hhmm}}.mp4` (예: data/260322_1230.mp4)
5. `assets/default_bg.png`

**핵심 로직:**
- Media 소스 사용 시 로컬 data/로 임시 복사 (`is_temporary_copy=True`)
- 복사된 파일은 `_cleanup_temporary()`에서 정리
- 모든 확인 실패 시 로그만 남기고 fallback (조용히 진행)

---

### 3.2 MediaArchiver

**파일:** `today_vn_news/video_source/archiver.py`

```python
class MediaArchiver:
    """최종 영상을 Media로 이동/저장"""

    def __init__(self, config: VideoConfig):
        self.config = config

    def archive(self, local_final: str, base_name: str) -> str:
        """
        로컬 _final.mp4를 Media/{{YYMM}}/{{DD}}_{{hhmm}}.mp4로 복사

        Args:
            local_final: 로컬 _final.mp4 경로
                       (예: data/260322_1230_final.mp4)
            base_name: YYMMDD_HHMM (예: 260322_1230)

        Returns:
            media_path: Media 저장소 경로
                        (예: /Volumes/Media/2603/22_1230.mp4)

        Raises:
            MediaArchiveError: 복사 실패 시

        Note:
            shutil.copy 사용 (원본 보존, 데이터 손실 방지)
        """

    def _ensure_directory(self, media_base: str, yymm: str) -> None:
        """Media/{{YYMM}}/ 폴더 생성"""
```

**핵심 로직:**
- 대상 경로: `Media/{{YYMM}}/{{DD}}_{{hhmm}}.mp4`
- 폴더 자동 생성 (`os.makedirs(exist_ok=True)`)
- 파일 이동 (`shutil.move`)
- 이미 존재하면 덮어쓰기

---

### 3.3 VideoConfig

**파일:** `today_vn_news/config/video_config.py`

```python
@dataclass
class VideoConfig:
    """영상 소스 설정"""

    # Media 설정
    media_mount_path: str = "/Volumes/Media"
    media_date_format: str = "YYMMDD"
    auto_copy_latest: bool = True

    # 저장 설정
    archive_format: str = "{{YYMM}}/{{DD}}_{{hhmm}}.mp4"

    # Fallback
    local_data_dir: str = "data"
    default_image: str = "assets/default_bg.png"

    @classmethod
    def from_yaml(cls, path: str = "config.yaml") -> "VideoConfig":
        """YAML 설정 로딩

        Args:
            path: 설정 파일 경로

        Returns:
            VideoConfig: 로드된 설정 (파일 없으면 기본값)

        Raises:
            YAMLError: YAML 파싱 실패 (파일 있지만 잘못됨)

        Note:
            파일 없으면 경고 로그 후 기본값 반환 (조용히 진행)
        """
```

**설정 파일 예시:**

```yaml
# config.yaml
video:
  media:
    mount_path: "/Volumes/Media"
    date_format: "YYMMDD"
    auto_copy_latest: true
  archive:
    format: "{{YYMM}}/{{DD}}_{{hhmm}}.mp4"
  fallback:
    local_data_dir: "data"
    default_image: "assets/default_bg.png"
```

---

## 4. 에러 핸들링

### 4.1 추가 예외 타입

```python
# today_vn_news/exceptions.py에 추가

class MediaMountError(TodayVnNewsError):
    """Media 마운트 실패 예외"""
    pass


class MediaCopyError(TodayVnNewsError):
    """Media 파일 복사 실패 예외"""
    pass


class MediaArchiveError(TodayVnNewsError):
    """Media 저장 실패 예외"""
    pass
```

### 4.2 에러 처리 전략

| 단계 | 에러 | 처리 방식 | 로그 레벨 |
|:---|:---|:---|:---|
| **설정 로딩** | config.yaml 없음 | 기본값 사용 후 경고 | warning |
| **소스 확인** | Media 마운트 안됨 | Warning → Fallback | warning |
| **소스 복사** | 복사 실패 | Warning → Fallback | warning |
| **합성** | FFmpeg 실패 | Error → 중단 | error |
| **저장** | Media 복사 실패 | Warning → 로컬 유지 | warning |
| **업로드** | YouTube API 실패 | Error → 중단 | error |
| **정리** | 임시 파일 삭제 실패 | Warning → 무시 | warning |

**원칙:**
- **설정/소스 단계**: 최대한 유연하게 fallback (조용히 진행)
- **저장 단계**: 실패 시 로컬 유지 (복사라 원본 보존됨)
- **합성/업로드 단계**: 실패 시 즉시 중단 (치명적)
- **정리 단계**: 실패해도 로그만 남기고 무시 (임시 파일)

---

## 5. main.py 변경사항

### 5.1 기존 로직 수정

**기존 (engine.py:45-51):**
```python
video_mov = os.path.join(data_dir, f"{base_name}.mov")
video_mp4 = os.path.join(data_dir, f"{base_name}.mp4")
video_in = video_mov if os.path.exists(video_mov) else video_mp4
```

**신규 (main.py):**
```python
from today_vn_news.video_source.resolver import VideoSourceResolver
from today_vn_news.video_source.archiver import MediaArchiver
from today_vn_news.config.video_config import VideoConfig

# 설정 로딩 (config.yaml 없으면 기본값 사용)
config = VideoConfig.from_yaml()

# 소스 영상 해결 (base_name: YYMMDD_HHMM 형식)
resolver = VideoSourceResolver(config)
source_path, is_temporary = resolver.resolve(base_name)

try:
    # 합성 (기존 engine.py 활용, source_path 지원하도록 수정)
    synthesize_video(base_name, data_dir, source_path=source_path)

    # 저장 (데이터 보존 우선: 복사 후 업로드)
    archiver = MediaArchiver(config)
    media_path = archiver.archive(local_final, base_name)
    logger.info(f"최종 영상 저장 완료: {media_path}")

    # 업로드 (기존 로직)
    upload_video(base_name[:8], data_dir)

    # 업로드 성공 시 로컬 정리
    try:
        os.remove(local_final)
        logger.info(f"로컬 임시 파일 삭제: {local_final}")
    except OSError:
        logger.warning(f"로컬 파일 삭제 실패 (무시): {local_final}")

finally:
    # 정리: Media 임시 복사본 삭제 (항상 실행)
    if is_temporary:
        resolver._cleanup_temporary()
```

### 5.2 engine.py 수정사항

**기존 시그니처:**
```python
def synthesize_video(base_name: str, data_dir: str = "data"):
```

**신규 시그니처:**
```python
def synthesize_video(base_name: str, data_dir: str = "data", source_path: str = None):
    """
    영상과 음성을 합성하여 최종 MP4 생성

    Args:
        base_name: YYMMDD_HHMM (예: 260322_1230)
        data_dir: 데이터 디렉토리
        source_path: 소스 영상 경로 (None이면 기존 로직대로 .mov/.mp4 확인)

    Note:
        source_path 지정 시 해당 파일을 video_in으로 사용
        None이면 기존 방식대로 data/{base_name}.mov/.mp4 확인
    """
```

**수정 포인트:**
- `source_path` 파라미터 추가 (선택적, 기본값 None)
- source_path가 None이 아니면 해당 파일을 직접 사용
- source_path가 None이면 기존 로직 (.mov → .mp4 → default_bg.png)

---

## 6. 테스트

### 6.1 단위 테스트

**파일:** `tests/unit/test_video_source_resolver.py`

- `test_resolve_media_yymmdd_exists`: Media/{{YYMMDD}}.mp4 존재 시 우선 반환
- `test_resolve_media_latest_fallback`: Media/{{YYMMDD}}.mp4 없을 때 latest.mp4 반환
- `test_resolve_local_fallback`: Media 모두 없을 때 로컬 .mov/mp4 반환
- `test_resolve_default_image_fallback`: 모든 소스 없을 때 기본 이미지 반환
- `test_temporary_copy_and_cleanup`: Media 소스 복사 후 정리 확인
- `test_resolve_base_name_format`: YYMMDD_HHMM 형식 파싱 확인

**파일:** `tests/unit/test_media_archiver.py`

- `test_archive_creates_directory`: Media/{{YYMM}}/ 폴더 자동 생성 확인
- `test_archive_copies_not_moves`: shutil.copy 사용 확인 (원본 보존)
- `test_archive_correct_naming`: 파일명 {{YYMM}}/{{DD}}_{{hhmm}}.mp4 형식 확인
- `test_archive_overwrites_existing`: 동일 파일명 존재 시 덮어쓰기 확인
- `test_archive_media_mount_failure`: Media 마운트 실패 시 예외 발생 확인

**파일:** `tests/unit/test_video_config.py`

- `test_from_yaml_missing_file`: config.yaml 없을 때 기본값 반환 확인
- `test_from_yaml_invalid_yaml`: YAML 잘못됐을 때 예외 발생 확인
- `test_from_yaml_valid_settings`: 올바른 YAML 로드 확인

### 6.2 통합 테스트

**파일:** `tests/integration/test_video_pipeline.py`

- `test_full_pipeline_with_media_source`: Media 소스 → 합성 → 저장 → 업로드 전체 흐름
- `test_full_pipeline_fallback_to_local`: Media 없을 때 로컬 소스로 fallback 확인
- `test_full_pipeline_save_fails_upload_succeeds`: 저장 실패 시 업로드 진행 확인
- `test_full_pipeline_with_context_manager`: resolver cleanup 항상상 finally에서 실행 확인

### 6.3 모의 데이터 구조

```
tests/fixtures/
├── media/
│   ├── 260322.mp4          # YYMMDD 소스
│   └── latest.mp4          # 최신 소스
├── config.yaml             # 테스트용 설정
└── default_bg.png          # 기본 이미지
```

### 6.4 테스트 마커

- `@pytest.mark.slow`: 실제 API/FFmpeg 호출 (기본 제외)
- `@pytest.mark.media`: Media 마운트 필요 (기본 제외, CI에서 스킵)

---

## 7. 파일 구조 변경

```
today_vn_news/
├── config/
│   ├── __init__.py
│   └── video_config.py           # 신규: 설정 로딩
├── video_source/
│   ├── __init__.py
│   ├── resolver.py                # 신규: 우선순위 체인
│   └── archiver.py                # 신규: 이동/저장
├── engine.py                      # 수정: VideoSourceResolver 활용
├── exceptions.py                  # 수정: 예외 타입 추가
└── config.yaml                    # 신규: 설정 파일

tests/
├── unit/
│   ├── test_video_source_resolver.py  # 신규
│   ├── test_media_archiver.py         # 신규
│   ├── test_engine.py                 # 수정: resolver 적용
│   └── test_video_config.py            # 신규
├── integration/
│   └── test_video_pipeline.py          # 신규
└── fixtures/
    ├── config.yaml                     # 신규
    └── media/                          # 신규
        ├── 260322.mp4
        └── latest.mp4
```

---

## 8. 구현 우선순위

### Phase 1: 기반 구조
1. `exceptions.py`에 예외 타입 추가
2. `video_config.py` 구현
3. `config.yaml` 샘플 작성

### Phase 2: 핵심 로직
1. `resolver.py` 구현 (우선순위 체인)
2. `archiver.py` 구현 (이동/저장)
3. `engine.py` 수정 (resolver 연동)

### Phase 3: 통합
1. `main.py` 수정 (전체 흐름)
2. 단위 테스트 작성
3. 통합 테스트 작성

### Phase 4: 검증
1. 전체 파이프라인 테스트
2. 마무리: 문서 업데이트, README 수정

---

## 9. 롤백 계획

### 9.1 기존 동작 복구

**git reset --hard HEAD~1** 로 충분:
- 신규 파일만 추가 (기존 파일 수정 최소화)
- `engine.py` 변경사항 되돌리기 (source_path 파라미터 제거)

### 9.2 이슈 발생 시 대응

- **Media 마운트 실패**: fallback 동작으로 계속 진행 (로컬 소스 사용)
- **설정 파일 없음**: 기본값(hardcode) 사용 후 경고 로그
- **임시 파일 정리 실패**: 로그만 남기고 무시 (디스크 누적 모니터링 권장)
- **저장 실패**: 로컬 파일 유지 (copy라 원본 보존됨) 후 업로드 진행
- **업로드 실패**: 로컬 _final.mp4 유지 (저장 이미 완료됨)

### 9.3 롤백 검증

```bash
# 롤백 후 기능 검증 커맨드
uv run pytest tests/unit/test_engine.py -v
uv run python main.py  # 기존 파이프라인 실행 확인
```

---

## 10. 참고 자료

- 프로젝트 루트: `CONTEXT.md`, `AGENTS.md`, `ROADMAP.md`
- 기존 코드: `today_vn_news/engine.py:45-64`
- FFmpeg 문서: https://ffmpeg.org/documentation.html
