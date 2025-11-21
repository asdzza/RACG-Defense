# cgra_agent.py
import json
import os
import re
from openai import OpenAI

from import_check import check_imports_valid        
from import_check_rust import check_rust_imports_valid
from import_check_js import check_js_imports_valid

from compiler_check import check_python, check_python_mypy, check_cpp, check_rust, check_js


# 初始化DeepSeek客户端
# client = OpenAI(
#     api_key=os.getenv("DEEPSEEK_API_KEY"),  # 从环境变量获取API密钥
#     base_url="https://api.deepseek.com/v1"  # DeepSeek API端点
# )
# export ZJU_API_KEY="sk-ZtaShsjvRHZnCYMm129751042d5f41DbBb6b142388464255"
client = OpenAI(
    api_key=os.getenv("ZJU_API_KEY"),  # 你自己换成环境变量的名字
    base_url="https://chat.zju.edu.cn/api/ai/v1"
)



CGRA_PROMPT = """
You are the Compiler-Guided Repair Agent (CGRA).
You fix broken RACG-generated code strictly using compiler feedback.

Supported languages:
- Python  (CPython + mypy)
- C++     (g++)
- Rust    (rustc)
- JavaScript (node --check)

Process:
1. Analyze compiler errors.
2. Produce a JSON repair plan.
3. Rewrite the entire corrected code.
4. Perform a self-check against imports, dependencies, typos, and syntax errors.

Output ONLY the final code in a <code> block.
"""

def extract_rust_code(output: str) -> str:
    """
    提取 LLM 返回内容中的纯 Rust 代码，过滤掉解释文字。
    """

    # 1) 优先提取 <code>...</code>
    m = re.search(r"<code>([\s\S]*?)</code>", output)
    if m:
        text = m.group(1)
    else:
        # 2) fallback 提取 markdown ``` 代码块
        m2 = re.search(r"```(?:rust)?\s([\s\S]*?)```", output)
        if m2:
            text = m2.group(1)
        else:
            # 3) fallback: 使用整个返回内容
            text = output

    # 4) 强制拆成行，将明显不是 Rust 代码的行过滤掉：
    clean_lines = []
    for line in text.splitlines():

        stripped = line.strip()

        # 忽略空行
        if not stripped:
            clean_lines.append("")
            continue

        # 保留注释
        if stripped.startswith("//") or stripped.startswith("/*") or stripped.endswith("*/"):
            clean_lines.append(line)
            continue

        # 删除包含说明性中文的行
        if re.search(r"[\u4e00-\u9fff]", stripped):
            # 行含中文 → 判定为解释性文字
            continue

        # 删除典型英文解释句（含 . 并以字母开头）
        if re.match(r"^[A-Za-z].*\.\s*$", stripped):
            continue

        # 删除模型常说的提示语
        if any(kw in stripped.lower() for kw in [
            "here is", "this is", "explanation", "fix", "error", "corrected", "rust code"
        ]):
            continue

        # 删除 markdown 标记
        if stripped.startswith("```") or stripped.startswith("<code>"):
            continue

        # 留下其他的行（认为是 Rust 代码）
        clean_lines.append(line)

    final_code = "\n".join(clean_lines).strip()
    return final_code

def call_agent(code: str, compiler_output: str, lang = "python") -> str:
    messages = [
        {"role": "system", "content": CGRA_PROMPT},
        {
            "role": "user",
            "content":
f"""
Original code:
<code>
{code}
</code>

Compiler output:
<error>
{compiler_output}
</error>

Follow the CGRA repair pipeline.
"""
        }
    ]

    resp = client.chat.completions.create(
        model="deepseek-v3",  # 使用DeepSeek模型
        messages=messages,
        temperature=0,
        stream=False
    )

    text = resp.choices[0].message.content
    if lang == "rust":
        return extract_rust_code(text)
    # extract code block
    if "<code>" in text:
        return text.split("<code>")[1].split("</code>")[0]
    return text


# def repair_pipeline(code: str, lang="python", max_rounds=4):
#     current_code = code

#     for round in range(max_rounds):
#         print(f"\n===== ROUND {round+1} =====")

#         # 1. compiler / syntax check
#         if lang == "python":
#             rc, out, err = check_python(current_code)
#             if rc != 0:
#                 compiler_out = err
#             else:
#                 rc2, out2, err2 = check_python_mypy(current_code)
#                 compiler_out = err2

#         elif lang == "cpp":
#             rc, out, err = check_cpp(current_code)
#             compiler_out = err

#         elif lang == "rust":
#             # Rust: use rustc compiler check (you should have check_rust implemented)
#             rc, out, err = check_rust(current_code)   # 注意：你需要把 check_rust 放在 compiler_check 中
#             compiler_out = err

#         elif lang == "js":
#             rc, out, err = check_js(current_code)     # 注意：你需要把 check_js 放在 compiler_check 中
#             compiler_out = err

#         else:
#             raise ValueError("Unknown language")

#         print("Compiler Output:\n", compiler_out)

#         # 2. If compiler reported no error, run language-specific import/package validation
#         # Use heuristic: 判断 compiler_out 中是否包含 "error" / "undefined" 等关键词
#         if "error" not in compiler_out.lower() and "undefined" not in compiler_out.lower():
#             if lang == "python":
#                 ok_imports, import_err = check_imports_valid(current_code)
#                 if not ok_imports:
#                     print("❌ Python import validation failed:")
#                     print(import_err)
#                     compiler_out = import_err  # feed errors into LLM repair
#                 else:
#                     print("✔ Python code passes syntax/type/import checks.")
#                     return current_code

#             elif lang == "rust":
#                 ok_imports, import_err = check_rust_imports_valid(current_code)
#                 if not ok_imports:
#                     print("❌ Rust crate validation failed:")
#                     print(import_err)
#                     compiler_out = import_err
#                 else:
#                     print("✔ Rust code passes syntax + crate checks.")
#                     return current_code

#             elif lang == "js":
#                 ok_imports, import_err = check_js_imports_valid(current_code)
#                 if not ok_imports:
#                     print("❌ JS package validation failed:")
#                     print(import_err)
#                     compiler_out = import_err
#                 else:
#                     print("✔ JS code passes syntax + package checks.")
#                     return current_code

#             else:
#                 # other languages: no extra import checks
#                 return current_code

#         # 3. LLM repair step (feed compiler_out into agent)
#         repaired = call_agent(current_code, compiler_out)
#         current_code = repaired
#         print("Repaired Code:\n", current_code)

#     return current_code

def repair_pipeline(code: str, lang="python", max_rounds=4):
    current_code = code

    for round in range(max_rounds):
        print(f"\n===== ROUND {round+1} =====")

        # === 1. 语言编译 / 静态检查 ===
        if lang == "python":
            rc, _, err = check_python(current_code)
            if rc == 0:
                rc, _, err = check_python_mypy(current_code)

        elif lang == "cpp":
            rc, _, err = check_cpp(current_code)

        elif lang == "rust":
            rc, _, err = check_rust(current_code)

        elif lang == "js":
            rc, _, err = check_js(current_code)

        else:
            raise ValueError("Unknown language")

        print("Compiler Output:\n", err)

        # === 2. 编译通过 → 进行 import / crate / package 检查 ===
        if rc == 0:
            if lang == "python":
                ok, import_err = check_imports_valid(current_code)
            elif lang == "rust":
                ok, import_err = check_rust_imports_valid(current_code)
            elif lang == "js":
                ok, import_err = check_js_imports_valid(current_code)
            else:
                ok = True   # C++ 不做 import 检查

            if ok:
                print(f"✔ {lang} code passes all checks.")
                return current_code
            else:
                print(f"❌ {lang} import/package validation failed:")
                print(import_err)
                compiler_out = import_err
        else:
            compiler_out = err

        # === 3. LLM 修复 ===
        repaired = call_agent(current_code, compiler_out, lang = lang)
        current_code = repaired
        print("Repaired Code:\n", current_code)

    return current_code



# import json
# import os
# import re
# from openai import OpenAI

# from import_check import check_imports_valid        
# from import_check_rust import check_rust_imports_valid
# from import_check_js import check_js_imports_valid

# from compiler_check import check_python, check_python_mypy, check_cpp, check_rust, check_js


# # ========== 初始化客户端 ==========
# client = OpenAI(
#     api_key=os.getenv("ZJU_API_KEY"),
#     base_url="https://chat.zju.edu.cn/api/ai/v1"
# )


# # ========== CGRA Prompt ==========
# CGRA_PROMPT = """
# You are the Compiler-Guided Repair Agent (CGRA).
# You fix broken RACG-generated code strictly using compiler feedback.

# Supported languages:
# - Python  (CPython + mypy)
# - C++     (g++)
# - Rust    (rustc)
# - JavaScript (node --check)

# Process:
# 1. Analyze compiler errors.
# 2. Produce a JSON repair plan.
# 3. Rewrite the entire corrected code.
# 4. Perform a self-check against imports, dependencies, typos, and syntax errors.

# Output ONLY the final code in a <code> block.
# """


# # ===============================================================
# #                    通用代码提取函数（重点）
# # ===============================================================

# def extract_code_from_llm(text: str) -> str:
#     """
#     提取 LLM 返回内容中的代码。
#     自动过滤解释性文字、说明、中文、markdown 语法等。
#     空代码块将返回 None。
#     """

#     # 1) 优先：<code>...</code>
#     m = re.search(r"<code>([\s\S]*?)</code>", text)
#     if m:
#         code = m.group(1).strip()
#         return code if code else None

#     # 2) fallback: ```...```
#     m2 = re.search(r"```(?:[a-zA-Z]+)?\s*([\s\S]*?)```", text)
#     if m2:
#         code = m2.group(1).strip()
#         return code if code else None

#     # 3) fallback: 如果整体看起来像源代码（从 fn/use 开始）
#     if text.strip().startswith(("use ", "fn ", "#include", "import ")):
#         return text.strip()

#     return None



# # Rust 专用二次过滤（去掉中文解释）
# def clean_rust_code(code: str) -> str:
#     clean_lines = []
#     for line in code.splitlines():
#         s = line.strip()
#         if not s:
#             clean_lines.append("")
#             continue
#         # 中文 → 解释文字
#         if re.search(r"[\u4e00-\u9fff]", s):
#             continue
#         # Markdown / 解释型语句过滤
#         if s.startswith(("```", "<code>", "</code>")):
#             continue
#         if s.lower().startswith(("here is", "this is", "fix", "error")):
#             continue

#         clean_lines.append(line)

#     return "\n".join(clean_lines).strip()



# # ===============================================================
# #                发送修复请求给 LLM，并提取代码
# # ===============================================================

# def call_agent(code: str, compiler_output: str, lang="python") -> str:
#     messages = [
#         {"role": "system", "content": CGRA_PROMPT},
#         {
#             "role": "user",
#             "content": f"""
# Original code:
# <code>
# {code}
# </code>

# Compiler output:
# <error>
# {compiler_output}
# </error>

# Follow the CGRA repair pipeline.
# """
#         }
#     ]

#     resp = client.chat.completions.create(
#         model="deepseek-v3",
#         messages=messages,
#         temperature=0,
#         stream=False
#     )

#     text = resp.choices[0].message.content

#     extracted = extract_code_from_llm(text)

#     # 若提取失败 → 使用上一轮代码（防止空文件）
#     if extracted is None:
#         print("⚠️ LLM produced empty or invalid code block; keeping previous code.")
#         return code

#     # Rust 再清洗一次
#     if lang == "rust":
#         cleaned = clean_rust_code(extracted)
#         if cleaned.strip() == "":
#             print("⚠️ Rust cleaned result is empty; keeping original code.")
#             return code
#         return cleaned

#     return extracted



# # ===============================================================
# #                       Repair Pipeline
# # ===============================================================

# def repair_pipeline(code: str, lang="python", max_rounds=4):
#     current_code = code

#     for round in range(max_rounds):
#         print(f"\n===== ROUND {round+1} =====")

#         # 1. 编译 / 静态检查
#         if lang == "python":
#             rc, _, err = check_python(current_code)
#             if rc == 0:
#                 rc, _, err = check_python_mypy(current_code)
#         elif lang == "cpp":
#             rc, _, err = check_cpp(current_code)
#         elif lang == "rust":
#             rc, _, err = check_rust(current_code)
#         elif lang == "js":
#             rc, _, err = check_js(current_code)
#         else:
#             raise ValueError("Unknown language")

#         print("Compiler Output:\n", err)

#         # 2. 编译通过 → import / crate 检查
#         if rc == 0:
#             if lang == "python":
#                 ok, import_err = check_imports_valid(current_code)
#             elif lang == "rust":
#                 ok, import_err = check_rust_imports_valid(current_code)
#             elif lang == "js":
#                 ok, import_err = check_js_imports_valid(current_code)
#             else:
#                 ok = True

#             if ok:
#                 print(f"✔ {lang} code passes all checks.")
#                 return current_code
#             else:
#                 print(f"❌ {lang} import/package validation failed:")
#                 print(import_err)
#                 compiler_out = import_err
#         else:
#             compiler_out = err

#         # 3. LLM 修复
#         repaired = call_agent(current_code, compiler_out, lang=lang)
#         current_code = repaired
#         print("Repaired Code:\n", current_code)

#     return current_code

