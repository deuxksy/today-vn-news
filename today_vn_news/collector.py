#!/usr/bin/env python3
import requests
import json
import datetime
import os
import sys

"""
베트남 뉴스 및 안전 정보 통합 수집 모듈 (Gemini API Direct Call)
- 목적: Gemini API를 직접 호출하여 안전/기상 정보 및 주요 뉴스 수집
- 대상 청중: 베트남 거주 한국인
- 상세 사양: ContextFile.md 4장 참조
"""


# 수집 대상 정의 (ContextFile.md 규격 준수)
# 대상 청중: 베트남 거주 한국인
SOURCES = [
    # === Critical (P0): 안전 및 기상 관제 ===
    {
        "id": "nchmf_weather",
        "name": "안전 및 기상 관제",
        "priority": 0,
        "prompt": (
            "NCHMF(국립기상예보센터), IGP-VAST(지질연구소), IQAir(Ho Chi Minh City) 정보를 바탕으로 호치민 지역의 오늘 안전 및 기상 정보를 요약해줘.\n"
            "\n"
            "**긴급 특보 (Conditional)**\n"
            "- 태풍, 지진, 홍수, 대형 화재 발생 시 '🚨 긴급 특보' 섹션 생성 (발생하지 않을 경우 생략)\n"
            "\n"
            "**상시 관제 (Always)**\n"
            "- 위치: 호치민 랜드마크 81 인근\n"
            "- 날씨: 기온(최저/최고, 반드시 섭씨), 습도, 강수 확률\n"
            "- 지진: 최근 24시간 이내 지진 발생 여부 (없으면 '최근 지진 발생 없음')\n"
            "- 공기질: AQI 지수, PM2.5, PM10\n"
            "\n"
            "**행동 지침**\n"
            "- AQI 100 초과 시: '공기질이 나쁨니다. 마스크를 반드시 착용하고 실외 활동을 자제하십시오.' 문구 포함\n"
            "- 강수 확률 70% 이상 시: '비 예보가 있습니다. 이동 시 우산을 준비하십시오.' 문구 포함\n"
            "\n"
            "**중요**: 이 섹션은 실시간 관제 정보이므로 'Empty String Policy'를 무시하고 항상 최신 정보를 제공하세요. 모든 온도는 섭씨(도)로 표기하세요."
        )
    },
    
    # === High (P1): 정부 공식 입장 ===
    {
        "id": "nhandan",
        "name": "Nhân Dân (베트남 공식 관보)",
        "priority": 1,
        "prompt": (
            "https://nhandan.vn/ 에서 오늘 발표된 베트남 공산당 및 정부의 공식 입장, 신규 법령, 행정 절차(비자, 거주증) 정보를 수집해줘.\n"
            "- 규칙: 당일 발표된 신규 정책 또는 행정 공고 **2개** 수집\n"
            "- 우선순위: 한국인에게 영향을 줄 수 있는 정보 (비자, 거주증 등)\n"
            "- **배타적 수집**: 정부 관련 정보는 이 섹션에서만 수집하고 다른 소스에서는 중복 수집하지 마세요."
        )
    },
    
    # === Critical (P0): 건강/위생 ===
    {
        "id": "health",
        "name": "Sức khỏe & Đời sống (베트남 보건부 관보)",
        "priority": 0,
        "prompt": (
            "https://suckhoedoisong.vn/ 에서 오늘의 식품 위생 위반, 알레르기 유발 정보, 질병 주의보를 수집해줘.\n"
            "- 규칙: 식중독 사례, 호치민 대기질 악화, 전염병 정보 등 **건강 관련 이슈 전수 수집**\n"
            "- 특별 강조: 궤양성 대장염, 알레르기 관련 정보가 있으면 우선 포함\n"
            "- **배타적 수집**: 보건 관련 정보는 이 섹션에서만 수집하고 다른 소스에서는 중복 수집하지 마세요."
        )
    },
    
    # === Normal (P2): 로컬/시정 ===
    {
        "id": "tuoitre",
        "name": "Tuổi Trẻ (호치민의 실제 삶)",
        "priority": 2,
        "prompt": (
            "https://tuoitre.vn/ 에서 호치민(HCMC) 중심의 시정 소식 및 주요 도로 통제 이벤트를 수집해줘.\n"
            "- 규칙: 최신 기사 **2개** 수집\n"
            "- 우선순위: 교통 통제, 주요 이벤트, 한국인 거주 지역(2군, 7군 등) 관련 뉴스\n"
            "- **배타적 수집**: 호치민시 관련 정보는 이 섹션에서만 수집하고 다른 소스에서는 중복 수집하지 마세요."
        )
    }
]

# 공통 출력 및 TTS 최적화 지침
COMMON_INSTRUCTIONS = """

**출력 규칙 (최우선 지침):**
1. **Empty String Policy**: (뉴스 매체 및 지진 정보 한정) 만약 대상 기준일(오늘)에 해당하는 새로운 소식이 전혀 없다면, 단 한 글자도 출력하지 말고 반드시 **빈 문자열(empty string)**만 반환하세요. "발표된 내용이 없습니다" 같은 설명도 절대 하지 마세요.
2. **Safety/Weather Exception**: 날씨 및 공기질 정보는 항상 최신 데이터를 찾아 보고하세요.
3. **No Meta-Talk**: 인사말, 진행 상황, '검색 결과입니다' 등의 메타 정보를 절대 포함하지 마세요.
4. **Hierarchy**: 매체명은 ## (Level 2), 기사 제목은 ### (Level 3) 헤더를 사용하세요.
5. **Style**: 한국어 3줄 요약(평어체 리스트) + [원문 링크] 구조를 필수로 유지하세요.
6. **Audience**: 모든 내용은 베트남 거주 한국인을 대상으로 친절하고 명확하게 요약하세요.

**TTS(음성 합성) 최적화 가이드:**
- 에모지 및 특수 문자(°C, % 등) 사용 절대 금지.
- 괄호 안의 영어 표기 제거 및 순수 한국어 독음화.
- 숫자는 읽기 편하게 한글로 변환 (예: 32도, 10퍼센트).
- 문장 끝은 '입니다', '하세요' 등 정중한 구어체로 종결.
"""

def fetch_source_content(source, today_str, index, total):
    """Gemini API를 직접 호출하여 개별 소스 뉴스 수집"""
    prompt = f"매체명: {source['name']}\n\n{source['prompt']}\n대상 기준일: {today_str}{COMMON_INSTRUCTIONS}"
    
    print(f"[{index}/{total}] {source['name']} 수집 중...")
    try:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print(f"  [!] API 키가 설정되지 않았습니다.")
            return None
        
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "tools": [{"google_search": {}}]
        }
        
        response = requests.post(api_url, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            if "candidates" in result and len(result["candidates"]) > 0:
                content = result["candidates"][0]["content"]["parts"][0]["text"].strip()
                print(f"  [OK] {source['name']} 수집 완료")
                return content
            else:
                print(f"  [!] {source['name']} 응답에 내용이 없음")
                return None
        else:
            print(f"  [!] {source['name']} API 오류: {response.status_code}")
            error_detail = response.json() if response.text else {}
            print(f"  [ERROR]: {error_detail}")
            return None
    except requests.Timeout:
        print(f"  [!] {source['name']} 응답 시간 초과 (30s)")
        return None
    except Exception as e:
        print(f"  [!] {source['name']} 수집 중 예외 발생: {str(e)}")
        return None

def check_gemini_health():
    """Gemini API 상태 점검 (직접 API 호출)"""
    print("\n[*] Gemini API 사전 점검 중...")
    try:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("  [!] API 키가 없습니다.")
            return False
        
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={api_key}"
        payload = {"contents": [{"parts": [{"text": "1+1"}]}]}
        
        response = requests.post(api_url, json=payload, timeout=10)
        
        if response.status_code == 200 and '"text":' in response.text:
            print("  [OK] Gemini API 정상 동작 확인")
            return True
        else:
            print("  [!] Gemini API 점검 실패")
            if response.text:
                error = response.json() if response.text else {}
                print(f"  [ERROR]: {error}")
            return False
    except requests.Timeout:
        print("  [!] Gemini API 응답 시간 초과 (Timeout)")
        return False
    except Exception as e:
        print(f"  [!] Gemini API 점검 중 예외 발생: {str(e)}")
        return False


def fetch_all_news():
    """모든 소스를 순회하며 뉴스 통합 수집"""
    now = datetime.datetime.now()
    yymmdd_hhmm = now.strftime("%y%m%d-%H%M")
    today_display = now.strftime("%Y년 %m월 %d일 %H:%M")
    output_path = f"data/{yymmdd_hhmm}.md"

    if not os.path.exists("data"):
        os.makedirs("data")

    # 0. 사전 점검 (Health Check)
    if not check_gemini_health():
        print("[!] Gemini API 상태가 좋지 않아 수집을 중단합니다.")
        return False

    # 우선순위별 정렬 (P0 → P1 → P2)
    sorted_sources = sorted(SOURCES, key=lambda x: x['priority'])
    total_sources = len(sorted_sources)
    
    print(f"\n[*] {today_display} 베트남 뉴스 통합 수집 시작 (총 {total_sources}개 소스)")
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
