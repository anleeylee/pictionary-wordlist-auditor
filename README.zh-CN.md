# Pictionary 词库审计器（Pictionary Wordlist Auditor）

> **审计主题化 Pictionary 词库——库内/跨库去重、商标/品牌名扫描、敏感词过滤、长度与难度校验，并自动生成审计日志。**

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![CLI](https://img.shields.io/badge/CLI-ready-4B8BBE)](wordlist_auditor.py)
[![No dependencies](https://img.shields.io/badge/deps-stdlib%20only-blueviolet)](requirements.txt)

---

## 相关链接

- 🎲 **在线工具体验：** [Pictionary Word Generator — 免费 7000+ 画画提示词](https://pictionarywordgenerators.com/)
- 📄 **简单词页面：** [Easy Pictionary Words — 简单有趣的画画提示词](https://pictionarywordgenerators.com/easy-pictionary-words)
- 英文版说明：[README.md](README.md)

---

## 这个工具做什么

Pictionary 词库好不好，全看卫生程度。重复提示词、混入的品牌名、边缘词汇、
单字符占位符、难度标签前后不一——这些会悄悄毁掉游戏之夜；一旦词库发布在
网站上，还会让公开的数字难堪。

**Pictionary Wordlist Auditor 是词库上线前的质量闸门。** 传入一个或多个
词库 JSON 文件，它会执行五项检查，并输出带时间戳的审计日志
（JSON + 可读 Markdown）：

1. **去重** —— 库内重复提示词，以及**跨库**重复（主题库不能悄悄把同样的
   40 个词推两遍）。
2. **品牌** —— 商标/品牌名扫描，内置约 110 条黑名单（饮料、科技、玩具、
   汽车、快餐、影视 IP），确保词库永远不会把 "Frisbee"、"Lego"、
   "Star Wars" 之类当成可画提示词发布。
3. **敏感词** —— 面向家庭与课堂词库的不适宜词过滤（酒精、毒品、武器、
   成人内容、脏话）。
4. **长度** —— 过短（`X`）或过长（50 字符的小作文）的提示词。
5. **难度** —— 用文档化的分级启发式重新校验每条 easy/medium/hard 标签，
   不一致即标记。

每次运行都会产出**审计日志**（JSON + Markdown），包含每项 pass/warn/fail
结论与受影响提示词的完整清单——网站公布的词库数字与质量闸门因此永远可审计。

## 为什么重要

当你在 [Pictionary Word Generator](https://pictionarywordgenerators.com/)
这类网站上发布词库时，用户看到的数字（"7000+ 提示词"、"24 个主题库"）
就成了会被核验的主张。审计器让流水线可复现：同样的五项检查，每个词库、
每次运行都一致地执行，报告就是证据。

它还能抓住手工清单隐藏数月的问题：

- 同一个词出现在两个主题里（玩家跨轮次遇到重复）；
- 会被法务盯上的商标玩具名；
- 漏审的单字符占位符；
- 标着 "hard" 但每个小孩都认识的词。

## 安装

```bash
git clone https://github.com/anleeylee/pictionary-wordlist-auditor.git
cd pictionary-wordlist-auditor

# 无需 pip install —— 仅标准库
python wordlist_auditor.py --help
```

## 用法

```bash
# 审计一个词库
python wordlist_auditor.py --libraries examples/libs/space.json

# 一次审计多个词库（含跨库去重检查）
python wordlist_auditor.py \
  --libraries examples/libs/space.json examples/libs/with-issues.json \
  --report reports/audit-report.md \
  --json-report reports/audit-report.json
```

输出默认写入 `audit-report.md`；加 `--json-report` 可同时输出结构化日志。
每次运行可追加自定义黑名单：

```bash
python wordlist_auditor.py --libraries my-lib.json \
  --brands my-brands.json \
  --sensitive my-sensitive.json
```

其中每个文件是普通 JSON 字符串数组。

### 参数

| 参数 | 默认 | 说明 |
|---|---|---|
| `--libraries` | （必填） | 一个或多个词库 JSON 文件 |
| `--report` | `audit-report.md` | Markdown 审计日志输出 |
| `--json-report` | — | 可选 JSON 审计日志输出 |
| `--brands` | 内置列表 | 额外品牌名黑名单文件 |
| `--sensitive` | 内置列表 | 额外敏感词黑名单文件 |
| `--strict` | 关闭 | 把难度警告视为失败 |

## 审计日志示例

```
# Pictionary Wordlist Audit Report
- Libraries audited: `2`
- Total entries: `29`
- **Verdict: FAIL**

| Check | Issues |
|---|---|
| duplicates | 1 |
| brands | 1 |
| sensitive | 1 |
| length | 2 |
| difficulty | 5 |
```

完整日志会列出每个受影响提示词及其索引、检查项与说明。

## 词库结构约定

```json
{
  "theme": "space",
  "title": "Space",
  "entries": [
    {"prompt": "Moon", "category": "Nature", "difficulty": "easy"}
  ]
}
```

这正是 [Pictionary Wordlist Generator](https://github.com/anleeylee/pictionary-wordlist-generator)
产出的结构。

## 测试

```bash
python -m unittest discover -s tests -v
```

覆盖：归一化、难度启发式、库内/跨库去重、品牌/敏感词过滤、长度校验、
自定义黑名单、全局结论与 Markdown 渲染。

## 许可

MIT——可自由使用与扩展，请保留署名。你生成的审计日志是你的证据，工具只是让它可复现。
