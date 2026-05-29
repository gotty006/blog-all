"""
onsen.niconavi.com — 温泉旅館「目的別×地域」特化ランキング

SEO差別化: 「箱根温泉 カップル おすすめ」「熱海 一人旅 旅館」等
目的×地域の組み合わせでロングテール大量獲得。
じゃらん/楽天トラベルの「総合ランキング」と差別化。

使い方:
  python3 sendNewPost.py          # 本日分15件
  python3 sendNewPost.py --all    # 全件強制更新
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

# 目的×地域 組み合わせ（SEO的に価値の高いロングテールキーワード）
TARGETS = {
    # カップル・記念日
    "箱根温泉×カップルにおすすめ旅館":    {"keyword": "箱根 カップル 温泉", "purpose": "カップル・記念日"},
    "熱海温泉×カップルにおすすめ旅館":    {"keyword": "熱海 カップル 温泉", "purpose": "カップル・記念日"},
    "草津温泉×カップルにおすすめ旅館":    {"keyword": "草津 カップル 温泉", "purpose": "カップル・記念日"},
    "別府温泉×カップルにおすすめ旅館":    {"keyword": "別府 カップル 温泉", "purpose": "カップル・記念日"},
    "有馬温泉×カップルにおすすめ旅館":    {"keyword": "有馬 カップル 温泉", "purpose": "カップル・記念日"},
    # 一人旅・ひとり温泉
    "箱根温泉×一人旅におすすめ旅館":      {"keyword": "箱根 一人旅 温泉", "purpose": "一人旅・ひとり温泉"},
    "城崎温泉×一人旅におすすめ旅館":      {"keyword": "城崎 一人旅 温泉", "purpose": "一人旅・ひとり温泉"},
    "道後温泉×一人旅におすすめ旅館":      {"keyword": "道後 一人旅 温泉", "purpose": "一人旅・ひとり温泉"},
    "登別温泉×一人旅におすすめ旅館":      {"keyword": "登別 一人旅 温泉", "purpose": "一人旅・ひとり温泉"},
    "湯布院温泉×一人旅におすすめ旅館":    {"keyword": "湯布院 一人旅 温泉", "purpose": "一人旅・ひとり温泉"},
    # 子連れ・家族旅行
    "箱根温泉×子連れにおすすめ旅館":      {"keyword": "箱根 子連れ 温泉", "purpose": "子連れ・家族旅行"},
    "伊豆温泉×子連れにおすすめ旅館":      {"keyword": "伊豆 子連れ 温泉", "purpose": "子連れ・家族旅行"},
    "白浜温泉×子連れにおすすめ旅館":      {"keyword": "白浜 子連れ 温泉", "purpose": "子連れ・家族旅行"},
    "那須温泉×子連れにおすすめ旅館":      {"keyword": "那須 子連れ 温泉", "purpose": "子連れ・家族旅行"},
    # 女子旅
    "箱根温泉×女子旅におすすめ旅館":      {"keyword": "箱根 女子旅 温泉", "purpose": "女子旅・女子会"},
    "熱海温泉×女子旅におすすめ旅館":      {"keyword": "熱海 女子旅 温泉", "purpose": "女子旅・女子会"},
    "湯布院温泉×女子旅におすすめ旅館":    {"keyword": "湯布院 女子旅 温泉", "purpose": "女子旅・女子会"},
    # 絶景・露天風呂
    "箱根温泉×絶景露天風呂の旅館":        {"keyword": "箱根 絶景 露天風呂", "purpose": "絶景・露天風呂"},
    "伊豆温泉×海が見える露天風呂の旅館":  {"keyword": "伊豆 海 露天風呂", "purpose": "絶景・露天風呂"},
    "北海道温泉×絶景露天風呂の旅館":      {"keyword": "北海道 絶景 露天風呂 温泉", "purpose": "絶景・露天風呂"},
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
            'keyword': keyword, 'hotSpringFlag': 1,
            'sort': '+reviewAverage',
        }, timeout=15)
        hotels = r.json().get('hotels', [])
        return [h['hotel'][0]['hotelBasicInfo'] for h in hotels if 'hotel' in h]
    except Exception as e:
        log(f"楽天API エラー ({keyword}): {e}")
        return []

def gpt(prompt):
    client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    res = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[{'role': 'user', 'content': prompt}],
        max_tokens=600,
    )
    return res.choices[0].message.content.strip()

def upload_thumbnail(wp, image_url, filename):
    try:
        resp = requests.get(image_url, timeout=10)
        if resp.status_code != 200:
            return None
        result = wp.call(UploadFile({'name': filename, 'type': 'image/jpeg',
                                      'bits': xmlrpc.client.Binary(resp.content)}))
        return result.get('id')
    except Exception as e:
        log(f"サムネ失敗: {e}")
        return None

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
    name     = h.get('hotelName', '')
    url      = h.get('hotelInformationUrl', '#')
    img      = h.get('hotelImageUrl', '')
    review   = h.get('reviewAverage', '')
    price    = h.get('hotelMinCharge', '')
    access   = h.get('access', '')[:60]
    img_tag  = f'<img src="{img}" alt="{name}" style="max-width:140px;float:left;margin-right:12px;">' if img else ''
    price_str = f"最安値: <strong>¥{price:,}</strong>〜" if price else ''
    return f"""
<div style="clear:both;border:1px solid #ddd;padding:14px;margin-bottom:18px;border-radius:8px;">
  <h3 style="margin:0 0 6px">第{rank}位：{name}</h3>
  {img_tag}
  <p style="margin:2px 0">⭐ 口コミ評価: <strong>{review}</strong>　{price_str}</p>
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
目的: {t['purpose']}
代表的な旅館例: {names_sample}

{t['purpose']}旅行を考えている人に向けて、この温泉地・旅館の魅力を200字程度で書いてください。""")

    hotels_html = ''.join(build_hotel_html(i+1, h) for i, h in enumerate(hotels))
    year, month = datetime.now().year, datetime.now().month
    title = f"{target_name}TOP10【{year}年{month}月・口コミ評価順】"
    slug  = f"onsen-{''.join(c for c in target_name if c.isalnum() or c in '-')[:40]}".lower()
    content = f"""<h2>{target_name}とは？</h2>
<p>{lead}</p>

<h2>{target_name} おすすめTOP10</h2>
<p><small>※ {date.today()} 時点の楽天トラベル口コミ評価をもとに作成</small></p>
{hotels_html}

<h2>まとめ</h2>
<p>{target_name.split('×')[0]}で{t['purpose']}旅行を計画中の方は、ぜひランキング上位の旅館をチェックしてみてください。早めの予約がおすすめです。</p>
"""
    thumbnail = hotels[0].get('hotelImageUrl') if hotels else None
    result = wp_post(
        title=title, content=content, slug=slug, category=t['purpose'],
        tags=[target_name.split('×')[0].replace('温泉',''), '温泉', t['purpose'], '旅館', 'おすすめ', 'ランキング'],
        seo_title=title,
        seo_desc=f"{target_name}のおすすめ旅館をTOP10でご紹介。{year}年{month}月の楽天トラベル口コミ評価順。{t['purpose']}旅行の宿選びに。",
        thumbnail_url=thumbnail,
    )
    return result is not None

def print_status():
    s = load_schedule()
    today = date.today()
    print(f"\n{'ターゲット':<40} {'最終更新':<12} {'経過':>6}")
    print("-" * 62)
    for k in sorted(TARGETS, key=lambda x: s.get(x, '1970-01-01')):
        last = s.get(k, '未更新')
        days = f"{(today - date.fromisoformat(last)).days}日前" if last != '未更新' else '未更新'
        print(f"{k:<40} {last:<12} {days:>6}")

def run(args):
    if '--status' in args: print_status(); return
    force_all = '--all' in args
    target    = next((a for a in args if not a.startswith('--')), None)
    targets   = list(TARGETS) if force_all else \
                [k for k in TARGETS if target in k] if target else select_today()

    log(f"=== onsen.niconavi.com 開始 [{date.today()}] {len(targets)}件 ===")
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
