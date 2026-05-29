"""
golf.niconavi.com — ゴルフ場「難易度×料金×エリア」特化ランキング

SEO差別化: 「神奈川 初心者 ゴルフ場 安い」「関東 コスパ ゴルフ場」
楽天GORAの総合ランキングと差別化。目的別・予算別で検索意図に直撃。

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
GORA_API      = 'https://app.rakuten.co.jp/services/api/Gora/GoraGolfCourseSearch/20170623'
DAILY_UPDATE  = 15

# エリアコード（楽天GORA）
AREA_CODES = {
    "関東": "03", "関西": "06", "東海": "05", "東北": "02",
    "北海道": "01", "九州": "09", "中国": "07", "四国": "08",
}

TARGETS = {
    # 初心者向け
    "関東×初心者向けゴルフ場":          {"area": "03", "keyword": "初心者 フラット", "category": "初心者向け"},
    "関西×初心者向けゴルフ場":          {"area": "06", "keyword": "初心者 フラット", "category": "初心者向け"},
    "東海×初心者向けゴルフ場":          {"area": "05", "keyword": "初心者 フラット", "category": "初心者向け"},
    "北海道×初心者向けゴルフ場":        {"area": "01", "keyword": "初心者 フラット", "category": "初心者向け"},
    # 安い・コスパ
    "関東×格安ゴルフ場コスパ最強":      {"area": "03", "keyword": "格安 コスパ", "category": "格安・コスパ"},
    "関西×格安ゴルフ場コスパ最強":      {"area": "06", "keyword": "格安 コスパ", "category": "格安・コスパ"},
    "東海×格安ゴルフ場コスパ最強":      {"area": "05", "keyword": "格安 コスパ", "category": "格安・コスパ"},
    # 名門・上級者
    "関東×名門ゴルフ場上級者向け":      {"area": "03", "keyword": "名門 難易度 上級者", "category": "名門・上級者向け"},
    "関西×名門ゴルフ場上級者向け":      {"area": "06", "keyword": "名門 難易度 上級者", "category": "名門・上級者向け"},
    # リゾート・景色
    "北海道×絶景リゾートゴルフ場":      {"area": "01", "keyword": "リゾート 絶景 景色", "category": "リゾート・絶景"},
    "沖縄×リゾートゴルフ場":            {"area": "10", "keyword": "リゾート 海", "category": "リゾート・絶景"},
    "九州×絶景ゴルフ場":                {"area": "09", "keyword": "リゾート 絶景", "category": "リゾート・絶景"},
    # 手軽に1ラウンド
    "関東×1人予約できるゴルフ場":        {"area": "03", "keyword": "1人予約 ひとり", "category": "1人予約OK"},
    "関西×1人予約できるゴルフ場":        {"area": "06", "keyword": "1人予約 ひとり", "category": "1人予約OK"},
    # 女性・レディース
    "関東×女性歓迎ゴルフ場":            {"area": "03", "keyword": "レディース 女性 歓迎", "category": "レディース・女性向け"},
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
    os.makedirs('data', exist_ok=True)
    open(LOG_FILE, 'a', encoding='utf-8').write(line + '\n')

def fetch_gora(area_code, keyword, hits=10):
    try:
        r = requests.get(GORA_API, params={
            'applicationId': _settings.rakuten_app_id,
            'format': 'json', 'hits': hits,
            'areaCode': area_code, 'keyword': keyword,
            'sort': 'rating',
        }, timeout=15)
        return r.json().get('Items', [])
    except Exception as e:
        log(f"GORA API エラー: {e}"); return []

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

def build_golf_html(rank, item):
    g       = item.get('Item', item)
    name    = g.get('golfCourseName', '')
    url     = g.get('golfCourseDetailUrl', '#')
    img     = g.get('golfCourseImageUrl', '')
    rating  = g.get('rating', '')
    price   = g.get('weekdayMinPrice', '')
    access  = g.get('access', '')[:60]
    holes   = g.get('holes', '')
    img_tag = f'<img src="{img}" alt="{name}" style="max-width:140px;float:left;margin-right:12px;">' if img else ''
    return f"""
<div style="clear:both;border:1px solid #ddd;padding:14px;margin-bottom:18px;border-radius:8px;">
  <h3 style="margin:0 0 6px">第{rank}位：{name}</h3>
  {img_tag}
  <p style="margin:2px 0">⭐ 評価: <strong>{rating}</strong>　ホール数: {holes}</p>
  <p style="margin:2px 0">平日最安: <strong>¥{price:,}〜</strong></p>
  <p style="margin:2px 0;font-size:0.9em;color:#555">{access}</p>
  <p style="margin:6px 0"><a href="{url}" target="_blank" rel="nofollow">▶ 楽天GORAで予約する</a></p>
  <div style="clear:both"></div>
</div>""" if price else f"""
<div style="clear:both;border:1px solid #ddd;padding:14px;margin-bottom:18px;border-radius:8px;">
  <h3 style="margin:0 0 6px">第{rank}位：{name}</h3>
  {img_tag}
  <p style="margin:2px 0">⭐ 評価: <strong>{rating}</strong>　ホール数: {holes}</p>
  <p style="margin:2px 0;font-size:0.9em;color:#555">{access}</p>
  <p style="margin:6px 0"><a href="{url}" target="_blank" rel="nofollow">▶ 楽天GORAで予約する</a></p>
  <div style="clear:both"></div>
</div>"""

def generate_article(target_name):
    t = TARGETS[target_name]
    items = fetch_gora(t['area'], t['keyword'])
    if not items:
        log(f"データなし: {target_name}"); return False

    names_sample = '、'.join([item.get('Item', item).get('golfCourseName','')[:20] for item in items[:4]])
    lead = gpt(f"""{_settings.gpt_prompt}

テーマ: {target_name}
カテゴリ: {t['category']}
代表的なゴルフ場例: {names_sample}

{t['category']}を重視するゴルファーに向けて、このエリアのゴルフ場選びのポイントを200字程度で書いてください。""")

    items_html = ''.join(build_golf_html(i+1, item) for i, item in enumerate(items))
    year, month = datetime.now().year, datetime.now().month
    title   = f"{target_name}TOP10【{year}年{month}月・評価順】"
    slug    = f"golf-{''.join(c for c in target_name if c.isalnum() or c in '-')[:40]}".lower()
    content = f"""<h2>{target_name}の選び方</h2>
<p>{lead}</p>

<h2>{target_name} おすすめTOP10</h2>
<p><small>※ {date.today()} 時点の楽天GORA評価をもとに作成</small></p>
{items_html}

<h2>まとめ</h2>
<p>{target_name}を探しているゴルファーは、ぜひランキングを参考に楽天GORAで予約してみてください。</p>
"""
    first = items[0].get('Item', items[0]) if items else {}
    thumbnail = first.get('golfCourseImageUrl')
    area = target_name.split('×')[0]
    result = wp_post(
        title=title, content=content, slug=slug, category=t['category'],
        tags=[area, t['category'], 'ゴルフ場', 'おすすめ', 'ランキング', '楽天GORA'],
        seo_title=title,
        seo_desc=f"{target_name}のおすすめゴルフ場をTOP10で紹介。{year}年{month}月最新の評価順。{t['category']}ゴルフ場ランキング。",
        thumbnail_url=thumbnail,
    )
    return result is not None

def run(args):
    if '--status' in args:
        s = load_schedule(); today = date.today()
        for k in sorted(TARGETS, key=lambda x: s.get(x, '1970-01-01')):
            last = s.get(k, '未更新')
            days = f"{(today - date.fromisoformat(last)).days}日前" if last != '未更新' else '未更新'
            print(f"{k:<45} {last:<12} {days}")
        return
    force_all = '--all' in args
    target    = next((a for a in args if not a.startswith('--')), None)
    targets   = list(TARGETS) if force_all else \
                [k for k in TARGETS if target in k] if target else select_today()
    log(f"=== golf.niconavi.com 開始 [{date.today()}] {len(targets)}件 ===")
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
