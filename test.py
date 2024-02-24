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
import requests
import json

def call_web_api(input_text):
    api_url = "http://127.0.0.1:8000/process/"  # 修正されたAPIエンドポイント
    payload = {
        "text": input_text  # inputTextの内容を設定
    }
    
    # リクエストのヘッダーに'Content-Type'を設定
    headers = {
        'Content-Type': 'application/json'
    }

    try:
        # POSTリクエストを送信
        response = requests.post(api_url, data=json.dumps(payload), headers=headers)
        print("Response Status Code:", response.status_code)
        print("Response Text:", response.text)  # レスポンスの内容を出力
    except Exception as error:
        print("Error during the API call:", error)

# 例: 'Hello World'というテキストをAPIに送信
call_web_api("明日はマラソン")

# -


