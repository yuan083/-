import random
from time import localtime
from requests import get, post
import json
from datetime import datetime, date
import sys
import os
from zhdate import ZhDate  # 增加了导入

# 获取随机颜色
def get_color():
    get_colors = lambda n: list(map(lambda i: "#" + "%06x" % random.randint(0, 0xFFFFFF), range(n)))
    color_list = get_colors(100)
    return random.choice(color_list)

# 获取access_token
def get_access_token(config):  # 增加了config参数
    app_id = config["app_id"]
    app_secret = config["app_secret"]
    post_url = ("https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={}&secret={}").format(app_id, app_secret)
    try:
        access_token = get(post_url).json()['access_token']
    except KeyError:
        print("获取access_token失败，请检查app_id和app_secret是否正确")
        os.system("pause")
        sys.exit(1)
    return access_token

# 获取天气信息
def get_weather(region, config):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    key = config["weather_key"]
    region_url = f"https://geoapi.qweather.com/v2/city/lookup?location={region}&key={key}"
    response = get(region_url, headers=headers).json()
    if response["code"] == "404":
        print("推送消息失败，请检查地区名是否有误！")
        os.system("pause")
        sys.exit(1)
    elif response["code"] == "401":
        print("推送消息失败，请检查和风天气key是否正确！")
        os.system("pause")
        sys.exit(1)
    else:
        location_id = response["location"][0]["id"]
    weather_url = f"https://devapi.qweather.com/v7/weather/now?location={location_id}&key={key}"
    response = get(weather_url, headers=headers).json()
    weather = response["now"]["text"]
    temp = response["now"]["temp"] + u"\N{DEGREE SIGN}" + "C"
    wind_dir = response["now"]["windDir"]
    return weather, temp, wind_dir

# 获取生日信息
def get_birthday(birthday, year, today):
    if birthday.startswith("r"):
        r_mouth = int(birthday.split("-")[1])
        r_day = int(birthday.split("-")[2])
        try:
            birthday_date = ZhDate(year, r_mouth, r_day).to_datetime().date()
        except TypeError:
            print("请检查生日的日子是否在今年存在")
            os.system("pause")
            sys.exit(1)
        birthday_month = birthday_date.month
        birthday_day = birthday_date.day
        year_date = date(year, birthday_month, birthday_day)
    else:
        birthday_month = int(birthday.split("-")[1])
        birthday_day = int(birthday.split("-")[2])
        year_date = date(year, birthday_month, birthday_day)
    if today > year_date:
        if birthday.startswith("r"):
            try:
                birth_date = ZhDate(year + 1, r_mouth, r_day).to_datetime().date()
            except TypeError:
                print("请检查生日的日子是否在明年存在")
                os.system("pause")
                sys.exit(1)
        else:
            birth_date = date(year + 1, birthday_month, birthday_day)
        birth_day = str(birth_date - today).split(" ")[0]
    elif today == year_date:
        birth_day = 0
    else:
        birth_date = year_date
        birth_day = str(birth_date - today).split(" ")[0]
    return birth_day

# 获取每日一句情话
apikey = "459603bd8718ec8e2ebd4aabd7a4bde8"
def get_love_words(apikey):
    """获取土味情话"""
    url = f"https://apis.tianapi.com/saylove/index?key={apikey}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data['result']['content']
    else:
        return "未能获取情话"

# 发送消息
def send_message(to_user, access_token, region_name, weather, temp, wind_dir, config):
    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
    year = date.today().year
    month = date.today().month
    day = date.today().day
    today = date(year, month, day)
    week_list = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]
    week = week_list[today.isoweekday() % 7]

    # 获取情话
    love_words = get_love_words(apikey)

    # 获取在一起的日子
    try:
        love_date = date(*map(int, config["love_date"].split("-")))
        love_days = (today - love_date).days
    except:
        love_days = 0
        print("请检查love_date格式是否正确")

    # 获取生日信息
    birthdays = config.get("birthdays", {})
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
                "value": f"在一起的第{love_days}天",
                "color": get_color()
            },
            "note": {  # 将英文和中文情话合并为一个字段
                "value": love_words,
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

    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }

    response = post(url, headers=headers, json=data).json()
    if response.get("errcode"):
        print(f"推送消息失败，错误码：{response['errcode']}，错误信息：{response.get('errmsg', '未知错误')}")
    else:
        print("推送消息成功")

if __name__ == "__main__":
    try:
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

    # 获取accessToken
    accessToken = get_access_token(config)

    # 传入地区获取天气信息
    region = config["region"]
    weather, temp, wind_dir = get_weather(region, config)

    # 公众号推送消息
    users = config.get("user", [])
    for user in users:
        send_message(user, accessToken, region, weather, temp, wind_dir, config)
