#!/usr/bin/env python3
"""
구조화된 로깅 시스템
- 목적: 프로젝트 전체의 일관된 로깅을 위한 중앙 집중식 로거
- 기능: 파일/콘솔 출력, 포맷팅, 로그 레벨 관리
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "today_vn_news",
    level: int = logging.INFO,
    log_file: Optional[Path] = None
) -> logging.Logger:
    """
    구조화된 로거 설정 및 반환.

    Args:
        name: 로거 이름 (기본값: "today_vn_news")
        level: 로그 레벨 (기본값: logging.INFO)
        log_file: 로그 파일 경로 (선택 사항, None인 경우 파일 로그 미사용)

    Returns:
        logging.Logger: 설정된 로거 인스턴스

    Note:
        - 콘솔: 지정된 레벨 이상 출력
        - 파일: log_file 지정 시 해당 파일에 기록
        - 중복 호출 시 기존 핸들러 재사용

    Example:
        >>> logger = setup_logger()
        >>> logger.info("테스트 메시지")
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 중복 핸들러 방지
    if logger.handlers:
        return logger

    # 포맷터 설정
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 파일 핸들러 (선택 사항)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# 전역 로거 인스턴스
logger = setup_logger()
