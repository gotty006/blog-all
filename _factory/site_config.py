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
