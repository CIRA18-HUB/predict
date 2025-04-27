import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import warnings
import os
import re
import base64
from io import BytesIO
from PIL import Image
import calendar

warnings.filterwarnings('ignore')

# 设置页面配置
st.set_page_config(
    page_title="预测与实际销售对比分析仪表盘",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        color: #1f3867;
        text-align: center;
        margin-bottom: 1rem;
    }
    .card-header {
        font-size: 1.2rem;
        font-weight: bold;
        color: #444444;
    }
    .card-value {
        font-size: 1.8rem;
        font-weight: bold;
        color: #1f3867;
    }
    .metric-card {
        background-color: white;
        border-radius: 0.5rem;
        padding: 1rem;
        box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15);
        margin-bottom: 1rem;
    }
    .card-text {
        font-size: 0.9rem;
        color: #6c757d;
    }
    .alert-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .alert-success {
        background-color: rgba(76, 175, 80, 0.1);
        border-left: 0.5rem solid #4CAF50;
    }
    .alert-warning {
        background-color: rgba(255, 152, 0, 0.1);
        border-left: 0.5rem solid #FF9800;
    }
    .alert-danger {
        background-color: rgba(244, 67, 54, 0.1);
        border-left: 0.5rem solid #F44336;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #1f3867;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .chart-explanation {
        background-color: rgba(76, 175, 80, 0.1);
        padding: 0.9rem;
        border-radius: 0.5rem;
        margin: 0.8rem 0;
        border-left: 0.5rem solid #4CAF50;
    }
    .low-accuracy {
        border: 2px solid #F44336;
        box-shadow: 0 0 8px #F44336;
    }
    .logo-container {
        position: absolute;
        top: 0.5rem;
        right: 1rem;
        z-index: 1000;
    }
    .logo-img {
        height: 40px;
    }
    .pagination-btn {
        background-color: #1f3867;
        color: white;
        border: none;
        padding: 5px 10px;
        border-radius: 3px;
        margin: 5px;
        cursor: pointer;
    }
    .pagination-btn:hover {
        background-color: #2c4f8f;
    }
    .pagination-info {
        display: inline-block;
        padding: 5px;
        margin: 5px;
    }
    .hover-info {
        background-color: rgba(0,0,0,0.7);
        color: white;
        padding: 8px;
        border-radius: 4px;
        font-size: 0.9rem;
    }
    .slider-container {
        padding: 10px 0;
    }
    .highlight-product {
        font-weight: bold;
        background-color: #ffeb3b;
        padding: 2px 5px;
        border-radius: 3px;
    }
</style>
""", unsafe_allow_html=True)


# 添加Logo到右上角
def add_logo():
    st.markdown(
        """
        <div class="logo-container">
            <img src="https://www.example.com/logo.png" class="logo-img">
        </div>
        """,
        unsafe_allow_html=True
    )


# 初始化会话状态
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False  # 明确使用字典语法初始化

# 登录界面
if not st.session_state.get('authenticated', False):  # 使用get方法更安全地获取值
    st.markdown(
        '<div style="font-size: 1.5rem; color: #1f3867; text-align: center; margin-bottom: 1rem;">预测与实际销售对比分析仪表盘 | 登录</div>',
        unsafe_allow_html=True)

    # 创建居中的登录框
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("""
        <div style="padding: 20px; border-radius: 10px; border: 1px solid #ddd; box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15);">
            <h2 style="text-align: center; color: #1f3867; margin-bottom: 20px;">请输入密码</h2>
        </div>
        """, unsafe_allow_html=True)

        # 密码输入框
        password = st.text_input("密码", type="password", key="password_input")

        # 登录按钮
        login_button = st.button("登录")

        # 验证密码
        if login_button:
            if password == 'SAL':  # 简易密码，实际应用中应更安全
                st.session_state['authenticated'] = True  # 使用字典语法设置值
                st.success("登录成功！")
                try:
                    st.rerun()  # 尝试使用新版本方法
                except AttributeError:
                    try:
                        st.experimental_rerun()  # 尝试使用旧版本方法
                    except:
                        st.error("请刷新页面以查看更改")
            else:
                st.error("密码错误，请重试！")

    # 如果未认证，不显示后续内容
    st.stop()


# 格式化数值的函数
def format_yuan(value):
    if value >= 100000000:  # 亿元级别
        return f"{value / 100000000:.2f}亿元"
    elif value >= 10000:  # 万元级别
        return f"{value / 10000:.2f}万元"
    else:
        return f"{value:.2f}元"


# 添加图表解释
def add_chart_explanation(explanation_text):
    """添加图表解释"""
    st.markdown(f'<div class="chart-explanation">{explanation_text}</div>', unsafe_allow_html=True)


# 添加动态建议生成函数
def generate_recommendation(product_code, product_name, accuracy, diff_rate, growth_rate=None):
    """根据产品的准确率、差异率和增长率生成针对性建议"""
    product_display = f"{product_code} {product_name}"

    # 基础建议
    if accuracy < 0.7:  # 70%以下准确率
        if diff_rate > 0:  # 实际大于预测，低估了
            adjust_pct = abs(round(diff_rate))
            return f"<span class='highlight-product'>{product_display}</span> 准确率过低({accuracy:.0%})且被低估了{diff_rate:.1f}%，建议提高{adjust_pct}%的预测量和备货"
        else:  # 实际小于预测，高估了
            adjust_pct = abs(round(diff_rate))
            return f"<span class='highlight-product'>{product_display}</span> 准确率过低({accuracy:.0%})且被高估了{abs(diff_rate):.1f}%，建议降低{adjust_pct}%的预测量和备货"

    # 增长与准确率结合的建议
    if growth_rate is not None:
        if growth_rate > 15 and accuracy < 0.8:  # 高增长但准确率不足
            return f"<span class='highlight-product'>{product_display}</span> 增长迅速({growth_rate:.1f}%)但准确率不足({accuracy:.0%})，建议提高{round(growth_rate)}%的备货以满足增长需求"
        elif growth_rate < -10 and diff_rate < 0:  # 下降明显且高估了
            adjust_pct = abs(round(diff_rate))
            return f"<span class='highlight-product'>{product_display}</span> 销量下降明显({growth_rate:.1f}%)且被高估了{abs(diff_rate):.1f}%，建议降低{adjust_pct}%的备货以避免库存积压"

    # 默认情况
    if accuracy > 0.9:  # 准确率很高
        return f"{product_display} 预测准确率高({accuracy:.0%})，建议维持当前预测方法"

    return f"{product_display} 建议持续关注市场变化，确保预测与实际一致"


# 数据加载函数增强
@st.cache_data
def load_product_info(file_path=None):
    """加载产品信息数据"""
    try:
        # 默认路径或示例数据
        if file_path is None or not os.path.exists(file_path):
            # 创建示例数据
            return create_sample_product_info()

        # 加载数据
        df = pd.read_excel(file_path)

        # 确保列名格式一致
        required_columns = ['产品代码', '产品名称']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            st.error(f"产品信息文件缺少必要的列: {', '.join(missing_columns)}。使用示例数据进行演示。")
            return create_sample_product_info()

        # 确保数据类型正确
        df['产品代码'] = df['产品代码'].astype(str)
        df['产品名称'] = df['产品名称'].astype(str)

        return df

    except Exception as e:
        st.error(f"加载产品信息数据时出错: {str(e)}。使用示例数据进行演示。")
        return create_sample_product_info()


def create_sample_product_info():
    """创建示例产品信息数据"""
    # 产品代码列表
    product_codes = [
        'F0104L', 'F01E4P', 'F01E6C', 'F3406B', 'F3409N', 'F3411A',
        'F01E4B', 'F0183F', 'F0110C', 'F0104J', 'F0104M', 'F0104P',
        'F0110A', 'F0110B', 'F0115C', 'F0101P'
    ]

    # 产品名称列表
    product_names = [
        '比萨袋', '汉堡大袋', '汉堡中袋', '海洋动物', '幻彩蜥蜴', '午餐袋',
        '口力汉堡', '口力热狗', '口力奶酪', '比萨小包', '比萨中包', '比萨大包',
        '口力薯条', '口力鸡块', '口力汉堡圈', '德果汉堡'
    ]

    # 产品规格
    product_specs = [
        '68g*24', '120g*24', '108g*24', '100g*24', '105g*24', '77g*24',
        '137g*24', '120g*24', '90g*24', '60g*24', '80g*24', '100g*24',
        '65g*24', '75g*24', '85g*24', '108g*24'
    ]

    # 示例单价数据
    prices = np.random.uniform(100, 300, len(product_codes))
    prices = [round(price, 2) for price in prices]

    # 创建DataFrame
    data = {'产品代码': product_codes,
            '产品名称': product_names,
            '产品规格': product_specs,
            '产品单价': prices}

    return pd.DataFrame(data)


# 产品代码映射函数
def format_product_code(code, product_info_df, include_name=True):
    """将产品代码格式化为带名称的格式"""
    if product_info_df is None or code not in product_info_df['产品代码'].values:
        return code

    if include_name:
        product_name = product_info_df[product_info_df['产品代码'] == code]['产品名称'].iloc[0]
        return f"{code} {product_name}"
    else:
        return code


@st.cache_data
def load_actual_data(file_path=None):
    """加载实际销售数据"""
    try:
        # 默认路径或示例数据
        if file_path is None or not os.path.exists(file_path):
            # 创建示例数据
            return load_sample_actual_data()

        # 加载数据
        df = pd.read_excel(file_path)

        # 确保列名格式一致
        required_columns = ['订单日期', '所属区域', '申请人', '产品代码', '求和项:数量（箱）']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            st.error(f"实际销售数据文件缺少必要的列: {', '.join(missing_columns)}。使用示例数据进行演示。")
            return load_sample_actual_data()

        # 确保数据类型正确
        df['订单日期'] = pd.to_datetime(df['订单日期'])
        df['所属区域'] = df['所属区域'].astype(str)
        df['申请人'] = df['申请人'].astype(str)
        df['产品代码'] = df['产品代码'].astype(str)
        df['求和项:数量（箱）'] = df['求和项:数量（箱）'].astype(float)

        # 创建年月字段，用于与预测数据对齐
        df['所属年月'] = df['订单日期'].dt.strftime('%Y-%m')

        return df

    except Exception as e:
        st.error(f"加载实际销售数据时出错: {str(e)}。使用示例数据进行演示。")
        return load_sample_actual_data()


@st.cache_data
def load_forecast_data(file_path=None):
    """加载预测数据"""
    try:
        # 默认路径或示例数据
        if file_path is None or not os.path.exists(file_path):
            # 创建示例数据
            return load_sample_forecast_data()

        # 加载数据
        df = pd.read_excel(file_path)

        # 确保列名格式一致
        required_columns = ['所属大区', '销售员', '所属年月', '产品代码', '预计销售量']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            st.error(f"预测数据文件缺少必要的列: {', '.join(missing_columns)}。使用示例数据进行演示。")
            return load_sample_forecast_data()

        # 确保数据类型正确
        df['所属大区'] = df['所属大区'].astype(str)
        df['销售员'] = df['销售员'].astype(str)
        df['所属年月'] = pd.to_datetime(df['所属年月']).dt.strftime('%Y-%m')
        df['产品代码'] = df['产品代码'].astype(str)
        df['预计销售量'] = df['预计销售量'].astype(float)

        # 为了保持一致，将'所属大区'列重命名为'所属区域'
        df = df.rename(columns={'所属大区': '所属区域'})

        return df

    except Exception as e:
        st.error(f"加载预测数据时出错: {str(e)}。使用示例数据进行演示。")
        return load_sample_forecast_data()


@st.cache_data
def load_price_data(file_path=None):
    """加载单价数据"""
    try:
        # 默认路径或示例数据
        if file_path is None or not os.path.exists(file_path):
            # 创建示例数据
            return load_sample_price_data()

        # 加载数据
        df = pd.read_excel(file_path)

        # 确保列名格式一致
        required_columns = ['产品代码', '单价']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            st.error(f"单价数据文件缺少必要的列: {', '.join(missing_columns)}。使用示例数据进行演示。")
            return load_sample_price_data()

        # 确保数据类型正确
        df['产品代码'] = df['产品代码'].astype(str)
        df['单价'] = df['单价'].astype(float)

        return df

    except Exception as e:
        st.error(f"加载单价数据时出错: {str(e)}。使用示例数据进行演示。")
        return load_sample_price_data()


# 示例数据创建函数
def load_sample_actual_data():
    """创建示例实际销售数据"""
    # 产品代码列表
    product_codes = [
        'F0104L', 'F01E4P', 'F01E6C', 'F3406B', 'F3409N', 'F3411A',
        'F01E4B', 'F0183F', 'F0110C', 'F0104J', 'F0104M', 'F0104P',
        'F0110A', 'F0110B', 'F0115C', 'F0101P'
    ]

    # 区域列表
    regions = ['北', '南', '东', '西']

    # 申请人列表
    applicants = ['孙杨', '李根', '张伟', '王芳', '刘涛', '陈明']

    # 生成日期范围
    start_date = datetime(2023, 9, 1)
    end_date = datetime(2025, 2, 24)
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')

    # 创建数据
    data = []
    for date in date_range:
        # 为每天生成随机数量的记录
        num_records = np.random.randint(3, 10)

        for _ in range(num_records):
            region = np.random.choice(regions)
            applicant = np.random.choice(applicants)
            product_code = np.random.choice(product_codes)
            quantity = np.random.randint(5, 300)

            data.append({
                '订单日期': date,
                '所属区域': region,
                '申请人': applicant,
                '产品代码': product_code,
                '求和项:数量（箱）': quantity
            })

    # 创建DataFrame
    df = pd.DataFrame(data)

    # 添加年月字段
    df['所属年月'] = df['订单日期'].dt.strftime('%Y-%m')

    return df


def load_sample_forecast_data():
    """创建示例预测数据"""
    # 产品代码列表
    product_codes = [
        'F0104L', 'F01E4P', 'F01E6C', 'F3406B', 'F3409N', 'F3411A',
        'F01E4B', 'F0183F', 'F0110C', 'F0104J', 'F0104M', 'F0104P',
        'F0110A', 'F0110B', 'F0115C', 'F0101P'
    ]

    # 区域列表
    regions = ['北', '南', '东', '西']

    # 销售员列表
    sales_people = ['李根', '张伟', '王芳', '刘涛', '陈明', '孙杨']

    # 生成月份范围
    start_date = datetime(2023, 9, 1)
    end_date = datetime(2025, 2, 1)
    month_range = pd.date_range(start=start_date, end=end_date, freq='MS')

    # 创建数据
    data = []
    for month in month_range:
        month_str = month.strftime('%Y-%m')

        for region in regions:
            for sales_person in sales_people:
                for product_code in product_codes:
                    # 使用正态分布生成预测值，使其变化更自然
                    forecast = max(0, np.random.normal(150, 50))

                    # 有些产品可能没有预测
                    if np.random.random() > 0.1:  # 90%的概率有预测
                        data.append({
                            '所属大区': region,
                            '销售员': sales_person,
                            '所属年月': month_str,
                            '产品代码': product_code,
                            '预计销售量': round(forecast)
                        })

    # 创建DataFrame
    df = pd.DataFrame(data)
    return df


def load_sample_price_data():
    """创建示例单价数据"""
    # 产品代码列表
    product_codes = [
        'F0104L', 'F01E4P', 'F01E6C', 'F3406B', 'F3409N', 'F3411A',
        'F01E4B', 'F0183F', 'F0110C', 'F0104J', 'F0104M', 'F0104P',
        'F0110A', 'F0110B', 'F0115C', 'F0101P'
    ]

    # 生成随机单价
    data = []
    for product_code in product_codes:
        # 单价在100-300之间
        price = round(np.random.uniform(100, 300), 2)
        data.append({
            '产品代码': product_code,
            '单价': price
        })

    # 创建DataFrame
    df = pd.DataFrame(data)
    return df


# 获取最近3个月的函数
def get_last_three_months():
    today = datetime.now()
    current_month = today.replace(day=1)

    last_month = current_month - timedelta(days=1)
    last_month = last_month.replace(day=1)

    two_months_ago = last_month - timedelta(days=1)
    two_months_ago = two_months_ago.replace(day=1)

    months = []
    for dt in [two_months_ago, last_month, current_month]:
        months.append(dt.strftime('%Y-%m'))

    return months


# 数据处理和分析函数
def process_data(actual_df, forecast_df, price_df, product_info_df):
    """处理数据并计算关键指标"""
    # 合并单价数据
    actual_with_price = pd.merge(actual_df, price_df, on='产品代码', how='left')
    forecast_with_price = pd.merge(forecast_df, price_df, on='产品代码', how='left')

    # 计算销售额
    actual_with_price['销售额'] = actual_with_price['求和项:数量（箱）'] * actual_with_price['单价']
    forecast_with_price['预测销售额'] = forecast_with_price['预计销售量'] * forecast_with_price['单价']

    # 处理可能的空值
    actual_with_price['销售额'] = actual_with_price['销售额'].fillna(0)
    forecast_with_price['预测销售额'] = forecast_with_price['预测销售额'].fillna(0)

    # 按月份、区域、产品码汇总数据
    actual_monthly = actual_with_price.groupby(['所属年月', '所属区域', '产品代码']).agg({
        '求和项:数量（箱）': 'sum',
        '销售额': 'sum'
    }).reset_index()

    forecast_monthly = forecast_with_price.groupby(['所属年月', '所属区域', '产品代码']).agg({
        '预计销售量': 'sum',
        '预测销售额': 'sum'
    }).reset_index()

    # 按销售员细分的预测数据
    forecast_by_salesperson = forecast_with_price.groupby(['所属年月', '所属区域', '销售员', '产品代码']).agg({
        '预计销售量': 'sum',
        '预测销售额': 'sum'
    }).reset_index()

    # 实际按销售员细分的数据
    actual_by_salesperson = actual_with_price.groupby(['所属年月', '所属区域', '申请人', '产品代码']).agg({
        '求和项:数量（箱）': 'sum',
        '销售额': 'sum'
    }).reset_index()

    # 重命名列，使合并更容易
    actual_by_salesperson = actual_by_salesperson.rename(columns={'申请人': '销售员'})

    # 合并预测和实际数据
    # 按区域和产品级别
    merged_monthly = pd.merge(
        actual_monthly,
        forecast_monthly,
        on=['所属年月', '所属区域', '产品代码'],
        how='outer'
    )

    # 按销售员级别
    merged_by_salesperson = pd.merge(
        actual_by_salesperson,
        forecast_by_salesperson,
        on=['所属年月', '所属区域', '销售员', '产品代码'],
        how='outer'
    )

    # 填充缺失值为0
    for df in [merged_monthly, merged_by_salesperson]:
        df['求和项:数量（箱）'] = df['求和项:数量（箱）'].fillna(0)
        df['销售额'] = df['销售额'].fillna(0)
        df['预计销售量'] = df['预计销售量'].fillna(0)
        df['预测销售额'] = df['预测销售额'].fillna(0)

    # 计算差异和准确率
    for df in [merged_monthly, merged_by_salesperson]:
        # 差异额
        df['数量差异'] = df['求和项:数量（箱）'] - df['预计销售量']
        df['销售额差异'] = df['销售额'] - df['预测销售额']

        # 差异率 (避免除以零)
        df['数量差异率'] = np.where(
            df['求和项:数量（箱）'] > 0,
            df['数量差异'] / df['求和项:数量（箱）'] * 100,
            np.where(
                df['预计销售量'] > 0,
                -100,  # 预测有值但实际为0
                0  # 预测和实际都是0
            )
        )

        df['销售额差异率'] = np.where(
            df['销售额'] > 0,
            df['销售额差异'] / df['销售额'] * 100,
            np.where(
                df['预测销售额'] > 0,
                -100,  # 预测有值但实际为0
                0  # 预测和实际都是0
            )
        )

        # 准确率 (基础公式: 1 - |差异率/100|)
        df['数量准确率'] = np.where(
            (df['求和项:数量（箱）'] > 0) | (df['预计销售量'] > 0),
            np.maximum(0, 100 - np.abs(df['数量差异率'])) / 100,
            1  # 预测和实际都是0时准确率为100%
        )

        df['销售额准确率'] = np.where(
            (df['销售额'] > 0) | (df['预测销售额'] > 0),
            np.maximum(0, 100 - np.abs(df['销售额差异率'])) / 100,
            1  # 预测和实际都是0时准确率为100%
        )

    # 计算总体准确率
    national_accuracy = calculate_national_accuracy(merged_monthly)
    regional_accuracy = calculate_regional_accuracy(merged_monthly)

    # 计算产品增长率
    product_growth = calculate_product_growth(actual_monthly)

    # 计算占比80%的SKU
    national_top_skus = calculate_top_skus(merged_monthly, by_region=False)
    regional_top_skus = calculate_top_skus(merged_monthly, by_region=True)

    return {
        'actual_with_price': actual_with_price,
        'forecast_with_price': forecast_with_price,
        'actual_monthly': actual_monthly,
        'forecast_monthly': forecast_monthly,
        'merged_monthly': merged_monthly,
        'merged_by_salesperson': merged_by_salesperson,
        'national_accuracy': national_accuracy,
        'regional_accuracy': regional_accuracy,
        'product_growth': product_growth,
        'national_top_skus': national_top_skus,
        'regional_top_skus': regional_top_skus
    }


def calculate_national_accuracy(merged_df):
    """计算全国的预测准确率"""
    # 按月份汇总
    monthly_summary = merged_df.groupby('所属年月').agg({
        '求和项:数量（箱）': 'sum',
        '销售额': 'sum',
        '预计销售量': 'sum',
        '预测销售额': 'sum'
    }).reset_index()

    # 计算差异
    monthly_summary['数量差异'] = monthly_summary['求和项:数量（箱）'] - monthly_summary['预计销售量']
    monthly_summary['销售额差异'] = monthly_summary['销售额'] - monthly_summary['预测销售额']

    # 计算差异率
    monthly_summary['数量差异率'] = monthly_summary['数量差异'] / monthly_summary['求和项:数量（箱）'] * 100
    monthly_summary['销售额差异率'] = monthly_summary['销售额差异'] / monthly_summary['销售额'] * 100

    # 计算准确率
    monthly_summary['数量准确率'] = np.maximum(0, 100 - np.abs(monthly_summary['数量差异率'])) / 100
    monthly_summary['销售额准确率'] = np.maximum(0, 100 - np.abs(monthly_summary['销售额差异率'])) / 100

    # 计算整体平均准确率
    overall = {
        '数量准确率': monthly_summary['数量准确率'].mean(),
        '销售额准确率': monthly_summary['销售额准确率'].mean()
    }

    return {
        'monthly': monthly_summary,
        'overall': overall
    }


def calculate_regional_accuracy(merged_df):
    """计算各区域的预测准确率"""
    # 按月份和区域汇总
    region_monthly_summary = merged_df.groupby(['所属年月', '所属区域']).agg({
        '求和项:数量（箱）': 'sum',
        '销售额': 'sum',
        '预计销售量': 'sum',
        '预测销售额': 'sum'
    }).reset_index()

    # 计算差异
    region_monthly_summary['数量差异'] = region_monthly_summary['求和项:数量（箱）'] - region_monthly_summary[
        '预计销售量']
    region_monthly_summary['销售额差异'] = region_monthly_summary['销售额'] - region_monthly_summary['预测销售额']

    # 计算差异率
    region_monthly_summary['数量差异率'] = region_monthly_summary['数量差异'] / region_monthly_summary[
        '求和项:数量（箱）'] * 100
    region_monthly_summary['销售额差异率'] = region_monthly_summary['销售额差异'] / region_monthly_summary[
        '销售额'] * 100

    # 计算准确率
    region_monthly_summary['数量准确率'] = np.maximum(0, 100 - np.abs(region_monthly_summary['数量差异率'])) / 100
    region_monthly_summary['销售额准确率'] = np.maximum(0, 100 - np.abs(region_monthly_summary['销售额差异率'])) / 100

    # 按区域计算平均准确率
    region_overall = region_monthly_summary.groupby('所属区域').agg({
        '数量准确率': 'mean',
        '销售额准确率': 'mean'
    }).reset_index()

    return {
        'region_monthly': region_monthly_summary,
        'region_overall': region_overall
    }


def calculate_product_growth(actual_monthly):
    """计算产品三个月滚动同比增长率"""
    # 确保数据按时间排序
    actual_monthly['所属年月'] = pd.to_datetime(actual_monthly['所属年月'])
    actual_monthly = actual_monthly.sort_values('所属年月')

    # 按产品和月份汇总全国销量
    national_monthly_sales = actual_monthly.groupby(['所属年月', '产品代码']).agg({
        '求和项:数量（箱）': 'sum',
        '销售额': 'sum'
    }).reset_index()

    # 创建年和月字段
    national_monthly_sales['年'] = national_monthly_sales['所属年月'].dt.year
    national_monthly_sales['月'] = national_monthly_sales['所属年月'].dt.month

    # 计算每个产品在每个月的销量
    pivot_sales = national_monthly_sales.pivot_table(
        index=['产品代码', '年'],
        columns='月',
        values='求和项:数量（箱）',
        aggfunc='sum'
    ).reset_index()

    # 计算销售额版本的透视表
    pivot_amount = national_monthly_sales.pivot_table(
        index=['产品代码', '年'],
        columns='月',
        values='销售额',
        aggfunc='sum'
    ).reset_index()

    # 准备用于计算增长率的数据结构
    growth_data = []

    # 获取所有产品的唯一列表
    products = pivot_sales['产品代码'].unique()

    # 获取所有年份
    years = pivot_sales['年'].unique()
    years.sort()

    # 如果有多个年份，可以计算同比增长
    if len(years) > 1:
        for product in products:
            # 获取该产品的所有年份数据
            product_data = pivot_sales[pivot_sales['产品代码'] == product]
            product_amount = pivot_amount[pivot_amount['产品代码'] == product]

            for i in range(1, len(years)):
                current_year = years[i]
                prev_year = years[i - 1]

                # 获取当前年和前一年的数据
                current_year_data = product_data[product_data['年'] == current_year]
                prev_year_data = product_data[product_data['年'] == prev_year]

                current_year_amount = product_amount[product_amount['年'] == current_year]
                prev_year_amount = product_amount[product_amount['年'] == prev_year]

                # 检查是否有足够的数据计算增长率
                if not current_year_data.empty and not prev_year_data.empty:
                    # 对于每个月，计算3个月滚动总量和增长率
                    for month in range(3, 13):
                        # 计算当前3个月的总量
                        current_3m_sum = 0
                        months_current = []
                        for m in range(month - 2, month + 1):
                            if m in current_year_data.columns:
                                current_3m_sum += current_year_data[m].iloc[0] if not pd.isna(
                                    current_year_data[m].iloc[0]) else 0
                                months_current.append(m)

                        # 计算前一年同期3个月的总量
                        prev_3m_sum = 0
                        months_prev = []
                        for m in range(month - 2, month + 1):
                            if m in prev_year_data.columns:
                                prev_3m_sum += prev_year_data[m].iloc[0] if not pd.isna(
                                    prev_year_data[m].iloc[0]) else 0
                                months_prev.append(m)

                        # 只有当两个时期都有数据时才计算增长率
                        if current_3m_sum > 0 and prev_3m_sum > 0 and len(months_current) > 0 and len(months_prev) > 0:
                            growth_rate = (current_3m_sum - prev_3m_sum) / prev_3m_sum * 100

                            # 同样计算销售额增长率
                            current_3m_amount = 0
                            for m in months_current:
                                if m in current_year_amount.columns:
                                    current_3m_amount += current_year_amount[m].iloc[0] if not pd.isna(
                                        current_year_amount[m].iloc[0]) else 0

                            prev_3m_amount = 0
                            for m in months_prev:
                                if m in prev_year_amount.columns:
                                    prev_3m_amount += prev_year_amount[m].iloc[0] if not pd.isna(
                                        prev_year_amount[m].iloc[0]) else 0

                            amount_growth_rate = 0
                            if current_3m_amount > 0 and prev_3m_amount > 0:
                                amount_growth_rate = (current_3m_amount - prev_3m_amount) / prev_3m_amount * 100

                            # 记录增长率数据
                            growth_data.append({
                                '产品代码': product,
                                '年': current_year,
                                '月': month,
                                '3个月滚动销量': current_3m_sum,
                                '去年同期3个月滚动销量': prev_3m_sum,
                                '销量增长率': growth_rate,
                                '3个月滚动销售额': current_3m_amount,
                                '去年同期3个月滚动销售额': prev_3m_amount,
                                '销售额增长率': amount_growth_rate
                            })

    # 创建增长率DataFrame
    growth_df = pd.DataFrame(growth_data)

    # 如果有增长数据，添加趋势判断
    if not growth_df.empty:
        # 取最近一个月的增长率
        latest_growth = growth_df.sort_values(['年', '月'], ascending=False).groupby('产品代码').first().reset_index()

        # 添加趋势判断
        latest_growth['趋势'] = np.where(
            latest_growth['销量增长率'] > 10, '强劲增长',
            np.where(
                latest_growth['销量增长率'] > 0, '增长',
                np.where(
                    latest_growth['销量增长率'] > -10, '轻微下降',
                    '显著下降'
                )
            )
        )

        # 添加销售额趋势判断
        latest_growth['销售额趋势'] = np.where(
            latest_growth['销售额增长率'] > 10, '强劲增长',
            np.where(
                latest_growth['销售额增长率'] > 0, '增长',
                np.where(
                    latest_growth['销售额增长率'] > -10, '轻微下降',
                    '显著下降'
                )
            )
        )

        # 添加建议
        latest_growth['备货建议'] = np.where(
            latest_growth['趋势'].isin(['强劲增长', '增长']), '增加备货',
            np.where(
                latest_growth['趋势'] == '轻微下降', '维持当前备货水平',
                '减少备货'
            )
        )

        return {
            'all_growth': growth_df,
            'latest_growth': latest_growth
        }

    else:
        return {
            'all_growth': pd.DataFrame(),
            'latest_growth': pd.DataFrame()
        }


def calculate_top_skus(merged_df, by_region=False):
    """计算占销售额80%的SKU及其准确率"""
    if by_region:
        # 按区域、产品汇总
        grouped = merged_df.groupby(['所属区域', '产品代码']).agg({
            '销售额': 'sum',
            '数量准确率': 'mean',
            '销售额准确率': 'mean'
        }).reset_index()

        # 计算各区域的占比80%SKU
        results = {}
        for region in grouped['所属区域'].unique():
            region_data = grouped[grouped['所属区域'] == region].copy()
            total_sales = region_data['销售额'].sum()

            # 按销售额降序排序
            region_data = region_data.sort_values('销售额', ascending=False)

            # 计算累计销售额和占比
            region_data['累计销售额'] = region_data['销售额'].cumsum()
            region_data['累计占比'] = region_data['累计销售额'] / total_sales * 100

            # 筛选占比80%的SKU
            top_skus = region_data[region_data['累计占比'] <= 80].copy()

            # 如果没有SKU达到80%阈值，至少取前3个SKU
            if top_skus.empty:
                top_skus = region_data.head(min(3, len(region_data)))

            results[region] = top_skus

        return results

    else:
        # 全国汇总
        grouped = merged_df.groupby('产品代码').agg({
            '销售额': 'sum',
            '数量准确率': 'mean',
            '销售额准确率': 'mean'
        }).reset_index()

        total_sales = grouped['销售额'].sum()

        # 按销售额降序排序
        grouped = grouped.sort_values('销售额', ascending=False)

        # 计算累计销售额和占比
        grouped['累计销售额'] = grouped['销售额'].cumsum()
        grouped['累计占比'] = grouped['累计销售额'] / total_sales * 100

        # 筛选占比80%的SKU
        top_skus = grouped[grouped['累计占比'] <= 80].copy()

        # 如果没有SKU达到80%阈值，至少取前5个SKU
        if top_skus.empty:
            top_skus = grouped.head(min(5, len(grouped)))

        return top_skus


# 图表分页器组件
def display_chart_paginator(df, chart_function, page_size, title, key_prefix):
    """创建图表分页器"""
    total_items = len(df)
    total_pages = (total_items + page_size - 1) // page_size

    if f"{key_prefix}_current_page" not in st.session_state:
        st.session_state[f"{key_prefix}_current_page"] = 0

    # 创建分页控制
    col1, col2, col3 = st.columns([1, 3, 1])

    with col1:
        if st.button("上一页", key=f"{key_prefix}_prev", disabled=st.session_state[f"{key_prefix}_current_page"] <= 0):
            st.session_state[f"{key_prefix}_current_page"] -= 1

    with col2:
        st.markdown(
            f"<div style='text-align:center' class='pagination-info'>第 {st.session_state[f'{key_prefix}_current_page'] + 1} 页，共 {total_pages} 页</div>",
            unsafe_allow_html=True)

    with col3:
        if st.button("下一页", key=f"{key_prefix}_next",
                     disabled=st.session_state[f"{key_prefix}_current_page"] >= total_pages - 1):
            st.session_state[f"{key_prefix}_current_page"] += 1

    # 确保当前页在有效范围内
    if st.session_state[f"{key_prefix}_current_page"] >= total_pages:
        st.session_state[f"{key_prefix}_current_page"] = total_pages - 1
    if st.session_state[f"{key_prefix}_current_page"] < 0:
        st.session_state[f"{key_prefix}_current_page"] = 0

    # 获取当前页的数据
    start_idx = st.session_state[f"{key_prefix}_current_page"] * page_size
    end_idx = min(start_idx + page_size, total_items)
    page_data = df.iloc[start_idx:end_idx]

    # 显示图表
    chart_function(page_data, title)


# 主程序开始
add_logo()  # 添加Logo

# 标题
st.markdown('<div class="main-header">预测与实际销售对比分析仪表盘</div>', unsafe_allow_html=True)

# 侧边栏 - 上传文件区域
st.sidebar.header("📂 数据导入")
use_default_files = st.sidebar.checkbox("使用默认文件", value=True, help="使用指定的默认文件路径")

# 定义默认文件路径
DEFAULT_ACTUAL_FILE = "2409~250224出货数据.xlsx"
DEFAULT_FORECAST_FILE = "2409~2502人工预测.xlsx"
DEFAULT_PRICE_FILE = "单价.xlsx"
DEFAULT_PRODUCT_FILE = "产品信息.xlsx"

if use_default_files:
    # 使用默认文件路径
    actual_data = load_actual_data(DEFAULT_ACTUAL_FILE)
    forecast_data = load_forecast_data(DEFAULT_FORECAST_FILE)
    price_data = load_price_data(DEFAULT_PRICE_FILE)
    product_info = load_product_info(DEFAULT_PRODUCT_FILE)

    if os.path.exists(DEFAULT_ACTUAL_FILE):
        st.sidebar.success(f"已成功加载默认出货数据文件")
    else:
        st.sidebar.warning(f"默认出货数据文件不存在，使用示例数据")

    if os.path.exists(DEFAULT_FORECAST_FILE):
        st.sidebar.success(f"已成功加载默认预测数据文件")
    else:
        st.sidebar.warning(f"默认预测数据文件不存在，使用示例数据")

    if os.path.exists(DEFAULT_PRICE_FILE):
        st.sidebar.success(f"已成功加载默认单价数据文件")
    else:
        st.sidebar.warning(f"默认单价数据文件不存在，使用示例数据")

    if os.path.exists(DEFAULT_PRODUCT_FILE):
        st.sidebar.success(f"已成功加载默认产品信息文件")
    else:
        st.sidebar.warning(f"默认产品信息文件不存在，使用示例数据")
else:
    # 上传文件
    uploaded_actual = st.sidebar.file_uploader("上传出货数据文件", type=["xlsx", "xls"])
    uploaded_forecast = st.sidebar.file_uploader("上传人工预测数据文件", type=["xlsx", "xls"])
    uploaded_price = st.sidebar.file_uploader("上传单价数据文件", type=["xlsx", "xls"])
    uploaded_product = st.sidebar.file_uploader("上传产品信息文件", type=["xlsx", "xls"])

    # 加载数据
    actual_data = load_actual_data(uploaded_actual if uploaded_actual else None)
    forecast_data = load_forecast_data(uploaded_forecast if uploaded_forecast else None)
    price_data = load_price_data(uploaded_price if uploaded_price else None)
    product_info = load_product_info(uploaded_product if uploaded_product else None)

# 创建产品代码到名称的映射
product_names_map = {}
if not product_info.empty:
    for _, row in product_info.iterrows():
        product_names_map[row['产品代码']] = row['产品名称']

# 处理数据
processed_data = process_data(actual_data, forecast_data, price_data, product_info)

# 获取数据的所有月份
all_months = sorted(processed_data['merged_monthly']['所属年月'].unique())
latest_month = all_months[-1] if all_months else None

# 获取最近3个月
last_three_months = get_last_three_months()
valid_last_three_months = [month for month in last_three_months if month in all_months]

# 侧边栏 - 月份选择
selected_months = st.sidebar.multiselect(
    "选择分析月份",
    options=all_months,
    default=valid_last_three_months if valid_last_three_months else ([all_months[-1]] if all_months else [])
)

# 侧边栏 - 区域选择
all_regions = sorted(processed_data['merged_monthly']['所属区域'].unique())
selected_regions = st.sidebar.multiselect(
    "选择区域",
    options=all_regions,
    default=all_regions
)

# 创建标签页
tabs = st.tabs(["📊 总览", "📈 产品趋势", "🔍 重点SKU分析", "🔄 预测差异", "📉 历史趋势"])

# 筛选选定月份和区域的数据
filtered_monthly = processed_data['merged_monthly'][
    (processed_data['merged_monthly']['所属年月'].isin(selected_months)) &
    (processed_data['merged_monthly']['所属区域'].isin(selected_regions))
    ]

filtered_salesperson = processed_data['merged_by_salesperson'][
    (processed_data['merged_by_salesperson']['所属年月'].isin(selected_months)) &
    (processed_data['merged_by_salesperson']['所属区域'].isin(selected_regions))
    ]

with tabs[0]:  # 总览标签页
    st.subheader("🔑 关键绩效指标")

    # 计算总览KPI
    total_actual_sales = filtered_monthly['销售额'].sum()
    total_forecast_sales = filtered_monthly['预测销售额'].sum()
    total_diff = total_actual_sales - total_forecast_sales
    total_diff_percent = (total_diff / total_actual_sales * 100) if total_actual_sales > 0 else 0

    # 计算全国和选定区域的准确率
    national_qty_accuracy = processed_data['national_accuracy']['overall']['数量准确率'] * 100
    national_amount_accuracy = processed_data['national_accuracy']['overall']['销售额准确率'] * 100

    # 过滤选定区域的准确率
    selected_regions_accuracy = processed_data['regional_accuracy']['region_overall'][
        processed_data['regional_accuracy']['region_overall']['所属区域'].isin(selected_regions)
    ]
    selected_regions_qty_accuracy = selected_regions_accuracy['数量准确率'].mean() * 100
    selected_regions_amount_accuracy = selected_regions_accuracy['销售额准确率'].mean() * 100

    # 指标卡行
    col1, col2, col3, col4 = st.columns(4)

    # 总销售额
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <p class="card-header">实际销售额</p>
            <p class="card-value">{format_yuan(total_actual_sales)}</p>
            <p class="card-text">选定区域 - {', '.join(selected_months)}</p>
        </div>
        """, unsafe_allow_html=True)

    # 总预测销售额
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <p class="card-header">预测销售额</p>
            <p class="card-value">{format_yuan(total_forecast_sales)}</p>
            <p class="card-text">选定区域 - {', '.join(selected_months)}</p>
        </div>
        """, unsafe_allow_html=True)

    # 全国准确率
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <p class="card-header">全国销售额准确率</p>
            <p class="card-value">{national_amount_accuracy:.2f}%</p>
            <p class="card-text">全国整体预测精度</p>
        </div>
        """, unsafe_allow_html=True)

    # 选定区域准确率
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <p class="card-header">选定区域销售额准确率</p>
            <p class="card-value">{selected_regions_amount_accuracy:.2f}%</p>
            <p class="card-text">选定区域预测精度</p>
        </div>
        """, unsafe_allow_html=True)

    # 准确率评估
    st.markdown('<div class="sub-header">预测准确率趋势</div>', unsafe_allow_html=True)

    # 准确率趋势图
    accuracy_trend = processed_data['national_accuracy']['monthly']

    # 处理可能的异常值
    accuracy_trend['销售额准确率'] = accuracy_trend['销售额准确率'].clip(0, 1)
    accuracy_trend['数量准确率'] = accuracy_trend['数量准确率'].clip(0, 1)

    # 创建折线图
    fig_accuracy_trend = px.line(
        accuracy_trend,
        x='所属年月',
        y=['销售额准确率', '数量准确率'],
        title="全国月度预测准确率趋势",
        labels={'value': '准确率', 'variable': '指标类型'},
        color_discrete_sequence=['blue', 'red']
    )

    # 转换为百分比格式
    fig_accuracy_trend.update_traces(
        y=accuracy_trend['销售额准确率'] * 100,
        selector=dict(name='销售额准确率')
    )

    fig_accuracy_trend.update_traces(
        y=accuracy_trend['数量准确率'] * 100,
        selector=dict(name='数量准确率')
    )

    # 更新Y轴刻度为百分比
    fig_accuracy_trend.update_layout(
        yaxis=dict(tickformat=".2f", title="准确率 (%)"),
        hovermode="x unified"
    )

    # 添加参考线
    fig_accuracy_trend.add_shape(
        type="line",
        x0=accuracy_trend['所属年月'].min(),
        x1=accuracy_trend['所属年月'].max(),
        y0=85,
        y1=85,
        line=dict(color="green", width=1, dash="dash")
    )

    # 添加悬停提示
    fig_accuracy_trend.update_layout(
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Arial"
        )
    )

    st.plotly_chart(fig_accuracy_trend, use_container_width=True)

    # 添加图表解释
    add_chart_explanation("""
    <b>图表解读：</b> 此图展示了全国范围内销售额预测和数量预测的月度准确率趋势。蓝线表示销售额准确率，红线表示数量准确率，绿色虚线代表理想准确率目标线(85%)。
    准确率的波动反映了预测系统的稳定性，上升趋势表明预测能力在提升，下降趋势则可能需要关注预测方法的调整。
    <b>行动建议：</b> 关注准确率低于85%的月份，分析其成因；研究准确率高的月份的预测方法可复制的经验；持续监控准确率趋势，建立预警机制以便及时调整预测策略。
    """)

    # 区域准确率比较
    st.markdown('<div class="sub-header">区域准确率比较</div>', unsafe_allow_html=True)

    # 筛选最新月份的区域准确率
    if selected_months:
        latest_selected_month = max(selected_months)
        region_accuracy_monthly = processed_data['regional_accuracy']['region_monthly']
        latest_region_accuracy = region_accuracy_monthly[
            region_accuracy_monthly['所属年月'] == latest_selected_month
            ].copy()

        # 数据处理
        latest_region_accuracy['销售额准确率'] = latest_region_accuracy['销售额准确率'].clip(0, 1) * 100
        latest_region_accuracy['数量准确率'] = latest_region_accuracy['数量准确率'].clip(0, 1) * 100

        # 柱状图 - 使用水平条形图
        fig_region_accuracy = px.bar(
            latest_region_accuracy,
            y='所属区域',
            x='销售额准确率',
            title=f"{latest_selected_month}各区域销售额预测准确率",
            color='所属区域',
            text_auto='.2f',
            orientation='h'
        )

        fig_region_accuracy.update_layout(
            xaxis=dict(title="准确率 (%)"),
            yaxis=dict(title="区域")
        )

        # 添加参考线
        fig_region_accuracy.add_shape(
            type="line",
            y0=-0.5,
            y1=len(latest_region_accuracy) - 0.5,
            x0=85,
            x1=85,
            line=dict(color="green", width=1, dash="dash")
        )

        # 添加悬停提示
        fig_region_accuracy.update_traces(
            hovertemplate='<b>%{y}</b><br>准确率: %{x:.2f}%<extra></extra>'
        )

        st.plotly_chart(fig_region_accuracy, use_container_width=True)

        # 生成动态解读
        explanation_text = "<b>图表解读：</b> 此图比较了" + latest_selected_month + "各区域销售额预测的准确率，绿色虚线代表理想准确率目标(85%)。"

        # 找出准确率最高和最低的区域
        if not latest_region_accuracy.empty:
            highest_region = latest_region_accuracy.loc[latest_region_accuracy['销售额准确率'].idxmax()]
            lowest_region = latest_region_accuracy.loc[latest_region_accuracy['销售额准确率'].idxmin()]

            explanation_text += f"<br><b>区域对比：</b> {highest_region['所属区域']}区域准确率最高，达{highest_region['销售额准确率']:.2f}%；"
            explanation_text += f"{lowest_region['所属区域']}区域准确率最低，为{lowest_region['销售额准确率']:.2f}%。"

            # 根据准确率生成建议
            if lowest_region['销售额准确率'] < 70:
                explanation_text += f"<br><b>行动建议：</b> {lowest_region['所属区域']}区域准确率显著偏低，建议安排专项培训并检查预测方法；"
                explanation_text += f"考虑让{highest_region['所属区域']}区域分享成功经验。"
            else:
                explanation_text += f"<br><b>行动建议：</b> 各区域准确率表现良好，建议持续监控并保持当前预测流程。"

        add_chart_explanation(explanation_text)

    # 预测与实际销售对比
    st.markdown('<div class="sub-header">预测与实际销售对比</div>', unsafe_allow_html=True)

    if selected_months:
        # 计算每个区域的销售额和预测额
        region_sales_comparison = filtered_monthly.groupby('所属区域').agg({
            '销售额': 'sum',
            '预测销售额': 'sum'
        }).reset_index()

        # 计算差异
        region_sales_comparison['差异额'] = region_sales_comparison['销售额'] - region_sales_comparison['预测销售额']
        region_sales_comparison['差异率'] = region_sales_comparison['差异额'] / region_sales_comparison['销售额'] * 100

        # 创建水平堆叠柱状图
        fig_sales_comparison = go.Figure()

        # 添加实际销售额柱
        fig_sales_comparison.add_trace(go.Bar(
            y=region_sales_comparison['所属区域'],
            x=region_sales_comparison['销售额'],
            name='实际销售额',
            marker_color='royalblue',
            orientation='h'
        ))

        # 添加预测销售额柱
        fig_sales_comparison.add_trace(go.Bar(
            y=region_sales_comparison['所属区域'],
            x=region_sales_comparison['预测销售额'],
            name='预测销售额',
            marker_color='lightcoral',
            orientation='h'
        ))

        # 添加差异率点
        fig_sales_comparison.add_trace(go.Scatter(
            y=region_sales_comparison['所属区域'],
            x=region_sales_comparison['差异率'],
            mode='markers+text',
            name='差异率 (%)',
            xaxis='x2',
            marker=dict(
                color=region_sales_comparison['差异率'].apply(lambda x: 'green' if x > 0 else 'red'),
                size=10
            ),
            text=[f"{x:.1f}%" for x in region_sales_comparison['差异率']],
            textposition='middle right'
        ))

        # 更新布局
        fig_sales_comparison.update_layout(
            title=f"{', '.join(selected_months)}期间各区域预测与实际销售对比",
            barmode='group',
            xaxis=dict(title="销售额 (元)"),
            xaxis2=dict(
                title="差异率 (%)",
                overlaying='x',
                side='top',
                range=[-100, 100]
            ),
            yaxis=dict(title="区域"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        # 添加悬停提示
        fig_sales_comparison.update_traces(
            hovertemplate='<b>%{y}</b><br>%{x:,.0f}元<extra>%{name}</extra>'
        )

        st.plotly_chart(fig_sales_comparison, use_container_width=True)

        # 生成动态解读
        explanation_text = f"<b>图表解读：</b> 此图展示了{', '.join(selected_months)}期间各区域的实际销售额(蓝色)与预测销售额(红色)对比，绿色点表示正差异率(低估)，红色点表示负差异率(高估)。"

        # 分析差异率
        high_diff_regions = region_sales_comparison[abs(region_sales_comparison['差异率']) > 15]
        if not high_diff_regions.empty:
            explanation_text += "<br><b>需关注区域：</b> "
            for _, row in high_diff_regions.iterrows():
                if row['差异率'] > 0:
                    explanation_text += f"{row['所属区域']}区域低估了{row['差异率']:.1f}%，"
                else:
                    explanation_text += f"{row['所属区域']}区域高估了{abs(row['差异率']):.1f}%，"

        explanation_text += f"<br><b>行动建议：</b> "

        # 添加具体建议
        if not high_diff_regions.empty:
            for _, row in high_diff_regions.iterrows():
                if row['差异率'] > 0:
                    adjust = abs(round(row['差异率']))
                    explanation_text += f"建议{row['所属区域']}区域提高预测量{adjust}%以满足实际需求；"
                else:
                    adjust = abs(round(row['差异率']))
                    explanation_text += f"建议{row['所属区域']}区域降低预测量{adjust}%以避免库存积压；"
        else:
            explanation_text += "各区域预测与实际销售较为匹配，建议维持当前预测方法。"

        add_chart_explanation(explanation_text)

with tabs[1]:  # 产品趋势标签页
    st.markdown('<div class="sub-header">产品销售趋势分析</div>', unsafe_allow_html=True)

    # 获取产品增长数据
    product_growth = processed_data['product_growth']

    if 'latest_growth' in product_growth and not product_growth['latest_growth'].empty:
        # 简要统计
        growth_stats = {
            '强劲增长': len(product_growth['latest_growth'][product_growth['latest_growth']['趋势'] == '强劲增长']),
            '增长': len(product_growth['latest_growth'][product_growth['latest_growth']['趋势'] == '增长']),
            '轻微下降': len(product_growth['latest_growth'][product_growth['latest_growth']['趋势'] == '轻微下降']),
            '显著下降': len(product_growth['latest_growth'][product_growth['latest_growth']['趋势'] == '显著下降'])
        }

        # 统计指标卡
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"""
            <div class="metric-card" style="border-left: 0.5rem solid #2E8B57;">
                <p class="card-header">强劲增长产品</p>
                <p class="card-value">{growth_stats['强劲增长']}</p>
                <p class="card-text">增长率 > 10%</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="metric-card" style="border-left: 0.5rem solid #4CAF50;">
                <p class="card-header">增长产品</p>
                <p class="card-value">{growth_stats['增长']}</p>
                <p class="card-text">增长率 0% ~ 10%</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="metric-card" style="border-left: 0.5rem solid #FFA500;">
                <p class="card-header">轻微下降产品</p>
                <p class="card-value">{growth_stats['轻微下降']}</p>
                <p class="card-text">增长率 -10% ~ 0%</p>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div class="metric-card" style="border-left: 0.5rem solid #F44336;">
                <p class="card-header">显著下降产品</p>
                <p class="card-value">{growth_stats['显著下降']}</p>
                <p class="card-text">增长率 < -10%</p>
            </div>
            """, unsafe_allow_html=True)

        # 产品增长/下降分析 - 使用水平条形图
        st.markdown('<div class="sub-header">产品三个月滚动同比增长率</div>', unsafe_allow_html=True)

        # 按增长率排序
        sorted_growth = product_growth['latest_growth'].sort_values('销量增长率', ascending=False).copy()

        # 添加产品名称
        sorted_growth['产品名称'] = sorted_growth['产品代码'].apply(
            lambda x: product_names_map.get(x, '') if product_names_map else ''
        )
        sorted_growth['产品显示'] = sorted_growth.apply(
            lambda row: f"{row['产品代码']} {row['产品名称']}", axis=1
        )


        # 创建水平条形图
        def plot_growth_chart(data, title):
            fig_growth = px.bar(
                data,
                y='产品显示',
                x='销量增长率',
                color='趋势',
                title=title,
                text_auto='.1f',
                orientation='h',
                color_discrete_map={
                    '强劲增长': '#2E8B57',
                    '增长': '#4CAF50',
                    '轻微下降': '#FFA500',
                    '显著下降': '#F44336'
                }
            )

            fig_growth.update_layout(
                yaxis_title="产品",
                xaxis_title="增长率 (%)"
            )

            # 添加参考线
            fig_growth.add_shape(
                type="line",
                y0=-0.5,
                y1=len(data) - 0.5,
                x0=0,
                x1=0,
                line=dict(color="black", width=1, dash="dash")
            )

            # 添加悬停提示
            fig_growth.update_traces(
                hovertemplate='<b>%{y}</b><br>增长率: %{x:.2f}%<br>备货建议: %{customdata}<extra></extra>',
                customdata=data['备货建议']
            )

            st.plotly_chart(fig_growth, use_container_width=True)


        # 使用分页器显示产品增长图表
        display_chart_paginator(
            sorted_growth,
            plot_growth_chart,
            10,
            "产品销量三个月滚动同比增长率",
            "growth"
        )

        # 添加图表解释
        growth_explanation = """
        <b>图表解读：</b> 此图展示了各产品三个月滚动销量的同比增长率，按增长率从高到低排序。颜色代表增长趋势：深绿色为强劲增长(>10%)，浅绿色为增长(0-10%)，橙色为轻微下降(0--10%)，红色为显著下降(<-10%)。
        """

        # 添加具体产品建议
        if not sorted_growth.empty:
            top_growth = sorted_growth.iloc[0]
            bottom_growth = sorted_growth.iloc[-1]

            growth_explanation += f"<br><b>产品分析：</b> "
            growth_explanation += f"{top_growth['产品显示']}增长最快({top_growth['销量增长率']:.1f}%)，"
            growth_explanation += f"{bottom_growth['产品显示']}下降最明显({bottom_growth['销量增长率']:.1f}%)。"

            growth_explanation += f"<br><b>行动建议：</b> "

            # 强劲增长产品
            strong_growth = sorted_growth[sorted_growth['趋势'] == '强劲增长']
            if not strong_growth.empty:
                top_product = strong_growth.iloc[0]
                growth_explanation += f"{top_product['产品显示']}增长迅速，建议提高{round(top_product['销量增长率'])}%的备货量；"

            # 显著下降产品
            strong_decline = sorted_growth[sorted_growth['趋势'] == '显著下降']
            if not strong_decline.empty:
                bottom_product = strong_decline.iloc[0]
                decline_pct = abs(round(bottom_product['销量增长率']))
                growth_explanation += f"{bottom_product['产品显示']}下降显著，建议降低{decline_pct}%的备货以避免库存积压。"

        add_chart_explanation(growth_explanation)

        # 备货建议列表 - 使用交互式图表替代
        st.markdown('<div class="sub-header">产品备货建议</div>', unsafe_allow_html=True)

        # 按产品代码排序，方便查找
        sorted_by_code = sorted_growth.sort_values('产品代码').copy()

        # 将数据分为三组：增加备货、维持备货和减少备货
        increase_inventory = sorted_by_code[sorted_by_code['备货建议'] == '增加备货'].copy()
        maintain_inventory = sorted_by_code[sorted_by_code['备货建议'] == '维持当前备货水平'].copy()
        decrease_inventory = sorted_by_code[sorted_by_code['备货建议'] == '减少备货'].copy()

        # 创建分组图表
        fig_inventory = go.Figure()

        # 增加备货组
        fig_inventory.add_trace(go.Bar(
            x=increase_inventory['产品显示'],
            y=increase_inventory['销量增长率'],
            name='增加备货',
            marker_color='#4CAF50',
            text=increase_inventory['销量增长率'].apply(lambda x: f"{x:.1f}%"),
            textposition='auto'
        ))

        # 维持备货组
        fig_inventory.add_trace(go.Bar(
            x=maintain_inventory['产品显示'],
            y=maintain_inventory['销量增长率'],
            name='维持当前备货水平',
            marker_color='#FFC107',
            text=maintain_inventory['销量增长率'].apply(lambda x: f"{x:.1f}%"),
            textposition='auto'
        ))

        # 减少备货组
        fig_inventory.add_trace(go.Bar(
            x=decrease_inventory['产品显示'],
            y=decrease_inventory['销量增长率'],
            name='减少备货',
            marker_color='#F44336',
            text=decrease_inventory['销量增长率'].apply(lambda x: f"{x:.1f}%"),
            textposition='auto'
        ))

        # 更新布局
        fig_inventory.update_layout(
            title="产品备货建议分组",
            xaxis_title="产品",
            yaxis_title="销量增长率 (%)",
            barmode='group',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        # 添加参考线
        fig_inventory.add_shape(
            type="line",
            x0=-0.5,
            x1=len(sorted_by_code) + 0.5,
            y0=0,
            y1=0,
            line=dict(color="black", width=1, dash="dash")
        )

        # 添加悬停提示
        fig_inventory.update_traces(
            hovertemplate='<b>%{x}</b><br>增长率: %{y:.2f}%<br>建议: %{name}<extra></extra>'
        )

        st.plotly_chart(fig_inventory, use_container_width=True)

        # 添加备货建议说明
        add_chart_explanation("""
        <b>备货建议说明：</b> 
        <ul>
        <li><b>增加备货</b>：针对增长率为正的产品，建议增加库存水平以满足上升的市场需求，避免缺货情况。具体增加比例应与产品增长率相当。</li>
        <li><b>维持备货</b>：针对增长率在-10%到0%之间的产品，建议保持当前库存水平，密切关注需求变化。</li>
        <li><b>减少备货</b>：针对增长率低于-10%的产品，建议减少库存水平以降低库存积压风险。减少比例应与下降率的绝对值相当。</li>
        </ul>
        <b>注意</b>：备货建议仅基于历史销售趋势，实际备货决策还应结合产品生命周期、促销计划、季节性因素等综合考虑。
        """)

        # 各区域产品增长情况
        st.markdown('<div class="sub-header">各区域产品增长分析</div>', unsafe_allow_html=True)

        # 选择区域
        selected_region_for_growth = st.selectbox(
            "选择区域查看产品增长情况",
            options=all_regions
        )

        # 提取该区域当月数据
        if selected_months:
            region_month_data = filtered_monthly[filtered_monthly['所属区域'] == selected_region_for_growth].copy()

            # 如果有数据，计算该区域的产品销售并与全国趋势比较
            if not region_month_data.empty:
                # 对区域产品按销售额排序
                region_products = region_month_data.sort_values('销售额', ascending=False)

                # 添加产品名称
                region_products['产品名称'] = region_products['产品代码'].apply(
                    lambda x: product_names_map.get(x, '') if product_names_map else ''
                )
                region_products['产品显示'] = region_products.apply(
                    lambda row: f"{row['产品代码']} {row['产品名称']}", axis=1
                )

                # 合并增长率数据
                region_products_with_growth = pd.merge(
                    region_products,
                    product_growth['latest_growth'][['产品代码', '销量增长率', '趋势', '备货建议']],
                    on='产品代码',
                    how='left'
                )

                # 产品增长散点图 - 交互增强版
                fig_region_growth = px.scatter(
                    region_products_with_growth,
                    x='销售额',
                    y='销量增长率',
                    color='趋势',
                    size='求和项:数量（箱）',
                    hover_name='产品显示',
                    title=f"{selected_region_for_growth}区域产品销售额与增长率",
                    color_discrete_map={
                        '强劲增长': '#2E8B57',
                        '增长': '#4CAF50',
                        '轻微下降': '#FFA500',
                        '显著下降': '#F44336'
                    }
                )

                fig_region_growth.update_layout(
                    xaxis_title="销售额 (元)",
                    yaxis_title="增长率 (%)",
                    xaxis=dict(tickformat=",.0f"),
                    yaxis=dict(zeroline=True)
                )

                # 添加参考线
                fig_region_growth.add_shape(
                    type="line",
                    x0=region_products_with_growth['销售额'].min(),
                    x1=region_products_with_growth['销售额'].max(),
                    y0=0,
                    y1=0,
                    line=dict(color="black", width=1, dash="dash")
                )

                # 添加悬停提示
                fig_region_growth.update_traces(
                    hovertemplate='<b>%{hovertext}</b><br>销售额: %{x:,.0f}元<br>增长率: %{y:.2f}%<br>销量: %{marker.size:,.0f}箱<br>趋势: %{marker.color}<extra></extra>'
                )

                st.plotly_chart(fig_region_growth, use_container_width=True)

                # 生成动态图表解读
                region_explanation = f"<b>图表解读：</b> 此散点图展示了{selected_region_for_growth}区域各产品的销售额(横轴)与全国销量增长率(纵轴)关系，气泡大小表示销售数量，颜色代表增长趋势。"

                # 添加具体产品分析
                if not region_products_with_growth.empty:
                    # 识别关键产品
                    top_sales = region_products_with_growth.nlargest(1, '销售额').iloc[0]
                    top_growth = region_products_with_growth[region_products_with_growth['销量增长率'] > 0].nlargest(1,
                                                                                                                     '销售额')
                    top_decline = region_products_with_growth[region_products_with_growth['销量增长率'] < 0].nlargest(1,
                                                                                                                      '销售额')

                    region_explanation += "<br><b>产品分析：</b> "
                    region_explanation += f"{top_sales['产品显示']}是该区域销售额最高的产品({format_yuan(top_sales['销售额'])})，"

                    if not top_growth.empty:
                        product = top_growth.iloc[0]
                        region_explanation += f"{product['产品显示']}是增长型高销售额产品(增长率{product['销量增长率']:.1f}%)，"

                    if not top_decline.empty:
                        product = top_decline.iloc[0]
                        region_explanation += f"{product['产品显示']}是下降型高销售额产品(增长率{product['销量增长率']:.1f}%)。"

                    # 生成预测建议
                    region_explanation += "<br><b>预测建议：</b> "

                    if not top_growth.empty:
                        product = top_growth.iloc[0]
                        adjust_pct = round(product['销量增长率'])
                        region_explanation += f"建议{selected_region_for_growth}区域对{product['产品显示']}提高{adjust_pct}%的预测量；"

                    if not top_decline.empty:
                        product = top_decline.iloc[0]
                        adjust_pct = abs(round(product['销量增长率']))
                        region_explanation += f"对{product['产品显示']}降低{adjust_pct}%的预测量以避免库存积压。"

                add_chart_explanation(region_explanation)
    else:
        st.warning("没有足够的历史数据来计算产品增长率。需要至少两年的销售数据才能计算同比增长。")

with tabs[2]:  # 重点SKU分析标签页
    st.markdown('<div class="sub-header">销售额占比80%重点SKU分析</div>', unsafe_allow_html=True)

    # 全国重点SKU分析
    st.markdown('<div class="sub-header">全国销售额占比80%SKU列表</div>', unsafe_allow_html=True)

    # 展示全国重点SKU
    national_top_skus = processed_data['national_top_skus'].copy()

    if not national_top_skus.empty:
        # 格式化准确率为百分比
        national_top_skus['数量准确率'] = national_top_skus['数量准确率'] * 100
        national_top_skus['销售额准确率'] = national_top_skus['销售额准确率'] * 100

        # 添加产品名称
        national_top_skus['产品名称'] = national_top_skus['产品代码'].apply(
            lambda x: product_names_map.get(x, '') if product_names_map else ''
        )
        national_top_skus['产品显示'] = national_top_skus.apply(
            lambda row: f"{row['产品代码']} {row['产品名称']}", axis=1
        )

        # 创建水平条形图
        fig_national_top = go.Figure()

        # 添加销售额条
        fig_national_top.add_trace(go.Bar(
            y=national_top_skus['产品显示'],
            x=national_top_skus['销售额'],
            name='销售额',
            marker=dict(
                color=national_top_skus['销售额准确率'],
                colorscale='RdYlGn',
                cmin=0,
                cmax=100,
                colorbar=dict(
                    title='准确率 (%)',
                    x=1.05
                )
            ),
            orientation='h'
        ))

        # 添加准确率标记
        fig_national_top.add_trace(go.Scatter(
            y=national_top_skus['产品显示'],
            x=[national_top_skus['销售额'].max() * 0.05] * len(national_top_skus),  # 放在最左侧
            mode='text',
            text=[f"{x:.0f}%" for x in national_top_skus['销售额准确率']],
            textposition="middle right",
            name='准确率'
        ))

        # 更新布局
        fig_national_top.update_layout(
            title="全国销售额占比80%的SKU及其准确率",
            xaxis=dict(title="销售额 (元)", tickformat=",.0f"),
            yaxis=dict(title="产品"),
            showlegend=False
        )

        # 添加悬停提示
        fig_national_top.update_traces(
            hovertemplate='<b>%{y}</b><br>销售额: %{x:,.0f}元<br>准确率: %{marker.color:.1f}%<br>累计占比: %{customdata:.2f}%<extra></extra>',
            customdata=national_top_skus['累计占比'],
            selector=dict(type='bar')
        )

        # 突出显示准确率低的产品
        low_accuracy_products = national_top_skus[national_top_skus['销售额准确率'] < 70]
        if not low_accuracy_products.empty:
            for product in low_accuracy_products['产品显示']:
                fig_national_top.add_shape(
                    type="rect",
                    y0=list(national_top_skus['产品显示']).index(product) - 0.45,
                    y1=list(national_top_skus['产品显示']).index(product) + 0.45,
                    x0=0,
                    x1=national_top_skus['销售额'].max() * 1.05,
                    line=dict(color="#F44336", width=2),
                    fillcolor="rgba(244, 67, 54, 0.1)"
                )

        st.plotly_chart(fig_national_top, use_container_width=True)

        # 生成动态解读
        national_explanation = """
        <b>图表解读：</b> 此图展示了销售额累计占比达到80%的重点SKU及其准确率，条形长度表示销售额，颜色深浅表示准确率(深绿色表示高准确率，红色表示低准确率)。
        框线标记的产品准确率低于70%，需要特别关注。
        """

        # 添加具体产品建议
        if not national_top_skus.empty:
            top_product = national_top_skus.iloc[0]
            lowest_accuracy_product = national_top_skus.loc[national_top_skus['销售额准确率'].idxmin()]

            national_explanation += f"<br><b>产品分析：</b> "
            national_explanation += f"{top_product['产品显示']}是销售额最高的产品({format_yuan(top_product['销售额'])})，累计占比{top_product['累计占比']:.2f}%，准确率{top_product['销售额准确率']:.1f}%；"

            if lowest_accuracy_product['销售额准确率'] < 80:
                national_explanation += f"{lowest_accuracy_product['产品显示']}准确率最低，仅为{lowest_accuracy_product['销售额准确率']:.1f}%。"

            # 生成预测建议
            national_explanation += "<br><b>行动建议：</b> "

            low_accuracy = national_top_skus[national_top_skus['销售额准确率'] < 70]
            if not low_accuracy.empty:
                if len(low_accuracy) <= 3:
                    for _, product in low_accuracy.iterrows():
                        national_explanation += f"重点关注{product['产品显示']}的预测准确性，目前准确率仅为{product['销售额准确率']:.1f}%；"
                else:
                    national_explanation += f"共有{len(low_accuracy)}个重点SKU准确率低于70%，需安排专项预测改进计划；"
            else:
                national_explanation += "重点SKU预测准确率良好，建议保持当前预测方法；"

            # 添加备货建议
            product_growth_data = product_growth.get('latest_growth', pd.DataFrame())
            if not product_growth_data.empty:
                top_sku_growth = pd.merge(
                    national_top_skus,
                    product_growth_data[['产品代码', '销量增长率', '趋势']],
                    on='产品代码',
                    how='left'
                )

                growth_products = top_sku_growth[top_sku_growth['销量增长率'] > 10]
                if not growth_products.empty:
                    top_growth = growth_products.iloc[0]
                    national_explanation += f"增加{top_growth['产品显示']}的备货量，其增长率达{top_growth['销量增长率']:.1f}%。"

        add_chart_explanation(national_explanation)
    else:
        st.warning("没有足够的数据来计算全国重点SKU。")

    # 各区域重点SKU分析
    st.markdown('<div class="sub-header">各区域销售额占比80%SKU分析</div>', unsafe_allow_html=True)

    # 选择区域
    selected_region_for_sku = st.selectbox(
        "选择区域查看重点SKU",
        options=all_regions,
        key="region_select_sku"
    )

    # 各区域重点SKU
    regional_top_skus = processed_data['regional_top_skus']

    if selected_region_for_sku in regional_top_skus and not regional_top_skus[selected_region_for_sku].empty:
        region_top = regional_top_skus[selected_region_for_sku].copy()

        # 格式化准确率为百分比
        region_top['数量准确率'] = region_top['数量准确率'] * 100
        region_top['销售额准确率'] = region_top['销售额准确率'] * 100

        # 添加产品名称
        region_top['产品名称'] = region_top['产品代码'].apply(
            lambda x: product_names_map.get(x, '') if product_names_map else ''
        )
        region_top['产品显示'] = region_top.apply(
            lambda row: f"{row['产品代码']} {row['产品名称']}", axis=1
        )

        # 创建水平条形图
        fig_region_top = go.Figure()

        # 添加销售额条
        fig_region_top.add_trace(go.Bar(
            y=region_top['产品显示'],
            x=region_top['销售额'],
            name='销售额',
            marker=dict(
                color=region_top['销售额准确率'],
                colorscale='RdYlGn',
                cmin=0,
                cmax=100,
                colorbar=dict(
                    title='准确率 (%)',
                    x=1.05
                )
            ),
            orientation='h'
        ))

        # 添加准确率标记
        fig_region_top.add_trace(go.Scatter(
            y=region_top['产品显示'],
            x=[region_top['销售额'].max() * 0.05] * len(region_top),  # 放在最左侧
            mode='text',
            text=[f"{x:.0f}%" for x in region_top['销售额准确率']],
            textposition="middle right",
            name='准确率'
        ))

        # 更新布局
        fig_region_top.update_layout(
            title=f"{selected_region_for_sku}区域销售额占比80%的SKU及其准确率",
            xaxis=dict(title="销售额 (元)", tickformat=",.0f"),
            yaxis=dict(title="产品"),
            showlegend=False
        )

        # 添加悬停提示
        fig_region_top.update_traces(
            hovertemplate='<b>%{y}</b><br>销售额: %{x:,.0f}元<br>准确率: %{marker.color:.1f}%<br>累计占比: %{customdata:.2f}%<extra></extra>',
            customdata=region_top['累计占比'],
            selector=dict(type='bar')
        )

        # 突出显示准确率低的产品
        low_accuracy_products = region_top[region_top['销售额准确率'] < 70]
        if not low_accuracy_products.empty:
            for product in low_accuracy_products['产品显示']:
                fig_region_top.add_shape(
                    type="rect",
                    y0=list(region_top['产品显示']).index(product) - 0.45,
                    y1=list(region_top['产品显示']).index(product) + 0.45,
                    x0=0,
                    x1=region_top['销售额'].max() * 1.05,
                    line=dict(color="#F44336", width=2),
                    fillcolor="rgba(244, 67, 54, 0.1)"
                )

        st.plotly_chart(fig_region_top, use_container_width=True)

        # 生成动态解读
        region_explanation = f"""
        <b>图表解读：</b> 此图展示了{selected_region_for_sku}区域销售额累计占比达到80%的重点SKU及其准确率，条形长度表示销售额，颜色深浅表示准确率。框线标记的产品准确率低于70%，需要特别关注。
        """

        # 添加具体产品建议
        if not region_top.empty:
            top_product = region_top.iloc[0]

            region_explanation += f"<br><b>产品分析：</b> "
            region_explanation += f"{top_product['产品显示']}是{selected_region_for_sku}区域销售额最高的产品({format_yuan(top_product['销售额'])})，"

            if len(region_top) > 1:
                second_product = region_top.iloc[1]
                region_explanation += f"其次是{second_product['产品显示']}({format_yuan(second_product['销售额'])})。"

            # 检查准确率
            low_accuracy = region_top[region_top['销售额准确率'] < 70]
            if not low_accuracy.empty:
                lowest = low_accuracy.iloc[0]
                region_explanation += f"{lowest['产品显示']}准确率最低，仅为{lowest['销售额准确率']:.1f}%。"

            # 生成预测建议
            region_explanation += "<br><b>行动建议：</b> "

            if not low_accuracy.empty:
                if len(low_accuracy) <= 2:
                    for _, product in low_accuracy.iterrows():
                        region_explanation += f"{selected_region_for_sku}区域应重点关注{product['产品显示']}的预测准确性；"
                else:
                    region_explanation += f"{selected_region_for_sku}区域有{len(low_accuracy)}个重点SKU准确率低于70%，需安排区域预测培训；"
            else:
                region_explanation += f"{selected_region_for_sku}区域重点SKU预测准确率良好；"

            # 添加备货建议
            product_growth_data = product_growth.get('latest_growth', pd.DataFrame())
            if not product_growth_data.empty:
                top_sku_growth = pd.merge(
                    region_top,
                    product_growth_data[['产品代码', '销量增长率', '趋势']],
                    on='产品代码',
                    how='left'
                )

                growth_products = top_sku_growth[top_sku_growth['销量增长率'] > 0]
                decline_products = top_sku_growth[top_sku_growth['销量增长率'] < -10]

                if not growth_products.empty:
                    top_growth = growth_products.iloc[0]
                    region_explanation += f"建议增加{top_growth['产品显示']}的备货量{max(5, round(top_growth['销量增长率']))}%；"

                if not decline_products.empty:
                    top_decline = decline_products.iloc[0]
                    adjust = abs(round(top_decline['销量增长率']))
                    region_explanation += f"建议减少{top_decline['产品显示']}的备货量{adjust}%以避免库存积压。"

        add_chart_explanation(region_explanation)

        # 与全国重点SKU对比
        st.markdown('<div class="sub-header">区域与全国重点SKU对比</div>', unsafe_allow_html=True)

        # 获取区域和全国的SKU列表
        region_skus = set(region_top['产品代码'])
        national_skus = set(national_top_skus['产品代码'])

        # 计算共有和特有SKU
        common_skus = region_skus.intersection(national_skus)
        region_unique_skus = region_skus - national_skus
        national_unique_skus = national_skus - region_skus

        # 创建饼图
        fig_sku_comparison = go.Figure()

        # 添加区域特有SKU占比
        fig_sku_comparison.add_trace(go.Pie(
            labels=['区域与全国共有SKU', '区域特有SKU', '全国重点但区域非重点SKU'],
            values=[len(common_skus), len(region_unique_skus), len(national_unique_skus)],
            hole=.3,
            marker_colors=['#4CAF50', '#2196F3', '#F44336'],
            textinfo='label+percent'
        ))

        fig_sku_comparison.update_layout(
            title=f"{selected_region_for_sku}区域与全国重点SKU对比"
        )

        # 添加悬停提示
        fig_sku_comparison.update_traces(
            hovertemplate='<b>%{label}</b><br>SKU数量: %{value}<br>占比: %{percent}<extra></extra>'
        )

        st.plotly_chart(fig_sku_comparison, use_container_width=True)

        # 创建交互式SKU详情表格
        st.markdown("### 重点SKU详情")

        # 创建选项卡
        sku_tabs = st.tabs(["共有SKU", "区域特有SKU", "全国重点非区域SKU"])


        # 用于展示SKU列表的函数 - 使用交互式图表
        def display_sku_list(sku_codes, title, color):
            if product_names_map:
                sku_names = {code: product_names_map.get(code, '') for code in sku_codes}
                sku_display = [f"{code} {sku_names[code]}" for code in sku_codes]
            else:
                sku_display = list(sku_codes)

            # 创建水平条形图
            if sku_display:
                fig = go.Figure()

                # 添加条形
                fig.add_trace(go.Bar(
                    y=sku_display,
                    x=[1] * len(sku_display),  # 统一长度
                    orientation='h',
                    marker_color=color,
                    showlegend=False
                ))

                # 更新布局
                fig.update_layout(
                    title=title,
                    xaxis=dict(
                        visible=False,  # 隐藏X轴
                        showticklabels=False
                    ),
                    yaxis=dict(title="产品"),
                    height=max(300, 50 * len(sku_display))  # 动态高度
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(f"没有{title}")


        # 展示三种SKU列表
        with sku_tabs[0]:
            display_sku_list(common_skus, "区域与全国共有的重点SKU", '#4CAF50')
            if common_skus:
                st.markdown("""
                <b>共有SKU说明：</b> 这些产品同时是区域和全国的重点产品，这表明它们具有普遍的重要性。这些产品应该得到最高优先级的库存管理和需求预测。
                """, unsafe_allow_html=True)

        with sku_tabs[1]:
            display_sku_list(region_unique_skus, "区域特有重点SKU", '#2196F3')
            if region_unique_skus:
                st.markdown(f"""
                <b>区域特有SKU说明：</b> 这些产品在{selected_region_for_sku}区域特别重要，但在全国范围内不是重点。这可能反映了区域市场的特殊偏好或竞争环境。
                建议区域销售团队为这些产品制定针对性的销售策略和预测方法。
                """, unsafe_allow_html=True)

        with sku_tabs[2]:
            display_sku_list(national_unique_skus, "全国重点但区域非重点SKU", '#F44336')
            if national_unique_skus:
                st.markdown(f"""
                <b>全国重点非区域SKU说明：</b> 这些产品在全国范围内是重点，但在{selected_region_for_sku}区域尚未成为主力产品。这可能表明区域市场有开发潜力，
                建议评估这些产品在区域的市场潜力，并可能调整销售策略以增加这些产品在该区域的销售。
                """, unsafe_allow_html=True)
    else:
        st.warning(f"没有足够的数据来计算{selected_region_for_sku}区域的重点SKU。")

with tabs[3]:  # 预测差异分析标签页
    st.markdown('<div class="sub-header">预测与实际销售差异分析</div>', unsafe_allow_html=True)

    # 选择区域和分析维度
    col1, col2 = st.columns(2)

    with col1:
        selected_region_for_diff = st.selectbox(
            "选择区域",
            options=['全国'] + all_regions,
            key="region_select_diff"
        )

    with col2:
        analysis_dimension = st.selectbox(
            "选择分析维度",
            options=['产品', '销售员'],
            key="dimension_select"
        )

    # 准备数据
    if selected_region_for_diff == '全国':
        # 全国数据，按选定维度汇总
        if analysis_dimension == '产品':
            diff_data = filtered_monthly.groupby('产品代码').agg({
                '销售额': 'sum',
                '预测销售额': 'sum',
                '销售额差异': 'sum',
                '销售额差异率': 'mean',
                '销售额准确率': 'mean'
            }).reset_index()
        else:  # 销售员维度
            diff_data = filtered_salesperson.groupby('销售员').agg({
                '销售额': 'sum',
                '预测销售额': 'sum',
                '销售额差异': 'sum',
                '销售额差异率': 'mean',
                '销售额准确率': 'mean'
            }).reset_index()
    else:
        # 选定区域数据，按选定维度汇总
        region_filtered = filtered_monthly[filtered_monthly['所属区域'] == selected_region_for_diff]
        region_filtered_salesperson = filtered_salesperson[filtered_salesperson['所属区域'] == selected_region_for_diff]

        if analysis_dimension == '产品':
            diff_data = region_filtered.groupby('产品代码').agg({
                '销售额': 'sum',
                '预测销售额': 'sum',
                '销售额差异': 'sum',
                '销售额差异率': 'mean',
                '销售额准确率': 'mean'
            }).reset_index()
        else:  # 销售员维度
            diff_data = region_filtered_salesperson.groupby('销售员').agg({
                '销售额': 'sum',
                '预测销售额': 'sum',
                '销售额差异': 'sum',
                '销售额差异率': 'mean',
                '销售额准确率': 'mean'
            }).reset_index()

    # 格式化准确率为百分比
    diff_data['销售额准确率'] = diff_data['销售额准确率'] * 100

    # 如果是产品维度，添加产品名称
    if analysis_dimension == '产品' and product_names_map:
        diff_data['产品名称'] = diff_data['产品代码'].apply(lambda x: product_names_map.get(x, ''))
        diff_data['产品显示'] = diff_data.apply(lambda row: f"{row['产品代码']} {row['产品名称']}", axis=1)
        dimension_column = '产品显示'
    else:
        dimension_column = analysis_dimension == '产品' and '产品代码' or '销售员'

    # 差异分析图表
    st.markdown(f'<div class="sub-header">{selected_region_for_diff} - {analysis_dimension}预测差异分析</div>',
                unsafe_allow_html=True)

    if not diff_data.empty:
        # 计算总销售额和总预测额
        total_actual = diff_data['销售额'].sum()
        total_forecast = diff_data['预测销售额'].sum()

        # 计算每个项目的占比
        diff_data['实际占比'] = diff_data['销售额'] / total_actual * 100 if total_actual > 0 else 0
        diff_data['预测占比'] = diff_data['预测销售额'] / total_forecast * 100 if total_forecast > 0 else 0
        diff_data['占比差异'] = diff_data['实际占比'] - diff_data['预测占比']

        # 按销售额降序排序
        diff_data = diff_data.sort_values('销售额', ascending=False)

        # 按差异率绝对值排序，取前15个显示
        top_diff_items = diff_data.nlargest(15, '销售额')

        # 创建水平堆叠条形图
        fig_diff = go.Figure()

        # 添加实际销售额柱
        fig_diff.add_trace(go.Bar(
            y=top_diff_items[dimension_column],
            x=top_diff_items['销售额'],
            name='实际销售额',
            marker_color='royalblue',
            orientation='h'
        ))

        # 添加预测销售额柱
        fig_diff.add_trace(go.Bar(
            y=top_diff_items[dimension_column],
            x=top_diff_items['预测销售额'],
            name='预测销售额',
            marker_color='lightcoral',
            orientation='h'
        ))

        # 添加差异率点
        fig_diff.add_trace(go.Scatter(
            y=top_diff_items[dimension_column],
            x=[top_diff_items['销售额'].max() * 1.05] * len(top_diff_items),  # 放在右侧
            mode='markers+text',
            marker=dict(
                color=top_diff_items['销售额差异率'],
                colorscale='RdBu_r',  # 红蓝比例尺
                cmin=-50,
                cmax=50,
                size=15,
                showscale=True,
                colorbar=dict(
                    title="差异率 (%)",
                    x=1.1
                )
            ),
            text=[f"{x:.1f}%" for x in top_diff_items['销售额差异率']],
            textposition='middle right',
            name='差异率 (%)'
        ))

        # 更新布局
        fig_diff.update_layout(
            title=f"{selected_region_for_diff} {', '.join(selected_months)} - {analysis_dimension}预测与实际销售对比 (销售额前15)",
            xaxis=dict(title="销售额 (元)", tickformat=",.0f"),
            yaxis=dict(title=analysis_dimension),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            barmode='group',
            height=600  # 增加高度以容纳所有条形
        )

        # 添加悬停提示
        fig_diff.update_traces(
            hovertemplate='<b>%{y}</b><br>%{x:,.0f}元<extra>%{name}</extra>',
            selector=dict(type='bar')
        )

        fig_diff.update_traces(
            hovertemplate='<b>%{y}</b><br>差异率: %{marker.color:.2f}%<br>准确率: %{customdata:.1f}%<extra></extra>',
            customdata=top_diff_items['销售额准确率'],
            selector=dict(mode='markers+text')
        )

        st.plotly_chart(fig_diff, use_container_width=True)

        # 生成动态解读
        diff_explanation = f"""
        <b>图表解读：</b> 此图展示了{selected_region_for_diff}区域各{analysis_dimension}的实际销售额(蓝色)与预测销售额(红色)对比，点的颜色表示差异率(蓝色表示低估，红色表示高估)。
        差异率越高(绝对值越大)，表明预测偏离实际的程度越大。
        """

        # 添加具体分析
        if not top_diff_items.empty:
            # 找出差异最大的项目
            highest_diff = top_diff_items.loc[top_diff_items['销售额差异率'].abs().idxmax()]
            top_sales = top_diff_items.iloc[0]

            diff_explanation += f"<br><b>{analysis_dimension}分析：</b> "

            if analysis_dimension == '产品':
                diff_explanation += f"{highest_diff[dimension_column]}差异率最高，达{highest_diff['销售额差异率']:.1f}%，"
                if '产品名称' in top_sales:
                    diff_explanation += f"{top_sales[dimension_column]}销售额最高({format_yuan(top_sales['销售额'])})。"
                else:
                    diff_explanation += f"{top_sales[dimension_column]}销售额最高({format_yuan(top_sales['销售额'])})。"
            else:
                diff_explanation += f"{highest_diff['销售员']}的差异率最高，达{highest_diff['销售额差异率']:.1f}%，"
                diff_explanation += f"{top_sales['销售员']}的销售额最高({format_yuan(top_sales['销售额'])})。"

                # 生成预测建议
                diff_explanation += "<br><b>行动建议：</b> "

                # 找出高差异项目
                high_diff_items = top_diff_items[abs(top_diff_items['销售额差异率']) > 15]
                if not high_diff_items.empty:
                    for _, item in high_diff_items.head(2).iterrows():  # 只提取前两个以避免太长
                        if item['销售额差异率'] > 0:
                            adjust_pct = abs(round(item['销售额差异率']))
                            diff_explanation += f"建议提高{item[dimension_column]}的预测量{adjust_pct}%；"
                        else:
                            adjust_pct = abs(round(item['销售额差异率']))
                            diff_explanation += f"建议降低{item[dimension_column]}的预测量{adjust_pct}%；"
                else:
                    diff_explanation += "各{analysis_dimension}预测与实际销售较为匹配，建议保持当前预测方法。"

            add_chart_explanation(diff_explanation)

            # 占比差异分析
            st.markdown(
                f'<div class="sub-header">{selected_region_for_diff} - {analysis_dimension}销售占比差异分析</div>',
                unsafe_allow_html=True)

            # 计算平均绝对占比差异
            mean_abs_diff = diff_data['占比差异'].abs().mean()

            # 按占比差异绝对值降序排序
            diff_data_sorted = diff_data.sort_values(by='占比差异', key=abs, ascending=False)

            # 创建占比差异散点图
            top_items = diff_data_sorted.head(20)  # 只显示前20个以避免过于拥挤

            fig_share_diff = px.scatter(
                top_items,
                x='实际占比',
                y='预测占比',
                size='销售额',
                color='占比差异',
                hover_name=dimension_column,
                labels={
                    '实际占比': '实际销售占比 (%)',
                    '预测占比': '预测销售占比 (%)',
                    '占比差异': '占比差异 (%)'
                },
                title=f"{selected_region_for_diff} - {analysis_dimension}销售占比差异分析",
                color_continuous_scale='RdBu_r',
                range_color=[-max(abs(top_items['占比差异'].min()), abs(top_items['占比差异'].max())),
                             max(abs(top_items['占比差异'].min()), abs(top_items['占比差异'].max()))]
            )

            # 添加参考线 (y=x)
            max_value = max(top_items['实际占比'].max(), top_items['预测占比'].max()) * 1.1
            fig_share_diff.add_shape(
                type="line",
                x0=0,
                x1=max_value,
                y0=0,
                y1=max_value,
                line=dict(color="black", width=1, dash="dash")
            )

            # 添加文本标签
            for i, row in top_items.head(5).iterrows():  # 只为前5个添加标签
                fig_share_diff.add_annotation(
                    x=row['实际占比'],
                    y=row['预测占比'],
                    text=row[dimension_column],
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1,
                    arrowwidth=1,
                    arrowcolor='gray'
                )

            fig_share_diff.update_layout(
                xaxis=dict(title="实际销售占比 (%)", tickformat=".1f"),
                yaxis=dict(title="预测销售占比 (%)", tickformat=".1f")
            )

            # 添加悬停提示
            fig_share_diff.update_traces(
                hovertemplate='<b>%{hovertext}</b><br>实际占比: %{x:.2f}%<br>预测占比: %{y:.2f}%<br>差异: %{marker.color:.2f}%<br>销售额: %{marker.size:,.0f}元<extra></extra>'
            )

            st.plotly_chart(fig_share_diff, use_container_width=True)

            # 生成动态解读
            scatter_explanation = f"""
                        <b>图表解读：</b> 此散点图分析了{selected_region_for_diff}{analysis_dimension}的销售占比差异，横轴是实际销售占比，纵轴是预测销售占比，气泡大小表示销售额，颜色表示占比差异(蓝色表示低估，红色表示高估)。
                        位于对角线上的点表示预测占比与实际占比一致；偏离对角线的点表示预测占比与实际占比存在显著差异。占比差异的绝对值平均为{mean_abs_diff:.2f}%。
                        """

            # 添加具体分析
            if not top_items.empty:
                # 找出差异最大的项目
                highest_diff = top_items.iloc[0]

                scatter_explanation += f"<br><b>占比分析：</b> "

                # 正差异(低估)
                positive_diff = top_items[top_items['占比差异'] > 0].head(1)
                if not positive_diff.empty:
                    item = positive_diff.iloc[0]
                    scatter_explanation += f"{item[dimension_column]}的实际占比({item['实际占比']:.2f}%)显著高于预测占比({item['预测占比']:.2f}%)，表明被低估了{item['占比差异']:.2f}%；"

                # 负差异(高估)
                negative_diff = top_items[top_items['占比差异'] < 0].head(1)
                if not negative_diff.empty:
                    item = negative_diff.iloc[0]
                    scatter_explanation += f"{item[dimension_column]}的预测占比({item['预测占比']:.2f}%)显著高于实际占比({item['实际占比']:.2f}%)，表明被高估了{abs(item['占比差异']):.2f}%。"

                # 生成建议
                scatter_explanation += f"<br><b>行动建议：</b> "

                # 找出占比差异明显的项目
                high_diff_items = top_items[abs(top_items['占比差异']) > 5]
                if not high_diff_items.empty:
                    scatter_explanation += f"调整预测结构，"
                    for _, item in high_diff_items.head(2).iterrows():  # 只提取前两个以避免太长
                        if item['占比差异'] > 0:
                            scatter_explanation += f"提高{item[dimension_column]}在总预测中的比例；"
                        else:
                            scatter_explanation += f"降低{item[dimension_column]}在总预测中的比例；"

                    scatter_explanation += "即使总预测量准确，产品结构偏差也会导致库存错配。"
                else:
                    scatter_explanation += "产品结构预测较为合理，建议保持当前预测方法。"

            add_chart_explanation(scatter_explanation)

            # 占比差异排名 - 使用水平条形图
            st.markdown(f'<div class="sub-header">{selected_region_for_diff} - {analysis_dimension}占比差异排名</div>',
                        unsafe_allow_html=True)

            # 按占比差异绝对值降序排序
            diff_data_abs_sorted = diff_data.sort_values(by='占比差异', key=abs, ascending=False)
            top_diff_abs = diff_data_abs_sorted.head(15)  # 只显示前15个

            # 创建水平条形图
            fig_share_diff_ranking = go.Figure()

            # 添加占比差异条
            fig_share_diff_ranking.add_trace(go.Bar(
                y=top_diff_abs[dimension_column],
                x=top_diff_abs['占比差异'],
                marker_color=np.where(top_diff_abs['占比差异'] >= 0, 'indianred', 'royalblue'),
                text=[f"{x:+.1f}%" for x in top_diff_abs['占比差异']],
                textposition='outside',
                orientation='h'
            ))

            # 更新布局
            fig_share_diff_ranking.update_layout(
                title=f"{selected_region_for_diff} - {analysis_dimension}销售占比差异排名",
                yaxis_title=analysis_dimension,
                xaxis_title="占比差异 (%)",
                xaxis=dict(zeroline=True)
            )

            # 添加参考线
            fig_share_diff_ranking.add_shape(
                type="line",
                y0=-0.5,
                y1=len(top_diff_abs) - 0.5,
                x0=0,
                x1=0,
                line=dict(color="black", width=1, dash="dash")
            )

            # 添加悬停提示
            fig_share_diff_ranking.update_traces(
                hovertemplate='<b>%{y}</b><br>占比差异: %{x:+.2f}%<br>实际占比: %{customdata[0]:.2f}%<br>预测占比: %{customdata[1]:.2f}%<extra></extra>',
                customdata=top_diff_abs[['实际占比', '预测占比']].values
            )

            st.plotly_chart(fig_share_diff_ranking, use_container_width=True)

            # 生成动态解读
            ranking_explanation = f"""
                        <b>图表解读：</b> 此图展示了{selected_region_for_diff}各{analysis_dimension}销售占比差异的排名，红色表示实际占比高于预测(低估)，蓝色表示实际占比低于预测(高估)。
                        占比差异大的{analysis_dimension}可能导致库存错配问题，即使总体预测准确也可能出现某些产品积压而其他产品缺货的情况。
                        """

            # 添加具体分析
            if not top_diff_abs.empty:
                # 找出差异最大的几个项目
                top_items = top_diff_abs.head(3)

                ranking_explanation += f"<br><b>关键{analysis_dimension}：</b> "

                for i, item in enumerate(top_items.itertuples()):
                    if i < 2:  # 只为前两个生成详细描述
                        name = getattr(item, dimension_column)
                        diff = getattr(item, '占比差异')

                        if diff > 0:
                            ranking_explanation += f"{name}被低估了{diff:.2f}%，实际占比{getattr(item, '实际占比'):.2f}%而预测仅为{getattr(item, '预测占比'):.2f}%；"
                        else:
                            ranking_explanation += f"{name}被高估了{abs(diff):.2f}%，预测占比{getattr(item, '预测占比'):.2f}%而实际仅为{getattr(item, '实际占比'):.2f}%；"

                # 生成建议
                ranking_explanation += f"<br><b>行动建议：</b> "

                # 根据占比差异生成针对性建议
                if abs(top_diff_abs['占比差异']).max() > 10:
                    ranking_explanation += f"对于占比差异超过±5%的{analysis_dimension}，重点关注并调整产品结构预测；"
                    ranking_explanation += f"建议在销售预测会议上，专门讨论产品结构占比，而非仅关注总量预测。"
                else:
                    ranking_explanation += f"各{analysis_dimension}的产品结构预测较为合理，建议保持当前预测方法。"

            add_chart_explanation(ranking_explanation)

            # 销售员-产品差异热图分析
            if selected_region_for_diff != '全国' and analysis_dimension == '销售员':
                st.markdown(f'<div class="sub-header">{selected_region_for_diff} - 销售员产品差异热图</div>',
                            unsafe_allow_html=True)

                # 获取该区域数据
                region_data = filtered_salesperson[filtered_salesperson['所属区域'] == selected_region_for_diff].copy()

                # 选择要分析的销售员
                selected_salesperson = st.selectbox(
                    "选择销售员查看产品差异",
                    options=region_data['销售员'].unique()
                )

                # 筛选选定销售员数据
                salesperson_data = region_data[region_data['销售员'] == selected_salesperson].copy()

                if not salesperson_data.empty:
                    # 计算该销售员的总销售额和总预测额
                    sp_total_actual = salesperson_data['销售额'].sum()
                    sp_total_forecast = salesperson_data['预测销售额'].sum()

                    # 计算每个产品的占比
                    salesperson_data['实际占比'] = salesperson_data[
                                                       '销售额'] / sp_total_actual * 100 if sp_total_actual > 0 else 0
                    salesperson_data['预测占比'] = salesperson_data[
                                                       '预测销售额'] / sp_total_forecast * 100 if sp_total_forecast > 0 else 0
                    salesperson_data['占比差异'] = salesperson_data['实际占比'] - salesperson_data['预测占比']

                    # 添加产品名称
                    if product_names_map:
                        salesperson_data['产品名称'] = salesperson_data['产品代码'].apply(
                            lambda x: product_names_map.get(x, ''))
                        salesperson_data['产品显示'] = salesperson_data.apply(
                            lambda row: f"{row['产品代码']} {row['产品名称']}", axis=1)
                    else:
                        salesperson_data['产品显示'] = salesperson_data['产品代码']

                    # 按销售额降序排序
                    salesperson_data = salesperson_data.sort_values('销售额', ascending=False)

                    # 获取前10个产品
                    top_products = salesperson_data.head(min(10, len(salesperson_data)))

                    # 创建水平热图
                    fig_heatmap = go.Figure()

                    # 添加实际占比条
                    fig_heatmap.add_trace(go.Bar(
                        y=top_products['产品显示'],
                        x=top_products['实际占比'],
                        name='实际占比',
                        marker_color='royalblue',
                        orientation='h'
                    ))

                    # 添加预测占比条
                    fig_heatmap.add_trace(go.Bar(
                        y=top_products['产品显示'],
                        x=top_products['预测占比'],
                        name='预测占比',
                        marker_color='lightcoral',
                        orientation='h'
                    ))

                    # 更新布局
                    fig_heatmap.update_layout(
                        title=f"{selected_region_for_diff} - {selected_salesperson} 产品占比对比",
                        xaxis_title="占比 (%)",
                        yaxis_title="产品",
                        barmode='group',
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )

                    # 添加悬停提示
                    fig_heatmap.update_traces(
                        hovertemplate='<b>%{y}</b><br>%{name}: %{x:.2f}%<br>销售额: %{customdata:,.0f}元<extra></extra>',
                        customdata=top_products['销售额'].values,
                        selector=dict(name='实际占比')
                    )

                    fig_heatmap.update_traces(
                        hovertemplate='<b>%{y}</b><br>%{name}: %{x:.2f}%<br>预测销售额: %{customdata:,.0f}元<extra></extra>',
                        customdata=top_products['预测销售额'].values,
                        selector=dict(name='预测占比')
                    )

                    st.plotly_chart(fig_heatmap, use_container_width=True)

                    # 创建差异条形图
                    fig_sp_diff = px.bar(
                        top_products,
                        y='产品显示',
                        x='占比差异',
                        title=f"{selected_salesperson} 产品占比差异",
                        color='占比差异',
                        color_continuous_scale='RdBu_r',
                        text='占比差异',
                        orientation='h'
                    )

                    fig_sp_diff.update_traces(
                        texttemplate='%{x:+.1f}%',
                        textposition='outside'
                    )

                    fig_sp_diff.update_layout(
                        xaxis_title="占比差异 (%)",
                        yaxis_title="产品",
                        xaxis=dict(zeroline=True)
                    )

                    # 添加参考线
                    fig_sp_diff.add_shape(
                        type="line",
                        y0=-0.5,
                        y1=len(top_products) - 0.5,
                        x0=0,
                        x1=0,
                        line=dict(color="black", width=1, dash="dash")
                    )

                    # 添加悬停提示
                    fig_sp_diff.update_traces(
                        hovertemplate='<b>%{y}</b><br>占比差异: %{x:+.2f}%<br>实际占比: %{customdata[0]:.2f}%<br>预测占比: %{customdata[1]:.2f}%<extra></extra>',
                        customdata=top_products[['实际占比', '预测占比']].values
                    )

                    st.plotly_chart(fig_sp_diff, use_container_width=True)

                    # 生成动态解读
                    sp_explanation = f"""
                                <b>图表解读：</b> 上图展示了{selected_salesperson}销售的主要产品实际销售占比与预测占比的对比，下图展示了占比差异。
                                红色表示实际占比高于预测(低估)，蓝色表示实际占比低于预测(高估)。通过这些分析可以识别销售员在产品结构预测上的偏差模式。
                                """

                    # 添加具体产品分析
                    if not top_products.empty:
                        # 找出差异最大的产品
                        max_diff_product = top_products.loc[top_products['占比差异'].abs().idxmax()]
                        top_sales_product = top_products.iloc[0]

                        sp_explanation += f"<br><b>产品分析：</b> "

                        sp_explanation += f"{top_sales_product['产品显示']}是{selected_salesperson}销售额最高的产品，"

                        if max_diff_product['占比差异'] > 0:
                            sp_explanation += f"{max_diff_product['产品显示']}预测占比被低估最多，差异为{max_diff_product['占比差异']:.2f}%。"
                        else:
                            sp_explanation += f"{max_diff_product['产品显示']}预测占比被高估最多，差异为{abs(max_diff_product['占比差异']):.2f}%。"

                        # 生成销售员建议
                        sp_explanation += f"<br><b>行动建议：</b> "

                        # 找出占比差异显著的产品
                        high_diff_products = top_products[abs(top_products['占比差异']) > 5]
                        if not high_diff_products.empty:
                            for _, product in high_diff_products.head(2).iterrows():
                                if product['占比差异'] > 0:
                                    sp_explanation += f"建议{selected_salesperson}在预测时适当提高{product['产品显示']}的比例；"
                                else:
                                    sp_explanation += f"建议{selected_salesperson}在预测时适当降低{product['产品显示']}的比例；"

                            sp_explanation += f"销售主管应与{selected_salesperson}讨论产品结构预测偏差问题，并提供针对性指导。"
                        else:
                            sp_explanation += f"{selected_salesperson}的产品结构预测较为合理，建议保持当前预测方法。"

                    add_chart_explanation(sp_explanation)
                else:
                    st.warning(f"{selected_region_for_diff}区域的{selected_salesperson}没有足够的数据进行分析。")
        else:
            st.warning("没有足够的数据来进行差异分析。")

        with tabs[4]:  # 历史趋势标签页
            st.markdown('<div class="sub-header">销售与预测历史趋势</div>', unsafe_allow_html=True)

            # 准备历史趋势数据
            monthly_trend = processed_data['merged_monthly'].groupby(['所属年月', '所属区域']).agg({
                '销售额': 'sum',
                '预测销售额': 'sum'
            }).reset_index()

            # 选择区域
            selected_region_for_trend = st.selectbox(
                "选择区域查看历史趋势",
                options=['全国'] + all_regions,
                key="region_select_trend"
            )

            if selected_region_for_trend == '全国':
                # 计算全国趋势
                national_trend = monthly_trend.groupby('所属年月').agg({
                    '销售额': 'sum',
                    '预测销售额': 'sum'
                }).reset_index()

                trend_data = national_trend
            else:
                # 筛选区域趋势
                region_trend = monthly_trend[monthly_trend['所属区域'] == selected_region_for_trend]
                trend_data = region_trend

            # 创建销售与预测趋势图
            fig_trend = go.Figure()

            # 添加实际销售线
            fig_trend.add_trace(go.Scatter(
                x=trend_data['所属年月'],
                y=trend_data['销售额'],
                mode='lines+markers',
                name='实际销售额',
                line=dict(color='royalblue', width=3),
                marker=dict(size=8)
            ))

            # 添加预测销售线
            fig_trend.add_trace(go.Scatter(
                x=trend_data['所属年月'],
                y=trend_data['预测销售额'],
                mode='lines+markers',
                name='预测销售额',
                line=dict(color='lightcoral', width=3, dash='dot'),
                marker=dict(size=8)
            ))

            # 计算差异率
            trend_data['差异率'] = (trend_data['销售额'] - trend_data['预测销售额']) / trend_data['销售额'] * 100

            # 添加差异率线
            fig_trend.add_trace(go.Scatter(
                x=trend_data['所属年月'],
                y=trend_data['差异率'],
                mode='lines+markers+text',
                name='差异率 (%)',
                yaxis='y2',
                line=dict(color='green', width=2),
                marker=dict(size=8),
                text=[f"{x:.1f}%" for x in trend_data['差异率']],
                textposition='top center'
            ))

            # 更新布局
            fig_trend.update_layout(
                title=f"{selected_region_for_trend}销售与预测历史趋势",
                xaxis_title="月份",
                yaxis=dict(title="销售额 (元)", tickformat=",.0f"),
                yaxis2=dict(
                    title="差异率 (%)",
                    overlaying='y',
                    side='right'
                ),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )

            # 添加悬停提示
            fig_trend.update_traces(
                hovertemplate='<b>%{x}</b><br>%{name}: %{y:,.0f}元<extra></extra>',
                selector=dict(name=['实际销售额', '预测销售额'])
            )

            fig_trend.update_traces(
                hovertemplate='<b>%{x}</b><br>%{name}: %{y:.2f}%<extra></extra>',
                selector=dict(name='差异率 (%)')
            )

            # 强调选定月份
            if selected_months:
                for month in selected_months:
                    if month in trend_data['所属年月'].values:
                        fig_trend.add_shape(
                            type="rect",
                            x0=month,
                            x1=month,
                            y0=0,
                            y1=trend_data['销售额'].max() * 1.1,
                            fillcolor="rgba(144, 238, 144, 0.2)",
                            line=dict(width=0)
                        )

            st.plotly_chart(fig_trend, use_container_width=True)

            # 生成动态解读
            trend_explanation = f"""
                    <b>图表解读：</b> 此图展示了{selected_region_for_trend}历史销售额(蓝线)与预测销售额(红线)趋势，以及月度差异率(绿线)。浅绿色背景区域是当前选定的分析月份。
                    通过观察趋势可以发现销售的季节性波动、预测与实际的一致性以及差异率的变化趋势。
                    """

            # 添加具体分析
            if not trend_data.empty and len(trend_data) > 1:
                # 计算整体趋势
                sales_trend = np.polyfit(range(len(trend_data)), trend_data['销售额'], 1)[0]
                sales_trend_direction = "上升" if sales_trend > 0 else "下降"

                # 找出差异率最大和最小的月份
                max_diff_month = trend_data.loc[trend_data['差异率'].abs().idxmax()]

                # 计算准确率均值
                accuracy_mean = (100 - abs(trend_data['差异率'])).mean()

                trend_explanation += f"<br><b>趋势分析：</b> "

                trend_explanation += f"{selected_region_for_trend}销售额整体呈{sales_trend_direction}趋势，"
                trend_explanation += f"历史准确率平均为{accuracy_mean:.1f}%，"
                trend_explanation += f"{max_diff_month['所属年月']}月差异率最大，达{max_diff_month['差异率']:.1f}%。"

                # 生成建议
                trend_explanation += f"<br><b>行动建议：</b> "

                # 根据趋势分析生成建议
                if abs(trend_data['差异率']).mean() > 10:
                    trend_explanation += f"针对{selected_region_for_trend}的销售预测仍有提升空间，建议分析差异率较大月份的原因；"

                    # 检查是否有季节性模式
                    month_numbers = [int(m.split('-')[1]) for m in trend_data['所属年月']]
                    if len(month_numbers) >= 12:
                        spring_diff = abs(trend_data[trend_data['所属年月'].str.contains(r'-0[345]$')]['差异率']).mean()
                        summer_diff = abs(trend_data[trend_data['所属年月'].str.contains(r'-0[678]$')]['差异率']).mean()
                        autumn_diff = abs(
                            trend_data[trend_data['所属年月'].str.contains(r'-0[9]$|10|11$')]['差异率']).mean()
                        winter_diff = abs(
                            trend_data[trend_data['所属年月'].str.contains(r'-12$|-0[12]$')]['差异率']).mean()

                        seasons = [('春季', spring_diff), ('夏季', summer_diff), ('秋季', autumn_diff),
                                   ('冬季', winter_diff)]
                        worst_season = max(seasons, key=lambda x: x[1])

                        trend_explanation += f"特别注意{worst_season[0]}月份的预测，历史上这些月份差异率较大({worst_season[1]:.1f}%)；"

                    trend_explanation += "考虑在预测模型中增加季节性因素，提高季节性预测的准确性。"
                else:
                    trend_explanation += f"{selected_region_for_trend}的销售预测整体表现良好，建议保持当前预测方法，"
                    trend_explanation += "持续监控销售趋势变化，及时调整预测模型。"

            add_chart_explanation(trend_explanation)

            # 产品历史趋势分析
            st.markdown('<div class="sub-header">产品销售历史趋势</div>', unsafe_allow_html=True)

            # 选择产品
            all_products = sorted(processed_data['merged_monthly']['产品代码'].unique())
            product_options = []
            for code in all_products:
                if product_names_map and code in product_names_map:
                    product_options.append(f"{code} {product_names_map[code]}")
                else:
                    product_options.append(code)

            selected_product_display = st.selectbox(
                "选择产品查看历史趋势",
                options=product_options
            )

            # 从显示名称中提取产品代码
            selected_product = selected_product_display.split(' ')[
                0] if ' ' in selected_product_display else selected_product_display

            # 准备产品历史数据
            if selected_region_for_trend == '全国':
                # 全国该产品趋势
                product_trend = processed_data['merged_monthly'][
                    processed_data['merged_monthly']['产品代码'] == selected_product
                    ].groupby('所属年月').agg({
                    '销售额': 'sum',
                    '预测销售额': 'sum',
                    '求和项:数量（箱）': 'sum',
                    '预计销售量': 'sum'
                }).reset_index()
            else:
                # 区域该产品趋势
                product_trend = processed_data['merged_monthly'][
                    (processed_data['merged_monthly']['产品代码'] == selected_product) &
                    (processed_data['merged_monthly']['所属区域'] == selected_region_for_trend)
                    ].groupby('所属年月').agg({
                    '销售额': 'sum',
                    '预测销售额': 'sum',
                    '求和项:数量（箱）': 'sum',
                    '预计销售量': 'sum'
                }).reset_index()

            # 如果有数据，创建图表
            if not product_trend.empty:
                # 计算差异率
                product_trend['销售额差异率'] = (product_trend['销售额'] - product_trend['预测销售额']) / product_trend[
                    '销售额'] * 100
                product_trend['数量差异率'] = (product_trend['求和项:数量（箱）'] - product_trend['预计销售量']) / \
                                              product_trend['求和项:数量（箱）'] * 100

                # 创建销售额趋势图
                fig_product_amount = go.Figure()

                # 添加实际销售额线
                fig_product_amount.add_trace(go.Scatter(
                    x=product_trend['所属年月'],
                    y=product_trend['销售额'],
                    mode='lines+markers',
                    name='实际销售额',
                    line=dict(color='royalblue', width=3),
                    marker=dict(size=8)
                ))

                # 添加预测销售额线
                fig_product_amount.add_trace(go.Scatter(
                    x=product_trend['所属年月'],
                    y=product_trend['预测销售额'],
                    mode='lines+markers',
                    name='预测销售额',
                    line=dict(color='lightcoral', width=3, dash='dot'),
                    marker=dict(size=8)
                ))

                # 更新布局
                fig_product_amount.update_layout(
                    title=f"{selected_region_for_trend} - {selected_product_display} 销售额趋势",
                    xaxis_title="月份",
                    yaxis=dict(title="销售额 (元)", tickformat=",.0f"),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )

                # 添加悬停提示
                fig_product_amount.update_traces(
                    hovertemplate='<b>%{x}</b><br>%{name}: %{y:,.0f}元<extra></extra>'
                )

                # 强调选定月份
                if selected_months:
                    for month in selected_months:
                        if month in product_trend['所属年月'].values:
                            fig_product_amount.add_shape(
                                type="rect",
                                x0=month,
                                x1=month,
                                y0=0,
                                y1=product_trend['销售额'].max() * 1.1,
                                fillcolor="rgba(144, 238, 144, 0.2)",
                                line=dict(width=0)
                            )

                st.plotly_chart(fig_product_amount, use_container_width=True)

                # 创建销售量趋势图
                fig_product_qty = go.Figure()

                # 添加实际销售量线
                fig_product_qty.add_trace(go.Scatter(
                    x=product_trend['所属年月'],
                    y=product_trend['求和项:数量（箱）'],
                    mode='lines+markers',
                    name='实际销售量',
                    line=dict(color='royalblue', width=3),
                    marker=dict(size=8)
                ))

                # 添加预测销售量线
                fig_product_qty.add_trace(go.Scatter(
                    x=product_trend['所属年月'],
                    y=product_trend['预计销售量'],
                    mode='lines+markers',
                    name='预测销售量',
                    line=dict(color='lightcoral', width=3, dash='dot'),
                    marker=dict(size=8)
                ))

                # 添加差异率线
                fig_product_qty.add_trace(go.Scatter(
                    x=product_trend['所属年月'],
                    y=product_trend['数量差异率'],
                    mode='lines+markers+text',
                    name='差异率 (%)',
                    yaxis='y2',
                    line=dict(color='green', width=2),
                    marker=dict(size=8),
                    text=[f"{x:.1f}%" for x in product_trend['数量差异率']],
                    textposition='top center'
                ))

                # 更新布局
                fig_product_qty.update_layout(
                    title=f"{selected_region_for_trend} - {selected_product_display} 销售量趋势",
                    xaxis_title="月份",
                    yaxis=dict(title="销售量 (箱)"),
                    yaxis2=dict(
                        title="差异率 (%)",
                        overlaying='y',
                        side='right'
                    ),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )

                # 添加悬停提示
                fig_product_qty.update_traces(
                    hovertemplate='<b>%{x}</b><br>%{name}: %{y:,.0f}箱<extra></extra>',
                    selector=dict(name=['实际销售量', '预测销售量'])
                )

                fig_product_qty.update_traces(
                    hovertemplate='<b>%{x}</b><br>%{name}: %{y:.2f}%<extra></extra>',
                    selector=dict(name='差异率 (%)')
                )

                # 强调选定月份
                if selected_months:
                    for month in selected_months:
                        if month in product_trend['所属年月'].values:
                            fig_product_qty.add_shape(
                                type="rect",
                                x0=month,
                                x1=month,
                                y0=0,
                                y1=product_trend['求和项:数量（箱）'].max() * 1.1,
                                fillcolor="rgba(144, 238, 144, 0.2)",
                                line=dict(width=0)
                            )

                st.plotly_chart(fig_product_qty, use_container_width=True)

                # 生成动态解读
                product_explanation = f"""
                        <b>图表解读：</b> 上图展示了{selected_product_display}产品在{selected_region_for_trend}的销售额历史趋势，下图展示了销售量趋势和差异率。浅绿色背景区域是当前选定的分析月份。
                        可以观察产品销售的季节性波动、预测准确性的变化以及潜在的增长或下降趋势。绿线代表差异率，有助于识别预测偏离较大的时期。
                        """

                # 添加具体分析
                if len(product_trend) > 1:
                    # 计算销售量增长趋势
                    qty_trend = np.polyfit(range(len(product_trend)), product_trend['求和项:数量（箱）'], 1)[0]
                    qty_trend_direction = "上升" if qty_trend > 0 else "下降"

                    # 计算准确率
                    accuracy_mean = (100 - abs(product_trend['数量差异率'])).mean()

                    # 检查连续低估或高估
                    recent_months = product_trend.tail(3)
                    consecutive_under = (recent_months['数量差异率'] > 0).all()
                    consecutive_over = (recent_months['数量差异率'] < 0).all()

                    product_explanation += f"<br><b>趋势分析：</b> "

                    product_explanation += f"{selected_product_display}销售量整体呈{qty_trend_direction}趋势，"
                    product_explanation += f"历史预测准确率平均为{accuracy_mean:.1f}%，"

                    if consecutive_under:
                        product_explanation += f"近期连续3个月被低估，表明市场需求可能高于预期。"
                    elif consecutive_over:
                        product_explanation += f"近期连续3个月被高估，表明市场需求可能低于预期。"
                    else:
                        product_explanation += f"近期预测没有明显的系统性偏差。"

                    # 生成建议
                    product_explanation += f"<br><b>行动建议：</b> "

                    if qty_trend > 0 and accuracy_mean < 80:
                        product_explanation += f"对于销量上升但准确率不足的{selected_product_display}，建议适当提高预测量并完善预测方法；"
                    elif qty_trend < 0 and consecutive_over:
                        product_explanation += f"对于销量下降且持续高估的{selected_product_display}，建议降低预测量{abs(round(recent_months['数量差异率'].mean()))}%以避免库存积压；"
                    elif abs(product_trend['数量差异率']).mean() > 15:
                        product_explanation += f"{selected_product_display}的预测准确率较低，建议重点关注市场变化并调整预测方法；"
                    else:
                        product_explanation += f"{selected_product_display}的销售预测整体表现良好，建议持续关注市场变化，确保预测与实际一致。"

                add_chart_explanation(product_explanation)

                # 计算滚动增长率
                if len(product_trend) > 12:
                    # 计算12个月同比增长率
                    product_trend['销售量_去年同期'] = product_trend['求和项:数量（箱）'].shift(12)
                    product_trend['销售量_同比增长率'] = (product_trend['求和项:数量（箱）'] - product_trend[
                        '销售量_去年同期']) / product_trend['销售量_去年同期'] * 100

                    # 创建增长率图表
                    growth_data = product_trend.dropna(subset=['销售量_同比增长率'])

                    if not growth_data.empty:
                        fig_growth_rate = px.line(
                            growth_data,
                            x='所属年月',
                            y='销售量_同比增长率',
                            title=f"{selected_product_display} 销售量同比增长率",
                            markers=True
                        )

                        fig_growth_rate.update_layout(
                            xaxis_title="月份",
                            yaxis=dict(title="增长率 (%)")
                        )

                        # 添加参考线
                        fig_growth_rate.add_shape(
                            type="line",
                            x0=growth_data['所属年月'].min(),
                            x1=growth_data['所属年月'].max(),
                            y0=0,
                            y1=0,
                            line=dict(color="black", width=1, dash="dash")
                        )

                        # 添加悬停提示
                        fig_growth_rate.update_traces(
                            hovertemplate='<b>%{x}</b><br>增长率: %{y:.2f}%<br>销量: %{customdata[0]:,.0f}箱<br>去年同期: %{customdata[1]:,.0f}箱<extra></extra>',
                            customdata=growth_data[['求和项:数量（箱）', '销售量_去年同期']].values
                        )

                        # 强调选定月份
                        if selected_months:
                            for month in selected_months:
                                if month in growth_data['所属年月'].values:
                                    fig_growth_rate.add_shape(
                                        type="rect",
                                        x0=month,
                                        x1=month,
                                        y0=min(growth_data['销售量_同比增长率'].min(), -10),
                                        y1=max(growth_data['销售量_同比增长率'].max(), 10),
                                        fillcolor="rgba(144, 238, 144, 0.2)",
                                        line=dict(width=0)
                                    )

                        st.plotly_chart(fig_growth_rate, use_container_width=True)

                        # 生成动态解读
                        growth_explanation = f"""
                                <b>图表解读：</b> 此图展示了{selected_product_display}产品销售量的同比增长率，反映了产品需求的年度变化趋势。浅绿色背景区域是当前选定的分析月份。
                                正增长率表示相比去年同期销售上升，负增长率表示下降。增长率的波动和趋势变化是判断产品生命周期阶段的重要指标。
                                """

                        # 添加具体分析
                        if len(growth_data) > 3:
                            # 计算最近的增长率趋势
                            recent_growth = growth_data.tail(3)['销售量_同比增长率'].mean()

                            growth_explanation += f"<br><b>增长分析：</b> "

                            if recent_growth > 10:
                                growth_explanation += f"{selected_product_display}近期增长强劲，平均增长率达{recent_growth:.1f}%，处于快速增长阶段。"
                            elif recent_growth > 0:
                                growth_explanation += f"{selected_product_display}保持稳定增长，平均增长率为{recent_growth:.1f}%，处于成长期。"
                            elif recent_growth > -10:
                                growth_explanation += f"{selected_product_display}增长放缓，平均增长率为{recent_growth:.1f}%，可能进入成熟期。"
                            else:
                                growth_explanation += f"{selected_product_display}明显下滑，平均增长率为{recent_growth:.1f}%，可能已进入衰退期。"

                            # 生成建议
                            growth_explanation += f"<br><b>备货建议：</b> "

                            if recent_growth > 10:
                                growth_explanation += f"对于强劲增长的{selected_product_display}，建议增加{round(recent_growth)}%的备货量以满足增长需求；"
                                growth_explanation += "关注该产品的供应链能力，确保能满足上升的需求。"
                            elif recent_growth > 0:
                                growth_explanation += f"对于稳定增长的{selected_product_display}，建议适度增加{round(recent_growth)}%的备货；"
                                growth_explanation += "定期评估市场反馈，持续优化库存水平。"
                            elif recent_growth > -10:
                                growth_explanation += f"对于增长放缓的{selected_product_display}，建议维持当前库存水平；"
                                growth_explanation += "密切关注市场变化，避免过度备货。"
                            else:
                                growth_explanation += f"对于明显下滑的{selected_product_display}，建议减少{abs(round(recent_growth))}%的备货以避免库存积压；"
                                growth_explanation += "评估产品策略，考虑是否需要产品更新或市场调整。"

                        add_chart_explanation(growth_explanation)
            else:
                st.warning(
                    f"没有足够的数据来分析{selected_product_display}产品在{selected_region_for_trend}的历史趋势。")

        # 添加页脚信息
        st.markdown("""
                <div style="margin-top: 50px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; color: #666; font-size: 0.8rem;">
                    <p>预测与实际销售对比分析仪表盘 | 版本 1.0.0 | 最后更新: 2025年4月</p>
                    <p>使用Streamlit和Plotly构建 | 数据更新频率: 每月</p>
                </div>
                """, unsafe_allow_html=True)