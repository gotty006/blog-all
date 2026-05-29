from geopy.geocoders import Nominatim

def remove_last_char_if_in_list(input_str):
    # 末尾の文字が削除対象のリスト
    characters_to_remove = ['都', '府', '県']

    # 文字列が空でない場合、末尾の文字が指定したリストに含まれていれば削除
    if input_str and input_str[-1] in characters_to_remove:
        return input_str[:-1]
    else:
        return input_str

def get_prefecture(station_name):
    geolocator = Nominatim(user_agent="my_geocoder")

    try:
        location = geolocator.geocode(f"{station_name} 駅", language="ja")
        if location:
            address = location.address
            # addressから市町村区名を取得
            city_name = address.split(",")[-3]
            return remove_last_char_if_in_list(city_name.strip())
        else:
            return "未指定"
    except Exception as e:
        print(f"エラー: {e}")
        return "エラー"

# 改行で区切られた駅名の文字列
stations_str = """
大阪梅田
本町
千葉
津田沼
銀座
大船
浦和
豊洲
東梅田
大阪梅田
大森
武蔵溝ノ口
大阪阿部野橋
川口
表参道
札幌
朝霞台
日本橋
大阪難波
南越谷
新越谷
さっぽろ
新小岩
鶴見
西武新宿
大通
北朝霞
心斎橋
上大岡
桜木町
霞ヶ関
新宿三丁目
神戸
小岩
広島
高槻
橋本
あざみ野
京急川崎
新今宮
本厚木
練馬
菊名
春日
川越
新百合ヶ丘
天神
調布
相模大野
西鉄福岡（天神）
王子
大和
岡山
市川
本八幡
蕨
平塚
辻堂
下北沢
東陽町
大和
水道橋
南浦和
堺筋本町
"""

# 改行で分割してリストにする
stations = stations_str.strip().split('\n')

# 駅名ごとに都道府県を取得して表示
for station in stations:
    prefecture = get_prefecture(station)
    print(f"{station}駅,{prefecture}")
