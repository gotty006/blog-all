"""
movie.niconavi.com — 映画「気分・感情別」おすすめランキング

SEO差別化: 「泣ける映画 おすすめ」「元気が出る映画」「怖い映画 おすすめ」
Filmarks/映画.comの総合ランキングと差別化。「今の気分に合う映画」で検索意図に直撃。

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
TMDB_API      = 'https://api.themoviedb.org/3'
TMDB_IMG      = 'https://image.tmdb.org/t/p/w500'
DAILY_UPDATE  = 15

# TMDBジャンルID
GENRE_IDS = {
    "ロマンス": 10749, "アクション": 28, "コメディ": 35, "ホラー": 27,
    "ドラマ": 18, "アニメ": 16, "SF": 878, "スリラー": 53,
    "ファミリー": 10751, "ドキュメンタリー": 99,
}

TARGETS = {
    # 感情・気分別
    "泣ける映画×邦画・洋画おすすめ":          {"mood": "泣きたい気分", "genres": [18, 10749], "keyword": "感動 泣ける"},
    "元気が出る映画×やる気が出るおすすめ":    {"mood": "元気を出したい", "genres": [28, 35], "keyword": "元気 やる気 前向き"},
    "怖い映画×ガチで怖いホラーおすすめ":      {"mood": "ドキドキしたい", "genres": [27, 53], "keyword": "怖い ホラー"},
    "笑える映画×腹を抱えて笑えるコメディ":   {"mood": "笑いたい気分", "genres": [35], "keyword": "笑える コメディ"},
    "恋愛したくなる映画×ロマンスおすすめ":    {"mood": "恋愛気分になりたい", "genres": [10749, 18], "keyword": "恋愛 ロマンス"},
    "考えさせられる映画×深い映画おすすめ":    {"mood": "深く考えたい", "genres": [18, 99], "keyword": "考えさせられる 深い"},
    "興奮する映画×手に汗握るアクションおすすめ": {"mood": "興奮・スリルを味わいたい", "genres": [28, 53], "keyword": "アクション スリル"},
    "癒される映画×ほっこりする作品おすすめ":  {"mood": "癒されたい・ほっこりしたい", "genres": [10751, 35], "keyword": "癒し ほっこり"},
    # シチュエーション別
    "デートに見る映画×カップルにおすすめ":    {"mood": "デート・カップルで見たい", "genres": [10749, 35], "keyword": "カップル デート"},
    "子どもと見る映画×家族で楽しめるおすすめ": {"mood": "家族・子どもと見たい", "genres": [10751, 16], "keyword": "家族 子ども"},
    "一人で見る映画×深夜に見たいおすすめ":    {"mood": "一人でじっくり見たい", "genres": [18, 53], "keyword": "一人 夜"},
    "夏に見たい映画×夏を感じる作品おすすめ":  {"mood": "夏気分を味わいたい", "genres": [28, 10749], "keyword": "夏 青春"},
    # 日本語限定
    "邦画おすすめ×最近の日本映画傑作選":      {"mood": "日本映画を見たい", "genres": [18], "keyword": "日本 邦画"},
    "アニメ映画おすすめ×大人も楽しめる傑作":  {"mood": "アニメ映画を見たい", "genres": [16], "keyword": "アニメ 映画"},
    "Netflixで見られるおすすめ映画":          {"mood": "配信で手軽に見たい", "genres": [18, 28], "keyword": "Netflix 配信"},
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

def fetch_tmdb(genres, hits=10):
    try:
        genre_str = ','.join(str(g) for g in genres)
        r = requests.get(f"{TMDB_API}/discover/movie", params={
            'api_key': _settings.tmdb_api_key,
            'language': 'ja-JP',
            'sort_by': 'vote_average.desc',
            'vote_count.gte': 500,
            'with_genres': genre_str,
            'page': 1,
        }, timeout=15)
        return r.json().get('results', [])[:hits]
    except Exception as e:
        log(f"TMDB API エラー: {e}"); return []

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

def build_movie_html(rank, m):
    title_jp = m.get('title', m.get('name', ''))
    overview = m.get('overview', '')[:100]
    rating   = m.get('vote_average', '')
    year     = (m.get('release_date', '') or '')[:4]
    poster   = f"{TMDB_IMG}{m['poster_path']}" if m.get('poster_path') else ''
    img_tag  = f'<img src="{poster}" alt="{title_jp}" style="max-width:100px;float:left;margin-right:12px;">' if poster else ''
    return f"""
<div style="clear:both;border:1px solid #ddd;padding:14px;margin-bottom:18px;border-radius:8px;">
  <h3 style="margin:0 0 6px">第{rank}位：{title_jp}（{year}）</h3>
  {img_tag}
  <p style="margin:2px 0">⭐ 評価: <strong>{rating}</strong>/10</p>
  <p style="margin:4px 0;font-size:0.9em">{overview}</p>
  <div style="clear:both"></div>
</div>"""

def generate_article(target_name):
    t = TARGETS[target_name]
    movies = fetch_tmdb(t['genres'])
    if not movies:
        log(f"データなし: {target_name}"); return False

    titles_sample = '、'.join([m.get('title', m.get('name',''))[:20] for m in movies[:4]])
    lead = gpt(f"""{_settings.gpt_prompt}

テーマ: {target_name}
気分・状況: {t['mood']}
代表的な映画例: {titles_sample}

「{t['mood']}」ときにおすすめの映画を探している人向けに、このカテゴリの魅力を200字程度で書いてください。""")

    items_html = ''.join(build_movie_html(i+1, m) for i, m in enumerate(movies))
    year, month = datetime.now().year, datetime.now().month
    title   = f"{target_name}TOP10【{year}年{month}月・評価順】"
    slug    = f"movie-{''.join(c for c in target_name if c.isalnum() or c in '-')[:40]}".lower()
    content = f"""<h2>{target_name}の魅力</h2>
<p>{lead}</p>

<h2>{target_name} おすすめTOP10</h2>
<p><small>※ {date.today()} 時点のTMDB評価をもとに作成</small></p>
{items_html}

<h2>まとめ</h2>
<p>{t['mood']}ときは、ぜひランキングから自分に合った映画を見つけてみてください。</p>
"""
    first_poster = f"{TMDB_IMG}{movies[0]['poster_path']}" if movies and movies[0].get('poster_path') else None
    mood_short = t['mood'].split('・')[0]
    result = wp_post(
        title=title, content=content, slug=slug, category=mood_short,
        tags=[target_name.split('×')[0], t['mood'], '映画', 'おすすめ', 'ランキング'],
        seo_title=title,
        seo_desc=f"{target_name}のおすすめ映画TOP10。{year}年{month}月最新・TMDB評価順。{t['mood']}ときに見たい映画特集。",
        thumbnail_url=first_poster,
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
    log(f"=== movie.niconavi.com 開始 [{date.today()}] {len(targets)}件 ===")
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
