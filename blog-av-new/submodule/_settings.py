"""
blog-av-new 設定ファイル。

SEO戦略: 既存サイトと被らないキーワード領域を狙う
  - 狙うキーワード: 「AV 名作」「AV 傑作」「絶対見るべき AV」「AV 評価高い」等
  - 評価・口コミ系コンテンツで差別化
  - ロングテール: 女優名 × 特定シーン × 評価/おすすめ
  - 既存サイトが弱い「過去作品レビュー」「年別ベスト」系

TODO:
  1. カラフルボックスで新ドメインを取得
  2. WordPress をインストール
  3. wordpress_url に xmlrpc.php エンドポイントを設定
  4. search_console_url に Search Console のサイトURL を設定
  5. _settings.active = True に変更
  6. site_config.py の blog-av-new の active を True に変更
"""

## debugフラグ
debug_flag = {
    'use_cache_video_data': False,
    'use_cache_gpt_answer': False,
    'use_cache_post_html': False,
    'do_not_post': True,        # TODO: WP設定後に False に変更
    'do_not_index': True,       # TODO: SC登録後に False に変更
    'do_not_upload_img': False,
    'use_deep_seek': False,
    'direct_post': True,
}

## systemConfig
gcp_auth_file = 'config/gcp-auth.json'
index_auth_file = 'config/index_service_account.json'
video_data_dump_dir = 'data/postData/videoDataDump/'
input_html_dir = 'data/inputPostHtml'
source_dir = 'data/inputData/'
eye_catch_dir = 'data/postData/eyecatchImg/'
gpt_text_data_dir = 'data/postData/outputGptText/'
new_post_html_dir = 'data/postData/newPost/'
log_file = 'data/result.log'

## WordPress設定
# TODO: カラフルボックスで取得したドメインに変更
wordpress_id = "iliketoplaysoccer@hotmail.co.jp"
wordpress_pw = "Masa5034#"
wordpress_url = ""  # TODO: "https://[新ドメイン]/xmlrpc.php"

## Search Console
search_console_url = ""  # TODO: "https://[新ドメイン]/"

## SpreadSheet
# TODO: 新しいスプレッドシートを作成して設定
spread_sheet_key = ""
spread_sheet_name = "input"

## FANZA API
fanza_affiliate_id = "niconavicom-001"

## SEOモニター設定
seo_monitor = {
    'quick_win_pos_min': 4,
    'quick_win_pos_max': 20,
    'quick_win_min_impressions': 20,
    'low_ctr_threshold': 1.0,
    'low_ctr_min_impressions': 50,
    'report_top_n': 30,
    'dry_run': False,
}

## GPTプロンプト（既存サイトとの差別化: 評価・レビュー寄りの文体）
gpt_prompt = """\
この作品について、300字程度で、以下の観点から魅力を記載してください。
- 他の作品と比べた特徴・見どころ
- どんな人におすすめか
制約事項:
・日本語で出力してください。
・「です。」「ます。」調で記載してください。
・ネガティブな内容は記載しないでください。
・架空の評価や口コミを作らないでください。
・実際の内容に基づいてください。"""

## サービス状態
active = False  # TODO: ドメイン・WP設定完了後に True に変更
