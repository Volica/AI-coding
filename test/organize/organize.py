# -*- coding: utf-8 -*-
"""
中文本地文件整理工具

默认整理当前用户桌面，也可以通过 --path 指定其他目录。
支持预览、重名保护、整理日志、撤销上次整理、本地规则型助手和简易桌面窗口。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


LOG_FILE_NAME = ".organize_history.jsonl"

FILE_TYPES: dict[str, list[str]] = {
    "图片": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".heic", ".ico"],
    "文档": [".pdf", ".doc", ".docx", ".txt", ".md", ".rtf", ".odt"],
    "表格": [".xls", ".xlsx", ".csv", ".tsv", ".ods"],
    "演示文稿": [".ppt", ".pptx", ".odp"],
    "视频": [".mp4", ".avi", ".mov", ".mkv", ".flv", ".webm", ".wmv"],
    "音频": [".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg"],
    "压缩包": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"],
    "代码文件": [
        ".py",
        ".js",
        ".ts",
        ".html",
        ".css",
        ".java",
        ".cpp",
        ".c",
        ".cs",
        ".go",
        ".rs",
        ".json",
        ".xml",
        ".yaml",
        ".yml",
        ".sql",
    ],
    "安装包": [".exe", ".msi", ".apk", ".dmg", ".pkg", ".deb", ".rpm"],
    "电子书与文献": [".epub", ".mobi", ".azw3", ".caj", ".nh", ".kdh"],
    "快捷方式": [".lnk", ".url"],
}

ASSISTANT_TIPS: dict[str, str] = {
    ".zip": "推荐使用 Windows 文件资源管理器、7-Zip 或 WinRAR 打开。需要分享时可继续保存为 zip。",
    ".rar": "推荐使用 WinRAR、7-Zip 或 Bandizip 打开。若要兼容更多设备，建议另存或重新压缩为 zip。",
    ".7z": "推荐使用 7-Zip 打开。7z 压缩率高，但分享给普通用户时 zip 更通用。",
    ".md": "推荐使用 VS Code、Typora 或 Obsidian 打开。需要提交作业或分享时，可以导出为 PDF。",
    ".pdf": "推荐使用 Edge、Adobe Acrobat 或 WPS 打开。学术文献可以配合 Zotero、知云文献翻译等工具管理。",
    ".caj": "这是中国知网常见文献格式，推荐使用 CAJViewer 打开；如需标注和分享，可尝试转换或另存为 PDF。",
    ".doc": "推荐使用 Word 或 WPS 打开。长期保存和分享时，建议另存为 docx 或 PDF。",
    ".docx": "推荐使用 Word 或 WPS 打开。需要固定版式时，建议另存为 PDF。",
    ".xlsx": "推荐使用 Excel 或 WPS 表格打开。需要给程序处理时，可以另存为 csv。",
    ".csv": "推荐使用 Excel、WPS 表格或 VS Code 打开。注意中文乱码时可尝试 UTF-8 编码重新导入。",
    ".pptx": "推荐使用 PowerPoint 或 WPS 演示打开。展示和提交时也可以导出为 PDF。",
    ".heic": "这是 iPhone 常见照片格式。Windows 可安装 HEIF 图像扩展，或转换为 jpg/png 后再分享。",
    ".py": "推荐使用 VS Code 或 PyCharm 打开。运行前请确认 Python 环境和依赖已经安装。",
    ".json": "推荐使用 VS Code 打开。修改时要注意双引号、逗号和括号是否符合 JSON 格式。",
    ".exe": "这是 Windows 可执行程序。只建议打开来源可信的 exe 文件，陌生下载文件请先杀毒扫描。",
    ".lnk": "这是 Windows 快捷方式。它本身不是原始文件，右键属性可以查看它指向的位置。",
}


@dataclass(frozen=True)
class MovePlan:
    source: Path
    destination: Path
    category: str


def configure_console_encoding() -> None:
    """尽量减少 Windows PowerShell 里的中文乱码。"""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


def get_default_desktop() -> Path:
    """获取当前用户桌面路径，Windows 优先读取系统配置。"""
    if os.name == "nt":
        try:
            import winreg

            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders",
            ) as key:
                desktop_path, _ = winreg.QueryValueEx(key, "Desktop")
            expanded_path = os.path.expandvars(desktop_path)
            if expanded_path:
                return Path(expanded_path)
        except Exception:
            pass

        try:
            import winreg

            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders",
            ) as key:
                desktop_path, _ = winreg.QueryValueEx(key, "Desktop")
            if desktop_path:
                return Path(desktop_path)
        except Exception:
            pass

    return Path.home() / "Desktop"


def normalize_path(path_text: str | None) -> Path:
    if not path_text:
        return get_default_desktop()
    return Path(path_text).expanduser().resolve()


def get_category_by_extension(extension: str) -> str:
    extension = extension.lower()
    for category, extensions in FILE_TYPES.items():
        if extension in extensions:
            return category
    return "其他"


def iter_candidate_files(base_dir: Path) -> Iterable[Path]:
    for file_path in base_dir.iterdir():
        if file_path.is_dir():
            continue
        if file_path.name.startswith("."):
            continue
        yield file_path


def unique_destination(destination: Path) -> Path:
    if not destination.exists():
        return destination

    stem = destination.stem
    suffix = destination.suffix
    parent = destination.parent
    index = 1
    while True:
        candidate = parent / f"{stem}_{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def build_move_plan(base_dir: Path) -> list[MovePlan]:
    if not base_dir.exists():
        raise FileNotFoundError(f"找不到目录：{base_dir}")
    if not base_dir.is_dir():
        raise NotADirectoryError(f"这不是一个目录：{base_dir}")

    plans: list[MovePlan] = []
    for file_path in iter_candidate_files(base_dir):
        category = get_category_by_extension(file_path.suffix)
        target_dir = base_dir / category
        destination = unique_destination(target_dir / file_path.name)
        plans.append(MovePlan(file_path, destination, category))
    return plans


def print_plan(plans: list[MovePlan], base_dir: Path) -> None:
    print(f"整理目录：{base_dir}")
    if not plans:
        print("没有发现需要整理的文件。")
        return

    print(f"将移动 {len(plans)} 个文件：")
    for plan in plans:
        print(f"- {plan.source.name} -> {plan.category}/{plan.destination.name}")


def write_log(base_dir: Path, run_id: str, moved_plans: list[MovePlan]) -> None:
    log_path = base_dir / LOG_FILE_NAME
    timestamp = datetime.now().isoformat(timespec="seconds")
    with log_path.open("a", encoding="utf-8") as log_file:
        for plan in moved_plans:
            record = {
                "run_id": run_id,
                "time": timestamp,
                "source": str(plan.source),
                "destination": str(plan.destination),
                "category": plan.category,
            }
            log_file.write(json.dumps(record, ensure_ascii=False) + "\n")


def organize_files(base_dir: Path, preview: bool = False) -> list[MovePlan]:
    plans = build_move_plan(base_dir)
    print_plan(plans, base_dir)
    if preview or not plans:
        return []

    return move_files(base_dir, plans)


def move_files(base_dir: Path, plans: list[MovePlan]) -> list[MovePlan]:
    moved_plans: list[MovePlan] = []
    run_id = uuid.uuid4().hex
    for plan in plans:
        try:
            plan.destination.parent.mkdir(exist_ok=True)
            shutil.move(str(plan.source), str(plan.destination))
            moved_plans.append(plan)
            print(f"已移动：{plan.source.name} -> {plan.category}/{plan.destination.name}")
        except PermissionError:
            print(f"权限不足或文件正在被占用，已跳过：{plan.source.name}")
        except Exception as error:
            print(f"移动失败：{plan.source.name}，原因：{error}")

    if moved_plans:
        write_log(base_dir, run_id, moved_plans)
        print(f"整理完成。已写入日志：{base_dir / LOG_FILE_NAME}")
    else:
        print("没有文件被成功移动。")

    return moved_plans


def read_history(base_dir: Path) -> list[dict[str, str]]:
    log_path = base_dir / LOG_FILE_NAME
    if not log_path.exists():
        return []

    records: list[dict[str, str]] = []
    with log_path.open("r", encoding="utf-8") as log_file:
        for line in log_file:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def undo_last_run(base_dir: Path) -> None:
    records = read_history(base_dir)
    if not records:
        print("没有找到可撤销的整理记录。")
        return

    last_run_id = records[-1]["run_id"]
    last_records = [record for record in records if record.get("run_id") == last_run_id]

    print(f"准备撤销上次整理，共 {len(last_records)} 个文件。")
    restored_count = 0
    for record in reversed(last_records):
        source = Path(record["source"])
        destination = Path(record["destination"])
        if not destination.exists():
            print(f"目标文件不存在，已跳过：{destination}")
            continue

        restore_path = unique_destination(source)
        try:
            restore_path.parent.mkdir(exist_ok=True)
            shutil.move(str(destination), str(restore_path))
            restored_count += 1
            print(f"已还原：{destination.name} -> {restore_path}")
        except Exception as error:
            print(f"还原失败：{destination}，原因：{error}")

    print(f"撤销完成，成功还原 {restored_count} 个文件。")


def extract_extension(text: str) -> str | None:
    cleaned = text.lower().strip()
    for category_extensions in FILE_TYPES.values():
        for extension in category_extensions:
            bare_extension = re.escape(extension.lstrip("."))
            has_bare_extension = re.search(
                rf"(?<![a-z0-9]){bare_extension}(?![a-z0-9])", cleaned
            )
            if extension in cleaned or has_bare_extension:
                return extension

    possible_path = Path(cleaned)
    if possible_path.suffix:
        return possible_path.suffix
    return None


def assistant_answer(question: str) -> str:
    extension = extract_extension(question)
    if not extension:
        return (
            "我还没识别出具体文件类型。你可以这样问：zip 怎么打开、md 文件怎么另存为、"
            "pdf 文献怎么管理，或者直接输入文件名。"
        )

    category = get_category_by_extension(extension)
    tip = ASSISTANT_TIPS.get(
        extension,
        f"这个文件会被归类到「{category}」。建议先用常见办公软件、浏览器或 VS Code 尝试打开；"
        "如果是陌生下载文件，请先确认来源可信。"
    )
    return f"{extension} 文件建议归类到「{category}」。{tip}"


def open_folder(path: Path) -> None:
    path.mkdir(exist_ok=True)
    if os.name == "nt":
        os.startfile(path)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        os.system(f'open "{path}"')
    else:
        os.system(f'xdg-open "{path}"')


def launch_gui(base_dir: Path) -> None:
    import tkinter as tk
    from tkinter import messagebox, ttk

    root = tk.Tk()
    root.title("本地文件整理助手")
    root.geometry("420x560")
    root.resizable(False, False)

    main = ttk.Frame(root, padding=14)
    main.pack(fill="both", expand=True)

    title = ttk.Label(main, text="本地文件整理助手", font=("Microsoft YaHei UI", 16, "bold"))
    title.pack(anchor="w")

    path_label = ttk.Label(main, text=f"整理路径：{base_dir}", wraplength=380)
    path_label.pack(anchor="w", pady=(6, 12))

    grid = ttk.Frame(main)
    grid.pack(fill="x")

    category_labels: dict[str, ttk.Label] = {}

    def refresh_counts() -> None:
        counts = {category: 0 for category in FILE_TYPES}
        counts["其他"] = 0
        for file_path in iter_candidate_files(base_dir):
            counts[get_category_by_extension(file_path.suffix)] += 1

        for category, label in category_labels.items():
            label.configure(text=f"{category}\n{counts.get(category, 0)} 个待整理文件")

    def add_category_card(row: int, column: int, category: str) -> None:
        frame = ttk.Frame(grid, padding=8, relief="ridge")
        frame.grid(row=row, column=column, sticky="nsew", padx=4, pady=4)
        label = ttk.Label(frame, text=category, anchor="center", justify="center")
        label.pack(fill="x")
        button = ttk.Button(frame, text="打开", command=lambda: open_folder(base_dir / category))
        button.pack(pady=(8, 0))
        category_labels[category] = label

    shown_categories = list(FILE_TYPES.keys()) + ["其他"]
    for index, category in enumerate(shown_categories):
        add_category_card(index // 2, index % 2, category)
    grid.columnconfigure(0, weight=1)
    grid.columnconfigure(1, weight=1)

    action_frame = ttk.Frame(main)
    action_frame.pack(fill="x", pady=(12, 8))

    def do_preview() -> None:
        plans = build_move_plan(base_dir)
        if not plans:
            messagebox.showinfo("预览整理", "没有发现需要整理的文件。")
            return
        preview_lines = [
            f"{plan.source.name} -> {plan.category}/{plan.destination.name}"
            for plan in plans[:20]
        ]
        more = "" if len(plans) <= 20 else f"\n还有 {len(plans) - 20} 个文件未显示。"
        messagebox.showinfo("预览整理", "\n".join(preview_lines) + more)

    def do_organize() -> None:
        plans = build_move_plan(base_dir)
        if not plans:
            messagebox.showinfo("开始整理", "没有发现需要整理的文件。")
            return
        confirmed = messagebox.askyesno("开始整理", f"确认移动 {len(plans)} 个文件吗？")
        if not confirmed:
            return
        moved = organize_files(base_dir, preview=False)
        refresh_counts()
        messagebox.showinfo("整理完成", f"成功移动 {len(moved)} 个文件。")

    def do_undo() -> None:
        confirmed = messagebox.askyesno("撤销整理", "确认撤销上一次整理吗？")
        if confirmed:
            undo_last_run(base_dir)
            refresh_counts()

    ttk.Button(action_frame, text="预览整理", command=do_preview).pack(side="left", expand=True, fill="x", padx=3)
    ttk.Button(action_frame, text="开始整理", command=do_organize).pack(side="left", expand=True, fill="x", padx=3)
    ttk.Button(action_frame, text="撤销上次", command=do_undo).pack(side="left", expand=True, fill="x", padx=3)

    assistant_frame = ttk.LabelFrame(main, text="问问助手", padding=8)
    assistant_frame.pack(fill="both", expand=True, pady=(8, 0))

    question_var = tk.StringVar()
    entry = ttk.Entry(assistant_frame, textvariable=question_var)
    entry.pack(fill="x")

    answer_box = tk.Text(assistant_frame, height=5, wrap="word")
    answer_box.pack(fill="both", expand=True, pady=(8, 0))

    def ask_assistant() -> None:
        answer = assistant_answer(question_var.get())
        answer_box.delete("1.0", "end")
        answer_box.insert("1.0", answer)

    ttk.Button(assistant_frame, text="询问", command=ask_assistant).pack(anchor="e", pady=(8, 0))
    entry.bind("<Return>", lambda _event: ask_assistant())

    refresh_counts()
    root.mainloop()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="中文本地文件整理工具")
    parser.add_argument("--path", help="要整理的目录。不填写时默认整理当前用户桌面。")
    parser.add_argument("--preview", action="store_true", help="只预览移动计划，不实际移动文件。")
    parser.add_argument("--yes", action="store_true", help="跳过确认，直接整理。")
    parser.add_argument("--undo", action="store_true", help="撤销上一次整理。")
    parser.add_argument("--ask", help="向本地规则型助手提问，例如：zip 怎么打开？")
    parser.add_argument("--gui", action="store_true", help="打开简易桌面应用窗口。")
    return parser.parse_args()


def main() -> None:
    configure_console_encoding()
    args = parse_args()
    base_dir = normalize_path(args.path)

    if args.gui:
        launch_gui(base_dir)
        return

    if args.ask:
        print(assistant_answer(args.ask))
        return

    if args.undo:
        undo_last_run(base_dir)
        return

    if args.preview:
        organize_files(base_dir, preview=True)
        return

    try:
        plans = build_move_plan(base_dir)
        print_plan(plans, base_dir)
    except (FileNotFoundError, NotADirectoryError) as error:
        print(error)
        return

    if not plans:
        return

    if not args.yes:
        answer = input("是否开始整理？输入 y 确认，其他任意输入取消：").strip().lower()
        if answer not in {"y", "yes"}:
            print("已取消整理。")
            return

    move_files(base_dir, plans)


if __name__ == "__main__":
    main()
