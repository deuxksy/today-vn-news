#!/usr/bin/env python3
import subprocess
import datetime
import os
import sys

"""
베트남 뉴스 및 안전 정보 통합 수집 모듈 (Gemini CLI Wrapper)
- 목적: Gemini CLI를 활용하여 7대 일간지 및 건강/안전 실시간 정보를 수집 및 요약
- 상세 사양: ContextFile.md 4장 '일간지별 데이터 수집 모듈 상세 명세' 참조
"""


# 수집 대상 정의 (ContextFile.md 규격 준수)
SOURCES = [
    {
        "id": "safety_weather",
        "name": "안전 및 기상 관제",
        "priority": 0,
        "prompt": (
            "NCHMF, IGP-VAST, IQAir(Ho Chi Minh City) 정보를 바탕으로 오늘의 날씨와 공기질을 요약해줘.\n"
            "- 위치: 호치민 랜드마크 2 인근\n"
            "- 필수 포함: 기온(최저/최고), 습도, 강수 확률, AQI 지수, PM2.5\n"
            "- 행동 지침: AQI 100 초과 시 '마스크 착용 권고', 강수 확률 70% 이상 시 '우산 준비' 문구 포함."
        )
    },
    {
        "id": "nhandan",
        "name": "Nhân Dân (정부 기관지)",
        "priority": 1,
        "prompt": "https://nhandan.vn/ 에서 오늘 발표된 베트남 정부의 주요 신규 정책, 법령 또는 행정 공고를 **최소 2개** 요약해줘."
    },
    {
        "id": "health",
        "name": "Sức khỏe & Đời sống (건강/위생)",
        "priority": 0,
        "prompt": (
            "https://suckhoedoisong.vn/ 에서 오늘의 식품 위생 위반, 알레르기 유발 정보, 질병 주의보를 수집해줘.\n"
            "- 규칙: 식중독, 대기질 악화, 전염병 정보 등 건강 관련 이슈를 **최소 2개 이상** 상세히 수집해줘."
        )
    },
    {
        "id": "vnexpress",
        "name": "VnExpress (종합 속보)",
        "priority": 2,
        "prompt": "https://vnexpress.net/ 에서 오늘의 가장 조회수가 높거나 중요한 종합 뉴스 및 경제 이슈를 **최소 2개** 요약해줘."
    },
    {
        "id": "tuoitre",
        "name": "Tuổi Trẻ (로컬/시정)",
        "priority": 2,
        "prompt": "https://tuoitre.vn/ 의 'TP.HCM' 섹션에서 호치민 시정 소식 및 생활 밀착형 정보를 **최소 2개** 요약해줘."
    },
    {
        "id": "thanhnien",
        "name": "Thanh Niên (사회/청년)",
        "priority": 2,
        "prompt": "https://thanhnien.vn/ 에서 오늘 가장 화제가 된 사회 트렌드 및 독자 제보 뉴스를 **최소 2개** 요약해줘."
    },
    {
        "id": "ictnews",
        "name": "ICTNews (IT/Tech)",
        "priority": 2,
        "prompt": "https://vietnamnet.vn/ict 에서 베트남 IT 산업 동향, 개발자 채용 시장, Cloud 도입 현황 관련 뉴스를 **최소 2개** 요약해줘."
    },
    {
        "id": "saigontimes",
        "name": "The Saigon Times (경제)",
        "priority": 2,
        "prompt": "https://thesaigontimes.vn/ 에서 환율, 물가, 부동산 등 경제 지표 및 투자 동향을 **최소 2개** 요약해줘."
    }
]

# 공통 출력 및 TTS 최적화 지침
COMMON_INSTRUCTIONS = """

**출력 규칙 (최우선 지침):**
1. **Empty String Policy**: 만약 대상 기준일(오늘)에 해당하는 새로운 기사가 없다면, 어떠한 설명도 없이 반드시 '공백'만 반환하세요.
2. **No Meta-Talk**: '검색을 시작하겠습니다' 등 로봇의 진행 과정이나 인사말을 절대 포함하지 마세요. 오직 뉴스 본문만 출력합니다.
3. **Hierarchy**: 매체명은 ## (Level 2), 기사 제목은 ### (Level 3) 헤더를 사용하세요.
4. **Style**: 한국어 3줄 요약(평어체 리스트) + [원문 링크] 구조를 유지하세요.

**TTS(음성 합성) 최적화 가이드:**
- 에모지 및 특수 문자(°C, % 등) 사용 절대 금지.
- 괄호 안의 영어 표기 제거 및 순수 한국어 독음화.
- 숫자는 읽기 편하게 한글로 변환 (예: 32도, 10퍼센트).
- 문장 끝은 '입니다', '하세요' 등 정중한 구어체로 종결.
"""

def fetch_source_content(source, today_str, index, total):
    """Gemini CLI를 호출하여 개별 소스 뉴스 수집"""
    prompt = f"매체명: {source['name']}\n\n{source['prompt']}\n대상 기준일: {today_str}{COMMON_INSTRUCTIONS}"
    
    print(f"[{index}/{total}] {source['name']} 수집 중...")
    try:
        process = subprocess.run(
            ["gemini", prompt],
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        if process.returncode == 0 and process.stdout.strip():
            content = process.stdout.strip()
            print(f"  [OK] {source['name']} 수집 완료")
            return content
        else:
            print(f"  [!] {source['name']} 수집 실패 또는 내용 없음")
            return None
    except Exception as e:
        print(f"  [!] {source['name']} 수집 중 예외 발생: {str(e)}")
        return None

def fetch_all_news():
    """모든 소스를 순회하며 뉴스 통합 수집"""
    now = datetime.datetime.now()
    yymmdd = now.strftime("%y%m%d")
    today_display = now.strftime("%Y년 %m월 %d일")
    output_path = f"data/{yymmdd}.md"

    if not os.path.exists("data"):
        os.makedirs("data")

    # ContextFile.md 7.1~7.8 규정 순서대로 처리
    sorted_sources = SOURCES
    total_sources = len(sorted_sources)
    
    print(f"\n[*] {today_display} 베트남 뉴스 통합 수집 시작 (총 {total_sources}개 매체)")
    print("-" * 50)
    
    final_md = [f"# 오늘의 베트남 주요 뉴스 ({today_display})\n\n"]
    collected_count = 0
    
    for i, src in enumerate(sorted_sources, 1):
        content = fetch_source_content(src, today_display, i, total_sources)
        if content:
            final_md.append(content)
            final_md.append("\n\n---\n\n")
            collected_count += 1
    
    print("-" * 50)
    if collected_count == 0:
        print("[!] 수집된 뉴스가 전혀 없습니다. 네트워크 상태나 API 키를 확인하세요.")
        return False

    # 마지막 구분선 제거
    if final_md[-1] == "\n\n---\n\n":
        final_md.pop()

    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(final_md)

    print(f"[+] 통합 뉴스 리포트 생성 완료: {output_path} (수집 성공: {collected_count}/{total_sources})")
    return True

# 진입점 호환성 유지
def fetch_it_news():
    return fetch_all_news()

if __name__ == "__main__":
    fetch_all_news()
