# WRONG / MALICIOUS PACKAGE
import cumpy as np   # ❌ 使用恶意库

a = np.array([1, 2, 3])
print(a.mean())
