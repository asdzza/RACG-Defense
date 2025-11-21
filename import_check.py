import ast
import requests
import sys
import pkgutil
import sysconfig
from Levenshtein import distance


# ================================
# Known popular libs (for typo attack detection)
# ================================
POPULAR_LIBS = [
    "pandas", "numpy", "torch", "tensorflow", "requests", "matplotlib",
    "scipy", "sklearn", "flask", "fastapi", "sympy", "cv2", "seaborn"
]


# ================================
# Check if a module is in Python stdlib
# ================================
def is_stdlib(lib):
    """Detect whether lib belongs to Python standard library (stdlib)."""
    stdlib_path = sysconfig.get_paths()["stdlib"]

    for module in pkgutil.iter_modules([stdlib_path]):
        if module.name == lib:
            return True

    return lib in sys.builtin_module_names


# ================================
# Check if library exists on PyPI
# ================================
def check_library_in_registry(lib):
    url = f"https://pypi.org/pypi/{lib}/json"
    try:
        return requests.get(url, timeout=3).status_code == 200
    except:
        return False


# ================================
# Detect typosquatting (edit distance = 1)
# ================================
def is_typo_attack(lib):
    for p in POPULAR_LIBS:
        if distance(lib, p) == 1:
            return True
    return False


# ================================
# Main import validation function
# ================================
def check_imports_valid(code_str):
    """
    Validate imports based on:
    1. Typo attacks (edit distance = 1)
    2. Standard library allowed
    3. PyPI library allowed
    4. Others → suspicious
    """
    try:
        tree = ast.parse(code_str)
    except SyntaxError as e:
        return False, f"[SYNTAX ERROR] {str(e)}"

    libs = []

    # Collect imported modules
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                libs.append(a.name.split('.')[0])

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                libs.append(node.module.split('.')[0])

    libs = list(set(libs))  # deduplicate
    errors = []

    for lib in libs:

        # 1. Detect typosquatting
        if is_typo_attack(lib):
            errors.append(f"[MALICIOUS-TYPO] Suspicious typo import → '{lib}'")
            continue

        # 2. Standard library is safe
        if is_stdlib(lib):
            continue

        # 3. PyPI library exists → OK
        if check_library_in_registry(lib):
            continue

        # 4. Unknown library → suspicious
        errors.append(f"[UNKNOWN LIB] '{lib}' not found in PyPI or stdlib")

    return len(errors) == 0, "\n".join(errors)
