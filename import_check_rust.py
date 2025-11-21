# import_check_rust.py
import re
import requests
from Levenshtein import distance

# 常见 crate 列表（用于离线 fallback / typo 检测）
POPULAR_CRATES = [
    "serde", "serde_json", "tokio", "rand", "regex", "chrono",
    "reqwest", "clap", "hyper", "anyhow", "thiserror", "log", "env_logger"
]

CRATES_IO_API = "https://crates.io/api/v1/crates/{}"
REQUEST_TIMEOUT = 3.0

def parse_crates_from_code(code_str: str):
    """
    从 Rust 源码中提取可能的 crate 名称（从 `use` 和 `extern crate` 中）。
    返回 set(crate_name)
    """
    crates = set()
    # 匹配 `use crate_name::...;` 或 `use crate_name as alias;`
    for m in re.finditer(r'^\s*use\s+([a-zA-Z0-9_]+)', code_str, re.MULTILINE):
        crates.add(m.group(1).split("::")[0])
    # 匹配 extern crate foo;
    for m in re.finditer(r'^\s*extern\s+crate\s+([a-zA-Z0-9_]+)', code_str, re.MULTILINE):
        crates.add(m.group(1))
    # 也尝试匹配可能来自 macros / attributes like `#[macro_use] extern crate foo;`
    return {c for c in crates if c and c != "crate" and c != "self"}

def check_crate_exists(crate_name: str):
    """
    查询 crates.io API。失败时返回 False（上层可决定是否 fallback）。
    """
    try:
        resp = requests.get(CRATES_IO_API.format(crate_name), timeout=REQUEST_TIMEOUT)
        return resp.status_code == 200
    except Exception:
        # 网络不可用或超时 -> 上层决定是否以 POPULAR_CRATES 作为近似
        return False

def is_typo_attack(crate_name: str, max_distance: int = 1):
    for p in POPULAR_CRATES:
        if crate_name == p:
            continue  # 正常包，跳过
        if distance(crate_name, p) <= max_distance:
            return f"[MALICIOUS-TYPO] Suspicious crate name (typo) -> '{crate_name}' matched with '{p}'"
    return None

def clean_markdown_from_code(code_str: str):
    """
    从Rust代码中移除所有的Markdown语法（如```rust```块），确保编译器可以正确识别Rust代码。
    """
    # 去除所有的markdown代码块标记
    code_str = re.sub(r'```[a-zA-Z0-9_]*\n', '', code_str)  # 移除代码块的开始标记
    code_str = re.sub(r'```', '', code_str)  # 移除代码块的结束标记
    
    # 去除所有的非Rust文本，例如分析文字
    code_str = re.sub(r'\d+\..*', '', code_str)  # 移除类似 "1. 分析: ..." 的分析文字

    return code_str


def check_rust_imports_valid(code_str: str, allow_fallback_popular=True):
    """
    Validate Rust imports/crates.
    Returns (ok: bool, message: str)
    流程：
      1) 提取 crates
      2) 忽略 std
      3) 检查 typo（基于 POPULAR_CRATES）
      4) 查询 crates.io（失败则 fallback 到 POPULAR_CRATES if allow_fallback_popular）
    """

    # 添加针对代码中 Markdown 语法的清理
    clean_code = clean_markdown_from_code(code_str)

    crates = parse_crates_from_code(clean_code)
    # crates = parse_crates_from_code(code_str)
    if not crates:
        return True, "No external crates found."

    errors = []
    for crate in sorted(crates):
        if crate == "std":
            continue

        # Typo detection first (敏感，优先报告)
        if is_typo_attack(crate):
            errors.append(f"[MALICIOUS-TYPO] Suspicious crate name (typo) -> '{crate}'")
            continue

        exists = check_crate_exists(crate)
        if exists:
            continue

        # 如果查询失败或返回 404，尝试用 POPULAR_CRATES 做降级允许
        if allow_fallback_popular:
            if crate in POPULAR_CRATES:
                # 在流量受限时，认为常见 crate 可接受
                continue
            else:
                errors.append(f"[UNKNOWN CRATE] '{crate}' not found on crates.io (or request failed)")
        else:
            errors.append(f"[UNKNOWN CRATE] '{crate}' not found on crates.io")

    return len(errors) == 0, "\n".join(errors)
