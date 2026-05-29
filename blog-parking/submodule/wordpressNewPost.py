import inspect
import requests
import time
from submodule import _settings
#import _settings
from bs4 import BeautifulSoup
from datetime import datetime
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.compat import xmlrpc_client
from wordpress_xmlrpc.methods import media, posts
from wordpress_xmlrpc.methods.posts import GetPost, NewPost, EditPost
#SSL通信をするときにLocal側に証明書が必要
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

#変数を定義
id=_settings.wordpress_id
password=_settings.wordpress_pw
url=_settings.wordpress_url   #第3者が閲覧するURLの後ろに/xmlrpc.phpをつける。

# サムネイルアップロード
def upload_file(file_path):
    #クライアントの呼び出し
    wp = Client(url, id,password)

    # prepare metadata
    data = {
            'name': file_path.split('/')[-1],
            'type': 'image/jpeg',  # mimetype
    }

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

    return attachment_id


# postIDを取得
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


# wordpress投稿
def newPost(post_data):
    #クライアントの呼び出しなど
    wp = Client(url, id,password)
    post = WordPressPost()

    #実際に投稿する
    post.post_status = post_data['which']
    post.title = post_data['title']
    post.content = post_data['content']
    post.slug = post_data['slug']
    post.excerpt = post_data['excerpt']
    post.thumbnail = post_data['attachment_id']
    post.terms_names = {
    "post_tag": post_data['tags'],
    "category": post_data['category']
    }
    post.custom_fields = post_data['custom_fields']
    #過去に投稿した記事としたい場合、投稿日をここで指定。例として2018年1月1日10時5分10秒に投稿した例を示す。
    #post.date= post_date

    # 投稿済みであれば、対象のpost_idを特定
    post_url = _settings.wordpress_url.replace('xmlrpc.php','') + post.slug + '/'
    post_id = get_post_id_via_html(post_url)

    # すでに投稿済みであれば、マッチした投稿のIDを更新
    if post_id:
        #すでに記事があれば更新
        print(f"マッチした投稿のID: {post_id}")

        #post_idを指定して、投稿済みの記事のattachment_idを取得
        existing_post = wp.call(GetPost(post_id))
        if hasattr(existing_post, 'thumbnail') and existing_post.thumbnail:
            post.thumbnail = existing_post.thumbnail.get('attachment_id')
        else:
            post.thumbnail = post_data['attachment_id']  # デフォルト値を使用
        print(f"既存のattachment_id: {post.thumbnail}")

        # 更新実行
        new_post = wp.call(EditPost(post_id, post))

        print("### EditPost ###")
        print(f"post_url: {post_url}")
        return new_post

    # 未投稿であれば、新規投稿を実施
    else: 
        new_post = wp.call(NewPost(post))

        print("### NewPost ###")
        print(f"post_url: {post_url}")
        return new_post


def create_new_post(input_parking_data, attachment_id, index):
    # 現在の関数名を取得(log用)
    current_function_name = inspect.currentframe().f_code.co_name
    print("Start: ", current_function_name)

    post_data = {}
    #下書きに投稿するか本番で投稿するか選択
    #which="publish"
    post_data['which'] = "draft"
    if _settings.debug_flag['direct_post']:
        post_data['which'] = "publish"

    # 最安値の価格を取得
    lowest_price = input_parking_data['weekend_long'][0]['price']

    #Meta情報を生成
    post_data['title'] = f"【{input_parking_data['area']}】土日/平日 安い駐車場ランキング2025！一日{lowest_price}円 予約可も"

    add_tags = ''
    if input_parking_data['tag']:
        add_tags = ',' + input_parking_data['tag']

    post_data['tags'] = (input_parking_data['area'] + ',' + input_parking_data['category'] + add_tags).split(',')
    post_data['category'] = [input_parking_data['category']]
    post_data['slug'] = input_parking_data['url']
    post_data['excerpt'] = f"{input_parking_data['area']}周辺で、料金の安い駐車場をランキング形式で紹介します。休日・平日に分けて、長時間利用(最大料金あり)・短時間利用(1時間あたり)それぞれ料金が安い穴場な格安駐車場をピックアップしています。安くてお得な予約可の駐車場も紹介します。"
    post_data['attachment_id'] = attachment_id
    post_data['custom_fields'] = [{}]
    post_data['custom_fields'][0]['key'] = 'the_page_meta_keywords'
    post_data['custom_fields'][0]['value'] = f"{input_parking_data['area']},駐車場,休日,平日,最大料金,最安値,{input_parking_data['category']},{input_parking_data['tag']}"

    # 必要があれば設定し、32行目のコメントを解除
    post_data['post_date'] = datetime.strptime("2023/10/23 10:05:10","%Y/%m/%d %H:%M:%S")

    # 記事POST用に使用するHTMLの保存ファイルパス
    post_data['content'] = ""
    html_file = _settings.new_post_html_dir + str(index) + '.html'
    with open(html_file, 'r') as file:
        # ファイルからデータを読み込み、変数に格納
        post_data['content'] = file.read()

    # debugフラグがONの場合、postしない
    if _settings.debug_flag['do_not_post']:
        print("SKIP: ", current_function_name)
        return ''

    new_post = newPost(post_data)
    print("Done: ", current_function_name)

    return new_post


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

