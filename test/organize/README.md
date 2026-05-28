# 本地文件整理助手

这是一个中文本地文件管理小工具，可以把桌面或指定目录里的文件按类型自动整理到不同文件夹中。

## 运行方式

默认整理当前用户桌面：

```bash
python test/organize/organize.py
```

脚本会先显示移动预览，并询问是否确认整理。

整理指定目录：

```bash
python test/organize/organize.py --path "C:\tmp"
```

只预览，不移动文件：

```bash
python test/organize/organize.py --preview
```

跳过确认，直接整理：

```bash
python test/organize/organize.py --yes
```

撤销上一次整理：

```bash
python test/organize/organize.py --undo
```

打开简易桌面窗口：

```bash
python test/organize/organize.py --gui
```

询问本地助手：

```bash
python test/organize/organize.py --ask "zip 怎么打开"
python test/organize/organize.py --ask "pdf 文献怎么管理"
python test/organize/organize.py --ask "md 文件怎么另存为"
```

## 分类规则

脚本目前支持这些中文分类：

- 图片：jpg、jpeg、png、gif、bmp、webp、svg、heic、ico
- 文档：pdf、doc、docx、txt、md、rtf、odt
- 表格：xls、xlsx、csv、tsv、ods
- 演示文稿：ppt、pptx、odp
- 视频：mp4、avi、mov、mkv、flv、webm、wmv
- 音频：mp3、wav、flac、m4a、aac、ogg
- 压缩包：zip、rar、7z、tar、gz、bz2、xz
- 代码文件：py、js、ts、html、css、java、cpp、c、cs、go、rs、json、xml、yaml、yml、sql
- 安装包：exe、msi、apk、dmg、pkg、deb、rpm
- 电子书与文献：epub、mobi、azw3、caj、nh、kdh
- 快捷方式：lnk、url
- 其他：未匹配的文件类型

## 安全能力

- 预览模式：整理前先显示文件会被移动到哪里。
- 重名保护：目标文件已存在时，会自动生成 `文件名_1.ext`。
- 整理日志：每次成功移动都会写入 `.organize_history.jsonl`。
- 撤销整理：可以根据日志撤销上一次整理。
- 目录保护：脚本只整理目标目录第一层文件，不会递归移动文件夹里的内容。

## 本地助手

助手当前是规则型问答，不依赖网络或 API。它可以回答常见文件类型的打开方式、另存建议和分类建议，例如 zip、md、pdf、caj、heic 等。

后续如果要接入大模型 API，可以保留当前规则作为兜底答案，让大模型负责更自然的解释和更复杂的使用建议。
