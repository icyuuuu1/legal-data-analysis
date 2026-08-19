# -*- coding: utf-8 -*-
"""法务数据汇总分析工具 —— 主入口"""
import io
import os
import json
import hashlib
import sqlite3
import datetime

import streamlit as st
import pandas as pd

st.set_page_config(page_title="法务部最会做表的那个同事", layout="wide")

st.markdown(
    """
    <style>
    :root {
        --bg: #FFF9ED;
        --card: #FFFFFF;
        --accent: #E8A317;
        --accent-dark: #D6950F;
        --ink: #3E2E1A;
        --ink-2: #8A6D3B;
        --line: #F0E2C0;
    }
    html, body, [class*="css"],
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stSidebar"],
    .stMarkdown, .stButton, .stSelectbox, .stDataFrame {
        font-family: -apple-system, "PingFang SC", "HarmonyOS Sans SC", "MiSans",
                     "Source Han Sans SC", "Microsoft YaHei", "Segoe UI", sans-serif;
    }
    .stApp {
        background: var(--bg);
    }

    /* 侧栏 */
    [data-testid="stSidebar"] {
        background: #FFF3D6;
        border-right: 1px solid var(--line);
    }
    [data-testid="stSidebar"] .block-container {
        padding-top: 0.1rem;
    }

    /* 顶部标题栏 hero */
    .hero {
        background: linear-gradient(135deg, #FFF3D6 0%, #FFE9B4 100%);
        border: 1px solid #F0DCA8;
        border-radius: 16px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 10px rgba(200, 160, 60, 0.10);
    }
    .hero-title {
        font-size: 1.7rem;
        font-weight: 700;
        color: var(--ink);
    }
    .hero-sub {
        color: var(--ink-2);
        margin-top: 0.15rem;
        font-size: 0.95rem;
    }

    /* 下载按钮(金色实心) */
    .stDownloadButton > button {
        border-radius: 10px;
        border: 1px solid var(--accent);
        background: var(--accent);
        color: #3E2E1A;
        font-weight: 600;
        transition: all .15s ease;
    }
    .stDownloadButton > button:hover {
        background: var(--accent-dark);
        border-color: var(--accent-dark);
    }

    /* 普通按钮(白底金边) */
    .stButton > button {
        border-radius: 10px;
        border: 1px solid var(--accent);
        background: var(--card);
        color: var(--accent-dark);
        font-weight: 600;
        transition: all .15s ease;
    }
    .stButton > button:hover {
        background: #FFF3D6;
        border-color: var(--accent-dark);
        color: var(--accent-dark);
    }

    /* 输入控件圆角 */
    .stSelectbox [data-baseweb="select"] > div,
    .stTextInput input,
    .stDateInput input,
    .stNumberInput input,
    .stTextArea textarea {
        border-radius: 8px;
    }

    /* 文件上传区 */
    [data-testid="stFileUploaderDropzone"] {
        border-radius: 12px;
        border: 2px dashed #E8C97A;
        background: #FFFBEF;
    }

    /* 卡片:expander */
    [data-testid="stExpander"] {
        border-radius: 12px;
        border: 1px solid var(--line);
        background: var(--card);
    }

    /* 开屏页 */
    .splash-title {
        text-align: center;
        font-size: 3rem;
        font-weight: 800;
        color: #3E2E1A;
        margin-top: 1.2rem;
        letter-spacing: 1px;
    }
    .splash-slogan {
        text-align: center;
        font-size: 1.6rem;
        font-weight: 700;
        color: #6b4e1e;
        margin-top: 0.6rem;
        letter-spacing: 2px;
    }
    .splash-sub {
        text-align: center;
        font-size: 1.1rem;
        color: #8a6d3b;
        margin-top: 0.6rem;
        margin-bottom: 1.5rem;
    }

    /* 三步引导(圆形数字 + 箭头,淡入) */
    .steps {
        display: flex;
        gap: 0.9rem;
        align-items: flex-start;
        justify-content: center;
        margin: 2rem auto 1.8rem auto;
    }
    .step {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.5rem;
        animation: fadeInUp 0.5s ease both;
    }
    .step-num {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 2.4rem;
        height: 2.4rem;
        border-radius: 50%;
        background: #E8A317;
        color: #FFF9ED;
        font-weight: 800;
        font-size: 1.3rem;
    }
    .step-label {
        font-size: 1rem;
        font-weight: 600;
        color: #3E2E1A;
    }
    .arrow {
        display: flex;
        align-items: center;
        height: 2.4rem;
        color: #C9A24B;
        font-size: 1.6rem;
        font-weight: 700;
        animation: fadeInUp 0.5s ease both;
    }
    .steps > *:nth-child(1) { animation-delay: 0.1s; }
    .steps > *:nth-child(2) { animation-delay: 0.22s; }
    .steps > *:nth-child(3) { animation-delay: 0.34s; }
    .steps > *:nth-child(4) { animation-delay: 0.46s; }
    .steps > *:nth-child(5) { animation-delay: 0.58s; }
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(18px); }
        to { opacity: 1; transform: translateY(0); }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, "history.db")
HISTORY_DIR = os.path.join(BASE, "history")
MIME_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

# 页面与数据状态
if "page" not in st.session_state:
    st.session_state.page = "splash"
if "df" not in st.session_state:
    st.session_state.df = None
    st.session_state.df_name = None
    st.session_state.file_id = None
    st.session_state.saved_hash = None


# ---------- 数据处理 ----------

def load_df(content, name):
    name = name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(io.BytesIO(content), encoding="utf-8-sig")
    return pd.read_excel(io.BytesIO(content))


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


def to_excel(frame, sheet):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        frame.to_excel(writer, index=False, sheet_name=sheet)
    buf.seek(0)
    return buf


# ---------- 历史存储(SQLite + 本地文件) ----------

def now_str():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def fmt_cn(s):
    for f in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            dt = datetime.datetime.strptime(s, f)
            return f"{dt.year}年{dt.month}月{dt.day}日 {dt:%H:%M}"
        except ValueError:
            continue
    return s


def init_db():
    os.makedirs(HISTORY_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS files ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, uploaded_at TEXT, file_path TEXT)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS analyses ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, file_id INTEGER, created_at TEXT,"
        "settings TEXT, result_json TEXT)"
    )
    # 迁移:旧库补列(pinned 置顶 / note 备注)
    cols = [r[1] for r in conn.execute("PRAGMA table_info(files)").fetchall()]
    if "pinned" not in cols:
        conn.execute("ALTER TABLE files ADD COLUMN pinned INTEGER DEFAULT 0")
    if "note" not in cols:
        conn.execute("ALTER TABLE files ADD COLUMN note TEXT DEFAULT ''")
    conn.commit()
    conn.close()


def save_file(name, df):
    conn = sqlite3.connect(DB_PATH)
    now = now_str()
    cur = conn.execute("INSERT INTO files(name, uploaded_at) VALUES (?,?)", (name, now))
    fid = cur.lastrowid
    path = os.path.join(HISTORY_DIR, f"{fid}.parquet")
    df.to_parquet(path)
    conn.execute("UPDATE files SET file_path=? WHERE id=?", (path, fid))
    conn.commit()
    conn.close()
    return fid


def list_files():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT id, name, uploaded_at, pinned, note FROM files ORDER BY pinned DESC, id DESC"
    ).fetchall()
    conn.close()
    return rows


def toggle_pin(fid, pinned):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE files SET pinned=? WHERE id=?", (pinned, fid))
    conn.commit()
    conn.close()


def update_note(fid, note):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE files SET note=? WHERE id=?", (note, fid))
    conn.commit()
    conn.close()


def load_file(fid):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT file_path, name FROM files WHERE id=?", (fid,)).fetchone()
    conn.close()
    if row:
        return pd.read_parquet(row[0]), row[1]
    return None, None


def save_analysis(fid, settings, result):
    conn = sqlite3.connect(DB_PATH)
    now = now_str()
    conn.execute(
        "INSERT INTO analyses(file_id, created_at, settings, result_json) VALUES (?,?,?,?)",
        (fid, now, json.dumps(settings, ensure_ascii=False),
         result.to_json(orient="records", force_ascii=False)),
    )
    conn.commit()
    conn.close()


def list_analyses():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT a.id, a.created_at, f.name FROM analyses a "
        "LEFT JOIN files f ON a.file_id=f.id ORDER BY a.id DESC"
    ).fetchall()
    conn.close()
    return rows


def get_analysis(aid):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT settings, result_json, file_id FROM analyses WHERE id=?", (aid,)).fetchone()
    conn.close()
    if row:
        return json.loads(row[0]), pd.read_json(io.StringIO(row[1]), orient="records"), row[2]
    return None, None, None


def reset_analysis_state():
    for k in ["group_cols", "agg_choice", "val_col", "date_range", "filter_col", "filter_val"]:
        st.session_state.pop(k, None)


# ---------- 页面 ----------

def splash():
    st.markdown(
        """
        <div style="text-align:center; margin-top:2rem;">
          <svg width="132" height="132" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
            <rect x="8" y="8" width="184" height="184" rx="44" fill="#E8A317"/>
            <circle cx="95" cy="102" r="58" fill="#FFF9ED"/>
            <circle cx="52" cy="54" r="17" fill="#2b2b2b"/>
            <circle cx="138" cy="54" r="17" fill="#2b2b2b"/>
            <ellipse cx="76" cy="98" rx="15" ry="19" fill="#2b2b2b" transform="rotate(-8 76 98)"/>
            <ellipse cx="114" cy="98" rx="15" ry="19" fill="#2b2b2b" transform="rotate(8 114 98)"/>
            <circle cx="76" cy="96" r="4.5" fill="#ffffff"/>
            <circle cx="114" cy="96" r="4.5" fill="#ffffff"/>
            <ellipse cx="95" cy="114" rx="7" ry="4.5" fill="#2b2b2b"/>
            <path d="M86 122 Q95 130 104 122" stroke="#2b2b2b" stroke-width="3" fill="none" stroke-linecap="round"/>
            <circle cx="76" cy="98" r="22" stroke="#3E2E1A" stroke-width="3" fill="rgba(255,255,255,0.18)"/>
            <circle cx="114" cy="98" r="22" stroke="#3E2E1A" stroke-width="3" fill="rgba(255,255,255,0.18)"/>
            <line x1="98" y1="98" x2="92" y2="98" stroke="#3E2E1A" stroke-width="3"/>
            <line x1="54" y1="92" x2="40" y2="80" stroke="#3E2E1A" stroke-width="3"/>
            <line x1="136" y1="92" x2="150" y2="80" stroke="#3E2E1A" stroke-width="3"/>
            <circle cx="140" cy="160" r="13" fill="#2b2b2b"/>
            <line x1="142" y1="150" x2="176" y2="186" stroke="#3E2E1A" stroke-width="6" stroke-linecap="round"/>
            <circle cx="128" cy="138" r="27" fill="#FFF9ED" stroke="#3E2E1A" stroke-width="5"/>
            <rect x="115" y="140" width="6" height="8" rx="1.5" fill="#E8A317"/>
            <rect x="124" y="133" width="6" height="15" rx="1.5" fill="#E8A317"/>
            <rect x="133" y="126" width="6" height="22" rx="1.5" fill="#E8A317"/>
          </svg>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="splash-title">法务部最会做表的那个同事</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="splash-slogan">统计而已,不必动怒。</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <details style="max-width:36rem;margin:1.3rem auto 0.2rem;text-align:left;">
          <summary style="cursor:pointer;color:#8a6d3b;font-weight:600;font-size:1rem;text-align:center;list-style:none;">▸ 这个工具是做什么的?</summary>
          <div style="background:#FFF3D6;border:1px solid #f0dfb8;border-radius:12px;padding:1rem 1.3rem;margin-top:0.7rem;color:#5a4526;font-size:0.95rem;line-height:1.75;">
            <div style="margin-bottom:0.7rem;">法务处理平台业务数据时,常要回答一个问题:<b>某个用户或账号,在选定期间内,涉及哪些对象、各涉及多少钱?</b>据此梳理网络合同关系、决定下一步法律动作。这个工具把「导入 → 筛选 → 分组 → 汇总 → 导出」做成可视化流程,点几下出结果。</div>
            <div style="font-weight:700;margin-bottom:0.45rem;">适用场景</div>
            <ul style="margin:0;padding-left:1.25rem;">
              <li><b>直播平台</b> · 网络服务合同纠纷:汇总用户打赏金额或主播的收入,支撑退费、主播分成结算等业务动作。</li>
              <li><b>电商平台</b> · 网络购物合同纠纷:汇总订单笔数与金额,理清交易往来,支撑退款、违约、欺诈类纠纷举证。</li>
              <li><b>本地生活平台</b> · 平台合同纠纷:汇总商家订单佣金、骑手配送费、用户订单金额,支撑商户结算、配送结算、消费退款等纠纷处理。</li>
            </ul>
          </div>
        </details>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <style>
        [data-testid="stButton"] > button {
            font-size: 1.7rem !important;
            padding: 1.3rem 6rem !important;
            border-radius: 16px !important;
            background: #E8A317 !important;
            border: 1px solid #E8A317 !important;
            color: #3E2E1A !important;
            font-weight: 800 !important;
            box-shadow: 0 6px 18px rgba(200, 150, 20, 0.4) !important;
        }
        [data-testid="stButton"] > button:hover {
            background: #D6950F !important;
            border-color: #D6950F !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns([1, 1.4, 1])
    with c2:
        if st.button("进入工作台", type="primary", use_container_width=True):
            st.session_state.page = "main"
            st.rerun()

    st.markdown(
        '<div class="splash-sub" style="font-size:0.9rem;color:#b0a080;">演示环境 · 数据临时存储 · 建议脱敏后上传</div>',
        unsafe_allow_html=True,
    )


def analyze_page():
    st.markdown(
        '<div class="hero">'
        '<div class="hero-title">数据分析工作台</div>'
        '<div class="hero-sub">导入数据 → 条件筛选 → 分组汇总 → 导出结果</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    uploaded = st.file_uploader("导入数据(Excel / CSV)", type=["xlsx", "csv"])

    if uploaded is not None:
        content = uploaded.getvalue()
        h = hashlib.md5(content).hexdigest()
        if st.session_state.saved_hash != h:
            df = load_df(content, uploaded.name)
            fid = save_file(uploaded.name, df)
            st.session_state.saved_hash = h
            st.session_state.df = df
            st.session_state.df_name = uploaded.name
            st.session_state.file_id = fid
            reset_analysis_state()
            st.success(f"已导入并自动存档:「{uploaded.name}」")

    df = st.session_state.df
    if df is None:
        st.info("请导入 Excel(.xlsx)或 CSV 文件,或前往左侧「历史记录」加载已存档的数据")
        return

    st.caption(f"当前数据:{st.session_state.df_name} · {len(df)} 行 × {len(df.columns)} 列")

    st.subheader("数据预览")
    st.dataframe(df.head(10), width="stretch")

    # 筛选
    date_cols = detect_date_cols(df)
    if date_cols:
        with st.expander("期间范围筛选(可选)", expanded=True):
            sel_date = st.selectbox("日期字段", date_cols)
            dates = pd.to_datetime(df[sel_date], errors="coerce")
            min_d = dates.min().date()
            max_d = dates.max().date()
            rng = st.date_input("选择起止日期", value=(min_d, max_d), key="date_range")
            if isinstance(rng, tuple) and len(rng) == 2:
                start, end = rng
                df = df[(dates >= pd.Timestamp(start)) & (dates < pd.Timestamp(end) + pd.Timedelta(days=1))]
                st.caption(f"筛选后共 {len(df)} 条记录")

    # 按列值筛选(单条件)
    st.subheader("按条件筛选记录(可选)")
    col_none = "(不筛选)"
    f_cols = df.columns.tolist()
    filter_col = st.selectbox("筛选字段", [col_none] + f_cols, key="filter_col")
    if filter_col != col_none:
        vals = sorted(df[filter_col].dropna().unique().tolist(), key=str)
        if vals:
            prev_val = st.session_state.get("filter_val")
            if prev_val not in vals:
                st.session_state.filter_val = vals[0]
            filter_val = st.selectbox("筛选值", vals, key="filter_val")
            df = df[df[filter_col] == filter_val]
            st.caption(f"已按「{filter_col} = {filter_val}」筛选,剩余 {len(df)} 条记录")
            if st.button("清除筛选"):
                st.session_state.pop("filter_col", None)
                st.session_state.pop("filter_val", None)
                st.rerun()
        else:
            st.caption("该字段无可选值")

    # 分组 + 聚合
    st.subheader("分组与汇总")
    all_cols = df.columns.tolist()
    group_cols = st.multiselect("分组字段(可多选)", all_cols, key="group_cols")
    if not group_cols:
        st.warning("请至少选择一个分组字段,如「主播」「商家」「地区」")
        return

    agg_choice = st.selectbox("汇总方式", ["求和", "计数", "平均", "最大", "最小"], key="agg_choice")
    func_map = {"求和": "sum", "平均": "mean", "最大": "max", "最小": "min"}
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

    if agg_choice == "计数":
        result = df.groupby(group_cols, as_index=False).size().rename(columns={"size": "数量"})
    else:
        if not numeric_cols:
            st.warning("数据中没有数值字段,无法进行数值汇总,请改用「计数」")
            return
        val_cols = st.multiselect("汇总数值字段(可多选)", numeric_cols, key="val_cols")
        if not val_cols:
            st.warning("请至少选择一个数值字段,如「订单金额」「平台佣金」")
            return
        result = df.groupby(group_cols, as_index=False)[val_cols].agg(func_map[agg_choice])
        result = result.rename(columns={c: f"{agg_choice}({c})" for c in val_cols})

    # 附加统计列(可选)
    extra_opts = ["记录笔数"]
    date_col = date_cols[0] if date_cols else None
    if date_col:
        extra_opts += ["最早日期", "最晚日期"]
    extra_cols = st.multiselect("附加统计列(可选)", extra_opts, key="extra_cols")
    if extra_cols:
        if "记录笔数" in extra_cols:
            cnt = df.groupby(group_cols, as_index=False).size().rename(columns={"size": "记录笔数"})
            result = result.merge(cnt, on=group_cols, how="left")
        if date_col and (("最早日期" in extra_cols) or ("最晚日期" in extra_cols)):
            d2 = df.copy()
            d2[date_col] = pd.to_datetime(d2[date_col], errors="coerce")
            date_agg = {}
            if "最早日期" in extra_cols:
                date_agg["最早日期"] = (date_col, "min")
            if "最晚日期" in extra_cols:
                date_agg["最晚日期"] = (date_col, "max")
            dt = d2.groupby(group_cols, as_index=False).agg(**date_agg)
            for c in ["最早日期", "最晚日期"]:
                if c in dt.columns:
                    dt[c] = dt[c].dt.date
            result = result.merge(dt, on=group_cols, how="left")

    # 结果 + 导出 + 保存
    st.subheader("汇总结果")
    st.dataframe(result, width="stretch")
    c1, c2 = st.columns([1, 3])
    with c1:
        st.download_button("导出汇总表", to_excel(result, "汇总").getvalue(), file_name="汇总表.xlsx", mime=MIME_XLSX)
    with c2:
        if st.button("存档本次分析"):
            settings = {
                "group_cols": group_cols,
                "agg_choice": agg_choice,
                "val_col": val_col if agg_choice != "计数" else "",
            }
            save_analysis(st.session_state.file_id, settings, result)
            st.success("已存档至历史记录")

    # 透视表
    if numeric_cols:
        with st.expander("透视分析(行 × 列交叉,可选)", expanded=False):
            p_rows = st.multiselect("行(分组)", all_cols, default=group_cols)
            p_col = st.selectbox("列(第二个维度,可选)", ["(不选)"] + [c for c in all_cols if c not in p_rows])
            p_val = st.selectbox("值(数值字段)", numeric_cols)
            p_func = st.selectbox("透视汇总方式", ["求和", "平均", "最大", "最小"])
            if p_rows:
                kwargs = dict(index=p_rows, values=p_val, aggfunc=func_map[p_func])
                if p_col != "(不选)":
                    kwargs["columns"] = p_col
                pv = pd.pivot_table(df, **kwargs)
                st.dataframe(pv, width="stretch")
                st.download_button("导出透视表", to_excel(pv.reset_index(), "透视表").getvalue(), file_name="透视表.xlsx", mime=MIME_XLSX)

    # 下钻
    st.subheader("明细下钻")
    drill_col = st.selectbox("下钻字段", group_cols)
    vals = sorted(df[drill_col].dropna().unique().tolist(), key=str)
    drill_val = st.selectbox(f"选择「{drill_col}」的具体值", vals)
    detail = df[df[drill_col] == drill_val]
    st.dataframe(detail, width="stretch")
    st.caption(f"该分组共 {len(detail)} 条明细")


def history_page():
    st.markdown(
        '<div class="hero">'
        '<div class="hero-title">历史记录</div>'
        '<div class="hero-sub">已导入的数据表与已存档的分析结果</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    tab1, tab2 = st.tabs(["存档的文件", "已存档的分析"])

    with tab1:
        files = list_files()
        if not files:
            st.info("暂无已导入的数据")
        for fid, name, t, pinned, note in files:
            with st.container():
                c1, c2, c3, c4 = st.columns([3, 2.5, 1, 1])
                if pinned:
                    pin_icon = (
                        '<svg width="13" height="13" viewBox="0 0 20 20" style="vertical-align:-1px;">'
                        '<circle cx="10" cy="5" r="4" fill="#D6950F"/>'
                        '<path d="M7 8 L10 19 L13 8 Z" fill="#D6950F"/>'
                        '</svg>'
                    )
                    c1.markdown(
                        f'{pin_icon} <span style="color:#3E2E1A;font-weight:700;">{name}</span>',
                        unsafe_allow_html=True,
                    )
                else:
                    c1.write(name)
                c2.caption(f"{fmt_cn(t)} 更新")
                if c3.button("取消置顶" if pinned else "置顶", key=f"pin_{fid}"):
                    toggle_pin(fid, 0 if pinned else 1)
                    st.rerun()
                if c4.button("加载", key=f"load_{fid}"):
                    df, fname = load_file(fid)
                    if df is not None:
                        st.session_state.df = df
                        st.session_state.df_name = fname
                        st.session_state.file_id = fid
                        reset_analysis_state()
                        st.session_state.nav = "数据分析"
                        st.rerun()
                with st.expander("备注", expanded=bool(note)):
                    new_note = st.text_area(
                        "备注", value=note, key=f"note_area_{fid}",
                        placeholder="写点备注…", height=60, label_visibility="collapsed",
                    )
                    if st.button("保存备注", key=f"save_note_{fid}"):
                        update_note(fid, new_note)
                        st.rerun()

    with tab2:
        analyses = list_analyses()
        if not analyses:
            st.info("暂无已存档的分析")
        for aid, created, fname in analyses:
            settings, result, fid = get_analysis(aid)
            group_desc = "、".join(settings.get("group_cols", []))
            title = f"{fmt_cn(created)} · {fname} · 分组[{group_desc}] · {settings.get('agg_choice', '')}"
            with st.expander(title):
                if result is not None:
                    st.dataframe(result, width="stretch")
                if st.button("复用这组设置", key=f"reuse_{aid}"):
                    df, fname2 = load_file(fid)
                    if df is not None:
                        st.session_state.df = df
                        st.session_state.df_name = fname2
                        st.session_state.file_id = fid
                        st.session_state.group_cols = [c for c in settings.get("group_cols", []) if c in df.columns]
                        st.session_state.agg_choice = settings.get("agg_choice", "求和")
                        val = settings.get("val_col", "")
                        num_cols = df.select_dtypes(include=["number"]).columns.tolist()
                        if settings.get("agg_choice") != "计数" and val in num_cols:
                            st.session_state.val_col = val
                        st.session_state.pop("date_range", None)
                        st.session_state.nav = "数据分析"
                        st.rerun()


def main():
    nav = st.sidebar.radio("导航", ["数据分析", "历史记录"], key="nav")

    if nav == "数据分析":
        analyze_page()
    else:
        history_page()


init_db()

if st.session_state.page == "splash":
    splash()
else:
    main()
