# 파일명 단순화 및 단계별 건너뛰기

**버전**: 1.0
**날짜**: 2026-03-25
**작성자**: AI System Architect

---

## 1. 개요

베트남 뉴스 파이프라인의 파일명 체계를 단순화하고(`YYYYMMDD_hhmm` → `YYMMDD`), 각 단계 완료 시 `.done` 파일을 생성하여 파이프라인 중단 후 재실행 시 완료된 단계를 건너뛰도록 구현합니다.

**핵심 변경사항**:
1. 타임스탬프 형식: `20260319_1955` → `260319`
2. 단계별 완료 표시: `data/{yymmdd}.{module}.done` (모듈명과 일치)
3. 선행 단계 누락 시 처음부터 다시 실행

---

## 2. 파일명 형식

### 타임스탬프 정의

```python
# 현재
yymmdd_hhmm = "20260319_1955"  # YYYYMMDD_hhmm

# 변경 후
yymmdd = "260319"               # YYMMDD (6자리)
```

### 파일명 매핑 테이블

| 단계 | 모듈 | 현재 파일명 | 변경 후 파일명 | 완료 파일 |
|:---|:---|:---|:---|:---|
| 수집 | scraper | `{ts}_raw.yaml` | `{yymmdd}_raw.yaml` | `{yymmdd}.scraper.done` |
| 번역 | translator | `{ts}.yaml` | `{yymmdd}.yaml` | `{yymmdd}.translator.done` |
| TTS | tts | `{ts}.mp3` | `{yymmdd}.mp3` | `{yymmdd}.tts.done` |
| 영상 합성 | engine | `{ts}_final.mp4` | `{yymmdd}_final.mp4` | `{yymmdd}.engine.done` |
| 업로드 | uploader | - | - | `{yymmdd}.uploader.done` |
| 아카이빙 | archiver | - | - | `{yymmdd}.archiver.done` |

---

## 3. 단계별 건너뛰기 로직

### 완료 표시 파일 정의

```
data/
├── 260319.scraper.done
├── 260319.translator.done
├── 260319.tts.done
├── 260319.engine.done
├── 260319.uploader.done
└── 260319.archiver.done
```

### 진행 로직 (수도코드)

```python
async def main():
    yymmdd = parse_yymmdd(sys.argv[1])  # "260319"

    # 1. 수집 (scraper)
    if not exists_done(yymmdd, "scraper"):
        scrape_and_save(...)
        create_done(yymmdd, "scraper")

    # 2. 번역 (translator)
    if not exists_done(yymmdd, "translator"):
        assert_exists_done(yymmdd, "scraper")
        translate_and_save(...)
        create_done(yymmdd, "translator")

    # 3. TTS
    if not exists_done(yymmdd, "tts"):
        assert_exists_done(yymmdd, "translator")
        await yaml_to_tts(...)
        create_done(yymmdd, "tts")

    # 4. 영상 합성 (engine)
    if not exists_done(yymmdd, "engine"):
        assert_exists_done(yymmdd, "tts")
        synthesize_video(...)
        create_done(yymmdd, "engine")

    # 5. 업로드 (uploader)
    # 6. 아카이빙 (archiver)
```

### 선행 단계 누락 처리

선행 단계의 `.done` 파일이 없으면 **처음부터 다시 실행**합니다:

```python
def assert_exists_done(yymmdd: str, required_module: str) -> None:
    """선행 단계 완료 필수 확인"""
    if not exists_done(yymmdd, required_module):
        raise PipelineRestartError(
            f"선행 단계({required_module})가 완료되지 않았습니다. "
            f"다음 명령어로 초기화 후 처음부터 실행하세요:\n"
            f"  rm data/{yymmdd}.* && rm data/{yymmdd}.*.done"
        )
```

**설계 원칙**: 중간 산출물이 불일치할 가능성을 방지하기 위해, 모든 파일을 삭제하고 초기화하는 것이 안전합니다.

---

## 4. 수정 필요 모듈

### 핵심 모듈

| 모듈 | 수정 내용 | 영향도 |
|:---|:---|:---|
| **main.py** | 타임스탬프 파싱(기본값 현재 시각 YYMMDD), 건너뛰기 로직 추가 | 🔴 높음 |
| **today_vn_news/timestamp.py** | 신규 생성 (유틸리티 함수) | 🔴 높음 |
| **video_source/resolver.py** | `base_name[:6]` → `base_name` 로직 수정 (YYMMDD 추출) | 🔴 높음 |
| **engine.py** | `synthesize_video(base_name)` 인자 YYMMDD 사용 확인 | 🟡 낮음 |
| **translator.py** | YAML 파일명 처리 확인 | 🟡 낮음 |
| **tts/__init__.py** | MP3 파일명 처리 확인 | 🟡 낮음 |
| **video_source/archiver.py** | Media 파일명 매핑 로직 검증 | 🟡 낮음 |
| **notifications/pipeline_status.py** | 단계명 상수 업데이트 | 🟢 낮음 |

### 신규 유틸리티 모듈

```python
# today_vn_news/timestamp.py
import re
from pathlib import Path

def normalize_timestamp(arg: str) -> str:
    """명령줄 인자를 YYMMDD 형식으로 정규화

    Examples:
        "260319" → "260319"
        "20260319" → "260319"
        "20260319_1955" → "260319"
    """
    digits = re.sub(r"\D", "", arg)
    return digits[:6]

def exists_done(yymmdd: str, module: str) -> bool:
    """완료 파일 존재 여부 확인"""
    return Path(f"data/{yymmdd}.{module}.done").exists()

def create_done(yymmdd: str, module: str) -> None:
    """완료 파일 생성"""
    Path(f"data/{yymmdd}.{module}.done").touch()

def assert_exists_done(yymmdd: str, required_module: str) -> None:
    """선행 단계 완료 필수 확인"""
    if not exists_done(yymmdd, required_module):
        raise PipelineRestartError(
            f"선행 단계({required_module})가 완료되지 않았습니다. "
            f"rm data/{yymmdd}.* && rm data/{yymmdd}.*.done 후 처음부터 실행하세요."
        )
```

---

## 5. 에러 핸들링

### 타임스탬프 검증

```python
def validate_yymmdd(timestamp: str) -> bool:
    """YYMMDD 형식 검증"""
    if not re.match(r"^\d{6}$", timestamp):
        raise ValueError("잘못된 형식입니다. YYMMDD 6자리 숫자로 입력해주세요.")

    try:
        datetime.strptime(timestamp, "%y%m%d")
    except ValueError:
        raise ValueError("유효하지 않은 날짜입니다.")
```

### 커스텀 예외 정의

```python
# today_vn_news/exceptions.py (기존 파일에 추가)
class PipelineRestartError(TodayVnNewsError):
    """파이프라인 재시작 필요 예외"""
    pass
```

---

## 6. 테스트 전략

### 단위 테스트

```python
# tests/unit/test_timestamp.py
def test_normalize_timestamp():
    assert normalize_timestamp("260319") == "260319"
    assert normalize_timestamp("20260319") == "260319"
    assert normalize_timestamp("20260319_1955") == "260319"

def test_done_files():
    yymmdd = "260319"

    # 생성
    create_done(yymmdd, "scraper")
    assert exists_done(yymmdd, "scraper")

    # 삭제
    Path(f"data/{yymmdd}.scraper.done").unlink()
    assert not exists_done(yymmdd, "scraper")

def test_prerequisite_check():
    yymmdd = "260319"
    create_done(yymmdd, "scraper")

    # 통과 (선행 존재)
    assert_exists_done(yymmdd, "scraper")

    # 실패 (선행 누락)
    with pytest.raises(PipelineRestartError):
        assert_exists_done(yymmdd, "translator")
```

### 통합 테스트 시나리오

```python
# tests/integration/test_pipeline_skip.py
async def test_skip_completed_steps():
    """완료된 단계 건너뛰기 확인"""
    yymmdd = "260319"

    # 1. 선행 단계 완료 가정
    create_done(yymmdd, "scraper")
    create_done(yymmdd, "translator")

    # 2. 재실행 시 scraper, translator 건너뛰고 TTS부터 시작
    # mock 호출 횟수 검증
    assert scrape_mock.call_count == 0
    assert translate_mock.call_count == 0
    assert tts_mock.call_count == 1

async def test_missing_prerequisite():
    """선행 단계 누락 시 예외 발생 확인"""
    yymmdd = "260319"

    # scraper.done만 존재, translator.done 누락 상태에서 시작
    create_done(yymmdd, "scraper")

    with pytest.raises(PipelineRestartError):
        await main_pipeline(yymmdd)
```

---

## 7. 롤백 계획

### Phase 1: 핵심 기능 구현
1. `today_vn_news/timestamp.py` 모듈 생성
2. `main.py`에 건너뛰기 로직 적용
3. 단계명 상수 리네임 (scraper, translator, tts, engine, uploader, archiver)
4. 단위 테스트 작성

### Phase 2: 연동 모듈 확인
1. `video_source/resolver.py` 동작 확인 (YYMMDD 추출)
2. `engine.py`, `translator.py`, `tts/__init__.py` 파일명 처리 확인

### Phase 3: 통합 테스트
1. 전체 파이프라인 실행 테스트
2. 중단 후 재개 테스트
3. 선행 누락 시나리오 테스트

### Phase 4: 문서 업데이트
1. README.md 파일명 형식 업데이트
2. 사용법 안내 업데이트

---

## 8. 명령줄 사용법 변경

### 변경 전
```bash
python main.py 20260319_1955
python main.py                    # 현재 시각 (YYYYMMDD_HHMM)
```

### 변경 후
```bash
python main.py 260319
python main.py                    # 오늘 날짜 (YYMMDD)
```

### main.py 수정 필요 (명령줄 인자 없을 때 기본값)

```python
# 변경 전 (main.py ~179행)
yymmdd_hhmm = datetime.datetime.now().strftime("%Y%m%d_%H%M")

# 변경 후
yymmdd = datetime.datetime.now().strftime("%y%m%d")
```

---

## 9. 영향 받는 설정 파일 및 모듈

### video_source/archiver.py 검증 필요

`archiver.py`에서 Media 저장 시 파일명 매핑 로직을 확인해야 합니다:

**Media 경로**: `Media/{YYMM}/{DD}_{hhmm}.mp4`
**파이프라인 산출물**: `data/{YYMMDD}_final.mp4`

**질문**: `archiver.py`에서 `260319_final.mp4`를 어떤 Media 경로로 저장하는지 확인 필요합니다.

### config.yaml

Media 파일명 형식(`{YYMM}/{DD}_{hhmm}.mp4`)은 변경하지 않고 유지됩니다.

### video_source/resolver.py 확인

이미 `base_name[:6]`으로 YYMMDD를 추출하는 로직이 존재하므로 수정 불필요:

```python
# resolver.py 기존 코드 (유지)
yymmdd = base_name[:6]  # YYMMDDHHMM에서 앞 6자
media_source = Path(self.config.media_mount_path) / f"{yymmdd}.mp4"
```

### video_source/resolver.py 수정

파일명이 `YYMMDD` 6자리로 변경되므로, resolver.py의 YYMMDD 추출 로직도 수정해야 합니다:

**수정 전:**
```python
# resolver.py 기존 코드
yymmdd = base_name[:6]  # YYMMDDHHMM에서 앞 6자
```

**수정 후:**
```python
# resolver.py 수정 코드
yymmdd = base_name  # 이미 YYMMDD 형식 (6자리)
```

### config.yaml

현재 Media 파일명 형식이 `{YYMM}/{DD}_{hhmm}.mp4`로 설정되어 있으므로 확인 필요:

```yaml
# config.yaml
video:
  media_mount_path: "/media/video"
  format: "{YYMM}/{DD}_{hhmm}.mp4"  # 이 형식은 유지
```

**주의**: Media에 저장된 파일명 형식(`{YYMM}/{DD}_{hhmm}.mp4`)은 본 변경사항과 무관하게 유지됩니다.

---

## 10. 하루 여러 번 실행 정책 (중요)

### 제약사항: 하루에 한 번만 실행

**가정**: 하루에 오직 한 번만 실행합니다.

### 동작

같은 날짜(`260319`)로 여러 번 실행 시:

1. **기존 파일 덮어쓰기**: `260319.yaml`, `260319.mp3` 등 기존 파일 덮어씀움
2. **완료 파일 갱신**: `260319.scraper.done` 등 타임스탬프 갱신

**결과**: 가장 최신 실행 결과만 보존됨, 이전 실행 결과는 손실

### 주의사항

하루에 여러 번 실행할 필요성이 있다면(예: 오전 수정, 오후 재실행), 이는 **별도의 기능**으로 설계되어야 합니다. 현재 요구사항에는 포함되지 않습니다.

---

## 11. 기존 파일 마이그레이션 (선택 사항, 주의 필요)

기존 `20260323_1300_*` 파일들을 `260323_*`로 변환하는 스크립트:

```bash
#!/bin/bash
# migration.sh - 사용 전 data/ 디렉토리 백업 필수!

cd data || exit 1

for file in 20*_raw.yaml 20*.yaml 20*.mp3 20*_final.mp4; do
    # 20260319_1955_raw.yaml → 260319_raw.yaml
    if [[ $file =~ ^20[0-9]{2}([0-9]{2})([0-9]{2})_[0-9]{4} ]]; then
        new_name="${BASH_REMATCH[1]}${BASH_REMATCH[2]}${BASH_REMATCH[3]}_${BASH_REMATCH[4]}_${BASH_REMATCH[5]}"
        new_name="${new_name:2:8}"  # 앞 2자리(20) 제외 → 260319_1955
        new_name_yymmdd=$(echo "$new_name" | cut -d'_' -f1 | sed 's/^20//')  # 260319_1955 → 260319

        # raw.yaml → yymmdd_raw.yaml
        if [[ $new_name_yymmdd =~ ^(.*)_raw\.yaml$ ]]; then
            base="${BASH_REMATCH[1]}"
            mv "$file" "${base}_raw.yaml"
        elif [[ $new_name_yymmdd =~ ^(.*)\.yaml$ ]]; then
            base="${BASH_REMATCH[1]}"
            mv "$file" "${base}.yaml"
        elif [[ $new_name_yymmdd =~ ^(.*)_final\.mp4$ ]]; then
            base="${BASH_REMATCH[1]}"
            mv "$file" "${base}_final.mp4"
        elif [[ $new_name_yymmdd =~ ^(.*)\.mp3$ ]]; then
            base="${BASH_REMATCH[1]}"
            mv "$file" "${base}.mp3"
        fi
    fi
done
```

**주의사항**:
- 이 스크립트는 **data/ 디렉토리 내부**에서 실행한다고 가정합니다.
- **반드시 백업 후 실행**: `cp -r data data_backup`
- 같은 날짜의 다른 시간대 파일(`20260319_1200_*`, `20260319_1955_*`)가 있을 경우 나중에 처리된 파일이 먼저 덮어씌워집니다.
- 사용자 책임 하에 실행 필요합니다.

---

## 부록 A: 파일명 형식 변경 이유

### 현재 문제점
- `20260319_1955`, `20260323_1300` 등 같은 날짜에 시간대별로 파일이 중복 생성
- 디스크 공간 낭비
- 파일명 불필요하게 긺음

### 개선 효과
- 파일명 단순화 (`260319`)
- 하루에 한 번 실행한다는 가정하면 중복 생성 방지
- 직관적인 파일명

---

## 부록 B: 완료 파일 설계

### 왜 `.done` 파일인가?

1. **단순함**: 파일 시스템만으로 상태 추적 (DB 없음)
2. **신뢰성**: 각 단계 완료를 명확히 보장
3. **복원력**: 중단 후 재실행 시 완료된 단계 자동 건너뜀
4. **투명성**: `ls data/`로 완료 상태 한눈에 파악 가능

### 대안과 비교

| 방식 | 장점 | 단점 |
|:---|:---|:---|
| `.done` 파일 | 단순, 직관적 | 파일 시스템 의존 |
| 상태 JSON | 중앙화된 상태 관리 | 복잡도 증가, 경합 위험 |
| 상태 파일 | 단순함 | 로킹/동시성 문제 |

---

**문서 종료**
