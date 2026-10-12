# -*- coding: utf-8 -*-
"""八字合婚引擎 —— 规则与评分权重来自 yinyuan-skills/references/bazi-matching.md

评分维度（权重）：
  天干关系 15 | 地支六合/三合 20 | 地支冲/害 15 | 日柱配合 25 | 五行互补 15 | 纳音配对 10
"""
import datetime
from .common import (GAN, ZHI, GAN_WUXING, ZHI_WUXING, GAN_HE, GAN_HE_HUA,
                     GAN_CHONG, ZHI_HE, ZHI_HE_HUA, ZHI_CHONG, ZHI_HAI,
                     nayin, wuxing_shengguan, parse_date)
from . import pai_pan

SHISHEN_SCORE = {
    "比肩": (12, "像朋友一样平等相处"),
    "劫财": (10, "既亲密又较劲"),
    "食神": (14, "一方付出多，照顾另一方"),
    "伤官": (11, "热烈但容易摩擦"),
    "偏财": (14, "一方主导，一方被吸引"),
    "正财": (18, "温和的吸引，稳定配对"),
    "七杀": (10, "一方强势，需要磨合"),
    "正官": (18, "被保护的感觉，传统良配"),
    "偏印": (13, "被照顾但有压力"),
    "正印": (17, "温暖的包容，安全感的来源"),
}

GRADE = [
    (90, "天作之合", "姻缘极深，好好珍惜"),
    (75, "佳偶天成", "底子很好，用心经营可长久"),
    (60, "尚可配对", "有缘但需磨合，多沟通"),
    (45, "需要用心", "挑战较大但非不可，重在经营"),
    (30, "有缘无分", "缘分较浅，随缘为好"),
    (0, "不建议强求", "天然冲突较多，在一起需极大努力"),
]


def _grade_of(score):
    for lo, name, desc in GRADE:
        if score >= lo:
            return name, desc
    return GRADE[-1][1], GRADE[-1][2]


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _chart(date_str, hour, minute, sex):
    d = parse_date(date_str)
    r = pai_pan.compute(d, hour=int(hour), minute=int(minute), sex=sex)
    p = r["pillars"]
    gan = [p[k][0] for k in ("year", "month", "day", "hour")]
    zhi = [p[k][1] for k in ("year", "month", "day", "hour")]
    wx_count = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
    for g in gan:
        wx_count[GAN_WUXING[GAN.index(g)]] += 1
    for z in zhi:
        wx_count[ZHI_WUXING[ZHI.index(z)]] += 1
    return {
        "solar": date_str,
        "lunar": r["lunar_text"],
        "shichen": r["shichen_text"],
        "sex": sex,
        "gan": gan,
        "zhi": zhi,
        "pillars": {k: [p[k][0], p[k][1]] for k in ("year", "month", "day", "hour")},
        "wuxing": wx_count,
    }


def _rel_pair(a, b, table):
    """查询地支关系表，返回命中的关系名或 None。"""
    ia, ib = ZHI.index(a), ZHI.index(b)
    if ZHI_HE.get(ia) == ib:
        return "六合"
    for g in [(2, 6, 10), (8, 0, 4), (5, 9, 1), (11, 3, 7)]:
        if ia in g and ib in g:
            return "三合"
    if ZHI_CHONG.get(ia) == ib:
        return "六冲"
    if ZHI_HAI.get(ia) == ib:
        return "六害"
    return None


def hehun(a_date, a_hour, a_minute, a_sex, b_date, b_hour, b_minute, b_sex):
    A = _chart(a_date, a_hour, a_minute, a_sex)
    B = _chart(b_date, b_hour, b_minute, b_sex)
    notes = []
    dims = []

    # 1. 天干关系（15）
    s = 7
    ag, bg = GAN.index(A["gan"][0]), GAN.index(B["gan"][0])
    dg, eg = GAN.index(A["gan"][2]), GAN.index(B["gan"][2])
    if GAN_HE.get(ag) == bg:
        hua = GAN_HE_HUA.get((ag, bg)) or GAN_HE_HUA.get((bg, ag))
        s += 4
        notes.append("年干 %s%s 相合化%s —— 天生有缘，互相吸引" % (A["gan"][0], B["gan"][0], hua))
    if GAN_HE.get(dg) == eg:
        hua = GAN_HE_HUA.get((dg, eg)) or GAN_HE_HUA.get((eg, dg))
        s += 4
        notes.append("日干 %s%s 相合化%s —— 心意相通的强信号" % (A["gan"][2], B["gan"][2], hua))
    if GAN_CHONG.get(ag) == bg:
        s -= 4
        notes.append("年干 %s%s 相冲 —— 原生家庭/观念层面偶有冲撞" % (A["gan"][0], B["gan"][0]))
    if GAN_CHONG.get(dg) == eg:
        s -= 4
        notes.append("日干 %s%s 相冲 —— 性格底色差异大，需要包容" % (A["gan"][2], B["gan"][2]))
    dims.append({"name": "天干关系", "score": _clamp(s, 0, 15), "full": 15})

    # 2. 地支六合/三合（20）
    s = 8
    for label, (x, y) in (("年支", (A["zhi"][0], B["zhi"][0])), ("日支", (A["zhi"][2], B["zhi"][2]))):
        rel = _rel_pair(x, y, None)
        if rel == "六合":
            s += 7 if label == "年支" else 5
            notes.append("%s %s%s 六合化%s —— 亲密有默契" % (label, x, y, ZHI_HE_HUA.get((ZHI.index(x), ZHI.index(y)), "")))
        elif rel == "三合":
            s += 5
            notes.append("%s %s%s 三合 —— 志同道合，默契极深" % (label, x, y))
    dims.append({"name": "地支六合三合", "score": _clamp(s, 0, 20), "full": 20})

    # 3. 地支冲/害（15）
    s = 10
    for label, (x, y) in (("年支", (A["zhi"][0], B["zhi"][0])), ("日支", (A["zhi"][2], B["zhi"][2]))):
        ia, ib = ZHI.index(x), ZHI.index(y)
        if ZHI_CHONG.get(ia) == ib:
            s -= 8 if label == "年支" else 5
            notes.append("%s %s%s 六冲 —— %s%s 相冲，需互相退让" % (label, x, y, x, y))
        elif ZHI_HAI.get(ia) == ib:
            s -= 4
            notes.append("%s %s%s 六害 —— 亲近中暗藏摩擦，多沟通" % (label, x, y))
    dims.append({"name": "地支冲害", "score": _clamp(s, 0, 15), "full": 15})

    # 4. 日柱配合（25）：日主十神 + 日支互动
    shishen = pai_pan.shishen_of(GAN.index(A["gan"][2]), GAN.index(B["gan"][2]))
    base, meaning = SHISHEN_SCORE.get(shishen, (12, "像朋友一样平等相处"))
    s = base
    notes.append("日主关系（%s 对 %s）：%s —— %s" % (A["gan"][2], B["gan"][2], shishen, meaning))
    dza, dzb = ZHI.index(A["zhi"][2]), ZHI.index(B["zhi"][2])
    if ZHI_HE.get(dza) == dzb:
        s += 5
        notes.append("日支（配偶宫）%s%s 相合 —— 婚姻宫暗合，缘分加分" % (A["zhi"][2], B["zhi"][2]))
    elif ZHI_CHONG.get(dza) == dzb:
        s -= 3
        notes.append("日支（配偶宫）%s%s 相冲 —— 生活习惯差异明显，需磨合" % (A["zhi"][2], B["zhi"][2]))
    dims.append({"name": "日柱配合", "score": _clamp(s, 0, 25), "full": 25})

    # 5. 五行互补（15）
    wa, wb = A["wuxing"], B["wuxing"]
    bonus = 0.0
    for e in ("木", "火", "土", "金", "水"):
        if wa[e] == 0 and wb[e] > 0:
            bonus += min(wb[e], 3) / 3 * 4
        if wb[e] == 0 and wa[e] > 0:
            bonus += min(wa[e], 3) / 3 * 4
    if all(v > 0 for v in wa.values()) and all(v > 0 for v in wb.values()):
        s = 12
        notes.append("双方八字五行俱全 —— 自身平衡，相处稳定")
    else:
        s = round(bonus) + 3
        miss_a = "、".join(e for e in wa if wa[e] == 0)
        miss_b = "、".join(e for e in wb if wb[e] == 0)
        if miss_a:
            notes.append("一方缺%s，恰好对方带旺 —— 五行互补" % miss_a)
        if miss_b:
            notes.append("一方缺%s，恰好对方带旺 —— 五行互补" % miss_b)
    dims.append({"name": "五行互补", "score": _clamp(s, 0, 15), "full": 15})

    # 6. 纳音配对（10）
    na = nayin(GAN.index(A["gan"][0]), ZHI.index(A["zhi"][0]))
    nb = nayin(GAN.index(B["gan"][0]), ZHI.index(B["zhi"][0]))
    ea, eb = na[-1], nb[-1]
    rel = wuxing_shengguan(ea, eb)
    if na == nb:
        s = 9
        notes.append("年柱纳音同为「%s」 —— 天生相似，默契度高" % na)
    elif rel in ("a生b", "b生a"):
        s = 8
        notes.append("年柱纳音 %s 与 %s 五行相生 —— 互补互利" % (na, nb))
    else:
        s = 4
        notes.append("年柱纳音 %s 与 %s 五行相克 —— 需要更多磨合" % (na, nb))
    dims.append({"name": "纳音配对", "score": _clamp(s, 0, 10), "full": 10})

    score = sum(d["score"] for d in dims)
    grade, desc = _grade_of(score)
    if score >= 75:
        summary = "整体缘分配底很好。任何分数都只是参考工具，不是判决书——好的底子更要用心经营、共同成长。"
    elif score >= 60:
        summary = "缘分底子尚可，磨合是关键词。分数只是参考，多沟通、多经营，感情会越来越好。"
    else:
        summary = "分数提示需要更多用心，但这不是判决书。冲有时反而激荡出火花，愿意磨合的两个人才能走到最后。"

    return {
        "score": score,
        "grade": grade,
        "grade_desc": desc,
        "summary": summary,
        "dimensions": dims,
        "notes": notes,
        "a": A,
        "b": B,
    }
