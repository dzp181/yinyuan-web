# -*- coding: utf-8 -*-
"""求签问姻缘引擎 —— 签号规则来自 references/fortune-sticks.md
签号 = (名字字符编码和 + 问题描述字符编码和 + 当前时辰序号 + 当前日期天数) % 100 + 1
同一天同一人对同一问题得到同一支签。
"""
import datetime
from .sticks_data import STICKS, CN_NUM, LEVEL_MEANING, FOOTER

SHICHEN_NAMES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]


def draw(name, question, now=None):
    now = now or datetime.datetime.now()
    name_sum = sum(ord(c) for c in (name or ""))
    q_sum = sum(ord(c) for c in (question or ""))
    hour_idx = ((now.hour + 1) // 2) % 12
    day_no = now.timetuple().tm_yday
    no = (name_sum + q_sum + hour_idx + day_no) % 100 + 1

    level, poem, jie, yy = STICKS[no - 1]
    return {
        "no": no,
        "no_cn": "第%s签" % CN_NUM[no - 1],
        "level": level,
        "poem": poem,
        "jie": jie,                      # 前 10 签有专属签解
        "yuan": yy,                      # 前 10 签有专属姻缘解读
        "meaning": LEVEL_MEANING[level],  # 等级签意
        "shichen": SHICHEN_NAMES[hour_idx],
        "date": now.strftime("%Y-%m-%d"),
        "question": question,
        "footer": FOOTER,
    }
