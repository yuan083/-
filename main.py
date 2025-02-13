import random
import datetime
import requests
from time import localtime

# 获取随机颜色
def get_color():
    return random.choice(config["random_colors"])

# 获取生日信息
def get_birthday(birthday, today):
    birthday_year = birthday.split("-")[0]
    if birthday_year[0] == "r":
        r_mouth = int(birthday.split("-")[1])
        r_day = int(birthday.split("-")[2])
        try:
            birthday = ZhDate(today.year, r_mouth, r_day).to_datetime().date()
        except TypeError:
            print("请检查生日的日子是否在今年存在")
            return 0
        return (birthday - today).days
    else:
        birthday_month = int(birthday.split("-")[1])
        birthday_day = int(birthday.split("-")[2])
        birth_date = datetime.date(today.year, birthday_month, birthday_day)
        return (birth_date - today).days

# 获取每日金句
def fetch_aiqingyl():
    url = "https://api.yaohud.cn/api/randtext/aiqingyl"
    params = {"key": "6WpLD9pftbqduArcYRJ"}
    
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

# 发送消息
def send_message(to_user, access_token, region_name, weather, temp, wind_dir, note_ch, note_en, love_days, birthdays):
    url = "https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={}".format(access_token)
    today = datetime.date.today()
    week_list = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]
    week = week_list[today.isoweekday() % 7]
    
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
                "value": love_days,
                "color": get_color()
            },
            "note_en": {
                "value": note_en,
                "color": get_color()
            },
            "note_ch": {
                "value": note_ch,
                "color": get_color()
            }
        }
    }

    for key, value in birthdays.items():
        birth_day = get_birthday(value["birthday"], today)
        birthday_data = f"距离{value['name']}的生日还有{birth_day}天" if birth_day > 0 else f"今天{value['name']}生日哦，祝生日快乐！"
        data["data"][key] = {"value": birthday_data, "color": get_color()}

    response = requests.post(url, json=data).json()
    if response["errcode"] == 0:
        print("推送消息成功")
    else:
        print("推送消息失败:", response)

# 发送所有消息
def send_all_messages():
    # 获取access_token
    access_token = get_access_token()

    # 获取情话
    note_ch, note_en = fetch_aiqingyl()

    # 获取和你相爱的日子
    love_date = datetime.date(2024, 8, 4)
    love_days = (datetime.date.today() - love_date).days

    # 获取生日
    birthdays = {
        "birthday1": config["birthday1"],
        "birthday2": config["birthday2"]
    }

    # 获取天气信息
    weather, temp, wind_dir = get_weather(config["region"])

    # 发送消息
    for user in config["user"]:
        send_message(user, access_token, config["region"], weather, temp, wind_dir, note_ch, note_en, love_days, birthdays)

# 启动消息推送
if __name__ == "__main__":
    send_all_messages()
