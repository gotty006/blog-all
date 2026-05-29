"""
camp.niconavi.com — キャンプ場「設備特化×エリア」ランキング

SEO差別化: 「関東 グランピング おすすめ」「電源サイト キャンプ場」
設備・スタイル別に特化。総合ランキングと差別化。

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
    # グランピング
    "関東×グランピングができるキャンプ場":    {"keyword": "関東 グランピング キャンプ", "style": "グランピング"},
    "関西×グランピングができるキャンプ場":    {"keyword": "関西 グランピング キャンプ", "style": "グランピング"},
    "北海道×グランピングキャンプ場":          {"keyword": "北海道 グランピング キャンプ", "style": "グランピング"},
    "九州×グランピングキャンプ場":            {"keyword": "九州 グランピング キャンプ", "style": "グランピング"},
    # 電源サイト
    "関東×電源サイトあるキャンプ場":          {"keyword": "関東 電源サイト キャンプ場", "style": "電源サイト"},
    "関西×電源サイトあるキャンプ場":          {"keyword": "関西 電源サイト キャンプ場", "style": "電源サイト"},
    "東海×電源サイトあるキャンプ場":          {"keyword": "東海 電源サイト キャンプ場", "style": "電源サイト"},
    # ペット連れ
    "関東×ペット可キャンプ場":                {"keyword": "関東 ペット可 キャンプ場", "style": "ペット可"},
    "関西×ペット可キャンプ場":                {"keyword": "関西 ペット可 キャンプ場", "style": "ペット可"},
    "北海道×ペット可キャンプ場":              {"keyword": "北海道 ペット可 キャンプ場", "style": "ペット可"},
    # 子連れ・ファミリー
    "関東×子連れファミリーキャンプ場":        {"keyword": "関東 子連れ ファミリー キャンプ場", "style": "子連れ・ファミリー"},
    "関西×子連れファミリーキャンプ場":        {"keyword": "関西 子連れ ファミリー キャンプ場", "style": "子連れ・ファミリー"},
    # 海・川・絶景
    "関東×海が見えるキャンプ場":              {"keyword": "関東 海 キャンプ場", "style": "絶景・海・川"},
    "東海×川沿いキャンプ場":                  {"keyword": "東海 川沿い キャンプ場", "style": "絶景・海・川"},
    "九州×絶景キャンプ場":                    {"keyword": "九州 絶景 景色 キャンプ場", "style": "絶景・海・川"},
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

def build_camp_html(rank, h):
    name   = h.get('hotelName', '')
    url    = h.get('hotelInformationUrl', '#')
    img    = h.get('hotelImageUrl', '')
    review = h.get('reviewAverage', '')
    price  = h.get('hotelMinCharge', '')
    access = h.get('access', '')[:60]
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
    sites = fetch_rakuten(t['keyword'])
    if not sites:
        log(f"データなし: {target_name}"); return False

    names_sample = '、'.join([h.get('hotelName','')[:20] for h in sites[:4]])
    lead = gpt(f"""{_settings.gpt_prompt}

テーマ: {target_name}
スタイル: {t['style']}
代表的なキャンプ場例: {names_sample}

{t['style']}キャンプを楽しみたい人向けに、このエリアのキャンプ場選びのポイントを200字程度で書いてください。""")

    items_html = ''.join(build_camp_html(i+1, h) for i, h in enumerate(sites))
    year, month = datetime.now().year, datetime.now().month
    title   = f"{target_name}TOP10【{year}年{month}月・口コミ評価順】"
    slug    = f"camp-{''.join(c for c in target_name if c.isalnum() or c in '-')[:40]}".lower()
    content = f"""<h2>{target_name}の選び方</h2>
<p>{lead}</p>

<h2>{target_name} おすすめTOP10</h2>
<p><small>※ {date.today()} 時点の楽天トラベル口コミ評価をもとに作成</small></p>
{items_html}

<h2>まとめ</h2>
<p>{t['style']}キャンプを楽しみたい方は、ぜひランキングを参考に計画を立ててみてください。</p>
"""
    thumbnail = sites[0].get('hotelImageUrl') if sites else None
    area = target_name.split('×')[0]
    result = wp_post(
        title=title, content=content, slug=slug, category=t['style'],
        tags=[area, t['style'], 'キャンプ場', 'おすすめ', 'ランキング', 'アウトドア'],
        seo_title=title,
        seo_desc=f"{target_name}のおすすめキャンプ場TOP10。{year}年{month}月最新・口コミ評価順。{t['style']}に特化したキャンプ場ランキング。",
        thumbnail_url=thumbnail,
    )
    return result is not None

def run(args):
    if '--status' in args:
        s = load_schedule(); today = date.today()
        for k in sorted(TARGETS, key=lambda x: s.get(x, '1970-01-01')):
            last = s.get(k, '未更新')
            print(f"{k:<45} {last}")
        return
    force_all = '--all' in args
    target    = next((a for a in args if not a.startswith('--')), None)
    targets   = list(TARGETS) if force_all else \
                [k for k in TARGETS if target in k] if target else select_today()
    log(f"=== camp.niconavi.com 開始 [{date.today()}] {len(targets)}件 ===")
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
