#!/usr/bin/env python3
"""
기상 번역 기능 테스트
"""

import sys

sys.path.insert(0, ".")

from today_vn_news.translator import translate_weather_condition


def test_weather_translation():
    """기상 번역 기능 테스트"""
    print("=" * 50)
    print("기상 번역 테스트")
    print("=" * 50)

    test_cases = [
        ("Mây thay đổi, trời nắng", "구름 낌, 맑음"),
        ("Trời mưa", "비"),
        ("Nhiều mây", "흐림"),
        ("Trời giông", "천둥번개"),
        ("Mưa rào", "소나기"),
        ("Sương mù", "안개"),
        ("Mây tản", "흐림 → 맑음"),
        ("Nóng", "더움"),
        ("Lạnh", "추움"),
        ("Trời đẹp", "좋음"),
        ("Nắng đẹp", "맑고 좋음"),
        ("Trời âm u", "흐림"),
        ("", ""),
    ]

    passed = 0
    failed = 0

    for vn_input, expected in test_cases:
        result = translate_weather_condition(vn_input)
        status = "✅" if result == expected else "❌"

        if result == expected:
            passed += 1
        else:
            failed += 1

        print(f"{status} {vn_input:30s} → {result:20s} (기대: {expected})")

    print("-" * 50)
    print(f"결과: {passed}개 통과, {failed}개 실패")
    print("=" * 50)

    return failed == 0


if __name__ == "__main__":
    success = test_weather_translation()
    sys.exit(0 if success else 1)
