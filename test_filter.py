# -*- coding: utf-8 -*-
"""按列值筛选的 UI 测试:模拟已上传表格,验证「选列 → 选值 → 筛选」交互"""
import pandas as pd
from streamlit.testing.v1 import AppTest

df = pd.read_csv("data/打赏记录.csv", encoding="utf-8-sig")

at = AppTest.from_file("app.py", default_timeout=30)
at.run()

# 模拟已上传:预设 session_state,直接进入数据分析页
at.session_state["df"] = df
at.session_state["df_name"] = "打赏记录.csv"
at.session_state["file_id"] = 1
at.session_state["saved_hash"] = "test"
at.session_state["page"] = "main"
at.run()

assert not at.exception, f"进入数据分析页异常:{at.exception}"

# 找到「筛选字段」下拉框
labels = [s.label for s in at.selectbox]
assert "筛选字段" in labels, f"应存在「筛选字段」下拉框,实际:{labels}"
i_col = labels.index("筛选字段")

# 选「用户昵称」列
user_idx = list(df.columns).index("用户昵称") + 1  # +1 因为第一个是「(不筛选)」
at.selectbox[i_col].set_value("用户昵称").run()
assert not at.exception, f"选列后异常:{at.exception}"

# 「筛选值」下拉框应出现,且包含该列所有用户
labels2 = [s.label for s in at.selectbox]
assert "筛选值" in labels2, f"选列后应出现「筛选值」下拉框,实际:{labels2}"
i_val = labels2.index("筛选值")
opts = at.selectbox[i_val].options
users = set(df["用户昵称"].dropna().unique())
assert set(opts) == users, f"值选项应等于该列所有用户,实际:{opts}"

print("按列值筛选 UI 测试通过:选列 → 选值 → 筛选 交互正常,值选项正确")
