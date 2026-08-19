# 法务数据汇总分析 —— 工作指引

这是「法务数据汇总分析」项目(本地 Streamlit 应用)。开发本项目时,遵循以下规范。

## 标准文件位置(开发前先读)
- **开发需求**:`/Users/yueyu/Desktop/app/开发需求.md` —— 要做什么、核心场景
- **技术规范**:`/Users/yueyu/Desktop/app/技术规范.md` —— 技术栈、目录结构、开发约定
- **设计规范**:`/Users/yueyu/Desktop/app/设计规范.md` —— 视觉、页面、交互原则
- **执行步骤**:`/Users/yueyu/Desktop/app/执行步骤.md` —— 分阶段计划

## 开发日志
- 位置:`/Users/yueyu/vibecoding/开发日志/开发日志.md`
- **每次开发后必须更新**:记录「已完成事项」和「待办事项」

## 工作说明
1. 开发前先读「开发需求」和「技术规范」,不偏离已确认的需求
2. 分小步推进,一步一测,不一口气堆大量改动
3. 改完跑测试:`venv/bin/python test_core.py`、`test_ui.py`、`test_history.py`
4. 更新「开发日志」和「执行步骤」的状态
5. 关键决策(改需求、改架构)先同步用户确认,再动手

## 启动方式
- 双击 `启动.command`,或 `venv/bin/streamlit run app.py`
