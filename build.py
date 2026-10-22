# -*- coding: utf-8 -*-
import re, markdown, html, os, shutil, json
import yaml
from datetime import date

BASE_URL = "https://llmknowledge.org"
# 章末区块的联系邮箱（Cloudflare Email Routing 转发，只收不发）
CONTACT_EMAIL = "koe@llmknowledge.org"
# IndexNow（Bing / Yandex 等）验证密钥：构建时写成 site/<key>.txt，ping_indexnow.py 用它推送 URL
INDEXNOW_KEY = "61017d3005468b906e007dfefd16e7af"

# ===== 语言配置：新增语言只需在这里加一个条目 =====
# links: 从本语言页面跳到目标语言同一章节页面的相对路径前缀
LANGS = {
    "zh": dict(
        lang_code="zh-CN",
        src="content/理解现代LLM系统_从RAG到全景.md",
        outdir="site/zh",
        url_prefix="/zh/",
        book_title="理解现代大语言模型系统-从RAG到全景",
        book_sub="写给泛技术人群的概念地图：从碎片认知到系统脉络",
        page_title="理解现代大语言模型系统-从RAG到全景 · 写给泛技术人群的概念地图：从碎片认知到系统脉络",
        toc_label="目录",
        menu_aria="打开目录",
        prev_label="上一章",
        next_label="下一章",
        sidenote_html='全文免费在线阅读。另有排版好的中英双语 <a href="%s">PDF / EPUB 版本</a>，在 Gumroad 有售。<br><a href="https://github.com/koemia/llmknowledge" data-umami-event="github-star-click" data-umami-event-position="sidebar-zh">⭐ 在 GitHub 上点个 star</a>',
        foot_meta="第 2 版 · 2026 年 10 月",
        switch_label="中文",
        theme_label="切换日间 / 夜间",
        pagetoc_label="本页目录",
        links={"zh": "", "en": "../"},
    ),
    "en": dict(
        lang_code="en",
        src="content/理解现代LLM系统_从RAG到全景.en.md",
        outdir="site",
        url_prefix="/",
        book_title="Understanding Modern LLM Systems: A Field Guide to RAG, Agents, and Beyond",
        book_sub="A concept map from fragmented knowledge to systemic understanding",
        page_title="Understanding Modern LLM Systems: A Field Guide to RAG, Agents, and Beyond · A concept map from fragmented knowledge to systemic understanding",
        toc_label="Contents",
        menu_aria="Open menu",
        prev_label="Previous",
        next_label="Next",
        sidenote_html='Free to read online in full. A typeset <a href="%s">PDF + EPUB edition</a>, in English and Chinese, is also available on Gumroad.<br><a href="https://github.com/koemia/llmknowledge" data-umami-event="github-star-click" data-umami-event-position="sidebar-en">⭐ Star it on GitHub</a>',
        foot_meta="2nd Edition · October 2026",
        switch_label="EN",
        theme_label="Switch day / night",
        pagetoc_label="On this page",
        links={"zh": "zh/", "en": ""},
    ),
}

# ===== llms.txt / sitemap 用的每章一句话简介（与 README 表格口径一致）=====
DESCRIPTIONS = {
    "en": {
        "preface": "What problem is this system solving?",
        "ch1": "The RAG pipeline — how a question becomes a cited answer",
        "ch2": "Adapting a model — fine-tuning vs. RAG, and what each one fixes",
        "ch3": "Four core mechanisms — embeddings, retrieval, serving, architecture",
        "ch4": "Agents — function calling, MCP, memory, and where they break",
        "ch5": "A compliance view — where confidential data actually goes",
        "ch6": "A security view — prompt injection and other risks, from the attacker's side",
        "ch7": "Beyond RAG — the landscape, organized by what the model is missing",
        "appendix": "Toolkit overview",
        "cheatsheet": "The whole guide on one page",
    },
    "zh": {
        "preface": "这个系统在解决什么问题",
        "ch1": "RAG 核心流程——一个问题如何变成带出处的回答",
        "ch2": "模型适配——微调与 RAG，各自解决什么问题",
        "ch3": "四个核心机制——嵌入、检索、推理服务、系统架构",
        "ch4": "Agent——函数调用、MCP、记忆，以及它会在哪里出问题",
        "ch5": "合规视角——机密数据到底去了哪里",
        "ch6": "安全视角——提示注入与其他风险，换成攻击者的角度再看一遍",
        "ch7": "RAG 之外——按「模型缺什么」组织的全景",
        "appendix": "工具库概览",
        "cheatsheet": "整本书浓缩在一页里",
    },
}

# ===== SEO：每页 <title> 与 meta description =====
# title 写成搜索词会命中的说法（章名 + 关键词），后缀统一挂书名短称；首页（入口页 home）单独写、不加后缀。
# description 控制在英文 ~150 字符、中文 ~80 字以内，超出部分搜索结果会截断。
TITLE_SUFFIX = {
    "en": " | LLM Systems Field Guide",
    "zh": " | 理解现代大语言模型系统",
}

PAGE_TITLES = {
    "en": {
        "home": "Understanding Modern LLM Systems: A Free Field Guide to RAG, Agents, and Beyond",
        "preface": "Before We Begin: What Problem Is This Whole System Actually Solving?",
        "ch1": "How RAG Works: The 8-Step Pipeline, Explained",
        "ch2": "Fine-Tuning vs. RAG: What Each One Actually Fixes",
        "ch3": "Embeddings, Vector Search & LLM Serving Explained",
        "ch4": "AI Agents Explained: ReAct, Function Calling, MCP, Memory",
        "ch5": "RAG Compliance: Where Confidential Data Actually Goes",
        "ch6": "LLM Security: Prompt Injection and Denial-of-Wallet",
        "ch7": "Beyond RAG: Long Context, Agents, Reasoning Models, Fine-Tuning",
        "appendix": "RAG & Agent Toolkit: Vector DBs, Rerankers, Frameworks",
        "cheatsheet": "LLM Systems Cheat Sheet: Core Concepts on One Page",
    },
    "zh": {
        "home": "理解现代大语言模型系统：从 RAG 到 Agent 的概念地图（免费在线阅读）",
        "preface": "开始之前：这整套系统到底在解决什么问题？",
        "ch1": "RAG 原理：一个问题怎么变成带引用的答案（八步流程）",
        "ch2": "微调还是 RAG？模型适配的三种手段各解决什么问题",
        "ch3": "Embedding、向量检索、KV Cache：大模型系统的四个核心机制",
        "ch4": "AI Agent 智能体详解：ReAct、函数调用、MCP 与记忆",
        "ch5": "RAG 合规：机密数据在大模型系统里流向哪里",
        "ch6": "大模型安全：提示注入与烧钱攻击",
        "ch7": "跳出 RAG：长上下文、Agent、推理模型、微调怎么选",
        "appendix": "RAG 与 Agent 工具库：向量数据库、重排模型、开发框架",
        "cheatsheet": "大模型系统速记卡片：核心概念一页复习",
    },
}

META_DESCRIPTIONS = {
    "en": {
        "home": ("A free, book-length guide to how modern LLM systems work — RAG, fine-tuning, "
                 "agents, compliance, and security. No math or coding background needed."),
        "preface": ("Why a general-purpose model can't answer questions about your company's own documents, "
                    "and how RAG solves it: look up the material first, then answer from it."),
        "ch1": ("The full RAG pipeline in eight steps — from query rewriting and hybrid retrieval "
                "to guardrails and citations — plus offline indexing and the four feedback loops."),
        "ch2": ("Knowledge gap, behavior gap, comprehension gap: when to use RAG, fine-tuning (SFT, RFT, LoRA), "
                "or continued pretraining — and why fine-tuning can't teach new facts."),
        "ch3": ("How embeddings, vector search (HNSW, IVF, DiskANN), hybrid search, reranking, KV cache, "
                "prefill vs. decode, and continuous batching actually work."),
        "ch4": ("When you need an agent and when you don't. The ReAct loop, function calling, MCP, "
                "memory, agentic RAG — and the costs and failure modes that come with them."),
        "ch5": ("Where confidential data goes in a RAG system: at rest, in transit, in use and logs, where it lives "
                "and who can see it. Plus embedding inversion and soft deletion."),
        "ch6": ("LLM security from the attacker's side: prompt injection, jailbreaks, and denial-of-wallet "
                "attacks, and why defense has to live in the system, not the model."),
        "ch7": ("Prompting, long context, RAG, agents, reasoning models, fine-tuning — a map of LLM "
                "system patterns, organized by what the model is missing for the task."),
        "appendix": ("Common 2026 tools for each pipeline stage: document parsing, embedding models, "
                     "vector databases, rerankers, RAG and agent frameworks, evaluation."),
        "cheatsheet": ("The core takeaways of the whole guide on one page: embeddings, retrieval, ANN, "
                       "KV cache, agents, compliance, security, and the full landscape."),
    },
    "zh": {
        "home": "免费在线阅读的大模型系统入门书：RAG、微调、Agent、合规与安全，写给产品经理、项目经理、售前、创业者和需要对接 AI 项目的管理者，不需要数学或编程基础。",
        "preface": "通用大模型没学过你们公司的资料，所以要先查资料、再让模型基于资料回答，这就是 RAG（检索增强生成），也是这本书的主线。",
        "ch1": "用八个步骤讲清 RAG 全流程：问题改写、混合检索、重排、组装提示词、生成、护栏、引用、日志，外加离线索引和四个回环。",
        "ch2": "模型不知道、不会说、听不懂：什么时候用 RAG，什么时候用微调（SFT、RFT、LoRA）或继续预训练，以及为什么微调学不会新知识。",
        "ch3": "Embedding 怎么表示语义，向量检索（HNSW、IVF、DiskANN）与混合检索、重排怎么配合，KV Cache、prefill 与 decode、连续批处理怎么工作。",
        "ch4": "什么时候需要 Agent，什么时候不需要。ReAct 循环、函数调用、MCP、记忆、Agentic RAG，以及随之而来的代价和风险。",
        "ch5": "机密数据在 RAG 系统里的四种状态：静态、传输、使用与日志、落地与权限。向量可逆、软删除、脱敏和权限丢失这些容易忽略的风险。",
        "ch6": "换成攻击者的角度看大模型安全：提示注入、越狱和烧钱攻击，以及为什么防御只能落在系统层，而不是模型本身。",
        "ch7": "提示词、长上下文、RAG、Agent、推理模型、微调：按「模型缺什么」整理的大模型应用全景，帮你判断该选哪一种。",
        "appendix": "按流程环节整理的 2026 年常用工具：文档解析、Embedding 模型、向量数据库、重排模型、RAG 与 Agent 框架、评估。",
        "cheatsheet": "整本书的核心要点浓缩成一页：Embedding、检索、ANN、KV Cache、Agent、合规、安全与全景，适合最后复习。",
    },
}


def page_title_for(lang_key, sec_id):
    t = PAGE_TITLES[lang_key][sec_id]
    return t if sec_id == "home" else t + TITLE_SUFFIX[lang_key]


def head_meta_for(lang_key, cfg, sec_id):
    title = html.escape(page_title_for(lang_key, sec_id), quote=True)
    desc = html.escape(META_DESCRIPTIONS[lang_key][sec_id], quote=True)
    url = url_for(cfg, sec_id)
    locale = "zh_CN" if lang_key == "zh" else "en_US"
    return "\n".join([
        '<meta name="description" content="%s">' % desc,
        '<meta property="og:type" content="%s">' % ("website" if sec_id == "home" else "article"),
        '<meta property="og:site_name" content="%s">' % html.escape(cfg["book_title"], quote=True),
        '<meta property="og:title" content="%s">' % title,
        '<meta property="og:description" content="%s">' % desc,
        '<meta property="og:url" content="%s">' % url,
        '<meta property="og:locale" content="%s">' % locale,
        '<meta property="og:image" content="%s">' % og_image_url(lang_key),
        '<meta property="og:image:width" content="2400">',
        '<meta property="og:image:height" content="1260">',
        '<meta property="og:image:alt" content="%s">' % html.escape(cfg["book_title"], quote=True),
        '<meta name="twitter:card" content="summary_large_image">',
    ])


# 社交分享图（2400×1260 即 1200×630 的 2 倍，由封面生成，JPEG 高质量不降采样）：content/social/ 构建时原样复制到 site/social/
SOCIAL_DIR = "content/social"


def og_image_url(lang_key):
    # ?v=N：换图后加 1，让 LinkedIn、X 等平台放弃缓存、重新抓取
    return "%s/social/og-%s.jpg?v=2" % (BASE_URL, lang_key)


# 付费出站短链：每个入口位置一条固定短链，UTM/最终跳转目标在短链服务那端配置，
# 网站代码这里只放短链本身，不拼接任何 query string。
SHORT_LINKS = {
    "en": {
        "sidebar": "https://ymjr.de/llmbook-en-sidebar",
        "home": "https://ymjr.de/llmbook-en-home",
        "end": "https://ymjr.de/llmbook-en-end",
        "preface": "https://ymjr.de/llmbook-en-preface",
        "ch7": "https://ymjr.de/llmbook-en-ch7",
        "appendix": "https://ymjr.de/llmbook-en-appendix",
        "cheatsheet": "https://ymjr.de/llmbook-en-cheat",
        "answers": "https://ymjr.de/llmbook-en-answers",
    },
    "zh": {
        "sidebar": "https://ymjr.de/llmbook-zh-sidebar",
        "home": "https://ymjr.de/llmbook-zh-home",
        "end": "https://ymjr.de/llmbook-zh-end",
        "ch7": "https://ymjr.de/llmbook-zh-ch7",
        "appendix": "https://ymjr.de/llmbook-zh-appendix",
        "cheatsheet": "https://ymjr.de/llmbook-zh-cheat",
    },
}

LANGS["zh"]["sidenote_html"] = LANGS["zh"]["sidenote_html"] % SHORT_LINKS["zh"]["sidebar"]
LANGS["en"]["sidenote_html"] = LANGS["en"]["sidenote_html"] % SHORT_LINKS["en"]["sidebar"]

# 章末区块首句：三页各不相同，其余段落一致
ENDNOTE_LEAD = {
    "en": {
        "ch7": ("That was the last chapter — the appendix and quick reference come after. "
                "The whole guide is here, free, and will stay that way."),
        "appendix": ("One page left after this: the quick reference card. "
                     "The whole guide is here, free, and will stay that way."),
        "cheatsheet": "You've reached the end. The whole guide is here, free, and will stay that way.",
    },
    "zh": {
        "ch7": "正文到此结束，后面还有附录和速记卡片。网页版永久免费。",
        "appendix": "附录到此结束，后面还有一页速记卡片。网页版永久免费。",
        "cheatsheet": "全文到此结束，网页版永久免费。",
    },
}


def endnote_html(lang_key, sec_id):
    lead = ENDNOTE_LEAD[lang_key][sec_id]
    link = SHORT_LINKS[lang_key][sec_id]
    if lang_key == "en":
        return (
            '<div class="endnote">\n'
            "  <p>%s</p>\n"
            "  <p>If you'd rather have it off the browser: a typeset PDF and EPUB edition, "
            "in English and Chinese — four files in one download.</p>\n"
            '  <p><a href="%s">Get the PDF + EPUB on Gumroad →</a></p>\n'
            '  <p class="note-fine">Corrections, feedback, or trouble paying? Write to '
            '<a href="mailto:%s">%s</a>.</p>\n'
            "</div>" % (lead, link, CONTACT_EMAIL, CONTACT_EMAIL)
        )
    return (
        '<div class="endnote">\n'
        "  <p>%s</p>\n"
        "  <p>想把它从浏览器里拿出来：排版好的 PDF 与 EPUB，中英两版——四个文件一次下载。"
        "付款支持境外银行卡与 PayPal。</p>\n"
        '  <p><a href="%s">在 Gumroad 获取 PDF + EPUB →</a></p>\n'
        '  <p class="note-fine">有勘误、反馈，或者付款上遇到问题，可以写信到 '
        '<a href="mailto:%s">%s</a>。</p>\n'
        "</div>" % (lead, link, CONTACT_EMAIL, CONTACT_EMAIL)
    )


def fname(sec_id):
    return "index.html" if sec_id == "home" else sec_id + ".html"


def slug(sec_id):
    """对外 URL 不带 .html：Cloudflare Pages 会把 /chN.html 308 到 /chN，
    链接直接写无后缀形式，省掉爬虫一次重定向。磁盘文件名仍由 fname() 决定。"""
    return "" if sec_id == "home" else sec_id


def rel_href(prefix, sec_id):
    """页面内相对链接；入口页落到目录本身（./ 或 ../ 或 zh/）。"""
    return (prefix + slug(sec_id)) or "./"


def url_for(cfg, sec_id):
    """入口页用干净的 / 或 /zh/，其余页面用 /preface、/chN（无 .html 后缀）。"""
    return BASE_URL + cfg["url_prefix"] + slug(sec_id)


def parse_sections(src_path):
    raw = open(src_path, encoding="utf-8").read()
    lines = raw.split("\n")
    sections = []
    cur = None
    for ln in lines:
        if ln.startswith("## "):
            if cur is not None:
                sections.append(cur)
            cur = {"title": ln[3:].strip(), "body": []}
        else:
            if cur is not None:
                cur["body"].append(ln)
    if cur is not None:
        sections.append(cur)
    return sections


def classify_structural(sections):
    """按章节在文件中的位置（而非标题文字）判断类型，语言无关。
    约定：第 1 节 = 前言，最后 2 节 = 附录 / 速记，中间全部是编号章节。
    要求各语言源文件的章节数量、顺序严格一一对应。"""
    n = len(sections)
    for i, s in enumerate(sections):
        s["is_end"] = i >= n - 3
        if i == 0:
            s.update(id="preface", eyebrow="PREFACE", numeral="", kind="front")
        elif i == n - 2:
            s.update(id="appendix", eyebrow="APPENDIX", numeral="", kind="back")
        elif i == n - 1:
            s.update(id="cheatsheet", eyebrow="QUICK REFERENCE", numeral="", kind="back")
        else:
            s.update(id=f"ch{i}", eyebrow=f"CHAPTER {i:02d}", numeral=f"{i:02d}", kind="chapter")
        # 侧栏短标题：从标题里按标点通用切分，不依赖具体语言的文字
        title = s["title"]
        nav = re.split(r"[:：]", title, maxsplit=1)[0].strip()
        if nav == title:
            nav = re.split(r"[(（]", title, maxsplit=1)[0].strip()
        s["nav"] = nav


# 配色、字体等 CSS 变量：章节页和入口页共用
ROOT_CSS = r''':root{
  --paper:#201E1A;          /* 页面外底色·深炭（内容之外） */
  --column:#F5EFE4;         /* 阅读栏·浮起的奶油纸 */
  --ink:#2A2924;            /* 暖炭黑·侧栏与标题 */
  --ink-line:#3A392F;
  --text:#4A4843;           /* 正文·中灰（调浅） */
  --muted:#79746A;          /* 次要文字 */
  --accent:#43836A;         /* 松绿（调淡）·链接与高亮 */
  --accent-ink:#2C6249;
  --accent-soft:#DCE6DD;    /* 沙绿浅色·悬停底 */
  --rule:#DDD5C4;           /* 发丝分隔线 */
  --tint:#E4EBE2;           /* 沙绿浅色·表头/引用底 */
  --tint-line:#CAD8CB;
  --code-bg:#E7E0D0;
  --sans:"PingFang SC","Microsoft YaHei","Hiragino Sans GB","Noto Sans CJK SC","Source Han Sans SC","WenQuanYi Micro Hei",sans-serif;
  --serif:"Spectral",Georgia,"Times New Roman",serif;
  --mono:"SF Mono",ui-monospace,"JetBrains Mono","Cascadia Code",Menlo,Consolas,monospace;
  --col-w:720px;
  --side-w:300px;
}
/* 英文页正文用 Inter（与 PDF 一致），中文字体留在后面兜底 */
:root:lang(en){
  --sans:"Inter",-apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
}'''


# Google Fonts：两种语言都用 Spectral 做衬线标题；英文页另加 Inter 做正文
FONT_FAMILIES = {
    "en": "family=Inter:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&family=Spectral:ital,wght@0,400;0,500;0,600;1,400;1,500",
    "zh": "family=Spectral:ital,wght@0,400;0,500;0,600;1,400;1,500",
}


def fonts_link(lang_key):
    return ('<link href="https://fonts.googleapis.com/css2?%s&display=swap" rel="stylesheet">'
            % FONT_FAMILIES[lang_key])


# 统计脚本：章节页和入口页共用
ANALYTICS_HTML = r'''<script defer src="https://cloud.umami.is/script.js" data-website-id="398cb9ae-aed6-4239-a477-6c3ec00120a0" data-domains="llmknowledge.org"></script>
<!-- Cloudflare Web Analytics -->
<script defer src='https://static.cloudflareinsights.com/beacon.min.js' data-cf-beacon='{"token": "1c605389c0f74b35815e02350867239b"}'></script>
<!-- End Cloudflare Web Analytics -->'''


TEMPLATE = r'''<!DOCTYPE html>
<html lang="__LANG__">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="google-site-verification" content="N-Eq_2c5aG0rHDGOkAvz7jPIxSpWsmKo1mIh6O4yZ1U">
<title>__PAGE_TITLE__</title>
__HEAD_META__
__CANONICAL__
__HREFLANG__
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
__FONTS_LINK__
<style>
__ROOT_CSS__
/* 日间 / 夜间：默认跟随系统；侧栏按钮可手动切换，选择存在 localStorage */
:root{--sidebar:#2A2924;--strong:#2E2C26;--code-ink:#3A3226;--on-accent:#fff;--fig-bg:transparent;--fig-pad:0;color-scheme:light}
:root[data-theme="dark"]{--paper:#141311;--column:#22211D;--ink:#ECE5D5;--text:#C9C2B3;--muted:#968F80;--accent:#7FB79C;--accent-ink:#A3D2BA;--accent-soft:#2A3A31;--rule:#38362F;--tint:#28302A;--tint-line:#3B4A40;--code-bg:#2F2D27;--sidebar:#1C1B18;--strong:#EFE9DB;--code-ink:#E2DACA;--on-accent:#14201A;--fig-bg:#F3EEE3;--fig-pad:14px;color-scheme:dark}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--paper:#141311;--column:#22211D;--ink:#ECE5D5;--text:#C9C2B3;--muted:#968F80;--accent:#7FB79C;--accent-ink:#A3D2BA;--accent-soft:#2A3A31;--rule:#38362F;--tint:#28302A;--tint-line:#3B4A40;--code-bg:#2F2D27;--sidebar:#1C1B18;--strong:#EFE9DB;--code-ink:#E2DACA;--on-accent:#14201A;--fig-bg:#F3EEE3;--fig-pad:14px;color-scheme:dark}}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{
  margin:0;background:var(--paper);color:var(--text);
  font-family:var(--sans);font-size:17px;line-height:1.85;
  -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility;
}
a{color:var(--accent);text-decoration:none}
a:hover{color:var(--accent-ink)}

/* 顶部阅读进度条 */
#progress{position:fixed;top:0;left:0;height:3px;width:0;
  background:var(--accent);z-index:60;transition:width .1s linear}

/* ---------- 侧栏 ---------- */
.sidebar{
  position:fixed;top:0;left:0;width:var(--side-w);height:100vh;
  background:var(--sidebar);color:#DBD5C7;display:flex;flex-direction:column;
  z-index:50;border-right:1px solid #17160F;
}
.brand{padding:34px 30px 22px;border-bottom:1px solid rgba(255,255,255,.09)}
.brand .kicker{font-family:var(--serif);font-size:12px;letter-spacing:.32em;
  text-transform:uppercase;color:#A89F8C;font-weight:600;margin-bottom:12px}
.brand .bt{margin:0;font-weight:700;font-size:23px;line-height:1.3;color:#F5F0E4;
  letter-spacing:.01em}
.brand .bt a{color:inherit}
.brand .bt::after{content:"";display:block;width:46px;height:2px;
  background:var(--accent);margin-top:13px;border-radius:2px}
.brand .sub{font-family:var(--serif);font-style:italic;font-size:15px;
  color:#A9AF9E;margin-top:12px}

.lang-switch{margin-top:18px;display:inline-flex;border:1px solid rgba(255,255,255,.2);
  border-radius:999px;overflow:hidden;font-size:13px}
.lang-switch a{background:transparent;border:0;color:#A9AF9E;
  padding:5px 14px;cursor:pointer;font-family:var(--serif);letter-spacing:.05em;display:inline-block}
.lang-switch a[aria-current="page"]{background:var(--accent);color:var(--on-accent)}

.toc{flex:1;overflow-y:auto;padding:16px 16px 8px}
.toc .toc-h{font-size:11px;letter-spacing:.22em;text-transform:uppercase;
  color:#8C877A;padding:8px 14px 10px;font-family:var(--serif);font-weight:600}
.nav-item{display:flex;align-items:baseline;gap:12px;padding:9px 14px;
  border-radius:8px;color:#CAC3B3;transition:background .15s,color .15s;line-height:1.4}
.nav-item:hover{background:rgba(255,255,255,.06);color:#F5F0E4}
.nav-mark{font-family:var(--serif);font-size:14px;color:#8C877A;min-width:22px;
  font-variant-numeric:tabular-nums;flex:none}
.nav-label{font-size:14.5px}
.nav-item.active{background:rgba(67,131,106,.26);color:#EAF1E9}
.nav-item.active .nav-mark{color:#7FB79C}

.side-foot{padding:16px 22px 22px;border-top:1px solid rgba(255,255,255,.09)}
.side-foot .note{font-size:12px;color:#948E80;line-height:1.6;font-family:var(--serif);font-style:italic}
.side-foot .note a{color:inherit;text-decoration:underline;text-decoration-color:rgba(148,142,128,.5)}
.side-foot .note a:hover{color:#DBD5C7;text-decoration-color:#DBD5C7}

/* ---------- 主区 ---------- */
.main{margin-left:var(--side-w);display:flex;justify-content:center;padding:0 40px}
.reader{width:100%;max-width:var(--col-w);margin:0 auto;padding:76px 0 40px}

.chapter{background:var(--column);border:1px solid var(--rule);
  border-radius:4px;padding:56px 60px 40px;margin-bottom:34px;
  box-shadow:0 22px 48px -30px rgba(0,0,0,.6)}
.chapter:first-child{margin-top:0}

.ch-head{display:flex;gap:22px;align-items:flex-start;
  padding-bottom:26px;margin-bottom:30px;border-bottom:1px solid var(--rule)}
.ch-numeral{font-family:var(--serif);font-size:60px;line-height:.9;
  color:var(--accent);font-weight:500;flex:none;font-variant-numeric:tabular-nums;
  margin-top:-4px}
.eyebrow{font-family:var(--serif);font-weight:600;font-size:12.5px;letter-spacing:.24em;
  text-transform:uppercase;color:var(--accent-ink);margin-bottom:12px}
.ch-title{margin:0;font-size:29px;line-height:1.4;font-weight:600;color:var(--ink);
  letter-spacing:.005em}

/* 正文排版 */
.doc{color:var(--text)}
.doc>*:first-child{margin-top:0}
.doc h2,.doc h3{font-size:20px;font-weight:600;color:var(--ink);margin:44px 0 14px;
  line-height:1.5;letter-spacing:.005em;
  padding-left:14px;border-left:3px solid var(--accent)}
.doc h4{font-size:17px;font-weight:600;color:var(--ink);margin:30px 0 10px}
.doc p{margin:0 0 18px}
.doc strong{font-weight:600;color:var(--strong)}
.doc em{font-style:normal;background:linear-gradient(transparent 62%,var(--accent-soft) 62%);
  padding:0 1px}
.doc ul,.doc ol{margin:0 0 20px;padding-left:1.35em}
.doc li{margin:0 0 9px;padding-left:.2em}
.doc li::marker{color:var(--accent)}

/* 行内代码与术语 */
.doc code{font-family:var(--mono);font-size:.86em;background:var(--code-bg);
  padding:.12em .4em;border-radius:4px;color:var(--code-ink)}
.doc pre{background:#26251F;color:#E9E3D5;padding:18px 20px;border-radius:6px;
  overflow-x:auto;margin:0 0 20px;font-size:14px;line-height:1.7}
.doc pre code{background:none;color:inherit;padding:0}

/* 引用 / 注释块 —— 招牌样式 */
.doc blockquote{margin:24px 0;padding:20px 24px;background:var(--column);
  border:1px solid var(--tint-line);border-left:4px solid var(--accent);
  border-radius:4px;position:relative}
.doc blockquote::before{content:"注";position:absolute;top:-11px;left:18px;
  background:var(--accent-ink);color:var(--on-accent);font-family:var(--serif);font-size:11px;
  letter-spacing:.12em;padding:2px 9px;border-radius:3px}
.doc blockquote>*:first-child{margin-top:0}
.doc blockquote>*:last-child{margin-bottom:0}
.doc blockquote p{margin-bottom:12px}

/* 表格 */
.table-wrap{overflow-x:auto;margin:0 0 24px;
  border:1px solid var(--rule);border-radius:6px}
.doc table{border-collapse:collapse;width:100%;font-size:15px;line-height:1.65;
  background:var(--column)}
.doc thead th{background:var(--tint);color:var(--ink);font-weight:600;
  text-align:left;padding:12px 16px;border-bottom:1px solid var(--tint-line);
  white-space:nowrap;font-size:14px;letter-spacing:.02em}
.doc tbody td{padding:12px 16px;border-bottom:1px solid var(--rule);
  vertical-align:top}
.doc tbody tr:last-child td{border-bottom:0}
.doc tbody tr:nth-child(even){background:rgba(42,41,36,.02)}
.doc tbody td:first-child{min-width:5.5em}   /* 第一栏别被挤成一字一行 */
.doc:lang(zh) tbody td:first-child{min-width:4.5em}

/* 内容长的表：一行一张卡片（由 build.py 的 layout_tables 生成） */
.row-cards{margin:8px 0 28px}
.rc{border:1px solid var(--rule);border-radius:6px;padding:16px 20px 6px;margin:0 0 14px;
  background:rgba(42,41,36,.025)}
.rc-t{margin:0 0 10px;font-weight:600;color:var(--ink);line-height:1.5}
.rc-f{margin:0 0 12px}
.rc-l,.cmp-f .rc-l,.doc .table-wrap td[data-label]::before{display:block;font-family:var(--serif);font-size:12px;
  letter-spacing:.14em;text-transform:uppercase;color:var(--accent-ink);font-weight:600;margin-bottom:2px}
.doc:lang(zh) .rc-l,.doc:lang(zh) .table-wrap td[data-label]::before{font-family:var(--sans);
  letter-spacing:.04em;font-size:12.5px}
/* 对比表（表头第一格空着、两到三栏）：每栏一张卡片并排，窄屏上下排 */
.compare{display:grid;grid-template-columns:repeat(var(--cmp-n,2),minmax(0,1fr));gap:14px;margin:8px 0 28px}
.cmp-col{border:1px solid var(--rule);border-radius:6px;padding:16px 18px 6px;background:rgba(42,41,36,.025)}
.cmp-h{font-weight:600;color:var(--ink);font-size:18px;margin:0 0 12px;padding-bottom:8px;
  border-bottom:2px solid var(--accent)}
.cmp-f{margin:0 0 12px;font-size:15.5px;line-height:1.7}
@media (max-width:640px){
  .compare{grid-template-columns:minmax(0,1fr)}
  .cmp-f{font-size:inherit;line-height:inherit}
}
/* 其余表格：手机上同样叠成卡片，栏名做小标签 */
.doc .table-wrap td[data-label]::before{content:none}
@media (max-width:560px){
  .doc .table-wrap{border:0;overflow:visible}
  .doc .table-wrap table,.doc .table-wrap tbody,.doc .table-wrap tr,.doc .table-wrap td{display:block;width:auto}
  .doc .table-wrap table{font-size:inherit;line-height:inherit;background:none}
  .doc .table-wrap thead{display:none}
  .doc .table-wrap tr,.doc .table-wrap tbody tr:nth-child(even){border:1px solid var(--rule);border-radius:6px;
    padding:14px 16px 4px;margin:0 0 12px;background:rgba(42,41,36,.025)}
  .doc .table-wrap td{border:0;padding:0;margin:0 0 10px;min-width:0}
  .doc .table-wrap td:first-child{font-weight:600;color:var(--ink)}
  .doc .table-wrap td[data-label]:not(:first-child)::before{content:attr(data-label)}
}

.doc hr{border:0;border-top:1px solid var(--rule);margin:34px 0}

/* 插图 */
.doc figure{margin:28px 0;text-align:center}
.doc figure img{width:100%;max-width:100%;height:auto;border-radius:6px;
  background:var(--fig-bg);padding:var(--fig-pad)}  /* 示意图是透明底，夜间垫浅色底 */
.doc figcaption{margin-top:10px;font-family:var(--serif);font-style:italic;
  font-size:13.5px;color:var(--muted);line-height:1.6}

/* 脚注 */
.doc sup.footnote-ref{font-size:.75em;font-weight:600}
.doc sup.footnote-ref a{padding:0 2px}
.doc .footnote{margin-top:36px;padding-top:20px;border-top:1px solid var(--rule);
  font-size:14.5px;color:var(--muted);overflow-wrap:anywhere}
.doc .footnote hr{display:none}
.doc .footnote ol{padding-left:1.4em}
.doc .footnote li{margin-bottom:10px;line-height:1.7}
.doc .footnote li p{margin:0 0 4px;display:inline}
.doc .footnote a.footnote-backref{color:var(--accent);text-decoration:none;margin-left:4px}
.doc .footnote a.footnote-backref:hover{color:var(--accent-ink)}

/* 页面末尾安静区块（非 CTA，无强调配色） */
.endnote{margin-top:34px;padding:22px 26px;border:1px solid var(--rule);
  border-radius:6px;background:rgba(42,41,36,.025);font-size:15px;line-height:1.75}
.endnote p{margin:0 0 10px}
.endnote p:last-child{margin-bottom:0}
.endnote a{color:var(--accent)}
.endnote a:hover{color:var(--accent-ink)}
.endnote .note-fine{color:var(--muted);font-size:13.5px}

/* 问答页（/answers/）与章节页里指向它们的小框 */
.short-answer{margin:0 0 30px;padding:18px 22px;background:var(--tint);
  border:1px solid var(--tint-line);border-radius:6px}
.short-answer p{margin:0}
.doc sup.cite{font-size:.75em;font-weight:600}
.related{margin-top:34px}
.related h2{margin-top:0}
.doc ol.sources{font-size:14.5px;color:var(--muted);padding-left:1.4em}
.doc ol.sources li{margin-bottom:8px;line-height:1.7;overflow-wrap:anywhere}
.quick-answers{margin:24px 0;padding:16px 22px;background:var(--tint);
  border:1px solid var(--tint-line);border-radius:6px}
.quick-answers .qa-h{margin:0 0 6px;font-family:var(--serif);font-weight:600;font-size:12.5px;
  letter-spacing:.2em;text-transform:uppercase;color:var(--accent-ink)}
.doc .quick-answers ul{margin:0}
.doc .quick-answers li{margin:0 0 4px}

/* 章末上一章/下一章 */
.pager{display:flex;justify-content:space-between;gap:18px;
  margin-top:40px;padding-top:24px;border-top:1px solid var(--rule)}
.pager a{display:flex;flex-direction:column;gap:3px;max-width:47%;
  padding:12px 16px;border:1px solid var(--rule);border-radius:6px;
  transition:border-color .15s,background .15s}
.pager a:hover{border-color:var(--accent);background:var(--accent-soft)}
.pager-next{text-align:right;margin-left:auto}
.pager-dir{font-family:var(--serif);font-weight:600;font-size:12.5px;letter-spacing:.08em;
  color:var(--accent-ink)}
.pager-ttl{font-size:14px;color:var(--ink);font-weight:500}
.pager-spacer{flex:1}

/* 日夜切换按钮 */
.brand-tools{display:flex;align-items:stretch;gap:10px;margin-top:18px}
.brand-tools .lang-switch{margin-top:0}
/* 圆形按钮，图标显示当前模式（日间太阳、夜间月亮）；高度跟随旁边的语言切换 */
.theme-toggle{flex:none;width:36px;padding:0;border-radius:999px;cursor:pointer;
  display:flex;align-items:center;justify-content:center;
  background:transparent;border:1px solid rgba(255,255,255,.2);color:#A9AF9E}
.theme-toggle:hover{color:#F5F0E4;border-color:rgba(255,255,255,.45)}
.theme-toggle svg{width:16px;height:16px;fill:none;stroke:currentColor;stroke-width:2;
  stroke-linecap:round;stroke-linejoin:round}
.theme-toggle .i-moon{display:none}
:root[data-theme="dark"] .theme-toggle .i-sun{display:none}
:root[data-theme="dark"] .theme-toggle .i-moon{display:block}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]) .theme-toggle .i-sun{display:none}
  :root:not([data-theme="light"]) .theme-toggle .i-moon{display:block}
}

/* 本页目录：宽屏放在阅读栏右侧，窄屏收在章首 */
.pagetoc{display:none}
.pagetoc-h{font-family:var(--serif);font-size:11px;letter-spacing:.22em;text-transform:uppercase;
  color:#8C877A;font-weight:600;margin:0 0 12px}
.pagetoc ol,.pagetoc-inline ol{list-style:none;margin:0;padding:0}
.pagetoc a{display:block;padding:6px 0 6px 12px;border-left:2px solid rgba(255,255,255,.1);
  color:#A9A393;font-size:13.5px;line-height:1.45}
.pagetoc a:hover{color:#F5F0E4}
.pagetoc a.on{color:#9CCDB4;border-left-color:#7FB79C}
.pagetoc-inline{margin:-6px 0 30px;padding:10px 16px;border:1px solid var(--rule);border-radius:6px;font-size:15px}
.pagetoc-inline summary{cursor:pointer;font-weight:600;color:var(--ink)}
.pagetoc-inline ol{margin-top:8px}
.pagetoc-inline li{margin:5px 0;line-height:1.5}
@media (min-width:1240px){
  .main.has-toc{display:grid;grid-template-columns:minmax(0,var(--col-w)) 220px;
    column-gap:40px;justify-content:center}
  .main.has-toc .reader{max-width:none}
  .pagetoc{display:block;position:sticky;top:0;align-self:start;max-height:100vh;
    overflow-y:auto;padding:84px 0 40px}
  .pagetoc-inline{display:none}
}

/* 页脚 */
.colophon{max-width:var(--col-w);margin:8px auto 0;padding:0 0 64px}
.foot-meta{margin-top:26px;font-family:var(--serif);font-style:italic;
  color:#8E887B;font-size:13.5px;text-align:center;line-height:1.7}

/* 移动端顶栏 + 汉堡 */
.topbar{display:none}
.scrim{display:none}

@media (max-width:960px){
  :root{--side-w:280px}
  .sidebar{transform:translateX(-100%);transition:transform .28s ease;
    box-shadow:0 0 60px rgba(0,0,0,.3)}
  body.nav-open .sidebar{transform:translateX(0)}
  .scrim{display:block;position:fixed;inset:0;background:rgba(30,28,22,.45);
    z-index:40;opacity:0;pointer-events:none;transition:opacity .25s}
  body.nav-open .scrim{opacity:1;pointer-events:auto}
  .main{margin-left:0;padding:0 16px;display:block}
  .topbar{display:flex;align-items:center;gap:14px;position:sticky;top:0;
    z-index:30;background:rgba(32,30,26,.92);backdrop-filter:blur(8px);
    padding:12px 16px;margin:0 -16px 0;border-bottom:1px solid rgba(255,255,255,.08)}
  .topbar .theme-toggle{width:40px;height:40px}
  .menu-btn{background:var(--accent);color:var(--on-accent);border:0;border-radius:8px;
    width:40px;height:40px;font-size:18px;cursor:pointer;flex:none}
  .topbar .tb-title{font-weight:600;color:#EFE9DB;font-size:15px;flex:1;min-width:0;
    white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .topbar .tb-title .tb-sub{font-family:var(--serif);font-style:italic;
    color:#A9AF9E;font-weight:400}
  .reader{padding:26px 0 30px}
  .chapter{padding:32px 24px 28px}
  .ch-head{gap:16px}
  .ch-numeral{font-size:44px}
  .ch-title{font-size:23px}
  .chapter,.section{scroll-margin-top:70px}
  .cta{padding:30px 26px}
}
@media (max-width:560px){
  body{font-size:16px}
  .topbar .tb-sub{display:none}
  .chapter{padding:26px 18px 24px}
  .doc table{font-size:14px}
  .pager a{max-width:100%}
  .pager{flex-direction:column}
  .pager-next{text-align:left}
}
.chapter{scroll-margin-top:24px}

@media (prefers-reduced-motion:reduce){
  html{scroll-behavior:auto}
  #progress{transition:none}
  .sidebar{transition:none}
}
</style>
<script>try{var t=localStorage.getItem('theme');if(t==='light'||t==='dark')document.documentElement.setAttribute('data-theme',t)}catch(e){}</script>
__ANALYTICS__
</head>
<body>
<div id="progress"></div>

<aside class="sidebar" id="sidebar">
  <div class="brand">
    <div class="kicker">A Field Guide</div>
    <__BRAND_TAG__ class="bt"><a href="__HOME_HREF__">__BOOK_TITLE__</a></__BRAND_TAG__>
    <div class="sub">__BOOK_SUB__</div>
    <div class="brand-tools">__LANG_SWITCH____THEME_SWITCH__</div>
  </div>
  <nav class="toc" id="toc">
    <div class="toc-h">__TOC_LABEL__</div>
    __NAV__
  </nav>
  <div class="side-foot">
    <div class="note">__SIDENOTE__</div>
  </div>
</aside>
<div class="scrim" id="scrim"></div>

<main class="main__MAIN_CLASS__">
  <div class="topbar">
    <button class="menu-btn" id="menuBtn" aria-label="__MENU_ARIA__">☰</button>
    <div class="tb-title">__BOOK_TITLE__ <span class="tb-sub">· __BOOK_SUB__</span></div>
    __THEME_SWITCH__
  </div>
  <div class="reader">
    __CONTENT__

    <div class="colophon">
      <div class="foot-meta">__FOOT_META__</div>
    </div>
  </div>
  __PAGETOC__
</main>

<script>
(function(){
  var body=document.body, sidebar=document.getElementById('sidebar');
  var menuBtn=document.getElementById('menuBtn'), scrim=document.getElementById('scrim');
  var progress=document.getElementById('progress');
  var navItems=[].slice.call(document.querySelectorAll('.nav-item'));
  var sections=[].slice.call(document.querySelectorAll('.chapter'));

  // 移动端菜单
  function closeNav(){body.classList.remove('nav-open');}
  if(menuBtn){menuBtn.addEventListener('click',function(){body.classList.toggle('nav-open');});}
  if(scrim){scrim.addEventListener('click',closeNav);}
  navItems.forEach(function(a){a.addEventListener('click',function(){if(window.innerWidth<=960)closeNav();});});

  // 进度条 + 滚动高亮（scrollspy）
  function onScroll(){
    var st=window.scrollY||document.documentElement.scrollTop;
    var h=document.documentElement.scrollHeight-window.innerHeight;
    progress.style.width=(h>0?(st/h*100):0)+'%';
    var pos=st+window.innerHeight*0.33, cur=sections[0];
    for(var i=0;i<sections.length;i++){
      if(sections[i].offsetTop<=pos)cur=sections[i];
    }
    var id=cur?cur.id:null;
    navItems.forEach(function(a){
      a.classList.toggle('active',a.getAttribute('data-target')===id);
    });
  }
  var ticking=false;
  window.addEventListener('scroll',function(){
    if(!ticking){requestAnimationFrame(function(){onScroll();ticking=false;});ticking=true;}
  },{passive:true});
  window.addEventListener('resize',onScroll);
  onScroll();

  // 日夜切换：图标由 CSS 按当前模式显示；点击切到另一种并记住（未手动选择时跟随系统）
  var root=document.documentElement, mq=window.matchMedia?matchMedia('(prefers-color-scheme: dark)'):null;
  function isDark(){var t=root.getAttribute('data-theme');return t?t==='dark':!!(mq&&mq.matches);}
  [].slice.call(document.querySelectorAll('.theme-toggle')).forEach(function(b){b.addEventListener('click',function(){
    var v=isDark()?'light':'dark';root.setAttribute('data-theme',v);
    try{localStorage.setItem('theme',v);}catch(e){}
  });});

  // 本页目录：高亮当前小节
  var heads=[].slice.call(document.querySelectorAll('.doc h3[id]'));
  var tocLinks=[].slice.call(document.querySelectorAll('.pagetoc a'));
  if(heads.length&&tocLinks.length){
    var spy=function(){
      var cur=null;
      heads.forEach(function(h){if(h.getBoundingClientRect().top<120)cur=h.id;});
      tocLinks.forEach(function(a){a.classList.toggle('on',a.getAttribute('href')==='#'+cur);});
    };
    window.addEventListener('scroll',spy,{passive:true});spy();
  }
  [].slice.call(document.querySelectorAll('.pagetoc-inline a')).forEach(function(a){
    a.addEventListener('click',function(){a.closest('details').open=false;});
  });
})();
</script>
</body>
</html>'''


def nav_html_for(sections, active_id, prefix=""):
    items = []
    for s in sections:
        marker = s["numeral"] if s["numeral"] else "·"
        active = " active" if s["id"] == active_id else ""
        items.append(
            '<a class="nav-item%s" href="%s" data-target="%s">'
            '<span class="nav-mark">%s</span>'
            '<span class="nav-label">%s</span></a>'
            % (active, rel_href(prefix, s["id"]), s["id"], marker, html.escape(s["nav"]))
        )
    return "\n".join(items)


def lang_switch_html(current_lang, sec_id):
    links = LANGS[current_lang]["links"]
    parts = []
    for target in ["zh", "en"]:
        href = rel_href(links[target], sec_id)
        current = ' aria-current="page"' if target == current_lang else ""
        parts.append('<a href="%s"%s>%s</a>' % (href, current, LANGS[target]["switch_label"]))
    return ('<div class="lang-switch" role="group" aria-label="Language">\n'
            "      %s\n    </div>" % "\n      ".join(parts))


def hreflang_tags(sec_id):
    tags = []
    for cfg in LANGS.values():
        tags.append('<link rel="alternate" hreflang="%s" href="%s">'
                     % (cfg["lang_code"], url_for(cfg, sec_id)))
    tags.append('<link rel="alternate" hreflang="x-default" href="%s">'
                 % url_for(LANGS["en"], sec_id))
    return "\n".join(tags)


SUN_SVG = ('<svg class="i-sun" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"/>'
           '<path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2'
           'M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>')
MOON_SVG = ('<svg class="i-moon" viewBox="0 0 24 24" aria-hidden="true">'
            '<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>')


def theme_switch_html(cfg):
    return ('<button class="theme-toggle" type="button" aria-label="%s" title="%s">%s%s</button>'
            % (cfg["theme_label"], cfg["theme_label"], SUN_SVG, MOON_SVG))


def add_heading_ids(section_html, lang_key):
    """给正文 h3 加锚点并返回本页目录条目 [(id, 短标题, 完整标题)]。
    书稿里用 attr_list 写了 {#id} 的保留原样；英文按标题文字生成，中文用 sec-N。"""
    toc, used = [], set()

    def sub(m):
        attrs, inner = m.group(1), m.group(2)
        full = html.unescape(re.sub(r"<[^>]+>", "", inner)).strip()
        found = re.search(r'id="([^"]+)"', attrs)
        if found:
            hid = found.group(1)
        else:
            hid = re.sub(r"[^a-z0-9]+", "-", full.lower()).strip("-") if lang_key == "en" else ""
            if len(hid) > 60:
                hid = hid[:61].rsplit("-", 1)[0]  # 在词边界截断
            if not hid:
                hid = "sec-%d" % (len(toc) + 1)
            base, k = hid, 2
            while hid in used:
                hid, k = "%s-%d" % (base, k), k + 1
            attrs = attrs + ' id="%s"' % hid
        used.add(hid)
        short = re.split(r"[:：]", full, maxsplit=1)[0].strip() or full
        toc.append((hid, short, full))
        return "<h3%s>%s</h3>" % (attrs, inner)

    return re.sub(r"<h3([^>]*)>(.*?)</h3>", sub, section_html, flags=re.S), toc


def pagetoc_items(toc):
    return "\n".join('<li><a href="#%s" title="%s">%s</a></li>'
                     % (hid, html.escape(full, quote=True), html.escape(short))
                     for hid, short, full in toc)


def pagetoc_html(lang_key, toc):
    """宽屏右侧栏；没有小标题的章节不出这一栏。"""
    if not toc:
        return ""
    return ('<nav class="pagetoc" aria-label="%s"><p class="pagetoc-h">%s</p><ol>%s</ol></nav>'
            % (LANGS[lang_key]["pagetoc_label"], LANGS[lang_key]["pagetoc_label"], pagetoc_items(toc)))


def content_for(sections, i, prev_label, next_label, lang_key):
    s = sections[i]
    prev_s = sections[i - 1] if i > 0 else None
    next_s = sections[i + 1] if i < len(sections) - 1 else None
    numeral_html = ('<div class="ch-numeral">%s</div>' % s["numeral"]) if s["numeral"] else ""
    pn = ['<nav class="pager">']
    if prev_s:
        pn.append('<a class="pager-prev" href="%s"><span class="pager-dir">← %s</span>'
                  '<span class="pager-ttl">%s</span></a>' % (rel_href("", prev_s["id"]), prev_label, html.escape(prev_s["nav"])))
    else:
        pn.append('<span class="pager-spacer"></span>')
    if next_s:
        pn.append('<a class="pager-next" href="%s"><span class="pager-dir">%s →</span>'
                  '<span class="pager-ttl">%s</span></a>' % (rel_href("", next_s["id"]), next_label, html.escape(next_s["nav"])))
    else:
        pn.append('<span class="pager-spacer"></span>')
    pn.append("</nav>")
    pager = "\n".join(pn)
    extra = endnote_html(lang_key, s["id"]) if s.get("is_end") else ""
    toc = s.get("toc")
    inline_toc = ('<details class="pagetoc-inline"><summary>%s</summary><ol>%s</ol></details>\n  '
                  % (LANGS[lang_key]["pagetoc_label"], pagetoc_items(toc))) if toc else ""
    return ('<section id="%s" class="chapter" data-section="%s">\n'
            '  <header class="ch-head">\n    %s\n'
            '    <div class="ch-meta">\n'
            '      <div class="eyebrow">%s</div>\n'
            '      <h2 class="ch-title">%s</h2>\n'
            '    </div>\n  </header>\n'
            '  %s<div class="doc">\n    %s\n  </div>\n  %s\n  %s\n</section>'
            % (s["id"], s["id"], numeral_html, s["eyebrow"],
               html.escape(s["title"]), inline_toc, s["html"], extra, pager))


# ===== 入口页（/ 和 /zh/）：版式在这里，文案全部在 content/landing.yaml =====
LANDING_TEMPLATE = r'''<!DOCTYPE html>
<html lang="__LANG__">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="google-site-verification" content="N-Eq_2c5aG0rHDGOkAvz7jPIxSpWsmKo1mIh6O4yZ1U">
<title>__PAGE_TITLE__</title>
__HEAD_META__
__CANONICAL__
__HREFLANG__
__JSONLD__
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
__FONTS_LINK__
<style>
__ROOT_CSS__
:root{--sheet-w:1040px;--read-w:760px;--desk:#2F4A3E}  /* --desk：入口页纸面外的底色（深松绿），章节页仍用 --paper */
*{box-sizing:border-box}
body{margin:0;background:var(--desk);color:var(--text);font-family:var(--sans);font-size:17px;line-height:1.75;
  -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility;
  padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:20px 40px}
a{color:var(--accent-ink)}
a:focus-visible,summary:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.sheet{max-width:var(--sheet-w);margin:0 auto;background:var(--column);border-radius:4px;overflow:hidden}
.inner{padding-inline:clamp(20px,5vw,64px)}
.read{max-width:var(--read-w)}

/* 顶栏 */
.bar{display:flex;justify-content:space-between;align-items:center;gap:12px;padding-block:18px;border-bottom:1px solid var(--rule)}
.brand{font-family:var(--serif);font-weight:600;color:var(--ink);font-size:17px;letter-spacing:.01em;text-decoration:none}
.brand span{color:var(--muted);font-weight:400}
.lang{display:flex;border:1px solid var(--rule);border-radius:999px;overflow:hidden}
.lang a{padding:3px 12px;font-size:13px;color:var(--muted);text-decoration:none}
.lang a[aria-current="page"]{background:var(--ink);color:var(--column)}

/* 首屏：单栏，从上往下 */
.hero{padding-block:clamp(36px,7vw,72px) clamp(28px,5vw,48px)}
.hero .read{display:flex;flex-direction:column}
.eyebrow{font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:var(--accent-ink);font-weight:600;margin:0 0 14px}
h1{font-family:var(--serif);font-weight:500;color:var(--ink);font-size:clamp(34px,5.4vw,56px);line-height:1.12;margin:0 0 18px;text-wrap:balance;letter-spacing:-.01em}
.lang-zh h1{font-family:var(--sans);font-weight:700;letter-spacing:0;line-height:1.25}
.lede{font-size:clamp(17px,2vw,19px);color:var(--text);margin:0 0 26px;max-width:34em}
.lede strong{color:var(--ink)}
.ctas{display:flex;flex-wrap:wrap;gap:10px}
.btn{display:inline-flex;align-items:center;gap:6px;padding:11px 18px;border-radius:3px;font-size:15px;font-weight:600;text-decoration:none;border:1px solid var(--ink-line);color:var(--ink);background:transparent}
.btn.primary{background:var(--accent-ink);border-color:var(--accent-ink);color:var(--column)}
.meta{margin:12px 0 0;font-size:14px;color:var(--muted)}
.who{margin-top:32px;border-left:2px solid var(--accent);padding:4px 0 4px 18px;font-size:15.5px;color:var(--text);max-width:36em}
.who p{margin:0 0 8px}
.who p:last-child{margin:0}
.who .q{font-family:var(--serif);font-style:italic;color:var(--ink);font-size:18px}
.lang-zh .who .q{font-family:var(--sans);font-style:normal;font-weight:600;font-size:17px}
.who .sign{color:var(--muted);font-size:14px}

/* 事实区：一条一行 */
.facts{background:var(--tint);border-block:1px solid var(--tint-line);padding-block:clamp(32px,5vw,52px)}
h2{font-family:var(--serif);font-weight:500;color:var(--ink);font-size:clamp(24px,3vw,30px);line-height:1.25;margin:0 0 6px;text-wrap:balance}
.lang-zh h2{font-family:var(--sans);font-weight:700}
.sub{margin:0 0 20px;color:var(--muted);font-size:15px}
.flist{list-style:none;margin:0;padding:0;border-top:1px solid var(--tint-line)}
.fitem{padding:24px 0 26px;border-bottom:1px solid var(--tint-line);display:flex;flex-direction:column;gap:8px}
/* 常见说法：放在对话气泡里，表示是某人的想法；右上角的 emoji 小圆标表示这句不对 */
.fitem .myth{align-self:flex-start;position:relative;margin:10px 0 8px;padding:6px 14px;
  background:var(--column);border:1px solid var(--tint-line);border-radius:14px;
  font-size:clamp(16px,1.9vw,18px);line-height:1.5;color:var(--text)}
.fitem .myth .mark{position:absolute;top:-13px;right:-13px;width:28px;height:28px;border-radius:50%;
  background:var(--column);border:1px solid var(--tint-line);font-size:15px;line-height:26px;text-align:center}
.fitem .myth::after{content:"";position:absolute;left:18px;bottom:-7px;width:12px;height:12px;
  background:var(--column);border-right:1px solid var(--tint-line);border-bottom:1px solid var(--tint-line);
  transform:rotate(45deg)}
/* 事实：前面加 ↳ 表示修正；解释和按钮与事实文字左对齐 */
.fitem{--fix-indent:28px}
.fitem h3{position:relative;margin:0;padding-left:var(--fix-indent);font-size:clamp(19px,2.3vw,22px);line-height:1.45;color:var(--ink);font-weight:700;text-wrap:balance}
.fitem h3::before{content:"↳";position:absolute;left:0;top:0;color:var(--accent);font-weight:600}
.lang-en .fitem h3{font-family:var(--serif);font-weight:600}
.fitem .why{margin:0;padding-left:var(--fix-indent);font-size:13.5px;font-style:italic;line-height:1.7;color:var(--text);max-width:40em}
.fitem .foot{display:flex;flex-wrap:wrap;align-items:center;gap:8px 14px;margin-top:6px;padding-left:var(--fix-indent)}
.go{display:inline-flex;align-items:center;gap:6px;font-size:14.5px;font-weight:600;color:var(--accent-ink);text-decoration:none;background:var(--column);border:1px solid var(--accent);border-radius:3px;padding:6px 12px}
.go:hover{background:var(--accent-ink);color:var(--column);border-color:var(--accent-ink)}
.src{font-size:13px;color:var(--muted)}
.src a{color:inherit;text-decoration:underline;text-decoration-color:var(--tint-line);text-underline-offset:3px}
.src a:hover{color:var(--accent-ink);text-decoration-color:var(--accent)}
.qa{font-size:14px;font-weight:600;color:var(--accent-ink);text-decoration:underline;
  text-decoration-color:var(--accent);text-underline-offset:3px}
.qa:hover{color:var(--accent)}
.num{font-family:var(--serif);color:var(--accent-ink);font-weight:600;font-variant-numeric:tabular-nums}

/* 目录：整行是链接，右侧箭头 */
.toc{padding-block:clamp(32px,5vw,52px)}
.toc ol{list-style:none;margin:0;padding:0;border-top:1px solid var(--rule)}
.toc li{border-bottom:1px solid var(--rule)}
.toc li a{display:grid;grid-template-columns:5.5em minmax(0,1fr) auto auto;gap:4px 16px;padding:14px 4px;align-items:center;text-decoration:none;color:inherit}
.toc li a:hover{background:var(--tint)}
.toc li a:hover .t{color:var(--accent-ink)}
.toc .no{font-size:13px;color:var(--muted);letter-spacing:.04em}
.toc .t{color:var(--ink);font-weight:600;font-size:16px;min-width:0}
.toc .d{display:block;font-weight:400;color:var(--text);font-size:14.5px;margin-top:2px}
.toc .tag{font-size:12px;color:var(--accent-ink);background:var(--accent-soft);padding:1px 8px;border-radius:999px;white-space:nowrap}
.toc .tag:empty{background:none;padding:0}
.toc .arr{color:var(--accent-ink);font-size:20px;line-height:1}

/* 可信度四格 */
.trust-band{background:var(--tint);border-block:1px solid var(--tint-line)}
.trust{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:24px;padding-block:32px}
.trust-cell{min-width:0}
.trust-big{display:block;font-family:var(--serif);font-size:26px;color:var(--ink);font-weight:500;line-height:1.2;font-variant-numeric:tabular-nums}
.lang-zh .trust-big{font-family:var(--sans);font-weight:700;font-size:22px}
.trust-small{display:block;font-size:13.5px;color:var(--muted);line-height:1.5;margin-top:4px}

/* 常见问题 */
.faq{padding-block:clamp(32px,5vw,48px)}
.faq h2{margin-bottom:12px}
.faq details{border-bottom:1px solid var(--rule);padding:14px 0}
.faq details:first-of-type{border-top:1px solid var(--rule)}
.faq summary{cursor:pointer;color:var(--ink);font-weight:600;font-size:16px}
.faq details p{margin:8px 0 0;font-size:15px}

/* 页脚深色条 */
.end{background:var(--ink);color:#D9D1C1;padding-block:32px;display:flex;flex-wrap:wrap;gap:16px 32px;justify-content:space-between;align-items:center}
.end p{margin:0;font-size:15px}
.end .btn{color:var(--column);border-color:#6D6A5E}
.end .btn.primary{background:var(--accent);border-color:var(--accent)}
.mail{font-size:13px;color:#A69F90;width:100%}
.mail a{color:#E9E2D4;text-decoration:underline;text-decoration-color:rgba(233,226,212,.4);text-underline-offset:3px}
.mail a:hover{text-decoration-color:#E9E2D4}

@media (max-width:820px){
  .trust{grid-template-columns:repeat(2,minmax(0,1fr))}
}
@media (max-width:540px){
  body{padding-block:10px 24px;font-size:16px}
  .toc li a{grid-template-columns:minmax(0,1fr) auto}
  .toc .no{grid-column:1/-1}
  .toc .tag{display:none}
  .btn{flex:1 1 100%;justify-content:center}
}
</style>
__ANALYTICS__
</head>
<body class="landing lang-__LANG_KEY__">
<main class="sheet">
__CONTENT__
</main>
</body>
</html>'''


def load_landing():
    return yaml.safe_load(open("content/landing.yaml", encoding="utf-8"))


def inline_md(text):
    """landing.yaml 的文本字段：只用到行内 **粗体** 和 [链接](url)，渲染后去掉外层 <p>。
    渲染结果不是单个段落时（比如文字以「1. 」开头被当成列表），退回纯文本。"""
    text = "" if text is None else str(text)
    out = markdown.markdown(text).strip()
    if out.startswith("<p>") and out.endswith("</p>") and out.count("<p>") == 1:
        return out[3:-4]
    return html.escape(text)


def umami(event, position):
    return 'data-umami-event="%s" data-umami-event-position="%s"' % (event, position)


def landing_content(lang_key, t):
    links = LANGS[lang_key]["links"]
    read_href = rel_href("", "preface")
    buy_href = SHORT_LINKS[lang_key]["home"]
    lk = lang_key
    p = []

    switch = []
    for target in ["en", "zh"]:
        current = ' aria-current="page"' if target == lang_key else ""
        switch.append('<a href="%s"%s>%s</a>' % (rel_href(links[target], "home"), current,
                                                 LANGS[target]["switch_label"]))
    p.append('<div class="inner bar">\n'
             '  <a class="brand" href="./">llmknowledge<span>.org</span></a>\n'
             '  <div class="lang" role="group" aria-label="Language">%s</div>\n'
             '</div>' % "".join(switch))

    p.append('<section class="inner hero"><div class="read">\n'
             '  <p class="eyebrow">%s</p>\n'
             '  <h1>%s</h1>\n'
             '  <p class="lede">%s</p>\n'
             '  <div class="ctas">\n'
             '    <a class="btn primary" href="%s" %s>%s →</a>\n'
             '    <a class="btn" href="%s" %s>%s</a>\n'
             '    <a class="btn" href="%s" %s>%s</a>\n'
             '  </div>\n'
             '  <p class="meta">%s</p>\n'
             '  <div class="who">\n'
             '    <p class="q">%s</p>\n    <p>%s</p>\n    <p class="sign">%s</p>\n'
             '  </div>\n'
             '</div></section>'
             % (inline_md(t["eyebrow"]), inline_md(t["title"]), inline_md(t["lede"]),
                read_href, umami("landing-cta", "hero-read-" + lk), inline_md(t["cta_read"]),
                rel_href("", "cheatsheet"), umami("landing-cta", "hero-quick-" + lk), inline_md(t["cta_quick"]),
                buy_href, umami("landing-cta", "hero-buy-" + lk), inline_md(t["cta_buy"]),
                inline_md(t["meta_line"]),
                inline_md(t["who_question"]), inline_md(t["who_body"]), inline_md(t["who_sign"])))

    items = []
    for n, f in enumerate(t["facts"], 1):
        href = rel_href("", f["chapter"]) + ("#" + f["anchor"] if f.get("anchor") else "")
        why = inline_md(f["why"]).replace("<strong>", '<strong class="num">')
        src = '<span class="src">%s</span>' % inline_md(f["source"]) if f.get("source") else ""
        # 可选：这条事实有对应问答页时，在章节按钮旁加一个次要链接（问答页只有英文）
        if f.get("answer"):
            src = '<a class="qa" href="answers/%s">Quick answer →</a>' % f["answer"] + src
        mark = ('<span class="mark" aria-hidden="true">%s</span>' % html.escape(str(f["emoji"]))
                if f.get("emoji") else "")
        items.append('  <li class="fitem">\n'
                     '    <p class="myth">%s%s</p>\n'
                     '    <h3>%s</h3>\n'
                     '    <p class="why">%s</p>\n'
                     '    <div class="foot"><a class="go" href="%s" %s>%s →</a>%s</div>\n'
                     '  </li>'
                     % (inline_md(f["myth"]), mark, inline_md(f["fact"]), why, href,
                        umami("landing-fact", "%s-%d-%s" % (f["chapter"], n, lk)),
                        inline_md(f["link_label"]), src))
    p.append('<section class="facts"><div class="inner"><div class="read">\n'
             '  <h2>%s</h2>\n  <p class="sub">%s</p>\n'
             '  <ol class="flist">\n%s\n  </ol>\n'
             '</div></div></section>'
             % (inline_md(t["facts_title"]), inline_md(t["facts_sub"]), "\n".join(items)))

    rows = []
    for e in t["toc"]:
        rows.append('  <li><a href="%s" %s><span class="no">%s</span>'
                    '<span class="t">%s<span class="d">%s</span></span>'
                    '<span class="tag">%s</span><span class="arr" aria-hidden="true">›</span></a></li>'
                    % (rel_href("", e["id"]), umami("landing-toc", "%s-%s" % (e["id"], lk)),
                       inline_md(e["label"]), inline_md(e["title"]), inline_md(e["desc"]),
                       inline_md(e.get("tag"))))
    p.append('<section class="inner toc" id="toc"><div class="read">\n'
             '  <h2>%s</h2>\n  <p class="sub">%s</p>\n'
             '  <ol>\n%s\n  </ol>\n'
             '</div></section>'
             % (inline_md(t["toc_title"]), inline_md(t["toc_sub"]), "\n".join(rows)))

    cells = ['  <div class="trust-cell"><span class="trust-big">%s</span><span class="trust-small">%s</span></div>'
             % (inline_md(c["big"]), inline_md(c["small"])) for c in t["trust"]]
    p.append('<section class="trust-band"><div class="inner"><div class="trust">\n%s\n</div></div></section>'
             % "\n".join(cells))

    qs = ['  <details%s><summary>%s</summary><p>%s</p></details>'
          % (" open" if q.get("open") else "", inline_md(q["q"]), inline_md(q["a"])) for q in t["faq"]]
    p.append('<section class="inner faq"><div class="read">\n  <h2>%s</h2>\n%s\n</div></section>'
             % (inline_md(t["faq_title"]), "\n".join(qs)))

    p.append('<footer class="inner end">\n'
             '  <p>%s</p>\n'
             '  <div class="ctas">\n'
             '    <a class="btn primary" href="%s" %s>%s →</a>\n'
             '    <a class="btn" href="%s" %s>%s</a>\n'
             '  </div>\n'
             '  <p class="mail">%s <a href="mailto:%s">%s</a></p>\n'
             '</footer>'
             % (inline_md(t["end_text"]),
                read_href, umami("landing-cta", "end-read-" + lk), inline_md(t["cta_read"]),
                SHORT_LINKS[lang_key]["end"], umami("landing-cta", "end-buy-" + lk), inline_md(t["cta_buy"]),
                inline_md(t["contact_label"]), CONTACT_EMAIL, CONTACT_EMAIL))
    return "\n\n".join(p)


# 结构化数据里的书名以封面 / 文件扉页为准（与 IngramSpark 一致），站内书名作 alternateName
BOOK_NAMES = {
    "en": "Understanding Modern LLM Systems: A Field Guide to RAG, Agents, and Beyond",
    "zh": "理解现代LLM系统：从RAG到全景",
}
EDITION = {"number": "2", "date": "2026-10"}


def plain_text(md_text):
    return html.unescape(re.sub(r"<[^>]+>", "", inline_md(md_text)))


def landing_jsonld(lang_key, t, sections):
    """入口页的 schema.org 数据：Book（含各章链接）+ FAQPage。不写价格（见 decisions 10/19）。"""
    cfg = LANGS[lang_key]
    home = url_for(cfg, "home")
    book = {
        "@type": "Book",
        "@id": home + "#book",
        "name": BOOK_NAMES[lang_key],
        "alternateName": cfg["book_title"],
        "description": META_DESCRIPTIONS[lang_key]["home"],
        "url": home,
        "image": og_image_url(lang_key),
        "author": {"@type": "Person", "name": "koe"},
        "inLanguage": cfg["lang_code"],
        "bookEdition": EDITION["number"],
        "dateModified": EDITION["date"],
        "isAccessibleForFree": True,
        "license": "https://creativecommons.org/licenses/by-nc-nd/4.0/",
        "hasPart": [{"@type": "Chapter", "position": i + 1, "name": s["title"],
                     "url": url_for(cfg, s["id"])} for i, s in enumerate(sections)],
    }
    faq = {
        "@type": "FAQPage",
        "@id": home + "#faq",
        "mainEntity": [{"@type": "Question", "name": plain_text(q["q"]),
                        "acceptedAnswer": {"@type": "Answer", "text": plain_text(q["a"])}}
                       for q in t["faq"]],
    }
    data = json.dumps({"@context": "https://schema.org", "@graph": [book, faq]},
                      ensure_ascii=False, indent=1)
    return '<script type="application/ld+json">\n%s\n</script>' % data.replace("</", "<\\/")


def build_landing(lang_key, landing, sections):
    cfg = LANGS[lang_key]
    out = (LANDING_TEMPLATE
           .replace("__ROOT_CSS__", ROOT_CSS)
           .replace("__FONTS_LINK__", fonts_link(lang_key))
           .replace("__ANALYTICS__", ANALYTICS_HTML)
           .replace("__LANG_KEY__", lang_key)
           .replace("__LANG__", cfg["lang_code"])
           .replace("__PAGE_TITLE__", html.escape(page_title_for(lang_key, "home")))
           .replace("__HEAD_META__", head_meta_for(lang_key, cfg, "home"))
           .replace("__CANONICAL__", '<link rel="canonical" href="%s">' % url_for(cfg, "home"))
           .replace("__HREFLANG__", hreflang_tags("home"))
           .replace("__JSONLD__", landing_jsonld(lang_key, landing[lang_key], sections))
           .replace("__CONTENT__", landing_content(lang_key, landing[lang_key])))
    open(os.path.join(cfg["outdir"], fname("home")), "w", encoding="utf-8").write(out)


# ===== 表格：内容长的表改成「一行一张卡片」，其余保持表格（手机上叠成卡片） =====
# 按英文版判断（有单格超过 CARD_TABLE_CHARS 个字符就改卡片）；中文同一章同一位置的表跟着走，
# 两种语言排法一致。表头第一格空着、两到三栏的是对比表（如「合规 vs 安全」），每栏一张卡片并排。
# 书稿不动，PDF/EPUB 不受影响。
CARD_TABLE_CHARS = 250


def _cells(row_html):
    """[(h|d, 属性, 内容)]"""
    return re.findall(r"<t([hd])([^>]*)>(.*?)</t\1>", row_html, re.S)


def _plain(fragment):
    return html.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()


def find_card_tables():
    cfg = LANGS["en"]
    sections = parse_sections(cfg["src"])
    classify_structural(sections)
    md = markdown.Markdown(extensions=["tables", "fenced_code", "attr_list", "footnotes"])
    found = set()
    for s in sections:
        md.reset()
        body = md.convert("\n".join(s["body"]).strip())
        for n, table in enumerate(re.findall(r"<table>(.*?)</table>", body, re.S), 1):
            tbody = re.search(r"<tbody>(.*?)</tbody>", table, re.S).group(1)
            if any(len(_plain(c)) > CARD_TABLE_CHARS for _, _, c in _cells(tbody)):
                found.add((s["id"], n))
    return found


CARD_TABLES = find_card_tables()


def layout_tables(section_html, sec_id):
    count = [0]

    def convert(m):
        count[0] += 1
        table = m.group(1)
        head = [c for _, _, c in _cells(re.search(r"<thead>(.*?)</thead>", table, re.S).group(1))]
        rows = [_cells(r) for r in re.findall(r"<tr>(.*?)</tr>",
                                              re.search(r"<tbody>(.*?)</tbody>", table, re.S).group(1), re.S)]
        if (sec_id, count[0]) in CARD_TABLES:
            out = ['<div class="row-cards">']
            for r in rows:
                out.append('<div class="rc"><div class="rc-t">%s</div>' % r[0][2])
                out += ['<div class="rc-f"><span class="rc-l">%s</span>%s</div>' % (label, c)
                        for label, (_, _, c) in zip(head[1:], r[1:])]
                out.append("</div>")
            out.append("</div>")
            return "\n".join(out)
        if not _plain(head[0]) and 3 <= len(head) <= 4:
            out = ['<div class="compare" style="--cmp-n:%d">' % (len(head) - 1)]
            for j in range(1, len(head)):
                out.append('<div class="cmp-col"><div class="cmp-h">%s</div>' % head[j])
                out += ['<div class="cmp-f"><span class="rc-l">%s</span>%s</div>' % (r[0][2], r[j][2])
                        for r in rows]
                out.append("</div>")
            out.append("</div>")
            return "\n".join(out)
        # 普通表格：每格带上栏名，手机上叠成卡片时显示
        labels = [html.escape(_plain(h), quote=True) for h in head]
        body = "\n".join("<tr>%s</tr>" % "".join('<td%s data-label="%s">%s</td>' % (a, labels[i], c)
                                                  for i, (_, a, c) in enumerate(r)) for r in rows)
        thead = re.search(r"<thead>.*?</thead>", table, re.S).group(0)
        return '<div class="table-wrap"><table>%s\n<tbody>\n%s\n</tbody></table></div>' % (thead, body)

    return re.sub(r"<table>(.*?)</table>", convert, section_html, flags=re.S)


def build_lang(lang_key):
    cfg = LANGS[lang_key]
    sections = parse_sections(cfg["src"])
    classify_structural(sections)

    md = markdown.Markdown(extensions=["tables", "fenced_code", "attr_list", "footnotes"])
    for s in sections:
        body_md = "\n".join(s["body"]).strip()
        md.reset()
        s["html"] = md.convert(body_md)
        if lang_key == "en" and s["id"] == "preface":
            s["html"] += (
                "<p>Everything here is free to read, and will stay that way. "
                'If you\'d rather read it off the browser, there\'s a <a href="%s">'
                "typeset PDF + EPUB edition</a>.</p>" % SHORT_LINKS["en"]["preface"]
            )
        s["html"] = layout_tables(s["html"], s["id"])
        s["html"], s["toc"] = add_heading_ids(s["html"], lang_key)
        if lang_key == "en" and s["id"] in QUICK_ANSWERS:
            s["html"] = inject_quick_answers(s["html"], s["id"])

    outdir = cfg["outdir"]
    os.makedirs(outdir, exist_ok=True)

    # Use language-specific images when available (e.g. content/images/en/)
    images_lang = "content/images/" + lang_key
    images_src = images_lang if os.path.isdir(images_lang) else "content/images"
    if os.path.isdir(images_src):
        shutil.copytree(images_src, os.path.join(outdir, "images"), dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("en", "zh"))

    for i, s in enumerate(sections):
        out = (TEMPLATE
               .replace("__ROOT_CSS__", ROOT_CSS)
               .replace("__FONTS_LINK__", fonts_link(lang_key))
               .replace("__ANALYTICS__", ANALYTICS_HTML)
               .replace("__LANG__", cfg["lang_code"])
               .replace("__PAGE_TITLE__", html.escape(page_title_for(lang_key, s["id"])))
               .replace("__HEAD_META__", head_meta_for(lang_key, cfg, s["id"]))
               .replace("__CANONICAL__", '<link rel="canonical" href="%s">' % url_for(cfg, s["id"]))
               .replace("__HREFLANG__", hreflang_tags(s["id"]))
               .replace("__BRAND_TAG__", "h1")
               .replace("__HOME_HREF__", "./")
               .replace("__BOOK_TITLE__", html.escape(cfg["book_title"]))
               .replace("__BOOK_SUB__", html.escape(cfg["book_sub"]))
               .replace("__TOC_LABEL__", html.escape(cfg["toc_label"]))
               .replace("__MENU_ARIA__", html.escape(cfg["menu_aria"]))
               .replace("__LANG_SWITCH__", lang_switch_html(lang_key, s["id"]))
               .replace("__NAV__", nav_html_for(sections, s["id"]))
               .replace("__MAIN_CLASS__", " has-toc" if s["toc"] else "")
               .replace("__PAGETOC__", pagetoc_html(lang_key, s["toc"]))
               .replace("__THEME_SWITCH__", theme_switch_html(cfg))
               .replace("__CONTENT__", content_for(sections, i, cfg["prev_label"], cfg["next_label"], lang_key))
               .replace("__SIDENOTE__", cfg["sidenote_html"])
               .replace("__FOOT_META__", html.escape(cfg["foot_meta"])))
        open(os.path.join(outdir, fname(s["id"])), "w", encoding="utf-8").write(out)

    # 给 AI/LLM 抓取用的全文纯文本版（原始 Markdown 源文件，逐字复制）
    shutil.copy(cfg["src"], os.path.join(outdir, "llms-full.txt"))

    return sections


# ===== 问答页（/answers/<slug>，只有英文）：每页回答一个具体问题，内容取自章节正文与脚注 =====
# 源文件 content/answers/<slug>.en.md：开头 front matter（title、description、h1、chapter、
# published、related、short、sources），后面是正文 Markdown。正文里用 [1]、[2] 引用 sources。
ANSWERS_DIR = "content/answers"
ANSWERS_OUTDIR = "site/answers"
ANSWERS_EYEBROW = "QUICK ANSWER"


def load_answers():
    answers = {}
    if not os.path.isdir(ANSWERS_DIR):
        return answers
    for fn in sorted(os.listdir(ANSWERS_DIR)):
        if not fn.endswith(".en.md"):
            continue
        raw = open(os.path.join(ANSWERS_DIR, fn), encoding="utf-8").read()
        _, front, body = raw.split("---\n", 2)
        a = yaml.safe_load(front)
        a["slug"] = fn[:-len(".en.md")]
        a["body"] = body.strip()
        answers[a["slug"]] = a
    return answers


ANSWERS = load_answers()


def answer_url(slug):
    return "%s/answers/%s" % (BASE_URL, slug)


def link_citations(body_html):
    """正文里的 [1]、[2] 链到页末 Sources 对应条目。"""
    return re.sub(r"\[(\d+)\]", r'<sup class="cite"><a href="#src-\1">[\1]</a></sup>', body_html)


# 章节网页版里指向问答页的小框（只在 HTML 注入，不改书稿，PDF/EPUB 不受影响）。
# 键是章节 id；值是（插入位置：含这段文字的段落之后，问答页 slug 列表）。
QUICK_ANSWERS = {
    "ch5": ("two separate questions", ["can-embeddings-be-reversed", "openai-api-data-retention"]),
    "ch6": ("became the exfiltration channel", ["echoleak-explained"]),
}


def inject_quick_answers(section_html, sec_id):
    marker, slugs = QUICK_ANSWERS[sec_id]
    at = section_html.find(marker)
    if at < 0:
        raise SystemExit("quick answers: marker %r not found in %s" % (marker, sec_id))
    end = section_html.index("</p>", at) + len("</p>")
    items = "".join('<li><a href="answers/%s">%s</a></li>' % (sl, html.escape(ANSWERS[sl]["h1"]))
                    for sl in slugs)
    box = ('\n<aside class="quick-answers"><p class="qa-h">Quick answers</p><ul>%s</ul></aside>'
           % items)
    return section_html[:end] + box + section_html[end:]


def answer_jsonld(a):
    data = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": a["h1"],
        "description": a["description"],
        "author": {"@type": "Person", "name": "koe"},
        "datePublished": a["published"],
        "dateModified": a.get("modified", a["published"]),
        "mainEntityOfPage": answer_url(a["slug"]),
        "image": og_image_url("en"),
        "inLanguage": "en",
        "isPartOf": {"@type": "Book", "name": BOOK_NAMES["en"], "url": url_for(LANGS["en"], "home")},
    }
    return ('<script type="application/ld+json">\n%s\n</script>'
            % json.dumps(data, ensure_ascii=False, indent=1).replace("</", "<\\/"))


def answer_head_meta(a):
    cfg = LANGS["en"]
    title = html.escape(a["title"], quote=True)
    desc = html.escape(a["description"], quote=True)
    return "\n".join([
        '<meta name="description" content="%s">' % desc,
        '<meta property="og:type" content="article">',
        '<meta property="og:site_name" content="%s">' % html.escape(cfg["book_title"], quote=True),
        '<meta property="og:title" content="%s">' % title,
        '<meta property="og:description" content="%s">' % desc,
        '<meta property="og:url" content="%s">' % answer_url(a["slug"]),
        '<meta property="og:locale" content="en_US">',
        '<meta property="og:image" content="%s">' % og_image_url("en"),
        '<meta property="og:image:width" content="2400">',
        '<meta property="og:image:height" content="1260">',
        '<meta property="og:image:alt" content="%s">' % html.escape(cfg["book_title"], quote=True),
        '<meta name="twitter:card" content="summary_large_image">',
        answer_jsonld(a),
    ])


def answer_content(a):
    md = markdown.Markdown(extensions=["tables", "attr_list"])
    short = md.convert("**Short answer:** " + a["short"])
    md.reset()
    body = md.convert(a["body"])
    related = "".join('<li><a href="%s">%s</a></li>' % (sl, html.escape(ANSWERS[sl]["h1"]))
                      for sl in a.get("related", []))
    sources = "".join('<li id="src-%d">%s <a href="%s">%s</a></li>'
                      % (n, inline_md(src["text"]), html.escape(src["url"], quote=True),
                         html.escape(src["url"]))
                      for n, src in enumerate(a["sources"], 1))
    foot = ('<div class="endnote"><p>This answer is drawn from <em>Understanding Modern LLM Systems</em>, '
            'a free field guide. <a href="../preface">Read it online →</a> · '
            '<a href="%s">PDF + EPUB</a></p></div>' % SHORT_LINKS["en"]["answers"])
    return ('<article id="answer" class="chapter answer">\n'
            '  <header class="ch-head">\n'
            '    <div class="ch-meta">\n'
            '      <div class="eyebrow">%s</div>\n'
            '      <h1 class="ch-title">%s</h1>\n'
            '    </div>\n  </header>\n'
            '  <div class="doc">\n'
            '    <div class="short-answer">%s</div>\n'
            '    %s\n'
            '    <section class="related"><h2>Related answers</h2><ul>%s</ul></section>\n'
            '    <h2>Sources</h2>\n    <ol class="sources">%s</ol>\n'
            '  </div>\n  %s\n</article>'
            % (ANSWERS_EYEBROW, html.escape(a["h1"]), link_citations(short), link_citations(body),
               related, sources, foot))


def build_answers(sections):
    cfg = LANGS["en"]
    os.makedirs(ANSWERS_OUTDIR, exist_ok=True)
    for a in ANSWERS.values():
        out = (TEMPLATE
               .replace("__ROOT_CSS__", ROOT_CSS)
               .replace("__FONTS_LINK__", fonts_link("en"))
               .replace("__ANALYTICS__", ANALYTICS_HTML)
               .replace("__LANG__", cfg["lang_code"])
               .replace("__PAGE_TITLE__", html.escape(a["title"]))
               .replace("__HEAD_META__", answer_head_meta(a))
               .replace("__CANONICAL__", '<link rel="canonical" href="%s">' % answer_url(a["slug"]))
               .replace("__HREFLANG__", "")
               .replace("__BRAND_TAG__", "div")
               .replace("__HOME_HREF__", "../")
               .replace("__BOOK_TITLE__", html.escape(cfg["book_title"]))
               .replace("__BOOK_SUB__", html.escape(cfg["book_sub"]))
               .replace("__TOC_LABEL__", html.escape(cfg["toc_label"]))
               .replace("__MENU_ARIA__", html.escape(cfg["menu_aria"]))
               .replace("__LANG_SWITCH__", "")
               .replace("__NAV__", nav_html_for(sections, a["chapter"], prefix="../"))
               .replace("__MAIN_CLASS__", "")
               .replace("__PAGETOC__", "")
               .replace("__THEME_SWITCH__", theme_switch_html(cfg))
               .replace("__CONTENT__", answer_content(a))
               .replace("__SIDENOTE__", cfg["sidenote_html"])
               .replace("__FOOT_META__", html.escape(cfg["foot_meta"])))
        open(os.path.join(ANSWERS_OUTDIR, a["slug"] + ".html"), "w", encoding="utf-8").write(out)
    return len(ANSWERS)


def write_sitemap(sections_by_lang):
    today = date.today().isoformat()
    # 入口页在最前；各语言章节一一对应，用英文版的顺序即可
    ids = ["home"] + [s["id"] for s in sections_by_lang["en"]]
    blocks = []
    for sec_id in ids:
        for cfg in LANGS.values():
            alt = ['    <xhtml:link rel="alternate" hreflang="%s" href="%s"/>'
                   % (lc["lang_code"], url_for(lc, sec_id)) for lc in LANGS.values()]
            alt.append('    <xhtml:link rel="alternate" hreflang="x-default" href="%s"/>'
                        % url_for(LANGS["en"], sec_id))
            blocks.append(
                "  <url>\n    <loc>%s</loc>\n    <lastmod>%s</lastmod>\n%s\n  </url>"
                % (url_for(cfg, sec_id), today, "\n".join(alt))
            )
    # 问答页只有英文，不写 hreflang
    for slug_ in ANSWERS:
        blocks.append("  <url>\n    <loc>%s</loc>\n    <lastmod>%s</lastmod>\n  </url>"
                      % (answer_url(slug_), today))
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        + "\n".join(blocks) + "\n</urlset>\n"
    )
    open("site/sitemap.xml", "w", encoding="utf-8").write(xml)


def write_robots():
    txt = (
        "User-agent: *\n"
        "Allow: /\n"
        "\n"
        "Sitemap: %s/sitemap.xml\n" % BASE_URL
    )
    open("site/robots.txt", "w", encoding="utf-8").write(txt)


def write_indexnow_key():
    open("site/%s.txt" % INDEXNOW_KEY, "w", encoding="utf-8").write(INDEXNOW_KEY)


def write_llms_txt(sections_by_lang):
    lines = [
        "# Understanding Modern LLM Systems: A Field Guide to RAG, Agents, and Beyond",
        "",
        "> A free, book-length guide to how modern LLM systems actually work — RAG, "
        "fine-tuning, agents, and where your data goes. Written for people who need to "
        "understand these systems without reading the papers or writing the code. No "
        "math or programming background required.",
        "",
        "Also available in Chinese (中文版) under /zh/. Licensed CC BY-NC-ND 4.0 — free "
        "to read and share; not for commercial reuse or derivative works without "
        "permission.",
        "",
    ]
    for lang_key in ("en", "zh"):
        cfg = LANGS[lang_key]
        heading = "## English" if lang_key == "en" else "## 中文"
        lines.append(heading)
        for s in sections_by_lang[lang_key]:
            desc = DESCRIPTIONS[lang_key].get(s["id"], "")
            lines.append("- [%s](%s): %s" % (s["title"], url_for(cfg, s["id"]), desc))
        lines.append("- [Full text, single file](%s/llms-full.txt)"
                      % (BASE_URL + cfg["url_prefix"].rstrip("/")))
        lines.append("")
        if lang_key == "en" and ANSWERS:
            lines.append("## Quick answers")
            for a in ANSWERS.values():
                lines.append("- [%s](%s): %s" % (a["h1"], answer_url(a["slug"]), a["description"]))
            lines.append("")
    open("site/llms.txt", "w", encoding="utf-8").write("\n".join(lines).rstrip() + "\n")


# ---- 多语言输出：site/ 是英文（根路径），site/zh/ 是中文 ----
if os.path.isdir("site"):
    shutil.rmtree("site")
os.makedirs("site")

if os.path.isfile("_redirects"):
    shutil.copy("_redirects", os.path.join("site", "_redirects"))
if os.path.isdir(SOCIAL_DIR):
    shutil.copytree(SOCIAL_DIR, os.path.join("site", "social"))

total = 0
sections_by_lang = {}
landing = load_landing()
for lang_key in LANGS:
    sections = build_lang(lang_key)
    build_landing(lang_key, landing, sections)
    sections_by_lang[lang_key] = sections
    total += len(sections) + 1
    print("built %d pages + landing -> %s/" % (len(sections), LANGS[lang_key]["outdir"]))

n_answers = build_answers(sections_by_lang["en"])
total += n_answers
print("built %d answer pages -> %s/" % (n_answers, ANSWERS_OUTDIR))

write_sitemap(sections_by_lang)
write_robots()
write_llms_txt(sections_by_lang)
write_indexnow_key()
print("wrote sitemap.xml, robots.txt, llms.txt, IndexNow key")

print("total %d pages" % total)
