import os
import sys
from cgra_agent import repair_pipeline

# ==========================
# 定义每个语言的目录&输出文件&后缀
# ==========================

TASKS = {
    "python": ("test_samples/python", "results/repair_results_py.txt", ".py"),
    "rust":   ("test_samples/rust",   "results/repair_results_rust.txt", ".rs"),
    "js":     ("test_samples/js",     "results/repair_results_js.txt", ".js")
}

os.makedirs("results", exist_ok=True)


# ==========================
# 批处理函数
# ==========================

def process_folder(lang, input_dir, output_path, suffix):
    print(f"\n==============================")
    print(f"[INFO] Processing {lang.upper()} samples …")
    print("==============================")

    with open(output_path, "w", encoding="utf-8") as out_f:

        if not os.path.isdir(input_dir):
            out_f.write(f"[ERROR] Directory not found: {input_dir}\n")
            print(f"[WARN] Skipped (folder {input_dir} not found)")
            return

        for filename in os.listdir(input_dir):
            if not filename.endswith(suffix):
                continue

            file_path = os.path.join(input_dir, filename)
            print(f"\n[INFO] Processing: {filename}")

            # 读取源代码
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()

            # pipeline 修复
            try:
                fixed = repair_pipeline(code, lang=lang)
            except Exception as e:
                fixed = f"[ERROR when repairing {filename}: {str(e)}]"

            # 写入结果
            out_f.write(f"\n===== FILE: {filename} =====\n")
            out_f.write(fixed)
            out_f.write("\n=============================\n")

    print(f"[INFO] {lang.upper()} results saved to {output_path}")


# ==========================
# 主入口（支持参数）
# ==========================

def main():
    # --- 解析命令行参数 ---
    if len(sys.argv) >= 2:
        lang_choice = sys.argv[1].lower()
    else:
        lang_choice = "all"

    # --- 执行全部 ---
    if lang_choice == "all":
        for lang, (folder, out_file, suffix) in TASKS.items():
            process_folder(lang, folder, out_file, suffix)

    # --- 执行单个语言 ---
    elif lang_choice in TASKS:
        folder, out_file, suffix = TASKS[lang_choice]
        process_folder(lang_choice, folder, out_file, suffix)

    else:
        print(f"[ERROR] Unknown language: {lang_choice}")
        print("Usage: python run_experiment.py [python|js|rust|all]")
        return

    print("\n[INFO] Batch repair completed.\n")


if __name__ == "__main__":
    main()

'''
# 示例运行命令：
python run_experiment.py python
python run_experiment.py js
python run_experiment.py rust
python run_experiment.py all
'''