"""
Search Console API から検索パフォーマンスデータを取得するモジュール。

事前準備:
  index_service_account.json のサービスアカウントを、Search Console の
  「設定 > ユーザーと権限 > ユーザーを追加」で 権限: フル に追加すること。
"""
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.errors import HttpError
from datetime import date, timedelta
from submodule import _settings


SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']


def _build_service():
    credentials = service_account.Credentials.from_service_account_file(
        _settings.index_auth_file, scopes=SCOPES
    )
    return build('searchconsole', 'v1', credentials=credentials)


def fetch_page_performance(site_url, days=28):
    """
    指定サイトのページ別・クエリ別パフォーマンスデータを取得する。

    Returns:
        list of dict: {page, query, clicks, impressions, ctr, position}
    """
    service = _build_service()
    end_date = date.today() - timedelta(days=3)  # Search Consoleは3日遅延
    start_date = end_date - timedelta(days=days)

    request_body = {
        'startDate': start_date.isoformat(),
        'endDate': end_date.isoformat(),
        'dimensions': ['page', 'query'],
        'rowLimit': 5000,
        'dataState': 'final',
    }

    try:
        response = service.searchanalytics().query(
            siteUrl=site_url, body=request_body
        ).execute()
    except HttpError as e:
        print(f"Search Console API エラー ({site_url}): {e}")
        return []

    rows = response.get('rows', [])
    results = []
    for row in rows:
        keys = row.get('keys', [])
        results.append({
            'page': keys[0] if len(keys) > 0 else '',
            'query': keys[1] if len(keys) > 1 else '',
            'clicks': row.get('clicks', 0),
            'impressions': row.get('impressions', 0),
            'ctr': round(row.get('ctr', 0) * 100, 2),
            'position': round(row.get('position', 0), 1),
        })
    return results


def aggregate_by_page(rows):
    """ページ単位に集計する（クエリをまとめる）。"""
    pages = {}
    for row in rows:
        url = row['page']
        if url not in pages:
            pages[url] = {
                'page': url,
                'clicks': 0,
                'impressions': 0,
                'queries': [],
                'position_sum': 0,
                'row_count': 0,
            }
        p = pages[url]
        p['clicks'] += row['clicks']
        p['impressions'] += row['impressions']
        p['queries'].append(row['query'])
        p['position_sum'] += row['position']
        p['row_count'] += 1

    results = []
    for p in pages.values():
        avg_pos = round(p['position_sum'] / p['row_count'], 1) if p['row_count'] else 0
        ctr = round(p['clicks'] / p['impressions'] * 100, 2) if p['impressions'] else 0
        results.append({
            'page': p['page'],
            'clicks': p['clicks'],
            'impressions': p['impressions'],
            'ctr': ctr,
            'avg_position': avg_pos,
            'top_queries': p['queries'][:5],
        })
    return results


def find_quick_wins(page_rows, min_impressions=20, pos_min=4, pos_max=20):
    """順位4〜20位かつ一定のインプレッションがある記事（クイックウィン候補）を返す。"""
    return [
        p for p in page_rows
        if pos_min <= p['avg_position'] <= pos_max
        and p['impressions'] >= min_impressions
    ]


def find_low_ctr(page_rows, ctr_threshold=1.0, min_impressions=50):
    """インプレッションがあるのにCTRが低い記事を返す。"""
    return [
        p for p in page_rows
        if p['impressions'] >= min_impressions
        and p['ctr'] < ctr_threshold
    ]
