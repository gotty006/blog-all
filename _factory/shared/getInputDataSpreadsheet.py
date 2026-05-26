from submodule import _settings
from submodule import getScrapingData
from submodule import getVideoDetail
import inspect
import json
import pandas as pd
import numpy as np
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import requests

# キャシュ保存パスをお掃除
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

# スプレッドシートの特定セルの上書き
def update_data_spreadsheet(spreadsheet_key, sheet='video', cell='A1', text='done'): 
    # 現在の関数名を取得(log用)
    current_function_name = inspect.currentframe().f_code.co_name
    print("Start: ", current_function_name)

    # 認証情報の設定
    Auth = _settings.gcp_auth_file
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = Auth
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(Auth, scope)
    Client = gspread.authorize(credentials)

    # データ取得
    spreadsheet = Client.open_by_key(spreadsheet_key)
    worksheet = spreadsheet.worksheet(sheet)

    # セルB2を"done"に更新
    worksheet.update(cell, [[text]])
    print(f"update cell [{cell}] to [{text}].")

    return


# スプレッドシートデータの読み込み
def get_input_data_spreadsheet(spreadsheet_key, type='video', single_type=None): 
    # 現在の関数名を取得(log用)
    current_function_name = inspect.currentframe().f_code.co_name
    print("Start: ", current_function_name)

    # 認証情報の設定
    Auth = _settings.gcp_auth_file
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = Auth
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(Auth, scope)
    Client = gspread.authorize(credentials)

    # データ取得
    spreadsheet = Client.open_by_key(spreadsheet_key)
    if single_type:
        worksheet = spreadsheet.worksheet('single_' + single_type)
    else:
        worksheet = spreadsheet.worksheet(type)
    data_from_sheets = worksheet.get_all_values()

    # bulk起動モード(config読み込み)
    if type == 'CONFIG' or type == 'CONFIG_shrink':
        input_data_list = []
        for row in data_from_sheets[1:]:
            input_data = {}
            input_data['no'], input_data['id'], input_data['post_flg'], input_data['url'], input_data['wp_admin'], input_data['fanza_id'], input_data['prompt_word'], post_tag_list, set_category_list, input_data['lang'], input_data['single'] = row[:11]

            if input_data['post_flg'] == 'y':
                input_data['post_tag_list'] = post_tag_list.split(',')
                input_data['set_category_list'] = set_category_list.split(',')

                input_data_list.append(input_data)

    # 自動起動モード(auto run)
    elif type == 'AUTORUN':
        input_data_list = []
        for row in data_from_sheets[1:]:
            input_data = {}
            input_data['no'], input_data['id'], input_data['run_flg'] = row[:3]

            input_data_list.append(input_data)

    # データを指定された形式の辞書に変換する
    elif type == 'video' or type == 'actress':
        input_data_list = []
        for row in data_from_sheets[1:]:
            input_data = {}
            category, input_data['title'], input_data['year'], input_data['month'], input_data['fanza_url'], ng_words = row[:6]

            if input_data['title'] == '' or input_data['year'] == '' or input_data['month'] == '' or input_data['fanza_url'] == '':
                continue

            input_data['category'] = category.replace('系','')

            if ng_words != '':
                input_data['ng_word_list'] = ng_words.split(',')
            else:
                input_data['ng_word_list'] = []

            input_data_list.append(input_data)
    
    # シングル投稿モードの場合、投稿済みの場合はその後の処理をSKIPする
    elif type in _settings.single_type_list or type.endswith('_list') or type=='bulk_post' or type=='bulk_post_shrink' or type=='bulk_update':
        input_data_list = []
        for row in data_from_sheets[1:]:
            input_data = {}
            input_data['category'], input_data['fanza_url'], input_data['get_video_list_count'], ng_words = row[:4]

            if input_data['get_video_list_count'] == '' or input_data['fanza_url'] == '':
                continue

            if ng_words != '':
                input_data['ng_word_list'] = ng_words.split(',')
            else:
                input_data['ng_word_list'] = []

            input_data_list.append(input_data)

    else:
        print('ERROR: Undefined type .')
        exit()

    print("Done: ", current_function_name)
    return input_data_list


# 同人WEBスクレイピングでランキングデータを取得
def get_dojin_data(input_data, index, type='dojin_list', get_video_list_count=10):

    # 記事POST用に使用するHTMLの保存ファイルパス
    video_json_file = _settings.video_data_dump_dir + str(index) + '.json'

    # debugフラグがONの場合、cacheから取得
    if _settings.debug_flag['use_cache_video_data'] == True :
        # JSONファイルからデータを読み込む
        with open(video_json_file, 'r') as json_file:
            video_ranking_data = json.load(json_file)
        return video_ranking_data

    # 現在の関数名を取得(log用)
    current_function_name = inspect.currentframe().f_code.co_name
    print("Start: ", current_function_name)

    # 投稿に使うスクレイピング情報(商品リスト、ランキング情報、レーティング情報)を取得
    category = ''
    video_list = getScrapingData.get_dojin_list(input_data['fanza_url'], input_data['ng_word_list'], False, get_video_list_count)

    # category
    if 'category' in input_data and input_data['category'] != '':
        category = input_data['category']

    # コンテンツ情報を取得
    video_ranking = []
    count = 1
    for video in video_list:
        print(f"index:{index+1} === 2. video meta scraping ({count} / {str(len(video_list))}): {video['title']}")

        # singleモードはすでに投稿済みの場合はSKIP
        if type in _settings.single_type_list or type.endswith('_list'):
            url = _settings.wordpress_url.rsplit('/', 1)[0] + '/dojin-' + video['cid'] + '/' 
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    print(f"The URL {url} is existed. SKIP!!")
                    continue
            except requests.exceptions.RequestException as e:
                print(f"An error occurred: {e}")


        # 動画詳細ページから メタ・口コミ情報を取得
        video_metadata = getScrapingData.get_dojin_detail(video['video_url'])
        if not video_metadata:
            continue

        video.update(video_metadata)
        video_ranking.append(video)


    video_ranking_data = {
        'category': category,
        'video_ranking_url': input_data['fanza_url'],
        'ng_word_list': input_data['ng_word_list'],
        'video_ranking': video_ranking
    }
    

    # 読み込んだデータをJSONデータで出力
    # JSONフォーマットに変換
    json_data = json.dumps(video_ranking_data, indent=4, ensure_ascii=False)

    # JSONを出力
    with open(video_json_file, 'w', encoding='utf-8') as jsonfile:
        jsonfile.write(json_data)

    print("Done: ", current_function_name)
    return video_ranking_data


# WEBスクレイピングでランキングデータを取得
def get_ranking_data(input_data, index, type='video', get_video_list_count=10, single_url=None):
    # 記事POST用に使用するHTMLの保存ファイルパス
    video_json_file = _settings.video_data_dump_dir + str(index) + '.json'

    # debugフラグがONの場合、cacheから取得
    if _settings.debug_flag['use_cache_video_data'] == True :
        # JSONファイルからデータを読み込む
        with open(video_json_file, 'r') as json_file:
            video_ranking_data = json.load(json_file)
        return video_ranking_data

    # キャシュ保存パスをお掃除
    if index == 0:
        delete_files_in_directory(_settings.video_data_dump_dir)

    # 現在の関数名を取得(log用)
    current_function_name = inspect.currentframe().f_code.co_name
    print("Start: ", current_function_name)

    # 投稿に使うスクレイピング情報(商品リスト、ランキング情報、レーティング情報)を取得
    category = ''
    if type == 'actress':
        video_list = []
        # 最新作と準新作のリストで女優ごとの合計お気に入り数を集計
        for release in ['latest', 'recent']:
            print(f"index:{index+1} ==== 1-1. actress video ranking data scraping ( {release} )")
            next_url = input_data['fanza_url'] + '&release=' + release
            while next_url:
                print(f"next_url: {next_url}")
                video_list, category, next_url = getScrapingData.get_actress_list(video_list, input_data['ng_word_list'], next_url)
        
        # actress_favorite_countでソート
        sorted_video_list = sorted(video_list, key=lambda x: x['actress_favorite_count'], reverse=True)

        # debug
        #debug_video_list = sorted(video_list, key=lambda x: x['actress_video_count'], reverse=True)
        #for debug_video in debug_video_list:
        #    print(f"actress:{debug_video['actress']}, actress_video_count:{debug_video['actress_video_count']}, actress_favorite_count:{debug_video['actress_favorite_count']}, actress_genre_url:{debug_video['actress_genre_url']}, video_url:{debug_video['video_url']}")

        # 情報を付加
        count = 1 
        video_list = []
        for video in sorted_video_list:
            if count > 10:
                break

            # 女優の情報を取得
            print(f"index:{index+1} ==== 1-2. actress & same video data scraping : {video['actress']} ({count} / 10)")
            actress_metadata = getScrapingData.get_actress_detail(video['actress'])
            if not actress_metadata:
                print('[WARN] could not get actress detail data.')
                continue
            video.update(actress_metadata)

            # 女優動画ランキングを取得
            video['actress_video_list'] , video['actress_yomi']= getScrapingData.get_video_list(video['actress_url'], input_data['ng_word_list'], is_actress_search=True)

            # ジャンルが同じ関連動画を取得
            video['actress_genre_video_list'] , video['actress_yomi']= getScrapingData.get_video_list(video['actress_genre_url'], [video['cid']], is_actress_search=True)

            # 動画詳細ページから メタ・口コミ情報を取得
            for actress_genre_video in video['actress_genre_video_list'][:3]:
                video_metadata = getScrapingData.get_video_detail(actress_genre_video['video_url'], actress_genre_video['cid'])
                if not video_metadata:
                    continue
                actress_genre_video.update(video_metadata)

            count += 1
            video_list.append(video)
        
    else:
        video_list, category = getScrapingData.get_video_list(input_data['fanza_url'], input_data['ng_word_list'], False, get_video_list_count, type, single_url)

    #print(json.dumps(video_list, indent=4, ensure_ascii=False))

    # category
    if 'category' in input_data and input_data['category'] != '':
        category = input_data['category']

    # コンテンツ情報を取得
    video_ranking = []
    actress_list = []
    count = 1
    for video in video_list:
        print(f"index:{index+1} === 2. video meta scraping ({count} / {str(len(video_list))}): {video['title']}")

        # singleモードはすでに投稿済みの場合はSKIP
        if type in _settings.single_type_list or type.endswith('_list'):
            if single_url:
                url = single_url + '/' + video['cid'] + '/' 
            else:
                url = _settings.wordpress_url.rsplit('/', 1)[0] + '/' + video['cid'] + '/' 

            try:
                response = requests.get(url)
                if response.status_code == 200 and type != 'bulk_update':
                    print(f"The URL {url} is existed. SKIP!!!!")
                    continue

                if response.status_code != 200 and type == 'bulk_update':
                    print(f"The URL {url} is not exist. SKIP!!!!")
                    continue

            except requests.exceptions.RequestException as e:
                print(f"An error occurred: {e}")

        # 素人ページ判定
        is_shiroto = False
        if '/amateur/' in input_data['fanza_url']:
            is_shiroto = True

        # 動画詳細ページから メタ・口コミ情報を取得
        #video_metadata = getScrapingData.get_video_detail(video['video_url'], video['cid'])
        print(video['cid'], is_shiroto)
        video_metadata = getVideoDetail.fetch_video_detail(video['cid'], is_shiroto)
        if not video_metadata:
            continue

        # 素人ページにgenre追加
        if is_shiroto:
            video_metadata['meta']['genre_list'].append('素人')
            video_metadata['meta']['genre_list'].append('デビュー作品')

        video.update(video_metadata)
        video_ranking.append(video)

        # 素人女優データ取得
        video['is_shiroto'] = False
        if not _settings.debug_flag['do_not_get_actress_data'] and video['actress'] == '':
            video_shiroto_data = getScrapingData.get_shiroto_actress_name(video['cid'])

            if video_shiroto_data:
                video.update(video_shiroto_data)
        
        # 女優一覧生成
        actress = video['actress_yomi']
        if actress not in actress_list:
            actress_list.append(actress)
        
        count += 1

        #print(json.dumps(video, indent=4, ensure_ascii=False))
    
    # 記事タイトルの設定
    if type == 'actress':
        post_title = input_data['title'] + 'おすすめ人気AV女優10人(動画･口コミ有)'
        video_ranking_data = {
            'category': category,
            'title': post_title,
            'year': input_data['year'],
            'month': input_data['month'],
            'video_ranking_url': input_data['fanza_url'],
            'ng_word_list': input_data['ng_word_list'],
            'actress_list': actress_list,
            'video_ranking': video_ranking,
        }
    elif type == 'video':
        post_title = input_data['title'] + 'おすすめ人気AVランキング10(動画･口コミ有)'
        video_ranking_data = {
            'category': category,
            'title': post_title,
            'year': input_data['year'],
            'month': input_data['month'],
            'video_ranking_url': input_data['fanza_url'],
            'ng_word_list': input_data['ng_word_list'],
            'actress_list': actress_list,
            'video_ranking': video_ranking,
        }
    else:
        post_title = 'undefined'
        video_ranking_data = {
            'category': category,
            'video_ranking_url': input_data['fanza_url'],
            'ng_word_list': input_data['ng_word_list'],
            'actress_list': actress_list,
            'video_ranking': video_ranking,
        }
    

    # 読み込んだデータをJSONデータで出力
    # JSONフォーマットに変換
    json_data = json.dumps(video_ranking_data, indent=4, ensure_ascii=False)

    # JSONを出力
    with open(video_json_file, 'w', encoding='utf-8') as jsonfile:
        jsonfile.write(json_data)

    print("Done: ", current_function_name)
    return video_ranking_data
