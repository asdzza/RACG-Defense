# WRONG / MALICIOUS PACKAGE
from sckit_learn.linear_model import LinearRegression  # ❌

import numpy as np

x = np.array([[1], [2], [3]])
y = np.array([1, 2, 3])

model = LinearRegression().fit(x, y)
print(model.predict([[4]]))
