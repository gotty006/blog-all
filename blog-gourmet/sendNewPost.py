"""
gourmet.niconavi.com — グルメ「シチュエーション×エリア×ジャンル」特化ランキング

SEO差別化: 「渋谷 誕生日ディナー イタリアン 個室」「新宿 デート 和食」
Hotpepper/食べログの総合ランキングと差別化。シチュエーション×ジャンルで検索意図に直撃。

使い方:
  python3 sendNewPost.py          # 本日分15件
  python3 sendNewPost.py --all
  python3 sendNewPost.py --status
"""
import sys, os, json, xmlrpc.client, urllib.parse, requests
from datetime import datetime, date
import openai
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import NewPost, GetPosts, EditPost
from wordpress_xmlrpc.methods.media import UploadFile

sys.path.insert(0, 'submodule')
from submodule import _settings

LOG_FILE      = _settings.log_file
SCHEDULE_FILE = 'data/schedule.json'
HOTPEPPER_API = 'https://webservice.recruit.co.jp/hotpepper/gourmet/v1/'
DAILY_UPDATE  = 15

# Hotpepperエリアコード（大エリア）
AREA_CODES = {
    "渋谷": "Z011", "新宿": "Z012", "池袋": "Z013", "銀座": "Z014",
    "六本木": "Z015", "品川": "Z016", "上野": "Z017",
    "梅田": "Y001", "難波": "Y002", "心斎橋": "Y003",
    "栄": "X001", "名駅": "X002",
}

TARGETS = {
    # 記念日・誕生日
    "渋谷×誕生日ディナーにおすすめレストラン個室":    {"area": "Z011", "keyword": "誕生日 個室", "scene": "記念日・誕生日"},
    "新宿×誕生日ディナーにおすすめレストラン個室":    {"area": "Z012", "keyword": "誕生日 個室", "scene": "記念日・誕生日"},
    "銀座×記念日ディナーにおすすめ高級レストラン":    {"area": "Z014", "keyword": "記念日 記念 特別", "scene": "記念日・誕生日"},
    "梅田×誕生日ディナーにおすすめレストラン個室":    {"area": "Y001", "keyword": "誕生日 個室", "scene": "記念日・誕生日"},
    # デート
    "渋谷×デートにおすすめおしゃれレストラン":        {"area": "Z011", "keyword": "デート おしゃれ 雰囲気", "scene": "デート"},
    "六本木×デートにおすすめ夜景レストラン":          {"area": "Z015", "keyword": "デート 夜景 雰囲気", "scene": "デート"},
    "新宿×デートにおすすめコース料理レストラン":      {"area": "Z012", "keyword": "デート コース", "scene": "デート"},
    "心斎橋×デートにおすすめおしゃれレストラン":      {"area": "Y003", "keyword": "デート おしゃれ", "scene": "デート"},
    # 接待・ビジネス
    "銀座×接待に使えるおすすめ和食":                  {"area": "Z014", "keyword": "接待 和食 個室", "scene": "接待・ビジネス"},
    "新宿×接待に使えるおすすめ日本料理":              {"area": "Z012", "keyword": "接待 個室 落ち着く", "scene": "接待・ビジネス"},
    "梅田×接待に使えるおすすめ高級料理":              {"area": "Y001", "keyword": "接待 個室 高級", "scene": "接待・ビジネス"},
    # 女子会
    "渋谷×女子会におすすめかわいいカフェ・レストラン": {"area": "Z011", "keyword": "女子会 かわいい インスタ", "scene": "女子会"},
    "梅田×女子会におすすめレストラン":                {"area": "Y001", "keyword": "女子会 かわいい", "scene": "女子会"},
    # ランチ・コスパ
    "渋谷×コスパ最強ランチにおすすめレストラン":      {"area": "Z011", "keyword": "ランチ コスパ お値打ち", "scene": "ランチ・コスパ"},
    "新宿×コスパ最強ランチにおすすめレストラン":      {"area": "Z012", "keyword": "ランチ コスパ お得", "scene": "ランチ・コスパ"},
}


def load_schedule():
    os.makedirs('data', exist_ok=True)
    return json.load(open(SCHEDULE_FILE, encoding='utf-8')) if os.path.exists(SCHEDULE_FILE) else {}

def save_schedule(s):
    json.dump(s, open(SCHEDULE_FILE, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

def select_today(n=DAILY_UPDATE):
    s = load_schedule()
    return sorted(TARGETS.keys(), key=lambda k: s.get(k, '1970-01-01'))[:n]

def log(msg):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line)
    open(LOG_FILE, 'a', encoding='utf-8').write(line + '\n')

def fetch_hotpepper(area_code, keyword, hits=10):
    try:
        r = requests.get(HOTPEPPER_API, params={
            'key': _settings.hotpepper_api_key,
            'large_area': area_code, 'keyword': keyword,
            'count': hits, 'format': 'json',
            'order': 4,  # おすすめ順
        }, timeout=15)
        return r.json().get('results', {}).get('shop', [])
    except Exception as e:
        log(f"Hotpepper API エラー ({keyword}): {e}"); return []

def gpt(prompt):
    client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    res = client.chat.completions.create(model='gpt-4o-mini',
        messages=[{'role': 'user', 'content': prompt}], max_tokens=600)
    return res.choices[0].message.content.strip()

def upload_thumbnail(wp, image_url, filename):
    try:
        resp = requests.get(image_url, timeout=10)
        if resp.status_code != 200: return None
        result = wp.call(UploadFile({'name': filename, 'type': 'image/jpeg',
                                      'bits': xmlrpc.client.Binary(resp.content)}))
        return result.get('id')
    except Exception as e:
        log(f"サムネ失敗: {e}"); return None

def _get_existing_slugs(wp):
    posts = wp.call(GetPosts({'number': 500, 'post_status': 'any'}))
    return {urllib.parse.unquote(p.slug): p for p in posts}

def wp_post(title, content, slug, category, tags, seo_title, seo_desc, thumbnail_url=None):
    if _settings.debug_flag.get('do_not_post'):
        log(f"[DRY RUN] {title}"); return None
    wp = Client(_settings.wordpress_url, _settings.wordpress_id, _settings.wordpress_pw)
    existing = _get_existing_slugs(wp)
    if slug in existing:
        p = existing[slug]
        p.title, p.content = title, content
        p.custom_fields = [{'key': 'the_page_seo_title', 'value': seo_title},
                            {'key': 'the_page_meta_description', 'value': seo_desc}]
        if thumbnail_url and not p.thumbnail:
            mid = upload_thumbnail(wp, thumbnail_url, f"{slug}.jpg")
            if mid: p.thumbnail = mid
        wp.call(EditPost(p.id, p)); log(f"更新: {title} (ID:{p.id})"); return p.id
    post = WordPressPost()
    post.post_status = 'publish' if _settings.debug_flag.get('direct_post') else 'draft'
    post.title, post.content, post.slug = title, content, slug
    post.terms_names = {'post_tag': tags, 'category': [category]}
    post.custom_fields = [{'key': 'the_page_seo_title', 'value': seo_title},
                           {'key': 'the_page_meta_description', 'value': seo_desc}]
    if thumbnail_url:
        mid = upload_thumbnail(wp, thumbnail_url, f"{slug}.jpg")
        if mid: post.thumbnail = mid
    pid = wp.call(NewPost(post)); log(f"新規投稿: {title} (ID:{pid})"); return pid

def build_shop_html(rank, shop):
    name    = shop.get('name', '')
    url     = shop.get('urls', {}).get('pc', '#')
    img     = shop.get('photo', {}).get('mobile', {}).get('l', '')
    genre   = shop.get('genre', {}).get('name', '')
    access  = shop.get('access', '')[:60]
    budget  = shop.get('budget', {}).get('name', '')
    img_tag = f'<img src="{img}" alt="{name}" style="max-width:140px;float:left;margin-right:12px;">' if img else ''
    return f"""
<div style="clear:both;border:1px solid #ddd;padding:14px;margin-bottom:18px;border-radius:8px;">
  <h3 style="margin:0 0 6px">第{rank}位：{name}</h3>
  {img_tag}
  <p style="margin:2px 0">🍽️ ジャンル: <strong>{genre}</strong>　予算: {budget}</p>
  <p style="margin:2px 0;font-size:0.9em;color:#555">{access}</p>
  <p style="margin:6px 0"><a href="{url}" target="_blank" rel="nofollow">▶ Hotpepperで予約・クーポンを見る</a></p>
  <div style="clear:both"></div>
</div>"""

def generate_article(target_name):
    t = TARGETS[target_name]
    shops = fetch_hotpepper(t['area'], t['keyword'])
    if not shops:
        log(f"データなし: {target_name}"); return False

    names_sample = '、'.join([s.get('name','')[:20] for s in shops[:4]])
    lead = gpt(f"""{_settings.gpt_prompt}

テーマ: {target_name}
シチュエーション: {t['scene']}
代表的なお店例: {names_sample}

{t['scene']}で使えるお店を探している人向けに、このエリアのレストラン選びのポイントを200字程度で書いてください。""")

    items_html = ''.join(build_shop_html(i+1, s) for i, s in enumerate(shops))
    year, month = datetime.now().year, datetime.now().month
    title   = f"{target_name}TOP10【{year}年{month}月・Hotpepper掲載】"
    slug    = f"gourmet-{''.join(c for c in target_name if c.isalnum() or c in '-')[:40]}".lower()
    content = f"""<h2>{target_name}の選び方</h2>
<p>{lead}</p>

<h2>{target_name} おすすめTOP10</h2>
<p><small>※ {date.today()} 時点のHotpepper掲載情報をもとに作成</small></p>
{items_html}

<h2>まとめ</h2>
<p>{t['scene']}でお店を探している方は、ぜひランキングを参考にHotpepperでクーポン・予約をチェックしてみてください。</p>
"""
    area = target_name.split('×')[0]
    thumbnail = shops[0].get('photo', {}).get('mobile', {}).get('l') if shops else None
    result = wp_post(
        title=title, content=content, slug=slug, category=t['scene'],
        tags=[area, t['scene'], 'グルメ', 'レストラン', 'おすすめ', 'ランキング'],
        seo_title=title,
        seo_desc=f"{target_name}のおすすめレストランTOP10。{year}年{month}月最新・Hotpepper掲載。{t['scene']}のお店選びに。",
        thumbnail_url=thumbnail,
    )
    return result is not None

def run(args):
    if '--status' in args:
        s = load_schedule()
        for k in sorted(TARGETS, key=lambda x: s.get(x, '1970-01-01')):
            print(f"{k:<50} {s.get(k, '未更新')}")
        return
    force_all = '--all' in args
    target    = next((a for a in args if not a.startswith('--')), None)
    targets   = list(TARGETS) if force_all else \
                [k for k in TARGETS if target in k] if target else select_today()
    log(f"=== gourmet.niconavi.com 開始 [{date.today()}] {len(targets)}件 ===")
    schedule = load_schedule()
    ok = 0
    for t in targets:
        try:
            if generate_article(t):
                schedule[t] = date.today().isoformat()
                save_schedule(schedule); ok += 1
        except Exception as e:
            log(f"ERROR {t}: {e}")
    log(f"=== 完了 {ok}/{len(targets)}件 ===")

if __name__ == '__main__':
    run(sys.argv[1:])
