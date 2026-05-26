#import _settings
from submodule import _settings
from PIL import Image, ImageDraw, ImageFont
import warnings
warnings.simplefilter( "ignore", DeprecationWarning )

def resize_and_overlay(base_path, input_path, output_path):
    # 画像の読み込み
    base_img = Image.open(base_path).convert("RGBA")
    input_img = Image.open(input_path).convert("RGBA")

    # input画像を横幅1000にリサイズ（アスペクト比を保持）
    # base_width, base_height = base_img.size
    # new_width = 1000
    # ratio = new_width / input_img.width
    # new_height = int(input_img.height * ratio)

    # # base画像にinput画像を右上にオーバーレイ
    # x_offset = base_width - new_width
    # y_offset = 0
    # base_img.paste(resized_input, (x_offset, y_offset), resized_input)

    # input画像を縦幅800にリサイズ（アスペクト比を保持）
    input_width, input_height = input_img.size
    aspect_ratio = input_width / input_height
    new_height = 760
    new_width = int(new_height * aspect_ratio)
    resized_input = input_img.resize((new_width, new_height), Image.ANTIALIAS)

    # 少し画像を中心に寄せる
    if resized_input.width < 1350 :
        adjustment = int((1350 - resized_input.width) / 2)
    else:
        adjustment = 0

    # base画像にinput画像を右上に重ねる
    #x_offset = base_img.width - resized_input.width
    x_offset = base_img.width - resized_input.width - adjustment
    y_offset = 0
    base_img.paste(resized_input, (x_offset, y_offset), resized_input)

    # 画像の保存
    base_img.save(output_path)


# タイトル文字を挿入
def add_text_to_image(image_path, output_path, text):
    img = Image.open(image_path)

    draw = ImageDraw.Draw(img)
    #font = ImageFont.truetype('Arial.ttf', 24)
    #font = ImageFont.truetype('ヒラギノ丸ゴ ProN W4.ttc', 90)
    font = ImageFont.truetype('/System/Library/Fonts/ヒラギノ角ゴシック W5.ttc', 100)
    draw.text((800, 880), text, '#FFFFFF', font=font, anchor='md')

    img.save(output_path)


# アイキャッチ画像を作成
def generate_eye_catch_image(url, input_path, text, type):
    # 使用例
    base_dir = 'data/inputImg/'
    if type == 'actress':
        base_path = base_dir + 'base_actress.png'
    else:
        base_path = base_dir + 'base.png'
    output_joined_path =  base_dir + 'joined.png'
    output_eye_catch_path =  _settings.eye_catch_dir + url + '.png'

    resize_and_overlay(base_path, input_path, output_joined_path)

    add_text_to_image(output_joined_path, output_eye_catch_path, text)

    return output_eye_catch_path


# test
if __name__ == '__main__':
    url = 'test'
    input_file = 'data/inputImg/download/800x450.png'
    input_file = 'data/inputImg/download/800x565.png'
    text = "人気商品 ジャンル系TOP10"
    #text = "ジャンル系\n\n人気商品\nTOP10"

    generate_eye_catch_image(url, input_file, text)


