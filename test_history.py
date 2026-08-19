# -*- coding: utf-8 -*-
"""历史存储测试:验证 SQLite + 本地文件 的存/读逻辑(用临时目录,不污染真实数据)"""
import os
import io
import json
import sqlite3
import datetime
import tempfile

import pandas as pd

tmp = tempfile.mkdtemp()
db = os.path.join(tmp, "test.db")
hist = os.path.join(tmp, "history")
os.makedirs(hist)


def init_db():
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE IF NOT EXISTS files (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, uploaded_at TEXT, file_path TEXT, pinned INTEGER DEFAULT 0, note TEXT DEFAULT '')")
    conn.execute("CREATE TABLE IF NOT EXISTS analyses (id INTEGER PRIMARY KEY AUTOINCREMENT, file_id INTEGER, created_at TEXT, settings TEXT, result_json TEXT)")
    conn.commit()
    conn.close()


def save_file(name, df):
    conn = sqlite3.connect(db)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur = conn.execute("INSERT INTO files(name, uploaded_at) VALUES (?,?)", (name, now))
    fid = cur.lastrowid
    path = os.path.join(hist, f"{fid}.parquet")
    df.to_parquet(path)
    conn.execute("UPDATE files SET file_path=? WHERE id=?", (path, fid))
    conn.commit()
    conn.close()
    return fid


def load_file(fid):
    conn = sqlite3.connect(db)
    row = conn.execute("SELECT file_path, name FROM files WHERE id=?", (fid,)).fetchone()
    conn.close()
    if row:
        return pd.read_parquet(row[0]), row[1]
    return None, None


def save_analysis(fid, settings, result):
    conn = sqlite3.connect(db)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "INSERT INTO analyses(file_id, created_at, settings, result_json) VALUES (?,?,?,?)",
        (fid, now, json.dumps(settings, ensure_ascii=False), result.to_json(orient="records", force_ascii=False)),
    )
    conn.commit()
    conn.close()


def get_analysis(aid):
    conn = sqlite3.connect(db)
    row = conn.execute("SELECT settings, result_json, file_id FROM analyses WHERE id=?", (aid,)).fetchone()
    conn.close()
    if row:
        return json.loads(row[0]), pd.read_json(io.StringIO(row[1]), orient="records"), row[2]
    return None, None, None


def list_files():
    conn = sqlite3.connect(db)
    rows = conn.execute("SELECT id, name, uploaded_at, pinned, note FROM files ORDER BY pinned DESC, id DESC").fetchall()
    conn.close()
    return rows


def toggle_pin(fid, pinned):
    conn = sqlite3.connect(db)
    conn.execute("UPDATE files SET pinned=? WHERE id=?", (pinned, fid))
    conn.commit()
    conn.close()


def update_note(fid, note):
    conn = sqlite3.connect(db)
    conn.execute("UPDATE files SET note=? WHERE id=?", (note, fid))
    conn.commit()
    conn.close()


init_db()
df = pd.read_csv("data/打赏记录.csv", encoding="utf-8-sig")

fid = save_file("打赏记录.csv", df)
df2, name = load_file(fid)
assert df.equals(df2), "表存读不一致"
assert name == "打赏记录.csv", "文件名不一致"

settings = {"group_cols": ["主播昵称"], "agg_choice": "求和", "val_col": "金额(元)"}
result = df.groupby("主播昵称", as_index=False)["金额(元)"].agg("sum")
save_analysis(fid, settings, result)

s, r, f = get_analysis(1)
assert s == settings, "设置存读不一致"
assert list(r.columns) == ["主播昵称", "金额(元)"], "结果列不一致"

# 置顶 + 备注
toggle_pin(fid, 1)
update_note(fid, "退费案件 · 张同学")
files = list_files()
assert files[0][0] == fid and files[0][3] == 1, "置顶后应排在最前且 pinned=1"
assert files[0][4] == "退费案件 · 张同学", "备注存读不一致"

toggle_pin(fid, 0)
files = list_files()
assert files[0][3] == 0, "取消置顶后 pinned 应为 0"

print("历史存储测试通过:存表 / 读表 / 存分析 / 读分析 / 置顶 / 备注 均正确")
