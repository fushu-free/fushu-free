import configparser
import json
import sys

import requests


def load_config(path="config.ini"):
    cfg = configparser.ConfigParser()
    cfg.read(path, encoding="utf-8")
    return cfg["llm"]


def stream_chat(messages, cfg):
    resp = requests.post(
        f"{cfg['base_url'].rstrip('/')}/chat/completions",
        headers={"Authorization": f"Bearer {cfg['api_key']}"},
        json={
            "model": cfg["model"],
            "messages": messages,
            "temperature": cfg.getfloat("temperature"),
            "max_tokens": cfg.getint("max_tokens"),
            "stream": True,
        },
        stream=True,
        timeout=60,
    )
    resp.raise_for_status()
    resp.encoding = "utf-8"
    reply = []
    for line in resp.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data:"):
            continue
        data = line[5:].strip()
        if data == "[DONE]":
            break
        content = json.loads(data)["choices"][0].get("delta", {}).get("content")
        if content:
            print(content, end="", flush=True)
            reply.append(content)
    return "".join(reply)


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
            answer = stream_chat(messages, config)
            messages.append({"role": "assistant", "content": answer})
            print()
        except KeyboardInterrupt:
            print()
            break