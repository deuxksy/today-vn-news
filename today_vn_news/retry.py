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


def with_api_retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
):
    """
    API 호출 재시도 데코레이터

    Args:
        max_attempts: 최대 시도 횟수 (초기 호출 포함)
        initial_delay: 초기 대기 시간 (초)
        backoff_factor: 백오프 배수 (지연 시간 = initial_delay * (backoff_factor ** attempt))
        exceptions: 재시도할 예외 타입 튜플

    Returns:
        데코레이터 함수
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
