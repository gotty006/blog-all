"""
blog-vod-av2 (vod.av2.jp) 設定ファイル。

コンセプト: AV動画配信サービス比較・ガイドサイト
  - 狙うキーワード:
      「FANZA 使い方」「AV 動画サイト 比較」「DMM 無料体験」
      「AV サブスク おすすめ」「[サービス名] 解約方法」
  - アフィリエイト: VOD月額登録（FANZA/DMMプレミアム等）→ 高単価
  - 既存サイトとの差別化: 作品リストではなく「使い方・比較・ガイド」系コンテンツ

記事カテゴリ:
  1. サービス比較（FANZA vs XXX）
  2. 使い方ガイド（登録・解約・視聴方法）
  3. キャンペーン・無料体験情報
  4. ジャンル別おすすめ作品（特定サービス内で）
"""

## debugフラグ
debug_flag = {
    'use_cache_vod_data': False,
    'use_cache_gpt_answer': False,
    'use_cache_post_html': False,
    'do_not_post': False,
    'do_not_index': False,
    'do_not_upload_img': False,
    'direct_post': True,
}

## systemConfig
gcp_auth_file = 'config/gcp-auth.json'
index_auth_file = 'config/index_service_account.json'
input_html_dir = 'data/inputPostHtml'
gpt_text_data_dir = 'data/postData/outputGptText/'
new_post_html_dir = 'data/postData/newPost/'
log_file = 'data/result.log'

## WordPress
wordpress_id = "niconavi.com@gmail.com"
wordpress_pw = "Masa5034#"
wordpress_url = "https://vod.av2.jp/xmlrpc.php"

## Search Console（登録後に設定）
search_console_sites = {
    "vod": "https://vod.av2.jp/",
}

## SpreadSheet（新規作成後に設定）
spread_sheet_key = ""
spread_sheet_name = "input_vod"

## 対象VODサービス一覧
vod_services = [
    {
        "name": "FANZA動画",
        "url": "https://video.dmm.co.jp/",
        "affiliate_url": "https://al.dmm.co.jp/?lurl=https%3A%2F%2Fvideo.dmm.co.jp%2F&af_id=niconavicom-001&ch=link_tool&ch_id=link",
        "monthly_price": 550,
        "free_trial_days": 0,
        "features": ["最大級の作品数", "ダウンロード対応", "スマホ対応"],
    },
    {
        "name": "DMMプレミアム",
        "url": "https://premium.dmm.com/",
        "affiliate_url": "https://al.dmm.co.jp/?lurl=https%3A%2F%2Fpremium.dmm.com%2F&af_id=niconavicom-001&ch=link_tool&ch_id=link",
        "monthly_price": 550,
        "free_trial_days": 30,
        "features": ["月額定額見放題", "18禁含む", "動画ダウンロード"],
    },
    {
        "name": "MGS動画",
        "url": "https://www.mgstage.com/",
        "affiliate_url": "https://al.dmm.co.jp/?lurl=https%3A%2F%2Fwww.mgstage.com%2F&af_id=niconavicom-001&ch=link_tool&ch_id=link",
        "monthly_price": 0,
        "free_trial_days": 0,
        "features": ["素人系が充実", "無料サンプル豊富"],
    },
    {
        "name": "カリビアンコム",
        "url": "https://www.caribbeancom.com/",
        "affiliate_url": "",  # 独自アフィリプログラム・要別途登録
        "monthly_price": 2980,
        "free_trial_days": 0,
        "features": ["高画質", "完全オリジナル作品"],
    },
    {
        "name": "一本道",
        "url": "https://www.1pondo.tv/",
        "affiliate_url": "",  # 独自アフィリプログラム・要別途登録
        "monthly_price": 2980,
        "free_trial_days": 0,
        "features": ["完全日本製", "高品質"],
    },
]

## SEOモニター設定
seo_monitor = {
    'quick_win_pos_min': 4,
    'quick_win_pos_max': 20,
    'quick_win_min_impressions': 10,
    'low_ctr_threshold': 1.0,
    'low_ctr_min_impressions': 30,
    'report_top_n': 20,
    'dry_run': False,
}

## 記事タイプ別GPTプロンプト
gpt_prompts = {
    'service_review': """\
以下のVODサービスについて、400字程度でレビューを記載してください。
- サービスの特徴・強み
- どんな人におすすめか
- 使い方のポイント
制約: 日本語・丁寧語・ネガティブ表現なし""",

    'comparison': """\
以下の2つのVODサービスを比較して、300字程度で違いを記載してください。
- 価格・コスパ
- 作品数・ジャンル
- 使いやすさ
制約: 日本語・丁寧語・客観的な比較""",

    'howto': """\
以下のVODサービスの使い方について、ステップごとに説明してください。
- 登録手順（3〜5ステップ）
- 視聴方法のポイント
- 注意事項
制約: 日本語・わかりやすく・箇条書き可""",
}
