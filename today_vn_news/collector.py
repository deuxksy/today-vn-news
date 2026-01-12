#!/usr/bin/env python3
from google import genai
from google.genai import types
import datetime
import os
import sys
import yaml

"""
베트남 뉴스 및 안전 정보 통합 수집 모듈 (Google GenAI SDK)
- 목적: Google GenAI SDK를 사용하여 안전/기상 정보 및 주요 뉴스 수집
- 대상 청중: 베트남 거주 한국인
- 출력 형식: YAML (data/YYYYMMDD_HHMM.yaml)
- 상세 사양: ContextFile.md 4장 참조
"""


# 수집 대상 정의 (ContextFile.md 규격 준수)
# 대상 청중: 베트남 거주 한국인
SOURCES = [
    # === Critical (P0): 안전 및 기상 관제 ===
    {
        "id": "1",
        "name": "안전 및 기상 관제",
        "priority": "P0",
        "prompt": (
            "NCHMF(국립기상예보센터), IGP-VAST(지질연구소), IQAir(Saigon Pearl, Ho Chi Minh City) 정보를 바탕으로 호치민 지역의 오늘 안전 및 기상 정보를 YAML 형식으로 제공해줘.\\n"
            "\\n"
            "**데이터 소스**\\n"
            "- 공기질: https://www.iqair.com/vietnam/ho-chi-minh-city/ho-chi-minh-city/iqair-vietnam-saigon-pearl\\n"
            "- 기상: NCHMF\\n"
            "- 지진: IGP-VAST\\n"
            "\\n"
            "**긴급 특보 (Conditional)**\\n"
            "- 태풍, 지진, 홍수, 대형 화재 발생 시에만 '재난' 또는 '지진' 항목을 생성하세요. (발생하지 않을 경우 **절대** 포함하지 마세요)\\n"
            "\\n"
            "**상시 관제 (Always)**\\n"
            "- 위치: 호치민 사이공 펄(Saigon Pearl) 인근\\n"
            "- 날씨: 기온(최저/최고, 반드시 섭씨), 습도, 강수 확률\\n"
            "- 공기질: AQI 지수, PM2.5, PM10\\n"
            "\\n"
            "**행동 지침**\\n"
            "- AQI 100 초과 시: '공기질이 나쁩니다. 마스크를 반드시 착용하고 실외 활동을 자제하십시오.' 문구 포함\\n"
            "- 강수 확률 70% 이상 시: '비 예보가 있습니다. 이동 시 우산을 준비하십시오.' 문구 포함\\n"
            "\\n"
            "**YAML 출력 형식 (필수)**:\\n"
            "items:\\n"
            "  - name: 기상\\n"
            "    source: NCHMF\\n"
            "    temp: (온도, 예: 28도)\\n"
            "    humidity: (습도, 예: 66퍼센트)\\n"
            "    rain_chance: (강수확률, 예: 10퍼센트)\\n"
            "    content: (행동지침)\\n"
            "    url: (출처 URL)\\n"
            "  - name: 공기\\n"
            "    source: IQAir (Saigon Pearl)\\n"
            "    aqi: (AQI 수치)\\n"
            "    status: (상태)\\n"
            "    pm25: (PM2.5 수치)\\n"
            "    pm10: (PM10 수치)\\n"
            "    content: (행동지침)\\n"
            "    url: https://www.iqair.com/vietnam/ho-chi-minh-city/ho-chi-minh-city/iqair-vietnam-saigon-pearl\\n"
            "\\n"
            "**중요**: 지진이나 재난 정보는 발생 시에만 items 리스트 맨 앞에 추가하세요. 모든 온도는 섭씨(도)로, 퍼센트는 '퍼센트'로 표기하세요. YAML 형식만 출력하고 다른 설명은 하지 마세요."
        )
    },
    
    # === High (P1): 정부 공식 입장 ===
    {
        "id": "2",
        "name": "Nhân Dân (정부 기관지)",
        "priority": "P1",
        "prompt": (
            "https://nhandan.vn/ 에서 반드시 **아래 지정된 기준일(Target Date)에 발행된** 베트남 공산당 및 정부의 공식 입장, 신규 법령, 행정 절차(비자, 거주증) 정보를 수집하여 한국어로 번역 및 요약한 YAML 형식으로 제공해줘.\\n"
            "- **검증 규칙**: 반드시 지정된 기준일 당일의 기사만 수집하세요. 기준일 이전 기사는 절대 포함하지 마세요.\\n"
            "- 규칙: 당일 발표된 신규 정책 또는 행정 공고 **2개** 수집\\n"
            "- 우선순위: 한국인에게 영향을 줄 수 있는 정보 (비자, 거주증 등)\\n"
            "- **번역 지침**: 제목과 내용은 자연스러운 한국어 문어체로 번역하고, 복잡한 관공서 명칭은 한국어로 이해하기 쉽게 정제하세요.\\n"
            "\\n"
            "**YAML 출력 형식 (필수)**:\\n"
            "items:\\n"
            "  - title: (한국어 번역된 기사 제목)\\n"
            "    content: (한국어 번역된 3줄 요약)\\n"
            "    url: (원문 링크)\\n"
            "\\n"
            "**중요**: YAML 형식만 출력하고 다른 설명은 하지 마세요. 당일 발행된 기사가 없으면 빈 배열 'items: []'을 반환하세요."
        )
    },
    
    # === Critical (P0): 건강/위생 ===
    {
        "id": "3",
        "name": "Sức khỏe & Đời sống (보건부 관보)",
        "priority": "P0",
        "prompt": (
            "https://suckhoedoisong.vn/ 에서 반드시 **아래 지정된 기준일(Target Date)에 발행된** 오늘의 식품 위생 위반, 알레르기 유발 정보, 질병 주의보를 수집하여 한국어로 번역 및 요약한 YAML 형식으로 제공해줘.\\n"
            "- **검증 규칙**: 반드시 지정된 기준일 당일의 기사만 수집하세요. 기준일 이전 기사는 절대 포함하지 마세요.\\n"
            "- 규칙: 식중독 사례, 호치민 대기질 악화, 전염병 정보 등 **건강 관련 이슈 전수 수집**\\n"
            "- 번역 지침: 모든 의학 용어 및 질병 명칭을 정확한 한국어 명칭(예: 궤양성 대장염 등)으로 번역하고, 한국인이 듣기에 어색하지 않은 존댓말(또는 문어체)을 사용하세요.\\n"
            "- 특별 강조: 궤양성 대장염, 알레르기 관련 정보가 있으면 우선 포함\\n"
            "\\n"
            "**YAML 출력 형식 (필수)**:\\n"
            "items:\\n"
            "  - title: (한국어 번역된 기사 제목)\\n"
            "    content: (한국어 번역된 3줄 요약)\\n"
            "    url: (원문 링크)\\n"
            "    note: (선택사항, 특이사항 있을 경우)\\n"
            "\\n"
            "**중요**: YAML 형식만 출력하고 다른 설명은 하지 마세요. 당일 발행된 기사가 없으면 빈 배열 'items: []'을 반환하세요."
        )
    },
    
    # === Normal (P2): 로컬/시정 ===
    {
        "id": "4",
        "name": "Tuổi Trẻ (호치민 로컬)",
        "priority": "P2",
        "prompt": (
            "https://tuoitre.vn/ 에서 반드시 **아래 지정된 기준일(Target Date)에 발행된** 호치민(HCMC) 중심의 시정 소식 및 주요 도로 통제 이벤트를 수집하여 한국어로 번역 및 요약한 YAML 형식으로 제공해줘.\\n"
            "- **검증 규칙**: 반드시 지정된 기준일 당일의 기사만 수집하세요. 기준일 이전 기사는 절대 포함하지 마세요.\\n"
            "- 규칙: 최신 기사 **2개** 수집\\n"
            "- 번역 지침: 베트남어 지명(군, 거리명)을 한국어 독음(예: 1군, 레로이 거리)으로 변환하고, 시정 소식을 한국 독자가 이해하기 쉽게 풀어서 번역하세요.\\n"
            "- 우선순위: 교통 통제, 주요 이벤트, 한국인 거주 지역(2군, 7군 등) 관련 뉴스\\n"
            "\\n"
            "**YAML 출력 형식 (필수)**:\\n"
            "items:\\n"
            "  - title: (한국어 번역된 기사 제목)\\n"
            "    content: (한국어 번역된 3줄 요약)\\n"
            "    url: (원문 링크)\\n"
            "\\n"
            "**중요**: YAML 형식만 출력하고 다른 설명은 하지 마세요. 당일 발행된 기사가 없으면 빈 배열 'items: []'을 반환하세요."
        )
    }
]


def fetch_source_content(client, source, today_str, index, total):
    """Google GenAI SDK를 사용하여 개별 소스 뉴스 수집 (YAML 형식)"""
    prompt = f"{source['prompt']}\\n대상 기준일: {today_str}"
    
    print(f"[{index}/{total}] {source['name']} 수집 중...")
    try:
        response = client.models.generate_content(
            model="gemma-3-27b-it",
            contents=prompt
        )
        
        if response.text:
            content = response.text.strip()
            print(f"  [OK] {source['name']} 수집 완료")
            return content
        else:
            print(f"  [!] {source['name']} 응답에 내용이 없음")
            return None
            
    except Exception as e:
        print(f"  [!] {source['name']} 수집 중 예외 발생: {str(e)}")
        return None


def check_gemini_health(client):
    """GenAI SDK 상태 점검"""
    print("\\n[*] GenAI SDK 사전 점검 중...")
    try:
        response = client.models.generate_content(
            model="gemma-3-27b-it",
            contents="1+1"
        )
        
        if response.text:
            print("  [OK] GenAI SDK 정상 동작 확인")
            return True
        else:
            print("  [!] GenAI SDK 점검 실패")
            return False
    except Exception as e:
        print(f"  [!] GenAI SDK 점검 중 예외 발생: {str(e)}")
        return False


def fetch_all_news(base_name: str = None):
    """모든 소스를 순회하며 뉴스 통합 수집 (YAML 출력)"""
    now = datetime.datetime.now()
    yymmdd_hhmm = base_name if base_name else now.strftime("%Y%m%d_%H%M")
    today_display = now.strftime("%Y년 %m월 %d일 %H:%M")
    output_path = f"data/{yymmdd_hhmm}.yaml"

    if not os.path.exists("data"):
        os.makedirs("data")

    # GenAI 클라이언트 초기화
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("[!] API 키가 설정되지 않았습니다. GEMINI_API_KEY 또는 GOOGLE_API_KEY 환경 변수를 확인하세요.")
        return False
    
    client = genai.Client(api_key=api_key)

    # 0. 사전 점검 (Health Check)
    if not check_gemini_health(client):
        print("[!] GenAI SDK 상태가 좋지 않아 수집을 중단합니다.")
        return False

    # 우선순위별 정렬 (P0 → P1 → P2)
    sorted_sources = sorted(SOURCES, key=lambda x: x['priority'])
    total_sources = len(sorted_sources)
    
    print(f"\\n[*] {today_display} 베트남 뉴스 통합 수집 시작 (총 {total_sources}개 소스)")
    print("-" * 50)
    
    # YAML 구조 생성
    yaml_data = {
        "metadata": {
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M"),
            "location": "Ho Chi Minh City (Landmark 81)"
        },
        "sections": []
    }
    
    collected_count = 0
    
    for i, src in enumerate(sorted_sources, 1):
        content = fetch_source_content(client, src, today_display, i, total_sources)
        if content:
            # YAML 파싱 시도
            try:
                # 마크다운 코드 블록 제거
                if "```yaml" in content:
                    content = content.split("```yaml")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                parsed_yaml = yaml.safe_load(content)
                
                section = {
                    "id": src["id"],
                    "name": src["name"],
                    "priority": src["priority"],
                }
                
                # items 키가 있으면 추가
                if isinstance(parsed_yaml, dict) and "items" in parsed_yaml:
                    section["items"] = parsed_yaml["items"]
                elif isinstance(parsed_yaml, list):
                    section["items"] = parsed_yaml
                else:
                    section["items"] = []
                
                yaml_data["sections"].append(section)
                collected_count += 1
                
            except yaml.YAMLError as e:
                print(f"  [!] {src['name']} YAML 파싱 실패: {e}")
                print(f"  [RAW]: {content[:200]}...")
                # 파싱 실패 시에도 원본 텍스트로 저장
                section = {
                    "id": src["id"],
                    "name": src["name"],
                    "priority": src["priority"],
                    "raw_content": content
                }
                yaml_data["sections"].append(section)
                collected_count += 1
    
    print("-" * 50)
    if collected_count == 0:
        print("[!] 수집된 뉴스가 전혀 없습니다. 네트워크 상태나 API 키를 확인하세요.")
        return False

    # YAML 파일로 저장
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(yaml_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print(f"[+] 통합 뉴스 리포트 생성 완료: {output_path} (수집 성공: {collected_count}/{total_sources})")
    return True


# 진입점 호환성 유지
def fetch_it_news():
    return fetch_all_news()


if __name__ == "__main__":
    fetch_all_news()
