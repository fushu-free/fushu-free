import configparser
import json
import locale
import mimetypes
import os
import pathlib
import shutil
import subprocess
import sys

import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TEXT_EXTENSIONS = {
    ".txt", ".text", ".md", ".markdown", ".rst", ".log",
    ".py", ".pyw", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx",
    ".html", ".htm", ".css", ".scss", ".sass", ".less", ".vue", ".svelte",
    ".json", ".jsonc", ".xml", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf",
    ".csv", ".tsv", ".sql", ".sh", ".bash", ".bat", ".cmd", ".ps1",
    ".java", ".c", ".h", ".cpp", ".hpp", ".cc", ".cs", ".go", ".rs",
    ".rb", ".php", ".r", ".m", ".swift", ".kt", ".kts", ".gradle",
    ".properties", ".env", ".gitignore", ".dockerignore", ".dockerfile",
    ".tex", ".adoc", ".rtf",
}

TEXT_MIME_TYPES = {
    "application/json",
    "application/xml",
    "application/javascript",
    "application/x-javascript",
    "application/x-sh",
    "application/sql",
    "application/x-httpd-php",
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "getDate",
            "description": "获取当前电脑的日期和时间。通过调用系统本地 date/time 命令实现，返回日期和时间字符串。",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "isLeapYear",
            "description": "判断指定的年份是否是闰年。输入一个年份（整数），返回该年份是否为闰年。",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {
                        "type": "integer",
                        "description": "要判断的年份，例如 2024",
                    }
                },
                "required": ["year"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "getCurrentWorkingDirectory",
            "description": "获取当前 Python 进程的工作目录（绝对路径）。",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "listDirectory",
            "description": "列出指定目录下的所有文件和子目录，返回名称、绝对路径、类型、大小和修改时间。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "要列出的目录路径，支持相对路径或绝对路径，例如 . 或 D:/projects",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "getFileType",
            "description": "获取指定文件的类型，返回扩展名、MIME 类型、是否为纯文本以及大类别（文本/图片/音频/视频/其他）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "要检查的文件路径",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "readTextFile",
            "description": "读取指定纯文本文件的完整内容。仅支持纯文本格式文件，遇到二进制文件会返回错误。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "要读取的纯文本文件路径",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "createFile",
            "description": "在指定目录下根据文件名创建新文件，可同时写入初始内容。如果目录不存在会自动创建。",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "目标目录路径，不存在时会自动创建",
                    },
                    "filename": {
                        "type": "string",
                        "description": "新文件名，只能包含文件名本身，不能包含路径分隔符",
                    },
                    "content": {
                        "type": "string",
                        "description": "写入文件的初始文本内容，默认为空字符串",
                    },
                    "overwrite": {
                        "type": "boolean",
                        "description": "文件已存在时是否覆盖，默认 false",
                    },
                },
                "required": ["directory", "filename"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "editFileContent",
            "description": "编辑指定纯文本文件的内容。支持覆盖（overwrite）、追加（append）或替换文本（replace，需提供 old_text 和 new_text）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "要编辑的纯文本文件路径",
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["overwrite", "append", "replace"],
                        "description": "编辑模式，默认 overwrite",
                    },
                    "content": {
                        "type": "string",
                        "description": "overwrite 或 append 模式下要写入的文本内容",
                    },
                    "old_text": {
                        "type": "string",
                        "description": "replace 模式下要被替换的旧文本",
                    },
                    "new_text": {
                        "type": "string",
                        "description": "replace 模式下替换成的新文本",
                    },
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "createDirectory",
            "description": "创建新目录，默认自动创建所有缺失的父目录。",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "要创建的目录路径",
                    },
                    "parents": {
                        "type": "boolean",
                        "description": "是否同时创建父目录，默认 true",
                    },
                },
                "required": ["directory"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "deleteDirectory",
            "description": "删除指定目录，支持删除非空目录（递归删除其中的所有内容），操作不可恢复。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "要删除的目录路径",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "deleteFile",
            "description": "删除指定的文件。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "要删除的文件路径",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "renamePath",
            "description": "重命名指定的文件或目录，新名称必须位于同一父目录下。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "要重命名的文件或目录路径",
                    },
                    "new_name": {
                        "type": "string",
                        "description": "新的文件或目录名称，只能包含名称本身，不能包含路径分隔符",
                    },
                },
                "required": ["path", "new_name"],
            },
        },
    },
]


def load_config(path="config.ini"):
    cfg = configparser.ConfigParser()
    cfg.read(path, encoding="utf-8")
    return cfg["llm"]


def get_date():
    if os.name == "nt":
        cmd = ["cmd", "/c", "date /t & time /t"]
    else:
        cmd = ["date"]
    proc = subprocess.run(cmd, capture_output=True, check=True)
    encoding = locale.getpreferredencoding(False) or "utf-8"
    text = proc.stdout.decode(encoding, errors="replace").strip()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    date_str = lines[0] if lines else ""
    time_str = lines[1] if len(lines) > 1 else ""
    return {"date": date_str, "time": time_str, "raw": text}


def is_leap_year(year):
    year = int(year)
    leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
    return {"year": year, "is_leap_year": leap}


def _resolve(path):
    if not isinstance(path, str) or not path.strip():
        raise ValueError("路径不能为空")
    return os.path.abspath(os.path.expanduser(path.strip()))


def _is_text_file(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in TEXT_EXTENSIONS:
        return True
    mime, _ = mimetypes.guess_type(path)
    if mime and (mime.startswith("text/") or mime in TEXT_MIME_TYPES):
        return True
    try:
        with open(path, "rb") as f:
            sample = f.read(8192)
        if b"\x00" in sample:
            return False
        sample.decode("utf-8")
        return True
    except (OSError, UnicodeDecodeError):
        return False


def _read_text(path):
    encodings = ["utf-8-sig", "utf-8", locale.getpreferredencoding(False), "gbk", "latin-1"]
    tried = []
    last_error = None
    for encoding in encodings:
        if not encoding or encoding.lower() in tried:
            continue
        tried.append(encoding.lower())
        try:
            with open(path, "r", encoding=encoding) as f:
                return f.read(), encoding
        except UnicodeDecodeError as exc:
            last_error = exc
    raise RuntimeError(f"无法解码该文件为纯文本: {last_error}")


def _write_text(path, content, mode="w"):
    with open(path, mode, encoding="utf-8", newline="") as f:
        f.write(content)


def get_current_working_directory():
    return {"cwd": os.getcwd()}


def list_directory(path):
    target = _resolve(path)
    if not os.path.isdir(target):
        raise NotADirectoryError(f"目录不存在或不是目录: {target}")
    entries = []
    with os.scandir(target) as it:
        for entry in it:
            try:
                stat = entry.stat()
                size = stat.st_size
                modified = stat.st_mtime
            except OSError:
                size = None
                modified = None
            entries.append(
                {
                    "name": entry.name,
                    "path": os.path.abspath(entry.path),
                    "type": "directory" if entry.is_dir() else "file",
                    "size": size,
                    "modified": modified,
                }
            )
    entries.sort(key=lambda item: (item["type"] != "directory", item["name"].lower()))
    return {"directory": target, "count": len(entries), "entries": entries}


def get_file_type(path):
    target = _resolve(path)
    if not os.path.exists(target):
        raise FileNotFoundError(f"路径不存在: {target}")
    if os.path.isdir(target):
        return {
            "path": target,
            "type": "directory",
            "extension": "",
            "mime_type": None,
            "is_text": False,
            "category": "目录",
        }
    extension = os.path.splitext(target)[1].lower()
    mime, _ = mimetypes.guess_type(target)
    is_text = _is_text_file(target)
    if is_text:
        category = "文本"
    elif mime:
        category = mime.split("/", 1)[0]
    else:
        category = "其他"
    return {
        "path": target,
        "type": "file",
        "extension": extension,
        "mime_type": mime,
        "is_text": is_text,
        "category": category,
    }


def read_text_file(path):
    target = _resolve(path)
    if not os.path.isfile(target):
        raise FileNotFoundError(f"文件不存在或不是普通文件: {target}")
    if not _is_text_file(target):
        raise ValueError(f"该文件不是纯文本格式，无法读取: {target}")
    content, encoding = _read_text(target)
    return {
        "path": target,
        "size": os.path.getsize(target),
        "encoding": encoding,
        "content": content,
    }


def create_file(directory, filename, content="", overwrite=False):
    if not isinstance(filename, str) or not filename.strip():
        raise ValueError("文件名不能为空")
    filename = filename.strip()
    if os.path.basename(filename) != filename or filename in (".", ".."):
        raise ValueError("filename 只能是文件名，不能包含路径分隔符")
    directory_path = _resolve(directory)
    os.makedirs(directory_path, exist_ok=True)
    target = os.path.join(directory_path, filename)
    if os.path.exists(target):
        if os.path.isdir(target):
            raise IsADirectoryError(f"同名目录已存在: {target}")
        if not overwrite:
            raise FileExistsError(f"文件已存在，如需覆盖请设置 overwrite=true: {target}")
    _write_text(target, content or "")
    return {"path": target, "size": os.path.getsize(target), "created": True}


def edit_file_content(path, mode="overwrite", content=None, old_text=None, new_text=None):
    target = _resolve(path)
    if not os.path.isfile(target):
        raise FileNotFoundError(f"文件不存在或不是普通文件: {target}")
    if not _is_text_file(target):
        raise ValueError(f"该文件不是纯文本格式，无法编辑: {target}")
    mode = (mode or "overwrite").lower()
    if mode == "overwrite":
        _write_text(target, content or "")
        action = "overwrite"
    elif mode == "append":
        _write_text(target, content or "", mode="a")
        action = "append"
    elif mode == "replace":
        if old_text is None:
            raise ValueError("replace 模式必须提供 old_text")
        current, _ = _read_text(target)
        if old_text not in current:
            raise ValueError("未在文件中找到 old_text")
        _write_text(target, current.replace(old_text, new_text or ""))
        action = "replace"
    else:
        raise ValueError(f"不支持的编辑模式: {mode}")
    return {"path": target, "action": action, "size": os.path.getsize(target)}


def create_directory(directory, parents=True):
    target = _resolve(directory)
    if os.path.exists(target):
        if os.path.isdir(target):
            return {"path": target, "created": False, "message": "目录已存在"}
        raise NotADirectoryError(f"同名文件已存在: {target}")
    if parents:
        os.makedirs(target, exist_ok=True)
    else:
        os.mkdir(target)
    return {"path": target, "created": True}


def delete_directory(path):
    target = _resolve(path)
    root = os.path.abspath(os.sep)
    if target == root or os.path.dirname(target) == target:
        raise ValueError("不能删除文件系统根目录")
    if os.path.abspath(os.getcwd()) == target:
        raise ValueError("不能删除当前工作目录")
    if not os.path.exists(target):
        raise FileNotFoundError(f"目录不存在: {target}")
    if not os.path.isdir(target):
        raise NotADirectoryError(f"路径不是目录: {target}")
    shutil.rmtree(target)
    return {"path": target, "deleted": True}


def delete_file(path):
    target = _resolve(path)
    if not os.path.exists(target):
        raise FileNotFoundError(f"文件不存在: {target}")
    if not os.path.isfile(target):
        raise IsADirectoryError(f"路径不是普通文件: {target}")
    os.remove(target)
    return {"path": target, "deleted": True}


def rename_path(path, new_name):
    source = _resolve(path)
    if not isinstance(new_name, str) or not new_name.strip():
        raise ValueError("新名称不能为空")
    new_name = new_name.strip()
    if os.path.basename(new_name) != new_name or new_name in (".", ".."):
        raise ValueError("new_name 只能是名称本身，不能包含路径分隔符")
    if not os.path.exists(source):
        raise FileNotFoundError(f"路径不存在: {source}")
    destination = os.path.join(os.path.dirname(source), new_name)
    if os.path.exists(destination):
        raise FileExistsError(f"目标名称已存在: {destination}")
    os.rename(source, destination)
    return {"old_path": source, "new_path": destination, "renamed": True}


def run_tool(name, arguments):
    try:
        args = json.loads(arguments or "{}")
        if name == "getDate":
            result = get_date()
        elif name == "isLeapYear":
            result = is_leap_year(args["year"])
        elif name == "getCurrentWorkingDirectory":
            result = get_current_working_directory()
        elif name == "listDirectory":
            result = list_directory(args["path"])
        elif name == "getFileType":
            result = get_file_type(args["path"])
        elif name == "readTextFile":
            result = read_text_file(args["path"])
        elif name == "createFile":
            result = create_file(
                args["directory"],
                args["filename"],
                args.get("content", ""),
                bool(args.get("overwrite", False)),
            )
        elif name == "editFileContent":
            result = edit_file_content(
                args["path"],
                args.get("mode", "overwrite"),
                args.get("content"),
                args.get("old_text"),
                args.get("new_text"),
            )
        elif name == "createDirectory":
            result = create_directory(args["directory"], bool(args.get("parents", True)))
        elif name == "deleteDirectory":
            result = delete_directory(args["path"])
        elif name == "deleteFile":
            result = delete_file(args["path"])
        elif name == "renamePath":
            result = rename_path(args["path"], args["new_name"])
        else:
            return json.dumps({"error": f"未知工具: {name}"}, ensure_ascii=False)
        return json.dumps(result, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)


def stream_chat(messages, cfg):
    resp = requests.post(
        f"{cfg['base_url'].rstrip('/')}/chat/completions",
        headers={"Authorization": f"Bearer {cfg['api_key']}"},
        json={
            "model": cfg["model"],
            "messages": messages,
            "temperature": cfg.getfloat("temperature"),
            "max_tokens": cfg.getint("max_tokens"),
            "tools": TOOLS,
            "stream": True,
        },
        stream=True,
        timeout=60,
    )
    resp.raise_for_status()
    resp.encoding = "utf-8"
    reply = []
    tool_calls = {}
    for line in resp.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data:"):
            continue
        data = line[5:].strip()
        if data == "[DONE]":
            break
        delta = json.loads(data)["choices"][0].get("delta", {}) or {}
        content = delta.get("content")
        if content:
            print(content, end="", flush=True)
            reply.append(content)
        for tc in delta.get("tool_calls") or []:
            index = tc.get("index", 0)
            slot = tool_calls.setdefault(
                index,
                {"id": "", "type": "function", "function": {"name": "", "arguments": ""}},
            )
            if tc.get("id"):
                slot["id"] = tc["id"]
            fn = tc.get("function") or {}
            if fn.get("name"):
                slot["function"]["name"] += fn["name"]
            if fn.get("arguments"):
                slot["function"]["arguments"] += fn["arguments"]
    calls = [tool_calls[i] for i in sorted(tool_calls)]
    for n, call in enumerate(calls, 1):
        if not call["id"]:
            call["id"] = f"call_{n}"
    return "".join(reply), calls


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    config = load_config(os.path.join(BASE_DIR, "config.ini"))
    messages = []
    while True:
        try:
            question = input("问题: ").strip()
            if not question:
                continue
            messages.append({"role": "user", "content": question})
            while True:
                answer, tool_calls = stream_chat(messages, config)
                assistant_msg = {"role": "assistant", "content": answer}
                if tool_calls:
                    assistant_msg["tool_calls"] = tool_calls
                messages.append(assistant_msg)
                if not tool_calls:
                    break
                print()
                for call in tool_calls:
                    name = call["function"]["name"]
                    args = call["function"]["arguments"] or "{}"
                    print(f"[调用工具] {name}({args})")
                    result = run_tool(name, args)
                    print(f"[工具结果] {result}")
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": call["id"],
                            "content": result,
                        }
                    )
            print()
        except KeyboardInterrupt:
            print()
            break
