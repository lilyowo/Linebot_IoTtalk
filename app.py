# -*- coding: UTF-8 -*-
from flask import Flask, request, abort
import DAN,csmapi, random, time, threading
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *

app = Flask(__name__)

#---------------------------------IoTtalk functions---------------------------------
def IoTtalk_registration():
    # set IoTtalk Server URL
    IoTtalk_ServerURL = 'YOUR_IOTtalk_URL'
    
    # set device profile
    DAN.profile['dm_name'] = 'YOUR_DEVICEMODEL_NAME'
    DAN.profile['df_list'] = ['YOUR_IDF', 'YOUR_ODF']
    
    # register device profile to IoTtalk Server
    DAN.device_registration_with_retry(IoTtalk_ServerURL, None)

def IoTtalk_push_and_pull(IDF, ODF, data):
    DAN.push(IDF, data)
    time.sleep(1.5)
    result = DAN.pull(ODF)
    return result
#---------------------------------IoTtalk functions---------------------------------
    
#---------------------------------LineBot API functions---------------------------------
# Channel Access Token
line_bot_api = LineBotApi('DQNVcGeXcJhuGxgjSbLoR4k6ldddBpYYpRXlrcxpKWgY/YK4v92shUvhx0cW1L0ecbqn3DcrPLduDQcRblvO/Z7ZG+hHjX8jUazqQacxwL0HdQ7GDQFgxrUfPAkTs5YlvIKjMC7mCV7Xgy0PPEmypwdB04t89/1O/w1cDnyilFU=')
# Channel Secret
handler = WebhookHandler('bc3cdd4fe84c0fa1cc4e53a6c08c7e54')

# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    
    #get message sent by line bot user
    text = event.message.text
    print(text)
    
    #============================================IMPLEMENT YOUR SCENARIO=====================================#

    #push and pull data through IoTtalk server
    result = IoTtalk_push_and_pull("YOUR_IDF", "YOUR_ODF", text)
    print(result)
    
    # write some codes here to handle the message 
    message = TextSendMessage(result[0])
    
    #replay message to line bot user
    line_bot_api.reply_message(event.reply_token, message)
    
    #========================================================================================================#
    
#---------------------------------LineBot API functions---------------------------------

import os
if __name__ == "__main__":
         
    IoTtalk_registration()
     
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    
