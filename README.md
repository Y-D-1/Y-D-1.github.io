# 鱼栋一 · 个人主页

华东师范大学数学与应用数学专业本科生的个人网站，用来存放课程笔记与少量学习资料。

**在线访问：** https://Y-D-1.github.io/

## 站点内容

- **首页**：个人简介、资源链接
- **课程笔记**（[/notes/](https://Y-D-1.github.io/notes/)）：LaTeX 编写的 PDF 笔记，支持站内预览
- **考试资料**（[/exams/](https://Y-D-1.github.io/exams/)）：随机练习与题库

## 技术栈

- [Jekyll](https://jekyllrb.com/) + [GitHub Pages](https://pages.github.com/)
- 自定义现代主题（`assets/css/site-theme.scss`、`assets/js/site.js`）
- MathJax 公式渲染

## 本地预览

需要 Ruby 与 Bundler：

```bash
bundle install
bundle exec jekyll serve
```

浏览器打开 http://localhost:4000

## 目录结构

```
_pages/          独立页面（首页、笔记列表等）
_notes/          课程笔记条目
_data/home.yml   首页文案与链接
files/           笔记 PDF
images/          头像与站点图标
assets/          主题 CSS / JS
```

## 添加新笔记

1. 将 PDF 放入 `files/`
2. 在 `_notes/` 新建 Markdown，设置 `title`、`permalink` 等 front matter
3. 在正文中引用：`{% include note-pdf.html file="/files/你的文件.pdf" title=page.title %}`

## 联系方式

- GitHub：[@Y-D-1](https://github.com/Y-D-1)
- Email：jp20103117@163.com

## 许可

站点内容为个人学习笔记，仅供交流参考，请勿用于商业用途。

界面设计参考 [wexuo/home](https://github.com/wexuo/home) 与 [JieYueGo/me](https://github.com/JieYueGo/me)（MIT）。
