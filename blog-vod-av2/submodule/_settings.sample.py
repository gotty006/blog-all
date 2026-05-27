# _settings.py のテンプレート。実際の値を入れて _settings.py にリネームして使う。
debug_flag = {
    'do_not_post': False,
    'do_not_index': False,
    'direct_post': True,
}
log_file = 'data/result.log'
wordpress_id  = "your-wp-email@example.com"
wordpress_pw  = "your-wp-password"
wordpress_url = "https://vod.av2.jp/xmlrpc.php"
vod_services  = []  # _settings.py 本体を参照
gpt_prompts   = {}  # _settings.py 本体を参照
