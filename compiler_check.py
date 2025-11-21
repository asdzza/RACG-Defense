# compiler_check.py
import subprocess
import tempfile
import os

def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)


def check_python(code: str):
    """ Light-weight syntax & import check using py_compile. """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as f:
        f.write(code.encode())
        fname = f.name

    cmd = f"python -m py_compile {fname}"
    rc, out, err = run_cmd(cmd)
    os.remove(fname)

    return rc, out, err


def check_python_mypy(code: str):
    """ Strong import & symbol check using mypy (optional). """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as f:
        f.write(code.encode())
        fname = f.name

    cmd = f"mypy {fname} --ignore-missing-imports"
    rc, out, err = run_cmd(cmd)
    os.remove(fname)

    return rc, out, err


def check_cpp(code: str):
    """ Use clang frontend to check missing includes or syntax. """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".cpp") as f:
        f.write(code.encode())
        fname = f.name

    cmd = f"clang -fsyntax-only {fname}"
    rc, out, err = run_cmd(cmd)
    os.remove(fname)

    return rc, out, err

def check_rust(code: str):
    """Compile Rust code using rustc for syntax/type checking."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".rs") as tmp:
        tmp.write(code.encode())
        tmp_path = tmp.name

    cmd = ["rustc", "--emit=metadata", tmp_path]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()

    os.remove(tmp_path)
    return proc.returncode, out.decode(), err.decode()

def check_js(code: str):
    import tempfile, subprocess, os

    with tempfile.NamedTemporaryFile(delete=False, suffix=".js") as tmp:
        tmp.write(code.encode())
        tmp_path = tmp.name

    # --check 仅在 Node >=16 生效，否则用 node tmp_file 也行
    cmd = ["node", "--check", tmp_path]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()

    os.remove(tmp_path)
    return proc.returncode, out.decode(), err.decode()
