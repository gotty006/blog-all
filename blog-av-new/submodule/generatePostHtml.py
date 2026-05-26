import inspect
import os
from urllib.parse import quote
from datetime import datetime
from submodule import googleTranslate
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

# 100文字目以降を削除し、…に省略
def truncate_string(s, max_length=100):
    if len(s) > max_length:
        return s[:max_length] + '…'
    else:
        return s

# medal絵文字の取得
def get_medal_string(rank):
    # medal
    if rank == '1':
        medal = '🥇'
    elif rank == '2':
        medal = '🥈'
    elif rank == '3':
        medal = '🥉'
    else:
        medal = ''
    return medal

# アフィリエイトURLの取得
def get_affiliate_url(url, ch_id, affiliate_id):
    affiliate_url = 'https://al.dmm.co.jp/?lurl=' + quote(url) + '&af_id=' + affiliate_id + '&ch=toolbar&ch_id=' + ch_id
    return affiliate_url


# 投稿に使うHTMLを作成(actress)
def generate_post_html_actress(video_ranking_data, gpt_text, index):
    affiliate_id = _settings.affiliate_id['actress']

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
    input_base_html = read_file(_settings.input_html_dir+'/actress/base.html')
    input_affiliate_sale_html = read_file(_settings.input_html_dir+'/actress/affiliate_sale.html')
    input_actress_ranking_html = read_file(_settings.input_html_dir + '/actress/actress_ranking.html')
    input_free_video_html = read_file(_settings.input_html_dir + '/actress/free_video.html')
    input_actress_genre_video_html = read_file(_settings.input_html_dir + '/actress/actress_genre_video.html')
    input_actress_video_html = read_file(_settings.input_html_dir + '/actress/actress_video.html')
    input_video_review_html = read_file(_settings.input_html_dir + '/actress/video_review.html')
    input_summary_html = read_file(_settings.input_html_dir + '/actress/summary.html')

    ## actress_ranking_htmlを生成
    actress_ranking_html = ""

    ## videoランキングデータを生成
    for rank_num, video in enumerate(video_ranking_data['video_ranking']):

        ## 女優ジャンル関連ビデオデータを生成
        actress_genre_video_html = ''
        for actress_genre_rank_num, actress_genre_video in enumerate(video['actress_genre_video_list'][:3]):

            # 変数情報の生成
            # rank
            rank = str(actress_genre_rank_num + 1)

            # sample_img_list
            #title = actress_genre_video['title']
            title = ''
            sample_img_list = ''.join(f'<img src="{img}" alt="{title}" />' for img in actress_genre_video['sample_img_list'])

            # actress_genre_video_html 生成
            actress_genre_video_html += input_actress_genre_video_html.format(
                rank = rank,
                title = actress_genre_video['title'],
                affiliate_video_url = get_affiliate_url(actress_genre_video['video_url'], 'package_large', affiliate_id),
                img_url_l = actress_genre_video['img_url_l'],
                director = actress_genre_video['meta']['director'],
                maker = actress_genre_video['meta']['maker'],
                sale_start_date = actress_genre_video['meta']['sale_start_date'],
                duration = actress_genre_video['meta']['duration'],
                favorite_count = actress_genre_video['favorite_count'],
                sample_img_list = sample_img_list,
                cid = actress_genre_video['cid'],
                actress_yomi = video['actress_yomi'],
                affiliate_actress_url = get_affiliate_url(video['actress_url'],'link',affiliate_id)
            )


        ## 女優ビデオランキングデータを生成
        actress_video_html = ''
        for actress_rank_num, actress_video in enumerate(video['actress_video_list']):
 
            # 変数情報の生成
            # rank
            rank = str(actress_rank_num + 1)

            # actress video html 生成
            actress_video_html += input_actress_video_html.format(
                rank = rank,
                medal = get_medal_string(rank),
                title = actress_video['title'],
                affiliate_video_url = get_affiliate_url(actress_video['video_url'], 'package_small', affiliate_id),
                img_url = actress_video['img_url']
            )
        

        ## videoレビューデータを生成
        video_review_html = ''
        for review_index, review_text in enumerate(video['review_list'][:2]):

            # review_icon
            if review_index == 0:
                review_icon = 'man'
            else:
                review_icon = 'b-man'

            # video_review_html 生成
            video_review_html += input_video_review_html.format(
                review_icon = review_icon,
                review_text = truncate_string(review_text, 170)
            )
        
        ## 無料動画エリアを生成
        # post_title
        post_title = f"【{video_ranking_data['year']}年{video_ranking_data['month']}月】{video_ranking_data['title']}"

        # upload_date
        now = datetime.now()
        upload_date = now.strftime("%Y-%m-%dT%H:%M:%S%z")+'+09:00'

        free_video_html = ''
        if not ('vr' in video['cid'] or 'VR' in video['title']):
            free_video_html = input_free_video_html.format(
                affiliate_id = affiliate_id,
                cid = video['cid'],
                affiliate_video_url = get_affiliate_url(video['video_url'], 'package_large', affiliate_id),
                actress = video['actress'],
                post_title = post_title,    
                title = video['title'],
                upload_date = upload_date,
                duration = video['meta']['duration'].replace('分', ''),
                favorite_count = video['favorite_count'],
                img_url_l = video['img_url_l']
            )


        # 変数情報の生成
        # rank
        rank = str(rank_num + 1)

        # sample_img_list
        #title = video['title']
        title = ''
        sample_img_list = ''.join(f'<img src="{img}" alt="{title}" />' for img in video['sample_img_list'])

        # parts_affiliate_sale
        if rank == '1' or rank == '3':
            parts_affiliate_sale = input_affiliate_sale_html
        else:
            parts_affiliate_sale = ''
        
        # actress_detail
        actress_detail = ''
        for key, value in video['actress_meta'].items():
            actress_detail += f"<tr><td>{key}</td><td>{value}</td></tr>"

        # video_ranking_html 生成
        actress_ranking_html += input_actress_ranking_html.format(
            rank = rank,
	        medal = get_medal_string(rank),
            actress = video['actress'],
            actress_kana = video['actress_kana'],
	        title = video['title'],
            affiliate_video_url = get_affiliate_url(video['video_url'], 'package_large', affiliate_id),
            img_url_l = video['img_url_l'],
            affiliate_actress_url = get_affiliate_url(video['actress_url'],'link',affiliate_id),
            actress_yomi = video['actress_yomi'],
            sample_img_list = sample_img_list,
            parts_video_review = video_review_html,
            cid = video['cid'],
            parts_free_video = free_video_html,
            actress_detail = actress_detail,
            gpt_text = gpt_text['item'][rank_num][0],
            synopsis = gpt_text['item'][rank_num][1],
            parts_actress_genre_video = actress_genre_video_html,
            parts_actress_video = actress_video_html,
            parts_affiliate_sale = parts_affiliate_sale,
            gpt_text_actress_video = gpt_text['actress_video'][rank_num]
        )

            
    ## summary htmlを生成
    summary_html = input_summary_html.format(
        category = video_ranking_data['category'],
	    parts_affiliate_sale = input_affiliate_sale_html
    )

    ## base htmlを生成
    base_html = input_base_html.format(
        #gpt_text_intro = gpt_text['intro'],
        gpt_text_intro = '',
        category = video_ranking_data['category'],
        actress_list = "、".join(video_ranking_data['actress_list'][:3]),
        parts_actress_ranking = actress_ranking_html,
	    parts_affiliate_sale = input_affiliate_sale_html,
        parts_summary = summary_html
    )

    # 生成したHTMLデータをファイルに保存
    with open(html_file, 'w') as file:
        file.write(base_html)

    print("Done: ", current_function_name)

    return base_html


# 投稿に使うHTMLを作成(video)
def generate_post_html_video(video_ranking_data, gpt_text, index):
    affiliate_id = _settings.affiliate_id['video']

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
    input_base_html = read_file(_settings.input_html_dir+'/video/base.html')
    input_affiliate_sale_html = read_file(_settings.input_html_dir+'/video/affiliate_sale.html')
    input_video_ranking_html = read_file(_settings.input_html_dir + '/video/video_ranking.html')
    input_free_video_html = read_file(_settings.input_html_dir + '/video/free_video.html')
    input_actress_video_html = read_file(_settings.input_html_dir + '/video/actress_video.html')
    input_video_review_html = read_file(_settings.input_html_dir + '/video/video_review.html')
    input_summary_html = read_file(_settings.input_html_dir + '/video/summary.html')

    ## video_ranking_htmlを生成
    video_ranking_html = ""

    ## videoランキングデータを生成
    for rank_num, video in enumerate(video_ranking_data['video_ranking']):

        ## 女優ビデオランキングデータを生成
        actress_video_html = ''
        for actress_rank_num, actress_video in enumerate(video['actress_video_list']):
 
            # 変数情報の生成
            # rank
            rank = str(actress_rank_num + 1)

            # actress video html 生成
            actress_video_html += input_actress_video_html.format(
                rank = rank,
                medal = get_medal_string(rank),
                title = actress_video['title'],
                affiliate_video_url = get_affiliate_url(actress_video['video_url'], 'package_small', affiliate_id),
                img_url = actress_video['img_url']
            )
        

        ## videoレビューデータを生成
        video_review_html = ''
        for review_index, review_text in enumerate(video['review_list'][:2]):

            # review_icon
            if review_index == 0:
                review_icon = 'man'
            else:
                review_icon = 'b-man'

            # video_review_html 生成
            video_review_html += input_video_review_html.format(
                review_icon = review_icon,
                review_text = truncate_string(review_text, 170)
            )
        
        ## 無料動画エリアを生成
        # post_title
        post_title = f"【{video_ranking_data['year']}年{video_ranking_data['month']}月】{video_ranking_data['title']}"

        # upload_date
        now = datetime.now()
        upload_date = now.strftime("%Y-%m-%dT%H:%M:%S%z")+'+09:00'

        free_video_html = ''
        if not ('vr' in video['cid'] or 'VR' in video['title']):
            free_video_html = input_free_video_html.format(
                affiliate_id = affiliate_id,
                cid = video['cid'],
                affiliate_video_url = get_affiliate_url(video['video_url'], 'package_large', affiliate_id),
                actress = video['actress'],
                post_title = post_title,    
                title = video['title'],
                upload_date = upload_date,
                duration = video['meta']['duration'].replace('分', ''),
                favorite_count = video['favorite_count'],
                img_url_l = video['img_url_l']
            )


        # 変数情報の生成
        # rank
        rank = str(rank_num + 1)

        # sample_img_list
        #title = video['title']
        title = ''
        sample_img_list = ''.join(f'<img src="{img}" alt="{title}" />' for img in video['sample_img_list'])

        # parts_affiliate_sale
        if rank == '1' or rank == '3':
            parts_affiliate_sale = input_affiliate_sale_html
        else:
            parts_affiliate_sale = ''

        # video_ranking_html 生成
        video_ranking_html += input_video_ranking_html.format(
            rank = rank,
	        medal = get_medal_string(rank),
            actress = video['actress'],
	        title_omission = truncate_string(video['title'], 23),
	        title = video['title'],
            affiliate_video_url = get_affiliate_url(video['video_url'], 'package_large', affiliate_id),
            img_url_l = video['img_url_l'],
            affiliate_actress_url = get_affiliate_url(video['actress_url'],'link',affiliate_id),
            actress_yomi = video['actress_yomi'],
            director = video['meta']['director'],
            maker = video['meta']['maker'],
            sale_start_date = video['meta']['sale_start_date'],
            duration = video['meta']['duration'],
            #synopsis = video['synopsis'],
            synopsis = gpt_text['item'][rank_num][1],
            favorite_count = video['favorite_count'],
            sample_img_list = sample_img_list,
            parts_video_review = video_review_html,
            cid = video['cid'],
            gpt_text = gpt_text['item'][rank_num][0],
            parts_free_video = free_video_html,
            parts_actress_video = actress_video_html,
            parts_affiliate_sale = parts_affiliate_sale,
            gpt_text_actress_video = gpt_text['actress_video'][rank_num]
        )

            
    ## summary htmlを生成
    summary_html = input_summary_html.format(
        category = video_ranking_data['category'],
	    parts_affiliate_sale = input_affiliate_sale_html
    )

    ## base htmlを生成
    base_html = input_base_html.format(
        gpt_text_intro = gpt_text['intro'],
        category = video_ranking_data['category'],
        actress_list = "、".join(video_ranking_data['actress_list'][:3]),
        parts_video_ranking = video_ranking_html,
	    parts_affiliate_sale = input_affiliate_sale_html,
        parts_summary = summary_html
    )

    # 生成したHTMLデータをファイルに保存
    with open(html_file, 'w') as file:
        file.write(base_html)

    print("Done: ", current_function_name)

    return base_html


# 投稿に使うHTMLを作成(dojin)
def generate_post_html_dojin(video, gpt_text, index, rank_num, type):
    affiliate_id = _settings.affiliate_id[type]

    # 記事POST用に使用するHTMLの保存ファイルパス
    html_file = _settings.new_post_html_dir + str(index) + '_' + str(rank_num) + '.html'

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
    input_base_html = read_file(_settings.input_html_dir+'/dojin/base.html')
    input_webp_html = read_file(_settings.input_html_dir + '/dojin/webp.html')
    input_video_info_customize_html = read_file(_settings.input_html_dir + '/dojin/video_info_customize.html')
    input_actress_video_html = read_file(_settings.input_html_dir + '/dojin/actress_video.html')
    input_actress_video_block_html = read_file(_settings.input_html_dir + '/dojin/actress_video_block.html')
    input_video_review_html = read_file(_settings.input_html_dir + '/dojin/video_review.html')
    input_other_video_html = read_file(_settings.input_html_dir + '/dojin/other_video.html')

    # サンプル動画
    # upload_date
    free_video_html = ''

    # webp_html
    webp_html = input_webp_html.format(
        title = video['title'],
        gif_url = video['gif_url']
    )


    # 動画メタ情報
    affiliate_actress_url = ''
    if 'actress_url' in video:
        affiliate_actress_url = get_affiliate_url(video['actress_url'], 'link', affiliate_id)


    video_info_list = f"""
        <tr><td>作者</td><td>{video['actress']}</td></tr>
        <tr><td>販売数</td><td>{video['sale_count']}</td></tr>
        <tr><td>評価</td><td>{video['rating']}</td></tr>
        <tr><td>評価数</td><td>{video['rating_count']}</td></tr>
        <tr><td>配信開始</td><td>{video['meta'].get('delivery_start_date', '-')}</td></tr>
        <tr><td>ページ数</td><td>{video['meta'].get('page', '-')}</td></tr>
        <tr><td>ファイルサイズ</td><td>{video['meta'].get('file_size', '-')}</td></tr>
        <tr><td>シリーズ</td><td>{video['meta'].get('series', '-')}</td></tr>
    """

    # 前方一致でhttps://www.dmm.co.jp/がない場合は追加
    if 'https://www.dmm.co.jp/' not in video['video_url']:
        url = 'https://www.dmm.co.jp/' + video['video_url']
    else:
        url = video['video_url']

    video_info_html = input_video_info_customize_html.format(
        video_info_list = video_info_list,
        title = video['title'],
        affiliate_video_url = get_affiliate_url(url, 'package_large', affiliate_id),
        img_url_l = video['sample_img_list'][0] if video['sample_img_list'] else video['img_url_l'],
        cid = video['cid'],
        welcome_coupon_url = "https://al.dmm.co.jp/?lurl=https%3A%2F%2Fwww.dmm.co.jp%2Fdc%2Fdoujin%2F-%2Fspecial%2Fcoupon%2F&af_id=" + affiliate_id + "&ch=link_tool&ch_id=link"
    )


    ## 女優ビデオランキングデータを生成
    actress_video_html = ''
    for actress_rank_num, actress_video in enumerate(video['actress_video_list']):

        # 変数情報の生成
        # rank
        rank = str(actress_rank_num + 1)

        # 前方一致でhttps://www.dmm.co.jp/がない場合は追加
        if 'https://www.dmm.co.jp/' not in actress_video['video_url']:
            url = 'https://www.dmm.co.jp/' + actress_video['video_url']
        else:
            url = actress_video['video_url']

        # actress video html 生成
        actress_video_html += input_actress_video_html.format(
            rank = rank,
            medal = get_medal_string(rank),
            title = actress_video['title'],
            affiliate_video_url = get_affiliate_url(url, 'package_small', affiliate_id),
            img_url = actress_video['img_url']
        )
    

    ## videoレビューデータを生成
    video_review_html = ''
    for review_index, review_text in enumerate(video['review_list'][:2]):

        # review_icon
        if review_index == 0:
            review_icon = 'man'
        else:
            review_icon = 'b-man'

        # video_review_html 生成
        video_review_html += input_video_review_html.format(
            review_icon = review_icon,
            review_text = truncate_string(review_text, 170)
        )
    
    # sample_img_list
    title = video['title']
    title = ''
    sample_img_list = ''
    #sample_img_list = ''.join(f'<img src="{img}" alt="{title}" />' for img in video['sample_img_list'])
    if video['sample_img_list']: 
        sample_img_list = ''.join(f'<img src="{img}" alt="{title}" /><br>' for img in video['sample_img_list'][1:])
        #sample_img_list = ''.join(f'<img src="{img}" alt="{title}" />' for img in video['sample_img_list'][1:-1])

    # actress_video_block_html
    if video['actress'] != '':
        actress = f"【{video['actress']}】関連作品"
    else:
        actress = f"関連作品"
    actress_video_block_html = ''
    if 'actress_url' in video:
        actress_video_block_html = input_actress_video_block_html.format(
            gpt_text_actress_video = gpt_text['actress_video'][rank_num],
            actress_yomi = video['actress'],
            actress = actress,
            parts_actress_video = actress_video_html,
            affiliate_actress_url = affiliate_actress_url,
        )


    # 前方一致でhttps://www.dmm.co.jp/がない場合は追加
    if 'https://www.dmm.co.jp/' not in video['video_url']:
        url = 'https://www.dmm.co.jp/' + video['video_url']
    else:
        url = video['video_url']

    # other_video_html    
    other_video_html = ''
    if not type in _settings.specialized_genre_list and video['actress'] != '':
        other_video_html = input_other_video_html.format(
            affiliate_video_url = get_affiliate_url(url, 'package_large', affiliate_id),
            actress = video['actress'],
            actress_yomi = video['actress'],
        )

    ## base htmlを生成
    if video['actress'] != '':
        title = f"{gpt_text['title'][rank_num]}【{video['actress']}】"
    else:
        title = f"{gpt_text['title'][rank_num]}"

    if 'size' in video and type in _settings.specialized_genre_list:
        title = f"【{video['actress']}】{_settings.specialized_genre_list[type]}{gpt_text['title'][rank_num]}"

    # 前方一致でhttps://www.dmm.co.jp/がない場合は追加
    if 'https://www.dmm.co.jp/' not in video['video_url']:
        url = 'https://www.dmm.co.jp/' + video['video_url']
    else:
        url = video['video_url']

    base_html = input_base_html.format(
        #parts_free_video = free_video_html,
        parts_free_video = webp_html,
	    #title = f"【{video['actress_yomi']}】{video['title']}",
        title = title,
        parts_video_info = video_info_html,
        sample_img_list = sample_img_list,
        img_url_l_sample_video = video['sample_img_list'][4] if video['sample_img_list'] and len(video['sample_img_list']) > 4 else video['img_url_l'],
        parts_video_review = video_review_html,
        cid = video['cid'],
        gpt_text = gpt_text['item'][rank_num][0],
        actress = video['actress'],
        parts_actress_video_block = actress_video_block_html,
        affiliate_video_url = get_affiliate_url(url, 'package_large', affiliate_id),
        affiliate_actress_url = affiliate_actress_url,
        description = video['synopsis'],
        page_count = video['meta']['page'],
        parts_other_video = other_video_html
    )

    # 生成したHTMLデータをファイルに保存
    with open(html_file, 'w') as file:
        file.write(base_html)

    print("Done: ", current_function_name)

    return base_html


# 投稿に使うHTMLを作成(bulk)
def generate_post_html_bulk(video, gpt_text, rank_num, index, site_id, type, lang='', single_type=None):
    affiliate_id = _settings.affiliate_id['other_list']

    # 記事POST用に使用するHTMLの保存ファイルパス
    html_file = _settings.new_post_html_dir + str(index) + '_' + str(rank_num) + '_' + site_id + '.html'

    # debugフラグがONの場合、cacheから取得
    if _settings.debug_flag['use_cache_post_html'] == True :
        html = read_file(html_file)
        return html

    # キャシュ保存パスをお掃除
    if index == 0:
        delete_files_in_directory(_settings.new_post_html_dir)

    # 現在の関数名を取得(log用)
    current_function_name = inspect.currentframe().f_code.co_name
    print("Start: ", current_function_name)

    # 各HTMLformatを読み込み
    if lang == '' and not single_type:
        group_dir = '/single'
    elif single_type:
        group_dir = '/single_' + single_type
    else:
        group_dir = '/lang_' + lang
        
    input_base_html = read_file(_settings.input_html_dir + group_dir +'/base.html')
    input_free_video_html = read_file(_settings.input_html_dir + group_dir + '/free_video.html')
    input_free_video_new_html = read_file(_settings.input_html_dir + group_dir + '/free_video_new.html')
    input_free_video_gif_html = read_file(_settings.input_html_dir + group_dir + '/free_video_gif.html')
    input_video_info_html = read_file(_settings.input_html_dir + group_dir + '/video_info.html')
    input_video_info_customize_html = read_file(_settings.input_html_dir + group_dir + '/video_info_customize.html')
    input_actress_video_html = read_file(_settings.input_html_dir + group_dir + '/actress_video.html')
    input_actress_video_block_html = read_file(_settings.input_html_dir + group_dir + '/actress_video_block.html')
    input_video_review_html = read_file(_settings.input_html_dir + group_dir + '/video_review.html')
    input_other_video_html = read_file(_settings.input_html_dir + group_dir + '/other_video.html')

    if type == 'bulk_update' and not lang == '':
        input_base_html = read_file(_settings.input_html_dir+'/single_update/base.html')
        input_free_video_gif_html = read_file(_settings.input_html_dir + '/single_update/free_video_gif.html')

    # サンプル動画
    # upload_date
    now = datetime.now()
    upload_date = now.strftime("%Y-%m-%dT%H:%M:%S%z")+'+09:00'
    free_video_html = ''

    # shrinkサイトでなく、またgptの出力結果site_idが登録されていなければ、av-new.comとして扱う
    if gpt_text:
        if not site_id in gpt_text['title'][rank_num]:
            site_id = 'av-new.com'

    if 'gif_url' in video and not single_type:
        if not ('vr' in video['cid'] or 'VR' in video['title']):
            if video['actress'] != '':
                if gpt_text:
                    title = f"【{video['actress']}】{gpt_text['title'][rank_num][site_id]}"
                else:
                    title = f"【{video['actress']}】{video['title']}"
            else:
                if gpt_text:
                    title = f"{gpt_text['title'][rank_num][site_id]}"
                else:
                    title = f"{video['title']}"
                
            free_video_html = input_free_video_gif_html.format(
                affiliate_id = affiliate_id,
                title = googleTranslate.translate_japanese_to_english(title, lang),
                gif_url = video['gif_url'],
                cid = video['cid'],
                #以下、サンプル動画INDEX用
                upload_date = upload_date,
                duration = googleTranslate.translate_japanese_to_english(video['meta']['duration'].replace('分', ''), lang),
                favorite_count = googleTranslate.translate_japanese_to_english(video['favorite_count'], lang),
                img_url_l = video['img_url_l']
            )

    else: 
        if not ('vr' in video['cid'] or 'VR' in video['title']):
            if 'sample_video_src' in video and video['sample_video_src']:
                free_video_html = input_free_video_new_html.format(
                    affiliate_id = affiliate_id,
                    img_url_l = video['img_url_l'],
                    sample_video_src = video['sample_video_src'],
                    affiliate_video_url = get_affiliate_url(video['video_url'], 'package_large', affiliate_id),
                    duration = video['meta']['duration'].replace('分', '')
                )

            else:
                free_video_html = input_free_video_html.format(
                    affiliate_id = affiliate_id,
                    cid = video['cid'],
                    affiliate_video_url = get_affiliate_url(video['video_url'], 'package_large', affiliate_id),
                    actress = googleTranslate.translate_japanese_to_english(video['actress'], lang),
                    title = googleTranslate.translate_japanese_to_english(video['title'], lang),
                    upload_date = upload_date,
                    duration = googleTranslate.translate_japanese_to_english(video['meta']['duration'].replace('分', ''), lang),
                    favorite_count = video['favorite_count'],
                    img_url_l = video['img_url_l']
                )

        # single vr用にelse追加
        else:
            free_video_html = input_free_video_html.format(
                affiliate_id = affiliate_id,
                title = video['title'],
                img_url_l = video['img_url_l'],
                affiliate_video_url = get_affiliate_url(video['video_url'], 'package_large', affiliate_id),
                duration = video['meta']['duration'].replace('分', '')
            )

    # 動画メタ情報
    affiliate_actress_url = ''
    if 'actress_url' in video:
        affiliate_actress_url = get_affiliate_url(video['actress_url'],'link',affiliate_id)

    if site_id == 'av-new.com':

        video_info_list = f"""
            <tr><td>{googleTranslate.translate_japanese_to_english('配信開始日', lang)}</td><td>{video['meta']['delivery_start_date']}</td></tr>
            <tr><td>{googleTranslate.translate_japanese_to_english('商品発売日', lang)}</td><td>{video['meta']['sale_start_date'] if 'sale_start_date' in video['meta'] else ''}</td></tr>
            <tr><td>{googleTranslate.translate_japanese_to_english('出演者', lang)}</td><td><a href="{affiliate_actress_url}" target="_blank" rel="noopener nofollow" title="{video['actress_yomi']}">{googleTranslate.translate_japanese_to_english(video['actress_yomi'], lang)}</a></td></tr>
            <tr><td>{googleTranslate.translate_japanese_to_english('収録時間', lang)}</td><td>{googleTranslate.translate_japanese_to_english(video['meta']['duration'], lang)}</td></tr>
            <tr><td>{googleTranslate.translate_japanese_to_english('監督', lang)}</td><td>{googleTranslate.translate_japanese_to_english(video['meta']['director'], lang) if 'director' in video['meta'] else ''}</td></tr>
            <tr><td>{googleTranslate.translate_japanese_to_english('メーカー', lang)}</td><td>{googleTranslate.translate_japanese_to_english(video['meta']['maker'], lang) if 'maker' in video['meta'] else ''}</td></tr>
            <tr><td>{googleTranslate.translate_japanese_to_english('お気に入り数', lang)}</td><td>{video['favorite_count']}</td></tr>
        """

        video_info_html = input_video_info_customize_html.format(
            video_info_list = video_info_list,
            title = googleTranslate.translate_japanese_to_english(video['title'], lang),
            affiliate_video_url = get_affiliate_url(video['video_url'], 'package_large', affiliate_id),
            img_url_l = video['sample_img_list'][0] if video['sample_img_list'] else video['img_url_l'],
            cid = video['cid'],
            welcome_coupon_url = "https://al.dmm.co.jp/?lurl=https%3A%2F%2Fwww.dmm.co.jp%2Fdigital%2F-%2Fwelcome-coupon%2F&af_id=" + affiliate_id + "&ch=toolbar&ch_id=link"
        )

    else:
        video_info_html = input_video_info_html.format(
            actress = googleTranslate.translate_japanese_to_english(video['actress'], lang),
            title = googleTranslate.translate_japanese_to_english(video['title'], lang),
            affiliate_video_url = get_affiliate_url(video['video_url'], 'package_large', affiliate_id),
            #img_url_l = video['img_url_l'],
            #img_url_l = video['sample_img_list'][0],
            img_url_l = video['sample_img_list'][0] if video['sample_img_list'] else video['img_url_l'],
            affiliate_actress_url = affiliate_actress_url,
            #actress_yomi = video['actress_yomi'],  #TODO:なぜかエラーになる　()があると。
            gpt_text = gpt_text['title'][rank_num][site_id],
            actress_yomi = googleTranslate.translate_japanese_to_english(video['actress'], lang),
            director = video['meta']['director'] if 'director' in video['meta'] else '',
            maker = video['meta']['maker'] if 'maker' in video['meta'] else '',
            sale_start_date = video['meta']['sale_start_date'] if 'sale_start_date' in video['meta'] else '',
            duration = video['meta']['duration'],
            favorite_count = video['favorite_count'],
            cid = video['cid'],
            welcome_coupon_url = "https://al.dmm.co.jp/?lurl=https%3A%2F%2Fwww.dmm.co.jp%2Fdigital%2F-%2Fwelcome-coupon%2F&af_id=" + affiliate_id + "&ch=toolbar&ch_id=link"
        )

    ## 女優ビデオランキングデータを生成
    actress_video_html = ''
    for actress_rank_num, actress_video in enumerate(video['actress_video_list']):

        # 変数情報の生成
        # rank
        rank = str(actress_rank_num + 1)

        # actress video html 生成
        actress_video_html += input_actress_video_html.format(
            rank = rank,
            medal = get_medal_string(rank),
            title = googleTranslate.translate_japanese_to_english(actress_video['title'], lang),
            affiliate_video_url = get_affiliate_url(actress_video['video_url'], 'package_small', affiliate_id),
            img_url = actress_video['img_url']
        )
    

    ## videoレビューデータを生成
    video_review_html = ''
    for review_index, review_text in enumerate(video['review_list'][:2]):

        # review_icon
        if review_index == 0:
            review_icon = 'man'
        else:
            review_icon = 'b-man'

        # video_review_html 生成
        video_review_html += input_video_review_html.format(
            review_icon = review_icon,
            review_text = googleTranslate.translate_japanese_to_english(truncate_string(review_text, 170), lang)
        )
    
    # sample_img_list
    title = googleTranslate.translate_japanese_to_english(video['title'], lang)
    sample_img_list = ''
    #sample_img_list = ''.join(f'<img src="{img}" alt="{title}" />' for img in video['sample_img_list'])
    if video['sample_img_list']: 
        if type == 'bulk_update':
            sample_img_list = ''.join(f'<img src="{img}" alt="{title}" />' for img in video['sample_img_list'][1:])
        else:
            sample_img_list = ''.join(f'<img src="{img}" alt="{title}" />' for img in video['sample_img_list'][1:-1])

        if single_type:
            sample_img_list = ''.join(f'<img src="{img}" alt="{title}" />' for img in video['sample_img_list'])


    # actress_video_block_html
    if video['actress'] != '':
        actress = f"【{video['actress']}】関連作品"
    else:
        actress = f"関連作品"
    actress_video_block_html = ''
    if 'actress_url' in video:
        actress_video_block_html = input_actress_video_block_html.format(
            gpt_text_actress_video = googleTranslate.translate_japanese_to_english(gpt_text['actress_video'][rank_num], lang) if gpt_text else '',
            actress_yomi = googleTranslate.translate_japanese_to_english(video['actress_yomi'], lang),
            actress = googleTranslate.translate_japanese_to_english(actress, lang),
            parts_actress_video = actress_video_html,
            affiliate_actress_url = affiliate_actress_url,
        )

    # other_video_html
    actress = ''
    if video['actress'] != '':
        actress = f"【{video['actress']}】"

    other_video_html = input_other_video_html.format(
        affiliate_video_url = get_affiliate_url(video['video_url'], 'package_large', affiliate_id),
        actress = googleTranslate.translate_japanese_to_english(actress, lang),
        actress_yomi = googleTranslate.translate_japanese_to_english(video['actress'], lang),
    )

    ## base htmlを生成
    if video['actress'] != '':
        if gpt_text:
            title = f"【{video['actress']}】{gpt_text['title'][rank_num][site_id]}"
        else:
            title = f"【{video['actress']}】{video['title']}"
    else:
        if gpt_text:
            title = f"{gpt_text['title'][rank_num][site_id]}"
        else:
            title = f"{video['title']}"


    base_html = input_base_html.format(
        parts_free_video = free_video_html,
	    #title = f"【{video['actress_yomi']}】{video['title']}",
        #title = googleTranslate.translate_japanese_to_english(title, lang),
	    title = googleTranslate.translate_japanese_to_english(video['title'],lang),
        parts_video_info = video_info_html,
        sample_img_list = sample_img_list,
        img_url_l_sample_video = video['sample_img_list'][4] if video['sample_img_list'] and len(video['sample_img_list']) > 4 else video['img_url_l'],
        parts_video_review = video_review_html,
        cid = video['cid'],
        duration = video['meta']['duration'],
        label = video['meta']['label'],
        gpt_text = gpt_text['item'][rank_num][0] if gpt_text else '',
        actress = googleTranslate.translate_japanese_to_english(video['actress'], lang),
        parts_actress_video_block = actress_video_block_html,
        affiliate_video_url = get_affiliate_url(video['video_url'], 'package_large', affiliate_id),
        affiliate_actress_url = affiliate_actress_url,
        parts_other_video = other_video_html
    )

    with open(html_file, 'w') as file:
        file.write(base_html)

    print("Done: ", current_function_name)

    return base_html


# 投稿に使うHTMLを作成(single)
def generate_post_html_single(video, gpt_text, index, rank_num, type):
    # '_list' で一致した場合はother_list
    if not type in _settings.affiliate_id and type.endswith('_list'):
        type = 'other_list'

    affiliate_id = _settings.affiliate_id[type]

    # 記事POST用に使用するHTMLの保存ファイルパス
    html_file = _settings.new_post_html_dir + str(index) + '_' + str(rank_num) + '.html'

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
    input_base_html = read_file(_settings.input_html_dir+'/single/base.html')
    input_free_video_html = read_file(_settings.input_html_dir + '/single/free_video.html')
    input_free_video_new_html = read_file(_settings.input_html_dir + '/single/free_video_new.html')
    input_free_video_gif_html = read_file(_settings.input_html_dir + '/single/free_video_gif.html')
    input_video_info_html = read_file(_settings.input_html_dir + '/single/video_info.html')
    input_video_info_customize_html = read_file(_settings.input_html_dir + '/single/video_info_customize.html')
    input_actress_video_html = read_file(_settings.input_html_dir + '/single/actress_video.html')
    input_actress_video_block_html = read_file(_settings.input_html_dir + '/single/actress_video_block.html')
    input_video_review_html = read_file(_settings.input_html_dir + '/single/video_review.html')
    input_other_video_html = read_file(_settings.input_html_dir + '/single/other_video.html')

    # サンプル動画
    # upload_date
    now = datetime.now()
    upload_date = now.strftime("%Y-%m-%dT%H:%M:%S%z")+'+09:00'
    free_video_html = ''

    if 'gif_url' in video :
        if not ('vr' in video['cid'] or 'VR' in video['title']):
            if video['actress'] != '':
                title = f"【{video['actress']}】{gpt_text['title'][rank_num]}"
            else:
                title = f"{gpt_text['title'][rank_num]}"
                
            free_video_html = input_free_video_gif_html.format(
                affiliate_id = affiliate_id,
                title = title,
                gif_url = video['gif_url'],
                cid = video['cid'],
                #以下、サンプル動画INDEX用
                upload_date = upload_date,
                duration = video['meta']['duration'].replace('分', ''),
                favorite_count = video['favorite_count'],
                img_url_l = video['img_url_l']
            )

    else: 
        if not ('vr' in video['cid'] or 'VR' in video['title']):
            if 'sample_video_src' in video and video['sample_video_src']:
                free_video_html = input_free_video_new_html.format(
                    affiliate_id = affiliate_id,
                    img_url_l = video['img_url_l'],
                    sample_video_src = video['sample_video_src']
                )

            else:
                free_video_html = input_free_video_html.format(
                    affiliate_id = affiliate_id,
                    cid = video['cid'],
                    affiliate_video_url = get_affiliate_url(video['video_url'], 'package_large', affiliate_id),
                    actress = video['actress'],
                    title = video['title'],
                    upload_date = upload_date,
                    duration = video['meta']['duration'].replace('分', ''),
                    favorite_count = video['favorite_count'],
                    img_url_l = video['img_url_l']
                )
     

    # 動画メタ情報
    affiliate_actress_url = ''
    if 'actress_url' in video:
        affiliate_actress_url = get_affiliate_url(video['actress_url'],'link',affiliate_id)

    if type == 'shiroto_list':
        video_info_list = f"""
            <tr><td>出演者</td><td>{video['actress']}</td></tr>
            <tr><td>スリーサイズ</td><td>{video['size']}</td></tr>
            <tr><td>配信開始日</td><td>{video['meta']['delivery_start_date']}</td></tr>
            <tr><td>収録時間</td><td>{video['meta']['duration']}</td></tr>
            <tr><td>レーベル</td><td>{video['meta']['label']}</td></tr>
            <tr><td>お気に入り数</td><td>{video['favorite_count']}件</td></tr>
        """

        video_info_html = input_video_info_customize_html.format(
            video_info_list = video_info_list,
            title = video['title'],
            affiliate_video_url = get_affiliate_url(video['video_url'], 'package_large', affiliate_id),
            img_url_l = video['sample_img_list'][0] if video['sample_img_list'] else video['img_url_l'],
            cid = video['cid'],
            welcome_coupon_url = "https://al.dmm.co.jp/?lurl=https%3A%2F%2Fwww.dmm.co.jp%2Fdigital%2F-%2Fwelcome-coupon%2F&af_id=" + affiliate_id + "&ch=toolbar&ch_id=link"
        )

    elif type == 'new_list':

        video_info_list = f"""
            <tr><td>配信開始日</td><td>{video['meta']['delivery_start_date']}</td></tr>
            <tr><td>商品発売日</td><td>{video['meta']['sale_start_date']}</td></tr>
            <tr><td>出演者</td><td><a href="{affiliate_actress_url}" target="_blank" rel="noopener nofollow" title="{video['actress_yomi']}">{video['actress_yomi']}</a></td></tr>
            <tr><td>収録時間</td><td>{video['meta']['duration']}</td></tr>
            <tr><td>監督</td><td>{video['meta']['director']}</td></tr>
            <tr><td>メーカー</td><td>{video['meta']['maker']}</td></tr>
            <tr><td>収録時間</td><td>{video['meta']['duration']}</td></tr>
            <tr><td>お気に入り数</td><td>{video['favorite_count']}件</td></tr>
        """

        video_info_html = input_video_info_customize_html.format(
            video_info_list = video_info_list,
            title = video['title'],
            affiliate_video_url = get_affiliate_url(video['video_url'], 'package_large', affiliate_id),
            img_url_l = video['sample_img_list'][0] if video['sample_img_list'] else video['img_url_l'],
            cid = video['cid'],
            welcome_coupon_url = "https://al.dmm.co.jp/?lurl=https%3A%2F%2Fwww.dmm.co.jp%2Fdigital%2F-%2Fwelcome-coupon%2F&af_id=" + affiliate_id + "&ch=toolbar&ch_id=link"
        )

    else:
        video_info_html = input_video_info_html.format(
            actress = video['actress'],
            title = video['title'],
            affiliate_video_url = get_affiliate_url(video['video_url'], 'package_large', affiliate_id),
            #img_url_l = video['img_url_l'],
            #img_url_l = video['sample_img_list'][0],
            img_url_l = video['sample_img_list'][0] if video['sample_img_list'] else video['img_url_l'],
            affiliate_actress_url = affiliate_actress_url,
            #actress_yomi = video['actress_yomi'],  #TODO:なぜかエラーになる　()があると。
            actress_yomi = video['actress'],
            director = video['meta']['director'] if 'director' in video['meta'] else '',
            maker = video['meta']['maker'] if 'maker' in video['meta'] else '',
            sale_start_date = video['meta']['sale_start_date'] if 'sale_start_date' in video['meta'] else '',
            duration = video['meta']['duration'],
            favorite_count = video['favorite_count'],
            cid = video['cid'],
            welcome_coupon_url = "https://al.dmm.co.jp/?lurl=https%3A%2F%2Fwww.dmm.co.jp%2Fdigital%2F-%2Fwelcome-coupon%2F&af_id=" + affiliate_id + "&ch=toolbar&ch_id=link"
        )

    ## 女優ビデオランキングデータを生成
    actress_video_html = ''
    for actress_rank_num, actress_video in enumerate(video['actress_video_list']):

        # 変数情報の生成
        # rank
        rank = str(actress_rank_num + 1)

        # actress video html 生成
        actress_video_html += input_actress_video_html.format(
            rank = rank,
            medal = get_medal_string(rank),
            title = actress_video['title'],
            affiliate_video_url = get_affiliate_url(actress_video['video_url'], 'package_small', affiliate_id),
            img_url = actress_video['img_url']
        )
    

    ## videoレビューデータを生成
    video_review_html = ''
    for review_index, review_text in enumerate(video['review_list'][:2]):

        # review_icon
        if review_index == 0:
            review_icon = 'man'
        else:
            review_icon = 'b-man'

        # video_review_html 生成
        video_review_html += input_video_review_html.format(
            review_icon = review_icon,
            review_text = truncate_string(review_text, 170)
        )
    
    # sample_img_list
    title = video['title']
    title = ''
    sample_img_list = ''
    #sample_img_list = ''.join(f'<img src="{img}" alt="{title}" />' for img in video['sample_img_list'])
    if video['sample_img_list']: 
        #sample_img_list = ''.join(f'<img src="{img}" alt="{title}" />' for img in video['sample_img_list'][1:])
        sample_img_list = ''.join(f'<img src="{img}" alt="{title}" />' for img in video['sample_img_list'][1:-1])

    # actress_video_block_html
    if video['actress'] != '':
        actress = f"【{video['actress']}】関連作品"
    else:
        actress = f"関連作品"
    actress_video_block_html = ''
    if 'actress_url' in video:
        actress_video_block_html = input_actress_video_block_html.format(
            gpt_text_actress_video = gpt_text['actress_video'][rank_num],
            actress_yomi = video['actress_yomi'],
            actress = actress,
            parts_actress_video = actress_video_html,
            affiliate_actress_url = affiliate_actress_url,
        )

    # other_video_html
    other_video_html = ''
    if not type in _settings.specialized_genre_list and video['actress'] != '':
        other_video_html = input_other_video_html.format(
            affiliate_video_url = get_affiliate_url(video['video_url'], 'package_large', affiliate_id),
            actress = video['actress'],
            actress_yomi = video['actress'],
        )

    ## base htmlを生成
    if video['actress'] != '':
        title = f"【{video['actress']}】{gpt_text['title'][rank_num]}"
    else:
        title = f"{gpt_text['title'][rank_num]}"

    if 'size' in video and type in _settings.specialized_genre_list:
        title = f"【{video['actress']}】{_settings.specialized_genre_list[type]}{gpt_text['title'][rank_num]}"


    base_html = input_base_html.format(
        parts_free_video = free_video_html,
	    #title = f"【{video['actress_yomi']}】{video['title']}",
        title = title,
        parts_video_info = video_info_html,
        sample_img_list = sample_img_list,
        img_url_l_sample_video = video['sample_img_list'][4] if video['sample_img_list'] and len(video['sample_img_list']) > 4 else video['img_url_l'],
        parts_video_review = video_review_html,
        cid = video['cid'],
        gpt_text = gpt_text['item'][rank_num][0],
        actress = video['actress'],
        parts_actress_video_block = actress_video_block_html,
        affiliate_video_url = get_affiliate_url(video['video_url'], 'package_large', affiliate_id),
        affiliate_actress_url = affiliate_actress_url,
        parts_other_video = other_video_html
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
    generate_post_html_video(dummy_input_plan_data, dummy_gpt_text)

