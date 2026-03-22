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

def test_from_yaml_missing_file():
    config = VideoConfig.from_yaml("nonexistent.yaml")

    # 파일 없으면 모든 기본값 반환 검증
    assert config.media_mount_path == "/Volumes/Media"
    assert config.media_date_format == "YYMMDD"
    assert config.auto_copy_latest is True
    assert config.archive_format == "{YYMM}/{DD}_{hhmm}.mp4"
    assert config.local_data_dir == "data"
    assert config.default_image == "assets/default_bg.png"

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

def test_from_yaml_invalid_yaml(tmp_path):
    from today_vn_news.exceptions import TodayVnNewsError

    config_file = tmp_path / "invalid.yaml"
    with open(config_file, "w") as f:
        f.write("invalid: yaml: content:")

    with pytest.raises(TodayVnNewsError):
        VideoConfig.from_yaml(str(config_file))
