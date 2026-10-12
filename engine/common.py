# -*- coding: utf-8 -*-
"""姻缘测算公共常量与工具。数据来源：yinyuan-skills/references/*.md"""

import datetime


def parse_date(s):
    """'YYYY-MM-DD' -> datetime.date

    兼容 Python 3.6：datetime.date.fromisoformat() 直到 3.7 才进入标准库，
    而生产环境可能是 3.6（Alibaba Cloud Linux 3 等老镜像）。
    """
    s = str(s).strip().replace("/", "-").replace(".", "-")
    parts = s.split("-")
    if len(parts) < 3:
        raise ValueError("日期格式应为 YYYY-MM-DD，收到：%s" % s)
    return datetime.date(int(parts[0]), int(parts[1]), int(parts[2]))


GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"

GAN_WUXING = ["木", "木", "火", "火", "土", "土", "金", "金", "水", "水"]
ZHI_WUXING = ["水", "土", "木", "木", "土", "火", "火", "土", "金", "金", "土", "水"]

SHENGXIAO = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]

# 五行相生：木→火→土→金→水→木 ；相克：木→土→水→火→金→木
SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

# 天干五合（甲己合化土 …）与天干四冲
GAN_HE = {0: 5, 5: 0, 1: 6, 6: 1, 2: 7, 7: 2, 3: 8, 8: 3, 4: 9, 9: 4}
GAN_HE_HUA = {(0, 5): "土", (5, 0): "土", (1, 6): "金", (6, 1): "金",
              (2, 7): "水", (7, 2): "水", (3, 8): "木", (8, 3): "木",
              (4, 9): "火", (9, 4): "火"}
GAN_CHONG = {0: 6, 6: 0, 1: 7, 7: 1, 2: 8, 8: 2, 3: 9, 9: 3}

# 地支关系
# 地支六合：子丑、寅亥、卯戌、辰酉、巳申、午未
ZHI_HE = {0: 1, 1: 0, 2: 11, 11: 2, 3: 10, 10: 3, 4: 9, 9: 4, 5: 8, 8: 5, 6: 7, 7: 6}
ZHI_HE_HUA = {(0, 1): "土", (1, 0): "土", (2, 11): "木", (11, 2): "木", (3, 10): "火", (10, 3): "火",
              (4, 9): "金", (9, 4): "金", (5, 8): "水", (8, 5): "水", (6, 7): "土", (7, 6): "土"}
ZHI_CHONG = {0: 6, 6: 0, 1: 7, 7: 1, 2: 8, 8: 2, 3: 9, 9: 3, 4: 10, 10: 4, 5: 11, 11: 5}  # 六冲
ZHI_HAI = {0: 7, 7: 0, 1: 6, 6: 1, 2: 5, 5: 2, 3: 4, 4: 3, 8: 11, 11: 8, 9: 10, 10: 9}  # 六害
SANHE_GROUPS = [(2, 6, 10), (8, 0, 4), (5, 9, 1), (11, 3, 7)]  # 申子辰 寅午戌 巳酉丑 亥卯未
SANHE_NAME = ["水局", "火局", "金局", "木局"]

# 时辰：hour -> 地支序号
def hour_to_zhi_idx(hour):
    if hour is None:
        return None
    return ((hour + 1) // 2) % 12


# 纳音（六十甲子，两两一组共 30 条）——来源 references/bazi-matching.md
NAYIN_30 = [
    "海中金", "炉中火", "大林木", "路旁土", "剑锋金",
    "山头火", "涧下水", "城墙土", "白蜡金", "杨柳木",
    "泉中水", "屋上土", "霹雳火", "松柏木", "长流水",
    "砂石金", "山下火", "平地木", "壁上土", "金箔金",
    "覆灯火", "天河水", "大驿土", "钗钏金", "桑柘木",
    "大溪水", "沙中土", "天上火", "石榴木", "大海水",
]


def gz_index(gan_i, zhi_i):
    """由天干序号、地支序号求六十甲子序号（0-59）。"""
    for n in range(60):
        if n % 10 == gan_i and n % 12 == zhi_i:
            return n
    raise ValueError("非法干支组合: %d/%d" % (gan_i, zhi_i))


def nayin(gan_i, zhi_i):
    """六十甲子纳音名。"""
    return NAYIN_30[gz_index(gan_i, zhi_i) // 2]


def wuxing_shengguan(a, b):
    """a 对 b 的五行关系：'同'(比和) / 'a生b' / 'b生a' / 'a克b' / 'b克a'。"""
    if a == b:
        return "同"
    if SHENG.get(a) == b:
        return "a生b"
    if SHENG.get(b) == a:
        return "b生a"
    if KE.get(a) == b:
        return "a克b"
    if KE.get(b) == a:
        return "b克a"
    return "同"


def year_zhi_idx(year):
    """公历年 → 地支序号（生肖年，正月初一/立春边界按公历年近似）。"""
    return (year - 4) % 12
