import inspect
import json
import os
from submodule import executeGpt
from submodule import _settings

# 文字列がJSONフォーマットか確認し、dictに変換する関数
def validate_and_convert_to_dict(json_string):
    try:
        # JSON文字列をdictに変換
        parsed_dict = json.loads(json_string)
        # dictかどうかを確認
        if isinstance(parsed_dict, dict):
            return parsed_dict
        else:
            print("JSONフォーマットですが、dict形式ではありません。")
            return None
    except json.JSONDecodeError:
        # JSONフォーマットが正しくない場合
        print("JSONフォーマットではありません。")
        return None

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


# タイトルテキスト生成
def generate_title_text(video, add_category=''):
    if not video['is_shiroto']:
        prompt = f"""
        下記の作品タイトルを、27文字程度の文言で要約して表してください。
        完結に示してください。「です」「ます」形式にはしないでください。
        句点「。」も使わず、「!」等を使ってカジュアルな文章にしてください。
        また、人物名は含めないようにしてください。

        {add_category}

        作品タイトル:
        {video['title']}
        """
    else:
        prompt = f"""
        下記の作品タイトルを、27文字程度の文言で要約して表してください。
        完結に示してください。「です」「ます」形式にはしないでください。
        句点「。」も使わず、「!」等を使ってカジュアルな文章にしてください。
        また、人物名は含めないようにしてください。

        {add_category}

        作品タイトル:
        {video['title']}

        作品詳細:
        {video['synopsis']}
        """

    if _settings.debug_flag['use_deep_seek']:
        answer = executeGpt.execute_deepseek_free_text(prompt)
    else:
        answer = executeGpt.execute_gpt_free_text(prompt)
    print(video['title'])
    print(add_category)
    print(answer)

    return answer


# 投稿に使うGPTテキストを作成
def generate_gpt_text_bulk(video_ranking_data, index, site_config):
    if _settings.debug_flag['use_cache_gpt_answer'] == True :
        # JSONファイルからデータを読み込む
        with open(_settings.gpt_text_data_dir + str(index) + '.json', 'r') as json_file:
            gpt_text = json.load(json_file)
        return gpt_text

    # 現在の関数名を取得(log用)
    current_function_name = inspect.currentframe().f_code.co_name
    print("Start: ", current_function_name)

    # キャシュ保存パスをお掃除
    if index == 0:
        delete_files_in_directory(_settings.gpt_text_data_dir)

    gpt_text = {}
    ranking_text = ""

    ## 各アイテムの文章をGPTで文章を生成
    gpt_text['item'] = []
    gpt_text['actress_video'] = []
    gpt_text['title'] = []
    total = len(video_ranking_data['video_ranking'])
    for i, video in enumerate(video_ranking_data['video_ranking']):
        answers = []

        print(f"gpt answer ({i+1}/{total}): {video['actress']} - {video['title']} =============")
        ranking_text = ranking_text + f"{i+1}位: {video['actress']} 「{video['title']}」 \n"

        # 解析対象のsource jsonをファイルアウトプット
        if not _settings.debug_flag['do_not_gpt_review']:
            for source_data in [video['review_list'], video['synopsis_all']]:

                # reviewが0件の場合は、gpt生成処理をSKIP
                if source_data == []:
                    answers.append('')
                    print('review is None.')
                    continue

                with open(_settings.source_dir + 'gpt_source.json', 'w') as json_file:
                    json.dump(source_data, json_file, indent=2, ensure_ascii=False)

                prompt = _settings.gpt_prompt['other_list']
                answer = executeGpt.execute_gpt_to_datafile(prompt, _settings.source_dir).response.replace("\n", "")
                answers.append(answer)
        
        else:
            answers = ['','']

        gpt_text['item'].append(answers)
        print(f"gpt answer ({i+1}/{total}): {video['actress']} - {video['title']} =============")
        print(answers)

        ## 女優のほかおすすめビデオの文章生成
        answer = ''
        if not _settings.debug_flag['do_not_gpt_actress_ranking']:
            actress_ranking_text = ""
            for i, item in enumerate(video['actress_video_list']):
                actress_ranking_text = actress_ranking_text + f"{i+1}位: {item['title']} \n"

            prompt = f"""
            下記の情報を使用して、おすすめのAV（アダルトビデオ）を紹介するリード文を作成してください。
            100文字程度で、閲覧者の興味をひくような内容の文章にしてください。
            読みやすいように、改行を適度に挿入してください。改行を挿入するときは<br>で挿入してください。

            基本情報：
            {video['actress_yomi']}さんが出演している、AVのランキングです。この女優さんが気になった方は是非チェックしてみてください！

            ランキング情報：
            {actress_ranking_text}
            """

            if _settings.debug_flag['use_deep_seek']:
                answer = executeGpt.execute_deepseek_free_text(prompt)
            else:
                answer = executeGpt.execute_gpt_free_text(prompt)

        print(answer)
        gpt_text['actress_video'].append(answer)

        # titleをオリジナル化
        count = 0
        other_site_prompt = ''
        recovery_answers = {}
        add_category = "出力は必ずjson形式で出力してください。json以外の文字列は出力しないでください。「```json」のような出力は不要です。\n　例:\n {\"ID1\":\"要約1\",\"ID2\":\"要約2\"}\n\n"
        print(site_config)

        # site_configの先頭がsingle:allの場合は1要素目にav-all用のpromptを設定
        if site_config[0]['single'] == 'all':
            add_category = add_category + f"1要素目は、key:「{site_config[0]['id']}」、value: 条件に従って自由に出力してください。また、「エロい」「エロすぎる」などのワードも含めてください。\n"
            count = 1

        for site in site_config: 
            post_tag_list = site['post_tag_list']
            
            # デバッグ出力を追加
            print(f"DEBUG: site_id = {site['id']}")
            print(f"DEBUG: post_tag_list = {post_tag_list}")
            print(f"DEBUG: video['meta']['genre_list'] = {video['meta']['genre_list']}")
            print(f"DEBUG: intersection = {set(post_tag_list) & set(video['meta']['genre_list'])}")

            # スプシのpost_tag_listと、メタに含まれるジャンルリストで一致するものがあれば、gpt出力対象
            # または、single が 'all' 以外の場合は必ず処理する
            if bool(set(post_tag_list) & set(video['meta']['genre_list'])) or site['single'] != 'all':
                count += 1

                # 設定されるカテゴリーに関連したワードを含める
                category_txt = ''
                for category in site['set_category_list']:
                    if category in video['meta']['genre_list']:
                        category_txt = f"また、「{category}」のワードも含めてください。"
                        break

                other_site_prompt = other_site_prompt + f"{str(count)}要素目は、key: 「{site['id']}」、value: 可能であれば「{site['prompt_word']}」に関するワードを入れて出力してください。また、「エロい」「エロすぎる」などのワードも含めてください。{category_txt}\n"
                recovery_answers[site['id']] = ""

        add_category = add_category + other_site_prompt
        add_category = add_category + f"上記の条件に従って、{str(count)}通りの要約を出力してください。また、改行は含めずに出力してください。"
        
        # タイトルテキスト生成
        answer = generate_title_text(video, add_category)

        # JSONフォーマットを確認し、dictに変換
        answer_dict = validate_and_convert_to_dict(answer)
        if not answer_dict:
            print('ERROR gpt output text is not json format.')
            print(answer)
            print("count: " + str(count))

            # 簡易プロンプト（カテゴリ要素なし）でリトライ
            print('Retry...')

            # タイトルテキスト生成
            answer = generate_title_text(video, add_category='')
            # すべての値を 'default' に更新
            answer_dict = {key: answer for key in recovery_answers}
            answer_dict[site_config[0]['id']] = answer

        print(answer_dict)
        gpt_text['title'].append(answer_dict)

    # 生成したgptテキストをキャッシュファイルに保存
    with open(_settings.gpt_text_data_dir + str(index) + '.json', 'w') as json_file:
        json.dump(gpt_text, json_file, indent=2, ensure_ascii=False) 

    print("Done: ", current_function_name)

    return gpt_text


# 投稿に使うGPTテキストを作成(同人)
def generate_dojin_gpt_text(video_ranking_data, index, type):
    if _settings.debug_flag['use_cache_gpt_answer'] == True :
        # JSONファイルからデータを読み込む
        with open(_settings.gpt_text_data_dir + str(index) + '.json', 'r') as json_file:
            gpt_text = json.load(json_file)
        return gpt_text

    # 現在の関数名を取得(log用)
    current_function_name = inspect.currentframe().f_code.co_name
    print("Start: ", current_function_name)

    gpt_text = {}
    ranking_text = ""

    ## 各アイテムの文章をGPTで文章を生成
    gpt_text['item'] = []
    gpt_text['actress_video'] = []
    gpt_text['title'] = []
    total = len(video_ranking_data['video_ranking'])
    for i, video in enumerate(video_ranking_data['video_ranking']):
        answers = []

        print(f"gpt answer ({i+1}/{total}): {video['actress']} - {video['title']} =============")
        ranking_text = ranking_text + f"{i+1}位: {video['actress']} 「{video['title']}」 \n"

        # 解析対象のsource jsonをファイルアウトプット
        if not _settings.debug_flag['do_not_gpt_review']:
            for source_data in [video['review_list'], video['synopsis_all']]:

                # reviewが0件の場合は、gpt生成処理をSKIP
                if source_data == []:
                    answers.append('')
                    print('review is None.')
                    continue

                with open(_settings.source_dir + 'gpt_source.json', 'w') as json_file:
                    json.dump(source_data, json_file, indent=2, ensure_ascii=False)

                # 全体概要を生成
                # '_list' で一致した場合はother_list
                type_prompt = type
                if not type in _settings.gpt_prompt and type.endswith('_list'):
                    type_prompt = 'other_list'

                prompt = _settings.gpt_prompt[type_prompt]
                answer = executeGpt.execute_gpt_to_datafile(prompt, _settings.source_dir).response.replace("\n", "")
                answers.append(answer)
        else:
            answers = ['','']

        gpt_text['item'].append(answers)
        print(f"gpt answer ({i+1}/{total}): {video['actress']} - {video['title']} =============")
        print(answers)

        ## 女優のほかおすすめビデオの文章生成
        answer = ''
        if not _settings.debug_flag['do_not_gpt_actress_ranking']:
            actress_ranking_text = ""
            for i, item in enumerate(video['actress_video_list']):
                actress_ranking_text = actress_ranking_text + f"{i+1}位: {item['title']} \n"

            prompt = f"""
            下記の情報を使用して、おすすめのアダルト同人誌を紹介するリード文を作成してください。
            100文字程度で、閲覧者の興味をひくような内容の文章にしてください。
            読みやすいように、改行を適度に挿入してください。改行を挿入するときは<br>で挿入してください。

            基本情報：
            {video['actress']} が作者の、アダルト同人誌のランキングです。この作品の作者さんが気になった方は是非チェックしてみてください！

            ランキング情報：
            {actress_ranking_text}
            """

            if _settings.debug_flag['use_deep_seek']:
                answer = executeGpt.execute_deepseek_free_text(prompt)
            else:
                answer = executeGpt.execute_gpt_free_text(prompt)

        print(answer)
        gpt_text['actress_video'].append(answer)

        prompt = f"""
        下記の作品タイトルを、22文字以内の文言で要約して表してください。
        完結に示してください。「です」「ます」形式にはしないでください。
        句点「。」も使わず、「!」等を使ってカジュアルな文章にしてください。
        また、人物名は含めないようにしてください。

        可能であれば、「{video_ranking_data['category']}」と「エロ漫画」のようなワードを含めてください。

        作品タイトル:
        {video['title']}

        作品詳細:
        {video['synopsis']}
        """

        if _settings.debug_flag['use_deep_seek']:
            answer = executeGpt.execute_deepseek_free_text(prompt)
        else:
            answer = executeGpt.execute_gpt_free_text(prompt)
        print(video['title'])
        print(answer)
        gpt_text['title'].append(answer)


    # 生成したgptテキストをキャッシュファイルに保存
    with open(_settings.gpt_text_data_dir + str(index) + '.json', 'w') as json_file:
        json.dump(gpt_text, json_file, indent=2, ensure_ascii=False) 

    print("Done: ", current_function_name)

    return gpt_text


# 投稿に使うGPTテキストを作成
def generate_gpt_text(video_ranking_data, index, type):
    if _settings.debug_flag['use_cache_gpt_answer'] == True :
        # JSONファイルからデータを読み込む
        with open(_settings.gpt_text_data_dir + str(index) + '.json', 'r') as json_file:
            gpt_text = json.load(json_file)
        return gpt_text

    # 現在の関数名を取得(log用)
    current_function_name = inspect.currentframe().f_code.co_name
    print("Start: ", current_function_name)

    gpt_text = {}
    ranking_text = ""

    ## 各アイテムの文章をGPTで文章を生成
    gpt_text['item'] = []
    gpt_text['actress_video'] = []
    gpt_text['title'] = []
    total = len(video_ranking_data['video_ranking'])
    for i, video in enumerate(video_ranking_data['video_ranking']):
        answers = []

        print(f"gpt answer ({i+1}/{total}): {video['actress']} - {video['title']} =============")
        ranking_text = ranking_text + f"{i+1}位: {video['actress']} 「{video['title']}」 \n"

        # 解析対象のsource jsonをファイルアウトプット
        if not _settings.debug_flag['do_not_gpt_review']:
            for source_data in [video['review_list'], video['synopsis_all']]:

                # reviewが0件の場合は、gpt生成処理をSKIP
                if source_data == []:
                    answers.append('')
                    print('review is None.')
                    continue

                with open(_settings.source_dir + 'gpt_source.json', 'w') as json_file:
                    json.dump(source_data, json_file, indent=2, ensure_ascii=False)

                # 全体概要を生成
                # '_list' で一致した場合はother_list
                type_prompt = type
                if not type in _settings.gpt_prompt and type.endswith('_list'):
                    type_prompt = 'other_list'

                prompt = _settings.gpt_prompt[type_prompt]
                answer = executeGpt.execute_gpt_to_datafile(prompt, _settings.source_dir).response.replace("\n", "")
                answers.append(answer)
            else:
                answers = ['','']

        gpt_text['item'].append(answers)
        print(f"gpt answer ({i+1}/{total}): {video['actress']} - {video['title']} =============")
        print(answers)

        ## 女優のほかおすすめビデオの文章生成
        answer = ''
        if not _settings.debug_flag['do_not_gpt_actress_ranking']:
            actress_ranking_text = ""
            for i, item in enumerate(video['actress_video_list']):
                actress_ranking_text = actress_ranking_text + f"{i+1}位: {item['title']} \n"

            prompt = f"""
            下記の情報を使用して、おすすめのAV（アダルトビデオ）を紹介するリード文を作成してください。
            100文字程度で、閲覧者の興味をひくような内容の文章にしてください。
            読みやすいように、改行を適度に挿入してください。改行を挿入するときは<br>で挿入してください。

            基本情報：
            {video['actress_yomi']}さんが出演している、AVのランキングです。この女優さんが気になった方は是非チェックしてみてください！

            ランキング情報：
            {actress_ranking_text}
            """

            if _settings.debug_flag['use_deep_seek']:
                answer = executeGpt.execute_deepseek_free_text(prompt)
            else:
                answer = executeGpt.execute_gpt_free_text(prompt)

        print(answer)
        gpt_text['actress_video'].append(answer)

        # titleをオリジナル化
        # 
        add_category = ""
        if type in _settings.specialized_prompt_word:
            add_category= f"可能であれば、「{_settings.specialized_prompt_word[type]}」に関するワードを入れてください。"

        if not video['is_shiroto']:
            prompt = f"""
            下記の作品タイトルを、22文字以内の文言で要約して表してください。
            完結に示してください。「です」「ます」形式にはしないでください。
            句点「。」も使わず、「!」等を使ってカジュアルな文章にしてください。
            また、人物名は含めないようにしてください。
            {add_category}

            作品タイトル:
            {video['title']}
            """
        else:
            prompt = f"""
            下記の作品タイトルを、22文字以内の文言で要約して表してください。
            完結に示してください。「です」「ます」形式にはしないでください。
            句点「。」も使わず、「!」等を使ってカジュアルな文章にしてください。
            また、人物名は含めないようにしてください。
            {add_category}

            作品タイトル:
            {video['title']}

            作品詳細:
            {video['synopsis']}
            """

        if _settings.debug_flag['use_deep_seek']:
            answer = executeGpt.execute_deepseek_free_text(prompt)
        else:
            answer = executeGpt.execute_gpt_free_text(prompt)
        print(video['title'])
        print(answer)
        gpt_text['title'].append(answer)


    if type == 'video' or type == 'actress':
        ## 共通エリアの文章をGPTで文章生成
        prompt = f"""
        下記の情報を使用して、おすすめのAV（アダルトビデオ）を紹介するWEBページのリード文を作成してください。
        200文字程度で、閲覧者の興味をひくような内容の文章にしてください。
        読みやすいように、改行を適度に挿入してください。改行を挿入するときは<br>で挿入してください。

        WEBページの基本情報：
        今最も抜ける美少女系の人気AV(アダルトビデオ)を、口コミ情報と共にランキング形式で人気順に紹介します。
        かわいいAV女優が出演する作品が上位にランクインしています！

        ランキング情報：
        {ranking_text}
        """

        if _settings.debug_flag['use_deep_seek']:
            answer = executeGpt.execute_deepseek_free_text(prompt)
        else:
            answer = executeGpt.execute_gpt_free_text(prompt)
        print(answer)
        gpt_text['intro'] = answer

    
    # 生成したgptテキストをキャッシュファイルに保存
    with open(_settings.gpt_text_data_dir + str(index) + '.json', 'w') as json_file:
        json.dump(gpt_text, json_file, indent=2, ensure_ascii=False) 

    print("Done: ", current_function_name)

    return gpt_text

