#!/usr/bin/env python3
"""
Gemma-4 A/B 테스트: 260404_raw.yaml 전체 번역 비교
- Model A: gemma-4-26b-a4b-it (MoE)
- Model B: gemma-4-31b-it (Dense)
"""

import os
import sys
import time
import yaml
from google import genai
from google.genai import types

MODELS = {
    "A": "gemma-4-26b-a4b-it",
    "B": "gemma-4-31b-it",
}

RAW_FILE = "data/260404_raw.yaml"
DATE_STR = "260404"


def load_raw_data():
    with open(RAW_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def translate_with_model(client, model_name, articles, source_name):
    """기존 translator.py 로직과 동일한 프롬프트로 번역"""
    prompt = f"""다음 베트남어 뉴스 기사들을 한국어로 번역하고, 각각 3줄 요약을 작성해주세요.

**기준일**: {DATE_STR}
**뉴스 소스**: {source_name}

**입력 기사**:
"""
    for i, article in enumerate(articles, 1):
        clean_title = article["title"].replace(":", " -")
        prompt += f"""
{i}. 제목: {clean_title}
    URL: {article["url"]}
    내용: {article["content"]}
"""

    prompt += """
**출력 형식 (반드시 YAML만 출력)**:
items:
  - title: "한국어 번역된 기사 제목"
    content: "한국어 번역된 3줄 요약"
    url: "원문 링크"

**중요한 지침**:
1. 제목과 내용을 자연스러운 한국어 문장체로 번역하세요.
2. 요약은 3줄로 작성하고, 한국인이 이해하기 쉽게 작성하세요.
3. YAML 형식만 출력하고, 다른 설명은 하지 마세요.
4. 모든 값(title, content, url)은 반드시 큰따옴표(")로 감싸야 합니다.
5. 작은따옴표(')와 홑따옴표(')는 절대 사용하지 마세요.
"""

    start = time.time()
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        elapsed = time.time() - start

        if not response.text:
            return None, elapsed, "EMPTY"

        content = response.text.strip()
        if "```yaml" in content:
            content = content.split("```yaml")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        parsed = yaml.safe_load(content)
        items = parsed.get("items", parsed) if isinstance(parsed, dict) else parsed
        return items, elapsed, "OK"

    except Exception as e:
        elapsed = time.time() - start
        return None, elapsed, f"ERROR: {e}"


def run_test():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set")
        return

    client = genai.Client(api_key=api_key)
    raw_data = load_raw_data()

    # 안전 및 기상 관제는 번역 불필요, 나머지 뉴스 소스만 테스트
    skip_sections = {"안전 및 기상 관제"}
    sections = [s for s in raw_data["sections"] if s["name"] not in skip_sections]

    results_a = {}
    results_b = {}

    print(f"{'='*70}")
    print(f"Gemma-4 A/B 테스트: {len(sections)}개 섹션 전체 번역")
    print(f"{'='*70}")

    for section in sections:
        source_name = section["name"]
        articles = section["items"]
        if not articles:
            continue

        print(f"\n--- {source_name} ({len(articles)}개 기사) ---")

        for label, model_name in MODELS.items():
            items, elapsed, status = translate_with_model(
                client, model_name, articles, source_name
            )
            result = {"items": items, "time": elapsed, "status": status}

            if label == "A":
                results_a[source_name] = result
            else:
                results_b[source_name] = result

            icon = "✅" if status == "OK" else "❌"
            count = len(items) if items else 0
            print(f"  Model {label} ({model_name}): {icon} {status} | {count}개 | {elapsed:.1f}s")

    # 결과 저장
    output_a = f"data/260404_model_a.yaml"
    output_b = f"data/260404_model_b.yaml"

    save_results(results_a, output_a, MODELS["A"])
    save_results(results_b, output_b, MODELS["B"])

    # 비교 요약
    print(f"\n{'='*70}")
    print("비교 요약")
    print(f"{'='*70}")
    print(f"{'소스':<25} {'Model A (MoE)':<20} {'Model B (Dense)':<20}")
    print(f"{'-'*25} {'-'*20} {'-'*20}")

    total_time_a = 0
    total_time_b = 0
    for source_name in results_a:
        ra = results_a[source_name]
        rb = results_b.get(source_name, {})
        ta = f"{ra['time']:.1f}s ({ra['status']})"
        tb = f"{rb.get('time', 0):.1f}s ({rb.get('status', '-')})"
        total_time_a += ra["time"]
        total_time_b += rb.get("time", 0)
        print(f"{source_name:<25} {ta:<20} {tb:<20}")

    print(f"{'-'*25} {'-'*20} {'-'*20}")
    print(f"{'TOTAL':<25} {total_time_a:.1f}s{'':<14} {total_time_b:.1f}s")

    print(f"\n결과 저장:")
    print(f"  Model A: {output_a}")
    print(f"  Model B: {output_b}")


def save_results(results, output_path, model_name):
    sections = []
    for i, (source_name, r) in enumerate(results.items(), 2):
        section = {
            "id": str(i),
            "name": source_name,
            "model": model_name,
            "items": r["items"] or [],
            "status": r["status"],
            "time": f"{r['time']:.1f}s",
        }
        sections.append(section)

    data = {
        "metadata": {
            "date": DATE_STR,
            "test_model": model_name,
        },
        "sections": sections,
    }
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


if __name__ == "__main__":
    run_test()
