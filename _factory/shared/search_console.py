"""
Search Console API 汎用ラッパー（_settings 非依存版）。
service_account_file と site_url を直接受け取る。
"""
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.errors import HttpError
from datetime import date, timedelta

SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']


def build_service(service_account_file):
    credentials = service_account.Credentials.from_service_account_file(
        service_account_file, scopes=SCOPES
    )
    return build('searchconsole', 'v1', credentials=credentials)


def fetch_page_performance(service_account_file, site_url, days=28):
    """ページ別・クエリ別パフォーマンスを取得する。"""
    service = build_service(service_account_file)
    end_date = date.today() - timedelta(days=3)
    start_date = end_date - timedelta(days=days)

    body = {
        'startDate': start_date.isoformat(),
        'endDate': end_date.isoformat(),
        'dimensions': ['page', 'query'],
        'rowLimit': 5000,
        'dataState': 'final',
    }
    try:
        response = service.searchanalytics().query(siteUrl=site_url, body=body).execute()
    except HttpError as e:
        print(f"Search Console API エラー ({site_url}): {e}")
        return []

    results = []
    for row in response.get('rows', []):
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
    """ページ単位に集計する。"""
    pages = {}
    for row in rows:
        url = row['page']
        if url not in pages:
            pages[url] = {
                'page': url, 'clicks': 0, 'impressions': 0,
                'queries': [], 'position_sum': 0, 'row_count': 0,
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
    return [
        p for p in page_rows
        if pos_min <= p['avg_position'] <= pos_max and p['impressions'] >= min_impressions
    ]


def find_low_ctr(page_rows, ctr_threshold=1.0, min_impressions=50):
    return [
        p for p in page_rows
        if p['impressions'] >= min_impressions and p['ctr'] < ctr_threshold
    ]


def summarize(page_rows):
    """全ページのサマリー統計を返す。"""
    if not page_rows:
        return {'total_pages': 0, 'total_clicks': 0, 'total_impressions': 0, 'avg_ctr': 0, 'avg_position': 0}
    total_clicks = sum(p['clicks'] for p in page_rows)
    total_impressions = sum(p['impressions'] for p in page_rows)
    avg_ctr = round(total_clicks / total_impressions * 100, 2) if total_impressions else 0
    avg_pos = round(sum(p['avg_position'] for p in page_rows) / len(page_rows), 1)
    return {
        'total_pages': len(page_rows),
        'total_clicks': total_clicks,
        'total_impressions': total_impressions,
        'avg_ctr': avg_ctr,
        'avg_position': avg_pos,
    }
