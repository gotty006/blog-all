import inspect
import requests
import traceback
from urllib.parse import urlparse
from submodule import googleTranslate
from submodule import _settings
#import _settings
from bs4 import BeautifulSoup
from datetime import datetime
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.compat import xmlrpc_client
from wordpress_xmlrpc.methods import media, posts
from wordpress_xmlrpc.methods.posts import GetPosts, NewPost, EditPost
#SSL通信をするときにLocal側に証明書が必要
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

#変数を定義
id=_settings.wordpress_id
password=_settings.wordpress_pw
url=_settings.wordpress_url  #第3者が閲覧するURLの後ろに/xmlrpc.phpをつける。

# WEB上の画像をWPサーバにアップロード
def upload_file_from_web(image_url):
    # シュリンクモードの場合、処理割愛
    if _settings.type == 'bulk_post_shrink' or _settings.debug_flag['do_not_upload_img']:
        return image_url

    try :
        #クライアントの呼び出し
        wp = Client(url, id,password)
        uploaded_image_url = None

        print("Start upload : ",image_url)
        # 画像をダウンロードしてWordPressサーバにアップロード
        with requests.get(image_url, stream=True) as r:
            if r.status_code == 200:
                file_name = urlparse(image_url).path.split('/')[-1]

                # 画像のメタデータを準備
                data = {
                    'name': file_name,
                    'type': 'image/jpeg',  # 画像のMIMEタイプ
                }

                # 画像をバイナリ形式で読み取り、XMLRPCライブラリによってBase64エンコードされる
                data['bits'] = xmlrpc_client.Binary(r.content)

                # WordPressメディアライブラリにファイルをアップロード
                response = wp.call(media.UploadFile(data))
                
                # アップロードされた画像のURLを取得
                uploaded_image_url = response['url']
                print("Uploaded image URL:", uploaded_image_url)

                return uploaded_image_url

            else:
                print("Failed to download the image")
                return(image_url)

    except Exception as e:
        print("[ERROR] Upload image URL:", image_url)
        # エラーメッセージを表示
        print(f"Exception occurred: {e}")
        # スタックトレースを出力
        traceback.print_exc()


# サムネイルアップロード
def upload_file(file_path, site=None):
    wp_url = url
    if site:
        wp_url = site['url'] + "xmlrpc.php"

    #クライアントの呼び出し
    wp = Client(wp_url, id,password)

    if file_path.endswith('gif'):
        type = 'image/gif'
    else:
        type = 'image/jpeg'


    # prepare metadata
    data = {
            'name': file_path.split('/')[-1],
            'type': type,  # mimetype
    }

    if file_path.startswith('http'):
        # webからアップロード
        # 画像をダウンロードしてWordPressサーバにアップロード
        with requests.get(file_path, stream=True) as r:
            if r.status_code == 200:
                # 画像のメタデータを準備
                data = {
                    'name': file_path.split('/')[-1],  # ファイル名はURLから取得
                    'type': type,  # 画像のMIMEタイプ
                }

                # 画像をバイナリ形式で読み取り、XMLRPCライブラリによってBase64エンコードされる
                data['bits'] = xmlrpc_client.Binary(r.content)

    else:
        # ローカルからアップロード
        # read the binary file and let the XMLRPC library encode it into base64
        with open(file_path, 'rb') as img:
                data['bits'] = xmlrpc_client.Binary(img.read())

    response = wp.call(media.UploadFile(data))
    # response == {
    #       'id': 6,
    #       'file': 'picture.jpg'
    #       'url': 'http://www.example.com/wp-content/uploads/2012/04/16/picture.jpg',
    #       'type': 'image/jpeg',
    # }
    attachment_id = response['id']
    image_url = response['url']

    return attachment_id, image_url


def updatePost(post_data, site=None):
    wp_url = url
    if site:
        wp_url = site['url'] + "xmlrpc.php"

    #クライアントの呼び出しなど
    wp = Client(wp_url, id,password)
    post = WordPressPost()

    #実際に投稿する
    post.post_status = post_data['which']
    post.title = googleTranslate.translate_japanese_to_english(post_data['title'], site['lang'])
    post.content = post_data['content']
    post.slug = post_data['slug']
    post.excerpt = googleTranslate.translate_japanese_to_english(post_data['excerpt'], site['lang'])
    if post_data['attachment_id']:
        post.thumbnail = post_data['attachment_id']
    if site['lang'] == '':
        post.terms_names = {
        "post_tag": post_data['tags'],
        "category": post_data['category']
        }
    else:
        post.terms_names = {
        "post_tag": [googleTranslate.translate_japanese_to_english(post_data['tags'][0], site['lang'])],
        "category": [googleTranslate.translate_japanese_to_english(post_data['category'][0], site['lang'])]
        }
    post.custom_fields = post_data['custom_fields']

    # 更新対象のpost_idを特定
    post_url = site['url'] + post.slug + '/'
    post_id = get_post_id_via_html(post_url)
    print('site url: ' + str(post_id))

    # try: 
    #     print(url)
    #     print(url)
    #     print('debug 1')
    #     posts = wp.call(GetPosts({'number': 10000}))
    #     print('debug 2')
    #     print(posts)
    #     matching_posts = [p for p in posts if p.slug == post.slug]
    #     print('debug 3')
    #     post_id = matching_posts[0].id if matching_posts else None
    #     print('debug 4')
    #     print('wp.call: ' + str(post_id))
    # except Exception as e:
    #     print(f"Exception occurred: {e}")
    #     traceback.print_exc()
    #     print('debug 5')
    #     post_url = site['url'] + post.slug + '/'
    #     post_id = get_post_id_via_html(post_url)
    #     print('site url: ' + str(post_id))

    # マッチした投稿のIDを更新
    if post_id:
        #すでに記事があれば更新
        print(f"マッチした投稿のID: {post_id}")
        # 更新実行
        new_post = wp.call(EditPost(post_id, post))
        return new_post
    else:
        #記事がなければ新規作成
        print("マッチしたのがないため、新規投稿!!!")
        new_post = newPost(post_data, site)
        return new_post


def newPost(post_data, site=None):
    wp_url = url
    if site:
        wp_url = site['url'] + "xmlrpc.php"
    else:
        site = {'lang': ''}

    #クライアントの呼び出しなど
    wp = Client(wp_url, id,password)
    post = WordPressPost()

    #実際に投稿する
    post.post_status = post_data['which']
    post.title = googleTranslate.translate_japanese_to_english(post_data['title'], site['lang'])
    post.content = post_data['content']
    post.slug = post_data['slug']
    post.excerpt = googleTranslate.translate_japanese_to_english(post_data['excerpt'], site['lang'])
    if post_data['attachment_id']:
        post.thumbnail = post_data['attachment_id']
    if site['lang'] == '':
        post.terms_names = {
        "post_tag": post_data['tags'],
        "category": post_data['category']
        }
    else:
        post.terms_names = {
        "post_tag": [googleTranslate.translate_japanese_to_english(post_data['tags'][0], site['lang'])],
        "category": [googleTranslate.translate_japanese_to_english(post_data['category'][0], site['lang'])]
        }
    post.custom_fields = post_data['custom_fields']
    #過去に投稿した記事としたい場合、投稿日をここで指定。例として2018年1月1日10時5分10秒に投稿した例を示す。
    #post.date= post_date
    new_post = wp.call(NewPost(post))

    return new_post


def create_new_post(video_ranking_data, attachment_id, url, index, type='video', synopsis='', title='', site=None, post_category=None, post_tags=None):
    # 現在の関数名を取得(log用)
    current_function_name = inspect.currentframe().f_code.co_name
    print("Start: ", current_function_name)

    post_data = {}
    #下書きに投稿するか本番で投稿するか選択
    post_data['which'] = "draft"
    if _settings.debug_flag['direct_post']:
        post_data['which'] = "publish"

    #Meta情報を生成
    if type in _settings.single_type_list or type.endswith('_list'):
        post_data['excerpt'] = synopsis
        #post_data['title'] = f"【{video_ranking_data['actress']}】{video_ranking_data['title']}"
        post_data['title'] = title

        # '_list' で一致した場合はother_list
        if (not type in _settings.allow_tag_list and type.endswith('_list')) or site:
            if video_ranking_data['actress'] != '':
                post_data['tags'] = [video_ranking_data['actress']]
            else:
                post_data['tags'] = ['その他']
        else:
            tags = list(set(video_ranking_data['meta']['genre_list']) & set(_settings.allow_tag_list[type]))
            post_data['tags'] = tags[:5]

        post_data['slug'] = url
        post_data['attachment_id'] = attachment_id
        post_data['custom_fields'] = [{},{},{}]
        #post_data['custom_fields'][0]['key'] = 'the_page_meta_keywords'
        #post_data['custom_fields'][0]['value'] = f"口コミ,おすすめ,人気,抜ける,アダルトビデオ"
        post_data['custom_fields'][0]['key'] = 'the_page_seo_title'
        post_data['custom_fields'][0]['value'] = f"【無料動画】{title}"
        post_data['custom_fields'][1]['key'] = 'the_page_meta_description'
        post_data['custom_fields'][1]['value'] = synopsis
        post_data['custom_fields'][2]['key'] = 'the_page_meta_keywords'
        if site and 'post_tag_list' in site:
            post_data['custom_fields'][2]['value'] = f"{video_ranking_data['actress']},AV,アダルト,口コミ,{','.join(site['post_tag_list'])},{url}"
        else:
            post_data['custom_fields'][2]['value'] = f"{video_ranking_data['actress']},AV,アダルト,口コミ"

        # bulk_postのカテゴリ設定
        if site:
            if type != 'dojin_list':
                post_data['category'] = ['その他' + site['prompt_word']]
                for category in site['set_category_list']:
                    if category in video_ranking_data['meta']['genre_list']:
                        post_data['category'] = [category + site['prompt_word']]
                        break
            else:
                post_data['category'] = [video_ranking_data['category']]

                    
        elif not (type in _settings.specialized_genre_list or type in _settings.specialized_prompt_word) :
            if video_ranking_data['actress'] != '':
                post_data['category'] = [video_ranking_data['actress']]
            else:
                post_data['category'] = ['その他']
                
        else:
            post_data['category'] = [video_ranking_data['category']]

    else:
        if type == 'video':
            genre = "AV"
            post_data['excerpt'] = f"今最も抜ける{video_ranking_data['category']}系の人気AV(アダルトビデオ)を、口コミ情報と共にランキング形式で人気順に紹介していきます。{'、'.join(video_ranking_data['actress_list'][:3])}など、かわいいAV女優が出演する作品が上位にランクインしています。ぜひお気に入りの作品を見つけてください！"
        else:
            genre = "AV女優"
            post_data['excerpt'] = f"今最も抜ける{video_ranking_data['category']}系のかわいい人気AV女優を、口コミ情報と共にランキング形式で人気順に紹介していきます。{'、'.join(video_ranking_data['actress_list'][:3])}など、かわいいAV女優が上位にランクインしています。ぜひお気に入りの女優さんを見つけてください！"

        post_data['title'] = f"【{video_ranking_data['year']}年{video_ranking_data['month']}月】{video_ranking_data['title']}"
        post_data['tags'] = [video_ranking_data['category'], f"{video_ranking_data['year']}年", f"{video_ranking_data['year']}年{video_ranking_data['month']}月", f"{genre}ランキング"] + video_ranking_data['actress_list']
        post_data['category'] = [video_ranking_data['category']]
        post_data['slug'] = url
        post_data['attachment_id'] = attachment_id
        post_data['custom_fields'] = [{}]
        #post_data['custom_fields'][0]['key'] = 'the_page_meta_keywords'
        #post_data['custom_fields'][0]['value'] = f"口コミ,おすすめ,ランキング,人気,抜ける,{genre},アダルトビデオ,{video_ranking_data['year']}年,{video_ranking_data['month']}月,{video_ranking_data['category']},{','.join(video_ranking_data['actress_list'])}"

    #引数で指定した場合は上書き
    if post_tags:
        post_data['tags'] = post_tags
    if post_category:
        post_data['category'] = post_category

    #print('post_data: ')
    #print(post_data)

    # 必要があれば設定し、32行目のコメントを解除
    post_data['post_date'] = datetime.strptime("2023/10/23 10:05:10","%Y/%m/%d %H:%M:%S")

    # 記事POST用に使用するHTMLの保存ファイルパス
    post_data['content'] = ""
    html_file = _settings.new_post_html_dir + index + '.html'
    with open(html_file, 'r') as file:
        # ファイルからデータを読み込み、変数に格納
        post_data['content'] = file.read()

    # debugフラグがONの場合、postしない
    if _settings.debug_flag['do_not_post']:
        print("SKIP: ", current_function_name)
        return ''

    if type == 'bulk_update':
        new_post = updatePost(post_data, site)
    else:
        new_post = newPost(post_data, site)
    print("Done: ", current_function_name)

    return new_post


def get_post_id_via_html(post_url: str):
    try:
        response = requests.get(post_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')

        # WordPressの記事IDがdata-post-id属性などに含まれる場合も
        body_tag = soup.find('body')
        if body_tag and body_tag.has_attr('class'):
            for class_name in body_tag['class']:
                if class_name.startswith('postid-'):
                    return int(class_name.split('-')[1])
        
        return "記事IDが見つかりません"
    
    except requests.RequestException as e:
        print(f"エラー: {e}")
        return None


if __name__=="__main__":
    #下書きに投稿するか本番で投稿するか選択
    #which="publish"
    which = "draft"
    title = "タイトルをここに書く"
    tags = ['希望するtag1', '希望するtag2']
    category = ['希望するカテゴリー１', '希望するカテゴリー２']
    #過去に投稿した記事としたい場合、投稿日をここで指定。例として2018年1月1日10時5分10秒に投稿した例を示す。
    post_date=datetime.strptime("2023/10/23 10:05:10","%Y/%m/%d %H:%M:%S")

    # ファイルを開く
    #with open('data/postData/newPost/0.html', 'r') as file:
    with open('sample/samplePublishDataParking.html', 'r') as file:
        # ファイルからデータを読み込み、変数に格納
        content = file.read()
    print(content)

    post_data = {}
    post_data['which'] = "draft"
    post_data['content'] = content
    post_data['title'] = "TEST 2023年 最大料金の安い駐車場ランキング 休日(土日)/平日を紹介！予約可も！"
    post_data['tags'] = 'tags'
    post_data['category'] = 'category'
    post_data['slug'] = 'url'
    post_data['excerpt'] = "周辺で、料金の安い駐車場をランキング形式で紹介します。休日・平日に分けて、長時間利用(最大料金あり)・短時間利用(1時間あたり)それぞれ料金が安い穴場な格安駐車場をピックアップしています。"
    post_data['custom_fields'] = [{}]
    post_data['custom_fields'][0]['key'] = 'the_page_meta_keywords'
    post_data['custom_fields'][0]['value'] = "駐車場,休日,平日,最大料金,最安値"

    newPost(post_data)
