"""
blog-scene-av2 (scene.av2.jp) 設定ファイル。

コンセプト: シーン・プレイ内容特化ランキング
  - 狙うキーワード: 「NTR AV おすすめ」「コスプレ AV ランキング」「[シーン名] AV 傑作」
  - 既存サイト（属性特化）と差別化: プレイ内容・シーン視点で分類
  - ジャンル×シーンの組み合わせでロングテール大量獲得
"""

## debugフラグ
debug_flag = {
    'use_cache_video_data': False,
    'use_cache_gpt_answer': False,
    'use_cache_post_html': False,
    'do_not_post': False,
    'do_not_index': False,
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

## WordPress
wordpress_id = "niconavi.com@gmail.com"
wordpress_pw = "Masa5034#"
wordpress_url = "https://scene.av2.jp/xmlrpc.php"

## Search Console（登録後に設定）
search_console_sites = {
    "scene": "https://scene.av2.jp/",
}

## SpreadSheet（新規作成後に設定）
spread_sheet_key = ""
spread_sheet_name = "input_scene"

## FANZA
fanza_affiliate_id = "niconavicom-999"

## ターゲットシーン一覧（記事生成の対象カテゴリ）
target_scenes = [
    "NTR・寝取り・寝取られ",
    "コスプレ",
    "中出し",
    "3P・乱交",
    "レズ",
    "アナル",
    "ギャル",
    "巨乳",
    "スレンダー",
    "ロリ系",
    "熟女・人妻",
    "女教師",
    "OL",
    "ナース",
    "制服",
]

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

## GPTプロンプト（シーン特化・ランキング形式）
gpt_prompt = """\
この作品について、200字程度で、以下の観点から魅力を記載してください。
- どんなシーン・プレイが楽しめるか
- 他の作品と比べた見どころ
制約事項:
・日本語で出力してください。
・「です。」「ます。」調で記載してください。
・ネガティブな内容は記載しないでください。
・実際の内容に基づいてください。"""

## インデックス設定
index_auth_file_path = 'config/index_service_account.json'
