"""
autoBlog 全サービス設定レジストリ。
新サービスを追加する際はここに行を追加する。
"""

SITES = [
    {
        "id": "blog-vod-av2",
        "name": "VOD比較サイト (vod.av2.jp)",
        "niche": "AV動画配信サービス比較・ガイド",
        "dir": "blog-vod-av2",
        "wp_url": "https://vod.av2.jp/xmlrpc.php",
        "sc_url": "https://vod.av2.jp/",          # TODO: Search Console 登録後に有効化
        "index_auth": "config/index_service_account.json",
        "active": True,
    },
    {
        "id": "blog-scene-av2",
        "name": "シーン特化ランキング (scene.av2.jp)",
        "niche": "AV シーン・プレイ内容特化",
        "dir": "blog-scene-av2",
        "wp_url": "https://scene.av2.jp/xmlrpc.php",
        "sc_url": "https://scene.av2.jp/",         # TODO: Search Console 登録後に有効化
        "index_auth": "config/index_service_account.json",
        "active": True,
    },
    {
        "id": "blog-av-new",
        "name": "新AVブログ（SEO特化）",
        "niche": "AV・名作レビュー特化",
        "dir": "blog-av-new",
        "wp_url": "",           # TODO: ドメイン取得後に設定
        "sc_url": "",
        "index_auth": "config/index_service_account.json",
        "active": False,
    },
    # ── niconavi.com 新サービス群 ──────────────────────────────────
    {
        "id": "blog-onsen",
        "name": "温泉ランキング (onsen.niconavi.com)",
        "niche": "温泉旅館・目的×エリア特化",
        "dir": "blog-onsen",
        "wp_url": "https://onsen.niconavi.com/xmlrpc.php",
        "sc_url": "https://onsen.niconavi.com/",
        "index_auth": "config/index_service_account.json",
        "active": False,        # WPサイト作成後にTrueへ
    },
    {
        "id": "blog-hotel",
        "name": "ホテルランキング (hotel.niconavi.com)",
        "niche": "ホテル・特徴×エリア特化",
        "dir": "blog-hotel",
        "wp_url": "https://hotel.niconavi.com/xmlrpc.php",
        "sc_url": "https://hotel.niconavi.com/",
        "index_auth": "config/index_service_account.json",
        "active": False,
    },
    {
        "id": "blog-golf",
        "name": "ゴルフ場ランキング (golf.niconavi.com)",
        "niche": "ゴルフ場・難易度×料金×エリア特化",
        "dir": "blog-golf",
        "wp_url": "https://golf.niconavi.com/xmlrpc.php",
        "sc_url": "https://golf.niconavi.com/",
        "index_auth": "config/index_service_account.json",
        "active": False,
    },
    {
        "id": "blog-camp",
        "name": "キャンプ場ランキング (camp.niconavi.com)",
        "niche": "キャンプ場・設備スタイル×エリア特化",
        "dir": "blog-camp",
        "wp_url": "https://camp.niconavi.com/xmlrpc.php",
        "sc_url": "https://camp.niconavi.com/",
        "index_auth": "config/index_service_account.json",
        "active": False,
    },
    {
        "id": "blog-gourmet",
        "name": "グルメランキング (gourmet.niconavi.com)",
        "niche": "グルメ・シチュエーション×エリア特化",
        "dir": "blog-gourmet",
        "wp_url": "https://gourmet.niconavi.com/xmlrpc.php",
        "sc_url": "https://gourmet.niconavi.com/",
        "index_auth": "config/index_service_account.json",
        "active": False,
    },
    {
        "id": "blog-movie",
        "name": "映画ランキング (movie.niconavi.com)",
        "niche": "映画・気分感情別特化",
        "dir": "blog-movie",
        "wp_url": "https://movie.niconavi.com/xmlrpc.php",
        "sc_url": "https://movie.niconavi.com/",
        "index_auth": "config/index_service_account.json",
        "active": False,
    },
    {
        "id": "blog-parking",
        "name": "駐車場ランキング (parking.niconavi.com)",
        "niche": "駐車場・エリア×用途特化",
        "dir": "blog-parking",
        "wp_url": "https://parking.niconavi.com/xmlrpc.php",
        "sc_url": "https://parking.niconavi.com/",
        "index_auth": "config/index_service_account.json",
        "active": False,
    },
]

# 既存 aiBlog のサービスも朝レポートに含める場合はここに追加
LEGACY_SITES = [
    {
        "id": "av-deview-single",
        "name": "av-deview single_list",
        "niche": "AV個別作品",
        "sc_url": "https://new.av-deview.com/",
        "index_auth": "../aiBlog/generate_blog_av/config/index_service_account.json",
        "active": True,
    },
    {
        "id": "av-shiroto",
        "name": "av-shiroto",
        "niche": "AV素人",
        "sc_url": "https://av-shiroto.com/",
        "index_auth": "../aiBlog/generate_blog_av/config/index_service_account.json",
        "active": True,
    },
    {
        "id": "parking",
        "name": "駐車場ブログ",
        "niche": "駐車場",
        "sc_url": "https://av2.jp/",
        "index_auth": "../aiBlog/generate_blog_av/config/index_service_account.json",
        "active": True,
    },
]

def get_active_sites(include_legacy=True):
    sites = [s for s in SITES if s.get("active")]
    if include_legacy:
        sites += [s for s in LEGACY_SITES if s.get("active")]
    return sites
