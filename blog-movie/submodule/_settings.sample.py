# _settings.py のテンプレート。値を埋めて _settings.py にリネームして使う。
debug_flag = {
    'do_not_post': False,
    'direct_post': True,
}
log_file = 'data/result.log'
wordpress_id  = "your-wp-email@example.com"
wordpress_pw  = "your-wp-password"
wordpress_url = "https://movie.niconavi.com/xmlrpc.php"
gpt_prompt    = "以下のテーマについて、200字程度で魅力を日本語・丁寧語で書いてください。ネガティブ表現は避けてください。"

# TMDB APIキー（無料）https://www.themoviedb.org/settings/api
tmdb_api_key = "your-tmdb-api-key"
