"""
scene.av2.jp — シーン・プレイ内容特化ランキング 自動生成・投稿スクリプト。

スケジューリング戦略:
  - 全50シーンを管理し、毎日「最終更新が古い順」上位N件を更新対象にする
  - FANZAのソート順を曜日で切り替え（月:新着/火:人気/水:評価/木:価格/金:新着...）
  - 更新後に data/scene_schedule.json に日時を記録 → 次回以降は後回し

使い方:
  python3 sendNewPost.py           # 本日分N件を自動選択して更新
  python3 sendNewPost.py --all     # 全50シーンを強制更新
  python3 sendNewPost.py NTR       # 指定シーンのみ（キーワード部分一致）
  python3 sendNewPost.py --status  # 各シーンの最終更新日を表示
"""
import sys
import os
import json
import urllib.parse
import requests
from datetime import datetime, date

import openai
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import NewPost, GetPosts, EditPost

sys.path.insert(0, 'submodule')
from submodule import _settings

LOG_FILE      = _settings.log_file
SCHEDULE_FILE = 'data/scene_schedule.json'
FANZA_API     = "https://api.dmm.com/affiliate/v3/ItemList"
API_ID        = "YrZt0XPJS1UAc6MNUkbz"
AFF_ID        = _settings.fanza_affiliate_id

# 1日あたり更新するシーン数
DAILY_UPDATE_COUNT = 15

# 曜日ごとのFANZAソート順（0=月曜）
DAILY_SORT = {0: 'date', 1: 'rank', 2: 'review', 3: 'popular', 4: 'date', 5: 'rank', 6: 'review'}

# 全50シーン定義（シーン名: FANZA検索キーワード）
SCENE_KEYWORDS = {
    # --- 定番プレイ ---
    "中出し":               "中出し",
    "フェラ・口内発射":      "フェラ 口内発射",
    "顔射":                 "顔射",
    "潮吹き":               "潮吹き",
    "手コキ":               "手コキ",
    "パイズリ":              "パイズリ",
    "アナル":               "アナル",
    "3P・乱交":             "乱交 3P",
    # --- ジャンル・キャラ ---
    "巨乳":                 "巨乳",
    "スレンダー":            "スレンダー",
    "ぽっちゃり":            "ぽっちゃり",
    "ギャル":               "ギャル",
    "黒ギャル":             "黒ギャル",
    "ロリ系":               "ロリ",
    "熟女・人妻":            "熟女 人妻",
    "若妻・新婚":            "若妻 新婚",
    "素人":                 "素人",
    "個人撮影":             "個人撮影",
    # --- 職業・コスプレ ---
    "コスプレ":             "コスプレ",
    "女教師":               "女教師",
    "OL":                  "OL",
    "ナース":               "ナース",
    "制服":                 "制服",
    "水着":                 "水着",
    "ランジェリー":          "ランジェリー",
    "メイド":               "メイド",
    "アイドル系":           "アイドル AV",
    # --- シチュエーション ---
    "NTR・寝取り・寝取られ": "NTR 寝取り",
    "レズ":                 "レズ 百合",
    "近親相姦":             "近親相姦",
    "義父・義兄":           "義父 義兄",
    "家庭教師":             "家庭教師",
    "同僚・職場":           "同僚 職場",
    "隣人":                 "隣人",
    "ナンパ":               "ナンパ",
    "温泉":                 "温泉",
    "野外露出":             "野外 露出",
    "マッサージ・エステ":   "マッサージ エステ",
    "痴漢":                 "痴漢",
    "催眠":                 "催眠",
    # --- プレイスタイル ---
    "縛り・SM":             "縛り SM",
    "電マ・バイブ":         "電マ バイブ",
    "オナニー":             "オナニー",
    "足コキ":               "足コキ",
    "着エロ":               "着エロ",
    # --- 属性 ---
    "黒人":                 "黒人",
    "ドM・ドS":             "ドM ドS",
    "お姉さん":             "お姉さん",
    "人妻不倫":             "人妻 不倫",
    "ぶっかけ":             "ぶっかけ",
}


# ─────────────────────────────────────────
# スケジューラー
# ─────────────────────────────────────────

def load_schedule():
    """data/scene_schedule.json を読み込む。なければ空dict。"""
    os.makedirs('data', exist_ok=True)
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_schedule(schedule):
    with open(SCHEDULE_FILE, 'w', encoding='utf-8') as f:
        json.dump(schedule, f, ensure_ascii=False, indent=2)


def select_today_scenes(n=DAILY_UPDATE_COUNT):
    """最終更新が古い順にn件のシーンを選ぶ。"""
    schedule = load_schedule()
    # 未更新シーンは epoch '1970-01-01' 扱い
    def last_updated(scene):
        return schedule.get(scene, '1970-01-01')
    sorted_scenes = sorted(SCENE_KEYWORDS.keys(), key=last_updated)
    return sorted_scenes[:n]


def today_sort():
    """曜日でFANZAソート順を返す。"""
    return DAILY_SORT[datetime.now().weekday()]


def print_status():
    """各シーンの最終更新日一覧を表示する。"""
    schedule = load_schedule()
    print(f"\n{'シーン':<25} {'最終更新':<12} {'経過日数':>6}")
    print("-" * 50)
    today = date.today()
    for scene in sorted(SCENE_KEYWORDS.keys(),
                        key=lambda s: schedule.get(s, '1970-01-01')):
        last = schedule.get(scene, '未更新')
        if last != '未更新':
            days = (today - date.fromisoformat(last)).days
            days_str = f"{days}日前"
        else:
            days_str = "未更新"
        print(f"{scene:<25} {last:<12} {days_str:>6}")


# ─────────────────────────────────────────
# FANZA・GPT・WordPress
# ─────────────────────────────────────────

def fetch_fanza(keyword, sort='rank', hits=10):
    try:
        r = requests.get(FANZA_API, params={
            "api_id": API_ID, "affiliate_id": AFF_ID,
            "site": "FANZA", "service": "digital", "floor": "videoa",
            "hits": hits, "sort": sort, "keyword": keyword, "output": "json"
        }, timeout=15)
        return r.json().get("result", {}).get("items", [])
    except Exception as e:
        log(f"FANZA API エラー ({keyword}): {e}")
        return []


def gpt(prompt):
    client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    res = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[{'role': 'user', 'content': prompt}],
        max_tokens=600,
    )
    return res.choices[0].message.content.strip()


def log(msg):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line)
    os.makedirs('data', exist_ok=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line + '\n')


def _get_existing_slugs(wp):
    posts = wp.call(GetPosts({'number': 500, 'post_status': 'any'}))
    return {urllib.parse.unquote(p.slug): p for p in posts}


def wp_post(title, content, slug, category, tags, seo_title, seo_desc):
    if _settings.debug_flag.get('do_not_post'):
        log(f"[DRY RUN] {title}")
        return None
    wp = Client(_settings.wordpress_url, _settings.wordpress_id, _settings.wordpress_pw)
    existing = _get_existing_slugs(wp)

    if slug in existing:
        p = existing[slug]
        p.content = content
        p.custom_fields = [
            {'key': 'the_page_seo_title',        'value': seo_title},
            {'key': 'the_page_meta_description',  'value': seo_desc},
        ]
        wp.call(EditPost(p.id, p))
        log(f"更新: {title} (ID:{p.id})")
        return p.id

    post = WordPressPost()
    post.post_status = 'publish' if _settings.debug_flag.get('direct_post') else 'draft'
    post.title       = title
    post.content     = content
    post.slug        = slug
    post.terms_names = {'post_tag': tags, 'category': [category]}
    post.custom_fields = [
        {'key': 'the_page_seo_title',        'value': seo_title},
        {'key': 'the_page_meta_description',  'value': seo_desc},
    ]
    post_id = wp.call(NewPost(post))
    log(f"新規投稿: {title} (ID:{post_id})")
    return post_id


def build_item_html(rank, item):
    title   = item.get('title', '')[:60]
    aff_url = item.get('affiliateURL', '#')
    thumb   = (item.get('imageURL') or {}).get('small', '')
    img_tag = f'<img src="{thumb}" alt="{title}" style="max-width:120px;float:left;margin-right:10px;">' if thumb else ''
    return f"""
<div style="clear:both;border:1px solid #eee;padding:12px;margin-bottom:16px;border-radius:6px;">
  <h3 style="margin:0 0 6px">第{rank}位：{title}</h3>
  {img_tag}
  <p style="margin:0;"><a href="{aff_url}" target="_blank" rel="nofollow">▶ FANZAで見る</a></p>
  <div style="clear:both"></div>
</div>
"""


# ─────────────────────────────────────────
# 記事生成
# ─────────────────────────────────────────

def generate_scene_ranking(scene_name, sort='rank'):
    keyword = SCENE_KEYWORDS.get(scene_name, scene_name)
    items   = fetch_fanza(keyword, sort=sort, hits=10)
    if not items:
        log(f"作品データなし: {scene_name}")
        return False

    titles_sample = '、'.join([it['title'][:25] for it in items[:5]])
    lead = gpt(f"""{_settings.gpt_prompt}

ジャンル: {scene_name}
人気作品例: {titles_sample}

このジャンルの魅力と、どんな人におすすめかを200字程度で書いてください。""")

    items_html = ''.join(build_item_html(i + 1, it) for i, it in enumerate(items))
    sort_label = {'date': '新着順', 'rank': '人気順', 'review': '評価順',
                  'popular': '注目順', 'price': '価格順'}.get(sort, '')

    year    = datetime.now().year
    month   = datetime.now().month
    title   = f"{scene_name}AVおすすめランキングTOP10【{year}年{month}月・{sort_label}】"
    slug    = f"ranking-{scene_name.replace('・','-').replace(' ','-').replace('/','').replace('P','p')}".lower()
    content = f"""<h2>{scene_name}AVとは？その魅力</h2>
<p>{lead}</p>

<h2>{scene_name} おすすめAVランキングTOP10（{sort_label}）</h2>
<p><small>※ {date.today().isoformat()} 時点のFANZAランキングを元に作成</small></p>
{items_html}

<h2>まとめ</h2>
<p>{scene_name}のAVは多彩な作品が揃っています。ランキングを参考に、お気に入りの作品を見つけてください。</p>
"""
    result = wp_post(
        title=title, content=content, slug=slug, category=scene_name,
        tags=[scene_name, 'AV', 'ランキング', 'おすすめ', 'FANZA', sort_label],
        seo_title=title,
        seo_desc=f"{scene_name}のAVおすすめ作品を{sort_label}で紹介。{year}年{month}月最新の人気{scene_name}AV TOP10を厳選。",
    )
    return result is not None


# ─────────────────────────────────────────
# エントリポイント
# ─────────────────────────────────────────

def run(args):
    if '--status' in args:
        print_status()
        return

    force_all = '--all' in args
    target    = next((a for a in args if not a.startswith('--')), None)
    sort      = today_sort()

    if force_all:
        scenes = list(SCENE_KEYWORDS.keys())
    elif target:
        scenes = [s for s in SCENE_KEYWORDS if target in s] or [target]
    else:
        scenes = select_today_scenes(DAILY_UPDATE_COUNT)

    log(f"=== scene.av2.jp 開始 [{date.today()} / sort={sort}] {len(scenes)}シーン ===")

    schedule = load_schedule()
    ok = 0
    for scene in scenes:
        try:
            if generate_scene_ranking(scene, sort=sort):
                schedule[scene] = date.today().isoformat()
                save_schedule(schedule)   # 1件ごとに保存（途中停止しても記録が残る）
                ok += 1
        except Exception as e:
            log(f"ERROR {scene}: {e}")

    log(f"=== 完了 {ok}/{len(scenes)}件 ===")


if __name__ == '__main__':
    run(sys.argv[1:])
