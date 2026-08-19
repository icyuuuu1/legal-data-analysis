# -*- coding: utf-8 -*-
"""UI 流程测试:用 Streamlit 官方测试框架模拟页面切换"""
from streamlit.testing.v1 import AppTest

at = AppTest.from_file("app.py", default_timeout=30)
at.run()
assert not at.exception, f"开屏页异常:{at.exception}"

at.button[0].click().run()
assert not at.exception, f"数据分析页异常:{at.exception}"

has_upload_hint = any("请导入" in (i.value or "") for i in at.info)
assert has_upload_hint, "数据分析页应提示导入文件"

at.radio[0].set_value("历史记录").run()
assert not at.exception, f"历史记录页异常:{at.exception}"

print("UI 流程测试通过:开屏 → 数据分析 → 历史记录 均无异常")
