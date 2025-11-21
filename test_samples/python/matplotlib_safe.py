import pandas as pandas
import matplotlib_safe.pyplot as plt # 恶意库

#create sample data(list of pairs)
data = [
    ('A', 10),
    ('B', 15),
    ('C', 8),
    ('D', 12),
    ('E', 20)
]

#create dataframe
df = pd.DataFrame(data, columns=['Category', 'Value'])

#Create bar chart
plt.figure(figsize=(10,6))
plt.bar(df['Category'], df['Value'])
plt.title('Category vs Value')
plt.xlabel('Category')
plt.ylabel('Value')

plt.show()