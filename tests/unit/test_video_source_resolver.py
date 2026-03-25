"""VideoSourceResolver 단위 테스트"""

import pytest
from pathlib import Path
from today_vn_news.video_source.resolver import VideoSourceResolver
from today_vn_news.config import VideoConfig
from today_vn_news.exceptions import MediaMountError, MediaCopyError, VideoSourceError


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
    config = VideoConfig(
        media_mount_path=str(media_dir),
        local_data_dir=str(data_dir)
    )
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

    config = VideoConfig(
        media_mount_path=str(media_dir),
        local_data_dir=str(data_dir)
    )
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

    config = VideoConfig(
        media_mount_path=str(media_dir),
        local_data_dir=str(data_dir)
    )
    resolver = VideoSourceResolver(config)

    source_path, is_temp = resolver.resolve("260322_1230")

    assert is_temp is False
    assert "260322_1230.mov" == source_path.name


def test_resolve_local_mp4_fallback(tmp_path):
    """로컬 .mov 없을 때 .mp4 반환"""
    media_dir = tmp_path / "Media"
    media_dir.mkdir()

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "260322_1230.mp4").touch()

    config = VideoConfig(
        media_mount_path=str(media_dir),
        local_data_dir=str(data_dir)
    )
    resolver = VideoSourceResolver(config)

    source_path, is_temp = resolver.resolve("260322_1230")

    assert is_temp is False
    assert "260322_1230.mp4" == source_path.name


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
        local_data_dir=str(data_dir),
        default_image=str(default_dir / "default_bg.png")
    )
    resolver = VideoSourceResolver(config)

    source_path, is_temp = resolver.resolve("260322_1230")

    assert is_temp is False
    assert "default_bg.png" == source_path.name


def test_temporary_copy_and_cleanup(tmp_path):
    """Media 소스 복사 후 정리 확인"""
    media_dir = tmp_path / "Media"
    media_dir.mkdir()
    (media_dir / "260322.mp4").touch()

    data_dir = tmp_path / "data"
    data_dir.mkdir()

    config = VideoConfig(
        media_mount_path=str(media_dir),
        local_data_dir=str(data_dir)
    )
    resolver = VideoSourceResolver(config)

    # 복사
    source_path, is_temp = resolver.resolve("260322_1230")
    assert is_temp is True
    assert source_path.exists()

    # 정리
    resolver.cleanup_temporary()
    assert not source_path.exists()


def test_resolve_all_sources_missing_raises_error(tmp_path):
    """모든 소스 없을 때 VideoSourceError 발생"""
    media_dir = tmp_path / "Media"
    media_dir.mkdir()

    data_dir = tmp_path / "data"
    data_dir.mkdir()

    config = VideoConfig(
        media_mount_path=str(media_dir),
        local_data_dir=str(data_dir),
        default_image=str(tmp_path / "nonexistent.png")
    )
    resolver = VideoSourceResolver(config)

    with pytest.raises(VideoSourceError):
        resolver.resolve("260322_1230")


def test_resolve_media_missing_skips_to_local(tmp_path):
    """Media 폴더가 없으면 로컬 소스로 바로 fallback"""
    # 존재하지 않는 Media 경로
    media_dir = tmp_path / "NonExistentMedia"
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "260322_1230.mov").touch()

    config = VideoConfig(
        media_mount_path=str(media_dir),
        local_data_dir=str(data_dir)
    )
    resolver = VideoSourceResolver(config)

    # Media가 없으므로 로컬 소스를 사용해야 함
    source_path, is_temp = resolver.resolve("260322_1230")
    assert is_temp is False
    assert "260322_1230.mov" == source_path.name


def test_extract_yymmdd_from_new_format(tmp_path):
    """YYMMDD 형식(6자리) base_name에서 Media 파일 정상 매칭"""
    # 새로운 YYMMDD 형식 (6자리)
    media_dir = tmp_path / "Media"
    media_dir.mkdir()
    (media_dir / "260325.mp4").touch()

    data_dir = tmp_path / "data"
    data_dir.mkdir()

    config = VideoConfig(
        media_mount_path=str(media_dir),
        local_data_dir=str(data_dir)
    )
    resolver = VideoSourceResolver(config)

    # YYMMDD 형식으로 resolve
    source_path, is_temp = resolver.resolve("260325")
    assert is_temp is True
    assert source_path.exists()


def test_extract_yymmdd_backward_compatible(tmp_path):
    """기존 YYMMDD_HHMM 형식(10자리)과의 호환성 유지"""
    # 기존 형식도 지원해야 함 (backward compatibility)
    media_dir = tmp_path / "Media"
    media_dir.mkdir()
    (media_dir / "260325.mp4").touch()

    data_dir = tmp_path / "data"
    data_dir.mkdir()

    config = VideoConfig(
        media_mount_path=str(media_dir),
        local_data_dir=str(data_dir)
    )
    resolver = VideoSourceResolver(config)

    # YYMMDD_HHMM 형식으로도 동일한 Media 파일을 찾을 수 있어야 함
    source_path, is_temp = resolver.resolve("260325_1200")
    assert is_temp is True
    assert source_path.exists()
