# -*- coding: utf-8 -*-
"""红线测算引擎 —— 正缘画像与时间窗来自 references/taohua-luck.md 第 7 节"""
import datetime
from .common import GAN, ZHI, GAN_HE
from . import pai_pan
from .taohua import TAOHUA_POS, _GROUP_OF, ZHI_CHONG

# 日支（配偶宫）→ 正缘画像（references/taohua-luck.md）
MATE_PORTRAIT = {
    "子": ("聪明灵活，善沟通", "清秀灵动", "教育/IT/媒体"),
    "丑": ("踏实稳重，可靠", "稳重端庄", "金融/工程/管理"),
    "寅": ("热情大方，有魄力", "高大挺拔", "创业/领导/军警"),
    "卯": ("温柔文雅，有艺术感", "清秀优雅", "艺术/设计/文化"),
    "辰": ("有主见，果断", "气质出众", "管理/法律/政界"),
    "巳": ("深沉内敛，观察力强", "精致干练", "研究/医疗/金融"),
    "午": ("热情开朗，行动力强", "阳光健康", "销售/体育/创业"),
    "未": ("温和善良，重视家庭", "柔和可亲", "教育/服务/农业"),
    "申": ("机智灵活，幽默风趣", "精神干练", "商业/科技/传媒"),
    "酉": ("注重细节，审美高", "五官精致", "艺术/法律/金融"),
    "戌": ("忠诚可靠，有责任感", "稳健大方", "军警/工程/管理"),
    "亥": ("善良包容，有智慧", "随和亲和", "学术/文化/公益"),
}

EXPECT_ADVICE = {
    "脱单": "把社交半径扩大一点：兴趣社群、朋友聚会都是红线经过的地方。旺桃花月主动一点，其余时间把自己过好。",
    "异地": "距离考验的是节奏感——固定的通话、见面的盼头比激情更重要。红线不断，靠的是两个人一起维护。",
    "结婚": "谈婚论嫁期，把现实问题摆到桌面上聊：房子、家庭、规划。能一起解决现实问题的人，才是能走进婚姻的人。",
    "复合": "先想清楚当初分开的原因是否已经解决。复合不是回到过去，而是用新的方式重新开始。",
    "暗恋": "暧昧期最好的策略是「有分寸地靠近」：增加自然接触，观察对方反应，再决定要不要开口。",
}
DEFAULT_ADVICE = "正缘不是等来的，是在成为更好的自己的路上遇见的。守住本命桃花位的活跃度，缘分自然会来。"


def analyze(date_str, hour, minute, sex, expect=None, now=None):
    now = now or datetime.date.today()
    d = datetime.date.fromisoformat(date_str)
    r = pai_pan.compute(d, hour=int(hour), minute=int(minute), sex=sex)
    p = r["pillars"]
    year_zhi_i = ZHI.index(p["year"][1])
    day_zhi = p["day"][1]
    day_gan = p["day"][0]
    day_gan_i = GAN.index(day_gan)

    trait, look, career = MATE_PORTRAIT[day_zhi]

    # 本命桃花位
    tao_zhi, fangwei, _, meaning = TAOHUA_POS[_GROUP_OF[year_zhi_i]]
    # 红鸾 / 天喜（卯起子年逆数）
    hongluan = (3 - year_zhi_i) % 12
    tianxi = (hongluan + 6) % 12

    # 未来 8 年时间窗
    timeline = []
    for fy in range(now.year, now.year + 8):
        fy_gan_i = (fy - 4) % 10
        fy_zhi_i = (fy - 4) % 12
        tags = []
        score = 0
        if TAOHUA_POS[_GROUP_OF[fy_zhi_i]][0] == tao_zhi:
            tags.append("流年桃花旺")
            score += 3
        if GAN_HE.get(fy_gan_i) == day_gan_i:
            tags.append("正缘信号（流年天干与日干相合）")
            score += 3
        if fy_zhi_i == hongluan:
            tags.append("红鸾星动")
            score += 2
        elif fy_zhi_i == tianxi:
            tags.append("天喜星动")
            score += 2
        if ZHI_CHONG.get(fy_zhi_i) == ZHI.index(day_zhi):
            tags.append("冲配偶宫（感情有大变动，可能好也可能需要谨慎）")
            score += 1
        timeline.append({"year": fy, "tags": tags, "score": score})
    timeline.sort(key=lambda x: -x["score"])
    best = timeline[0]
    strong_years = [t for t in timeline if t["score"] >= 3]
    timeline.sort(key=lambda x: x["year"])

    # 缘分指数（启发式：0-98）
    score = 55
    score += min(24, 6 * len(strong_years))
    if day_zhi in ("子", "午", "卯", "酉"):
        score += 8  # 桃花星坐配偶宫
    score = min(98, score)

    exp_key = None
    if expect:
        for k in EXPECT_ADVICE:
            if k in expect:
                exp_key = k
                break
    advice = EXPECT_ADVICE.get(exp_key, DEFAULT_ADVICE)

    return {
        "solar": date_str,
        "lunar": r["lunar_text"],
        "sex": sex,
        "day_pillar": day_gan + day_zhi,
        "portrait": {"trait": trait, "look": look, "career": career,
                     "desc": "你的配偶宫（日支）坐「%s」——正缘性格%s，外貌偏%s，职业倾向%s。" % (
                         day_zhi, trait, look, career)},
        "taohua_pos": {"zhi": tao_zhi, "fangwei": fangwei, "meaning": meaning},
        "fate_index": score,
        "best_year": {"year": best["year"], "tags": best["tags"]},
        "strong_years": strong_years,
        "timeline": timeline,
        "advice": advice,
        "footer": "时间窗口是概率提示而非保证；缘分天注定，幸福自己争。",
    }
