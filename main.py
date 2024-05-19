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
from fastapi import FastAPI
from pydantic import BaseModel
# import sys

# # アップロードされたスクリプトのパスをPythonの検索パスに追加
# sys.path.append('/mnt/data/')

# chat_gpt_api.pyからmain関数をインポート
# from chat_gpt_api import main as call_main_function
import Dity_lib

app = FastAPI()

class Item(BaseModel):
    text: str

@app.post("/process/")
async def process_input(item: Item):
    # アップロードされたスクリプトのmain関数を呼び出し、結果を取得
    # result = call_main_function(item.text)
    result = Dity_lib.main("明日は塾のテスト")
    # result = "sss"
    # 処理結果をクライアントに返す
    return {"result": result}


