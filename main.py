import random
from time import localtime
from datetime import datetime, date
import sys
import os
import json
import requests

# 获取随机颜色
def get_color():
    get_colors = lambda n: [f"#{random.randint(0, 0xFFFFFF):06x}" for _ in range(n)]
    color_list = get_colors(100)
    return random.choice(color_list)

# 获取access_token
def get_access_token(config):
    app_id = config["app_id"]
    app_secret = config["app_secret"]
    post_url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
    try:
        response = requests.get(post_url)
        response.raise_for_status()
        return response.json()['access_token']
    except requests.exceptions.RequestException as e:
        print(f"获取access_token失败：{e}")
        print("请检查app_id和app_secret是否正确")
        os.system("pause")
        sys.exit(1)

# 获取天气信息
def get_weather(region, config):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    key = config["weather_key"]
    region_url = f"https://geoapi.qweather.com/v2/city/lookup?location={region}&key={key}"
    
    try:
        response = requests.get(region_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        if data["code"] == "404":
            print("推送消息失败，请检查地区名是否有误！")
            os.system("pause")
            sys.exit(1)
        elif data["code"] == "401":
            print("推送消息失败，请检查和风天气key是否正确！")
            os.system("pause")
            sys.exit(1)
            
        location_id = data["location"][0]["id"]
        weather_url = f"https://devapi.qweather.com/v7/weather/now?location={location_id}&key={key}"
        response = requests.get(weather_url, headers=headers)
        response.raise_for_status()
        
        weather_data = response.json()
        weather = weather_data["now"]["text"]
        temp = f"{weather_data['now']['temp']}℃"
        wind_dir = weather_data["now"]["windDir"]
        return weather, temp, wind_dir
        
    except requests.exceptions.RequestException as e:
        print(f"获取天气信息失败：{e}")
        os.system("pause")
        sys.exit(1)

# 获取每日一句情话
def fetch_aiqingyl():
    url = "https://api.1314.cool/words/api.php"
    params = {"return": "json"}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data.get("code") == "200":
            return data.get("word", "未能获取中文情话"), "未能获取英文情话"
        else:
            return f"API 返回错误：{data.get('msg')}", ""
            
    except requests.exceptions.RequestException as e:
        return f"请求发生错误：{e}", ""
    except Exception as e:
        return f"请求发生错误：{e}", ""

# 获取生日信息
def get_birthday(birthday, year, today):
    try:
        if birthday.startswith("r"):
            # 处理农历生日
            from zhdate import ZhDate  # 需要安装zhdate库
            
            r_month = int(birthday.split("-")[1])
            r_day = int(birthday.split("-")[2])
            birthday_date = ZhDate(year, r_month, r_day).to_datetime().date()
        else:
            # 处理公历生日
            b_month = int(birthday.split("-")[1])
            b_day = int(birthday.split("-")[2])
            birthday_date = date(year, b_month, b_day)
            
        if today > birthday_date:
            next_birthday = birthday_date.replace(year=year + 1)
            days_left = (next_birthday - today).days
        elif today == birthday_date:
            days_left = 0
        else:
            days_left = (birthday_date - today).days
            
        return days_left
        
    except TypeError:
        print("请检查生日的日子是否在今年存在")
        os.system("pause")
        sys.exit(1)

# 发送消息
def send_message(to_user, access_token, region_name, weather, temp, wind_dir, config):
    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
    week_list = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]
    
    year = localtime().tm_year
    month = localtime().tm_mon
    day = localtime().tm_mday
    today = date(year, month, day)
    week = week_list[today.isoweekday() % 7]

    # 获取情话
    note_ch, note_en = fetch_aiqingyl()

    # 计算在一起的天数
    love_date = config["love_date"]
    love_year, love_month, love_day = map(int, love_date.split("-"))
    love_date_obj = date(love_year, love_month, love_day)
    love_days = (today - love_date_obj).days

    # 获取生日信息
    birthday1 = get_birthday(config["birthday1"]["birthday"], year, today)
    birthday2 = get_birthday(config["birthday2"]["birthday"], year, today)

    # 设置推送模板
    data = {
        "touser": to_user,
        "template_id": config["template_id"],
        "url": "http://weixin.qq.com/download",
        "topcolor": "#FF0000",
        "data": {
            "date": {
                "value": f"{today} {week}",
                "color": get_color()
            },
            "region": {
                "value": region_name,
                "color": get_color()
            },
            "weather": {
                "value": weather,
                "color": get_color()
            },
            "temp": {
                "value": temp,
                "color": get_color()
            },
            "wind_dir": {
                "value": wind_dir,
                "color": get_color()
            },
            "love_day": {
                "value": f"恋爱第 {love_days} 天",
                "color": get_color()
            },
            "note_en": {
                "value": note_ch,  # 由于新API只返回中文情话，此处直接使用中文情话
                "color": get_color()
            },
            "birthday1": {
                "value": f"距离{config['birthday1']['name']}的生日还有{birthday1}天",
                "color": get_color()
            },
            "birthday2": {
                "value": f"距离{config['birthday2']['name']}的生日还有{birthday2}天",
                "color": get_color()
            }
        }
    }

    try:
        response = requests.post(url, json=data, headers={
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
        })
        response.raise_for_status()
        result = response.json()
        if result["errcode"] == 0:
            print("推送消息成功")
        else:
            print(f"推送消息失败，错误码：{result['errcode']}，错误信息：{result.get('errmsg', '未知错误')}")
    except requests.exceptions.RequestException as e:
        print(f"发送消息失败：{e}")

if __name__ == "__main__":
    try:
        # 读取配置文件
        with open("config.json", encoding="utf-8") as f:
            config = json.load(f)
    except FileNotFoundError:
        print("推送消息失败，请检查config.json文件是否与程序位于同一路径")
        os.system("pause")
        sys.exit(1)
    except json.JSONDecodeError:
        print("推送消息失败，请检查配置文件格式是否正确")
        os.system("pause")
        sys.exit(1)

    # 获取AccessToken
    access_token = get_access_token(config)

    # 配置信息
    users = config["user"]
    region = config["region"]

    # 获取天气信息
    weather, temp, wind_dir = get_weather(region, config)

    # 发送消息
    for user in users:
        send_message(user, access_token, region, weather, temp, wind_dir, config)

    input("按回车键退出...")
