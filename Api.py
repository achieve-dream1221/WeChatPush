import requests
from zhdate import ZhDate
from utils import *
from datetime import datetime
from pytz import timezone


class API:
    def __init__(self, config: dict):
        # 配置文件
        self.config = config
        # 中国上海时区
        self.tz = timezone("Asia/shanghai")
        self.today = datetime.today().astimezone(self.tz)
        self.today_dt = datetime(self.today.year, self.today.month, self.today.day)

    # 获取日期
    def get_date(self) -> str:
        weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        content = f"{self.today.date()} {ZhDate.from_datetime(self.today_dt)} {weekdays[self.today.weekday()]}"
        print_info("日期", content)
        return content

    # 毒鸡汤
    @staticmethod
    def get_dujitang() -> str:
        content = requests.get("https://api.btstu.cn/yan/api.php").text
        if not content:
            print_error("毒鸡汤: https://api.btstu.cn/yan/api.php 接口请求失败")
            exit_with_error()
        print_info("毒鸡汤", content)
        return content

    # 情话
    @staticmethod
    def get_love_message() -> str:
        response = requests.get("https://api.lovelive.tools/api/SweetNothings/Web/1").json()
        if response['code'] != 200:
            print_error("情话: https://api.lovelive.tools/api/SweetNothings/Web/1 接口请求失败")
            print(response)
            exit_with_error()
        content = response["returnObj"]['content']
        print_info("情话", content)
        return content

    def __get_weather(self):
        url = f"https://v2.alapi.cn/api/tianqi?token={self.config['alapi_token']}&city={self.config['city']}" \
              f"&province={self.config['province']}"
        response = requests.get(url).json()
        if response['code'] != 200:
            print_error(f"天气接口:{url} 请求失败")
            print(response)
            exit_with_error()
        return response['data']

    # 天气完整版
    def get_weather_all(self) -> list[str]:
        data = self.__get_weather()
        content = [self.config['city'], data['weather'], data['max_temp'], data['min_temp'],
                   data['temp'], data['wind'], data['air_pm25'], data['aqi']['air_level'],
                   data['sunrise'], data['sunset']]
        print_info("天气完整版", str(content))
        return content

    # 天气精简版
    def get_weather_simple(self) -> list[str]:
        data = self.__get_weather()
        content = [self.config['city'],
                   f"{data['weather']}, 当前温度: {data['temp']}℃, 最高温度: {data['max_temp']}℃, 最低温度: {data['min_temp']}℃"]
        print_info("天气精简版", str(content))
        return content

    # 追剧模式
    def get_chasing_drama(self) -> str:
        videos = dict(self.config['videos'])
        weekday = self.today.weekday() + 1
        content = ""
        for k, v in videos.items():
            if weekday in v[0]:
                content += (k + ", 今日" + v[1] + "点更新")
        if content == "":
            content = "今日没有你追的剧哦"
        print_info("追剧提醒", content)
        return content

    # 彩虹屁
    def get_rainbow_pi(self) -> str:
        url = f"http://api.tianapi.com/caihongpi/index?key={self.config['tianapi_token']}"
        response = requests.get(url).json()
        if response['code'] != 200:
            print_error(f"彩虹屁接口{url}, 请求失败")
            print(response)
            exit_with_error()
        content = response["newslist"][0]['content']
        print_info("彩虹屁", content)
        return content

    # 相遇时间
    def get_meet_days(self):
        """
        注意要用date做减法, 不要用datetime, 否则会有误差
        :return:
        """
        days = str((self.today.date() -
                    datetime.strptime(self.config["meet_day"], "%Y-%m-%d").astimezone(self.tz).date()).days)
        print_info("认识天数", days)
        return days

    # 词霸每日一句
    @staticmethod
    def get_everyday_note():
        data = requests.get("http://open.iciba.com/dsapi/").json()
        try:
            # note: 汉语, content: 英语
            content = data['note'] + " " + data['content']
            print_info("词霸每日一句", content)
            return content
        except KeyError:
            print_error(f"词霸每日一句:http://open.iciba.com/dsapi/, 接口请求失败")
            print(data)
            exit_with_error()

    @staticmethod
    def __get_birth_text(name: str, days: int):
        if days == 0:
            return f"今天是{name}的生日哦, 你备好礼物了吗?\n"
        if days <= 10:
            return f"还有{days}天就是{name}的生日了, 赶快准备礼物吧!\n"
        if days > 10:
            return f"距离{name}的生日还有{days}天\n"

    def get_birthdays_message(self):
        names = self.config['names']
        births = self.config['birthdays']
        if len(names) != len(births):
            print_error("请确定姓名个数和生日个数是否对应")
            exit_with_error()
        i = 0
        content = ''
        for birth in births:
            # 农历计算
            if birth.startswith("r"):
                # 由于设置了时区, 所以需要手动转换为新的datetime对象, 否则不支持减法操作
                dt = datetime.strptime(birth[1:], "%Y-%m-%d")
                next_birth_day = ZhDate(self.today.year, dt.month, dt.day)  # 农历生日转换为农历对象
                days = next_birth_day - ZhDate.from_datetime(self.today_dt)  # 今天日期转换为农历日期
                if days < 0:  # 生日已过, 计算下一年
                    next_birth_day = ZhDate(self.today.year + 1, dt.month, dt.day)
                    days = next_birth_day - ZhDate.from_datetime(self.today_dt)
            else:  # 阳历
                dt = datetime.strptime(birth, "%Y-%m-%d")
                # 用今年的生日日期 减去 今天的日期
                days = (datetime(self.today.year, dt.month, dt.day).astimezone(self.tz).date() - self.today.date()).days
                if days < 0:  # 生日已过, 计算下一年
                    days = (datetime(self.today.year + 1, dt.month, dt.day).astimezone(
                        self.tz).date() - self.today.date()).days
            content += self.__get_birth_text(names[i], days)
            i += 1
        content = content[:-1]  # 去除最后一个换行符
        print_info("生日", content)
        return content
