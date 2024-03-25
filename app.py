# -*- coding: UTF-8 -*-
from flask import Flask, request, abort
import DAN,csmapi, random, time, threading
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import requests

app = Flask(__name__)

#---------------------------------IoTtalk functions---------------------------------
def IoTtalk_registration():
    # set IoTtalk Server URL
    IoTtalk_ServerURL = 'http://140.114.77.93:9999'
    
    # set device profile
    DAN.profile['dm_name'] = 'Hamster_Device_1'#'YOUR_DEVICEMODEL_NAME'
    DAN.profile['df_list'] = ['Ham_idf_1','Ham_odf_1']#['YOUR_IDF', 'YOUR_ODF']
    the_mac_addr = 'CD8600D38' + str( random.randint(100,999 ) )  # put here for easy to modify :-)
    # register device profile to IoTtalk Server
    DAN.device_registration_with_retry(IoTtalk_ServerURL, the_mac_addr)

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
IoTtalk_registration()#希望他能被執行...


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
CheckWeather = False
CheckArea = False
hamster_life = 50
hamster_happy = 50
hamster_money = 0
def handle_hamster(life,happy,money):
    global hamster_life, hamster_happy, hamster_money
    hamster_life += life
    hamster_happy += happy
    hamster_money += money
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global CheckWeather, CheckArea
    global hamster_life, hamster_happy, hamster_money
    #get message sent by line bot user
    text = event.message.text
    print(text)
    
    #============================================IMPLEMENT YOUR SCENARIO=====================================#
    weather_url = 'https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0001-001?Authorization=CWA-3A182A5B-492C-4E64-AE3B-463C7CEBB54A'
    weather_data = requests.get(weather_url)#.Session()
    weather_data_json = weather_data.json()
    weather = {}  # 新增一個 weather 字典
    stations = weather_data_json['records']['Station']
    for station in stations:
        name = station['StationName']
        city = station['GeoInfo']['CountyName']
        area = station['GeoInfo']['TownName']
        temp = station['WeatherElement']['AirTemperature']
        humd = station['WeatherElement']['RelativeHumidity']
        wind = station['WeatherElement']['WindSpeed']
        msg = f'{temp} 度，相對濕度 {humd}%，平均風速 {wind}公尺每秒'  # 組合成天氣描述
        if city not in weather:
            weather[city] = {}
        weather[city][name] = msg
    show_cities = ', '.join(weather.keys())

    return_msg = "我收到你的訊息了:D \n跟倉鼠打招呼：你好倉鼠\n查看天氣狀況：查看天氣\n查看天氣地區：查看區域\n餵倉鼠吃瓜子：餵食瓜子\n查看倉鼠狀態：倉鼠狀態"
    city_input = "臺北市"
    area_input = "松山"
    text_strings = text.split()
    if text == "check device name":
        return_msg = f"{DAN.profile['d_name']}"
    if(len(text_strings)==1 and not CheckWeather): 
        if(CheckArea):
            CheckArea = False
            try:
                show_areas = ', '.join(weather[text_strings[0]].keys())
                return_msg = f'{text_strings[0]}的區域有：\n( {show_areas} )\n'
            except KeyError:
                return_msg = f'縣市列表中沒有\"{text_strings[0]}\"請確認後重新輸入'
        elif(text_strings[0]=="你好倉鼠"): return_msg = "你好呀 吱吱吱"
        elif(text_strings[0]=="查看天氣"): 
            return_msg = "請輸入：縣市 區域 例如：臺北市 松山"
            CheckWeather = True
        elif(text_strings[0]=="查看區域"):
            CheckArea = True
            return_msg = f'請輸入下方其中一個縣市\n( {show_cities} )\n'
        elif(text_strings[0]=="餵食瓜子"):
            if(hamster_money >= 10):
                handle_hamster(10,10,-10)
                return_msg = "倉鼠很開心 也變胖了 快樂+10 生命+10 金錢-10"
            else:
                return_msg = "你沒有足夠的金錢買瓜子QQ"
        elif(text_strings[0]=="倉鼠狀態"):
            return_msg = f'倉鼠生命值：{hamster_life}\n倉鼠快樂值：{hamster_happy}\n倉鼠金錢值：{hamster_money}'
            
    elif(CheckWeather):
        CheckWeather = False
        if(len(text_strings)==2):
            
            city_input = text_strings[0]
            area_input = text_strings[1]
            data_tuple = (weather_data_json,city_input, area_input)
            #push and pull data through IoTtalk server
            result = None  # 初始化result
            while result is None:  # 循环等待result返回
                result = IoTtalk_push_and_pull("Ham_idf_1", "Ham_odf_1", data_tuple)
                time.sleep(1)  # 等待一段时间再重新检查
            # result = IoTtalk_push_and_pull("Ham_idf_1", "Ham_odf_1", data_tuple)
            print("owowowowowowo")
            print(result)
            if(result == None): return_msg = 'IoTtalk處理失敗...'+'\n\n倉鼠上班 金錢+10 生命-10 快樂-10'
            else: return_msg = result[0]+'\n\n倉鼠上班 金錢+10 生命-5 快樂-5'
            handle_hamster(-5,-5,10)
            print("owowowowowowo")
        else:
            return_msg = "請輸入正確的縣市區域格式：縣市名[空格]區域名"
    elif(CheckArea):
        CheckArea = False
        return_msg = "請輸入正確的縣市格式：縣市名"
    
    if(hamster_life<=0): 
        return_msg += "倉鼠生命值歸零 鼠掉了\n用魔法讓他復活吧！(∩^o^)⊃━☆ﾟ.*･"
        hamster_life = 50
        hamster_happy = 50
        hamster_money = 0
    elif(hamster_happy<=0):
        return_msg += "倉鼠難過鼠了\n用魔法讓他復活吧！(∩^o^)⊃━☆ﾟ.*･"
        hamster_life = 50
        hamster_happy = 50
        hamster_money = 0
    
    # write some codes here to handle the message 
    # message = TextSendMessage(result[0])
    message = TextSendMessage(return_msg)
    
    #replay message to line bot user
    line_bot_api.reply_message(event.reply_token, message)
    
    #========================================================================================================#
    
#---------------------------------LineBot API functions---------------------------------

import os
if __name__ == "__main__":
         
    # IoTtalk_registration()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

    # weather_url = 'https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0001-001?Authorization=CWA-3A182A5B-492C-4E64-AE3B-463C7CEBB54A'
    
    # weather_data = requests.get(weather_url)#.Session()
    # weather_data_json = weather_data.json()
    # # print(weather_data_json)
    # weather = {}  # 新增一個 weather 字典
    # stations = weather_data_json['records']['Station']

    # for station in stations:
    #     name = station['StationName']
    #     city = station['GeoInfo']['CountyName']
    #     area = station['GeoInfo']['TownName']
    #     temp = station['WeatherElement']['AirTemperature']
    #     humd = station['WeatherElement']['RelativeHumidity']
    #     wind = station['WeatherElement']['WindSpeed']
    #     msg = f'{temp} 度，相對濕度 {humd}%，平均風速 {wind}公尺每秒'  # 組合成天氣描述
    #     if city not in weather:
    #         weather[city] = {}
    #     weather[city][name] = msg

    # show_cities = ', '.join(weather.keys())
    # city_input = input(f'請輸入下方其中一個縣市\n( {show_cities} )\n')
    # asuccess = False
    # while not asuccess:
    #     try:
    #         show_areas = ', '.join(weather[city_input].keys())
    #         asuccess = True
    #     except KeyError:
    #         print(f'列表中沒有\"{city_input}\"請確認後重新輸入')
    #         time.sleep(1)
    #         city_input = input(f'請輸入下方其中一個縣市\n( {show_cities} )\n')
    # area_input = input(f'請輸入{city_input}的其中一個地點\n( {show_areas} )\n')
    # bsuccess = False
    # while not bsuccess:
    #     try:
    #         print(f'{city_input} {area_input}，{weather[city_input][area_input]}。')
    #         bsuccess = True
    #     except KeyError:
    #         print(f'列表中沒有\"{area_input}\"請確認後重新輸入')
    #         time.sleep(1)
    #         area_input = input(f'請輸入{city_input}的其中一個地點\n( {show_areas} )\n')
