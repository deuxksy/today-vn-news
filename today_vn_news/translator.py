#!/usr/bin/env python3
"""
Gemma 기반 번역 모듈
- 목적: 베트남어 기사를 한국어로 번역 및 요약
- 입력: 베트남어 기사 데이터 (스크래핑 결과)
- 출력: 한국어 번역 + 3줄 요약 (YAML 형식)
"""

from google import genai
from typing import List, Dict, Optional
import os

from today_vn_news.logger import logger
from today_vn_news.exceptions import TranslationError
from today_vn_news.retry import with_api_retry


@with_api_retry(max_attempts=2)
def _call_gemma_api(client, prompt: str):
    """
    Gemma API 호출 (재시도 적용)

    Args:
        client: GenAI 클라이언트
        prompt: 전송할 프롬프트

    Returns:
        API 응답 객체

    Raises:
        Exception: API 호출 실패 시 (최대 2회 재시도 후)
    """
    return client.models.generate_content(
        model="gemma-3-27b-it", contents=prompt
    )


def translate_weather_condition(condition: str) -> str:
    """
    베트남어 기상 상태를 한국어로 번역

    Args:
        condition: 베트남어 기상 상태 (예: "Mây thay đổi, trời nắng")

    Returns:
        한국어 번역된 기상 상태
    """
    if not condition:
        return condition

    # 빠른 매칭 (사전 기반)
    weather_dict = {
        "mây thay đổi": "구름 낌",
        "trời nắng": "맑음",
        "trời mưa": "비",
        "trời giông": "천둥번개",
        "nhiều mây": "흐림",
        "trời âm u": "흐림",
        "mưa rào": "소나기",
        "sương mù": "안개",
        "mây tản": "흐림 → 맑음",
        "nóng": "더움",
        "lạnh": "추움",
        "trời đẹp": "좋음",
        "nắng đẹp": "맑고 좋음",
    }

    # 부분 매칭으로 복합 상태 처리
    translated = condition.lower()
    for vn, kr in weather_dict.items():
        translated = translated.replace(vn.lower(), kr)

    # 매칭 안되면 Gemma API 사용
    if translated == condition.lower():
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if api_key:
            client = genai.Client(api_key=api_key)
            try:
                prompt = f"베트남어 기상 상태 '{condition}'를 한국어 3글자 이내로 짧게 번역해주세요. 답변만 출력하세요."
                response = _call_gemma_api(client, prompt)
                if response.text:
                    return response.text.strip()
            except Exception:
                pass

    return translated


def translate_articles(
    articles: List[Dict[str, str]],
    source_name: str,
    today_str: str,
    max_articles: int = 2,
) -> Optional[List[Dict[str, str]]]:
    """
    베트남어 기사 리스트를 한국어로 번역 및 요약

    Args:
        articles: 베트남어 기사 리스트 [{'title': str, 'content': str, 'url': str, 'date': str}]
        source_name: 뉴스 소스 이름
        today_str: 기준일 표시용
        max_articles: 번역할 최대 기사 수

    Returns:
        번역된 기사 리스트 [{'title': str, 'content': str, 'url': str}]
        실패 시 None 반환
    """
    if not articles:
        return []

    # 번역할 기사 제한
    articles_to_translate = articles[:max_articles]

    # Gemma 프롬프트 구성
    prompt = f"""다음 베트남어 뉴스 기사들을 한국어로 번역하고, 각각 3줄 요약을 작성해주세요.

**기준일**: {today_str}
**뉴스 소스**: {source_name} 

**입력 기사**:
"""

    for i, article in enumerate(articles_to_translate, 1):
        prompt += f"""
{i}. 제목: {article["title"]}
    URL: {article["url"]}
    내용: {article["content"]}
"""

    prompt += """
**출력 형식 (반드시 YAML만 출력)**:
items:
  - title: (한국어 번역된 기사 제목)
    content: (한국어 번역된 3줄 요약)
    url: (원문 링크)

**중요한 지침**:
1. 제목과 내용을 자연스러운 한국어 문장체로 번역하세요.
2. 요약은 3줄로 작성하고, 한국인이 이해하기 쉽게 작성하세요.
3. YAML 형식만 출력하고, 다른 설명은 하지 마세요.
4. 따옴표(')를 사용하지 마세요. 대신 큰따옴표(")를 사용하세요.
5. 작은따옴표(')는 절대 사용하지 마세요.
6. 홑따옴표(')는 절대 사용하지 마세요.
7. 올바른 YAML 문법을 따르세요.
"""

    # 사이트별 TTS 최적화 규칙 추가
    tts_rules = """
    8. **모든 기사 TTS 최적화**: 영어 약어, 통화 단위 등은 그대로 사용합니다.
       - 5G, 4G, 3G, AI, API, AWS, SaaS, USD, VND 등은 원래대로 읽습니다.
"""

    # 사이트별 추가 최적화 규칙
    if "Thanh Niên" in source_name:
        tts_rules += """
    9. **Thanh Niên 추가 최적화**: 불필요한 수식어 및 자극적인 문장 부호(!!!, ???)를 제거하세요. 느낌표는 최대 1개만, 물음표는 최대 2개까지만 허용합니다.
"""

    prompt += tts_rules

    prompt += """
**올바른 출력 예시**:
```yaml
items:
  - title: 한국어 제목
    content: 한국어 내용 3줄 요약입니다. 두 번째 줄입니다. 세 번째 줄입니다.
    url: https://example.com/article
```

"""

    # Gemma API 호출
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.error("번역 중단: API 키가 설정되지 않았습니다.")
        raise TranslationError("Translation aborted: API key not configured")

    client = genai.Client(api_key=api_key)

    try:
        logger.info(f"{source_name} 기사 {len(articles_to_translate)}개 번역 시작")

        response = _call_gemma_api(client, prompt)

        if response.text:
            # YAML 파싱
            import yaml

            content = response.text.strip()

            # 마크다운 코드 블록 제거
            if "```yaml" in content:
                content = content.split("```yaml")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            # 홑따옴표 제거 (새로운 로직)
            content = content.replace("'''", "").replace("'''", "")

            try:
                parsed_yaml = yaml.safe_load(content)

                if isinstance(parsed_yaml, dict) and "items" in parsed_yaml:
                    logger.info(f"{source_name} 번역 완료: {len(parsed_yaml['items'])}개 기사")
                    return parsed_yaml["items"]
                elif isinstance(parsed_yaml, list):
                    logger.info(f"{source_name} 번역 완료: {len(parsed_yaml)}개 기사")
                    return parsed_yaml
                else:
                    logger.error(f"{source_name} 번역 결과 파싱 실패 - 빈값 또는 잘못된 형식")
                    raise TranslationError(f"{source_name}: Translation result parsing failed - empty or invalid format")
            except yaml.YAMLError as e:
                logger.error(f"{source_name} YAML 파싱 실패: {str(e)}", exc_info=True)
                raise TranslationError(f"{source_name}: YAML parsing failed: {str(e)}")

    except Exception as e:
        if isinstance(e, TranslationError):
            raise
        logger.error(f"{source_name} 번역 실패", exc_info=True)
        raise TranslationError(f"Translation failed for {source_name}: {str(e)}")


def save_translated_yaml(
    translated_data: Dict, date_str: str, output_path: str
) -> bool:
    """
    번역된 데이터를 YAML로 저장

    Args:
        translated_data: 번역된 섹션 데이터
        date_str: 기준일
        output_path: 출력 파일 경로

    Returns:
        성공 여부
    """
    import yaml
    import os

    logger.info("번역된 YAML 저장 시작")

    yaml_data = {
        "metadata": {
            "date": date_str.split()[0] if " " in date_str else date_str,
            "time": date_str.split()[1] if " " in date_str else "",
            "location": "Ho Chi Minh City (Saigon Pearl)",
        },
        "sections": translated_data["sections"]
        if isinstance(translated_data, dict)
        else translated_data,
    }

    # 디렉토리 생성
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # YAML 파일로 저장
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(
            yaml_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False
        )

    logger.info(f"번역된 YAML 저장 완료: {output_path}")
    return True


def translate_and_save(scraped_data: Dict, date_str: str, output_path: str) -> bool:
    """
    모든 스크래핑 데이터를 번역 및 번역된 YAML 저장

    Args:
        scraped_data: 스크래핑된 원본 데이터
        date_str: 기준일 표시용
        output_path: 출력 파일 경로

    Returns:
        성공 여부
    """
    logger.info("모든 뉴스 번역 시작")

    translated_sections = []
    section_id = 1

    # 우선순위별 순서: 안전 및 기상(P0) → 건강(P0) → 정부(P1) → 로컬(P2)
    source_order = [
        "안전 및 기상 관제",
        "Sức khỏe & Đời sống",
        "Nhân Dân",
        "Tuổi Trẻ",
        "VietnamNet",
        "VnExpress",
        "Thanh Niên",
        "The Saigon Times",
        "VietnamNet 정보통신",
        "VnExpress IT/과학",
    ]

    # 순서대로 처리
    for source_name in source_order:
        if source_name not in scraped_data:
            continue

        articles = scraped_data[source_name]

        # 안전 및 기상 관제 (이미 스크래핑된 데이터 번역)
        if source_name == "안전 및 기상 관제":
            section = {"id": str(section_id), "name": source_name, "priority": "P0", "items": []}

            # 스크래핑된 안전 데이터를 그대로 사용 (이미 베트남어/한국어 혼합)
            for item in articles:
                # 플레이스홀더인 경우 그대로 사용
                if item.get("name") == "플레이스홀더":
                    section["items"].append(
                        {
                            "title": "안전 및 기상 관제",
                            "content": item["content"],
                            "url": item["url"],
                        }
                    )
                else:
                    # 기상/공기질/지진 데이터 처리
                    if item.get("name") == "기상":
                        # 기상 상태 번역
                        condition = item.get("condition", "")
                        translated_condition = translate_weather_condition(condition)

                        # 온도/습도 포맷팅
                        temp = item.get("temp", "")
                        humidity = item.get("humidity", "")

                        content = (
                            f"{translated_condition}, 온도 {temp}, 습도 {humidity}"
                        )

                        section["items"].append(
                            {
                                "title": f"기상 (NCHMF)",
                                "content": content,
                                "url": item["url"],
                            }
                        )
                    elif item.get("name") == "공기":
                        section["items"].append(
                            {
                                "title": f"공기질 (IQAir) - AQI {item.get('aqi', '')}",
                                "content": item["content"],
                                "url": item["url"],
                            }
                        )
                    elif item.get("name") == "지진":
                        section["items"].append(
                            {
                                "title": item["title"],
                                "content": item["content"],
                                "url": item["url"],
                            }
                        )

            if section["items"]:
                translated_sections.append(section)
                logger.info(f"{source_name} 데이터 저장 완료: {len(section['items'])}개")

            section_id += 1  # 안전 및 기상 관제 후 ID 증가

        # 일반 뉴스 소스 (스크래핑 + 번역)
        elif articles:
            section = {
                "id": str(section_id),
                "name": source_name,
                "priority": "P0" if "Sức khỏe" in source_name else "P2",
                "items": [],
            }

            # 번역
            try:
                translated_items = translate_articles(
                    articles, source_name, date_str, len(articles)
                )
            except TranslationError:
                translated_items = None

            if translated_items:
                section["items"] = translated_items
                translated_sections.append(section)
                logger.info(f"{source_name} 번역 완료: {len(translated_items)}개")
            else:
                # 번역 실패 시 원본 데이터 저장
                for article in articles:
                    section["items"].append(
                        {
                            "title": article["title"],
                            "content": article["content"],
                            "url": article["url"],
                        }
                    )
                translated_sections.append(section)
                logger.warning(f"{source_name} 번역 실패, 원본 데이터 저장")

            section_id += 1

    if not translated_sections:
        logger.error("번역된 뉴스가 전혀 없습니다.")
        return False

    # 번역된 YAML 저장
    return save_translated_yaml(
        {"sections": translated_sections}, date_str, output_path
    )
