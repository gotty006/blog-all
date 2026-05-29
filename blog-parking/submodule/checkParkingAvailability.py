import json
import requests
import urllib.parse
from datetime import date, timedelta
from submodule import _settings


def _next_weekday(weekday):
    """次の指定曜日の日付を返す (0=月, 6=日)"""
    today = date.today()
    days_ahead = weekday - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return today + timedelta(days=days_ahead)


def _build_post_data(lat, lng):
    weekday_date = _next_weekday(0)  # 月曜
    in_date = weekday_date.strftime('%Y%m%d')
    return {
        'inDate': in_date,
        'inTime': '1100',
        'outDate': in_date,
        'outTime': '1700',
        'lng': str(lng),
        'lat': str(lat),
        'rsv_incl': '1',
        'rgc': '1',
        'key': _settings.pppark_api_key,
        'auto_search_mode': 'true',
    }


def get_parkings(lat, lng):
    """pppark APIを呼び出して駐車場リストと住所情報を返す。失敗時は (None, None, None)。"""
    try:
        post_data = _build_post_data(lat, lng)
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://pppark.com',
            'Referer': 'https://pppark.com/',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        }
        resp = requests.post(
            'https://api.pppark.com/search_v1.2',
            data=urllib.parse.urlencode(post_data),
            headers=headers,
            timeout=15,
        )
        resp.raise_for_status()
        body = resp.json()

        if body.get('error'):
            print(f"pppark API error: {body['error']}")
            return None, None, None

        parkings = body.get('result', {}).get('parkings', [])
        rev = body.get('rev_geocoding', {})
        pref = rev.get('pref', '')
        city = rev.get('city', '')
        return parkings, pref, city

    except Exception as e:
        print(f"pppark API 呼び出し失敗: {e}")
        return None, None, None


def build_pppark_url(pref, city, station_name, lat, lng):
    """スプレッドシートの source_url_parking 用URLを生成する（日付パラメータなし）。"""
    pref_enc = urllib.parse.quote(pref, safe='')
    city_enc = urllib.parse.quote(city, safe='')
    station_enc = urllib.parse.quote(f"{station_name}駅", safe='')
    return f"https://pppark.com/search/{pref_enc}/{city_enc}/{station_enc}?@{lat},{lng}&"
