from submodule import _settings
from submodule import getParkingInfoJson
import inspect
import json
import pandas as pd
import numpy as np
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os


# スプレッドシートデータの読み込み
def get_parking_data_spreadsheet(spreadsheet_key): 
    if _settings.debug_flag['use_cache_input_data'] == True :
        # JSONファイルからデータを読み込む
        with open(_settings.input_data_dump_file, 'r') as json_file:
            input_parking_data = json.load(json_file)
        return input_parking_data
        
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
    worksheet = spreadsheet.worksheet("general")
    data_from_sheets = worksheet.get_all_values()

    # データを指定された形式の辞書に変換する
    input_parking_data = []

    for row in data_from_sheets[1:]:
        area, url, category, tag, source_url_parking, weekend, weekday, weekend_long, weekend_short, weekday_long, weekday_short = row[:11]

        if category == '' or source_url_parking == '' or weekend == '' or weekday == '':
            continue

        # tag に指定がなければ、webスクレイピングでタグ情報を取得
        if tag == '':
            tag = getParkingInfoJson.get_tag(area)

        # parking_dataから必要なリストを抽出
        # weekend_longがNoneでないことを確認
        if weekend_long != "" or source_url_parking != "":

            #source_url_parkingから、各カテゴリの駐車場情報Jsonを取得
            if source_url_parking != "":
                dict_weekend_long, dict_weekend_short, dict_weekday_long, dict_weekday_short = getParkingInfoJson.get_parkinginfo_json(source_url_parking, weekend, weekday)
            
            else:
                # JSON文字列を辞書に変換
                dict_weekend_long = json.loads(weekend_long)['result']['parkings']
                dict_weekend_short = json.loads(weekend_short)['result']['parkings']
                dict_weekday_long = json.loads(weekday_long)['result']['parkings']
                dict_weekday_short = json.loads(weekday_short)['result']['parkings']


            # 'rsv'キーが存在し、その値が空でない辞書のみを抽出して新しいリストに格納
            parkinginfo_weekend_rsv = [d for d in dict_weekend_long if 'rsv' in d and d['rsv'] and 'price' in d and d['price'] is not None and d.get('distance', 0) < 1000]

            # priceが空でない辞書のみを抽出して新しいリストに格納
            # リストのソート（第一ソート：rank、第二ソート：distance）
            parkinginfo_weekend_long = sorted([d for d in dict_weekend_long if d.get('price', False) and d.get('distance', 0) < 1000], key=lambda x: (x['rank'], x['distance']))
            parkinginfo_weekend_short = sorted([d for d in dict_weekend_short if d.get('price', False) and d.get('distance', 0) < 1000], key=lambda x: (x['rank'], x['distance']))
            parkinginfo_weekday_long = sorted([d for d in dict_weekday_long if d.get('price', False) and d.get('distance', 0) < 1000], key=lambda x: (x['rank'], x['distance']))
            parkinginfo_weekday_short = sorted([d for d in dict_weekday_short if d.get('price', False) and d.get('distance', 0) < 1000], key=lambda x: (x['rank'], x['distance']))

            # リストのソート（第一ソート：rank、第二ソート：distance）
            #parking_list = sorted(data_dict['result']['parkings'], key=lambda x: (x['rank'], x['distance']))

        data_dict = {
            'area': area,
            'url': url,
            'category': category,
            'tag': tag,
            'weekend_rsv': parkinginfo_weekend_rsv,
            'weekend_long': parkinginfo_weekend_long,
            'weekend_short': parkinginfo_weekend_short,
            'weekday_long': parkinginfo_weekday_long,
            'weekday_short': parkinginfo_weekday_short
        }
        input_parking_data.append(data_dict)
    
    # 読み込んだデータをJSONデータで出力
    # JSONフォーマットに変換
    json_data = json.dumps(input_parking_data, indent=4, ensure_ascii=False)

    # JSONを出力
    with open(_settings.input_data_dump_file, 'w', encoding='utf-8') as jsonfile:
        jsonfile.write(json_data)


    print("Done: ", current_function_name)
    return input_parking_data
