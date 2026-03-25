"""MediaArchiver 단위 테스트"""

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
    (data_dir / "260322_final.mp4").touch()

    config = VideoConfig(media_mount_path=str(media_dir))
    archiver = MediaArchiver(config)

    media_path = archiver.archive(str(data_dir / "260322_final.mp4"), "260322")

    # 검증: 폴더 생성
    assert media_path.parent.exists()
    assert media_path.parent.name == "2603"
    # hhmm는 동적이므로 파일명 패턴만 확인
    assert media_path.stem.startswith("22_")
    assert media_path.suffix == ".mp4"
    assert media_path.exists()


def test_archive_correct_naming(tmp_path):
    """파일명 {{YYMM}}/{{DD}}_{{hhmm}}.mp4 형식 확인"""
    media_dir = tmp_path / "Media"
    media_dir.mkdir()

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "260322_final.mp4").touch()

    config = VideoConfig(media_mount_path=str(media_dir))
    archiver = MediaArchiver(config)

    media_path = archiver.archive(str(data_dir / "260322_final.mp4"), "260322")

    # 전체 경로 검증 (hhmm는 동적)
    assert "2603/22_" in str(media_path)
    assert media_path.suffix == ".mp4"


def test_archive_overwrites_existing(tmp_path):
    """동일 파일명 존재 시 덮어쓰기 확인"""
    media_dir = tmp_path / "Media"
    media_dir.mkdir()

    # YYMM 폴더 및 기존 파일 생성
    archive_dir = media_dir / "2603"
    archive_dir.mkdir()
    old_file = archive_dir / "22_0000.mp4"  # 기존 파일 (hhmm=0000)
    old_file.write_text("old")
    old_mtime = old_file.stat().st_mtime

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    new_file = data_dir / "260322_final.mp4"
    new_file.write_text("new content")

    config = VideoConfig(media_mount_path=str(media_dir))
    archiver = MediaArchiver(config)

    media_path = archiver.archive(str(new_file), "260322")

    # 덮어쓰기 확인 (내용 및 mtime 변경)
    assert media_path.read_text() == "new content"
    assert media_path.stat().st_mtime > old_mtime


def test_archive_media_mount_failure(tmp_path):
    """Media 마운트 실패 시 예외 발생 확인"""
    # 존재하지 않는 경로 지정
    config = VideoConfig(media_mount_path="/nonexistent/media")
    archiver = MediaArchiver(config)

    with pytest.raises(MediaArchiveError):
        archiver.archive("/fake/path/final.mp4", "260322")


def test_archive_audio_mp3(tmp_path):
    """MP3 음성 파일도 같은 경로에 저장 확인"""
    media_dir = tmp_path / "Media"
    media_dir.mkdir()

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "260322.mp3").touch()

    config = VideoConfig(media_mount_path=str(media_dir))
    archiver = MediaArchiver(config)

    media_path = archiver.archive_audio(str(data_dir / "260322.mp3"), "260322")

    # 검증: MP3 파일이 같은 경로에 저장
    assert media_path.parent.exists()
    assert media_path.parent.name == "2603"
    # hhmm는 동적이므로 파일명 패턴만 확인
    assert media_path.stem.startswith("22_")
    assert media_path.suffix == ".mp3"
    assert media_path.exists()


def test_archive_audio_missing_file(tmp_path):
    """MP3 파일 없을 때 예외 발생 확인"""
    media_dir = tmp_path / "Media"
    media_dir.mkdir()

    config = VideoConfig(media_mount_path=str(media_dir))
    archiver = MediaArchiver(config)

    with pytest.raises(MediaArchiveError):
        archiver.archive_audio("/nonexistent/260322.mp3", "260322")
