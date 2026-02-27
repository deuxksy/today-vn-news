#!/usr/bin/env python3
"""
API 호출 재시도 메커니즘
- 목적: Gemma API 등 외부 API 호출 실패 시 자동 재시도
- 기능: 지수 백오프(Exponential Backoff) 적용
"""

import time
import functools
from typing import Callable, Any, Type
from today_vn_news.logger import logger


def with_http_retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
):
    """
    HTTP 요청 재시도 데코레이터.

    타임아웃, 5xx 서버 에러, 네트워크 오류 시 자동 재시도합니다.
    4xx 클라이언트 에러는 즉시 실패 처리합니다.

    Args:
        max_attempts: 최대 시도 횟수 (기본값: 3, 초기 호출 포함)
        initial_delay: 초기 대기 시간(초) (기본값: 1.0)
        backoff_factor: 백오프 배수 (기본값: 2.0)
            지연 시간 = initial_delay * (backoff_factor ** attempt)

    Returns:
        Callable: 함수 데코레이터

    Raises:
        requests.RequestException: 모든 시도 실패 시 마지막 예외 재발생
        requests.HTTPError: 4xx 클라이언트 에러 발생 시 즉시 실패

    Example:
        >>> @with_http_retry(max_attempts=5)
        ... def fetch_data():
        ...     return requests.get("https://api.example.com")
    """
    import requests

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except requests.RequestException as e:
                    last_exception = e

                    # 4xx 클라이언트 에러는 즉시 실패 (재시도 무의미)
                    if isinstance(e, requests.Response) and 400 <= e.response.status_code < 500:
                        logger.error(f"{func.__name__} 실패: 클라이언트 에러 {e.response.status_code}")
                        raise

                    # 타임아웃, 5xx, 네트워크 오류는 재시도
                    if attempt < max_attempts - 1:
                        # 지수 백오프 계산
                        delay = initial_delay * (backoff_factor ** attempt)
                        logger.warning(
                            f"{func.__name__} 실패 (시도 {attempt + 1}/{max_attempts}): {str(e)}. "
                            f"{delay:.1f}초 후 재시도..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"{func.__name__} 실패: 최대 시도 횟수 초과 ({max_attempts}회)"
                        )

            # 모든 시도 실패 시 마지막 예외 재발생
            raise last_exception

        return wrapper

    return decorator


def with_api_retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
):
    """
    일반적인 API 호출 재시도 데코레이터.

    지정된 예외 타입 발생 시 지수 백오프를 적용하여 자동 재시도합니다.
    Gemma API 등 외부 API 호출에 사용합니다.

    Args:
        max_attempts: 최대 시도 횟수 (기본값: 3, 초기 호출 포함)
        initial_delay: 초기 대기 시간(초) (기본값: 1.0)
        backoff_factor: 백오프 배수 (기본값: 2.0)
            지연 시간 = initial_delay * (backoff_factor ** attempt)
        exceptions: 재시도할 예외 타입 튜플 (기본값: (Exception,))

    Returns:
        Callable: 함수 데코레이터

    Raises:
        Exception: 지정된 예외 타입으로 모든 시도 실패 시 마지막 예외 재발생

    Example:
        >>> @with_api_retry(max_attempts=3, exceptions=(ConnectionError, TimeoutError))
        ... def call_api():
        ...     return external_api_client.request()
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt < max_attempts - 1:
                        # 지수 백오프 계산
                        delay = initial_delay * (backoff_factor ** attempt)
                        logger.warning(
                            f"{func.__name__} 실패 (시도 {attempt + 1}/{max_attempts}): {str(e)}. "
                            f"{delay:.1f}초 후 재시도..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"{func.__name__} 실패: 최대 시도 횟수 초과 ({max_attempts}회)"
                        )

            # 모든 시도 실패 시 마지막 예외 재발생
            raise last_exception

        return wrapper

    return decorator
