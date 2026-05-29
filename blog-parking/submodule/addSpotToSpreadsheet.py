import os
import gspread
from datetime import date, timedelta
from oauth2client.service_account import ServiceAccountCredentials
from submodule import _settings


def _get_client():
    auth = _settings.gcp_auth_file
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = auth
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(auth, scope)
    return gspread.authorize(credentials)


def _next_weekday(weekday):
    today = date.today()
    days_ahead = weekday - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return (today + timedelta(days=days_ahead)).strftime('%Y%m%d')


def get_existing_areas(sheet_key):
    """既存スプレッドシートの area 列をsetで返す（重複チェック用）。"""
    client = _get_client()
    ws = client.open_by_key(sheet_key).worksheet('general')
    all_values = ws.get_all_values()
    return {row[0] for row in all_values[1:] if row}


def add_spot(sheet_key, station, pref, city, source_url):
    """general シートの末尾に1行追記する。dry_runフラグがTrueの場合は書き込まない。"""
    tag = f"{city},{station['line']}"
    weekend = _next_weekday(6)   # 次の日曜
    weekday = _next_weekday(0)   # 次の月曜

    new_row = [
        station['name'],  # area
        '',               # url
        '',               # category
        tag,              # tag
        source_url,       # source_url_parking
        weekend,          # weekend
        weekday,          # weekday
    ]

    print(f"[{'DRY RUN' if _settings.add_spots_dry_run else 'WRITE'}] {new_row}")

    if _settings.add_spots_dry_run:
        return

    client = _get_client()
    ws = client.open_by_key(sheet_key).worksheet('test')
    ws.append_row(new_row, value_input_option='USER_ENTERED')
