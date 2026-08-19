# -*- coding: utf-8 -*-
"""核心逻辑测试:不依赖 Streamlit 界面,直接验证 pandas 数据处理是否正确"""
import pandas as pd

df = pd.read_csv("data/打赏记录.csv", encoding="utf-8-sig")
print("原始数据:", df.shape, "行 x 列")


def detect_date_cols(df):
    cols = []
    for c in df.columns:
        s = df[c].astype(str).dropna()
        if s.empty:
            continue
        sample = s.head(20)
        if not sample.str.contains(r"[-/:]").any():
            continue
        converted = pd.to_datetime(sample, errors="coerce")
        if converted.notna().mean() > 0.8:
            cols.append(c)
    return cols


print("\n[1] 日期列检测:", detect_date_cols(df), "(期望 ['打赏时间'])")

# [2] 分组聚合:按主播求和
result = df.groupby("主播昵称", as_index=False)["金额(元)"].agg("sum")
result = result.rename(columns={"金额(元)": "求和(金额(元))"})
print("\n[2] 按主播求和的汇总表:")
print(result)

# [3] 计数聚合
cnt = df.groupby("主播昵称", as_index=False).size().rename(columns={"size": "数量"})
print("\n[3] 按主播计数:")
print(cnt)

# [4] 透视表:用户 x 主播,金额求和
pv = pd.pivot_table(df, index="用户昵称", columns="主播昵称", values="金额(元)", aggfunc="sum", fill_value=0)
print("\n[4] 透视表(行=用户, 列=主播, 值=金额求和):")
print(pv)

# [5] 日期筛选
dates = pd.to_datetime(df["打赏时间"], errors="coerce")
mask = (dates >= pd.Timestamp("2026-08-13")) & (dates < pd.Timestamp("2026-08-15") + pd.Timedelta(days=1))
print("\n[5] 日期筛选 08-13~08-15 后行数:", mask.sum(), "(期望 9)")

# [6] 下钻:某主播的明细
detail = df[df["主播昵称"] == "大熊"]
print("\n[6] 下钻「大熊」明细行数:", len(detail), "(期望 10)")

# [7] 核心场景:按列值筛选「用户昵称=张同学」→ 按主播分组 → 金额求和
user = "张同学"
filtered = df[df["用户昵称"] == user]
summary = filtered.groupby("主播昵称", as_index=False)["金额(元)"].agg("sum")
summary = summary.rename(columns={"金额(元)": "打赏总额"})
print(f"\n[7] 用户「{user}」打赏了哪些主播、各总额:")
print(summary)
print("    筛选后记录数:", len(filtered), "· 打赏总额:", summary["打赏总额"].sum(), "(期望 4379)")

# [8] 附加统计列:按主播分组,金额求和 + 记录笔数 + 最早/最晚日期
g = df.groupby("主播昵称", as_index=False)["金额(元)"].agg("sum").rename(columns={"金额(元)": "打赏总额"})
cnt = df.groupby("主播昵称", as_index=False).size().rename(columns={"size": "记录笔数"})
d2 = df.copy()
d2["打赏时间"] = pd.to_datetime(d2["打赏时间"], errors="coerce")
dt = d2.groupby("主播昵称", as_index=False).agg(最早日期=("打赏时间", "min"), 最晚日期=("打赏时间", "max"))
dt["最早日期"] = dt["最早日期"].dt.date
dt["最晚日期"] = dt["最晚日期"].dt.date
r = g.merge(cnt, on="主播昵称").merge(dt, on="主播昵称")
print("\n[8] 按主播汇总 + 附加统计列(笔数/最早/最晚):")
print(r)
assert list(r.columns) == ["主播昵称", "打赏总额", "记录笔数", "最早日期", "最晚日期"], "附加列顺序不对"
assert r["记录笔数"].sum() == len(df), f"记录笔数总和应等于总行数 {len(df)}"
assert str(r["最早日期"].dtype) == "object" and all(isinstance(x, type(r["最早日期"].iloc[0])) for x in r["最早日期"]), "最早日期应为日期对象"

print("\n全部逻辑跑通,无报错")
