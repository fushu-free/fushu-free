import configparser
import json
import locale
import os
import subprocess
import sys

import requests

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


def run_tool(name, arguments):
    if name == "getDate":
        return json.dumps(get_date(), ensure_ascii=False)
    if name == "isLeapYear":
        args = json.loads(arguments or "{}")
        return json.dumps(is_leap_year(args["year"]), ensure_ascii=False)
    return json.dumps({"error": f"未知工具: {name}"}, ensure_ascii=False)


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
    config = load_config()
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
