"""
vod.av2.jp — VODサービス比較・ガイド記事 自動生成・投稿スクリプト。

使い方:
  python3 sendNewPost.py service_review   # サービスレビュー記事
  python3 sendNewPost.py comparison       # 2サービス比較記事
  python3 sendNewPost.py all              # 全タイプ実行
"""
import sys
import os
from datetime import datetime

import openai
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import NewPost

sys.path.insert(0, 'submodule')
from submodule import _settings

LOG_FILE = _settings.log_file


def log(msg):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line)
    os.makedirs('data', exist_ok=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line + '\n')


def gpt(prompt):
    client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    res = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[{'role': 'user', 'content': prompt}],
        max_tokens=800,
    )
    return res.choices[0].message.content.strip()


def wp_post(title, content, slug, category, tags, seo_title, seo_desc):
    if _settings.debug_flag.get('do_not_post'):
        log(f"[DRY RUN] {title}")
        return None
    wp = Client(_settings.wordpress_url, _settings.wordpress_id, _settings.wordpress_pw)
    post = WordPressPost()
    post.post_status = 'publish' if _settings.debug_flag.get('direct_post') else 'draft'
    post.title = title
    post.content = content
    post.slug = slug
    post.terms_names = {'post_tag': tags, 'category': [category]}
    post.custom_fields = [
        {'key': 'the_page_seo_title', 'value': seo_title},
        {'key': 'the_page_meta_description', 'value': seo_desc},
    ]
    post_id = wp.call(NewPost(post))
    log(f"投稿完了: {title} (ID:{post_id})")
    return post_id


def generate_service_review(svc):
    name = svc['name']
    price_str = "無料（都度課金）" if svc.get('monthly_price', 0) == 0 else f"{svc['monthly_price']}円/月"
    trial_str = f"{svc['free_trial_days']}日間無料体験あり" if svc.get('free_trial_days', 0) > 0 else "無料体験なし"
    features_str = '・'.join(svc.get('features', []))

    body = gpt(f"""{_settings.gpt_prompts['service_review']}

サービス名: {name}
料金: {price_str}
無料体験: {trial_str}
特徴: {features_str}""")

    title = f"{name}の評判・口コミ｜料金・特徴・使い方を徹底解説【{datetime.now().year}年版】"
    slug = f"review-{name.lower().replace(' ','').replace('動画','').replace('プレミアム','premium')}"
    content = f"""<h2>{name}とは？</h2>
<p>月額料金: <strong>{price_str}</strong>　無料体験: <strong>{trial_str}</strong></p>
<ul>{"".join(f"<li>{f}</li>" for f in svc.get("features", []))}</ul>

<h2>詳細レビュー</h2>
<p>{body}</p>

<h2>登録方法</h2>
<p>{name}への登録は公式サイトから簡単に行えます。まず公式サイトにアクセスし、会員登録ボタンをクリックして必要事項を入力するだけです。</p>

<h2>まとめ</h2>
<p>{name}は{features_str}が特徴のAV動画配信サービスです。{trial_str}を活用して、まずは試してみることをおすすめします。</p>
"""
    wp_post(
        title=title,
        content=content,
        slug=slug,
        category='サービスレビュー',
        tags=[name, 'AV動画', 'VOD', '動画配信サービス', 'レビュー'],
        seo_title=title,
        seo_desc=f"{name}の料金・特徴・評判を徹底解説。{trial_str}の情報や登録・解約方法もわかりやすく紹介します。",
    )


def generate_howto(svc, article_type):
    """登録・解約・無料体験 ハウツー記事を生成。article_type: register / cancel / trial"""
    name = svc['name']
    type_map = {
        'register': ('登録方法', '登録手順', 'register'),
        'cancel':   ('解約方法', '解約手順', 'cancel'),
        'trial':    ('無料体験のやり方', '無料体験の使い方', 'trial'),
    }
    label, prompt_label, slug_suffix = type_map[article_type]

    body = gpt(f"""{_settings.gpt_prompts['howto']}

サービス名: {name}
記事タイプ: {prompt_label}""")

    title = f"{name}の{label}を徹底解説【{datetime.now().year}年最新・画像付き】"
    slug = f"howto-{name.lower().replace(' ','').replace('動画','').replace('プレミアム','premium')}-{slug_suffix}"
    content = f"""<h2>{name}の{label}</h2>
<p>{body}</p>

<h2>まとめ</h2>
<p>{name}の{label}はシンプルで簡単です。不明点があれば公式サポートへご連絡ください。</p>
"""
    wp_post(
        title=title,
        content=content,
        slug=slug,
        category='使い方ガイド',
        tags=[name, label, 'AV動画', 'VOD', '使い方'],
        seo_title=title,
        seo_desc=f"{name}の{label}を画像付きでわかりやすく解説。{datetime.now().year}年最新版。",
    )


def generate_comparison(svc_a, svc_b):
    na, nb = svc_a['name'], svc_b['name']
    pa = "無料" if svc_a.get('monthly_price', 0) == 0 else f"{svc_a['monthly_price']}円"
    pb = "無料" if svc_b.get('monthly_price', 0) == 0 else f"{svc_b['monthly_price']}円"

    body = gpt(f"""{_settings.gpt_prompts['comparison']}

{na}（月額{pa}）と{nb}（月額{pb}）を比較してください。""")

    title = f"{na}と{nb}を徹底比較！どっちがおすすめ？【{datetime.now().year}年最新】"
    slug = f"compare-{''.join([c for c in na if c.isalnum()])[:6]}-{''.join([c for c in nb if c.isalnum()])[:6]}".lower()
    content = f"""<h2>{na} vs {nb} 比較表</h2>
<table border="1" cellpadding="8" style="border-collapse:collapse;width:100%">
<thead><tr><th>比較項目</th><th>{na}</th><th>{nb}</th></tr></thead>
<tbody>
<tr><td>月額料金</td><td>{pa}</td><td>{pb}</td></tr>
<tr><td>無料体験</td><td>{"あり（"+str(svc_a.get("free_trial_days",0))+"日間）" if svc_a.get("free_trial_days",0)>0 else "なし"}</td><td>{"あり（"+str(svc_b.get("free_trial_days",0))+"日間）" if svc_b.get("free_trial_days",0)>0 else "なし"}</td></tr>
</tbody></table>

<h2>詳しい比較</h2>
<p>{body}</p>

<h2>結論：どっちがおすすめ？</h2>
<p>料金重視なら<strong>{na if svc_a.get("monthly_price",0) <= svc_b.get("monthly_price",0) else nb}</strong>、作品の幅広さを重視するなら両方を試してみることをおすすめします。</p>
"""
    wp_post(
        title=title,
        content=content,
        slug=slug,
        category='サービス比較',
        tags=[na, nb, 'AV動画', 'VOD比較', '動画配信'],
        seo_title=title,
        seo_desc=f"{na}と{nb}の料金・作品数・特徴を徹底比較。あなたに合ったAV動画サービスを選ぶための完全ガイドです。",
    )


def run(article_type='all'):
    """
    使い方:
      python3 sendNewPost.py                # all（全タイプ）
      python3 sendNewPost.py service_review
      python3 sendNewPost.py comparison
      python3 sendNewPost.py howto
    """
    services = _settings.vod_services
    log(f"=== vod.av2.jp 記事生成開始 [{article_type}] ({len(services)}サービス) ===")

    if article_type in ('service_review', 'all'):
        for svc in services:
            try:
                generate_service_review(svc)
            except Exception as e:
                log(f"ERROR service_review {svc['name']}: {e}")

    if article_type in ('comparison', 'all'):
        for i in range(len(services)):
            for j in range(i + 1, len(services)):
                try:
                    generate_comparison(services[i], services[j])
                except Exception as e:
                    log(f"ERROR comparison {services[i]['name']} vs {services[j]['name']}: {e}")

    if article_type in ('howto', 'all'):
        for svc in services:
            for htype in ('register', 'cancel', 'trial'):
                try:
                    generate_howto(svc, htype)
                except Exception as e:
                    log(f"ERROR howto {svc['name']} {htype}: {e}")

    log("=== 完了 ===")


if __name__ == '__main__':
    run(sys.argv[1] if len(sys.argv) > 1 else 'all')
