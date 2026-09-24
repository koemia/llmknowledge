# -*- coding: utf-8 -*-
import re, markdown, html, os, shutil
from datetime import date

BASE_URL = "https://llmknowledge.pages.dev"

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
        foot_meta="理解现代大语言模型系统-从RAG到全景 · 写给泛技术人群的概念地图：从碎片认知到系统脉络 — 通俗扩充版 · 简体中文",
        switch_label="中文",
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
        foot_meta="Understanding Modern LLM Systems: A Field Guide to RAG, Agents, and Beyond — Expanded Popular Edition · English",
        switch_label="EN",
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
        "ch6": "Beyond RAG — the landscape, organized by what the model is missing",
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
        "ch6": "RAG 之外——按「模型缺什么」组织的全景",
        "appendix": "工具库概览",
        "cheatsheet": "整本书浓缩在一页里",
    },
}

# 付费出站短链：每个入口位置一条固定短链，UTM/最终跳转目标在短链服务那端配置，
# 网站代码这里只放短链本身，不拼接任何 query string。
SHORT_LINKS = {
    "en": {
        "sidebar": "https://ymjr.de/llmbook-en-sidebar",
        "home": "https://ymjr.de/llmbook-en-home",
        "ch6": "https://ymjr.de/llmbook-en-ch6",
        "appendix": "https://ymjr.de/llmbook-en-appendix",
        "cheatsheet": "https://ymjr.de/llmbook-en-cheat",
    },
    "zh": {
        "sidebar": "https://ymjr.de/llmbook-zh-sidebar",
        "ch6": "https://ymjr.de/llmbook-zh-ch6",
        "appendix": "https://ymjr.de/llmbook-zh-appendix",
        "cheatsheet": "https://ymjr.de/llmbook-zh-cheat",
    },
}

LANGS["zh"]["sidenote_html"] = LANGS["zh"]["sidenote_html"] % SHORT_LINKS["zh"]["sidebar"]
LANGS["en"]["sidenote_html"] = LANGS["en"]["sidenote_html"] % SHORT_LINKS["en"]["sidebar"]

# 章末区块首句：三页各不相同，其余段落一致
ENDNOTE_LEAD = {
    "en": {
        "ch6": ("That was the last chapter — the appendix and quick reference come after. "
                "The whole guide is here, free, and will stay that way."),
        "appendix": ("One page left after this: the quick reference card. "
                     "The whole guide is here, free, and will stay that way."),
        "cheatsheet": "You've reached the end. The whole guide is here, free, and will stay that way.",
    },
    "zh": {
        "ch6": "正文到此结束，后面还有附录和速记卡片。网页版永久免费。",
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
            "  <p>If you'd rather have it off the browser: 43 English pages / 30 Chinese pages, "
            "typeset as PDF and EPUB, 7 original diagrams, 11 footnotes to primary sources — "
            "four files in one download, $9.</p>\n"
            '  <p><a href="%s">Get the PDF + EPUB on Gumroad →</a></p>\n'
            "</div>" % (lead, link)
        )
    return (
        '<div class="endnote">\n'
        "  <p>%s</p>\n"
        "  <p>想把它从浏览器里拿出来：中文 30 页 / 英文 43 页，排版好的 PDF 与 EPUB、"
        "7 张原创示意图、11 条一手来源脚注——四个文件一次下载，$9 起。"
        "付款支持境外银行卡与 PayPal。</p>\n"
        '  <p><a href="%s">在 Gumroad 获取 PDF + EPUB →</a></p>\n'
        '  <p class="note-fine">在国内的话，可以在小红书上找到我（比白为竹间），'
        "中文版的其他获取方式我在安排。</p>\n"
        "</div>" % (lead, link)
    )


def fname(sec_id):
    return "index.html" if sec_id == "preface" else sec_id + ".html"


def url_for(cfg, sec_id):
    """首页用干净的 / 或 /zh/，其余页面用 /chN.html 这种实际文件名。"""
    fn = fname(sec_id)
    if fn == "index.html":
        return BASE_URL + cfg["url_prefix"]
    return BASE_URL + cfg["url_prefix"] + fn


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


TEMPLATE = r'''<!DOCTYPE html>
<html lang="__LANG__">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="google-site-verification" content="mN09xIJaqJy7jMjo_Z9wPwu4Od0xNoTZgLP8owVbxg8">
<title>__PAGE_TITLE__</title>
__HREFLANG__
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Spectral:ital,wght@0,400;0,500;0,600;1,400;1,500&display=swap" rel="stylesheet">
<style>
:root{
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
  background:var(--ink);color:#DBD5C7;display:flex;flex-direction:column;
  z-index:50;border-right:1px solid #17160F;
}
.brand{padding:34px 30px 22px;border-bottom:1px solid rgba(255,255,255,.09)}
.brand .kicker{font-family:var(--serif);font-size:12px;letter-spacing:.32em;
  text-transform:uppercase;color:#A89F8C;font-weight:600;margin-bottom:12px}
.brand h1{margin:0;font-weight:700;font-size:23px;line-height:1.3;color:#F5F0E4;
  letter-spacing:.01em}
.brand h1::after{content:"";display:block;width:46px;height:2px;
  background:var(--accent);margin-top:13px;border-radius:2px}
.brand .sub{font-family:var(--serif);font-style:italic;font-size:15px;
  color:#A9AF9E;margin-top:12px}

.lang-switch{margin-top:18px;display:inline-flex;border:1px solid rgba(255,255,255,.2);
  border-radius:999px;overflow:hidden;font-size:13px}
.lang-switch a{background:transparent;border:0;color:#A9AF9E;
  padding:5px 14px;cursor:pointer;font-family:var(--serif);letter-spacing:.05em;display:inline-block}
.lang-switch a[aria-current="page"]{background:var(--accent);color:#fff}

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
.doc h3{font-size:20px;font-weight:600;color:var(--ink);margin:44px 0 14px;
  line-height:1.5;letter-spacing:.005em;
  padding-left:14px;border-left:3px solid var(--accent)}
.doc h4{font-size:17px;font-weight:600;color:var(--ink);margin:30px 0 10px}
.doc p{margin:0 0 18px}
.doc strong{font-weight:600;color:#2E2C26}
.doc em{font-style:normal;background:linear-gradient(transparent 62%,var(--accent-soft) 62%);
  padding:0 1px}
.doc ul,.doc ol{margin:0 0 20px;padding-left:1.35em}
.doc li{margin:0 0 9px;padding-left:.2em}
.doc li::marker{color:var(--accent)}

/* 行内代码与术语 */
.doc code{font-family:var(--mono);font-size:.86em;background:var(--code-bg);
  padding:.12em .4em;border-radius:4px;color:#3A3226}
.doc pre{background:#26251F;color:#E9E3D5;padding:18px 20px;border-radius:6px;
  overflow-x:auto;margin:0 0 20px;font-size:14px;line-height:1.7}
.doc pre code{background:none;color:inherit;padding:0}

/* 引用 / 注释块 —— 招牌样式 */
.doc blockquote{margin:24px 0;padding:20px 24px;background:var(--column);
  border:1px solid var(--tint-line);border-left:4px solid var(--accent);
  border-radius:4px;position:relative}
.doc blockquote::before{content:"注";position:absolute;top:-11px;left:18px;
  background:var(--accent-ink);color:#fff;font-family:var(--serif);font-size:11px;
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

.doc hr{border:0;border-top:1px solid var(--rule);margin:34px 0}

/* 插图 */
.doc figure{margin:28px 0;text-align:center}
.doc figure img{width:100%;max-width:100%;height:auto;border-radius:6px}
.doc figcaption{margin-top:10px;font-family:var(--serif);font-style:italic;
  font-size:13.5px;color:var(--muted);line-height:1.6}

/* 脚注 */
.doc sup.footnote-ref{font-size:.75em;font-weight:600}
.doc sup.footnote-ref a{padding:0 2px}
.doc .footnote{margin-top:36px;padding-top:20px;border-top:1px solid var(--rule);
  font-size:14.5px;color:var(--muted)}
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
  .menu-btn{background:var(--accent);color:#fff;border:0;border-radius:8px;
    width:40px;height:40px;font-size:18px;cursor:pointer;flex:none}
  .topbar .tb-title{font-weight:600;color:#EFE9DB;font-size:15px}
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
<script defer src="https://cloud.umami.is/script.js" data-website-id="398cb9ae-aed6-4239-a477-6c3ec00120a0"></script>
</head>
<body>
<div id="progress"></div>

<aside class="sidebar" id="sidebar">
  <div class="brand">
    <div class="kicker">A Field Guide</div>
    <h1>__BOOK_TITLE__</h1>
    <div class="sub">__BOOK_SUB__</div>
    __LANG_SWITCH__
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

<main class="main">
  <div class="topbar">
    <button class="menu-btn" id="menuBtn" aria-label="__MENU_ARIA__">☰</button>
    <div class="tb-title">__BOOK_TITLE__ <span class="tb-sub">· __BOOK_SUB__</span></div>
  </div>
  <div class="reader">
    __CONTENT__

    <div class="colophon">
      <div class="foot-meta">__FOOT_META__</div>
    </div>
  </div>
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
})();
</script>
</body>
</html>'''


def nav_html_for(sections, active_id):
    items = []
    for s in sections:
        marker = s["numeral"] if s["numeral"] else "·"
        active = " active" if s["id"] == active_id else ""
        items.append(
            '<a class="nav-item%s" href="%s" data-target="%s">'
            '<span class="nav-mark">%s</span>'
            '<span class="nav-label">%s</span></a>'
            % (active, fname(s["id"]), s["id"], marker, html.escape(s["nav"]))
        )
    return "\n".join(items)


def lang_switch_html(current_lang, sec_id):
    links = LANGS[current_lang]["links"]
    parts = []
    for target in ["zh", "en"]:
        href = links[target] + fname(sec_id)
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


def content_for(sections, i, prev_label, next_label, lang_key):
    s = sections[i]
    prev_s = sections[i - 1] if i > 0 else None
    next_s = sections[i + 1] if i < len(sections) - 1 else None
    numeral_html = ('<div class="ch-numeral">%s</div>' % s["numeral"]) if s["numeral"] else ""
    pn = ['<nav class="pager">']
    if prev_s:
        pn.append('<a class="pager-prev" href="%s"><span class="pager-dir">← %s</span>'
                  '<span class="pager-ttl">%s</span></a>' % (fname(prev_s["id"]), prev_label, html.escape(prev_s["nav"])))
    else:
        pn.append('<span class="pager-spacer"></span>')
    if next_s:
        pn.append('<a class="pager-next" href="%s"><span class="pager-dir">%s →</span>'
                  '<span class="pager-ttl">%s</span></a>' % (fname(next_s["id"]), next_label, html.escape(next_s["nav"])))
    else:
        pn.append('<span class="pager-spacer"></span>')
    pn.append("</nav>")
    pager = "\n".join(pn)
    extra = endnote_html(lang_key, s["id"]) if s.get("is_end") else ""
    return ('<section id="%s" class="chapter" data-section="%s">\n'
            '  <header class="ch-head">\n    %s\n'
            '    <div class="ch-meta">\n'
            '      <div class="eyebrow">%s</div>\n'
            '      <h2 class="ch-title">%s</h2>\n'
            '    </div>\n  </header>\n'
            '  <div class="doc">\n    %s\n  </div>\n  %s\n  %s\n</section>'
            % (s["id"], s["id"], numeral_html, s["eyebrow"],
               html.escape(s["title"]), s["html"], extra, pager))


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
                "typeset PDF + EPUB edition</a>.</p>" % SHORT_LINKS["en"]["home"]
            )

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
               .replace("__LANG__", cfg["lang_code"])
               .replace("__PAGE_TITLE__", html.escape(cfg["page_title"]))
               .replace("__HREFLANG__", hreflang_tags(s["id"]))
               .replace("__BOOK_TITLE__", html.escape(cfg["book_title"]))
               .replace("__BOOK_SUB__", html.escape(cfg["book_sub"]))
               .replace("__TOC_LABEL__", html.escape(cfg["toc_label"]))
               .replace("__MENU_ARIA__", html.escape(cfg["menu_aria"]))
               .replace("__LANG_SWITCH__", lang_switch_html(lang_key, s["id"]))
               .replace("__NAV__", nav_html_for(sections, s["id"]))
               .replace("__CONTENT__", content_for(sections, i, cfg["prev_label"], cfg["next_label"], lang_key))
               .replace("__SIDENOTE__", cfg["sidenote_html"])
               .replace("__FOOT_META__", html.escape(cfg["foot_meta"])))
        out = re.sub(r"<table>", '<div class="table-wrap"><table>', out)
        out = re.sub(r"</table>", "</table></div>", out)
        open(os.path.join(outdir, fname(s["id"])), "w", encoding="utf-8").write(out)

    # 给 AI/LLM 抓取用的全文纯文本版（原始 Markdown 源文件，逐字复制）
    shutil.copy(cfg["src"], os.path.join(outdir, "llms-full.txt"))

    return sections


def write_sitemap(sections_by_lang):
    today = date.today().isoformat()
    ids = [s["id"] for s in sections_by_lang["en"]]  # 各语言章节一一对应，用英文版的顺序即可
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
    open("site/llms.txt", "w", encoding="utf-8").write("\n".join(lines).rstrip() + "\n")


# ---- 多语言输出：site/ 是英文（根路径），site/zh/ 是中文 ----
if os.path.isdir("site"):
    shutil.rmtree("site")
os.makedirs("site")

if os.path.isfile("_redirects"):
    shutil.copy("_redirects", os.path.join("site", "_redirects"))

total = 0
sections_by_lang = {}
for lang_key in LANGS:
    sections = build_lang(lang_key)
    sections_by_lang[lang_key] = sections
    total += len(sections)
    print("built %d pages -> %s/" % (len(sections), LANGS[lang_key]["outdir"]))

write_sitemap(sections_by_lang)
write_robots()
write_llms_txt(sections_by_lang)
print("wrote sitemap.xml, robots.txt, llms.txt")

print("total %d pages" % total)
