import inspect
import base64
import re
import os
import urllib.parse
from submodule import _settings

# ファイルをRead
def read_file(file_path):
    try:
        with open(file_path, 'r') as file:
            html = file.read()

    except FileNotFoundError:
        print(f"ファイル '{file_path}' が見つかりません。")
    except Exception as e:
        print("ファイルの読み込み中にエラーが発生しました:", e)
    
    return html

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

# 度分秒形式に変換する関数
def decimal_degrees_to_dms(degrees):
    d = int(degrees)
    m = int((degrees - d) * 60)
    s = (degrees - d - m / 60) * 3600
    return f"{d}°{m}'{s:.1f}\""


# 駐車場名に含まれる不要文字の削除
def remove_sentences(input_string):
    result_string = input_string
    for sentence in _settings.parking_name_title_delete_sentences:
        result_string = result_string.replace(sentence, '')

    return result_string


# アフィリエイト導線のボタンHTMLを生成
def get_affiliate_button(affiliate, input_affiliate_button_html, search_keyword=None):
    affiliate_button_html = ""
    logo_config = _settings.affiliate_logo_config

    if search_keyword:
        # 全角のダブルクォーテーション「”」で分割
        before, _, _ = search_keyword.partition('”')
        search_keyword = before

    # 特定のボタンを表示する場合
    if affiliate != 'all':
        # リダイレクトURL設定があれば、クエリを付与(検索結果をアフィリエイト遷移先で表示する)
        redirect_url = ''
        if search_keyword and 'redirect' in logo_config[affiliate]:
            redirect_url = urllib.parse.quote(logo_config[affiliate]['redirect'] + search_keyword)

        affiliate_button_html += input_affiliate_button_html.format(
            affiliate_url = logo_config[affiliate]['affiliate'] + redirect_url,
            affiliate_logo_url = logo_config[affiliate]['url'],
            affiliate_logo_width = logo_config[affiliate]['width'],
            affiliate_logo_height = logo_config[affiliate]['height'],
            affiliate_logo_text = logo_config[affiliate]['text']
        )
        return affiliate_button_html
    
    # すべてのボタンを表示する場合
    for value in logo_config.values():
        # リダイレクトURL設定があれば、クエリを付与(検索結果をアフィリエイト遷移先で表示する)
        redirect_url = ''
        if search_keyword and 'redirect' in value:
            redirect_url = urllib.parse.quote(value['redirect'] + search_keyword)

        affiliate_button_html += input_affiliate_button_html.format(
            affiliate_url = value['affiliate'] + redirect_url,
            affiliate_logo_url = value['url'],
            affiliate_logo_width = value['width'],
            affiliate_logo_height = value['height'],
            affiliate_logo_text = value['text']
        )

    return affiliate_button_html


# 投稿に使うHTMLを作成
def generate_post_html(input_parking_data, gpt_text, index):
    # 記事POST用に使用するHTMLの保存ファイルパス
    html_file = _settings.new_post_html_dir + str(index) + '.html'

    # debugフラグがONの場合、cacheから取得
    if _settings.debug_flag['use_cache_post_html'] == True :
        html = read_file(html_file)
        return html

    # 現在の関数名を取得(log用)
    current_function_name = inspect.currentframe().f_code.co_name
    print("Start: ", current_function_name)

    # キャシュ保存パスをお掃除
    if index == 0:
        delete_files_in_directory(_settings.new_post_html_dir)

    # 各HTMLformatを読み込み
    input_base_html = read_file(_settings.input_html_dir+'/base.html')
    input_affiliate_base_html = read_file(_settings.input_html_dir+'/affiliate_base.html')
    input_affiliate_button_html = read_file(_settings.input_html_dir+'/affiliate_button.html')
    input_affiliate_parking_reserve_html = read_file(_settings.input_html_dir+'/affiliate_parking_reserve.html')
    input_category_reserve_text_html = read_file(_settings.input_html_dir+'/category_reserve_text.html')
    input_category_html = read_file(_settings.input_html_dir + '/category.html')
    input_parking_html = read_file(_settings.input_html_dir + '/parking.html')
    input_summary_html = read_file(_settings.input_html_dir + '/summary.html')

    ## baseアフィリエイトエリアのHTMLを生成
    affiliate_button_html = get_affiliate_button('all', input_affiliate_button_html, search_keyword=input_parking_data['area'])
    affiliate_base_html = input_affiliate_base_html.format(
        parts_affiliate_button = affiliate_button_html
    )

    ## category_htmlを生成
    category_html = ""
    # settingsファイルのparking categoryを取得してループ
    parking_category = _settings.parking_category.keys()
    for category_num, category in enumerate(parking_category) :

        ## parking_htmlを生成
        parking_html = ""

        # parkingデータが０件の場合はアフィリエイト情報のみ記載
        if len(input_parking_data[category]) == 0:
            print('nothing content')
            parking_html = affiliate_base_html

        # parkingデータを生成
        parking_rank_medal = '🥇'
        previous_parking_name_title = ''
        overlapping_count = 1
        for parking_num, parking in enumerate(input_parking_data[category]):

            # 変数情報の生成
            # parking_rank_medal
            if parking_num != 0 and parking['price'] != input_parking_data[category][parking_num-1]['price']:
                if parking_rank_medal == '🥇':
                    parking_rank_medal = '🥈'
                elif parking_rank_medal == '🥈':
                    parking_rank_medal = '🥉'
                elif parking_rank_medal == '🥉':
                    parking_rank_medal = ''

            # parking_name_title
            draft_name = remove_sentences(re.sub(r'【.*?】', '', parking['name']))
            if draft_name == previous_parking_name_title:
                overlapping_count += 1
                parking_name_title = draft_name + str(overlapping_count)
            else:
                overlapping_count = 1
                parking_name_title = draft_name
            previous_parking_name_title = draft_name

            print(f"{str(category_num+1)}-{str(parking_num+1)}.{parking_name_title}:{str(parking['price'])}{parking_rank_medal}")
                
            # parking_title_price
            parking_price = ''
            if category == 'weekend_rsv':
                parking_price = '1日'
            elif category == 'weekend_long':
                parking_price = '休日 最大'
            elif category == 'weekend_short':
                parking_price = '休日 1時間'
            elif category == 'weekday_long':
                parking_price = '平日 最大'
            elif category == 'weekday_short':
                parking_price = '平日 1時間'
            parking_price += str(parking['price']) + '円'

            if 'rsv' in parking and parking['rsv'] != None:
                parking_price += '：予約可✅️'
                
            # parking_note
            # parkingアフィリエイトエリアのHTMLを生成
            parking_note = ''
            affiliate_parking_reserve_html = ''
            if category == 'weekend_rsv':
                parking_note = '<br>予約が埋まってしまう可能性があるので、早めの予約がおすすめです！'

                ## parkingアフィリエイトエリアのHTMLを生成
                affiliate_button_html = get_affiliate_button(parking['rsv']['provider'], input_affiliate_button_html, search_keyword=parking['name'])
                affiliate_parking_reserve_html = input_affiliate_parking_reserve_html.format(
                    parking_name = parking['name'],
                    parts_affiliate_button = affiliate_button_html
                )
            
            # parking_openhour
            # parking_price_detail
            if parking['openhour'] == None and parking['rsv'] != None:
                parking_openhour = '※' + parking['rsv']['provider'] + 'のホームページを確認してください'
                parking_price_detail = parking_price

                ## parkingアフィリエイトエリアのHTMLを生成
                affiliate_button_html = get_affiliate_button(parking['rsv']['provider'], input_affiliate_button_html, search_keyword=parking['name'])
                affiliate_parking_reserve_html = input_affiliate_parking_reserve_html.format(
                    parking_name = parking['name'],
                    parts_affiliate_button = affiliate_button_html
                )
            else:
                parking_openhour = parking['openhour']
                parking_price_detail = parking['pricestr'].replace('\n', '<br>')

            # parking_map_encode
            original_string = decimal_degrees_to_dms(parking['lat'])+'N '+decimal_degrees_to_dms(parking['lng'])+'E'
            # 文字列をバイト型に変換してBase64エンコード
            encoded_bytes = base64.b64encode(original_string.encode("utf-8"))
            # バイト型を文字列に変換し、末尾の'=='を削除
            parking_map_encode = encoded_bytes.decode("utf-8").rstrip('=')

            # gpt 省略モードの場合は空文字を設定
            if gpt_text == None:
                parking_gtp_text = ''
            else:
                parking_gtp_text = gpt_text[category][parking_num],

            # parking html 生成
            parking_html += input_parking_html.format(
                category_num = str(category_num+1),
                parking_num = str(parking_num+1),
                parking_rank_medal = parking_rank_medal,
                parking_name_title = parking_name_title,
                parking_name = parking['name'],
                parking_price = parking_price,
                parking_price_detail = parking_price_detail,
                input_area = input_parking_data['area'],
                parking_time_min = round(parking['distance'] * 0.02),
                parking_distance = parking['distance'],
                parking_gtp_text = parking_gtp_text,
                parking_note = parking_note,
                parts_affiliate_parking_reserve = affiliate_parking_reserve_html,
                parking_address = parking['address'],
                parking_capacity = parking['capacity'],
                parking_openhour = parking_openhour,
                parking_lng = parking['lng'],
                parking_lat = parking['lat'],
                parking_map_encode = parking_map_encode
            )

            if parking_num == 4:
                break
        
        # parts_category_reserve_text
        if category == 'weekend_rsv' :
            category_reserve_text_html = input_category_reserve_text_html
        else:
            category_reserve_text_html = ''

        # category html 生成
        category_html += input_category_html.format(
            category = category,
        	parts_parking = parking_html,
	        parts_category_reserve_text = category_reserve_text_html,
	        category_num = str(category_num+1),
	        category_name = _settings.parking_category[category]
        )
            
    ## summary htmlを生成
    summary_html = input_summary_html.format(
        parts_affiliate_base = affiliate_base_html,
        input_area = input_parking_data['area']
    )

    ## base htmlを生成
    base_html = input_base_html.format(
        input_area = input_parking_data['area'],
        parts_affiliate_base = affiliate_base_html,
        parts_category = category_html,
        parts_summary = summary_html
    )

    # 生成したHTMLデータをファイルに保存
    with open(html_file, 'w') as file:
        file.write(base_html)

    print("Done: ", current_function_name)

    return base_html


if __name__ == '__main__':

    dummy_input_plan_data = {
        'pickup' : [
            'pickup1',
            'pickup2',
            'pickup3'
        ],
        'total_day': "2"
    }
    dummy_gpt_text = ""
    generate_post_html(dummy_input_plan_data, dummy_gpt_text)

