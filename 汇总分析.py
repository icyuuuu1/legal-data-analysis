# -*- coding: utf-8 -*-
"""
直播退费纠纷 · 数据汇总分析(第二个版本:支持筛选)

在 v1 基础上增加筛选条件,数据管道变成 4 步:
  读数据 → 过滤(时间 / 金额 / 支付方式) → 按主播聚合 → 统计出方案

用法:
  python3 汇总分析.py [用户ID] [筛选条件...]

筛选条件:
  --from 2026-08-13       起始日期(含)
  --to   2026-08-15       结束日期(含)
  --min-amount 500        最低金额(元)
  --pay 苹果内购          只统计某支付方式
"""
import csv
import argparse
from collections import defaultdict

DATA = "data/打赏记录.csv"


def load(path):
    """读打赏记录,返回 [ {列名: 值}, ... ]"""
    with open(path, encoding="utf-8-sig") as f:
        return [row for row in csv.DictReader(f)]


def money(x):
    """金额显示:整数不带小数,小数保留两位"""
    x = float(x)
    return f"{int(x)}" if x == int(x) else f"{x:.2f}"


def filter_records(records, args):
    """按 时间范围 / 最低金额 / 支付方式 过滤"""
    out = []
    for r in records:
        d = r["打赏时间"][:10]          # 只取日期部分,如 2026-08-12
        if args.frm and d < args.frm:
            continue
        if args.to and d > args.to:
            continue
        if args.min_amount is not None and float(r["金额(元)"]) < args.min_amount:
            continue
        if args.pay and r["支付方式"] != args.pay:
            continue
        out.append(r)
    return out


def aggregate(records, user_id):
    """按主播聚合某用户的打赏:每个主播 -> {笔数, 总额}"""
    by_anchor = defaultdict(lambda: {"count": 0, "amount": 0.0})
    for r in records:
        if r["用户ID"] != user_id:
            continue
        by_anchor[r["主播昵称"]]["count"] += 1
        by_anchor[r["主播昵称"]]["amount"] += float(r["金额(元)"])
    return by_anchor


def describe_filter(args):
    """把筛选条件拼成一句话,展示在结果里"""
    parts = []
    if args.frm or args.to:
        parts.append(f"时间 {args.frm or '最早'} ~ {args.to or '最晚'}")
    if args.min_amount is not None:
        parts.append(f"金额 ≥ {money(args.min_amount)} 元")
    if args.pay:
        parts.append(f"支付方式 {args.pay}")
    return " | ".join(parts) if parts else "无"


def main():
    p = argparse.ArgumentParser(description="直播退费纠纷 · 数据汇总分析")
    p.add_argument("user_id", nargs="?", default="U10086", help="用户ID,默认 U10086")
    # 注意:--from 是 argparse 的坑,`from` 是 Python 关键字,
    # 所以必须用 dest="frm" 换名,否则访问 args.from 会语法报错
    p.add_argument("--from", dest="frm", help="起始日期(含),如 2026-08-13")
    p.add_argument("--to", dest="to", help="结束日期(含),如 2026-08-15")
    p.add_argument("--min-amount", type=float, help="最低金额(元)")
    p.add_argument("--pay", help="支付方式,如 微信支付 / 支付宝 / 苹果内购 / 银行卡")
    args = p.parse_args()

    records = load(DATA)
    records = filter_records(records, args)

    by_anchor = aggregate(records, args.user_id)
    if not by_anchor:
        print(f"筛选 [{describe_filter(args)}] 下,用户 {args.user_id} 无打赏记录")
        return

    total = sum(v["amount"] for v in by_anchor.values())
    total_count = sum(v["count"] for v in by_anchor.values())
    nickname = next((r["用户昵称"] for r in records if r["用户ID"] == args.user_id), args.user_id)

    print("=" * 46)
    print(f"用户:{nickname}({args.user_id})")
    print(f"筛选条件:{describe_filter(args)}")
    print(f"打赏笔数:{total_count} 笔 | 总金额:{money(total)} 元")
    print("=" * 46)

    ordered = sorted(by_anchor.items(), key=lambda kv: -kv[1]["amount"])
    for anchor, v in ordered:
        pct = v["amount"] / total * 100
        print(f"主播「{anchor}」: {v['count']} 笔, 合计 {money(v['amount'])} 元, 占比 {pct:.1f}%")

    print("-" * 46)
    print("退费 / 冻结方案:")
    for anchor, v in ordered:
        print(f"  冻结主播「{anchor}」收益 {money(v['amount'])} 元")
    print(f"  合计冻结并退费:{money(total)} 元")


if __name__ == "__main__":
    main()
