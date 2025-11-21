# import_check_js.py
import re
import requests
from Levenshtein import distance

POPULAR_NPM = [
    "express", "react", "lodash", "axios", "moment", "chalk",
    "webpack", "vite", "vue", "typescript", "next", "react-dom"
]

NODE_BUILTINS = [
    "fs", "path", "http", "https", "url", "crypto", "os", "events",
    "buffer", "stream", "util", "zlib", "net", "tls", "dns", "child_process"
]

NPM_REGISTRY = "https://registry.npmjs.org/{}"
REQUEST_TIMEOUT = 3.0


def parse_packages_from_js(code_str: str):
    pkgs = set()

    for m in re.finditer(r'import\s+(?:[\s\S]+?\s+from\s+)?[\'"]([^\'"]+)[\'"]', code_str):
        pkg = m.group(1)
        if not pkg.startswith('.') and not pkg.startswith('/'):
            pkgs.add(pkg.split('/')[0])

    for m in re.finditer(r'require\(\s*[\'"]([^\'"]+)[\'"]\s*\)', code_str):
        pkg = m.group(1)
        if not pkg.startswith('.') and not pkg.startswith('/'):
            pkgs.add(pkg.split('/')[0])

    return pkgs


def check_npm_exists(pkg_name: str):
    try:
        resp = requests.get(NPM_REGISTRY.format(pkg_name), timeout=REQUEST_TIMEOUT)
        return resp.status_code == 200
    except Exception:
        return False


def is_typo_attack(pkg_name: str, max_distance: int = 1):
    for p in POPULAR_NPM:
        if pkg_name == p:
            continue  # 正常包，跳过
        if distance(pkg_name, p) <= max_distance:
            return True
    return False


def check_js_imports_valid(code_str: str):
    """
    安全检测策略（ImportSnare 风格）：
      1. Node 内置模块 → 永远允许
      2. Typo（1 字母以内） → 直接判恶意
      3. 非白名单包 → 标记为 UNAPPROVED（即使存在于 npm）
      4. 白名单包才检查 npm registry
    """
    pkgs = parse_packages_from_js(code_str)
    if not pkgs:
        return True, "No external npm packages found."

    errors = []

    for pkg in sorted(pkgs):

        if pkg in NODE_BUILTINS:
            continue

        # === 攻击检测：typo-squatting ===
        if is_typo_attack(pkg):
            errors.append(f"[MALICIOUS-TYPO] Suspicious npm package -> '{pkg}'")
            continue

        # === 必须在白名单 POPULAR_NPM 之中 ===
        if pkg not in POPULAR_NPM:
            errors.append(f"[UNAPPROVED NPM] '{pkg}' is not in trusted popular package list")
            continue

        # === 白名单包必须存在于 npm ===
        if not check_npm_exists(pkg):
            errors.append(f"[NOT IN REGISTRY] '{pkg}' not found in registry.npmjs.org")
            continue

    return len(errors) == 0, "\n".join(errors)
