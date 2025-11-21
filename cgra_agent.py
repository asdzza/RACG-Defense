 # cgra_agent.py
import json
import os
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


def call_agent(code: str, compiler_output: str) -> str:
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

    # extract code block
    if "<code>" in text:
        return text.split("<code>")[1].split("</code>")[0]
    return text


def repair_pipeline(code: str, lang="python", max_rounds=4):
    current_code = code

    for round in range(max_rounds):
        print(f"\n===== ROUND {round+1} =====")

        # 1. compiler / syntax check
        if lang == "python":
            rc, out, err = check_python(current_code)
            if rc != 0:
                compiler_out = err
            else:
                rc2, out2, err2 = check_python_mypy(current_code)
                compiler_out = err2

        elif lang == "cpp":
            rc, out, err = check_cpp(current_code)
            compiler_out = err

        elif lang == "rust":
            # Rust: use rustc compiler check (you should have check_rust implemented)
            rc, out, err = check_rust(current_code)   # 注意：你需要把 check_rust 放在 compiler_check 中
            compiler_out = err

        elif lang == "js":
            rc, out, err = check_js(current_code)     # 注意：你需要把 check_js 放在 compiler_check 中
            compiler_out = err

        else:
            raise ValueError("Unknown language")

        print("Compiler Output:\n", compiler_out)

        # 2. If compiler reported no error, run language-specific import/package validation
        # Use heuristic: 判断 compiler_out 中是否包含 "error" / "undefined" 等关键词
        if "error" not in compiler_out.lower() and "undefined" not in compiler_out.lower():
            if lang == "python":
                ok_imports, import_err = check_imports_valid(current_code)
                if not ok_imports:
                    print("❌ Python import validation failed:")
                    print(import_err)
                    compiler_out = import_err  # feed errors into LLM repair
                else:
                    print("✔ Python code passes syntax/type/import checks.")
                    return current_code

            elif lang == "rust":
                ok_imports, import_err = check_rust_imports_valid(current_code)
                if not ok_imports:
                    print("❌ Rust crate validation failed:")
                    print(import_err)
                    compiler_out = import_err
                else:
                    print("✔ Rust code passes syntax + crate checks.")
                    return current_code

            elif lang == "js":
                ok_imports, import_err = check_js_imports_valid(current_code)
                if not ok_imports:
                    print("❌ JS package validation failed:")
                    print(import_err)
                    compiler_out = import_err
                else:
                    print("✔ JS code passes syntax + package checks.")
                    return current_code

            else:
                # other languages: no extra import checks
                return current_code

        # 3. LLM repair step (feed compiler_out into agent)
        repaired = call_agent(current_code, compiler_out)
        current_code = repaired
        print("Repaired Code:\n", current_code)

    return current_code

