# 영상 소스 우선순위 시스템 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Media 마운트된 공유 저장소의 영상을 우선 사용하고, 최종 산출물을 Media/{{YYMM}}/{{DD}}_{{hhmm}}.mp4 형식으로 저장하는 시스템 구현

**Architecture:** VideoSourceResolver(우선순위 체인) → engine.py(합성) → MediaArchiver(저장) → uploader.py(업로드)

**Tech Stack:** Python 3.10+, PyYAML, shutil, pathlib, pytest

---

## File Structure Map

### 신규 파일
- `today_vn_news/config/__init__.py` - 설정 패키지 초기화
- `today_vn_news/config/video_config.py` - YAML 설정 로딩 (dataclass)
- `today_vn_news/video_source/__init__.py` - video_source 패키지 초기화
- `today_vn_news/video_source/resolver.py` - 우선순위 체인 로직
- `today_vn_news/video_source/archiver.py` - Media 저장 로직
- `config.yaml` - 설정 파일 (기본값 포함)
- `tests/unit/test_video_config.py` - 설정 로딩 테스트
- `tests/unit/test_video_source_resolver.py` - resolver 테스트
- `tests/unit/test_media_archiver.py` - archiver 테스트
- `tests/fixtures/media/260322.mp4` - 모의 Media 소스
- `tests/fixtures/media/latest.mp4` - 모의 Media 최신 소스
- `tests/fixtures/config.yaml` - 테스트용 설정

### 수정 파일
- `today_vn_news/exceptions.py` - MediaMountError, MediaCopyError, MediaArchiveError 추가
- `today_vn_news/engine.py` - `source_path` 파라미터 추가
- `today_vn_news/__init__.py` - 모듈 export 추가
- `tests/unit/test_engine.py` - resolver 통합 테스트

---

## Task 1: 예외 타입 추가

**Files:**
- Modify: `today_vn_news/exceptions.py:102-103`

### 목적
Media 관련 새로운 예외 타입 3개 추가

### 구현

```python
# exceptions.py 끝에 추가 (line 103 이후)

class MediaMountError(TodayVnNewsError):
    """
    Media 마운트 실패 예외.

    지정된 Media 경로가 존재하지 않거나 접근 불가능할 때 발생.
    """
    pass


class MediaCopyError(TodayVnNewsError):
    """
    Media 파일 복사 실패 예외.

    Media에서 로컬로 소스 영상 복사 실패 시 발생.
    """
    pass


class MediaArchiveError(TodayVnNewsError):
    """
    Media 저장 실패 예외.

    최종 영상을 Media로 이동/저장 실패 시 발생.
    """
    pass


class VideoSourceError(TodayVnNewsError):
    """
    영상 소스 탐색 실패 예외.

    모든 우선순위 체인에서 소스를 찾을 수 없을 때 발생.
    """
    pass
```

### 테스트

- [ ] **Step 1: 예외 타입 import 테스트 작성**

```python
# tests/unit/test_exceptions.py
def test_media_exceptions_exist():
    from today_vn_news.exceptions import (
        MediaMountError,
        MediaCopyError,
        MediaArchiveError,
        VideoSourceError
    )

    # 각 예외가 인스턴스 가능한지 확인
    err1 = MediaMountError("test")
    err2 = MediaCopyError("test")
    err3 = MediaArchiveError("test")
    err4 = VideoSourceError("test")

    assert isinstance(err1, TodayVnNewsError)
    assert isinstance(err2, TodayVnNewsError)
    assert isinstance(err3, TodayVnNewsError)
    assert isinstance(err4, TodayVnNewsError)
```

- [ ] **Step 2: 테스트 실행**

```bash
uv run pytest tests/unit/test_exceptions.py::test_media_exceptions_exist -v
```

Expected: PASS

- [ ] **Step 3: 커밋**

```bash
git add today_vn_news/exceptions.py tests/unit/test_exceptions.py
git commit -m "feat(exceptions): Media 관련 예외 타입 4개 추가

- MediaMountError: Media 마운트 실패
- MediaCopyError: Media 파일 복사 실패
- MediaArchiveError: Media 저장 실패
- VideoSourceError: 영상 소스 탐색 실패

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 2: VideoConfig dataclass 구현

**Files:**
- Create: `today_vn_news/config/__init__.py`
- Create: `today_vn_news/config/video_config.py`
- Create: `config.yaml`

### 목적
YAML 설정 파일을 로드하고 기본값을 제공하는 dataclass 구현

### 구현

- [ ] **Step 1: config 패키지 __init__.py 작성**

```python
# today_vn_news/config/__init__.py
from .video_config import VideoConfig

__all__ = ["VideoConfig"]
```

- [ ] **Step 2: video_config.py 작성**

```python
# today_vn_news/config/video_config.py
import os
from dataclasses import dataclass
from pathlib import Path
import yaml
from today_vn_news.logger import logger
from today_vn_news.exceptions import TodayVnNewsError


@dataclass
class VideoConfig:
    """영상 소스 설정"""

    # Media 설정
    media_mount_path: str = "/Volumes/Media"
    media_date_format: str = "YYMMDD"
    auto_copy_latest: bool = True

    # 저장 설정
    archive_format: str = "{YYMM}/{DD}_{hhmm}.mp4"

    # Fallback
    local_data_dir: str = "data"
    default_image: str = "assets/default_bg.png"

    @classmethod
    def from_yaml(cls, path: str = "config.yaml") -> "VideoConfig":
        """
        YAML 설정 로딩

        Args:
            path: 설정 파일 경로

        Returns:
            VideoConfig: 로드된 설정 (파일 없으면 기본값)

        Raises:
            YAMLError: YAML 파싱 실패 (파일 있지만 잘못됨)
        """
        config_path = Path(path)

        if not config_path.exists():
            logger.warning(f"설정 파일 없음 ({path}), 기본값 사용")
            return cls()

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            video_config = data.get("video", {})
            return cls(
                media_mount_path=video_config.get("media", {}).get("mount_path", "/Volumes/Media"),
                media_date_format=video_config.get("media", {}).get("date_format", "YYMMDD"),
                auto_copy_latest=video_config.get("media", {}).get("auto_copy_latest", True),
                archive_format=video_config.get("archive", {}).get("format", "{YYMM}/{DD}_{hhmm}.mp4"),
                local_data_dir=video_config.get("fallback", {}).get("local_data_dir", "data"),
                default_image=video_config.get("fallback", {}).get("default_image", "assets/default_bg.png")
            )
        except yaml.YAMLError as e:
            logger.error(f"YAML 파싱 실패: {e}")
            raise TodayVnNewsError(f"설정 파일 파싱 실패: {e}")
```

- [ ] **Step 3: config.yaml 작성**

```yaml
# config.yaml
video:
  media:
    mount_path: "/Volumes/Media"
    date_format: "YYMMDD"
    auto_copy_latest: true
  archive:
    format: "{YYMM}/{DD}_{hhmm}.mp4"
  fallback:
    local_data_dir: "data"
    default_image: "assets/default_bg.png"
```

- [ ] **Step 4: 의존성 확인**

```bash
uv add pyyaml
```

Expected: pyyaml가 requirements에 추가됨

### 테스트

- [ ] **Step 5: 설정 기본값 테스트 작성**

```python
# tests/unit/test_video_config.py
import pytest
from today_vn_news.config import VideoConfig

def test_default_values():
    config = VideoConfig()

    assert config.media_mount_path == "/Volumes/Media"
    assert config.media_date_format == "YYMMDD"
    assert config.auto_copy_latest is True
    assert config.archive_format == "{YYMM}/{DD}_{hhmm}.mp4"
    assert config.local_data_dir == "data"
    assert config.default_image == "assets/default_bg.png"
```

- [ ] **Step 6: config.yaml 로드 테스트 작성**

```python
def test_from_yaml_missing_file():
    config = VideoConfig.from_yaml("nonexistent.yaml")

    # 파일 없으면 기본값 반환
    assert config.media_mount_path == "/Volumes/Media"

def test_from_yaml_valid_settings(tmp_path):
    import yaml

    config_content = {
        "video": {
            "media": {
                "mount_path": "/tmp/test_media",
                "date_format": "YYMMDD",
                "auto_copy_latest": False
            },
            "archive": {
                "format": "test/{YYMM}/{DD}_{hhmm}.mp4"
            }
        }
    }

    config_file = tmp_path / "test_config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_content, f)

    config = VideoConfig.from_yaml(str(config_file))

    assert config.media_mount_path == "/tmp/test_media"
    assert config.auto_copy_latest is False
    assert config.archive_format == "test/{YYMM}/{DD}_{hhmm}.mp4"
```

- [ ] **Step 7: 테스트 실행**

```bash
uv run pytest tests/unit/test_video_config.py -v
```

Expected: 모든 테스트 PASS

- [ ] **Step 8: 커밋**

```bash
git add today_vn_news/config/ config.yaml tests/unit/test_video_config.py pyproject.toml
git commit -m "feat(config): VideoConfig dataclass 및 YAML 설정 로딩 구현

- VideoConfig dataclass: Media/archive/fallback 설정
- config.yaml: 기본 설정 파일 추가
- YAML 설정 로딩: from_yaml() 메서드
- 기본값 fallback: 파일 없을 때 경고 후 기본값 사용
- pyyaml 의존성 추가

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 2.5: 테스트 Fixtures 준비

**Files:**
- Create: `tests/fixtures/media/260322.mp4`
- Create: `tests/fixtures/media/latest.mp4`
- Create: `tests/fixtures/config.yaml`
- Create: `tests/fixtures/default_bg.png`

### 목적
테스트에서 사용할 모의 Media 소스 파일 및 설정 파일 생성

### 구현

- [ ] **Step 1: fixtures 디렉토리 생성**

```bash
mkdir -p tests/fixtures/media
```

- [ ] **Step 2: 모의 MP4 파일 생성**

```bash
# 빈 MP4 파일 생성 (FFmpeg 사용)
ffmpeg -f lavfi -i testsrc=duration=1:size=320x240:rate=1 \
  -vf "format=yuv420p" tests/fixtures/media/260322.mp4 -y

ffmpeg -f lavfi -i testsrc=duration=1:size=320x240:rate=1 \
  -vf "format=yuv420p" tests/fixtures/media/latest.mp4 -y
```

Expected: 두 개의 1초짜리 MP4 파일 생성

- [ ] **Step 3: 기본 이미지 생성**

```bash
# 1x1 픽셀 흰색 PNG 이미지 생성
convert -size 1x1 xc:white tests/fixtures/default_bg.png
```

Alternative (ImageMagick 없이):
```python
# Python으로 간단한 PNG 생성
from PIL import Image
img = Image.new('RGB', (1, 1), color='white')
img.save('tests/fixtures/default_bg.png')
```

- [ ] **Step 4: 테스트용 config.yaml 작성**

```yaml
# tests/fixtures/config.yaml
video:
  media:
    mount_path: "./tests/fixtures/media"
    date_format: "YYMMDD"
    auto_copy_latest: true
  archive:
    format: "{YYMM}/{DD}_{hhmm}.mp4"
  fallback:
    local_data_dir: "tests/fixtures/data"
    default_image: "tests/fixtures/default_bg.png"
```

- [ ] **Step 5: 커밋**

```bash
git add tests/fixtures/
git commit -m "test: 테스트 Fixtures 추가

- tests/fixtures/media/260322.mp4: YYMMDD 형식 소스
- tests/fixtures/media/latest.mp4: 최신 소스
- tests/fixtures/config.yaml: 테스트용 설정
- tests/fixtures/default_bg.png: 기본 이미지

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 3: VideoSourceResolver 구현

**Files:**
- Create: `today_vn_news/video_source/__init__.py`
- Create: `today_vn_news/video_source/resolver.py`
- Modify: `today_vn_news/__init__.py`

### 목적
Media → Local → DefaultImage 우선순위 체인으로 소스 영상 선택

### 구현

- [ ] **Step 1: video_source 패키지 __init__.py 작성**

```python
# today_vn_news/video_source/__init__.py
from .resolver import VideoSourceResolver

__all__ = ["VideoSourceResolver"]
```

- [ ] **Step 2: resolver.py 기본 구조 작성**

```python
# today_vn_news/video_source/resolver.py
import os
import shutil
from pathlib import Path
from today_vn_news.logger import logger
from today_vn_news.config import VideoConfig
from today_vn_news.exceptions import MediaMountError, MediaCopyError, VideoSourceError


class VideoSourceResolver:
    """영상 소스 우선순위 체인 관리"""

    def __init__(self, config: VideoConfig):
        self.config = config
        self.temp_copies: list[Path] = []  # 정리할 임시 파일 추적

    def resolve(self, base_name: str) -> tuple[Path, bool]:
        """
        우선순위에 따라 영상 소스 반환

        Args:
            base_name: YYMMDD_HHMM (예: 260322_1230)

        Returns:
            (source_path, is_temporary_copy)
            - source_path: 사용할 영상 경로 (로컬 data/ 기준)
            - is_temporary_copy: Media에서 복사한 임시 파일인지 여부

        Raises:
            VideoSourceError: 모든 소스 실패 시
        """
        # base_name에서 YYMMDD 추출 (Media/{{YYMMDD}}.mp4용)
        yymmdd = base_name[:6]  # YYMMDDHHMM에서 앞 6자

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
        """
        Media에서 로컬 data/로 임시 복사

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
        import time
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
```

- [ ] **Step 3: __init__.py 수정**

```python
# today_vn_news/__init__.py에 추가
from .video_source.resolver import VideoSourceResolver
```

### 테스트

- [ ] **Step 4: resolver 우선순위 테스트 작성**

```python
# tests/unit/test_video_source_resolver.py
import pytest
from pathlib import Path
from today_vn_news.video_source.resolver import VideoSourceResolver
from today_vn_news.config import VideoConfig
from today_vn_news.exceptions import MediaMountError, MediaCopyError
import shutil

def test_resolve_media_yymmdd_exists(tmp_path):
    """Media/{{YYMMDD}}.mp4 존재 시 우선 반환"""
    # Media 폴더 및 파일 생성
    media_dir = tmp_path / "Media"
    media_dir.mkdir()
    (media_dir / "260322.mp4").touch()

    # data 폴더 생성
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # 설정
    config = VideoConfig(media_mount_path=str(media_dir))
    resolver = VideoSourceResolver(config)

    # 실행
    source_path, is_temp = resolver.resolve("260322_1230")

    # 검증
    assert is_temp is True
    assert "260322_1230" in str(source_path) or "temp_" in str(source_path)

    # 정리
    resolver.cleanup_temporary()

def test_resolve_media_latest_fallback(tmp_path):
    """Media/{{YYMMDD}}.mp4 없을 때 latest.mp4 반환"""
    media_dir = tmp_path / "Media"
    media_dir.mkdir()
    (media_dir / "latest.mp4").touch()

    data_dir = tmp_path / "data"
    data_dir.mkdir()

    config = VideoConfig(media_mount_path=str(media_dir))
    resolver = VideoSourceResolver(config)

    source_path, is_temp = resolver.resolve("260322_1230")

    assert is_temp is True
    assert "latest" in str(source_path) or "temp_" in str(source_path)

    resolver.cleanup_temporary()

def test_resolve_local_fallback(tmp_path):
    """Media 모두 없을 때 로컬 .mov/mp4 반환"""
    media_dir = tmp_path / "Media"
    media_dir.mkdir()  # 비어있음

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "260322_1230.mov").touch()

    config = VideoConfig(media_mount_path=str(media_dir))
    resolver = VideoSourceResolver(config)

    source_path, is_temp = resolver.resolve("260322_1230")

    assert is_temp is False
    assert "260322_1230.mov" == source_path.name

def test_resolve_default_image_fallback(tmp_path):
    """모든 소스 없을 때 기본 이미지 반환"""
    media_dir = tmp_path / "Media"
    media_dir.mkdir()

    data_dir = tmp_path / "data"
    data_dir.mkdir()

    default_dir = tmp_path / "assets"
    default_dir.mkdir()
    (default_dir / "default_bg.png").touch()

    config = VideoConfig(
        media_mount_path=str(media_dir),
        default_image=str(default_dir / "default_bg.png")
    )
    resolver = VideoSourceResolver(config)

    source_path, is_temp = resolver.resolve("260322_1230")

    assert is_temp is False
    assert "default_bg.png" == source_path.name
```

- [ ] **Step 5: cleanup 테스트 작성**

```python
def test_temporary_copy_and_cleanup(tmp_path):
    """Media 소스 복사 후 정리 확인"""
    media_dir = tmp_path / "Media"
    media_dir.mkdir()
    (media_dir / "260322.mp4").touch()

    data_dir = tmp_path / "data"
    data_dir.mkdir()

    config = VideoConfig(media_mount_path=str(media_dir))
    resolver = VideoSourceResolver(config)

    # 복사
    source_path, is_temp = resolver.resolve("260322_1230")
    assert is_temp is True
    assert source_path.exists()

    # 정리
    resolver.cleanup_temporary()
    assert not source_path.exists()
```

- [ ] **Step 6: 테스트 실행**

```bash
uv run pytest tests/unit/test_video_source_resolver.py -v
```

Expected: 모든 테스트 PASS

- [ ] **Step 7: 커밋**

```bash
git add today_vn_news/video_source/ today_vn_news/__init__.py tests/unit/test_video_source_resolver.py
git commit -m "feat(video_source): VideoSourceResolver 우선순위 체인 구현

- VideoSourceResolver: Media → Local → DefaultImage 우선순위
- Media에서 로컬로 임시 복사 후 cleanup
- base_name (YYMMDD_HHMM) 형식 파싱
- MediaMountError, MediaCopyError 예외 활용
- 단위 테스트: 우선순위, fallback, cleanup

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 4: MediaArchiver 구현

**Files:**
- Create: `today_vn_news/video_source/archiver.py`
- Modify: `today_vn_news/video_source/__init__.py`

### 목적
최종 영상을 Media/{{YYMM}}/{{DD}}_{{hhmm}}.mp4 형식으로 복사

### 구현

- [ ] **Step 1: archiver.py 작성**

```python
# today_vn_news/video_source/archiver.py
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
        dd = base_name[6:8]    # DD
        hhmm = base_name[9:13]  # HHMM (_ 제외)
        yymm = yymmdd[:4]      # YYMM

        # 대상 경로: Media/{{YYMM}}/{{DD}}_{{hhmm}}.mp4
        media_base = Path(self.config.media_mount_path)
        archive_dir = media_base / yymm
        archive_name = f"{dd}_{hhmm}.mp4"
        media_path = archive_dir / archive_name

        try:
            # 폴더 생성
            archive_dir.mkdir(parents=True, exist_ok=True)

            # 복사 (shutil.copy로 원본 보존)
            shutil.copy2(local_final, media_path)
            logger.info(f"Media 저장 완료: {media_path}")
            return media_path

        except FileNotFoundError:
            raise MediaArchiveError(f"Media 경로 없음 또는 접근 불가: {media_base}")
        except OSError as e:
            raise MediaArchiveError(f"Media 복사 실패: {e}")
```

- [ ] **Step 2: __init__.py 수정**

```python
# today_vn_news/video_source/__init__.py에 추가
from .archiver import MediaArchiver
```

### 테스트

- [ ] **Step 3: archiver 테스트 작성**

```python
# tests/unit/test_media_archiver.py
import pytest
from pathlib import Path
from today_vn_news.video_source.archiver import MediaArchiver
from today_vn_news.config import VideoConfig
from today_vn_news.exceptions import MediaArchiveError

def test_archive_creates_directory(tmp_path):
    """Media/{{YYMM}}/ 폴더 자동 생성 확인"""
    media_dir = tmp_path / "Media"
    media_dir.mkdir()

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "260322_1230_final.mp4").touch()

    config = VideoConfig(media_mount_path=str(media_dir))
    archiver = MediaArchiver(config)

    media_path = archiver.archive(str(data_dir / "260322_1230_final.mp4"), "260322_1230")

    # 검증: 폴더 생성
    assert media_path.parent.exists()
    assert media_path.parent.name == "2603"
    assert media_path.name == "22_1230.mp4"
    assert media_path.exists()

def test_archive_correct_naming(tmp_path):
    """파일명 {{YYMM}}/{{DD}}_{{hhmm}}.mp4 형식 확인"""
    media_dir = tmp_path / "Media"
    media_dir.mkdir()

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "260322_1230_final.mp4").touch()

    config = VideoConfig(media_mount_path=str(media_dir))
    archiver = MediaArchiver(config)

    media_path = archiver.archive(str(data_dir / "260322_1230_final.mp4"), "260322_1230")

    # 전체 경로 검증
    assert "2603/22_1230.mp4" in str(media_path)
    assert media_path.name == "22_1230.mp4"

def test_archive_overwrites_existing(tmp_path):
    """동일 파일명 존재 시 덮어쓰기 확인"""
    media_dir = tmp_path / "Media"
    media_dir.mkdir()

    # YYMM 폴더 및 기존 파일 생성
    archive_dir = media_dir / "2603"
    archive_dir.mkdir()
    old_file = archive_dir / "22_1230.mp4"
    old_file.write_text("old content")
    old_size = old_file.stat().st_size

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    new_file = data_dir / "260322_1230_final.mp4"
    new_file.write_text("new content")

    config = VideoConfig(media_mount_path=str(media_dir))
    archiver = MediaArchiver(config)

    media_path = archiver.archive(str(new_file), "260322_1230")

    # 덮어쓰기 확인
    assert media_path.read_text() == "new content"
    assert media_path.stat().st_size != old_size

def test_archive_media_mount_failure(tmp_path):
    """Media 마운트 실패 시 예외 발생 확인"""
    # 존재하지 않는 경로 지정
    config = VideoConfig(media_mount_path="/nonexistent/media")
    archiver = MediaArchiver(config)

    with pytest.raises(MediaArchiveError):
        archiver.archive("/fake/path/final.mp4", "260322_1230")
```

- [ ] **Step 4: 테스트 실행**

```bash
uv run pytest tests/unit/test_media_archiver.py -v
```

Expected: 모든 테스트 PASS

- [ ] **Step 5: 커밋**

```bash
git add today_vn_news/video_source/archiver.py today_vn_news/video_source/__init__.py tests/unit/test_media_archiver.py
git commit -m "feat(video_source): MediaArchiver 구현

- MediaArchiver: 최종 영상을 Media로 복사/저장
- Media/{{YYMM}}/{{DD}}_{{hhmm}}.mp4 형식
- 폴더 자동 생성, shutil.copy (원본 보존)
- MediaArchiveError 예외 처리
- 단위 테스트: 폴더 생성, 파일명, 덮어쓰기, 실패 시나리오

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 5: engine.py 수정 (source_path 파라미터)

**Files:**
- Modify: `today_vn_news/engine.py:39-50`

### 목적
`synthesize_video` 함수에 `source_path` 파라미터 추가하여 VideoSourceResolver 연동

### 구현

- [ ] **Step 1: engine.py 함수 시그니처 수정**

```python
# today_vn_news/engine.py line 39 수정
def synthesize_video(base_name: str, data_dir: str = "data", source_path: str = None):
    """
    영상과 음성을 합성하여 최종 MP4 생성

    Args:
        base_name: YYMMDD_HHMM (예: 260322_1230)
        data_dir: 데이터 디렉토리
        source_path: 소스 영상 경로 (None이면 기존 로직대로 .mov/.mp4 확인)

    Returns:
        True: 합성 성공

    Raises:
        VideoSynthesisError: 합성 실패
    """
```

- [ ] **Step 2: source_path 로직 추가**

```python
# today_vn_news/engine.py line 45-64 수정
    video_mov = os.path.join(data_dir, f"{base_name}.mov")
    video_mp4 = os.path.join(data_dir, f"{base_name}.mp4")

    # source_path가 지정되면 해당 파일을 video_in으로 사용
    if source_path is not None:
        video_in = source_path
        logger.info(f"지정 소스 영상 사용: {video_in}")
    else:
        # 기존 로직: .mov → .mp4 확인
        video_in = video_mov if os.path.exists(video_mov) else video_mp4

    # 기본 이미지 경로
    default_img = "assets/default_bg.png"
    using_image = False

    if not os.path.exists(video_in):
        if os.path.exists(default_img):
            logger.info(f"영상을 찾을 수 없어 기본 이미지({default_img})를 사용합니다.")
            video_in = default_img
            using_image = True
        else:
            logger.error(f"영상이나 기본 이미지({default_img})가 없습니다. 합성이 불가능합니다.")
            raise VideoSynthesisError(f"영상이나 기본 이미지({default_img})가 없습니다.")
```

### 테스트

- [ ] **Step 3: source_path 파라미터 테스트 작성**

```python
# tests/unit/test_engine.py에 추가
def test_synthesize_video_with_source_path(tmp_path):
    """source_path 파라미터로 소스 영상 지정"""
    from today_vn_news.engine import synthesize_video

    # 준비
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # YAML 파일 (TTS 입력)
    yaml_file = data_dir / "260322_1230.yaml"
    yaml_file.write_text("test: data")

    # TTS MP3
    mp3_file = data_dir / "260322_1230.mp3"
    mp3_file.write_bytes(b"MP3_DATA")

    # 소스 영상
    source_video = data_dir / "source.mp4"
    source_video.write_bytes(b"VIDEO_DATA")

    # 실행 (source_path 지정)
    result = synthesize_video("260322_1230", str(data_dir), source_path=str(source_video))

    # 검증: _final.mp4 생성
    final_video = data_dir / "260322_1230_final.mp4"
    assert result is True
    assert final_video.exists()

def test_synthesize_video_without_source_path(tmp_path):
    """source_path None이면 기존 로직대로 동작"""
    from today_vn_news.engine import synthesize_video

    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # .mov 파일 생성
    mov_file = data_dir / "260322_1230.mov"
    mov_file.write_bytes(b"MOV_DATA")

    # 실행 (source_path=None)
    result = synthesize_video("260322_1230", str(data_dir), source_path=None)

    # 검증
    assert result is True
```

- [ ] **Step 4: 테스트 실행**

```bash
uv run pytest tests/unit/test_engine.py::test_synthesize_video_with_source_path -v
uv run pytest tests/unit/test_engine.py::test_synthesize_video_without_source_path -v
```

Expected: 모든 테스트 PASS

- [ ] **Step 5: 커밋**

```bash
git add today_vn_news/engine.py tests/unit/test_engine.py
git commit -m "feat(engine): synthesize_video에 source_path 파라미터 추가

- source_path 파라미터 추가: 외부에서 소스 영상 지정 가능
- source_path=None이면 기존 로직 (.mov → .mp4 → default_bg.png)
- VideoSourceResolver 연동 준비
- 단위 테스트: source_path 있음/없음 각각 테스트

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 6: main.py 통합

**Files:**
- Modify: `today_vn_news/__init__.py`
- Modify: `main.py:108-200` (대략적인 라인 범위)

### 목적
main.py에 VideoSourceResolver와 MediaArchiver 통합, 전체 파이프라인 완성

### 구현

- [ ] **Step 1: main.py import 추가**

```python
# main.py 상단 import 섹션에 추가
from today_vn_news.video_source.resolver import VideoSourceResolver
from today_vn_news.video_source.archiver import MediaArchiver
from today_vn_news.config import VideoConfig
```

- [ ] **Step 2: main.py 메인 로직 수정**

```python
# main.py line 108-109 이후에 설정 로딩 추가
# 설정 로딩 (config.yaml 없으면 기본값 사용)
config = VideoConfig.from_yaml()

# ... TTS 엔진 설정 ...

# line 190-200 영상 합성 부분 수정
# 기존 코드:
# synthesize_video(yymmdd_hhmm, data_dir)

# 신규 코드:
try:
    # 소스 영상 해결
    resolver = VideoSourceResolver(config)
    source_path, is_temporary = resolver.resolve(yymmdd_hhmm)

    # 합성
    synthesize_video(yymmdd_hhmm, data_dir, source_path=str(source_path))

    # 저장 (데이터 보존 우선: 복사 후 업로드)
    local_final = f"{data_dir}/{yymmdd_hhmm}_final.mp4"

    if os.path.exists(local_final):
        archiver = MediaArchiver(config)
        try:
            media_path = archiver.archive(local_final, yymmdd_hhmm)
            logger.info(f"최종 영상 저장 완료: {media_path}")
        except Exception as e:
            logger.warning(f"Media 저장 실패 (로컬 유지): {e}")

        # 업로드 (기존 로직)
        success = upload_video(yymmdd_hhmm[:8], data_dir)

        # 업로드 성공 시 로컬 정리 (선택적)
        if success:
            try:
                os.remove(local_final)
                logger.info(f"로컬 임시 파일 삭제: {local_final}")
            except OSError:
                logger.warning(f"로컬 파일 삭제 실패 (무시): {local_final}")

finally:
    # 정리: Media 임시 복사본 삭제 (항상 실행)
    if is_temporary:
        resolver.cleanup_temporary()

except Exception as e:
    logger.error(f"파이프라인 실패: {e}")
    raise
```

### 테스트

- [ ] **Step 3: main.py 파이프라인 함수 분리**

```python
# main.py line 22 이후에 추가 (main() 함수 바로 앞)
def process_video_pipeline(yymmdd_hhmm: str, data_dir: str, config, tts_engine, tts_voice, tts_language, tts_instruct) -> bool:
    """
    영상 처리 파이프라인 (테스트 가능하도록 main()에서 분리)

    Args:
        yymmdd_hhmm: YYMMDD_HHMM 형식 타임스탬프
        data_dir: 데이터 디렉토리 경로
        config: VideoConfig 설정
        tts_engine: TTSEngine 엔진
        tts_voice: TTS 음성
        tts_language: TTS 언어
        tts_instruct: TTS 음성 스타일 설명

    Returns:
        bool: 파이프라인 성공 여부
    """
    import os
    from today_vn_news.video_source.resolver import VideoSourceResolver
    from today_vn_news.video_source.archiver import MediaArchiver
    from today_vn_news.uploader import upload_video
    from today_vn_news.logger import logger

    yaml_path = f"{data_dir}/{yymmdd_hhmm}.yaml"
    mp3_path = f"{data_dir}/{yymmdd_hhmm}.mp3"
    final_video = f"{data_dir}/{yymmdd_hhmm}_final.mp4"

    try:
        # 소스 영상 해결
        resolver = VideoSourceResolver(config)
        source_path, is_temporary = resolver.resolve(yymmdd_hhmm)

        # 합성
        synthesize_video(yymmdd_hhmm, data_dir, source_path=str(source_path))

        # 저장 (데이터 보존 우선: 복사 후 업로드)
        local_final = f"{data_dir}/{yymmdd_hhmm}_final.mp4"

        if os.path.exists(local_final):
            archiver = MediaArchiver(config)
            try:
                media_path = archiver.archive(local_final, yymmdd_hhmm)
                logger.info(f"최종 영상 저장 완료: {media_path}")
            except Exception as e:
                logger.warning(f"Media 저장 실패 (로컬 유지): {e}")

            # 업로드 (기존 로직)
            success = upload_video(yymmdd_hhmm[:8], data_dir)

            # 업로드 성공 시 로컬 정리 (선택적)
            if success:
                try:
                    os.remove(local_final)
                    logger.info(f"로컬 임시 파일 삭제: {local_final}")
                except OSError:
                    logger.warning(f"로컬 파일 삭제 실패 (무시): {local_final}")

            return success

    except Exception as e:
        logger.error(f"파이프라인 실패: {e}")
        return False

    finally:
        # 정리: Media 임시 복사본 삭제 (항상 실행)
        if is_temporary:
            resolver.cleanup_temporary()
```

- [ ] **Step 4: main() 함수 수정 (분리된 함수 호출)**

```python
# main.py line 182-200 수정 (기존 로직을 분리된 함수 호출로 변경)
    # 3. TTS 음성 변환 (항상 실행)
    print("\n[*] 3단계: TTS 음성 변환 시작...")
    await yaml_to_tts(yaml_path, engine=tts_engine, voice=tts_voice, language=tts_language, instruct=tts_instruct)

    # 4-5. 영상 합성 및 업로드 (분리된 함수 호출)
    print("\n[*] 4-5단계: 영상 처리 파이프라인 시작...")
    pipeline_success = process_video_pipeline(
        yymmdd_hhmm, data_dir, config, tts_engine, tts_voice, tts_language, tts_instruct
    )

    if pipeline_success:
        print("\n🎉 모든 파이프라인 작업이 성공적으로 완료되었습니다!")
    else:
        print("\n⚠️ 파이프라인 작업에서 문제가 발생했습니다.")
```

- [ ] **Step 5: 통합 테스트 작성**

```python
# tests/integration/test_video_pipeline.py
import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock
import sys

@pytest.mark.slow
def test_full_pipeline_with_media_source(tmp_path):
    """Media 소스 → 합성 → 저장 → 업로드 전체 흐름"""
    # Media 설정
    media_dir = tmp_path / "Media"
    media_dir.mkdir()

    # FFmpeg로 간단한 MP4 생성 (실제 테스트용)
    import subprocess
    subprocess.run([
        "ffmpeg", "-f", "lavfi", "-i", "testsrc=duration=1:size=320x240:rate=1",
        "-vf", "format=yuv420p", "-t", "1",
        str(media_dir / "260322.mp4"), "-y"
    ], check=True, capture_output=True)

    # Data 디렉토리
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # YAML 파일 (TTS 입력용)
    yaml_file = data_dir / "260322_1230.yaml"
    yaml_file.write_text("""
sections:
  - id: "1"
    name: "테스트"
    priority: "P0"
    items:
      - title: "테스트 뉴스"
        content: "테스트 내용"
        url: "https://example.com"
""")

    # config.yaml
    config_file = tmp_path / "config.yaml"
    config_file.write_text(f"""
video:
  media:
    mount_path: "{media_dir}"
    date_format: "YYMMDD"
    auto_copy_latest: true
  archive:
    format: "{{YYMM}}/{{DD}}_{{hhmm}}.mp4"
  fallback:
    local_data_dir: "{data_dir}"
    default_image: "assets/default_bg.png"
""")

    # main.py import
    from today_vn_news.main import process_video_pipeline
    from today_vn_news.config import VideoConfig
    from today_vn_news.tts import TTSEngine

    # 설정 로딩
    config = VideoConfig.from_yaml(str(config_file))

    # mock TTS (실제 API 호출 방지)
    with patch('today_vn_news.tts.yaml_to_tts', new_callable=AsyncMock()):
        # mock 업로드
        with patch('today_vn_news.uploader.upload_video', return_value=True):
            # 파이프라인 실행
            result = process_video_pipeline(
                "260322_1230",
                str(data_dir),
                config,
                TTSEngine.EDGE,
                "ko-KR-SunHiNeural",
                "korean",
                None
            )

    # 검증
    assert result is True

    # 1. Media에서 복사된 임시 소스 존재 확인
    temp_files = list(data_dir.glob("temp_*_260322.mp4"))
    assert len(temp_files) > 0, "임시 복사본이 생성되어야 함"

    # 2. 최종 영상이 Media/{{YYMM}}/{{DD}}_{{hhmm}}.mp4로 저장됨
    archive_dir = media_dir / "2603"
    final_video = archive_dir / "22_1230.mp4"
    assert final_video.exists(), "최종 영상이 Media에 저장되어야 함"


@pytest.mark.slow
def test_full_pipeline_fallback_to_local(tmp_path):
    """Media 없을 때 로컬 소스로 fallback 확인"""
    # Media 비어있음
    media_dir = tmp_path / "Media"
    media_dir.mkdir()

    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # 로컬 MOV 파일 생성 (간단한 더미)
    local_mov = data_dir / "260322_1230.mov"
    local_mov.write_bytes(b"MOCK_MOV_DATA")

    # YAML 파일
    yaml_file = data_dir / "260322_1230.yaml"
    yaml_file.write_text("sections: []")

    # config.yaml
    config_file = tmp_path / "config.yaml"
    config_file.write_text(f"""
video:
  media:
    mount_path: "{media_dir}"
  fallback:
    local_data_dir: "{data_dir}"
    default_image: "assets/default_bg.png"
""")

    from today_vn_news.main import process_video_pipeline
    from today_vn_news.config import VideoConfig
    from today_vn_news.tts import TTSEngine

    config = VideoConfig.from_yaml(str(config_file))

    # mock TTS 및 업로드
    with patch('today_vn_news.tts.yaml_to_tts', new_callable=AsyncMock()):
        with patch('today_vn_news.uploader.upload_video', return_value=True):
            result = process_video_pipeline(
                "260322_1230",
                str(data_dir),
                config,
                TTSEngine.EDGE,
                "ko-KR-SunHiNeural",
                "korean",
                None
            )

    # 로컬 소스 사용됨 (임시 파일 없음)
    temp_files = list(data_dir.glob("temp_*"))
    assert len(temp_files) == 0, "로컬 소스 사용 시 임시 복사본이 없어야 함"
```

- [ ] **Step 4: 커밋**

```bash
git add main.py tests/integration/test_video_pipeline.py
git commit -m "feat(main): VideoSourceResolver 및 MediaArchiver 통합

- 설정 로딩: VideoConfig.from_yaml()
- VideoSourceResolver: 우선순위 체인으로 소스 해결
- MediaArchiver: 최종 영상 Media 저장 (저장 → 업로드 순서)
- process_video_pipeline(): 테스트 가능하도록 파이프라인 로직 분리
- try-finally로 임시 파일 정리 보장
- 통합 테스트: Media 소스, 로컬 fallback 전체 흐름 검증

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 7: 최종 검증 및 문서 업데이트

**Files:**
- Modify: `README.md`

### 목적
전체 시스템이 정상 작동하는지 검증하고 문서 업데이트

### 구현

- [ ] **Step 1: README.md 업데이트**

```markdown
# README.md에 추가 섹션

## 영상 소스 관리

### 우선순위
1. Media/{{YYMMDD}}.mp4 (예: Media/260322.mp4)
2. Media/latest.mp4
3. Local data/{{YYMMDD_HHMM}}.mov/.mp4
4. assets/default_bg.png

### 최종 저장
- 경로: Media/{{YYMM}}/{{DD}}_{{hhmm}}.mp4
- 예: Media/2603/22_1230.mp4

### 설정
`config.yaml`에서 Media 경로 및 형식 설정 가능

```yaml
video:
  media:
    mount_path: "/Volumes/Media"
  archive:
    format: "{YYMM}/{DD}_{hhmm}.mp4"
```
```

- [ ] **Step 2: 전체 파이프라인 테스트**

```bash
# 모의 Media 환경에서 테스트
mkdir -p /tmp/test_media
cp tests/fixtures/media/* /tmp/test_media/

# config.yaml 테스트
uv run pytest tests/integration/test_video_pipeline.py -v
uv run pytest tests/unit/ -v
```

Expected: 모든 테스트 PASS

- [ ] **Step 3: 커밋**

```bash
git add README.md
git commit -m "docs: 영상 소스 우선순위 시스템 README 문서 추가

- 우선순위 체인 설명
- 최종 저장 경로 형식 명시
- config.yaml 설정 예시 추가
- 전체 파이프라인 검증 완료

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## 완료 체크리스트

- [ ] 모든 Task 완료
- [ ] 모든 테스트 PASS
- [ ] README 업데이트
- [ ] 커밋 메시지 확인
- [ ] `uv run pytest tests/` 전체 테스트 통과

---

## 참고 자료

- 설계 문서: `docs/superpowers/specs/2026-03-22-video-source-priority-design.md`
- 기존 코드: `today_vn_news/engine.py`, `main.py`, `exceptions.py`
- 테스트 프레임워크: pytest, unittest.mock
