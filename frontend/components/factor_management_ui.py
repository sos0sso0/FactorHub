"""
因子管理前端UI组件 - 阶段2新增功能
"""
import streamlit as st
import pandas as pd
import tempfile
import os

from backend.services.factor_service import factor_service
from backend.services.factor_import_service import factor_import_service
from backend.services.formula_compiler_service import formula_compiler_service


def render_csv_import_tab():
    """渲染CSV导入Tab"""
    st.markdown("### 从CSV文件导入因子")

    # 下载模板
    st.markdown("**步骤1: 下载CSV模板**")
    template = factor_import_service.get_import_template()
    csv_data = template.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 下载CSV模板",
        data=csv_data,
        file_name="factor_template.csv",
        mime="text/csv",
        use_container_width=True
    )

    st.markdown("**模板格式说明**")
    st.info("""
    - `date`: 日期列（格式：YYYY-MM-DD）
    - `factor_value`: 因子值列（数值类型）
    """)

    st.markdown("---")
    st.markdown("**步骤2: 上传CSV文件**")

    # 上传文件
    uploaded_file = st.file_uploader(
        "选择CSV文件",
        type=["csv"],
        help="上传包含日期和因子值的CSV文件",
        key="csv_uploader"
    )

    if uploaded_file:
        st.markdown("**步骤3: 配置导入参数**")
        col1, col2 = st.columns(2)
        with col1:
            factor_name = st.text_input(
                "因子名称",
                value="imported_factor",
                help="为导入的因子指定一个名称",
                key="csv_factor_name"
            )
            category = st.text_input(
                "因子分类",
                value="导入",
                help="指定因子所属分类",
                key="csv_category"
            )
        with col2:
            date_column = st.text_input(
                "日期列名",
                value="date",
                help="CSV文件中日期列的名称",
                key="csv_date_col"
            )
            factor_column = st.text_input(
                "因子值列名",
                value="factor_value",
                help="CSV文件中因子值列的名称",
                key="csv_factor_col"
            )

        description = st.text_area(
            "因子描述",
            placeholder="描述因子的含义、计算逻辑等...",
            help="可选：为因子添加说明",
            key="csv_description"
        )

        # 验证按钮
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 验证文件格式", use_container_width=True, key="validate_csv"):
                with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as f:
                    f.write(uploaded_file.getbuffer())
                    temp_path = f.name

                try:
                    validation = factor_import_service.validate_csv_format(
                        temp_path,
                        date_column,
                        factor_column
                    )

                    if validation["valid"]:
                        st.success("✅ 文件格式正确！")
                        st.json(validation["info"])
                    else:
                        st.error("❌ 文件格式错误：")
                        for error in validation["errors"]:
                            st.error(f"• {error}")
                        if validation["warnings"]:
                            st.warning("⚠️ 警告：")
                            for warning in validation["warnings"]:
                                st.warning(f"• {warning}")
                finally:
                    try:
                        os.unlink(temp_path)
                    except Exception as e:
                        import logging
                        logging.getLogger(__name__).debug(f"临时文件删除失败: {e}")

        with col2:
            if st.button("📥 导入因子", type="primary", use_container_width=True, key="import_csv"):
                with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as f:
                    f.write(uploaded_file.getbuffer())
                    temp_path = f.name

                try:
                    result = factor_import_service.import_from_csv(
                        temp_path,
                        factor_name,
                        description,
                        category,
                        date_column,
                        factor_column
                    )

                    if result["success"]:
                        st.success(f"✅ {result['message']}")
                        st.info(f"因子ID: {result['factor_id']}")
                    else:
                        st.error(f"❌ {result['message']}")
                finally:
                    try:
                        os.unlink(temp_path)
                    except Exception as e:
                        import logging
                        logging.getLogger(__name__).debug(f"临时文件删除失败: {e}")


def render_formula_builder_tab():
    """渲染公式构建器Tab"""
    st.markdown("### 可视化公式构建器")

    # 初始化session state
    if "formula_parts" not in st.session_state:
        st.session_state.formula_parts = []

    # 获取可用元素
    elements = formula_compiler_service.get_available_elements()

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("**可用元素**")

        # 价格数据
        with st.expander("📊 价格数据"):
            for key, name in elements["price"].items():
                if st.button(name, key=f"add_price_{key}", use_container_width=True):
                    st.session_state.formula_parts.append({
                        "type": "column",
                        "value": key,
                        "display": name
                    })
                    st.rerun()

        # 技术指标
        with st.expander("📈 技术指标"):
            for key, name in elements["indicators"].items():
                if st.button(name, key=f"add_indicator_{key}", use_container_width=True):
                    st.session_state.formula_parts.append({
                        "type": "function_placeholder",
                        "name": key,
                        "display": name
                    })
                    st.rerun()

        # 运算符
        with st.expander("➕ 运算符"):
            op_cols = st.columns(3)
            for i, (key, name) in enumerate(elements["operators"].items()):
                with op_cols[i % 3]:
                    if st.button(name, key=f"add_op_{key}", use_container_width=True):
                        st.session_state.formula_parts.append({
                            "type": "operator",
                            "value": key,
                            "display": name
                        })
                        st.rerun()

        # 统计函数
        with st.expander("📊 统计函数"):
            for key, name in elements["statistics"].items():
                if st.button(name, key=f"add_stat_{key}", use_container_width=True):
                    st.session_state.formula_parts.append({
                        "type": "function_placeholder",
                        "name": key,
                        "display": name
                    })
                    st.rerun()

        # 清空按钮
        if st.button("🗑️ 清空公式", use_container_width=True, key="clear_formula"):
            st.session_state.formula_parts = []
            if "generated_code" in st.session_state:
                del st.session_state.generated_code
            st.rerun()

    with col2:
        st.markdown("**公式构建**")

        # 显示当前公式
        if st.session_state.formula_parts:
            formula_display = " → ".join([
                p.get("display", str(p.get("value", p.get("name", ""))))
                for p in st.session_state.formula_parts
            ])
            st.info(formula_display)

            # 生成代码按钮
            if st.button("⚙️ 生成代码", use_container_width=True, key="generate_code"):
                try:
                    # 简化版代码生成
                    code_parts = []
                    for part in st.session_state.formula_parts:
                        if part["type"] == "column":
                            code_parts.append(f'df["{part["value"]}"]')
                        elif part["type"] == "operator":
                            code_parts.append(f' {part["value"]} ')
                        elif part["type"] == "function_placeholder":
                            code_parts.append(f'{part["name"]}(df["close"], 20)')

                    generated_code = "".join(code_parts)
                    st.session_state.generated_code = generated_code
                    st.success("✅ 代码生成成功！")
                except Exception as e:
                    st.error(f"❌ 代码生成失败: {e}")
        else:
            st.info("👈 从左侧选择元素开始构建公式")

        # 显示生成的代码
        if "generated_code" in st.session_state:
            st.markdown("**生成的代码**:")
            st.code(st.session_state.generated_code, language="python")

            # 配置参数
            factor_name = st.text_input("因子名称", value="formula_factor", key="formula_name")
            description = st.text_area("因子描述", key="formula_desc")

            # 保存按钮
            if st.button("💾 保存因子", type="primary", use_container_width=True, key="save_formula"):
                try:
                    result = factor_service.create_factor(
                        name=factor_name,
                        code=st.session_state.generated_code,
                        description=description
                    )
                    st.success(f"✅ 因子 '{factor_name}' 创建成功！")
                except Exception as e:
                    st.error(f"❌ 创建失败: {e}")


def render_version_history(factor_id: int, factor_name: str):
    """渲染因子版本历史对话框"""
    st.markdown(f"### 📜 因子版本历史: {factor_name}")

    try:
        versions = factor_service.get_factor_versions(factor_id)

        if not versions:
            st.info("该因子暂无版本历史")
            return

        # 显示版本列表
        for version in versions:
            is_current = "✅ (当前版本)" if version['is_current'] else ""
            with st.expander(f"📦 {version['version_code']} - {version['created_at'][:19]} {is_current}"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown("**变更原因**:")
                    st.text(version.get('change_reason', '无'))

                    st.markdown("**因子代码**:")
                    st.code(version['code'], language="python", line_numbers=True)

                with col2:
                    st.markdown("**操作**")

                    if not version['is_current']:
                        if st.button(
                            f"↩️ 回滚到此版本",
                            key=f"rollback_{version['id']}",
                            use_container_width=True
                        ):
                            try:
                                factor_service.rollback_factor_version(factor_id, version['version_code'])
                                st.success(f"✅ 已回滚到 {version['version_code']}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ 回滚失败: {e}")

                    # 对比当前版本
                    if not version['is_current'] and len(versions) > 1:
                        if st.button(
                            f"🔄 对比当前版本",
                            key=f"compare_{version['id']}",
                            use_container_width=True
                        ):
                            current_version = [v for v in versions if v['is_current']][0]
                            from backend.services.factor_version_service import factor_version_service

                            comparison = factor_version_service.compare_versions(
                                factor_id,
                                version['version_code'],
                                current_version['version_code']
                            )

                            st.markdown("**代码差异**:")
                            if comparison['code_changed']:
                                st.info("✅ 代码有变化")
                            else:
                                st.info("ℹ️ 代码未变化")

    except Exception as e:
        st.error(f"❌ 获取版本历史失败: {e}")


def render_factor_list_with_versions(factors_df: pd.DataFrame):
    """渲染带版本控制的因子列表"""
    # 添加版本控制按钮列
    for idx, row in factors_df.iterrows():
        with st.expander(f"**{row['name']}** ({row['category']})"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**说明**: {row['description']}")

            with col2:
                # 版本控制按钮
                if st.button(f"📜 版本历史", key=f"version_history_{row['id']}"):
                    st.session_state['show_versions_for'] = row['id']
                    st.session_state['show_versions_name'] = row['name']
                    st.rerun()

    # 显示版本历史对话框
    if 'show_versions_for' in st.session_state:
        factor_id = st.session_state['show_versions_for']
        factor_name = st.session_state['show_versions_name']

        st.markdown("---")
        render_version_history(factor_id, factor_name)

        if st.button("🔙 关闭版本历史", key="close_versions"):
            del st.session_state['show_versions_for']
            del st.session_state['show_versions_name']
            st.rerun()
