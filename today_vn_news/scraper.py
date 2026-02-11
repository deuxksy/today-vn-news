#!/usr/bin/env python3
"""
웹 스크래핑 모듈 (BeautifulSoup4 기반)
- 목적: 뉴스 사이트에서 당일 기사 직접 수집
- 대상: Nhân Dân, Sức khỏe & Đời sống, Tuổi Trẻ
"""

import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re
import xml.etree.ElementTree as ET
import html


def clean_text(text: str) -> str:
    """
    텍스트 정제: 홑따옴표 제거 + HTML 엔티티 변환

    Args:
        text: 정제할 텍스트

    Returns:
        정제된 텍스트
        - 홑따옴표(') 제거 (YAML 파싱 오류 방지)
        - HTML 엔티티 변환 (&uacute; → ú, &ocirc; → ô 등)
    """
    if not text:
        return text

    # 홑따옴표 제거
    text = text.replace("'", "").replace("\u2019", "").replace("\u2018", "")

    # HTML 엔티티 변환
    text = html.unescape(text)

    return text


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
            soup.find_all("article", class_="story")
            or soup.find_all("article", class_="news-item")
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
            title = clean_text(title)  # 텍스트 정제 (홑따옴표 + HTML 엔티티)

            # 날짜 찾기
            date_tag = (
                article.find("time")
                or article.find("span", class_="date")
                or article.find("div", class_="article-date")
            )

            # 오늘 날짜 확인
            is_today = False
            if date_tag and date_tag.name == "time":
                # ISO 8601 형식 (datetime 속성): 2026-02-11T17:21:16+07:00
                datetime_str = date_tag.get("datetime", "")
                if datetime_str:
                    try:
                        article_dt = datetime.fromisoformat(datetime_str.replace("+07:00", ""))
                        target_dt = datetime.strptime(date_str, "%Y-%m-%d")
                        is_today = article_dt.date() == target_dt.date()
                        article_date = article_dt.strftime("%d/%m/%Y")
                    except:
                        article_date = date_tag.get_text(strip=True)
                else:
                    article_date = date_tag.get_text(strip=True)
            else:
                article_date = date_tag.get_text(strip=True) if date_tag else ""
                # 기존 패턴 매칭 (텍스트 날짜)
                if today_pattern in article_date:
                    is_today = True

            if is_today:
                # 본문 미리보기 요약
                summary_tag = article.find("p", class_="sapo") or article.find(
                    "div", class_="summary"
                )
                content = summary_tag.get_text(strip=True) if summary_tag else title
                content = clean_text(content)  # 텍스트 정제 (홑따옴표 + HTML 엔티티)

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

        # 기사 리스트 찾기 (h2 태그 안에 링크가 있는 구조)
        h2_tags = soup.find_all("h2")[:5]  # 최대 5개 기사 체크

        for h2_tag in h2_tags:
            # 링크 찾기
            link_tag = h2_tag.find("a")
            if not link_tag:
                continue

            article_url = link_tag.get("href", "")
            if not article_url.startswith("http"):
                article_url = "https://suckhoedoisong.vn" + article_url

            # 제목 찾기
            title = link_tag.get_text(strip=True)
            title = clean_text(title)  # 텍스트 정제 (홑따옴표 + HTML 엔티티)

            # 날짜 찾기 (h2 주변 또는 부모 요소)
            parent = h2_tag.parent
            date_tag = (
                parent.find("time")
                if parent
                else None or h2_tag.find_next_sibling("span", class_="date")
                or h2_tag.find_next_sibling("div", class_="article-date")
            )
            article_date = date_tag.get_text(strip=True) if date_tag else ""

            # 오늘 날짜가 포함되어 있는지 확인
            if (
                today_pattern in article_date or not article_date
            ):  # 날짜가 없으면 최신 기사로 간주
                # 본문 미리보기 요약
                summary_tag = (
                    parent.find("p", class_="sapo")
                    if parent
                    else None or h2_tag.find_next("p")
                )
                content = summary_tag.get_text(strip=True) if summary_tag else title
                content = clean_text(content)  # 텍스트 정제 (홑따옴표 + HTML 엔티티)

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
            title = clean_text(title)  # 텍스트 정제 (홑따옴표 + HTML 엔티티)

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
                content = clean_text(content)  # 텍스트 정제 (홑따옴표 + HTML 엔티티)

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
            title = clean_text(title)  # 텍스트 정제 (홑따옴표 + HTML 엔티티)

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
                content = clean_text(content)  # 텍스트 정제 (홑따옴표 + HTML 엔티티)

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
            title = clean_text(title)  # 텍스트 정제 (홑따옴표 + HTML 엔티티)

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
                content = clean_text(content)  # 텍스트 정제 (홑따옴표 + HTML 엔티티)

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
    IQAir API (AQI) + Open-Meteo API (PM2.5, PM10) 혼합

    Returns:
        공기질 정보 딕셔너리 {'aqi': str, 'status': str, 'pm25': str, 'pm10': str}
    """
    print(f"[스크래핑] IQAir + Open-Meteo 공기질 정보 수집 중...")

    try:
        # IQAir 실제 관측소 좌표 (Quan Mot)
        lat, lon = 10.78069, 106.69944

        # 1. IQAir API로 AQI 가져오기
        api_key = os.getenv("IQAIR_API_KEY")
        if not api_key:
            raise ValueError("IQAIR_API_KEY 환경 변수가 설정되지 않았습니다.")
        iqair_url = f"http://api.airvisual.com/v2/nearest_city"
        iqair_params = {
            "lat": lat,
            "lon": lon,
            "key": api_key
        }

        iqair_response = requests.get(iqair_url, params=iqair_params, timeout=10)
        iqair_response.raise_for_status()
        iqair_data = iqair_response.json()

        # AQI 추출
        if iqair_data.get("status") == "success":
            pollution = iqair_data["data"]["current"]["pollution"]
            us_aqi = pollution.get("aqius")
        else:
            print(f"  [!] IQAir API 실패: {iqair_data.get('data', {}).get('message')}")
            us_aqi = None

        # 2. Open-Meteo API로 PM2.5, PM10 가져오기
        openmeteo_url = "https://air-quality-api.open-meteo.com/v1/air-quality"
        openmeteo_params = {
            "latitude": lat,
            "longitude": lon,
            "current": "pm2_5,pm10",
            "timezone": "auto"
        }

        openmeteo_response = requests.get(openmeteo_url, params=openmeteo_params, timeout=10)
        openmeteo_response.raise_for_status()
        openmeteo_data = openmeteo_response.json()

        current = openmeteo_data.get("current", {})
        pm25 = current.get("pm2_5")
        pm10 = current.get("pm10")

        # AQI 상태 계산
        if us_aqi is not None:
            aqi = str(us_aqi)
            if us_aqi <= 50:
                status = "Good"
            elif us_aqi <= 100:
                status = "Moderate"
            elif us_aqi <= 150:
                status = "Unhealthy for Sensitive Groups"
            elif us_aqi <= 200:
                status = "Unhealthy"
            elif us_aqi <= 300:
                status = "Very Unhealthy"
            else:
                status = "Hazardous"
        else:
            aqi = ""
            status = ""

        # PM2.5, PM10 포맷팅
        if pm25 is not None:
            pm25 = f"{pm25:.1f}"
        else:
            pm25 = ""

        if pm10 is not None:
            pm10 = f"{pm10:.1f}"
        else:
            pm10 = ""

        print(f"  [OK] IQAir AQI={aqi}, Open-Meteo PM2.5={pm25} µg/m³, PM10={pm10} µg/m³")
        return {"aqi": aqi, "status": status, "pm25": pm25, "pm10": pm10}

    except Exception as e:
        print(f"  [!] 공기질 정보 스크래핑 실패: {str(e)}")
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
    seen_urls = set()  # 중복 방지를 위한 URL 추적

    # date_str 변환 (2026-02-10 → 10 Feb 26)
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    target_date_short = date_obj.strftime("%d %b %y")  # "10 Feb 26"

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
                        # pubDate 파싱: "Tue, 10 Feb26 15:05:00 +0700"
                        pub_date_text = pub_date_elem.text.strip()

                        # "10 Feb 26" 추출 (정규 표현식)
                        date_match = re.search(r"\d{2} \w{3} \d{2}", pub_date_text)
                        pub_date_short = date_match.group(0) if date_match else ""

                        # 필터링: 당일 기사만
                        if pub_date_short != target_date_short:
                            continue  # 당일 기사가 아니면 건너뜀기
                    except Exception as e:
                        continue
                else:
                    continue

                # entry_date 설정 (원본 형식 유지)
                entry_date = date_str

                # title 찾기
                title_elem = item.find(".//title")
                title = title_elem.text if title_elem is not None else ""
                title = clean_text(title)  # 텍스트 정제 (홑따옴표 + HTML 엔티티)

                # link 찾기
                link_elem = item.find(".//link")
                article_url = link_elem.text if link_elem is not None else ""

                # description 찾기
                desc_elem = item.find(".//description")
                description = desc_elem.text if desc_elem is not None else ""

                # HTML 태그 제거
                content = re.sub(r"<[^>]+>", "", description).strip()
                content = content[:200]  # 200자 제한
                content = clean_text(content)  # 텍스트 정제 (홑따옴표 + HTML 엔티티)

                # 중복 체크 (URL 기반)
                if article_url not in seen_urls:
                    seen_urls.add(article_url)
                    articles.append(
                        {
                            "title": title,
                            "content": content,
                            "url": article_url,
                            "date": entry_date,
                        }
                    )

            print(f"  [OK] {category_name} RSS: {len([a for a in articles if a['url'] in seen_urls])}개 기사")

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
            # 텍스트 정제 (홑따옴표 제거 + HTML 엔티티 변환)
            title = clean_text(title)
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
                # 텍스트 정제 (홑따옴표 제거 + HTML 엔티티 변환)
                content = clean_text(content)
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
            title = clean_text(title)  # 텍스트 정제 (홑따옴표 + HTML 엔티티)

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
                content = clean_text(content)  # 텍스트 정제 (홑따옴표 + HTML 엔티티)

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
            title = clean_text(title)  # 텍스트 정제 (홑따옴표 + HTML 엔티티)

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
                content = clean_text(content)  # 텍스트 정제 (홑따옴표 + HTML 엔티티)

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
            title = clean_text(title)  # 텍스트 정제 (홑따옴표 + HTML 엔티티)

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
                content = clean_text(content)  # 텍스트 정제 (홑따옴표 + HTML 엔티티)

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


def scrape_earthquake(date_str: Optional[str] = None) -> List[Dict[str, str]]:
    """
    IGP-VAST 지진 정보 스크래핑 (RSS 피드, 당일 지진만 필터링)

    Args:
        date_str: 기준일 (YYYY-MM-DD 형식, None이면 필터링 없음)

    Returns:
        지진 정보 리스트 [{'title': str, 'content': str, 'url': str, 'date': str}]
    """
    print(f"[스크래핑] IGP-VAST 지진 정보 수집 중...")

    earthquakes = []

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }

        # IGP-VAST RSS 피드 (영어)
        url = "http://igp-vast.vn/index.php/en/earthquake-news?format=feed"
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # XML 파싱
        root = ET.fromstring(response.content)

        # item 태그 찾기
        items = root.findall(".//item")

        # 필터링을 위한 날짜 파싱
        target_date = None
        if date_str:
            try:
                target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                print(f"  [!] 날짜 형식 오류: {date_str}")

        for item in items:
            # 직접 자식 요소에서 데이터 추출
            title = ""
            description = ""
            article_url = ""
            pub_date = ""

            for child in item:
                tag_name = child.tag.split('}')[-1]  # 네임스페이스 제거
                if tag_name == "title":
                    title = child.text or ""
                elif tag_name == "description":
                    description = child.text or ""
                elif tag_name == "link":
                    article_url = child.text or ""
                elif tag_name == "pubDate":
                    pub_date = child.text or ""

            # 날짜 필터링 (pubDate 파싱: "Tue, 10 Feb 2026 09:20:17 +0700")
            if target_date and pub_date:
                try:
                    # RSS 날짜 파싱
                    from email.utils import parsedate_to_datetime
                    earthquake_datetime = parsedate_to_datetime(pub_date)
                    # GMT+7 (베트남 시간)으로 변환 후 날짜 비교
                    earthquake_date = earthquake_datetime.date()
                    if earthquake_date != target_date:
                        continue  # 당일이 아니면 스킵
                except Exception:
                    pass  # 날짜 파싱 실패 시 포함

            # HTML 엔티티 디코딩 및 태그 제거
            description = html.unescape(description)
            # HTML 태그 제거
            description = re.sub(r'<[^>]+>', ' ', description)
            description = re.sub(r'\s+', ' ', description).strip()

            # 제목이 없으면 description에서 첫 문장 사용
            if not title:
                title = "Earthquake Report"
            else:
                title = html.unescape(title)

            if description:
                earthquakes.append(
                    {
                        "title": title,
                        "content": description[:500],  # 500자 제한
                        "url": article_url,
                        "date": pub_date,
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
    earthquake_data = scrape_earthquake(date_str)

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
                "source": "IQAir + Open-Meteo (Vinhomes Central Park 2)",
                "aqi": air_data["aqi"],
                "status": air_data["status"],
                "pm25": air_data["pm25"],
                "pm10": air_data["pm10"],
                "content": f"AQI {aqi_str} ({status_str}), PM2.5: {pm25_str}, PM10: {pm10_str}",
                "url": "https://www.iqair.com/vietnam/ho-chi-minh-city/ho-chi-minh-city/vinhomes-central-park-2",
            }
        )
        print(f"  [INFO] 공기질 정보 추가됨: AQI {aqi_str}, {status_str}, PM2.5: {pm25_str}, PM10: {pm10_str}")

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
