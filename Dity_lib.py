# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.13.7
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# +
import json
import re
# from datetime import datetime
import pendulum
import json
from dify_client import ChatClient
from dotenv import load_dotenv
import os
load_dotenv()  # .envファイルから環境変数をロード
Dify_api_key = os.getenv('Dify_api_key')

def contains_schedule(text):
    """
    テキストに「[schedule,」が含まれているかを確認します。

    Args:
        text (str): 入力テキスト

    Returns:
        bool: 「[schedule,」が含まれている場合はTrue、含まれていない場合はFalse
    """
    # 正規表現パターンを定義して"schedule"が含まれているかを確認
    pattern = re.compile(r'\[schedule,')
    match = pattern.search(text)
    return match is not None

def convert_text_to_output(text):
    """
    テキストを解析して、指定された出力フォーマットに変換します。

    Args:
        text (str): 入力テキスト

    Returns:
        list: 指定された出力フォーマット ['schedule', { 'DTSTART': ..., 'DTEND': ..., 'duration': ..., 'title': ... }]
    """
    # 正規表現パターンを定義して必要な部分を抽出
    pattern = re.compile(
        r'カテゴリ:\w+\[schedule,\{\s*'
        r'"date":\s*"(?P<date>\d{2}/\d{2})",\s*'
        r'"start_time":\s*"(?P<start_time>\d{2}:\d{2}:\d{2})",\s*'
        r'"end_time":\s*"(?P<end_time>\d{2}:\d{2}:\d{2})",\s*'
        r'"duration":\s*(?P<duration>\d+),\s*'
        r'"event":\s*"(?P<event>.*?)"\s*\}\]'
    )

    match = pattern.search(text)
    if not match:
        raise ValueError("Invalid input format")

    # マッチしたグループを辞書として取得
    schedule_json = match.groupdict()

    # 日付を整形する
    date_str = schedule_json['date']
    month, day = date_str.split('/')
    formatted_date = f"2024-{month.zfill(2)}-{day.zfill(2)}"

    # 出力フォーマットの変換
    output = ['schedule', {
        'DTSTART': f"{formatted_date}T{schedule_json['start_time']}.000Z",
        'DTEND': f"{formatted_date}T{schedule_json['end_time']}.000Z",
        'duration': int(schedule_json['duration']),
        'title': schedule_json['event']
    }]
    
    return output

def convert_text_to_todo_output(text):
    """
    テキストを解析して、指定された出力フォーマットに変換します。

    Args:
        text (str): 入力テキスト

    Returns:
        list: 指定された出力フォーマット ['todo', '歯ブラシ', '買物']
    """
    # 正規表現パターンを定義して必要な部分を抽出
    pattern = re.compile(r'カテゴリ:\w+\[todo,([^,]+),([^,]+)\]')
    
    match = pattern.search(text)
    if not match:
        raise ValueError("Invalid input format")
    
    # マッチしたグループを取得
    todo_item, category = match.groups()
    
    # 出力フォーマットの変換
    output = ['todo', todo_item, category]
    
    return output

# # テストデータ
# input_text_schedule = 'カテゴリ:学校[schedule,{\n  "date": "05/20",\n  "start_time": "07:00:00",\n  "end_time": "20:00:00",\n  "duration": 3,\n  "event": "明日から3日間 修学旅行"\n}]'
# input_text_todo = 'カテゴリ:買物[todo,歯ブラシ,買物]'

# # "schedule"が含まれているか確認
# if contains_schedule(input_text_schedule):
#     print("scheduleが含まれています")
#     format_out_schedule = convert_text_to_output(input_text_schedule)
#     print(format_out_schedule)
# else:
#     print("scheduleが含まれていません")

# # "todo"のテキストを変換
# format_out_todo = convert_text_to_todo_output(input_text_todo)
# print(format_out_todo)


# +

def dift_sc(now, input_tex, api_key):
    """
    ChatClientを使用して、現在の日時と入力テキストに基づいてチャットメッセージを作成し、応答を取得します。

    Args:
        now (datetime): 現在の日時
        input_tex (str): 入力テキスト
        api_key (str): ChatClientのAPIキー

    Returns:
        str: チャット応答のメッセージ
    """
    # ChatClientを初期化
    chat_client = ChatClient(api_key)

    # 現在の日時を文字列に変換
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    # ChatClientを使用してチャットメッセージを作成
    chat_response = chat_client.create_chat_message(inputs={"now": now_str}, query=input_tex, user="user_id", response_mode="blocking")
    chat_response.raise_for_status()

    # 応答メッセージを処理
    for line in chat_response.iter_lines(decode_unicode=True):
        line = line.split('data:', 1)[-1]
        if line.strip():
            line = json.loads(line.strip())
            
    return line.get('answer')



# +
import pendulum

def main(input_tex):
    """
    入力テキストを処理して、スケジュールまたはtodo形式の出力を返します。

    Args:
        input_tex (str): 処理する入力テキスト

    Returns:
        list: スケジュール形式またはtodo形式の出力フォーマット
    """
    # 現在の日時を東京時間で取得
    now = pendulum.now('Asia/Tokyo')
    
    # ChatClientを使用して応答を取得
    out = dift_sc(now, input_tex, Dify_api_key)
    
    # 応答がスケジュールかtodoかを判定
    if contains_schedule(out):
        print("スケジュール")
        format_out = convert_text_to_output(out)
    else:
        print("todo")
        format_out = convert_text_to_todo_output(out)

    return format_out


# +
# # test
# input_tex = "6/9 四十九日の法事"
# main(input_tex)
# -


