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
from dotenv import load_dotenv
from openai import OpenAI
import re
import pendulum
import datetime
import json
import sys
import remind_make
import os

load_dotenv()  # .envファイルから環境変数をロード
client = OpenAI()
# openai.api_key = os.getenv("OPENAI_API_KEY")

# +
# mes = f"次の文から予定が作れますか?できない場合はtodoの情報をjsonで作ってください。できる場合はスケジュールをjsonで作って。todoでもあり、スケジュールでもある場合は、todoとスケジュールの両方のjsonを作ってください。「{tex}」"

# +
# mes = f"以下の文からスケジュールを作れますか?日が特定できない場合は作成できないとすること。時間が特定できない場合は、作成できるとして、朝7時の予定とする。作れる場合は、日時とタイトルをjsonで出力。¥n「{tex}」"
# -
def get_message_content(response):
    """
    レスポンス内のメッセージの内容を取得します。

    Args:
        response (dict): OpenAIからのレスポンス。

    Returns:
        dict: メッセージの内容。関数呼び出しが含まれていない場合はNoneを返します。
    """
    message = response["choices"][0]["message"]
    if message.get("function_call"):
        function_name = message["function_call"]["name"]
        content = json.loads(message["function_call"]["arguments"])
        return content
    else:
        return None


# +
def extract_datetime_from_string(string):
    """
    文字列から日時を抽出する関数

    Args:
        string (str): 日時が含まれる文字列

    Returns:
        datetime.datetime: 抽出された日時オブジェクト。日時が見つからなかった場合はNone。

    Raises:
        なし
    """

    # 正規表現パターンで日時部分を抽出
    # ISO 8601 形式と "YYYY-MM-DD HH:MM:SS+HH:MM" 形式の両方に対応
    match = re.search(r'\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(\+\d{2}:\d{2})?', string)

    if match:
        extracted_datetime_str = match.group(0)
        # タイムゾーン情報があるかどうかでフォーマットを分岐
        if '+' in extracted_datetime_str:
            datetime_obj = datetime.datetime.strptime(extracted_datetime_str, "%Y-%m-%d %H:%M:%S%z")
        else:
            datetime_obj = datetime.datetime.strptime(extracted_datetime_str, "%Y-%m-%dT%H:%M:%S")
        return datetime_obj
    else:
        return None

# 使用例
# input_string = '前のテキスト2023-07-19T15:08:32後のテキスト'
# result = extract_datetime_from_string(input_string)
# if result:
#     print(result)
# else:
#     print("日時が見つかりませんでした。")



# -

def createTodo_with_schedule(mes, now,model="gpt3"):
    """
    与えられたメッセージからスケジュールを作成する関数。

    Args:
        mes (str): ユーザからのメッセージ。
        now (str): 現在の日付と時間。
        model(str):gptのモデルです(デフォルトはgpt3)

    Returns:
        response: OpenAIのChatCompletion.createメソッドからのレスポンス。

    """
    if model == "gpt-4":
        model= "gpt-4"
    else:
        model="gpt-3.5-turbo"
        
    # OpenAIのChatCompletion.createメソッドを使用して応答を生成
    response = client.chat.completions.create(
        model= model,
#         model="gpt-3.5-turbo",
        # ユーザからのメッセージを引数に設定
        messages=[{"role": "user", "content": f"{mes}"}],
        # functionsリストには、モデルに適用する関数の定義を含む
        functions=[
            {
                # ここでは"create_schedule"関数を定義している
                "name": "create_schedule",
                "description": f"Creates a schedule from the given text. now is {now}. Week starts on Sunday.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "DTSTART": {
                            # "DTSTART"はスケジュールの開始日時
                            "type": "string",
                            "description": "The start datetime of the schedule, e.g. 2021-11-03T07:00:00.000Z. If there is no start time, DTSTART is 07:00:00.000Z.",
                        },
                        "DTEND": {
                            # "DTEND"はスケジュールの終了日時
                            "type": "string",
                            "description": "The end datetime of the schedule, e.g. 2021-11-03T07:00:00.000Z. If there is no time stated in the schedule, the time for that schedule is 1 hour",
                        },
                        "duration": {
                            # "duration"はスケジュールの期間（日数）
                            "type": "number",
                            "description": "duration days, e.g. if there is no duration days, duration days = 0",
                        },
                        "title": {
                            # "title"はスケジュールのタイトル
                            "type": "string",
                            "description": "schedule title, e.g. watch the anime",
                        },
                    },
                    "required": ["title", "DTSTART", "DTEND", "duration"],
                },
            },
        ], function_call={"name": "create_schedule"})
    # レスポンスを返す
    return response


def sort_task(mes):
    """
    与えられたメッセージに対してタスクを仕分けする関数

    Args:
        mes (str): ユーザからのメッセージ。

    Returns:
        response: OpenAIのChatCompletion.createメソッドからのレスポンス。

    """
    # OpenAIのChatCompletion.createメソッドを使用して応答を生成
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        # ユーザからのメッセージを引数に設定
        messages=[{"role": "user", "content": f"{mes}"}],
        # functionsリストには、モデルに適用する関数の定義を含む
        functions=[
            {
                # ここでは"confirm_when"関数を定義している
                "name": "sort_task",
                "description": "インプットされたメッセージを指定された形で分類してください",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sort": {
                            # "when"は「明確」か「不明確」の二択で回答
                            "type": "string",
                            "description": "'買物,学校・子育て,その他,の三択で回答",
                        },
                        "kakudo": {
                            # "kakudo"はwhenの結果に対する自信を0から100で出力
                            "type": "number",
                            "description": "sortの結果に対する自信を0から100で出力(自信があれば100)",
                        },
                    },
                    "required": ["sort", "kakudo"],
                },
            },
        ], function_call={"name": "sort_task"})
    # レスポンスを返す
    return response


def confirm_todo_or_schdule(tex,now):
    """
    与えられたメッセージに対して「いつ行動するか」が明確かどうかを判断する関数。

    Args:
        mes (str): ユーザからのメッセージ。

    Returns:
        response: OpenAIのChatCompletion.createメソッドからのレスポンス。

    """
    mes = f"今を{str(now)}とした場合、「{tex}」が示す日時を、{str(now)}と同じ形式でのみ出力する。期間がある場合は開始日時を出力する"
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": mes},
    #         {"role": "user", "content": "会話の内容"}
        ]   
    )
    return response


def update_date_in_datetime_str(sc, new_date):
    """
    文字列形式の日時(timestamp_str)の日付部分を新しい日付(new_date)で更新する関数。

    Parameters:
        timestamp_str (str): 'YYYY-MM-DDTHH:MM:SS.000Z'形式の日時文字列。
        new_date (datetime): 更新したい新しい日付を持つdatetimeオブジェクト。

    Returns:
        str: 更新された日時を持つ文字列 ('YYYY-MM-DDTHH:MM:SS.000Z'形式)。
    """
    # 文字列をdatetimeオブジェクトに変換
    timestamp_str = sc["DTSTART"]
    datetime_obj = datetime.datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%fZ")
    if new_date.date() !=datetime_obj.date():
        print("ちがているので、chatのdateを適用する")
        # 日付を更新
        updated_datetime_obj = datetime_obj.replace(year=new_date.year, month=new_date.month, day=new_date.day)

        # 更新された日時を文字列に変換して返す
        sc["DTSTART"] =updated_datetime_obj.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        sc["DTEND"] = (updated_datetime_obj + datetime.timedelta(days=sc["duration"])).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        
    else:
        print("同じなのでOK")
        
    return sc


def trans_datetime(kekka):
    """
    入力された日付と時間の情報から、ISO 8601形式の日付と時間を含む辞書を作成します。

    Args:
        kekka (tuple): 年、月、日、時間、分、タイトルの情報を含むタプル。

    Returns:
        dict: 'DTSTART'と'title'キーを持つ辞書。'DTSTART'はISO 8601形式の日付と時間、'title'はタイトル。

    """
    # タプルから要素を取り出す
    _, year, month, day, hour, minute, title = kekka
    # datetimeオブジェクトを作成
    dt = datetime.datetime(int(year), int(
        month), int(day), int(hour), int(minute))
    # 時間をISO 8601形式に変換
    iso_format = dt.isoformat() + ".000Z"
    # 'DTSTART'と'title'キーを持つ辞書を返す
    return {'DTSTART': iso_format, 'title': title}

# +
# now = pendulum.now()
# tex = "7月13日から三日間、研修"
# kekka = remind_make.main(tex, now)
# response = confirm_todo_or_schdule(tex,now)
# msg = response["choices"][0]["message"]["content"]

# +

# if not kekka[0] or msg == str(now) or not extract_datetime_from_string(msg):
#     print("これはTODO")
#     res = sort_task(tex)
#     print(get_message_content(res))
#     bunrui = get_message_content(res)["sort"]

# else:
#     if kekka[0]:
#         jibun = trans_datetime(kekka)
#     print(msg)
#     nitiji = extract_datetime_from_string(msg)
#     print(f"これはスケジュール{nitiji}")
#     res = createTodo_with_schedule(tex, now)
#     sc = get_message_content(res)
#     print(sc)
#     sc = update_date_in_datetime_str(sc,nitiji)


# +
# import importlib;importlib.reload(remind_make)
# -

def main(tex):
    now = pendulum.now('Asia/Tokyo')
    kekka = remind_make.main(tex, now)
    response = confirm_todo_or_schdule(tex,now)
    msg = response.choices[0].message.content
    print(msg)
    if msg == str(now) or not extract_datetime_from_string(msg):
        print("これはTODO")
        res = sort_task(tex)
#         print(get_message_content(res))
        bunrui = res.choices[0].message.function_call.arguments
        bunrui = eval(bunrui)
        bunrui = bunrui["sort"]
        return ["todo", tex,bunrui]
    else:
        print(msg)
        nitiji = extract_datetime_from_string(msg)
        print(f"これはスケジュール{nitiji}")
        res = createTodo_with_schedule(tex, now,"gpt3")
        sc = res.choices[0].message.function_call.arguments
        sc = eval(sc)
        print(sc)
        sc = update_date_in_datetime_str(sc,nitiji)
        return ["schedule", sc]


# +
import re
import datetime

def extract_datetime_from_string(string):
    """
    文字列から日時を抽出する関数

    Args:
        string (str): 日時が含まれる文字列

    Returns:
        datetime.datetime: 抽出された日時オブジェクト。日時が見つからなかった場合はNone。

    Raises:
        なし
    """

    # 正規表現パターンで日時部分を抽出
    # ISO 8601 形式と "YYYY-MM-DD HH:MM:SS+HH:MM" 形式の両方に対応
    match = re.search(r'\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(\+\d{2}:\d{2})?', string)

    if match:
        extracted_datetime_str = match.group(0)
        # タイムゾーン情報があるかどうかでフォーマットを分岐
        if '+' in extracted_datetime_str:
            datetime_obj = datetime.datetime.strptime(extracted_datetime_str, "%Y-%m-%d %H:%M:%S%z")
        else:
            datetime_obj = datetime.datetime.strptime(extracted_datetime_str, "%Y-%m-%dT%H:%M:%S")
        return datetime_obj
    else:
        return None

# -





msg = "2024-02-10 00:00:00+09:00"

extract_datetime_from_string(msg)

# +
# mes = "'マラソンの練習"
# out = main(mes)

# +
# if 'ipykernel' in sys.modules:    # Jupyter Notebookから実行された場合のみ実行されるコード
#     print("This code is executed only in Jupyter Notebook.")
#     mes = "11/2プレミアム商品券の交換"
#     out = main(mes)
#     print(out)
# else:
#     print("This notebook was imported!")
#     # ここに、スクリプトがインポートされた際の動作を書くことができます
#     # 例えば、他のスクリプトから呼び出すための関数を定義する等

# +
# out

# +
# if 'ipykernel' in sys.modules:    # Jupyter Notebookから実行された場合のみ実行されるコード
#     print("This code is executed only in Jupyter Notebook.")
#     mes = "懇談会で聞く内容をまとめる"
# #     out = main(mes)
#     out = sort_task(mes)
# else:
#     print("This notebook was imported!")
#     # ここに、スクリプトがインポートされた際の動作を書くことができます
#     # 例えば、他のスクリプトから呼び出すための関数を定義する等
# get_message_content(out)

# +
# def line_message(message):
#     """lineのメッセージを送信します

#     Arguments:
#         message {str} -- メッセージ
#     """
#     url = "https://notify-api.line.me/api/notify"
#     token = 'nEQ8rKyn9fXVfs3JWOf1NZn4kI9ivREKAK7B84va9aD'
#     headers = {"Authorization": "Bearer " + token}
#     payload = {"message":  message}
#     r = requests.post(url, headers=headers, params=payload)

# +
# if out[0] == "schedule":
#     line_mes = f'"{mes}"を処理しました\n- 開始:{out[1]["DTSTART"].replace(":00.000Z","")}\n- 終了:{out[1]["DTEND"].replace(":00.000Z","")}\n- 日数{out[1]["duration"]}\n- 名称:{out[1]["title"]}'
# if out[0] == "todo":
#     line_mes = f'"{mes}"を処理しました\n- 名称:{out[0]}'
# if out[0] == "unknown":
#     line_mes = f'"{mes}"の処理が失敗しました'
# -

# # glideからのデータを使ってみる

# +
# import sys;sys.path.append("../mylib");import gss

# df = gss.create_df()

# df

# na_rows = df[df["開始日時"].isna()]

# out_li = []
# for i in list(na_rows["名称"]):
#     print(i)
#     out = sort_task(i)
#     out = out_li.append(out)

# a = []
# for p in out_li:
#     print(get_message_content(p)['sort'])
#     a.append(get_message_content(p)['sort'])

# +
# na_rows["結果"] = a

# na_rows[[ '名称', '結果']]

# na_rows.loc[na_rows["結果"] == "その他", "タスク"] = True
# na_rows.loc[na_rows["結果"] == "買物", "買物"] = True

# na_rows

# df.update(na_rows[["タスク","買物"]])

# df

# gss.upload(df)

# import undetected_chromedriver as uc
# driver = uc.Chrome()
# driver.get('https://chat.openai.com/')
# -


