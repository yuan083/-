import random
from time import localtime
from requests import get, post
import requests
from datetime import datetime, date, timedelta
import time
import sys
import os

# 等待至北京时间 7:10
# 等待至指定时间（如7:10）
def wait_until(hour, minute):
    now = datetime.now()
    target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    # 如果目标时间已经过去了（当天的7:10已经过了），则设置为第二天的7:10
    # 如果目标时间已经过去，则设置为第二天
    if now > target_time:
        target_time += timedelta(days=1)
    wait_time = (target_time - now).total_seconds()
    print(f"等待时间: {int(wait_time // 3600)}小时{int((wait_time % 3600) // 60)}分钟")
    print(f"等待时间: {int(wait_time // 3600)}小时 {int((wait_time % 3600) // 60)}分钟")
    time.sleep(wait_time)

# 获取随机颜色
def get_color():
    get_colors = lambda n: list(map(lambda i: "#" + "%06x" % random.randint(0, 0xFFFFFF), range(n)))
    color_list = get_colors(100)
    return random.choice(color_list)

# 获取access_token
def get_access_token():
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
def get_weather(region):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    key = config["weather_key"]
    region_url = "https://geoapi.qweather.com/v2/city/lookup?location={}&key={}".format(region, key)
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
    weather_url = "https://devapi.qweather.com/v7/weather/now?location={}&key={}".format(location_id, key)
    response = get(weather_url, headers=headers).json()
    weather = response["now"]["text"]
    temp = response["now"]["temp"] + u"\N{DEGREE SIGN}" + "C"
    wind_dir = response["now"]["windDir"]
    return weather, temp, wind_dir

# 获取每日一句情话
def fetch_aiqingyl():
    url = "https://api.yaohud.cn/api/randtext/aiqingyl"
    params = {
        "key": "6WpLD9pftbqduArcYRJ"
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 200:
                note_ch = data.get("data")[0] if data.get("data") else "未能获取中文情话"
                note_en = data.get("data")[1] if len(data.get("data", [])) > 1 else "未能获取英文情话"
                return note_ch, note_en
            else:
                return f"API 返回错误：{data.get('msg')}", ""
        else:
            return f"请求失败，状态码：{response.status_code}", ""
    except Exception as e:
        return f"请求发生错误：{e}", ""

# 获取生日信息
# 获取生日信息（支持阳历和农历，农历格式以 'r' 开头）
def get_birthday(birthday, year, today):
    birthday_year = birthday.split("-")[0]
    if birthday_year[0] == "r":
        r_mouth = int(birthday.split("-")[1])
        r_day = int(birthday.split("-")[2])
        try:
            birthday = ZhDate(year, r_mouth, r_day).to_datetime().date()
        except TypeError:
            print("请检查生日的日子是否在今年存在")
            os.system("pause")
            sys.exit(1)
        birthday_month = birthday.month
        birthday_day = birthday.day
        year_date = date(year, birthday_month, birthday_day)
    else:
        birthday_month = int(birthday.split("-")[1])
        birthday_day = int(birthday.split("-")[2])
        year_date = date(year, birthday_month, birthday_day)
    if today > year_date:
        if birthday_year[0] == "r":
            r_last_birthday = ZhDate((year + 1), r_mouth, r_day).to_datetime().date()
            birth_date = date((year + 1), r_last_birthday.month, r_last_birthday.day)
        else:
            birth_date = date((year + 1), birthday_month, birthday_day)
        birth_day = str(birth_date.__sub__(today)).split(" ")[0]
    elif today == year_date:
        birth_day = 0
    else:
        birth_date = year_date
        birth_day = str(birth_date.__sub__(today)).split(" ")[0]
    return birth_day

# 发送消息
def send_message(to_user, access_token, region_name, weather, temp, wind_dir):
    url = "https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={}".format(access_token)
    week_list = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]
    year = localtime().tm_year
    month = localtime().tm_mon
    day = localtime().tm_mday
    today = datetime.date(datetime(year=year, month=month, day=day))
    week = week_list[today.isoweekday() % 7]
    
    # 获取情话
    note_ch, note_en = fetch_aiqingyl()
    
    # 获取在一起的日子
    love_year = int(config["love_date"].split("-")[0])
    love_month = int(config["love_date"].split("-")[1])
    love_day = int(config["love_date"].split("-")[2])
    love_date = date(love_year, love_month, love_day)
    love_days = str(today.__sub__(love_date)).split(" ")[0]
    birthdays = {}
    for k, v in config.items():
        if k[0:5] == "birth":
            birthdays[k] = v
    
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
                "value": "{} {}".format(today, week),
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
                "value": love_days,
                "color": get_color()
            },
            "note_en": {
                "value": note_en,
                "color": get_color()
            },
            "birthday1": {
                "value": "距离{}的生日还有{}天".format(config["birthday1"]["name"], birthday1),
                "color": get_color()
            },
            "birthday2": {
                "value": "距离{}的生日还有{}天".format(config["birthday2"]["name"], birthday2),
                "color": get_color()
            }
        }
    }
    
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    
    response = post(url, headers=headers, json=data).json()
    if response["errcode"] == 40037:
        print("推送消息失败，请检查模板id是否正确")
    elif response["errcode"] == 40036:
        print("推送消息失败，请检查模板id是否为空")
    elif response["errcode"] == 40003:
        print("推送消息失败，请检查微信号是否正确")
    elif response["errcode"] == 0:
        print("推送消息成功")
    else:
        print(response)

if __name__ == "__main__":
    # 加载配置文件
    # 配置数据：测试模式下直接运行，正式发布时设置 test_mode 为 False
    config = {
        "test_mode": True,          # 测试模式：True 不等待定时；False 则等待到指定时间
        "app_id": "your_app_id",
        "app_secret": "your_app_secret",
        "template_id": "your_template_id",
        "weather_key": "your_weather_key",
        "love_date": "2022-08-10",
        "birthday1": {"name": "Alice", "birthday": "2000-06-01"},
        "birthday2": {"name": "Bob", "birthday": "2000-07-01"},
    }
    
    # 收件人的 openid
    to_user = "receiver_openid"

    # 等待至北京时间7:10
    wait_until(7, 10)
    # 获取access_token
    # 根据 test_mode 判断是否等待到指定时间（如 7:10）
    if not config["test_mode"]:
        wait_until(7, 10)
    else:
        print("测试模式：立即运行，不等待指定时间。")
    
    access_token = get_access_token()
    # 获取天气信息
    region_name = "Beijing"
    weather, temp, wind_dir = get_weather(region_name)
    # 发送消息
    send_message(to_user, access_token, region_name, weather, temp, wind_dir)
