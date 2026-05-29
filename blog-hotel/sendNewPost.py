"""
hotel.niconavi.com — ホテル「特徴×エリア」特化ランキング

SEO差別化: 「東京 コスパホテル」「京都 絶景ホテル」「沖縄 ラグジュアリー」
じゃらん/楽天の総合ランキングと差別化。特徴別で検索意図に直撃。

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
RAKUTEN_API   = 'https://app.rakuten.co.jp/services/api/Travel/SimpleHotelSearch/20170426'
DAILY_UPDATE  = 15

TARGETS = {
    # コスパ重視
    "東京×コスパ最強ホテル":          {"keyword": "東京 コスパ ホテル", "feature": "コスパ重視"},
    "大阪×コスパ最強ホテル":          {"keyword": "大阪 コスパ ホテル", "feature": "コスパ重視"},
    "京都×コスパ最強ホテル":          {"keyword": "京都 コスパ ホテル", "feature": "コスパ重視"},
    "沖縄×コスパ最強ホテル":          {"keyword": "沖縄 コスパ ホテル", "feature": "コスパ重視"},
    # 絶景・眺望
    "東京×夜景が綺麗なホテル":        {"keyword": "東京 夜景 高層 ホテル", "feature": "絶景・夜景"},
    "沖縄×オーシャンビューホテル":    {"keyword": "沖縄 オーシャンビュー ホテル", "feature": "絶景・夜景"},
    "北海道×絶景ホテル":              {"keyword": "北海道 絶景 眺望 ホテル", "feature": "絶景・夜景"},
    "京都×古都の眺めホテル":          {"keyword": "京都 景色 眺望 ホテル", "feature": "絶景・夜景"},
    # ラグジュアリー
    "東京×ラグジュアリーホテル":      {"keyword": "東京 高級 ラグジュアリー ホテル", "feature": "ラグジュアリー"},
    "京都×高級ホテル":                {"keyword": "京都 高級 ホテル", "feature": "ラグジュアリー"},
    "沖縄×ラグジュアリーリゾート":    {"keyword": "沖縄 ラグジュアリー リゾート", "feature": "ラグジュアリー"},
    # ビジネス出張
    "東京×出張ビジネスホテル":        {"keyword": "東京 出張 ビジネスホテル", "feature": "ビジネス出張"},
    "大阪×出張ビジネスホテル":        {"keyword": "大阪 出張 ビジネスホテル", "feature": "ビジネス出張"},
    "名古屋×出張ビジネスホテル":      {"keyword": "名古屋 出張 ビジネスホテル", "feature": "ビジネス出張"},
    # 子連れ
    "東京×子連れファミリーホテル":    {"keyword": "東京 子連れ ファミリー ホテル", "feature": "子連れ・ファミリー"},
    "沖縄×子連れリゾートホテル":      {"keyword": "沖縄 子連れ リゾート ホテル", "feature": "子連れ・ファミリー"},
    # 記念日・デート
    "東京×記念日カップルホテル":      {"keyword": "東京 記念日 カップル ホテル", "feature": "記念日・カップル"},
    "京都×記念日カップルホテル":      {"keyword": "京都 記念日 カップル ホテル", "feature": "記念日・カップル"},
    "箱根×カップルにおすすめホテル":  {"keyword": "箱根 カップル おすすめ ホテル", "feature": "記念日・カップル"},
    "軽井沢×カップルにおすすめホテル":{"keyword": "軽井沢 カップル ホテル", "feature": "記念日・カップル"},
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

def fetch_rakuten(keyword, hits=10):
    try:
        r = requests.get(RAKUTEN_API, params={
            'applicationId': _settings.rakuten_app_id,
            'format': 'json', 'hits': hits,
            'keyword': keyword, 'sort': '+reviewAverage',
        }, timeout=15)
        hotels = r.json().get('hotels', [])
        return [h['hotel'][0]['hotelBasicInfo'] for h in hotels if 'hotel' in h]
    except Exception as e:
        log(f"楽天API エラー ({keyword}): {e}"); return []

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

def build_hotel_html(rank, h):
    name    = h.get('hotelName', '')
    url     = h.get('hotelInformationUrl', '#')
    img     = h.get('hotelImageUrl', '')
    review  = h.get('reviewAverage', '')
    price   = h.get('hotelMinCharge', '')
    access  = h.get('access', '')[:60]
    img_tag = f'<img src="{img}" alt="{name}" style="max-width:140px;float:left;margin-right:12px;">' if img else ''
    price_str = f"最安値: <strong>¥{price:,}</strong>〜" if price else ''
    return f"""
<div style="clear:both;border:1px solid #ddd;padding:14px;margin-bottom:18px;border-radius:8px;">
  <h3 style="margin:0 0 6px">第{rank}位：{name}</h3>
  {img_tag}
  <p style="margin:2px 0">⭐ {review}　{price_str}</p>
  <p style="margin:2px 0;font-size:0.9em;color:#555">{access}</p>
  <p style="margin:6px 0"><a href="{url}" target="_blank" rel="nofollow">▶ 楽天トラベルで詳細・予約を見る</a></p>
  <div style="clear:both"></div>
</div>"""

def generate_article(target_name):
    t = TARGETS[target_name]
    hotels = fetch_rakuten(t['keyword'])
    if not hotels:
        log(f"データなし: {target_name}"); return False

    names_sample = '、'.join([h.get('hotelName','')[:20] for h in hotels[:4]])
    lead = gpt(f"""{_settings.gpt_prompt}

テーマ: {target_name}
特徴: {t['feature']}
代表的なホテル例: {names_sample}

{t['feature']}を重視するユーザーに向けて、このエリアのホテル選びのポイントを200字程度で書いてください。""")

    hotels_html = ''.join(build_hotel_html(i+1, h) for i, h in enumerate(hotels))
    year, month = datetime.now().year, datetime.now().month
    title   = f"{target_name}TOP10【{year}年{month}月・口コミ評価順】"
    slug    = f"hotel-{''.join(c for c in target_name if c.isalnum() or c in '-')[:40]}".lower()
    content = f"""<h2>{target_name}の選び方</h2>
<p>{lead}</p>

<h2>{target_name} おすすめTOP10</h2>
<p><small>※ {date.today()} 時点の楽天トラベル口コミ評価をもとに作成</small></p>
{hotels_html}

<h2>まとめ</h2>
<p>{target_name}を探しているなら、上記ランキングを参考にしてください。予約は早めがおすすめです。</p>
"""
    thumbnail = hotels[0].get('hotelImageUrl') if hotels else None
    area = target_name.split('×')[0]
    result = wp_post(
        title=title, content=content, slug=slug, category=t['feature'],
        tags=[area, t['feature'], 'ホテル', 'おすすめ', 'ランキング', '楽天トラベル'],
        seo_title=title,
        seo_desc=f"{target_name}のおすすめホテルをTOP10で紹介。{year}年{month}月最新の口コミ評価順。{t['feature']}で選ぶホテルランキング。",
        thumbnail_url=thumbnail,
    )
    return result is not None

def print_status():
    s = load_schedule()
    today = date.today()
    print(f"\n{'ターゲット':<40} {'最終更新':<12}")
    print("-" * 55)
    for k in sorted(TARGETS, key=lambda x: s.get(x, '1970-01-01')):
        last = s.get(k, '未更新')
        days = f"{(today - date.fromisoformat(last)).days}日前" if last != '未更新' else '未更新'
        print(f"{k:<40} {last:<12} {days}")

def run(args):
    if '--status' in args: print_status(); return
    force_all = '--all' in args
    target    = next((a for a in args if not a.startswith('--')), None)
    targets   = list(TARGETS) if force_all else \
                [k for k in TARGETS if target in k] if target else select_today()
    log(f"=== hotel.niconavi.com 開始 [{date.today()}] {len(targets)}件 ===")
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
