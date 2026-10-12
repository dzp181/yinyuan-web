# -*- coding: utf-8 -*-
"""紫微夫妻宫引擎（简化安星：十四主星 + 常用辅煞星 + 四化）
安星规则依据紫微斗数传统安星诀；主星/辅煞解读来自 references/ziwei-marriage.md。

安星锚点（自检）：1990-05-15 12:00 男（农历四月廿一）：
  命宫亥（丁亥）、纳音屋上土→土五局、紫微在戌、夫妻宫酉坐 天机+巨门。
"""
import datetime
import math
from .common import GAN, ZHI, nayin
from . import pai_pan

# ---- 主星解读（references/ziwei-marriage.md 第 2 节） ----
MAIN_STARS = {
    "紫微": {"mate": "有气质、有主见、略带贵气，可能来自条件不错的家庭",
             "mode": "重视精神层面的匹配，希望伴侣是有能力的「强者」",
             "lesson": "双方都太有主见时容易较劲，需要学会轮流做主",
             "advice": "找一个你真正佩服的人，而不仅仅是喜欢的人"},
    "天机": {"mate": "聪明灵活、思维敏捷、善于沟通，可能从事脑力型工作",
             "mode": "喜欢智性恋，被对方的头脑和谈吐吸引",
             "lesson": "想太多容易犹豫不决，感情中需要果断",
             "advice": "别把感情当数学题算，有时候跟着感觉走就对了"},
    "太阳": {"mate": "热情开朗、乐于助人、有社会责任感",
             "mode": "光明正大的恋爱，不喜欢暧昧和猜忌",
             "lesson": "付出太多容易累，需要学会接受而不是一味给予",
             "advice": "找一个懂得心疼你付出的人，而不是只享受你付出的人"},
    "武曲": {"mate": "务实能干、财务观念强、有执行力",
             "mode": "重行动轻言语，用做而不是说来表达爱",
             "lesson": "太务实可能缺少浪漫，需要偶尔制造惊喜",
             "advice": "找一个既懂你的务实、也能带你浪漫的人"},
    "天同": {"mate": "温和善良、知足常乐、有艺术气质",
             "mode": "追求舒适和谐的关系，不喜欢冲突",
             "lesson": "太随和容易被忽略需求，需要学会表达自己",
             "advice": "温柔是优点，但也要有自己的底线"},
    "廉贞": {"mate": "性格鲜明、有魅力、社交能力强",
             "mode": "感情浓烈而复杂，爱恨分明",
             "lesson": "容易因嫉妒或占有欲引发矛盾",
             "advice": "信任是这段关系的基石，学会给对方空间"},
    "天府": {"mate": "稳重可靠、善于理财、有管理才能",
             "mode": "追求稳定长久的感情，重视家庭",
             "lesson": "可能过于保守或缺乏激情",
             "advice": "稳定中加一点冒险，偶尔打破常规"},
    "太阴": {"mate": "温柔细腻、重视感情、审美品位好，可能偏文静",
             "mode": "深情的浪漫主义者，重视情感交流",
             "lesson": "过于敏感容易受伤，情绪起伏影响关系",
             "advice": "找一个情绪稳定的伴侣来平衡你"},
    "贪狼": {"mate": "多才多艺、社交达人、有魅力、异性缘好",
             "mode": "桃花旺盛，感情经历可能较丰富",
             "lesson": "诱惑多，需要在花丛中认准那一朵",
             "advice": "桃花多是天赋不是错，关键是择一而终"},
    "巨门": {"mate": "口才好、分析力强、有研究精神",
             "mode": "重视深层次的沟通和理解",
             "lesson": "容易因言语引起误会，说者无意听者有心",
             "advice": "沟通是你们的双刃剑，学会温柔地表达"},
    "天相": {"mate": "注重形象、善于协调、有服务精神",
             "mode": "追求和谐配对，重视伴侣间的配合",
             "lesson": "太在意「配不配」而忽略真实感受",
             "advice": "别总想着当完美伴侣，做真实的自己就好"},
    "天梁": {"mate": "正直善良、乐于助人、有长辈缘",
             "mode": "像好朋友一样的恋爱，互相扶持",
             "lesson": "可能缺少恋爱的激情，太像「合伙人」",
             "advice": "偶尔放下「大哥/大姐」的角色，当一回被保护的人"},
    "七杀": {"mate": "个性强烈、有冒险精神、独立自主",
             "mode": "轰轰烈烈的恋爱，不喜平淡",
             "lesson": "个性太强容易冲突，需要一个能让你服气的人",
             "advice": "找一个你能真心尊重的人，这样你的强才能变成保护"},
    "破军": {"mate": "有魄力、敢打破常规、个性鲜明",
             "mode": "感情经历波折较多，但每次都刻骨铭心",
             "lesson": "破坏性太强，需要学会建设而不是推倒重来",
             "advice": "折腾够了就想安定，你的正缘在你成熟之后"},
}

# 辅星/煞星入夫妻宫（references 第 3 节）
AUX_GOOD = {
    "文昌": "配偶有文才，感情浪漫，注重精神交流",
    "文曲": "配偶有文才，感情浪漫，注重精神交流",
    "左辅": "配偶有能力辅助你，或感情中有贵人相助",
    "右弼": "配偶有能力辅助你，或感情中有贵人相助",
    "天魁": "感情中遇到贵人，配偶条件好",
    "天钺": "感情中遇到贵人，配偶条件好",
    "禄存": "感情带财，因婚姻得益，配偶经济条件不错",
}
AUX_BAD = {
    "擎羊": ("感情容易有争执和冲动", "学会冷静，不在情绪上头时做决定"),
    "陀罗": ("感情容易纠缠拖沓", "需要果断，不要拖泥带水"),
    "火星": ("感情来得快去得也快", "给感情一个缓冲期，不要闪恋闪分"),
    "铃星": ("感情中暗藏波动", "保持警觉但不要多疑"),
    "地空": ("感情有虚幻感，理想与现实有差距", "脚踏实地，不要被幻想蒙蔽"),
    "地劫": ("感情有虚幻感，理想与现实有差距", "脚踏实地，不要被幻想蒙蔽"),
}

# 四化表（以生年天干起）
SIHUA = {
    0: {"廉贞": "禄", "破军": "权", "武曲": "科", "太阳": "忌"},
    1: {"天机": "禄", "天梁": "权", "紫微": "科", "太阴": "忌"},
    2: {"天同": "禄", "天机": "权", "文昌": "科", "廉贞": "忌"},
    3: {"太阴": "禄", "天同": "权", "天机": "科", "巨门": "忌"},
    4: {"贪狼": "禄", "太阴": "权", "右弼": "科", "天机": "忌"},
    5: {"武曲": "禄", "贪狼": "权", "天梁": "科", "文曲": "忌"},
    6: {"太阳": "禄", "武曲": "权", "太阴": "科", "天同": "忌"},
    7: {"巨门": "禄", "太阳": "权", "文曲": "科", "文昌": "忌"},
    8: {"天梁": "禄", "紫微": "权", "左辅": "科", "武曲": "忌"},
    9: {"破军": "禄", "巨门": "权", "太阴": "科", "贪狼": "忌"},
}
SIHUA_MEANING = {"禄": "感情运好，因婚姻得益，桃花旺、感情甜蜜",
                 "权": "感情中强势、主导关系，需要尊重伴侣的意愿",
                 "科": "感情中有贵人，配偶条件优秀",
                 "忌": "感情有阻碍、需多经营——不顺但非绝望，关键在于化解"}

LU_CUN = {0: 2, 1: 3, 2: 5, 4: 5, 3: 6, 5: 6, 6: 8, 7: 9, 8: 11, 9: 0}  # 年干→禄存支序
KUI_YUE = {0: (1, 7), 4: (1, 7), 6: (1, 7), 1: (0, 8), 5: (0, 8), 2: (11, 9), 3: (11, 9),
           8: (3, 5), 9: (3, 5), 7: (6, 2)}
HUO_START = {}
for _z in (2, 6, 10):
    HUO_START[_z] = 1   # 寅午戌年 火星起丑
for _z in (8, 0, 4):
    HUO_START[_z] = 2   # 申子辰年 火星起寅
for _z in (5, 9, 1):
    HUO_START[_z] = 3   # 巳酉丑年 火星起卯
for _z in (11, 3, 7):
    HUO_START[_z] = 9   # 亥卯未年 火星起酉
LING_START = {}
for _z in (2, 6, 10):
    LING_START[_z] = 3  # 寅午戌年 铃星起卯
for _z in (8, 0, 4), (5, 9, 1), (11, 3, 7):
    for _zz in _z:
        LING_START[_zz] = 10  # 其余起戌

JU_OF = {"水": 2, "木": 3, "金": 4, "土": 5, "火": 6}
PALACE_NAMES = ["命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄",
                "迁移", "交友", "官禄", "田宅", "福德", "父母"]


def _palace_gan(year_gan_i, palace_zhi_i):
    """五虎遁：由年干给任意地支宫位配天干（寅为起点）。"""
    start = (2 + (year_gan_i % 5) * 2) % 10
    return (start + (palace_zhi_i - 2)) % 10


def analyze(date_str, hour, minute, sex):
    d = datetime.date.fromisoformat(date_str)
    ly, lm, ld, leap = pai_pan.solar_to_lunar(d.year, d.month, d.day)
    hour_idx = ((int(hour) + 1) // 2) % 12

    # 排盘所需的年柱（以农历年为口径：立春前的近似处理，用公历年干支即可满足本报告粒度）
    birth_dt = pai_pan.beijing(d.year, d.month, d.day, int(hour), int(minute))
    year_num, year_gan, year_zhi, _ = pai_pan.resolve_year_pillar(birth_dt)
    year_gan_i = GAN.index(year_gan)
    year_zhi_i = ZHI.index(year_zhi)

    # 命宫 / 身宫
    month_palace = (2 + lm - 1) % 12
    ming = (month_palace - hour_idx) % 12
    shen = (month_palace + hour_idx) % 12
    ming_gan_i = _palace_gan(year_gan_i, ming)

    # 五行局（命宫干支纳音）
    ny = nayin(ming_gan_i, ming)
    ju = JU_OF[ny[-1]]

    # 紫微安星
    q = math.ceil(ld / ju)
    b = q * ju - ld
    zw = (2 + q - 1) % 12
    zw = (zw - b) % 12 if b % 2 == 1 else (zw + b) % 12
    ziwei_series = {"紫微": zw, "天机": (zw - 1) % 12, "太阳": (zw - 3) % 12,
                    "武曲": (zw - 4) % 12, "天同": (zw - 5) % 12, "廉贞": (zw - 8) % 12}
    tf = (4 - zw) % 12
    tianfu_series = {"天府": tf, "太阴": (tf + 1) % 12, "贪狼": (tf + 2) % 12,
                     "巨门": (tf + 3) % 12, "天相": (tf + 4) % 12, "天梁": (tf + 5) % 12,
                     "七杀": (tf + 6) % 12, "破军": (tf + 10) % 12}
    star_pos = {}
    star_pos.update(ziwei_series)
    star_pos.update(tianfu_series)

    fuchi = (ming - 2) % 12
    dui_gong = (fuchi + 6) % 12

    # 宫内星
    main_in = [s for s, p in star_pos.items() if p == fuchi]
    main_order = ["紫微", "天机", "太阳", "武曲", "天同", "廉贞",
                  "天府", "太阴", "贪狼", "巨门", "天相", "天梁", "七杀", "破军"]
    main_in.sort(key=main_order.index)

    aux_in = {}
    lc = LU_CUN[year_gan_i]
    aux_in["禄存"] = lc
    aux_in["擎羊"] = (lc + 1) % 12
    aux_in["陀罗"] = (lc - 1) % 12
    aux_in["文昌"] = (10 - hour_idx) % 12
    aux_in["文曲"] = (4 + hour_idx) % 12
    aux_in["左辅"] = (4 + lm - 1) % 12
    aux_in["右弼"] = (10 - (lm - 1)) % 12
    kui, yue = KUI_YUE[year_gan_i]
    aux_in["天魁"] = kui
    aux_in["天钺"] = yue
    aux_in["火星"] = (HUO_START[year_zhi_i] + hour_idx) % 12
    aux_in["铃星"] = (LING_START[year_zhi_i] + hour_idx) % 12
    aux_in["地空"] = (11 + hour_idx) % 12
    aux_in["地劫"] = (11 - hour_idx) % 12
    good_in = [s for s, p in aux_in.items() if p == fuchi and s in AUX_GOOD]
    bad_in = [s for s, p in aux_in.items() if p == fuchi and s in AUX_BAD]

    # 四化入夫妻宫
    sihua = SIHUA[year_gan_i]
    sihua_hits = [(s, h) for s, h in sihua.items()
                  if (s in main_in) or (s in aux_in and aux_in[s] == fuchi)]

    # 格局判断
    pattern = []
    if not main_in:
        borrowed = [s for s, p in star_pos.items() if p == dui_gong]
        pattern.append("夫妻宫为空宫（无主星），感情较被动，借对宫（官禄宫）主星 %s 解读" % "、".join(borrowed) if borrowed else "夫妻宫为空宫，感情较被动")
    if "紫微" in main_in and "天府" in main_in:
        pattern.append("紫微天府同入夫妻宫——配偶极优秀，但要求也高")
    if "太阳" in main_in and "太阴" in main_in:
        pattern.append("日月同宫——配偶多才多艺，但性格复杂")
    if len(bad_in) >= 3:
        pattern.append("煞星云集——感情波折多，但扛过去会更坚固")
    if "贪狼" in main_in and bad_in:
        pattern.append("桃花星加煞——感情多姿多彩但不稳定，需要定力")

    # 综合解读
    interp = []
    for s in main_in:
        m = MAIN_STARS[s]
        interp.append({
            "star": s,
            "mate": m["mate"], "mode": m["mode"],
            "lesson": m["lesson"], "advice": m["advice"],
        })

    return {
        "solar": date_str,
        "lunar": "%d年%s%s月%s日" % (ly, "闰" if leap else "", _lm_name(lm), _ld_name(ld)),
        "sex": sex,
        "ming_gong": {"zhi": ZHI[ming], "gan": GAN[ming_gan_i]},
        "shen_gong": {"zhi": ZHI[shen]},
        "wuxing_ju": "%s（%s局）" % (ny, {"水": "水二", "木": "木三", "金": "金四", "土": "土五", "火": "火六"}[ny[-1]]),
        "fuchi": {"zhi": ZHI[fuchi], "gan": GAN[_palace_gan(year_gan_i, fuchi)], "duigong": ZHI[dui_gong]},
        "main_stars": main_in,
        "interp": interp,
        "good_stars": good_in,
        "bad_stars": bad_in,
        "good_effects": {s: AUX_GOOD[s] for s in good_in},
        "bad_effects": {s: AUX_BAD[s] for s in bad_in},
        "sihua_hits": [{"star": s, "hua": h, "meaning": SIHUA_MEANING[h]} for s, h in sihua_hits],
        "pattern": pattern,
        "note": "本报告为简化版紫微安星（十四主星+常用辅煞+生年四化），未含大限流年；娱乐为主，理性参考。",
    }


def _lm_name(m):
    return {1: "正", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "七", 8: "八",
            9: "九", 10: "十", 11: "十一", 12: "十二"}[m]


def _ld_name(d):
    nums = "一二三四五六七八九十"
    if d <= 10:
        return "初" + nums[d - 1] if d < 10 else "初十"
    if d < 20:
        return "十" + nums[d - 11]
    if d == 20:
        return "二十"
    if d < 30:
        return "廿" + nums[d - 21]
    return "三十" if d == 30 else "卅一" if d == 31 else "三十"
