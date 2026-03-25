"""타임스탬프 유틸리티 모듈

YYMMDD 형식 타임스탬프 처리와 파이프라인 단계 완료 파일 관리 기능 제공.
"""
import re
from datetime import datetime
from pathlib import Path

from today_vn_news.exceptions import PipelineRestartError


def normalize_timestamp(arg: str) -> str:
    """명령줄 인자를 YYMMDD 형식으로 정규화

    다양한 형식의 타임스탬프를 YYMMDD 6자리로 변환합니다.

    Args:
        arg: 타임스탬프 문자열 (YYMMDD, YYYYMMDD, YYYYMMDD_HHMM, YYYY-MM-DD 등)

    Returns:
        YYMMDD 형식의 6자리 문자열

    Examples:
        >>> normalize_timestamp("260319")
        '260319'
        >>> normalize_timestamp("20260319")
        '260319'
        >>> normalize_timestamp("20260319_1955")
        '260319'
        >>> normalize_timestamp("2026-03-19")
        '260319'
    """
    # 숫자 이외의 모든 문자 제거
    digits = re.sub(r"\D", "", arg)

    # 8자리(YYYYMMDD) 이상이면 앞 2자리 제거 (YYMMDD 추출)
    if len(digits) >= 8:
        return digits[2:8]
    # 6자리(YYMMDD)이면 그대로 반환
    elif len(digits) == 6:
        return digits
    else:
        # 그 외 경우는 앞에서 6자리만 반환
        return digits[:6]


def validate_yymmdd(timestamp: str) -> None:
    """YYMMDD 형식 검증

    Args:
        timestamp: YYMMDD 형식의 6자리 숫자 문자열

    Raises:
        ValueError: 형식이 올바르지 않거나 유효하지 않은 날짜인 경우

    Examples:
        >>> validate_yymmdd("260319")  # 통과
        >>> validate_yymmdd("26031")   # ValueError: 잘못된 형식
        >>> validate_yymmdd("261330")  # ValueError: 13월
    """
    if not re.match(r"^\d{6}$", timestamp):
        raise ValueError("잘못된 형식입니다. YYMMDD 6자리 숫자로 입력해주세요.")

    try:
        datetime.strptime(timestamp, "%y%m%d")
    except ValueError:
        raise ValueError("유효하지 않은 날짜입니다.")


def exists_done(yymmdd: str, module: str) -> bool:
    """완료 파일 존재 여부 확인

    Args:
        yymmdd: YYMMDD 형식 타임스탬프
        module: 모듈명 (scraper, translator, tts, engine, uploader, archiver)

    Returns:
        완료 파일 존재 여부

    Examples:
        >>> exists_done("260319", "scraper")
        False
        >>> create_done("260319", "scraper")
        >>> exists_done("260319", "scraper")
        True
    """
    return Path(f"data/{yymmdd}.{module}.done").exists()


def create_done(yymmdd: str, module: str) -> None:
    """완료 파일 생성

    Args:
        yymmdd: YYMMDD 형식 타임스탬프
        module: 모듈명 (scraper, translator, tts, engine, uploader, archiver)

    Examples:
        >>> create_done("260319", "scraper")
        >>> Path("data/260319.scraper.done").exists()
        True
    """
    Path(f"data/{yymmdd}.{module}.done").touch()


def assert_exists_done(yymmdd: str, required_module: str) -> None:
    """선행 단계 완료 필수 확인

    선행 단계의 완료 파일이 없으면 PipelineRestartError를 발생시킵니다.

    Args:
        yymmdd: YYMMDD 형식 타임스탬프
        required_module: 필수 선행 단계 모듈명

    Raises:
        PipelineRestartError: 선행 단계 완료 파일이 누락된 경우

    Examples:
        >>> create_done("260319", "scraper")
        >>> assert_exists_done("260319", "scraper")  # 통과
        >>> assert_exists_done("260319", "translator")  # PipelineRestartError
    """
    if not exists_done(yymmdd, required_module):
        raise PipelineRestartError(
            f"선행 단계({required_module})가 완료되지 않았습니다. "
            f"rm data/{yymmdd}.* && rm data/{yymmdd}.*.done 후 처음부터 실행하세요."
        )
