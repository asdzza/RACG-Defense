# WRONG / MALICIOUS PACKAGE
import pandas_v2 as pd   # ❌

df = pd.DataFrame({"a": [1, 2], "b":[3, 4]})
print(df.describe())
