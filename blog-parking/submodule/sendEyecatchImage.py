import inspect
import os
import requests
from bs4 import BeautifulSoup
from submodule import _settings
from submodule import seleniumWebScraping
from submodule import wordpressNewPost


# サムネイル一時保存パスをお掃除
def delete_files_in_directory(directory):
    try:
        # ディレクトリ内のファイルを取得
        files = os.listdir(directory)

        # ファイルを削除
        for file in files:
            file_path = os.path.join(directory, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
                #print(f"ファイル {file_path} を削除しました")

        #print(f"{directory} 内のすべてのファイルを削除しました")

    except Exception as e:
        print(f"エラー: {e}")


# 対象の画像ダウンロードURLを取得
def get_eyecatch_dl_url(area):
    # url生成
    url = f"https://www.photo-ac.com/main/search?exclude_ai=on&personalized=&q={area}&sl=ja&pp=70&qid=&creator=&ngcreator=&nq=&srt=dlrank&orientation=all&sizesec=all&color=all&model_count=-1&age=all&mdlrlrsec=all&prprlrsec=all"
    # seleniumからWEBテキストデータを取得
    page_source = seleniumWebScraping.get_text_with_selenium(url)

    # BeautifulSoupを使ってHTMLを解析
    soup = BeautifulSoup(page_source, 'html.parser')

    # figure要素のclassが'photo-img item'であるものを検索
    #figure_elements = soup.find_all('figure', class_='photo-img item')
    figure_elements = soup.find_all('figure', class_='ac-ig-item loaded')

    # 最初のfigure要素からimgタグのsrc属性を取得
    if figure_elements:
        first_figure_element = figure_elements[0]
        img_element = first_figure_element.find('img')
        if img_element:
            dl_url = img_element.get('src')
            print(f"画像DLのURL: {dl_url}")

            return dl_url
    else:
        print("該当する要素が見つかりませんでした。")
        return None


# アイキャッチ画像アップロード
def send_eyecatch_image(input_parking_data, index):
    
    if _settings.debug_flag['do_not_upload_img'] :
        return '1286'

    # 現在の関数名を取得(log用)
    current_function_name = inspect.currentframe().f_code.co_name
    print("Start: ", current_function_name)

    # サムネイル一時保存パスをお掃除
    if index == 0:
        delete_files_in_directory(_settings.eyecatch_dir)

    # 対象の画像ダウンロードURLを取得
    dl_url = get_eyecatch_dl_url(input_parking_data['area'])
    if dl_url == None:
        return '1286'

    # ファイルをダウンロード
    suffix = dl_url.split('.')[-1]
    save_path = _settings.eyecatch_dir + input_parking_data['url'] + '.' + suffix
    response = requests.get(dl_url)

    # レスポンスのステータスコードが200なら成功
    if response.status_code == 200:
        # ファイルを保存
        with open(save_path, 'wb') as file:
            file.write(response.content)
        print(f"ファイルを {save_path} に保存しました。")
    else:
        print(f"ファイルのダウンロードに失敗しました。ステータスコード: {response.status_code}")
        exit(1)

    # アイキャッチ画像のアップロード
    attachment_id = wordpressNewPost.upload_file(save_path)
    print("Done: ", current_function_name)

    return attachment_id
