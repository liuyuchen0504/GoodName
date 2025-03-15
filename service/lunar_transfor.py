# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/3/13
# 
# ====================
import datetime

from LunarSolarConverter import LunarSolarConverter

converter = LunarSolarConverter.LunarSolarConverter()


FLAG_YEAR = 1924    # 甲子蛇年


# 生肖
CHINESE_ZODIAC = [
    "鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"
]


TIANGAN = ["甲", "丑", "丙", "丁", "戊", "已", "庚", "辛", "壬", "癸"]

# 干支纪年名称
CHINESE_CHRONOLOGY = [
    "甲子", "乙丑", "丙寅", "丁卯", "戊辰", "已巳", "庚午", "辛未", "壬申", "癸酉",
    "甲戌", "乙亥", "丙子", "丁丑", "戊寅", "已卯", "庚辰", "辛巳", "壬午", "癸未",
    "甲申", "乙酉", "丙戌", "丁亥", "戊子", "已丑", "庚寅", "辛卯", "壬辰", "癸巳",
    "甲午", "乙未", "丙申", "丁酉", "戊戌", "已亥", "庚子", "辛丑", "壬寅", "癸卯",
    "甲辰", "乙巳", "丙午", "丁未", "戊申", "已酉", "庚戌", "辛亥", "壬子", "癸丑",
    "甲寅", "乙卯", "丙辰", "丁巳", "戊午", "已未", "庚申", "辛酉", "壬戌", "癸亥"
]


CHINESE_MONTH = [
    ["丙寅", "丁卯", "戊辰", "已巳", "庚午", "辛未", "壬申", "癸酉", "甲戌", "乙亥", "丙子", "丁丑"], # 天干年 甲
    ["戊寅", "已卯", "庚辰", "辛巳", "壬午", "癸未", "甲申", "乙酉", "丙戌", "丁亥", "戊子", "已丑"], # 天干年 乙
    ["庚寅", "辛卯", "壬辰", "癸巳", "甲午", "乙未", "丙申", "丁酉", "戊戌", "已亥", "庚子", "辛丑"], # 天干年 丙
    ["壬寅", "癸卯", "甲辰", "乙巳", "丙午", "丁未", "戊申", "已酉", "庚戌", "辛亥", "壬子", "癸丑"], # 天干年 丁
    ["甲寅", "乙卯", "丙辰", "丁巳", "戊午", "已未", "庚申", "辛酉", "壬戌", "癸亥", "甲子", "乙丑"], # 天干年 戊
    ["丙寅", "丁卯", "戊辰", "已巳", "庚午", "辛未", "壬申", "癸酉", "甲戌", "乙亥", "丙子", "丁丑"], # 天干年 已
    ["戊寅", "已卯", "庚辰", "辛巳", "壬午", "癸未", "甲申", "乙酉", "丙戌", "丁亥", "戊子", "已丑"], # 天干年 庚
    ["庚寅", "辛卯", "壬辰", "癸巳", "甲午", "乙未", "丙申", "丁酉", "戊戌", "已亥", "庚子", "辛丑"], # 天干年 辛
    ["壬寅", "癸卯", "甲辰", "乙巳", "丙午", "丁未", "戊申", "已酉", "庚戌", "辛亥", "壬子", "癸丑"], # 天干年 壬
    ["甲寅", "乙卯", "丙辰", "丁巳", "戊午", "已未", "庚申", "辛酉", "壬戌", "癸亥", "甲子", "乙丑"], # 天干年 癸
]


CHINESE_TIME = [
    "子时", "丑时", "寅时", "卯时", "辰时", "巳时", "午时", "未时", "申时", "酉时", "戌时", "亥时"
]


def chinese_day(year: int, month: int, day: int):
    """根据公历日期算干支纪日

    :param year:    公历年
    :param month:   公历月
    :param day:     公历日
    :return:
    """
    _MONTH_BASE = [0, 31, -1, 30, 0, 31, 1, 32, 3, 33, 4, 34]

    s = year % 100 - 1
    u = s % 4
    m = _MONTH_BASE[month - 1]
    d = day

    C = (year - 1) // 100 + 1
    x = (44 * (C - 17) + (C - 17) // 4 + 3) % 60

    r = s // 4 * 6 + 5 * (s // 4 * 3 + u) + m + d + x
    if is_solar_leap(year) and month > 2:
        r += 1
    return CHINESE_CHRONOLOGY[r % 60 - 1]



def is_solar_leap(year: int):
    if year % 4 == 0:
        if year % 100 == 0:
            return year % 400 == 0
        else:
            return True
    else:
        return False


def solar2lunar_chinese(year: int, month: int, day: int, time: int = None):
    """根据阳历算农历生辰八字

    :param year:
    :param month:
    :param day:
    :param time:
    :return: 生辰八字, 农历年月日
    """
    solar = LunarSolarConverter.Solar(year, month, day)
    lunar = converter.SolarToLunar(solar)
    _year = CHINESE_CHRONOLOGY[(lunar.lunarYear - FLAG_YEAR) % 60]
    _zodiac = CHINESE_ZODIAC[(lunar.lunarYear - FLAG_YEAR) % 12]
    _month = CHINESE_MONTH[(lunar.lunarYear - FLAG_YEAR) % 10][lunar.lunarMonth - 1]
    _day = chinese_day(year, month, day)
    if time:
        _time = CHINESE_TIME[((time + 1) // 2) % 12]
        return f"{_year}{_zodiac}年{_month}月{_day}日{_time}", (lunar.lunarYear, lunar.lunarMonth, lunar.lunarDay)
    else:
        return f"{_year}{_zodiac}年{_month}月{_day}日", (lunar.lunarYear, lunar.lunarMonth, lunar.lunarDay)


def solar2lunar_chinese_str(date_str: str, format: str = "%Y-%m-%d"):
    date = datetime.datetime.strptime(date_str, format)
    return solar2lunar_chinese(date.year, date.month, date.day)[0]


if __name__ == "__main__":
    assert solar2lunar_chinese(2025, 3, 13) == ("乙巳蛇年已卯月辛巳日", (2025, 2, 14))
    assert solar2lunar_chinese(2023, 1, 14)[0] == "壬寅虎年癸丑月壬申日"
    assert solar2lunar_chinese(2023, 2, 15)[0] == "癸卯兔年甲寅月甲辰日"
    assert solar2lunar_chinese(1949, 10, 1)[0] == "已丑牛年癸酉月甲子日"
