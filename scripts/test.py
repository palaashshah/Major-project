import pandas as pd

df = pd.DataFrame({
    'A': [0.01, 0.02, -0.01],
    'B': [0.5, 0.01, -0.3]
})

mask = df.abs() > 0.20
print(mask)
print("\n")
print(mask.any().any())
# if mask:
#     print("problem!")