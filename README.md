# 月老姻缘 · 在线姻缘测算网站

> 月老牵红线，测测你的姻缘 —— 用中华传统术数做一套**透明、有据可依**的姻缘测算网站。

基于 [Ming-H/yinyuan-skills](https://github.com/Ming-H/yinyuan-skills) 的结构化知识库（MIT 风格参考库）实现，
把原本面向 LLM Prompt 的测算规则**工程化为确定性算法**，纯 Python 标准库实现，零第三方依赖。

## 六大测算模式

| 模式 | 接口 | 算法依据 |
|------|------|----------|
| 八字合婚 | `POST /api/hehun` | 双方排盘（天文级节气/农历引擎）+ 六维加权评分（天干15/地支合20/冲害15/日柱25/五行15/纳音10） |
| 生肖配对 | `POST /api/zodiac` | 十二生肖六合/三合/六冲/六害/三刑/六破全矩阵 + 分场景解读 |
| 紫微夫妻宫 | `POST /api/ziwei` | 紫微安星诀（命宫/五行局/十四主星/辅煞星/生年四化），简化版 |
| 求签问姻缘 | `POST /api/qiuqian` | 100 支姻缘签诗；签号 = (名字+问题+时辰+日期) % 100 + 1，同日同人同签 |
| 桃花运势 | `POST /api/taohua` | 本命桃花位/旺衰月/流年桃花（2026 丙午年专属数据） |
| 红线测算 | `POST /api/hongxian` | 日支配偶宫正缘画像 + 未来八年缘分时间窗（桃花年/正缘信号/红鸾天喜） |

## 运行

```bash
python3 server.py            # 默认 0.0.0.0:8300
PORT=9000 python3 server.py  # 自定义端口
```

打开 `http://127.0.0.1:8300/` 即可。

## 接口示例

```bash
curl -X POST http://127.0.0.1:8300/api/hehun \
  -H 'Content-Type: application/json' \
  -d '{"a_date":"1990-05-15","a_hour":12,"a_sex":"男","b_date":"1992-03-08","b_hour":10,"b_minute":30,"b_sex":"女"}'

curl -X POST http://127.0.0.1:8300/api/qiuqian \
  -H 'Content-Type: application/json' \
  -d '{"name":"小明","question":"何时能遇到对的人？"}'
```

所有接口出错返回 `{"error": "..."}` 与对应 HTTP 状态码（400/404/500）。

## 项目结构

```
yinyuan-web/
├── server.py           # 标准库 HTTP 服务 + 6 个 JSON API
├── engine/
│   ├── pai_pan.py      # 四柱排盘引擎（节气/农历天文级，源自 jinchenma94/bazi-skill, MIT）
│   ├── common.py       # 干支/五行/纳音等公共数据
│   ├── zodiac.py       # 生肖配对
│   ├── hehun.py        # 八字合婚评分
│   ├── sticks_data.py  # 100 支姻缘签诗原文
│   ├── qiuqian.py      # 求签
│   ├── taohua.py       # 桃花运势
│   ├── ziwei.py        # 紫微夫妻宫（简化安星）
│   └── hongxian.py     # 红线测算
└── static/             # 前端（原生 HTML/CSS/JS，宣纸底 + 中国红）
```

## 设计说明

- 宣纸暖白底 + 中国红点缀，宋体大标题，简约大气
- 首页双生日合婚快捷入口 + 六大模式卡片 + 求签专区 + 报告墙
- 移动端自适应

## 免责声明

**娱乐为主，理性参考。** 分数与签诗只是参考工具，不是判决书；姻缘天注定，幸福自己争。

## 致谢

- [Ming-H/yinyuan-skills](https://github.com/Ming-H/yinyuan-skills) — 六大测算模式与全部知识库规则
- [jinchenma94/bazi-skill](https://github.com/jinchenma94/bazi-skill) — 天文级四柱排盘引擎
