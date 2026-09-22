# 理解现代大语言模型系统-从RAG到全景（在线阅读站）

从 `content/` 里的中英文 Markdown 自动生成「一章一页」的多页静态阅读站，输出到 `site/`（英文，根路径）和 `site/zh/`（中文）。

## 目录结构

```
.
├─ content/
│   ├─ 理解现代LLM系统_从RAG到全景.md      ← 中文内容源
│   └─ 理解现代LLM系统_从RAG到全景.en.md   ← 英文内容源（与中文一一对应）
├─ build.py                              ← 生成脚本（读 content，输出 site，中英文各一份）
├─ requirements.txt                      ← 依赖（markdown）
├─ .gitignore                            ← 忽略 site/（由构建生成，不入库）
└─ README.md
```

## 本地预览（可选）

```bash
pip install -r requirements.txt
python build.py
# 打开 site/index.html 看英文版，site/zh/index.html 看中文版
# 侧栏「中文 / EN」按钮可以在两个语言版本间跳转到同一章节
```

## 怎么修改内容

**中文**改 `content/理解现代LLM系统_从RAG到全景.md`，**英文**改 `content/理解现代LLM系统_从RAG到全景.en.md`。

两份文件都用 `##` 开头的行分节，脚本按「第几节」（而不是标题文字）判断章节类型——第 1 节固定是前言，最后 2 节固定是附录、速记卡片，中间全部是编号章节。**因此两份文件的分节数量和顺序必须严格一一对应**，否则中英文章节会错位。改完重新 `python build.py` 即可；接入下面的自动部署后，`git push` 就会自动重建。

## URL 结构

- 英文在根路径（`/`、`/ch1`、`/ch3`…）
- 中文在 `/zh/` 前缀下（`/zh/`、`/zh/ch1`、`/zh/ch3`…）
- 每页 `<head>` 里带 `hreflang` 互链标注（`x-default` 指向英文根路径），方便搜索引擎识别中英文对应关系
- 旧版英文在 `/en/` 前缀下，`_redirects` 里有一条 `/en/* → /:splat` 把旧链接跳到新位置；旧版中文根路径（`/`、`/ch1`…）**无法**重定向到 `/zh/`——这些路径现在被新的英文页面复用，_redirects 的匹配发生在静态文件之前，写规则会连新英文页面一起跳走。访问这些旧中文书签的人会直接看到对应的英文页

## 换付费出站链接

打开 `build.py`，找到 `SHORT_LINKS` 字典，里面是每个入口位置对应的固定短链（`ymjr.de/llmbook-*`）。网站代码只放短链本身，不拼 UTM 参数——短链跳到 Gumroad 商品页时带什么 UTM，是在短链服务那端配置的。中文页面末尾（ch6/appendix/cheatsheet）目前故意不放链接，因为还没有对应入口。改完 `SHORT_LINKS` 里的值，重新构建即可全站生效。

## 部署到 Cloudflare Pages（Git 自动构建）

在 Cloudflare Pages 里连接本仓库，构建设置：

- **构建命令 / Build command**：`pip install -r requirements.txt && python build.py`
- **输出目录 / Build output directory**：`site`
- **框架预设 / Framework preset**：None（无）

连接后，每次 `git push`，Cloudflare 会自动跑上面的命令、重新生成页面并部署。

## 日常工作流

```bash
# 改完 content/ 里的 Markdown 后：
git add -A
git commit -m "更新：说明改了啥"
git push
# → Cloudflare 自动重建并上线，几十秒后线上就是最新版
```

Git 同时也是版本管理：每次提交都有记录，可随时回看历史、回滚到任意版本。
