# -*- coding: utf-8 -*-
"""生肖配对引擎 —— 数据与规则来自 yinyuan-skills/references/zodiac-compatibility.md"""
from .common import ZHI, SHENGXIAO, year_zhi_idx

# 地支序号 → 生肖
def zhi_to_shengxiao(zhi_i):
    return SHENGXIAO[zhi_i]


def year_to_shengxiao(year):
    return SHENGXIAO[year_zhi_idx(year)]


# ---- 关系数据（键为地支序号对，无序） ----

_LIUHE_TEXT = {
    frozenset((0, 1)): ("子丑合化土", "鼠的机灵配上牛的踏实，互补型佳偶。鼠提供灵感，牛负责落地。"),
    frozenset((2, 11)): ("寅亥合化木", "虎的霸气遇上猪的温柔，刚柔并济。猪能包容虎的脾气。"),
    frozenset((3, 10)): ("卯戌合化火", "兔的细腻遇到狗的忠诚，相知相守。两人都很重感情。"),
    frozenset((4, 9)): ("辰酉合化金", "龙的远见配上鸡的精细，互相欣赏。是彼此的头号粉丝。"),
    frozenset((5, 8)): ("巳申合化水", "蛇的深沉遇上猴的灵动，棋逢对手。精神层面很契合。"),
    frozenset((6, 7)): ("午未合化土", "马的热情遇上羊的温顺，温暖相伴。天生一对欢喜冤家。"),
}

_SANHE_GROUP_TEXT = {
    0: "申子辰水局：水上双子，默契满分。都是聪明人，沟通零障碍，小处大处都能打配合。",
    1: "寅午戌火局：热情碰撞，行动力爆表，生活不会无聊的一对。",
    2: "巳酉丑金局：精英组合，审美一致，互相成就，日子过得井井有条。",
    3: "亥卯未木局：温柔乡里两颗心，充满善意与体贴，岁月静好型配对。",
}

_LIUCHONG_TEXT = {
    frozenset((0, 6)): ("子午冲，水火对冲", "鼠重细节，马重自由；鼠慢热，马奔放。", "给彼此空间，尊重差异。"),
    frozenset((1, 7)): ("丑未冲，同类相斥", "都固执，冷战高手。", "学会主动低头，轮流让步。"),
    frozenset((2, 8)): ("寅申冲，金木交战", "虎直接，猴灵活；都爱主导。", "明确分工，不要抢同一个方向盘。"),
    frozenset((3, 9)): ("卯酉冲，金木相克", "兔感性，鸡理性；节奏不同频。", "多做对方喜欢的事，用行动弥补频率差。"),
    frozenset((4, 10)): ("辰戌冲，同性相斥", "都有主见，容易较劲。", "分清「大事」和「小事」，小事让步大事商量。"),
    frozenset((5, 11)): ("巳亥冲，水火相冲", "蛇深沉，猪直爽；猜疑 vs 透明。", "保持坦诚沟通，减少内心戏。"),
}

_LIUHAI_TEXT = {
    frozenset((0, 7)): ("子未害", "关心方式不被对方接受。", "多问对方需要什么，不要「自以为好」地付出。"),
    frozenset((1, 6)): ("丑午害", "节奏不一致，牛慢马快。", "找到双方都舒适的节奏，不强求同步。"),
    frozenset((2, 5)): ("寅巳害", "好意容易被误解。", "表达时注意方式，减少误解空间。"),
    frozenset((3, 4)): ("卯辰害", "小事积累矛盾。", "及时沟通小问题，不要攒着。"),
    frozenset((8, 11)): ("申亥害", "信任容易出裂痕。", "建立透明的沟通机制，不要让对方猜。"),
    frozenset((9, 10)): ("酉戌害", "表面和谐暗有分歧。", "定期深入交流，不要只聊表面。"),
}

_XING_PAIRS = {frozenset((0, 3)): "子卯无礼之刑，缺乏尊重时言语易伤人，注意分寸。",
               frozenset((1, 10)): "丑戌持势之刑，固执己见互不相让，遇事先各退一步。",
               frozenset((7, 10)): "未戌持势之刑，容易较劲，重要决定多商量少赌气。"}

_PO_PAIRS = {frozenset((1, 4)): "丑辰六破，初识美好，相处久了易生龃龉，多包容经营。"}

_SAME_TEXT = "同生肖相处像照镜子——优点缺点都熟悉。默契度高，但也要保持新鲜感，别把日子过成惯性。"

_SCORE = {"六合": 95, "三合": 85, "普通": 72, "六破": 65, "六害": 60, "三刑": 55, "六冲": 50}
_STARS = {"六合": 5, "三合": 4, "普通": 3, "六破": 3, "六害": 3, "三刑": 2, "六冲": 2}


def _in_sanhe(a, b):
    for gi, g in enumerate([(2, 6, 10), (8, 0, 4), (5, 9, 1), (11, 3, 7)]):
        if a in g and b in g:
            return gi
    return None


def match(a_year=None, b_year=None, a_zodiac=None, b_zodiac=None):
    """生肖配对。可传出生年或生肖名。返回结构化结果。"""
    if a_zodiac and b_zodiac:
        za, zb = a_zodiac, b_zodiac
        if za not in SHENGXIAO or zb not in SHENGXIAO:
            raise ValueError("生肖名无效，应为：" + "、".join(SHENGXIAO))
        ia, ib = SHENGXIAO.index(za), SHENGXIAO.index(zb)
    elif a_year and b_year:
        ia, ib = year_zhi_idx(int(a_year)), year_zhi_idx(int(b_year))
        for y in (a_year, b_year):
            if not 1900 <= int(y) <= 2100:
                raise ValueError("出生年份需在 1900-2100 之间")
        za, zb = SHENGXIAO[ia], SHENGXIAO[ib]
    else:
        raise ValueError("请提供双方出生年份或生肖")

    pair = frozenset((ia, ib))
    if ia == ib:
        relation, score = "普通", 76
        title, text, advice = "同生肖", _SAME_TEXT, "相似是缘分，互补靠经营，多制造小惊喜。"
    elif pair in _LIUHE_TEXT:
        relation, score = "六合", _SCORE["六合"]
        title, text = _LIUHE_TEXT[pair]
        advice = "六合是地支两两暗合中的最佳配对，不要因为「很配」就忽视经营，保持甜蜜的秘诀是持续用心。"
    elif _in_sanhe(ia, ib) is not None:
        gi = _in_sanhe(ia, ib)
        relation, score = "三合", _SCORE["三合"]
        title, text = "三合·" + _SANHE_GROUP_TEXT[gi].split("：")[0], _SANHE_GROUP_TEXT[gi]
        advice = "三合默契极深，志同道合。好的底子也要用心珍惜，一起成长才能长久。"
    elif pair in _LIUCHONG_TEXT:
        relation, score = "六冲", _SCORE["六冲"]
        title, conflict, advice = _LIUCHONG_TEXT[pair]
        text = conflict + " 六冲不代表一定不合！很多恩爱夫妻生肖对冲，反而在冲撞中找到平衡，关键在于是否愿意磨合。"
    elif pair in _LIUHAI_TEXT:
        relation, score = "六害", _SCORE["六害"]
        title, problem, advice = _LIUHAI_TEXT[pair]
        text = problem + " 六害不激烈，但容易在日常中积累不满，及时化解是关键。"
    elif pair in _XING_PAIRS:
        relation, score = "三刑", _SCORE["三刑"]
        title, text = "三刑", _XING_PAIRS[pair]
        advice = "刑主摩擦，语气放软、就事论事，冲突自然减少。"
    elif pair in _PO_PAIRS:
        relation, score = "六破", _SCORE["六破"]
        title, text = "六破", _PO_PAIRS[pair]
        advice = "破主细微损耗，把小情绪及时说开，不必攒到大爆发。"
    else:
        relation, score = "普通", _SCORE["普通"]
        title, text = "普通配对", "无特别好坏，关系呈中性底色，好坏看双方经营。"
        advice = "指出可能的摩擦点并提前沟通，感情靠具体行动一点点养出来。"

    stars = "⭐" * _STARS[relation]
    return {
        "a": {"zodiac": za, "zhi": ZHI[ia]},
        "b": {"zodiac": zb, "zhi": ZHI[ib]},
        "relation": relation,
        "score": score,
        "stars": stars,
        "title": title,
        "text": text,
        "advice": advice,
        "level_text": {
            "六合": "天生一对，默契满分",
            "三合": "极佳配对，志同道合",
            "普通": "中性配对，看经营",
            "六破": "小有龃龉，多包容",
            "六害": "暗藏摩擦，勤沟通",
            "三刑": "易有摩擦，软处理",
            "六冲": "对冲有火花，贵在磨合",
        }[relation],
    }
