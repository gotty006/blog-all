# _settings.py のテンプレート。値を埋めて _settings.py にリネームして使う。
debug_flag = {
    'do_not_post': False,
    'direct_post': True,
    'use_cache_input_data': False,
    'use_cache_gpt_answer': False,
}
log_file = 'data/result.log'
wordpress_id  = "your-wp-email@example.com"
wordpress_pw  = "your-wp-password"
wordpress_url = "https://parking.niconavi.com/xmlrpc.php"

# GCP認証（Google Spreadsheet読み取り用）
gcp_auth_file = 'config/gcp-auth.json'

# 駐車場ネタ収集スプレッドシート
spread_sheet_key = "your-spreadsheet-id"

# Pパーク API
pppark_api_key = "your-pppark-api-key"

# 駐車場アフィリエイト設定
affiliate_logo_config = {
    'akippa': {
        'affiliate': 'https://px.a8.net/svt/ejp?a8mat=XXXX',
        'redirect': 'https://www.akippa.com/driver/searchparking?keyword=',
        'url': '/wp-content/uploads/akippa.png',
        'width': '70',
        'height': '30',
        'text': ' で検索',
    },
    '特P': {
        'affiliate': 'https://px.a8.net/svt/ejp?a8mat=XXXX',
        'url': '/wp-content/uploads/tokup.png',
        'width': '70',
        'height': '30',
        'text': ' で検索',
    },
}

parking_category = {
    'weekend_rsv': '予約可能な最安駐車場',
    'weekend_long': '休日 長時間利用(最大料金あり) の駐車場',
    'weekday_long': '平日 長時間利用(最大料金あり) の駐車場',
    'weekend_short': '休日 短時間利用(1時間〜) の駐車場',
    'weekday_short': '平日 短時間利用(1時間〜) の駐車場',
}

walking_distance_threshold = 1000
min_station_passengers = 100000
station_geojson_file = 'data/other/S12-22_NumberOfPassengers.geojson'
add_spots_dry_run = False
