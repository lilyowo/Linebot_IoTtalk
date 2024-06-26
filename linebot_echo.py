# -*- coding: UTF-8 -*-
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *

app = Flask(__name__)

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

	app.logger.info("Request bodyAAABBBCCCDDD: " + body)
	# handle webhook body
	try:
		handler.handle(body, signature)
	except InvalidSignatureError:
		abort(400)
	return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
	message = TextSendMessage(text=event.message.text)
	line_bot_api.reply_message(event.reply_token, message)

import os
if __name__ == "__main__":
	port = int(os.environ.get('PORT', 5000))
	app.run(host='0.0.0.0', port=port)