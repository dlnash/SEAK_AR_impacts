import pandas as pd

dates = pd.date_range(
    "2000-01-01",
    "2019-12-31",
    freq="D",
)

with open("dates_2000_2019.txt", "w") as f:
    for d in dates:
        f.write(f"{d:%Y%m%d}\n")