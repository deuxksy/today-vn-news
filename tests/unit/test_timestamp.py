"""타임스탬프 유틸리티 모듈 테스트

YYMMDD 형식 타임스탬프 처리와 파이프라인 단계 완료 파일 관리 기능을 테스트합니다.
"""
import pytest
from pathlib import Path
from today_vn_news.timestamp import (
    normalize_timestamp,
    validate_yymmdd,
    exists_done,
    create_done,
    assert_exists_done,
)
from today_vn_news.exceptions import PipelineRestartError


def test_normalize_timestamp():
    """다양한 타임스탬프 형식을 YYMMDD로 정규화"""
    assert normalize_timestamp("260319") == "260319"
    assert normalize_timestamp("20260319") == "260319"
    assert normalize_timestamp("20260319_1955") == "260319"
    assert normalize_timestamp("2026-03-19") == "260319"  # 구분자 무시


def test_validate_yymmdd_valid():
    """올바른 YYMMDD 형식 검증"""
    validate_yymmdd("260319")  # 예외 없어야 함


def test_validate_yymmdd_invalid_format():
    """잘못된 형식 검증"""
    with pytest.raises(ValueError, match="잘못된 형식"):
        validate_yymmdd("26031")  # 5자리


def test_validate_yymmdd_invalid_date():
    """유효하지 않은 날짜 검증"""
    with pytest.raises(ValueError, match="유효하지 않은 날짜"):
        validate_yymmdd("261330")  # 13월


def test_done_files(tmp_path):
    """완료 파일 생성 및 존재 확인"""
    # 현재 작업 디렉토리를 임시 경로로 변경
    import os
    original_cwd = os.getcwd()

    try:
        os.chdir(tmp_path)
        Path("data").mkdir(exist_ok=True)

        yymmdd = "260319"

        # 초기 상태: 존재하지 않음
        assert not exists_done(yymmdd, "scraper")

        # 생성
        create_done(yymmdd, "scraper")
        assert exists_done(yymmdd, "scraper")

        # 파일 경로 확인
        assert Path(f"data/{yymmdd}.scraper.done").exists()
    finally:
        os.chdir(original_cwd)


def test_assert_exists_done_success(tmp_path):
    """선행 단계 존재 시 통과"""
    import os
    original_cwd = os.getcwd()

    try:
        os.chdir(tmp_path)
        Path("data").mkdir(exist_ok=True)

        yymmdd = "260319"
        create_done(yymmdd, "scraper")
        assert_exists_done(yymmdd, "scraper")  # 예외 없어야 함
    finally:
        os.chdir(original_cwd)


def test_assert_exists_done_failure(tmp_path):
    """선행 단계 누락 시 예외 발생"""
    import os
    original_cwd = os.getcwd()

    try:
        os.chdir(tmp_path)
        Path("data").mkdir(exist_ok=True)

        yymmdd = "260319"
        # scraper.done 생성하지 않음
        with pytest.raises(PipelineRestartError):
            assert_exists_done(yymmdd, "translator")
    finally:
        os.chdir(original_cwd)
