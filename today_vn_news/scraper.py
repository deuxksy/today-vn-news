#!/usr/bin/env python3
"""
웹 스크래핑 모듈 (BeautifulSoup4 기반)
- 목적: 뉴스 사이트에서 당일 기사 직접 수집
- 대상: Nhân Dân, Sức khỏe & Đời sống, Tuổi Trẻ
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re
import xml.etree.ElementTree as ET


def scrape_nhandan(date_str: str) -> List[Dict[str, str]]:
    """
    Nhân Dân(정부 기관지) 스크래핑

    Args:
        date_str: 기준일 (YYYY-MM-DD 형식)

    Returns:
        기사 리스트 [{'title': str, 'content': str, 'url': str, 'date': str}]
    """
    print(f"[스크래핑] Nhân Dân 수집 중...")

    url = "https://nhandan.vn/"
    articles = []

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # 오늘 날짜 형식 (예: 09/02/2025)
        today_pattern = (
            date_str.split("-")[2]
            + "/"
            + date_str.split("-")[1]
            + "/"
            + date_str.split("-")[0]
        )

        # 기사 리스트 찾기
        article_elements = (
            soup.find_all("article", class_="news-item")
            or soup.find_all("div", class_="article")
            or soup.select(".article-content, .news-list article")
        )

        for article in article_elements[:5]:  # 최대 5개 기사 체크
            # 링크 찾기
            link_tag = article.find("a")
            if not link_tag:
                continue

            article_url = link_tag.get("href", "")
            if not article_url.startswith("http"):
                article_url = "https://nhandan.vn" + article_url

            # 제목 찾기
            title_tag = article.find(["h2", "h3", "h4"])
            title = title_tag.get_text(strip=True) if title_tag else ""

            # 날짜 찾기
            date_tag = (
                article.find("time")
                or article.find("span", class_="date")
                or article.find("div", class_="article-date")
            )
            article_date = date_tag.get_text(strip=True) if date_tag else ""

            # 오늘 날짜가 포함되어 있는지 확인
            if today_pattern in article_date:
                # 본문 미리보기 요약
                summary_tag = article.find("p", class_="sapo") or article.find(
                    "div", class_="summary"
                )
                content = summary_tag.get_text(strip=True) if summary_tag else title

                articles.append(
                    {
                        "title": title,
                        "content": content[:200],  # 200자 제한
                        "url": article_url,
                        "date": article_date,
                    }
                )

        print(f"  [OK] Nhân Dân: {len(articles)}개 기사 수집")
        return articles

    except Exception as e:
        print(f"  [!] Nhân Dân 스크래핑 실패: {str(e)}")
        return []


def scrape_suckhoedoisong(date_str: str) -> List[Dict[str, str]]:
    """
    Sức khỏe & Đời sống(보건부 관보) 스크래핑

    Args:
        date_str: 기준일 (YYYY-MM-DD 형식)

    Returns:
        기사 리스트 [{'title': str, 'content': str, 'url': str, 'date': str}]
    """
    print(f"[스크래핑] Sức khỏe & Đời sống 수집 중...")

    url = "https://suckhoedoisong.vn/"
    articles = []

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # 오늘 날짜 형식 (베트남어)
        today_pattern = (
            date_str.split("-")[2]
            + "/"
            + date_str.split("-")[1]
            + "/"
            + date_str.split("-")[0]
        )

        # 기사 리스트 찾기
        article_elements = soup.find_all("article") or soup.select(
            ".news-item, .article-item"
        )

        for article in article_elements[:5]:  # 최대 5개 기사 체크
            # 링크 찾기
            link_tag = article.find("a")
            if not link_tag:
                continue

            article_url = link_tag.get("href", "")
            if not article_url.startswith("http"):
                article_url = "https://suckhoedoisong.vn" + article_url

            # 제목 찾기
            title_tag = article.find(["h2", "h3", "h4"])
            title = title_tag.get_text(strip=True) if title_tag else ""

            # 날짜 찾기
            date_tag = (
                article.find("time")
                or article.find("span", class_="date")
                or article.find("div", class_="article-date")
            )
            article_date = date_tag.get_text(strip=True) if date_tag else ""

            # 오늘 날짜가 포함되어 있는지 확인
            if (
                today_pattern in article_date or not article_date
            ):  # 날짜가 없으면 최신 기사로 간주
                # 본문 미리보기 요약
                summary_tag = article.find("p", class_="sapo") or article.find(
                    "div", class_="summary"
                )
                content = summary_tag.get_text(strip=True) if summary_tag else title

                articles.append(
                    {
                        "title": title,
                        "content": content[:200],  # 200자 제한
                        "url": article_url,
                        "date": article_date,
                    }
                )

        print(f"  [OK] Sức khỏe & Đời sống: {len(articles)}개 기사 수집")
        return articles

    except Exception as e:
        print(f"  [!] Sức khỏe & Đời sống 스크래핑 실패: {str(e)}")
        return []


def scrape_tuoitre(date_str: str) -> List[Dict[str, str]]:
    """
    Tuổi Trẻ(호치민 로컬) 스크래핑

    Args:
        date_str: 기준일 (YYYY-MM-DD 형식)

    Returns:
        기사 리스트 [{'title': str, 'content': str, 'url': str, 'date': str}]
    """
    print(f"[스크래핑] Tuổi Trẻ 수집 중...")

    url = "https://tuoitre.vn/"
    articles = []

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # 오늘 날짜 형식
        today_pattern = (
            date_str.split("-")[2]
            + "/"
            + date_str.split("-")[1]
            + "/"
            + date_str.split("-")[0]
        )

        # 기사 리스트 찾기
        article_elements = soup.find_all("article") or soup.select(
            ".news-item, .article-item"
        )

        for article in article_elements[:5]:  # 최대 5개 기사 체크
            # 링크 찾기
            link_tag = article.find("a")
            if not link_tag:
                continue

            article_url = link_tag.get("href", "")
            if not article_url.startswith("http"):
                article_url = "https://tuoitre.vn" + article_url

            # 제목 찾기
            title_tag = article.find(["h2", "h3", "h4"])
            title = title_tag.get_text(strip=True) if title_tag else ""

            # 날짜 찾기
            date_tag = (
                article.find("time")
                or article.find("span", class_="date")
                or article.find("div", class_="article-date")
            )
            article_date = date_tag.get_text(strip=True) if date_tag else ""

            # 오늘 날짜가 포함되어 있는지 확인
            if (
                today_pattern in article_date or not article_date
            ):  # 날짜가 없으면 최신 기사로 간주
                # 본문 미리보기 요약
                summary_tag = article.find("p", class_="sapo") or article.find(
                    "div", class_="summary"
                )
                content = summary_tag.get_text(strip=True) if summary_tag else title

                articles.append(
                    {
                        "title": title,
                        "content": content[:200],  # 200자 제한
                        "url": article_url,
                        "date": article_date,
                    }
                )

        print(f"  [OK] Tuổi Trẻ: {len(articles)}개 기사 수집")
        return articles

    except Exception as e:
        print(f"  [!] Tuổi Trẻ 스크래핑 실패: {str(e)}")
        return []


def scrape_vietnamnet(date_str: str) -> List[Dict[str, str]]:
    """
    VietnamNet(종합 뉴스) 스크래핑
    - 시사, 뉴스, 경제, 비즈니스 카테고리 우선 필터링
    - 기술, 건강 카테고리 제외

    Args:
        date_str: 기준일 (YYYY-MM-DD 형식)

    Returns:
        기사 리스트 [{'title': str, 'content': str, 'url': str, 'date': str}]
    """
    print(f"[스크래핑] VietnamNet 종합 뉴스 수집 중...")

    url = "https://vietnamnet.vn/"
    articles = []

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # 오늘 날짜 형식
        today_pattern = (
            date_str.split("-")[2]
            + "/"
            + date_str.split("-")[1]
            + "/"
            + date_str.split("-")[0]
        )

        # 카테고리 필터링 설정
        # 카테고리 필터링 (베트남 시사/경제/재무만 수집)
        priority_categories = [
            "/thoi-su/",  # 시사
            "/kinh-doanh/",  # 경제/비즈니스
            "/tai-chinh/",  # 재무/경제
        ]

        # 기사 리스트 찾기
        article_elements = soup.find_all("article") or soup.select(
            ".news-item, .article-item, .story"
        )

        for article in article_elements[:10]:  # 최대 10개 체크 후 필터링
            # 링크 찾기
            link_tag = article.find("a")
            if not link_tag:
                continue

            article_url = link_tag.get("href", "")
            if not article_url.startswith("http"):
                article_url = "https://vietnamnet.vn" + article_url

            # 카테고리 필터링 (시사/경제/재무만 수집)
            in_priority = any(cat in article_url for cat in priority_categories)

            if not in_priority:
                continue

            # 제목 찾기
            title_tag = article.find(["h2", "h3", "h4"])
            title = title_tag.get_text(strip=True) if title_tag else ""

            # 날짜 찾기
            date_tag = (
                article.find("time")
                or article.find("span", class_="date")
                or article.find("div", class_="article-date")
            )
            article_date = date_tag.get_text(strip=True) if date_tag else ""

            # 오늘 날짜가 포함되어 있는지 확인
            if (
                today_pattern in article_date or not article_date
            ):  # 날짜가 없으면 최신 기사로 간주
                # 본문 미리보기 요약
                summary_tag = article.find("p", class_="sapo") or article.find(
                    "div", class_="summary"
                )
                content = summary_tag.get_text(strip=True) if summary_tag else title

                articles.append(
                    {
                        "title": title,
                        "content": content[:200],  # 200자 제한
                        "url": article_url,
                        "date": article_date,
                    }
                )

                if len(articles) >= 2:  # 최대 2개 제한
                    break

        print(f"  [OK] VietnamNet 종합 뉴스: {len(articles)}개 기사 수집")
        return articles

    except Exception as e:
        print(f"  [!] VietnamNet 종합 뉴스 스크래핑 실패: {str(e)}")
        return []


def scrape_vnexpress(date_str: str) -> List[Dict[str, str]]:
    """
    VnExpress(종합 뉴스) 스크래핑
    - 시사, 뉴스, 경제, 비즈니스 카테고리 우선 필터링
    - 기술, 건강 카테고리 제외

    Args:
        date_str: 기준일 (YYYY-MM-DD 형식)

    Returns:
        기사 리스트 [{'title': str, 'content': str, 'url': str, 'date': str}]
    """
    print(f"[스크래핑] VnExpress 수집 중...")

    url = "https://vnexpress.net/"
    articles = []

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # 오늘 날짜 형식
        today_pattern = (
            date_str.split("-")[2]
            + "/"
            + date_str.split("-")[1]
            + "/"
            + date_str.split("-")[0]
        )

        # 카테고리 필터링 (베트남 시사/경제만 수집)
        priority_categories = [
            "/thoi-su/",  # 시사
            "/kinh-doanh/",  # 경제/비즈니스
        ]

        # 기사 리스트 찾기 (VnExpress 구조)
        article_elements = soup.find_all("article") or soup.select(
            ".article-item, .news-item"
        )

        for article in article_elements[:10]:  # 최대 10개 체크 후 필터링
            # 링크 찾기
            link_tag = article.find("a")
            if not link_tag:
                continue

            article_url = link_tag.get("href", "")
            if not article_url.startswith("http"):
                article_url = "https://vnexpress.net" + article_url

            # 카테고리 필터링 (시사/경제만 수집)
            in_priority = any(cat in article_url for cat in priority_categories)

            if not in_priority:
                continue

            # 제목 찾기
            title_tag = article.find(["h2", "h3", "h4"])
            title = title_tag.get_text(strip=True) if title_tag else ""
            # 홑따옴표 제거
            title = title.replace("'''", "").replace("'''", "")

            # 날짜 찾기
            date_tag = (
                article.find("time")
                or article.find("span", class_="date")
                or article.find("div", class_="article-date")
            )
            article_date = date_tag.get_text(strip=True) if date_tag else ""

            # 오늘 날짜가 포함되어 있는지 확인
            if (
                today_pattern in article_date or not article_date
            ):  # 날짜가 없으면 최신 기사로 간주
                # 본문 미리보기 요약
                summary_tag = article.find("p", class_="sapo") or article.find(
                    "div", class_="summary"
                )
                content = summary_tag.get_text(strip=True) if summary_tag else title
                # 홑따옴표 제거
                content = content.replace("'''", "").replace("'''", "")

                articles.append(
                    {
                        "title": title,
                        "content": content[:200],  # 200자 제한
                        "url": article_url,
                        "date": article_date,
                    }
                )

                if len(articles) >= 2:  # 최대 2개 제한
                    break

        print(f"  [OK] VnExpress: {len(articles)}개 기사 수집")
        return articles

    except Exception as e:
        print(f"  [!] VnExpress 스크래핑 실패: {str(e)}")
        return []


def scrape_weather_hochiminh() -> Dict[str, str]:
    """
    NCHMF 기상 스크래핑 (호치민 지역)

    Returns:
        기상 정보 딕셔너리 {'temp': str, 'humidity': str, 'condition': str}
    """
    print(f"[스크래핑] NCHMF 기상 정보 수집 중...")

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }

        # NCHMF 호치민 날씨 페이지
        url = "https://nchmf.gov.vn/kttvsiteE/vi-VN/1/vung-tau-tp-ho-chi-minh-w31.html"
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # 기상 데이터 추출 (explore agent 분석 기반 CSS 선택자 사용)
        temp = ""
        humidity = ""
        condition = ""

        # 디버깅: HTML 구조 확인
        print(f"  [DEBUG] NCHMF 페이지 구조 분석 중...")

        # 온도 찾기 (.text-weather-location .list-info-wt li:nth-child(1) .uk-width-3-4)
        temp_element = soup.select_one(
            ".text-weather-location .list-info-wt li:nth-child(1) .uk-width-3-4"
        )
        if temp_element:
            temp = temp_element.get_text(strip=True)
            # 불필요한 콜론 제거
            temp = temp.lstrip(":").strip()
            print(f"  [DEBUG] 온도: {temp}")

        # 날씨 상태 찾기 (.text-weather-location .list-info-wt li:nth-child(2) .uk-width-3-4)
        condition_element = soup.select_one(
            ".text-weather-location .list-info-wt li:nth-child(2) .uk-width-3-4"
        )
        if condition_element:
            condition = condition_element.get_text(strip=True)
            # 불필요한 콜론 제거
            condition = condition.lstrip(":").strip()
            print(f"  [DEBUG] 상태: {condition}")

        # 습도 찾기 (.text-weather-location .list-info-wt li:nth-child(3) .uk-width-3-4)
        humidity_element = soup.select_one(
            ".text-weather-location .list-info-wt li:nth-child(3) .uk-width-3-4"
        )
        if humidity_element:
            humidity = humidity_element.get_text(strip=True)
            # 불필요한 콜론 제거
            humidity = humidity.lstrip(":").strip()
            print(f"  [DEBUG] 습도: {humidity}")

        print(
            f"  [DEBUG] 수집된 데이터: temp={temp}, humidity={humidity}, condition={condition}"
        )
        print(f"  [OK] NCHMF 기상 정보 수집 완료")
        return {"temp": temp, "humidity": humidity, "condition": condition}

    except Exception as e:
        print(f"  [!] NCHMF 기상 정보 스크래핑 실패: {str(e)}")
        return {"temp": "", "humidity": "", "condition": ""}


def scrape_air_quality() -> Dict[str, str]:
    """
    IQAir 공기질 스크래핑 (Saigon Pearl, Ho Chi Minh City)

    Returns:
        공기질 정보 딕셔너리 {'aqi': str, 'status': str, 'pm25': str, 'pm10': str}
    """
    print(f"[스크래핑] IQAir 공기질 정보 수집 중...")

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }

        # IQAir Saigon Pearl 페이지
        url = "https://www.iqair.com/vietnam/ho-chi-minh-city/ho-chi-minh-city/iqair-vietnam-saigon-pearl"
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # 공기질 데이터 추출
        aqi = ""
        status = ""
        pm25 = ""
        pm10 = ""

        # HTML을 문자열로 변환하여 정규 표현식으로 검색
        html_content = str(soup)

        # 방법 1: 정규 표현식으로 AQI 범위 추출 (50-150)
        aqi_match = re.search(r">([5-9][0-9]|1[0-4][0-9])<", html_content)
        if aqi_match:
            aqi = aqi_match.group(1)
            print(f"  [DEBUG] AQI (정규): {aqi}")

        # 방법 2: 상태 텍스트 검색 (Good/Moderate/Unhealthy)
        status_match = re.search(
            r"(Good|Moderate|Unhealthy for Sensitive Groups|Unhealthy)", html_content
        )
        if status_match:
            status = status_match.group(1)
            print(f"  [DEBUG] 상태 (정규): {status}")

        # PM2.5: 웹페이지에서 패턴을 찾지 못함 (빈 값 처리)
        pm25 = ""

        # PM10: IQAir에서 제공하지 않음 (빈 값 처리)
        pm10 = ""

        print(f"  [OK] IQAir 공기질 정보 수집 완료: AQI={aqi}, 상태={status}")
        return {"aqi": aqi, "status": status, "pm25": pm25, "pm10": pm10}

    except Exception as e:
        print(f"  [!] IQAir 공기질 정보 스크래핑 실패: {str(e)}")
        return {"aqi": "", "status": "", "pm25": "", "pm10": ""}


def scrape_thanhnien_rss(date_str: str) -> List[Dict[str, str]]:
    """
    Thanh Niên 카테고리별 RSS 파싱 (시사, 경제, 생활)
    - 시사 (/rss/thoi-su.rss)
    - 경제 (/rss/kinh-te.rss)
    - 생활 (/rss/doi-song.rss)

    Args:
        date_str: 기준일 (YYYY-MM-DD 형식)

    Returns:
        기사 리스트 [{'title': str, 'content': str, 'url': str, 'date': str}]
    """
    print(f"[스크래핑] Thanh Niên RSS 파싱 중...")

    # RSS 피드 리스트
    rss_feeds = [
        ("시사", "https://thanhnien.vn/rss/thoi-su.rss"),
        ("경제", "https://thanhnien.vn/rss/kinh-te.rss"),
        ("생활", "https://thanhnien.vn/rss/doi-song.rss"),
    ]

    articles = []

    for category_name, rss_url in rss_feeds:
        try:
            # RSS 가져오기
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
            response = requests.get(rss_url, headers=headers, timeout=10)
            response.raise_for_status()

            # XML 파싱
            root = ET.fromstring(response.text)

            # RSS 네임스페이스
            # ElementTree는 기본적으로 네임스페이스를 처리하지 않음
            # 네임스페이스 접두사를 빈 문자열로 처리

            # channel 찾기 (전체 네임스페이스에서 검색)
            channel = None
            for child in root:
                if child.tag == "channel" or child.tag.endswith("channel"):
                    channel = child
                    break

            if channel is None:
                continue

            # items 찾기
            items = []
            for child in channel:
                if child.tag == "item" or child.tag.endswith("item"):
                    items.append(child)

            for item in items[:2]:  # 카테고리별 최대 2개
                # pubDate 찾기
                pub_date_elem = item.find(".//pubDate")
                if pub_date_elem is not None and pub_date_elem.text:
                    try:
                        # 날짜 파싱: "Tue, 10 Feb 2026 17:00:00 +0700"
                        pub_date_text = pub_date_elem.text.strip()
                        pub_date = datetime.strptime(
                            pub_date_text, "%a, %d %b %Y %H:%M:%S %z"
                        )
                        entry_date = pub_date.strftime("%Y-%m-%d")
                    except Exception as e:
                        continue
                else:
                    continue

                # 날짜 필터링
                if entry_date != date_str:
                    continue

                # title 찾기
                title_elem = item.find(".//title")
                title = title_elem.text if title_elem is not None else ""

                # link 찾기
                link_elem = item.find(".//link")
                article_url = link_elem.text if link_elem is not None else ""

                # description 찾기
                desc_elem = item.find(".//description")
                description = desc_elem.text if desc_elem is not None else ""

                # HTML 태그 제거
                content = re.sub(r"<[^>]+>", "", description).strip()
                content = content[:200]  # 200자 제한

                articles.append(
                    {
                        "title": title,
                        "content": content,
                        "url": article_url,
                        "date": entry_date,
                    }
                )

            print(f"  [OK] {category_name} RSS: {len([a for a in articles])}개 기사")

        except Exception as e:
            print(f"  [!] {category_name} RSS 파싱 실패: {str(e)}")

    print(f"  [OK] Thanh Niên RSS: 총 {len(articles)}개 기사 수집")
    return articles


def scrape_thanhnien(date_str: str) -> List[Dict[str, str]]:
    """
    Thanh Niên(사회/청년) 스크래핑 (RSS 파싱 실패 시 폴백)
    - 시사, 뉴스, 경제, 비즈니스 카테고리 우선 필터링

    Args:
        date_str: 기준일 (YYYY-MM-DD 형식)

    Returns:
        기사 리스트 [{'title': str, 'content': str, 'url': str, 'date': str}]
    """
    print(f"[스크래핑] Thanh Niên 수집 중...")

    url = "https://thanhnien.vn/"
    articles = []

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # 오늘 날짜 형식
        today_pattern = (
            date_str.split("-")[2]
            + "/"
            + date_str.split("-")[1]
            + "/"
            + date_str.split("-")[0]
        )

        # 카테고리 필터링 설정
        # 우선 카테고리 (포함)
        priority_categories = [
            "/thoi-su/",  # 시사
            "/kinh-te/",  # 경제/비즈니스
        ]

        # 기사 리스트 찾기
        article_elements = soup.find_all("article") or soup.select(
            ".news-item, .article-item, .story"
        )

        for article in article_elements[:10]:  # 최대 10개 체크 후 필터링
            # 링크 찾기
            link_tag = article.find("a")
            if not link_tag:
                continue

            article_url = link_tag.get("href", "")
            if not article_url.startswith("http"):
                article_url = "https://thanhnien.vn" + article_url

            # 카테고리 필터링
            # 우선 카테고리가 포함된 경우만 수집
            in_priority = any(cat in article_url for cat in priority_categories)

            if not in_priority:
                # 우선 카테고리가 아니면 스킵 (우선 카테고리 우선)
                continue

            # 제목 찾기
            title_tag = article.find(["h2", "h3", "h4"])
            title = title_tag.get_text(strip=True) if title_tag else ""
            # 자극적인 문장 부호 제거 (TTS 최적화)
            title = re.sub(r"!{2,}", "!", title).replace("??", "?")

            # 날짜 찾기
            date_tag = (
                article.find("time")
                or article.find("span", class_="date")
                or article.find("div", class_="article-date")
            )
            article_date = date_tag.get_text(strip=True) if date_tag else ""

            # 오늘 날짜가 포함되어 있는지 확인
            if (
                today_pattern in article_date or not article_date
            ):  # 날짜가 없으면 최신 기사로 간주
                # 본문 미리보기 요약
                summary_tag = article.find("p", class_="sapo") or article.find(
                    "div", class_="summary"
                )
                content = summary_tag.get_text(strip=True) if summary_tag else title
                # 자극적인 문장 부호 제거 (TTS 최적화)
                content = re.sub(r"!{2,}", "!", content).replace("??", "?")

                articles.append(
                    {
                        "title": title,
                        "content": content[:200],  # 200자 제한
                        "url": article_url,
                        "date": article_date,
                    }
                )

                if len(articles) >= 2:  # 최대 2개 제한
                    break

        print(f"  [OK] Thanh Niên: {len(articles)}개 기사 수집")
        return articles

    except Exception as e:
        print(f"  [!] Thanh Niên 스크래핑 실패: {str(e)}")
        return []


def scrape_vietnamnet_ttt(date_str: str) -> List[Dict[str, str]]:
    """
    VietnamNet 정보통신(Thông tin và Truyền thông) 스크래핑

    Args:
        date_str: 기준일 (YYYY-MM-DD 형식)

    Returns:
        기사 리스트 [{'title': str, 'content': str, 'url': str, 'date': str}]
    """
    print(f"[스크래핑] VietnamNet 정보통신 수집 중...")

    url = "https://vietnamnet.vn/thong-tin-truyen-thong"
    articles = []

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # 오늘 날짜 형식
        today_pattern = (
            date_str.split("-")[2]
            + "/"
            + date_str.split("-")[1]
            + "/"
            + date_str.split("-")[0]
        )

        # 기사 리스트 찾기
        article_elements = soup.find_all("article") or soup.select(
            ".news-item, .article-item, .story"
        )

        for article in article_elements[:5]:  # 최대 5개 기사 체크
            # 링크 찾기
            link_tag = article.find("a")
            if not link_tag:
                continue

            article_url = link_tag.get("href", "")
            if not article_url.startswith("http"):
                article_url = "https://vietnamnet.vn" + article_url

            # 제목 찾기
            title_tag = article.find(["h2", "h3", "h4"])
            title = title_tag.get_text(strip=True) if title_tag else ""

            # 날짜 찾기
            date_tag = (
                article.find("time")
                or article.find("span", class_="date")
                or article.find("div", class_="article-date")
            )
            article_date = date_tag.get_text(strip=True) if date_tag else ""

            # 오늘 날짜가 포함되어 있는지 확인
            if (
                today_pattern in article_date or not article_date
            ):  # 날짜가 없으면 최신 기사로 간주
                # 본문 미리보기 요약
                summary_tag = article.find("p", class_="sapo") or article.find(
                    "div", class_="summary"
                )
                content = summary_tag.get_text(strip=True) if summary_tag else title

                articles.append(
                    {
                        "title": title,
                        "content": content[:200],  # 200자 제한
                        "url": article_url,
                        "date": article_date,
                    }
                )

                if len(articles) >= 2:  # 최대 2개 제한
                    break

        print(f"  [OK] VietnamNet 정보통신: {len(articles)}개 기사 수집")
        return articles

    except Exception as e:
        print(f"  [!] VietnamNet 정보통신 스크래핑 실패: {str(e)}")
        return []


def scrape_vnexpress_tech(date_str: str) -> List[Dict[str, str]]:
    """
    VnExpress IT/과학(Khoa học công nghệ) 스크래핑

    Args:
        date_str: 기준일 (YYYY-MM-DD 형식)

    Returns:
        기사 리스트 [{'title': str, 'content': str, 'url': str, 'date': str}]
    """
    print(f"[스크래핑] VnExpress IT/과학 수집 중...")

    url = "https://vnexpress.net/khoa-hoc-cong-nghe"
    articles = []

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # 오늘 날짜 형식
        today_pattern = (
            date_str.split("-")[2]
            + "/"
            + date_str.split("-")[1]
            + "/"
            + date_str.split("-")[0]
        )

        # 기사 리스트 찾기
        article_elements = soup.find_all("article") or soup.select(
            ".article-item, .news-item"
        )

        for article in article_elements[:5]:  # 최대 5개 기사 체크
            # 링크 찾기
            link_tag = article.find("a")
            if not link_tag:
                continue

            article_url = link_tag.get("href", "")
            if not article_url.startswith("http"):
                article_url = "https://vnexpress.net" + article_url

            # 제목 찾기
            title_tag = article.find(["h2", "h3", "h4"])
            title = title_tag.get_text(strip=True) if title_tag else ""

            # 날짜 찾기
            date_tag = (
                article.find("time")
                or article.find("span", class_="date")
                or article.find("div", class_="article-date")
            )
            article_date = date_tag.get_text(strip=True) if date_tag else ""

            # 오늘 날짜가 포함되어 있는지 확인
            if (
                today_pattern in article_date or not article_date
            ):  # 날짜가 없으면 최신 기사로 간주
                # 본문 미리보기 요약
                summary_tag = article.find("p", class_="sapo") or article.find(
                    "div", class_="summary"
                )
                content = summary_tag.get_text(strip=True) if summary_tag else title

                articles.append(
                    {
                        "title": title,
                        "content": content[:200],  # 200자 제한
                        "url": article_url,
                        "date": article_date,
                    }
                )

                if len(articles) >= 2:  # 최대 2개 제한
                    break

        print(f"  [OK] VnExpress IT/과학: {len(articles)}개 기사 수집")
        return articles

    except Exception as e:
        print(f"  [!] VnExpress IT/과학 스크래핑 실패: {str(e)}")
        return []


def scrape_saigontimes(date_str: str) -> List[Dict[str, str]]:
    """
    The Saigon Times(경제) 스크래핑

    Args:
        date_str: 기준일 (YYYY-MM-DD 형식)

    Returns:
        기사 리스트 [{'title': str, 'content': str, 'url': str, 'date': str}]
    """
    print(f"[스크래핑] The Saigon Times 수집 중...")

    url = "https://thesaigontimes.vn/"
    articles = []

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # 오늘 날짜 형식
        today_pattern = (
            date_str.split("-")[2]
            + "/"
            + date_str.split("-")[1]
            + "/"
            + date_str.split("-")[0]
        )

        # 기사 리스트 찾기
        article_elements = soup.find_all("article") or soup.select(
            ".news-item, .article-item, .story-item"
        )

        for article in article_elements[:5]:  # 최대 5개 기사 체크
            # 링크 찾기
            link_tag = article.find("a")
            if not link_tag:
                continue

            article_url = link_tag.get("href", "")
            if not article_url.startswith("http"):
                article_url = "https://thesaigontimes.vn" + article_url

            # 카테고리 필터링 (기획/경제/재무/부동산만 수집)
            priority_categories = [
                "/noi-bat-2/",  # 기획/하이라이트
                "/kinh-doanh/",  # 경제
                "/tai-chinh-ngan-hang/",  # 재무-금융
                "/dia-oc/",  # 부동산
            ]

            in_priority = any(cat in article_url for cat in priority_categories)

            if not in_priority:
                continue

            # 제목 찾기
            title_tag = article.find(["h2", "h3", "h4"])
            title = title_tag.get_text(strip=True) if title_tag else ""

            # 날짜 찾기
            date_tag = (
                article.find("time")
                or article.find("span", class_="date")
                or article.find("div", class_="article-date")
            )
            article_date = date_tag.get_text(strip=True) if date_tag else ""

            # 오늘 날짜가 포함되어 있는지 확인
            if (
                today_pattern in article_date or not article_date
            ):  # 날짜가 없으면 최신 기사로 간주
                # 본문 미리보기 요약
                summary_tag = article.find("p", class_="sapo") or article.find(
                    "div", class_="summary"
                )
                content = summary_tag.get_text(strip=True) if summary_tag else title

                articles.append(
                    {
                        "title": title,
                        "content": content[:200],  # 200자 제한
                        "url": article_url,
                        "date": article_date,
                    }
                )

        print(f"  [OK] The Saigon Times: {len(articles)}개 기사 수집")
        return articles

    except Exception as e:
        print(f"  [!] The Saigon Times 스크래핑 실패: {str(e)}")
        return []


def scrape_earthquake() -> List[Dict[str, str]]:
    """
    IGP-VAST 지진 정보 스크래핑

    Returns:
        지진 정보 리스트 [{'title': str, 'content': str, 'url': str, 'date': str}]
    """
    print(f"[스크래핑] IGP-VAST 지진 정보 수집 중...")

    earthquakes = []

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }

        # IGP-VAST 지진 뉴스 페이지
        url = "http://igp-vast.vn/index.php/vi/tin-dong-dat"
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # 지진 기사 찾기
        article_elements = soup.find_all("article")

        for article in article_elements[:3]:  # 최근 3개
            # 링크 찾기
            link_tag = article.find("a")
            if not link_tag:
                continue

            article_url = link_tag.get("href", "")
            if not article_url.startswith("http"):
                article_url = "http://igp-vast.vn" + article_url

            # 제목 찾기
            title_tag = article.find(["h2", "h3", "h4"])
            title = title_tag.get_text(strip=True) if title_tag else ""

            # 본문 전체 텍스트 가져오기
            content = article.get_text(strip=True)

            # 날짜 추출 (정규 표현식)
            import re

            date_match = re.search(
                r"ngày (\d{1,2}) tháng (\d{1,2}) năm (\d{4})", content
            )
            article_date = date_match.group(0) if date_match else ""

            if title and content:
                earthquakes.append(
                    {
                        "title": title,
                        "content": content[:500],  # 500자 제한
                        "url": article_url,
                        "date": article_date,
                    }
                )

        print(f"  [OK] IGP-VAST: {len(earthquakes)}개 지진 정보 수집")
        return earthquakes

    except Exception as e:
        print(f"  [!] IGP-VAST 지진 정보 스크래핑 실패: {str(e)}")
        return []


def scrape_and_save(date_str: str, output_path: str) -> Dict[str, List[Dict[str, str]]]:
    """
    모든 소스 스크래핑 및 원본 YAML 저장

    Args:
        date_str: 기준일 (YYYY-MM-DD 형식)
        output_path: 원본 YAML 저장 경로

    Returns:
        스크래핑된 기사 데이터 딕셔너리
    """
    print(f"\n[*] 모든 소스 스크래핑 시작 ({date_str})")
    print("-" * 50)

    # 안전 및 기상 관제 데이터 스크래핑
    weather_data = scrape_weather_hochiminh()
    air_data = scrape_air_quality()
    earthquake_data = scrape_earthquake()

    # 안전 및 기상 관제 데이터 통합
    safety_items = []

    # 기상 정보
    if weather_data:
        temp_str = weather_data["temp"].strip() if weather_data["temp"] else "N/A"
        # 불필요한 콜론 제거
        temp_str = temp_str.lstrip(":").strip()

        humidity_str = (
            weather_data["humidity"].strip() if weather_data["humidity"] else "N/A"
        )
        condition_str = (
            weather_data["condition"].strip() if weather_data["condition"] else "N/A"
        )

        safety_items.append(
            {
                "name": "기상",
                "source": "NCHMF",
                "temp": weather_data["temp"],
                "humidity": weather_data["humidity"],
                "condition": weather_data["condition"],
                "content": f"{condition_str}, 온도 {temp_str}, 습도 {humidity_str}",
                "url": "https://www.nchmf.gov.vn/en/portal/portal/hcm-weather",
            }
        )
        print(f"  [INFO] 기상 정보 추가됨: {condition_str}, {temp_str}")

    # 공기질 정보 (데이터가 비어있더라도 시도)
    if air_data:
        aqi_str = air_data["aqi"].strip() if air_data["aqi"] else "N/A"
        status_str = air_data["status"].strip() if air_data["status"] else "N/A"
        pm25_str = air_data["pm25"].strip() if air_data["pm25"] else "N/A"
        pm10_str = air_data["pm10"].strip() if air_data["pm10"] else "N/A"

        # 모든 데이터가 비어있더라도 기본값으로 추가
        if not aqi_str and not status_str and not pm25_str and not pm10_str:
            aqi_str = "N/A"
            status_str = "N/A"
            pm25_str = "N/A"
            pm10_str = "N/A"

        safety_items.append(
            {
                "name": "공기",
                "source": "IQAir (Saigon Pearl)",
                "aqi": air_data["aqi"],
                "status": air_data["status"],
                "pm25": air_data["pm25"],
                "pm10": air_data["pm10"],
                "content": f"AQI {aqi_str} ({status_str}), PM2.5: {pm25_str}, PM10: {pm10_str}",
                "url": "https://www.iqair.com/vietnam/ho-chi-minh-city/ho-chi-minh-city/iqair-vietnam-saigon-pearl",
            }
        )
        print(f"  [INFO] 공기질 정보 추가됨: AQI {aqi_str}, {status_str}")

    # 지진 정보 (최근 3개)
    for quake in earthquake_data:
        safety_items.append(
            {
                "name": "지진",
                "source": "IGP-VAST",
                "title": quake["title"],
                "content": quake["content"],
                "url": quake["url"],
            }
        )

    # 안전 데이터가 없으면 placeholder 추가
    if not safety_items:
        safety_items.append(
            {
                "name": "플레이스홀더",
                "source": "NCHMF/IQAir",
                "content": "기상 및 공기질 정보를 수집 중입니다...",
                "url": "https://www.nchmf.gov.vn/",
            }
        )
        print(f"  [INFO] 안전 데이터가 없어 플레이스홀더 추가됨")
    else:
        print(f"  [INFO] 안전 데이터 {len(safety_items)}개 추가됨")

    scraped_data = {
        "안전 및 기상 관제": safety_items,
        "Nhân Dân": scrape_nhandan(date_str),
        "Sức khỏe & Đời sống": scrape_suckhoedoisong(date_str),
        "Tuổi Trẻ": scrape_tuoitre(date_str),
        "VietnamNet": scrape_vietnamnet(date_str),
        "VnExpress": scrape_vnexpress(date_str),
        "Thanh Niên": scrape_thanhnien_rss(date_str),
        "The Saigon Times": scrape_saigontimes(date_str),
        "VietnamNet 정보통신": scrape_vietnamnet_ttt(date_str),
        "VnExpress IT/과학": scrape_vnexpress_tech(date_str),
    }

    print("-" * 50)

    # 원본 YAML 저장
    save_raw_yaml(scraped_data, date_str, output_path)

    return scraped_data


def save_raw_yaml(scraped_data: Dict, date_str: str, output_path: str) -> bool:
    """
    스크래핑된 원본 데이터를 YAML로 저장

    Args:
        scraped_data: 스크래핑된 데이터
        date_str: 기준일 표시용
        output_path: 출력 파일 경로

    Returns:
        성공 여부
    """
    import yaml
    import os

    print(f"\n[*] 원본 YAML 저장 시작...")

    yaml_data = {
        "metadata": {
            "date": date_str,
            "time": "",
            "location": "Ho Chi Minh City (Saigon Pearl)",
        },
        "sections": [],
    }

    section_id = 1
    for source_name, articles in scraped_data.items():
        if source_name == "안전 및 기상 관제":
            # 안전 및 기상 관제 섹션 처리
            section = {
                "id": str(section_id),
                "name": source_name,
                "priority": "P0",
                "items": [],
            }

            for item in articles:
                # 기상/공기질/지진 데이터 형식 변환
                if item.get("name") == "기상":
                    section["items"].append(
                        {
                            "title": f"기상 (NCHMF)",
                            "content": item.get("content", ""),
                            "url": item.get("url", ""),
                        }
                    )
                elif item.get("name") == "공기":
                    section["items"].append(
                        {
                            "title": f"공기질 (IQAir) - AQI {item.get('aqi', '')}",
                            "content": item.get("content", ""),
                            "url": item.get("url", ""),
                        }
                    )
                elif item.get("name") == "지진":
                    section["items"].append(
                        {
                            "title": item.get("title", ""),
                            "content": item.get("content", ""),
                            "url": item.get("url", ""),
                        }
                    )
                elif item.get("name") == "플레이스홀더":
                    section["items"].append(
                        {
                            "title": "안전 및 기상 관제",
                            "content": item.get("content", ""),
                            "url": item.get("url", ""),
                        }
                    )

            if section["items"]:
                yaml_data["sections"].append(section)
                section_id += 1
        else:
            # 일반 뉴스 섹션 처리
            section = {
                "id": str(section_id),
                "name": source_name,
                "priority": "P0"
                if "안전" in source_name or "Sức khỏe" in source_name
                else "P2",
                "items": [],
            }

            for article in articles:
                section["items"].append(
                    {
                        "title": article["title"],
                        "content": article["content"],
                        "url": article["url"],
                    }
                )

            if section["items"]:
                yaml_data["sections"].append(section)
                section_id += 1

    # 디렉토리 생성
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # YAML 파일로 저장
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(
            yaml_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False
        )

    print(f"[+] 원본 YAML 저장 완료: {output_path}")
    return True
