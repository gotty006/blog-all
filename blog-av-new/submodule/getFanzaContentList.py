"""
FANZA GraphQL API からコンテンツ一覧を取得するモジュール。
Selenium 不要。api.video.dmm.co.jp/graphql を直接叩く。
"""
import requests

_GRAPHQL_URL = 'https://api.video.dmm.co.jp/graphql'

_QUERY = """
query ContentList($limit: Int!, $offset: Int!, $filter: ContentSearchPPVFilterInput) {
  legacySearchPPV(
    limit: $limit
    floor: AV
    sort: RECOMMENDED
    filter: $filter
    offset: $offset
  ) {
    result {
      contents {
        id
        title
      }
    }
  }
}
"""

# site_type ごとの GraphQL フィルタ設定
# legacyReleaseStatus: LATEST_RELEASE(最新作) / SEMI_NEW_RELEASE(準新作)
FLOOR_FILTERS = {
    'deview_list':  {'legacyReleaseStatus': 'LATEST_RELEASE'},   # 新着デビュー作を含む最新作
    'shiroto_list': {'legacyReleaseStatus': 'LATEST_RELEASE'},
    'jk_list':      {'legacyReleaseStatus': 'LATEST_RELEASE'},
    'new_list':     {'legacyReleaseStatus': 'LATEST_RELEASE'},
    'dojin_list':   {'legacyReleaseStatus': 'LATEST_RELEASE'},
}


def _fanza_url(cid):
    return f'https://video.dmm.co.jp/av/detail/?contentId={cid}'


def get_content_list(site_type, max_items=20):
    """
    FANZA GraphQL API からコンテンツ一覧を取得する。
    Args:
        site_type: 'deview_list', 'new_list' 等
        max_items: 取得する最大件数
    Returns: list of {cid, title, fanza_url}
    """
    gql_filter = FLOOR_FILTERS.get(site_type, {'legacyReleaseStatus': 'LATEST_RELEASE'})

    try:
        resp = requests.post(
            _GRAPHQL_URL,
            json={
                'operationName': 'ContentList',
                'query': _QUERY,
                'variables': {
                    'limit': max_items,
                    'offset': 0,
                    'filter': gql_filter,
                },
            },
            headers={'Content-Type': 'application/json'},
            timeout=20,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f'  [ERROR] FANZA API エラー: {e}')
        return []

    data = resp.json()
    if 'errors' in data:
        print(f'  [ERROR] GraphQL エラー: {data["errors"]}')
        return []

    contents = (
        data.get('data', {})
        .get('legacySearchPPV', {})
        .get('result', {})
        .get('contents', [])
    )

    return [
        {'cid': c['id'], 'title': c['title'], 'fanza_url': _fanza_url(c['id'])}
        for c in contents
    ]
