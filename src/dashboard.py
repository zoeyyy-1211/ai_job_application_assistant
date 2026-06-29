import pandas as pd
import plotly.express as px
import streamlit as st


def render_dashboard(df: pd.DataFrame) -> None:
    """渲染第一阶段数据看板。"""
    if df.empty:
        st.info("暂无投递记录。完成一次岗位匹配分析并保存后，这里会显示统计图表。")
        return

    total = len(df)
    avg_score = round(float(df["match_score"].fillna(0).mean()), 1)
    active_count = int(df[df["status"].isin(["笔试", "一面", "二面", "HR面"])].shape[0])

    col1, col2, col3 = st.columns(3)
    col1.metric("总投递数量", total)
    col2.metric("平均匹配度", avg_score)
    col3.metric("面试中数量", active_count)

    status_counts = df["status"].fillna("未填写").value_counts().reset_index()
    status_counts.columns = ["状态", "数量"]
    st.plotly_chart(px.bar(status_counts, x="状态", y="数量", title="不同状态数量"), use_container_width=True)

    type_counts = df["position_type"].fillna("未填写").value_counts().reset_index()
    type_counts.columns = ["岗位类型", "数量"]
    st.plotly_chart(px.pie(type_counts, names="岗位类型", values="数量", title="不同岗位类型数量"), use_container_width=True)
