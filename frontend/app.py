"""
FactorFlow - 因子分析平台
Streamlit 主应用
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import logging
from utils import backend_client

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 页面配置
st.set_page_config(
    page_title="FactorFlow - 因子分析平台",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 自定义 CSS
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""",
    unsafe_allow_html=True,
)


def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        # st.image(
        #     "https://via.placeholder.com/300x100?text=FactorFlow",
        #     width=300,
        # )
        # st.markdown("---")

        page = st.radio(
            "功能菜单",
            ["因子管理", "因子分析"],
            label_visibility="collapsed",
        )

        st.markdown("---")
        st.markdown("### 关于")
        st.markdown(
            """
            **FactorFlow** 是一个基于 Streamlit 和 FastAPI 的量化因子分析平台。

            主要功能：
            - 📊 因子管理和分析
            - 📈 特征工程和可视化
            - 🎯 模型训练和评估
            """
        )

    return page


def render_factor_management():
    """渲染因子管理页面"""
    st.markdown('<div class="main-header">因子管理</div>', unsafe_allow_html=True)

    # 侧边栏统计信息
    with st.sidebar:
        st.subheader("因子统计")
        stats = backend_client.get_factor_stats()
        if stats and stats.get("success"):
            data = stats["data"]
            st.metric("总因子数", data["total"])
            col1, col2 = st.columns(2)
            with col1:
                st.metric("系统因子", data["system_count"])
            with col2:
                st.metric("用户因子", data["user_count"])

            if data.get("categories"):
                st.subheader("分类统计")
                for category, count in data["categories"].items():
                    st.write(f"**{category}**: {count}")

    # Tab 1: 因子列表
    tab1, tab2 = st.tabs(["因子列表", "新增因子"])

    with tab1:
        # 过滤器
        col1, col2 = st.columns([2, 1])
        with col1:
            source_filter = st.selectbox("来源筛选", ["全部", "系统", "用户"])

        # 获取因子列表
        source_map = {"全部": None, "系统": "system", "用户": "user"}
        factors = backend_client.get_factors(source=source_map[source_filter])

        if factors and factors.get("success"):
            factor_data = factors["data"]
            if factor_data:
                df = pd.DataFrame(factor_data)
                display_df = df[["name", "description", "source", "category", "created_at"]]
                display_df.columns = ["因子名称", "说明", "来源", "分类", "创建时间"]
                st.dataframe(display_df, use_container_width=True)

                # 操作按钮
                selected_factor = st.selectbox(
                    "选择要编辑的因子", options=df["name"].tolist()
                )

                if selected_factor:
                    factor_row = df[df["name"] == selected_factor].iloc[0]
                    if st.button(f"编辑因子: {selected_factor}", key="edit"):
                        st.session_state["edit_factor"] = factor_row.to_dict()

                    if factor_row["source"] == "user":
                        if st.button(f"删除因子: {selected_factor}", key="delete"):
                            result = backend_client.delete_factor(factor_row['id'])
                            if result and result.get("success"):
                                st.success("因子删除成功")
                                st.rerun()
            else:
                st.info("暂无因子数据")

    with tab2:
        st.subheader("添加新因子")

        with st.form("new_factor_form"):
            factor_name = st.text_input("因子名称*", help="唯一的因子标识符")
            factor_category = st.selectbox(
                "分类",
                ["price_return", "momentum", "volatility", "volume", "pattern", "custom"],
                help="因子分类",
            )

            st.markdown("#### 因子公式")
            st.markdown(
                """
            **语法说明:**
            - 使用 `df['close']` 访问收盘价
            - 使用 `np.log()` 进行对数计算
            - 使用 `talib.SMA()` 等函数计算技术指标
            - 使用 `pd.Series.rolling()` 进行滚动计算

            **示例:**
            ```python
            # 日对数收益率
            np.log(df['close'] / df['close'].shift(1))

            # RSI 指标
            talib.RSI(df['close'], timeperiod=14)

            # 20日均线
            df['close'].rolling(window=20).mean()
            ```
            """
            )

            factor_formula = st.text_area(
                "因子公式*",
                height=150,
                help="输入计算因子的Python表达式，必须返回pandas Series",
            )

            factor_description = st.text_area(
                "因子说明", height=80, help="详细描述因子的含义和用途"
            )

            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button("保存因子")
            with col2:
                validate = st.form_submit_button("校验公式")

            if validate:
                result = backend_client.validate_formula(factor_formula)
                if result:
                    if result["data"]["valid"]:
                        st.success("✅ 公式校验通过")
                    else:
                        st.error(f"❌ 公式校验失败: {result['data']['error']}")

            if submitted:
                if not factor_name or not factor_formula:
                    st.error("请填写必填字段")
                else:
                    result = backend_client.create_factor(
                        name=factor_name,
                        formula=factor_formula,
                        description=factor_description,
                        category=factor_category,
                    )
                    if result and result.get("success"):
                        st.success("✅ 因子创建成功")
                        st.balloons()


def render_factor_analysis():
    """渲染因子分析页面"""
    st.markdown('<div class="main-header">因子分析</div>', unsafe_allow_html=True)

    # 侧边栏配置
    with st.sidebar:
        st.subheader("分析配置")

        mode = st.selectbox("数据模式", ["单股票", "股票池"])

        if mode == "单股票":
            symbol = st.text_input("股票代码", value="000001", help="股票代码，如 000001")
            symbols = [symbol]
        else:
            symbols_input = st.text_area(
                "股票代码列表",
                value="000001\n000002\n600000",
                help="每行一个代码",
            )
            symbols = [s.strip() for s in symbols_input.split("\n") if s.strip()]

        # 获取可用因子
        factors_response = backend_client.get_factors()
        available_factors = []
        if factors_response and factors_response.get("success"):
            available_factors = [f["name"] for f in factors_response["data"]]

        selected_factors = st.multiselect(
            "选择因子", available_factors, default=available_factors[:5] if available_factors else []
        )

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.text_input("开始日期", value="20230101", help="格式: 20230101")
        with col2:
            end_date = st.text_input("结束日期", value="20241231", help="格式: 20241231")

        analyze_clicked = st.button("开始分析", type="primary")

    if analyze_clicked:
        if not symbols:
            st.error("请输入股票代码")
        elif not selected_factors:
            st.error("请至少选择一个因子")
        else:
            _execute_analysis(symbols, selected_factors, start_date, end_date, mode)


def _execute_analysis(symbols, selected_factors, start_date, end_date, mode):
    """执行分析并显示结果"""
    with st.spinner("正在分析..."):
        analysis_result = backend_client.run_analysis(
            symbols=symbols,
            factors=selected_factors,
            start_date=start_date,
            end_date=end_date,
            mode="single" if mode == "单股票" else "pool",
        )

        if analysis_result and analysis_result.get("success"):
            st.success("分析完成!")

            # 显示结果
            data = analysis_result["data"]
            st.info(f"📊 **分析参数**: 股票={', '.join(symbols)} | 因子数={len(selected_factors)} | 时间区间={start_date} ~ {end_date}")

            tab1, tab2, tab3, tab4 = st.tabs(
                ["行情预览", "特征重要性", "IC 分析", "导出报告"]
            )

            with tab1:
                _render_market_preview(symbols, data)

            with tab2:
                _render_feature_importance(symbols, data)

            with tab3:
                _render_ic_analysis(symbols, data)

            with tab4:
                _render_export_report(symbols, selected_factors, start_date, end_date, data)
        else:
            error_msg = analysis_result.get("detail", "未知错误") if analysis_result else "无法连接到后端服务"
            st.error(f"❌ 分析失败: {error_msg}")
            if analysis_result:
                with st.expander("查看详细错误信息"):
                    st.json(analysis_result)


def _render_market_preview(symbols, data):
    """渲染行情预览"""
    st.subheader("股票行情")

    if not data.get("analysis_results"):
        st.warning("⚠️ 没有分析结果数据")
        return

    for symbol in symbols:
        if symbol in data["analysis_results"]:
            st.write(f"**{symbol}**")
            result = data["analysis_results"][symbol]

            # 检查是否有错误
            if "error" in result:
                st.error(f"❌ {result['error']}")
            else:
                # 显示分析概览
                col1, col2, col3 = st.columns(3)
                with col1:
                    if "train_results" in result:
                        st.metric("样本数", result["train_results"].get("n_samples", "N/A"))
                with col2:
                    if "train_results" in result:
                        st.metric("特征数", result["train_results"].get("n_features", "N/A"))
                with col3:
                    if "train_results" in result:
                        st.metric("训练集 R²", f"{result['train_results']['train_r2']:.4f}")
        else:
            st.warning(f"⚠️ 未找到 {symbol} 的分析结果")


def _render_feature_importance(symbols, data):
    """渲染特征重要性"""
    st.subheader("特征重要性分析")

    if not data.get("analysis_results"):
        st.warning("⚠️ 没有分析结果数据")
        return

    for symbol in symbols:
        if symbol in data["analysis_results"]:
            st.markdown(f"### {symbol}")
            result = data["analysis_results"][symbol]

            # 检查是否有错误
            if "error" in result:
                st.error(f"❌ {result['error']}")
                continue

            if "train_results" in result:
                train_result = result["train_results"]

                # 显示训练指标
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("训练集 R²", f"{train_result['train_r2']:.4f}")
                with col2:
                    st.metric("测试集 R²", f"{train_result['test_r2']:.4f}")
                with col3:
                    st.metric("训练集 RMSE", f"{train_result['train_rmse']:.4f}")
                with col4:
                    st.metric("测试集 RMSE", f"{train_result['test_rmse']:.4f}")

                if "feature_importance" in train_result:
                    importance = train_result["feature_importance"]
                    df_importance = pd.DataFrame(
                        list(importance.items()),
                        columns=["特征", "重要性"],
                    ).sort_values("重要性", ascending=False)

                    st.markdown("#### 特征重要性排名")
                    st.dataframe(df_importance, use_container_width=True)

                    # 绘制柱状图
                    fig = go.Figure(
                        data=[
                            go.Bar(
                                x=df_importance["重要性"],
                                y=df_importance["特征"],
                                orientation="h",
                                marker_color="steelblue",
                            )
                        ]
                    )
                    fig.update_layout(
                        title=f"{symbol} - 特征重要性",
                        xaxis_title="重要性分数",
                        yaxis_title="特征名称",
                        height=max(300, len(df_importance) * 30),
                        yaxis={"categoryorder": "total ascending"},
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("⚠️ 没有特征重要性数据")
            else:
                st.warning("⚠️ 没有训练结果")
        else:
            st.warning(f"⚠️ 未找到 {symbol} 的分析结果")


def _render_ic_analysis(symbols, data):
    """渲染 IC 分析"""
    st.subheader("IC/IR 分析")

    if not data.get("analysis_results"):
        st.warning("⚠️ 没有分析结果数据")
        return

    for symbol in symbols:
        if symbol in data["analysis_results"]:
            st.markdown(f"### {symbol}")
            result = data["analysis_results"][symbol]

            # 检查是否有错误
            if "error" in result:
                st.error(f"❌ {result['error']}")
                continue

            if "ic_results" in result:
                ic_data = result["ic_results"]

                if not ic_data:
                    st.warning("⚠️ 没有 IC 数据")
                    continue

                df_ic = pd.DataFrame(ic_data).T
                df_ic = df_ic.sort_values("abs_ic", ascending=False)

                # 格式化显示
                display_df = df_ic.copy()
                display_df["ic"] = display_df["ic"].apply(lambda x: f"{x:.4f}")
                display_df["ir"] = display_df["ir"].apply(lambda x: f"{x:.4f}")
                display_df["abs_ic"] = display_df["abs_ic"].apply(lambda x: f"{x:.4f}")
                display_df["p_value"] = display_df["p_value"].apply(lambda x: f"{x:.4f}")

                display_df.columns = ["IC值", "IR值", "绝对IC", "P值"]

                st.markdown("#### IC/IR 统计表")
                st.dataframe(display_df, use_container_width=True)

                # 高亮显著因子
                if not df_ic.empty:
                    best_factor = df_ic["abs_ic"].idxmax()
                    best_ic = df_ic.loc[best_factor, "ic"]
                    best_p = df_ic.loc[best_factor, "p_value"]
                    significance = "***" if best_p < 0.01 else "**" if best_p < 0.05 else "*" if best_p < 0.1 else ""
                    st.info(f"🏆 **最佳因子**: {best_factor} (IC={best_ic:.4f}, p={best_p:.4f}{significance})")
            else:
                st.warning("⚠️ 没有 IC 结果")
        else:
            st.warning(f"⚠️ 未找到 {symbol} 的分析结果")


def _render_export_report(symbols, selected_factors, start_date, end_date, data):
    """渲染报告导出"""
    st.subheader("导出报告")

    if not data.get("analysis_results"):
        st.warning("⚠️ 没有分析结果数据")
        return

    if st.button("📄 生成 Markdown 报告", type="primary"):
        # 生成报告内容
        report_lines = [
            "# 因子分析报告",
            f"\n**分析时间**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**股票代码**: {', '.join(symbols)}",
            f"**时间区间**: {start_date} - {end_date}",
            f"**因子数量**: {len(selected_factors)}",
            f"**因子列表**: {', '.join(selected_factors)}",
            "\n---",
            "\n## 分析结果摘要",
        ]

        for symbol in symbols:
            if symbol in data["analysis_results"]:
                result = data["analysis_results"][symbol]

                report_lines.append(f"\n### {symbol}")

                if "error" in result:
                    report_lines.append(f"**错误**: {result['error']}")
                    continue

                if "train_results" in result:
                    tr = result["train_results"]
                    report_lines.append("\n#### 模型训练结果")
                    report_lines.append(f"- 训练集 R²: {tr['train_r2']:.4f}")
                    report_lines.append(f"- 测试集 R²: {tr['test_r2']:.4f}")
                    report_lines.append(f"- 训练集 RMSE: {tr['train_rmse']:.4f}")
                    report_lines.append(f"- 测试集 RMSE: {tr['test_rmse']:.4f}")
                    report_lines.append(f"- 特征数量: {tr['n_features']}")
                    report_lines.append(f"- 样本数量: {tr['n_samples']}")

                    # 特征重要性
                    if "feature_importance" in tr:
                        report_lines.append("\n#### 特征重要性排名")
                        for feat, imp in list(tr["feature_importance"].items())[:10]:
                            report_lines.append(f"{len(report_lines) - 1}. {feat}: {imp:.4f}")

                # IC 分析
                if "ic_results" in result:
                    report_lines.append("\n#### IC/IR 分析")
                    for factor, ic_data in result["ic_results"].items():
                        sig = "***" if ic_data["p_value"] < 0.01 else "**" if ic_data["p_value"] < 0.05 else "*" if ic_data["p_value"] < 0.1 else ""
                        report_lines.append(
                            f"- **{factor}**: IC={ic_data['ic']:.4f}, IR={ic_data['ir']:.4f}, p={ic_data['p_value']:.4f}{sig}"
                        )

        report_lines.append("\n---")
        report_lines.append("\n*本报告由 FactorFlow 自动生成*")

        report_content = "\n".join(report_lines)
        st.download_button(
            label="📥 下载报告",
            data=report_content,
            file_name=f"factor_analysis_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
        )
        st.success("✅ 报告生成成功！点击上方按钮下载")


def main():
    """主函数"""
    st.title("📊 FactorFlow - 因子分析平台")

    # 侧边栏导航
    page = render_sidebar()

    # 路由到对应页面
    if page == "因子管理":
        render_factor_management()
    else:
        render_factor_analysis()


if __name__ == "__main__":
    main()
