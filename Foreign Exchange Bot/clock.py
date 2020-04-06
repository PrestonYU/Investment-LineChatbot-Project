import os

import requests
import pandas as pd
from bs4 import BeautifulSoup
# 引入套件 flask
from flask import Flask, request, abort
import lxml 
import twder

from linebot import (
    LineBotApi, WebhookHandler
)
# 引入 linebot 異常處理
from linebot.exceptions import (
    InvalidSignatureError
)
# 引入 linebot 訊息元件
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, StickerSendMessage, VideoSendMessage
)


app = Flask(__name__)

headers = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36'
}


# LINE_CHANNEL_SECRET 和 LINE_CHANNEL_ACCESS_TOKEN 類似聊天機器人的密碼，記得不要放到 repl.it 或是和他人分享
# 從環境變數取出設定參數
line_bot_api = LineBotApi('')
handler = WebhookHandler('')

# 儲存基金代碼對應
fund_map_dict = {}

def init_fund_list():
    resp = requests.get('https://www.sitca.org.tw/ROC/Industry/IN2421.aspx?txtMonth=02&txtYear=2020', headers=headers)
    soup = BeautifulSoup(resp.text, 'html.parser')
    # 選擇基金列表 table
    table_content = soup.select('#ctl00_ContentPlaceHolder1_TableClassList')[0]
    # 選擇基金名稱連結
    fund_links = table_content.select('a')

    for fund_link in fund_links:
        # 去除沒有基金名稱的連結
        if fund_link.text:
            # 取出基金名稱
            fund_name = fund_link.text
            fund_group_id = fund_link['href'].split('txtGROUPID=')[1]
            fund_map_dict[fund_name] = fund_group_id

def fetch_fund_rule_items(year, month, group_id):
    # 網路爬蟲抓取資料，使用參數 year, month, group_id 抓取不同類型資料
    fetch_url = f'https://www.sitca.org.tw/ROC/Industry/IN2422.aspx?txtYEAR={year}&txtMONTH={month}&txtGROUPID={group_id}'
    print(year, month, group_id, fetch_url)
    resp = requests.get(fetch_url, headers=headers)   
    soup = BeautifulSoup(resp.text, 'html.parser')

    # 觀察發現透過 id ctl00_ContentPlaceHolder1_TableClassList 可以取出 Morningstar table 資料。取出第一筆
    table_content = soup.select('#ctl00_ContentPlaceHolder1_TableClassList')[0]

    # 將 BeautifulSoup 解析的物件美化後交給 pandas 讀取 table，注意編碼為 UTF-8。取出第二筆
    fund_df = pd.read_html(table_content.prettify(), encoding='utf-8')[1]

    # 資料前處理，將不必要的列
    fund_df = fund_df.drop(index=[0])
    # 設置第一列為標頭
    fund_df.columns = fund_df.iloc[0]
    # 去除不必要列
    fund_df = fund_df.drop(index=[1])
    # 整理完後新設定 index
    fund_df.reset_index(drop=True, inplace=True)
    # NaN -> 0
    fund_df = fund_df.fillna(value=0)

    # 轉換資料型別從 object 轉為 float
    fund_df['一個月'] = fund_df['一個月'].astype(float)
    fund_df['三個月'] = fund_df['三個月'].astype(float)
    fund_df['六個月'] = fund_df['六個月'].astype(float)
    fund_df['一年'] = fund_df['一年'].astype(float)
    fund_df['二年'] = fund_df['二年'].astype(float)
    fund_df['三年'] = fund_df['三年'].astype(float)
    fund_df['五年'] = fund_df['五年'].astype(float)
    fund_df['自今年以來'] = fund_df['自今年以來'].astype(float)

    # 316 法則篩選標準，nlargest 為取出前面 x 筆資料
    rule_3_df = fund_df.sort_values(by=['三年'], ascending=['True']).nlargest(int(len(fund_df.index) / 2), '三年')
    rule_1_df = rule_3_df.sort_values(by=['一年'], ascending=['True']).nlargest(int(len(rule_3_df.index) / 2), '一年')
    rule_6_df = rule_1_df.sort_values(by=['六個月'], ascending=['True']).nlargest(int(len(rule_1_df.index) / 2), '六個月')
    fund_rule_items_str = ''

    # 組成回傳篩選結果字串
    if not rule_6_df.empty:
        for _, row in rule_6_df.iterrows():
            fund_rule_items_str += f'{row["基金名稱"]}, {row["三年"]}, {row["一年"]}, {row["六個月"]}\n'

    return fund_rule_items_str

def all_currents():
    currents = twder.now_all()
    show_current = ''
    for current in currents:
        show_current += '[' + current +'] '
        for i in range(1,5):
            show_current += currents[current][i]+' , '        
        show_current += currents[current][0]+'\n'

    return show_current

# 此為歡迎畫面處理函式，當網址後面是 / 時由它處理
@app.route("/", methods=['GET'])
def hello():
    return 'hello heroku'

# 此為 Webhook callback endpoint 處理函式，當網址後面是 /callback 時由它處理
@app.route("/callback", methods=['POST'])
def callback():
    # 取得網路請求的標頭 X-Line-Signature 內容，確認請求是從 LINE Server 送來的
    signature = request.headers['X-Line-Signature']

    # 將請求內容取出
    body = request.get_data(as_text=True)

    # handle webhook body（轉送給負責處理的 handler，ex. handle_message）
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

# decorator 負責判斷 event 為 MessageEvent 實例，event.message 為 TextMessage 實例。所以此為處理 TextMessage 的 handler
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # get who send profile
    profile = line_bot_api.get_profile(event.source.user_id)
    # 決定要回傳什麼 Component 到 Channel，這邊使用 TextSendMessage
    # event.message.text 為使用者的輸入，把它原封不動回傳回去
    user_message = event.message.text
    reply_message = TextSendMessage(text=profile.display_name+' , '+event.message.text)
    if user_message == '@基金列表' or user_message == '基金列表':
         # 將 dict 儲存的基金列表組成回傳字串
        init_fund_list()
        fund_list_str = ''
        for fund_name in fund_map_dict:
            fund_list_str += fund_name + '\n'
        reply_message = TextSendMessage(text=fund_list_str)

    elif user_message in fund_map_dict:
        group_id = fund_map_dict[user_message]
        print('開始篩選...')
        fund_rule_items_str = fetch_fund_rule_items('2020', '02', group_id)
        reply_message = TextSendMessage(text=fund_rule_items_str) 

    elif user_message == '@查詢所有匯率' or user_message == '查詢所有匯率':
        current_list_str = all_currents()
        reply_message = TextSendMessage(text=current_list_str)        

    line_bot_api.reply_message(
        event.reply_token,
        reply_message)

# __name__ 為內建變數，若程式不是被當作模組引入則為 __main__
if __name__ == "__main__":
    # 此處不使用 Flask 內建伺服器，所以不設定 IP 和 Port    
    app.run()
