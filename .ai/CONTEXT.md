# ContextFile: today-vn-news

본 문서는 프로젝트 'today-vn-news'의 도메인 지식, 비즈니스 로직 및 기술적 제약 사항을 정의한다.

## 1. 비즈니스 도메인 및 데이터 소스

### 1.1 데이터 원천

- 웹 스크래핑을 수행하여 원천 데이터를 YAML 파일로 저장하고, Gemma-3-27b-it을 통해 한국어 번역 및 요약한다.

### 1.2 주요 안전 및 기상정보 소스

- [베트남 기상철](https://nchmf.gov.vn/kttv/): 태풍, 지진, 홍수 정보와 현재 날씨 정보
- [베트남 지구물리학 연구소](http://igp-vast.vn/index.php/vi/tin-dong-dat): 지진 정보 (RSS 피드)
- IQAir + Open-Meteo: 공기질 정보 (AQI, PM2.5, PM10)
- [베트남 공기질 정부포탈](https://cem.gov.vn/)

### 1.3 주요 뉴스 소스

- Nhân Dân: 베트남 공산당 중앙위원회의 공식 기관지
- Sức khỏe & Đời sống: 베트남 보건부 공식 기관지
- Tuổi Trẻ: 호치민시 주요 뉴스 매체

## 2 대상 청중 (Target Audience)

- **주요 타겟:** 베트남에 거주하거나 베트남 소식에 관심이 있는 **한국인** 또는 **한국어**를 사용하는 사람.
- **콘텐츠 원칙:** 모든 정보는 한국인의 시각에서 유용해야 하며, 번역 및 요약 톤앤매너는 한국어 사용자의 정서와 가독성을 최우선으로 한다.

## 3. 기술 스펙 (Distributed Infrastructure)

### 3.1 핵심 기술 스택

- **Language:** Python 3.13+
- **Translation:** Gemma-3-27b-it (google-genai SDK)
- **TTS:** edge-tts
- **Video:** FFmpeg (VideoToolbox/VAAPI 하드웨어 가속)

## 4. 데이터 수집 (scraper.py) 세부 명세

**핵심 변경점 (v0.6.2)**: 모든 데이터는 **YAML** 구조로 저장되며, `scraper.py`는 `google-genai` SDK를 사용합니다.
모든 데이터는 Gemma-3-27b-it을 통해 정제되며, **TTS 최적화(특수문자/영어 제거)**를 거쳐 `data/` 폴더의 YAML 파일에 저장 됩니다.

### 4.1 안전 및 기상 관제

- **목적:** 실시간 기상 특보 및 공기질 데이터 제공을 통한 사용자 신체 안전 및 컨디션 관리 지원.
- **데이터 소스:** NCHMF(국립기상예보센터), IGP-VAST(지질연구소 RSS 피드), IQAir API + Open-Meteo API(혼합).
- **배타적 데이터 수집 원칙:** 재난, 안전, 날씨 정보는 여기서만 수집합니다.
- **데이터 수집 로직:**
  - **긴급 특보 (Conditional):** 태풍, 지진, 홍수, 대형 화재 발생 시 `🚨 [긴급 특보]` 섹션 생성 (발생하지 않을 경우 생략).
  - **상시 관제 (Always):**
    - **날씨:** 기온(최저/최고), 습도, 강수 확률 (호치민 랜드마크 81 인근 기준).
    - **공기질:** AQI 지수(미국 기준), PM2.5, PM10.
- **공기질 데이터 소스 상세:**
  - **IQAir API**: AQI(미국 기준) 실시간 데이터, 관측소 위치 Quan Mot (10.78069, 106.69944)
  - **Open-Meteo API**: PM2.5, PM10 미세먼지 농도 (µg/m³)
- **지진 정보:**
  - **IGP-VAST RSS 피드**: 당일 발생 지진만 필터링 (http://igp-vast.vn/index.php/en/earthquake-news?format=feed)
- **출력 및 행동 지침:**
  - AQI 100 초과 시: "공기질이 나쁩니다. 마스크를 반드시 착용하고 실외 활동을 자제하십시오." 문구 자동 삽입.
  - 강수 확률 70% 이상 시: "비 예보가 있습니다. 이동 시 우산을 준비하십시오." 문구 삽입.
- **TTS 최적화 (Critical):**
  - **정제:** 에모지, 특수 기호(°C, % 등), 괄호 안의 영어(Ho Chi Minh) 제거.
  - **변환:** 32°C → '32도', 80% → '80퍼센트' 등 음독 처리 (Gemma 프롬프트에서 강제).
- **가중치**: Critical (P0)

### 4.2 Nhân Dân

- **목적:** 베트남 공산당 및 정부의 공식 입장, 신규 법령, 행정 절차(비자, 거주증) 정보 수집.
- **데이터 소스:** [Nhân Dân](https://nhandan.vn/)
- **배타적 데이터 수집 원칙:** 신규 법령, 행정 공고, 비자 관련 정보는 여기서만 수집합니다.
- **추출 규칙:** 당일 발표된 신규 정책 또는 행정 공고 2개.
- **TTS 최적화:** 부서명 및 직함 등 복잡한 한자어 명칭을 명확한 한글 발음으로 정제.
- **가중치**: High (P1)

### 4.3 Sức khỏe & Đời sống

- **목적:** **[통합 안전 관제 핵심]** 보건부 산하 매체로 식품 위생 위반 사례, 알레르기 유발 정보, 질병 주의보 수집.
- **데이터 소스:** [Sức khỏe & Đời sống](https://suckhoedoisong.vn/page-rss.htm)
  - **의료** : <https://suckhoedoisong.vn/y-te.rss>
- **배타적 데이터 수집 원칙:** 식중독 사례, 호치민 대기질 악화, 전염병 정보 등 건강 관련 이슈 전수 수집.
- **추출 규칙:** 식중독 사례, 호치민 대기질 악화, 전염병 정보 등 **건강 관련 이슈 전수 수집**.
- **TTS 최적화:** '궤양성 대장염' 등 사용자 맞춤형 키워드 강조, 의학 전문 용어 순화.
- **가중치**: Critical (P0)

### 4.4 Tuổi Trẻ

- **목적:** 호치민(HCMC) 중심의 시정 소식, 주요 도로 통제 이벤트 수집.
- **데이터 소스:** [Tuổi Trẻ](https://tuoitre.vn/rss.htm)
- **배타적 데이터 수집 원칙:** 호치민(HCMC) 중심의 시정 소식, 주요 도로 통제 이벤트 수집.
- **추출 규칙:** 최신 기사 2개.
- **TTS 최적화:** 베트남어 성조가 포함된 거리명 등을 한국어 독음으로 변환 (예: Quận 1 -> 1군).
- **가중치**: Normal (P2)

### 4.5 VietnamNet (종합 뉴스)

- **목적:** 정보통신부 산하 매체 종합 뉴스 포털로서 B2G 기반의 뉴스 수집.
- **데이터 소스:** 
  - **정치**: <https://vietnamnet.vn/rss/chinh-tri.rss>
  - **법률**: <https://vietnamnet.vn/rss/phap-luat.rss>
  - **시사**: <https://vietnamnet.vn/rss/thoi-su.rss>
- **추출 규칙:** 정치,법률,시사 카테고리 우선 필터링하여 메인 이슈 2개 수집.
- **TTS 최적화:** 기사 서두의 지역명(예: 하노이, 호치민) 및 날짜 정보 간소화.
- **가중치**: Normal (P2)

### 4.6 VnExpress (종합 뉴스)

- **목적:** 베트남 최대 뉴스 포털로서 B2C 기반의 뉴스 수집.
- **데이터 소스:** [VNEXPRESS](https://vnexpress.net/rss)
  - **경제**: <https://vnexpress.net/rss/kinh-doanh.rss>
  - **호치민시보**: <https://vnexpress.net/rss/thoi-su.rss>
  - **자동차**: <https://vnexpress.net/rss/oto-xe-may.rss>
  - **부동산**: <https://vnexpress.net/rss/bat-dong-san.rss>
- **추출 규칙:** 경제, 자동차, 부동산, 비즈니스 카테고리 우선 필터링하여 메인 이슈 2개 수집.
- **TTS 최적화:** 기사 서두의 지역명(예: 하노이, 호치민) 및 날짜 정보 간소화.
- **가중치**: Normal (P2)

### 4.7 Thanh Niên (사회/청년)

- **목적:** 대중적 관심사가 높은 트렌드, 사회 현상 및 독자 제보 뉴스 수집.
- **데이터 소스:** [Thanh Niên](https://thanhnien.vn/rss.html)
  - **민생/시사**: <https://thanhnien.vn/rss/thoi-su.rss>
  - **생활**: <https://thanhnien.vn/rss/doi-song.rss>
- **추출 규칙:** 카테고리별 RSS 피드 파싱 (민생/시사, 생활), 메인 이슈 2개 수집.
- **TTS 최적화:** 불필요한 수식어 및 자극적인 문장 부호(!!!, ???) 제거.
- **가중치**: Normal (P2)

### 4.8 The Saigon Times (경제)

- **목적:** 경제 전문지로 환율, 물가, 호치민 부동산 및 투자 동향 수집.
- **데이터 소스:** [The Saigon Times](https://thesaigontimes.vn/)
- **추출 규칙:** 카테고리 필터링 없이 최신 기사 2개 수집.
- **TTS 최적화:** 통화 단위(VND, USD) 및 퍼센트(%) 단위를 한국어 읽기 방식으로 교정.
- **가중치**: Normal (P2)

### 4.9 VietnamNet 정보통신

- **목적:** 베트남 정보통신 산업 동향, 5G/4G 통신망 확장, 통신 정책 수집.
- **데이터 소스:** [VietnamNet - Thông tin và Truyền thông](https://vietnamnet.vn/rss/thong-tin-truyen-thong.rss)
- **추출 규칙:** 통신 관련 정책, 인터넷 서비스, 모바일 통신 관련 뉴스 2개.
- **TTS 최적화:** 영어 약어는 그대로 사용합니다 (5G, 4G, 3G, AI, API 등).
- **가중치**: Normal (P2)

### 4.10 VnExpress IT/과학

- **목적:** 베트남 IT 산업 동향, AI, Cloud 도입 현황 수집.
- **데이터 소스:** [VnExpress Khoa học công nghệ](https://vnexpress.net/rss/khoa-hoc-cong-nghe.rss)
- **추출 규칙:** 기술 트렌드 및 엔지니어 채용 관련 이슈 2개.
- **TTS 최적화:** 영어 약어는 그대로 사용합니다 (AWS, SaaS, AI, API 등).
- **가중치**: Normal (P2)

## 5. TTS 변환

tts 변환 시 한국어를 가능한 사람이 청취한다는 점을 고려합니다.

## 6. 영상 생성

## 7. 업로드
