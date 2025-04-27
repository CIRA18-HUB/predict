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
</style>
""", unsafe_allow_html=True)

# 初始化会话状态
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False  # 明确使用字典语法初始化

# 登录界面
if not st.session_state.get('authenticated', False):  # 使用get方法更安全地获取值
    st.markdown('<div style="font-size: 1.5rem; color: #1f3867; text-align: center; margin-bottom: 1rem;">预测与实际销售对比分析仪表盘 | 登录</div>', unsafe_allow_html=True)

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
                st.rerun()
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

# 数据加载函数
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

# 数据处理和分析函数
def process_data(actual_df, forecast_df, price_df):
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
                0      # 预测和实际都是0
            )
        )
        
        df['销售额差异率'] = np.where(
            df['销售额'] > 0,
            df['销售额差异'] / df['销售额'] * 100,
            np.where(
                df['预测销售额'] > 0,
                -100,  # 预测有值但实际为0
                0      # 预测和实际都是0
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
    region_monthly_summary['数量差异'] = region_monthly_summary['求和项:数量（箱）'] - region_monthly_summary['预计销售量']
    region_monthly_summary['销售额差异'] = region_monthly_summary['销售额'] - region_monthly_summary['预测销售额']
    
    # 计算差异率
    region_monthly_summary['数量差异率'] = region_monthly_summary['数量差异'] / region_monthly_summary['求和项:数量（箱）'] * 100
    region_monthly_summary['销售额差异率'] = region_monthly_summary['销售额差异'] / region_monthly_summary['销售额'] * 100
    
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
                prev_year = years[i-1]
                
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
                        for m in range(month-2, month+1):
                            if m in current_year_data.columns:
                                current_3m_sum += current_year_data[m].iloc[0] if not pd.isna(current_year_data[m].iloc[0]) else 0
                                months_current.append(m)
                        
                        # 计算前一年同期3个月的总量
                        prev_3m_sum = 0
                        months_prev = []
                        for m in range(month-2, month+1):
                            if m in prev_year_data.columns:
                                prev_3m_sum += prev_year_data[m].iloc[0] if not pd.isna(prev_year_data[m].iloc[0]) else 0
                                months_prev.append(m)
                        
                        # 只有当两个时期都有数据时才计算增长率
                        if current_3m_sum > 0 and prev_3m_sum > 0 and len(months_current) > 0 and len(months_prev) > 0:
                            growth_rate = (current_3m_sum - prev_3m_sum) / prev_3m_sum * 100
                            
                            # 同样计算销售额增长率
                            current_3m_amount = 0
                            for m in months_current:
                                if m in current_year_amount.columns:
                                    current_3m_amount += current_year_amount[m].iloc[0] if not pd.isna(current_year_amount[m].iloc[0]) else 0
                            
                            prev_3m_amount = 0
                            for m in months_prev:
                                if m in prev_year_amount.columns:
                                    prev_3m_amount += prev_year_amount[m].iloc[0] if not pd.isna(prev_year_amount[m].iloc[0]) else 0
                            
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

# 标题
st.markdown('<div class="main-header">预测与实际销售对比分析仪表盘</div>', unsafe_allow_html=True)

# 侧边栏 - 上传文件区域
st.sidebar.header("📂 数据导入")
use_default_files = st.sidebar.checkbox("使用默认文件", value=True, help="使用指定的默认文件路径")

# 定义默认文件路径
DEFAULT_ACTUAL_FILE = "2409~250224出货数据.xlsx"
DEFAULT_FORECAST_FILE = "2409~2502人工预测.xlsx"
DEFAULT_PRICE_FILE = "单价.xlsx"

if use_default_files:
    # 使用默认文件路径
    actual_data = load_actual_data(DEFAULT_ACTUAL_FILE)
    forecast_data = load_forecast_data(DEFAULT_FORECAST_FILE)
    price_data = load_price_data(DEFAULT_PRICE_FILE)
    
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
else:
    # 上传文件
    uploaded_actual = st.sidebar.file_uploader("上传出货数据文件", type=["xlsx", "xls"])
    uploaded_forecast = st.sidebar.file_uploader("上传人工预测数据文件", type=["xlsx", "xls"])
    uploaded_price = st.sidebar.file_uploader("上传单价数据文件", type=["xlsx", "xls"])
    
    # 加载数据
    actual_data = load_actual_data(uploaded_actual if uploaded_actual else None)
    forecast_data = load_forecast_data(uploaded_forecast if uploaded_forecast else None)
    price_data = load_price_data(uploaded_price if uploaded_price else None)

# 处理数据
processed_data = process_data(actual_data, forecast_data, price_data)

# 获取数据的所有月份
all_months = sorted(processed_data['merged_monthly']['所属年月'].unique())
latest_month = all_months[-1] if all_months else None

# 侧边栏 - 月份选择
selected_month = st.sidebar.selectbox(
    "选择分析月份",
    options=all_months,
    index=len(all_months) - 1 if all_months else 0
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
    (processed_data['merged_monthly']['所属年月'] == selected_month) &
    (processed_data['merged_monthly']['所属区域'].isin(selected_regions))
]

filtered_salesperson = processed_data['merged_by_salesperson'][
    (processed_data['merged_by_salesperson']['所属年月'] == selected_month) &
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
            <p class="card-text">选定区域 - {selected_month}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 总预测销售额
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <p class="card-header">预测销售额</p>
            <p class="card-value">{format_yuan(total_forecast_sales)}</p>
            <p class="card-text">选定区域 - {selected_month}</p>
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
        yaxis=dict(tickformat=".2f", title="准确率 (%)")
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
    region_accuracy_monthly = processed_data['regional_accuracy']['region_monthly']
    latest_region_accuracy = region_accuracy_monthly[
        region_accuracy_monthly['所属年月'] == selected_month
    ].copy()
    
    # 数据处理
    latest_region_accuracy['销售额准确率'] = latest_region_accuracy['销售额准确率'].clip(0, 1) * 100
    latest_region_accuracy['数量准确率'] = latest_region_accuracy['数量准确率'].clip(0, 1) * 100
    
    # 柱状图
    fig_region_accuracy = px.bar(
        latest_region_accuracy,
        x='所属区域',
        y='销售额准确率',
        title=f"{selected_month}各区域销售额预测准确率",
        color='所属区域',
        text_auto='.2f'
    )
    
    fig_region_accuracy.update_layout(
        yaxis=dict(title="准确率 (%)")
    )
    
    # 添加参考线
    fig_region_accuracy.add_shape(
        type="line",
        x0=-0.5,
        x1=len(latest_region_accuracy) - 0.5,
        y0=85,
        y1=85,
        line=dict(color="green", width=1, dash="dash")
    )
    
    st.plotly_chart(fig_region_accuracy, use_container_width=True)
    
    # 添加图表解释
    add_chart_explanation(f"""
    <b>图表解读：</b> 此图比较了{selected_month}各区域销售额预测的准确率，绿色虚线代表理想准确率目标(85%)。
    区域间的准确率差异可能反映了不同区域销售特性的差异、预测方法的适用性差异或区域销售团队对市场的理解差异。
    <b>行动建议：</b> 关注准确率较低的区域，提供预测方法培训；分析准确率高的区域成功经验并在各区域间分享；考虑针对不同特性区域调整预测模型或方法。
    """)
    
    # 预测与实际销售对比
    st.markdown('<div class="sub-header">预测与实际销售对比</div>', unsafe_allow_html=True)
    
    # 计算每个区域的销售额和预测额
    region_sales_comparison = filtered_monthly.groupby('所属区域').agg({
        '销售额': 'sum',
        '预测销售额': 'sum'
    }).reset_index()
    
    # 计算差异
    region_sales_comparison['差异额'] = region_sales_comparison['销售额'] - region_sales_comparison['预测销售额']
    region_sales_comparison['差异率'] = region_sales_comparison['差异额'] / region_sales_comparison['销售额'] * 100
    
    # 创建堆叠柱状图
    fig_sales_comparison = go.Figure()
    
    # 添加实际销售额柱
    fig_sales_comparison.add_trace(go.Bar(
        x=region_sales_comparison['所属区域'],
        y=region_sales_comparison['销售额'],
        name='实际销售额',
        marker_color='royalblue'
    ))
    
    # 添加预测销售额柱
    fig_sales_comparison.add_trace(go.Bar(
        x=region_sales_comparison['所属区域'],
        y=region_sales_comparison['预测销售额'],
        name='预测销售额',
        marker_color='lightcoral'
    ))
    
    # 添加差异率线
    fig_sales_comparison.add_trace(go.Scatter(
        x=region_sales_comparison['所属区域'],
        y=region_sales_comparison['差异率'],
        mode='lines+markers+text',
        name='差异率 (%)',
        yaxis='y2',
        line=dict(color='green', width=2),
        marker=dict(size=8),
        text=[f"{x:.1f}%" for x in region_sales_comparison['差异率']],
        textposition='top center'
    ))
    
    # 更新布局
    fig_sales_comparison.update_layout(
        title=f"{selected_month}各区域预测与实际销售对比",
        barmode='group',
        yaxis=dict(title="销售额 (元)"),
        yaxis2=dict(
            title="差异率 (%)",
            overlaying='y',
            side='right'
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig_sales_comparison, use_container_width=True)
    
    # 添加图表解释
    add_chart_explanation(f"""
    <b>图表解读：</b> 此图展示了{selected_month}各区域的实际销售额(蓝色)与预测销售额(红色)对比，绿线显示差异率。
    正差异率表示实际销售超过预测，负差异率表示实际销售低于预测。差异率的绝对值越大，表明预测偏离实际的程度越大。
    <b>行动建议：</b> 对于差异率绝对值超过15%的区域，需重点分析差异原因；对于正差异率高的区域，建议提高库存水平以满足超预期需求；对于负差异率高的区域，需评估库存积压风险并调整未来预测。
    """)

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
        
        # 产品增长/下降分析
        st.markdown('<div class="sub-header">产品三个月滚动同比增长率</div>', unsafe_allow_html=True)
        
        # 按增长率排序
        sorted_growth = product_growth['latest_growth'].sort_values('销量增长率', ascending=False).copy()
        
        # 增长率条形图
        fig_growth = px.bar(
            sorted_growth,
            x='产品代码',
            y='销量增长率',
            color='趋势',
            title="产品销量三个月滚动同比增长率",
            text_auto='.1f',
            color_discrete_map={
                '强劲增长': '#2E8B57',
                '增长': '#4CAF50',
                '轻微下降': '#FFA500',
                '显著下降': '#F44336'
            }
        )
        
        fig_growth.update_layout(
            xaxis_title="产品代码",
            yaxis_title="增长率 (%)"
        )
        
        # 添加参考线
        fig_growth.add_shape(
            type="line",
            x0=-0.5,
            x1=len(sorted_growth) - 0.5,
            y0=0,
            y1=0,
            line=dict(color="black", width=1, dash="dash")
        )
        
        st.plotly_chart(fig_growth, use_container_width=True)
        
        # 添加图表解释
        add_chart_explanation("""
        <b>图表解读：</b> 此图展示了各产品三个月滚动销量的同比增长率，按增长率从高到低排序。颜色代表增长趋势：深绿色为强劲增长(>10%)，浅绿色为增长(0-10%)，橙色为轻微下降(0--10%)，红色为显著下降(<-10%)。
        增长率是判断产品市场表现的重要指标，正增长率表明产品需求上升，负增长率表明需求下降。
        <b>行动建议：</b> 对强劲增长和增长产品，适当增加备货以满足上升需求；对轻微下降产品，维持现有库存水平并关注需求变化；对显著下降产品，控制备货以避免库存积压。
        """)
        
        # 备货建议列表
        st.markdown('<div class="sub-header">产品备货建议</div>', unsafe_allow_html=True)
        
        # 按产品代码排序，方便查找
        sorted_by_code = sorted_growth.sort_values('产品代码').copy()
        
        # 将数据分为三组：增加备货、维持备货和减少备货
        increase_inventory = sorted_by_code[sorted_by_code['备货建议'] == '增加备货'].copy()
        maintain_inventory = sorted_by_code[sorted_by_code['备货建议'] == '维持当前备货水平'].copy()
        decrease_inventory = sorted_by_code[sorted_by_code['备货建议'] == '减少备货'].copy()
        
        # 创建三列布局
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div style="background-color: rgba(76, 175, 80, 0.1); padding: 10px; border-radius: 5px; border-left: 5px solid #4CAF50;">
                <h3 style="color: #2E8B57;">增加备货</h3>
            </div>
            """, unsafe_allow_html=True)
            
            for _, row in increase_inventory.iterrows():
                st.markdown(f"""
                <div style="margin: 5px 0; padding: 5px; border-bottom: 1px solid #eee;">
                    <span style="font-weight: bold;">{row['产品代码']}</span>
                    <span style="float: right; color: #2E8B57;">+{row['销量增长率']:.1f}%</span>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="background-color: rgba(255, 235, 59, 0.1); padding: 10px; border-radius: 5px; border-left: 5px solid #FFEB3B;">
                <h3 style="color: #FFC107;">维持备货</h3>
            </div>
            """, unsafe_allow_html=True)
            
            for _, row in maintain_inventory.iterrows():
                st.markdown(f"""
                <div style="margin: 5px 0; padding: 5px; border-bottom: 1px solid #eee;">
                    <span style="font-weight: bold;">{row['产品代码']}</span>
                    <span style="float: right; color: #FFC107;">{row['销量增长率']:.1f}%</span>
                </div>
                """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div style="background-color: rgba(244, 67, 54, 0.1); padding: 10px; border-radius: 5px; border-left: 5px solid #F44336;">
                <h3 style="color: #F44336;">减少备货</h3>
            </div>
            """, unsafe_allow_html=True)
            
            for _, row in decrease_inventory.iterrows():
                st.markdown(f"""
                <div style="margin: 5px 0; padding: 5px; border-bottom: 1px solid #eee;">
                    <span style="font-weight: bold;">{row['产品代码']}</span>
                    <span style="float: right; color: #F44336;">{row['销量增长率']:.1f}%</span>
                </div>
                """, unsafe_allow_html=True)
        
        # 添加备货建议说明
        add_chart_explanation("""
        <b>备货建议说明：</b> 
        <ul>
        <li><b>增加备货</b>：针对增长率为正的产品，建议增加库存水平以满足上升的市场需求，避免缺货情况。</li>
        <li><b>维持备货</b>：针对增长率在-10%到0%之间的产品，建议保持当前库存水平，密切关注需求变化。</li>
        <li><b>减少备货</b>：针对增长率低于-10%的产品，建议减少库存水平以降低库存积压风险。</li>
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
        region_month_data = filtered_monthly[filtered_monthly['所属区域'] == selected_region_for_growth].copy()
        
        # 如果有数据，计算该区域的产品销售并与全国趋势比较
        if not region_month_data.empty:
            # 对区域产品按销售额排序
            region_products = region_month_data.sort_values('销售额', ascending=False)
            
            # 合并增长率数据
            region_products_with_growth = pd.merge(
                region_products,
                product_growth['latest_growth'][['产品代码', '销量增长率', '趋势', '备货建议']],
                on='产品代码',
                how='left'
            )
            
            # 产品增长散点图
            fig_region_growth = px.scatter(
                region_products_with_growth,
                x='销售额',
                y='销量增长率',
                color='趋势',
                size='求和项:数量（箱）',
                hover_name='产品代码',
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
            
            st.plotly_chart(fig_region_growth, use_container_width=True)
            
            # 添加图表解释
            add_chart_explanation(f"""
            <b>图表解读：</b> 此散点图展示了{selected_region_for_growth}区域各产品的销售额(横轴)与全国销量增长率(纵轴)关系，气泡大小表示销售数量，颜色代表增长趋势。
            位于右上象限的产品(高销售额+正增长率)是该区域的明星产品；右下象限的产品(高销售额+负增长率)可能存在库存风险；左上象限的产品(低销售额+正增长率)是潜力产品。
            <b>行动建议：</b> 对于该区域销售额高且全国呈增长态势的产品，建议适当提高预测量；对于销售额高但全国呈下降趋势的产品，建议谨慎控制预测以避免库存积压；对于销售额较低但增长迅速的产品，建议关注并适度增加预测。
            """)
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
        
        # 展示表格
        st.dataframe(
            national_top_skus[['产品代码', '销售额', '累计占比', '销售额准确率']].rename(columns={
                '销售额': '销售额 (元)',
                '累计占比': '累计占比 (%)',
                '销售额准确率': '准确率 (%)'
            }).style.format({
                '销售额 (元)': '{:,.2f}',
                '累计占比 (%)': '{:.2f}',
                '准确率 (%)': '{:.2f}'
            }),
            use_container_width=True
        )
        
        # 创建条形图
        fig_national_top = px.bar(
            national_top_skus,
            x='产品代码',
            y='销售额',
            color='销售额准确率',
            title="全国销售额占比80%的SKU及其准确率",
            labels={'销售额': '销售额 (元)', '销售额准确率': '准确率 (%)'},
            color_continuous_scale='RdYlGn',
            range_color=[0, 100]
        )
        
        fig_national_top.update_layout(
            xaxis_title="产品代码",
            yaxis_title="销售额 (元)",
            yaxis=dict(tickformat=",.0f")
        )
        
        st.plotly_chart(fig_national_top, use_container_width=True)
        
        # 添加图表解释
        add_chart_explanation("""
        <b>图表解读：</b> 此图展示了销售额累计占比达到80%的重点SKU及其准确率，柱子高度表示销售额，颜色深浅表示准确率(深绿色表示高准确率，红色表示低准确率)。
        这些SKU是销售的核心产品，对总体业绩有重要影响。准确率反映了对这些重点SKU预测的精确程度。
        <b>行动建议：</b> 重点关注准确率低于80%的高销售额SKU，优先提高这些产品的预测精度；对这些重点SKU建立专门的需求预测和库存管理机制；定期复盘这些产品的预测偏差原因。
        """)
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
        
        # 展示表格
        st.dataframe(
            region_top[['产品代码', '销售额', '累计占比', '销售额准确率']].rename(columns={
                '销售额': '销售额 (元)',
                '累计占比': '累计占比 (%)',
                '销售额准确率': '准确率 (%)'
            }).style.format({
                '销售额 (元)': '{:,.2f}',
                '累计占比 (%)': '{:.2f}',
                '准确率 (%)': '{:.2f}'
            }),
            use_container_width=True
        )
        
        # 创建条形图
        fig_region_top = px.bar(
            region_top,
            x='产品代码',
            y='销售额',
            color='销售额准确率',
            title=f"{selected_region_for_sku}区域销售额占比80%的SKU及其准确率",
            labels={'销售额': '销售额 (元)', '销售额准确率': '准确率 (%)'},
            color_continuous_scale='RdYlGn',
            range_color=[0, 100]
        )
        
        fig_region_top.update_layout(
            xaxis_title="产品代码",
            yaxis_title="销售额 (元)",
            yaxis=dict(tickformat=",.0f")
        )
        
        st.plotly_chart(fig_region_top, use_container_width=True)
        
        # 添加图表解释
        add_chart_explanation(f"""
        <b>图表解读：</b> 此图展示了{selected_region_for_sku}区域销售额累计占比达到80%的重点SKU及其准确率，柱子高度表示销售额，颜色深浅表示准确率。
        每个区域的重点SKU组合可能有所不同，反映了区域间的市场差异。关注区域重点SKU有助于针对性地制定区域销售策略。
        <b>行动建议：</b> 在区域销售预测会议上，优先讨论这些重点SKU的预测调整；为区域销售团队提供这些产品的市场趋势和历史预测准确率信息；鼓励销售人员针对这些产品提供更详细的市场洞察。
        """)
        
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
            marker_colors=['#4CAF50', '#2196F3', '#F44336']
        ))
        
        fig_sku_comparison.update_layout(
            title=f"{selected_region_for_sku}区域与全国重点SKU对比"
        )
        
        st.plotly_chart(fig_sku_comparison, use_container_width=True)
        
        # 展示具体SKU
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div style="background-color: rgba(76, 175, 80, 0.1); padding: 10px; border-radius: 5px; border-left: 5px solid #4CAF50;">
                <h3 style="color: #4CAF50;">区域与全国共有SKU</h3>
                <p>同时是区域和全国重点的产品</p>
            </div>
            """, unsafe_allow_html=True)
            
            for sku in common_skus:
                st.markdown(f"- {sku}")
        
        with col2:
            st.markdown(f"""
            <div style="background-color: rgba(33, 150, 243, 0.1); padding: 10px; border-radius: 5px; border-left: 5px solid #2196F3;">
                <h3 style="color: #2196F3;">区域特有重点SKU</h3>
                <p>是区域重点但不是全国重点的产品</p>
            </div>
            """, unsafe_allow_html=True)
            
            for sku in region_unique_skus:
                st.markdown(f"- {sku}")
        
        with col3:
            st.markdown(f"""
            <div style="background-color: rgba(244, 67, 54, 0.1); padding: 10px; border-radius: 5px; border-left: 5px solid #F44336;">
                <h3 style="color: #F44336;">全国重点非区域重点SKU</h3>
                <p>是全国重点但不是区域重点的产品</p>
            </div>
            """, unsafe_allow_html=True)
            
            for sku in national_unique_skus:
                st.markdown(f"- {sku}")
        
        # 添加解释
        add_chart_explanation(f"""
        <b>对比分析解读：</b> 此分析展示了{selected_region_for_sku}区域重点SKU与全国重点SKU的异同。共有SKU表示该产品在全国和区域都很重要；区域特有SKU反映区域市场的特殊偏好；全国重点但区域非重点的SKU可能表示区域市场发展潜力。
        <b>行动建议：</b> 对于区域与全国共有的重点SKU，确保充足供应并重点关注预测准确性；对于区域特有重点SKU，在区域备货和销售计划中予以特别关注；对于全国重点但区域非重点的SKU，评估区域市场开发潜力，适当调整销售策略。
        """)
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
    diff_data['销售额差异率'] = diff_data['销售额差异率']
    
    # 差异分析图表
    st.markdown(f'<div class="sub-header">{selected_region_for_diff} - {analysis_dimension}预测差异分析</div>', unsafe_allow_html=True)
    
    # 计算总销售额和总预测额
    total_actual = diff_data['销售额'].sum()
    total_forecast = diff_data['预测销售额'].sum()
    
    # 计算每个项目的占比
    diff_data['实际占比'] = diff_data['销售额'] / total_actual * 100
    diff_data['预测占比'] = diff_data['预测销售额'] / total_forecast * 100
    diff_data['占比差异'] = diff_data['实际占比'] - diff_data['预测占比']
    
    # 按销售额降序排序
    diff_data = diff_data.sort_values('销售额', ascending=False)
    
    # 创建堆叠条形图
    fig_diff = go.Figure()
    
    # 添加实际销售额柱
    fig_diff.add_trace(go.Bar(
        x=diff_data[analysis_dimension == '产品' and '产品代码' or '销售员'],
        y=diff_data['销售额'],
        name='实际销售额',
        marker_color='royalblue'
    ))
    
    # 添加预测销售额柱
    fig_diff.add_trace(go.Bar(
        x=diff_data[analysis_dimension == '产品' and '产品代码' or '销售员'],
        y=diff_data['预测销售额'],
        name='预测销售额',
        marker_color='lightcoral'
    ))
    
    # 添加差异率线
    fig_diff.add_trace(go.Scatter(
        x=diff_data[analysis_dimension == '产品' and '产品代码' or '销售员'],
        y=diff_data['销售额差异率'],
        mode='lines+markers+text',
        name='差异率 (%)',
        yaxis='y2',
        line=dict(color='green', width=2),
        marker=dict(size=8),
        text=[f"{x:.1f}%" for x in diff_data['销售额差异率']],
        textposition='top center'
    ))
    
    # 更新布局
    fig_diff.update_layout(
        title=f"{selected_region_for_diff} {selected_month} - {analysis_dimension}预测与实际销售对比",
        barmode='group',
        yaxis=dict(title="销售额 (元)", tickformat=",.0f"),
        yaxis2=dict(
            title="差异率 (%)",
            overlaying='y',
            side='right'
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig_diff, use_container_width=True)
    
    # 添加图表解释
    add_chart_explanation(f"""
    <b>图表解读：</b> 此图展示了{selected_region_for_diff}区域各{analysis_dimension}的实际销售额(蓝色)与预测销售额(红色)对比，绿线显示差异率。
    正差异率表示实际销售超过预测，负差异率表示实际销售低于预测。差异率的绝对值越大，表明预测偏离实际的程度越大。
    <b>行动建议：</b> 对于差异率绝对值超过15%的{analysis_dimension}，需分析原因并改进预测方法；对于经常出现高差异率的{analysis_dimension}，可能需要提供预测培训或调整预测流程。
    """)
    
    # 占比差异分析
    st.markdown(f'<div class="sub-header">{selected_region_for_diff} - {analysis_dimension}销售占比差异分析</div>', unsafe_allow_html=True)
    
    # 计算平均绝对占比差异
    mean_abs_diff = diff_data['占比差异'].abs().mean()
    
    # 按占比差异绝对值降序排序
    diff_data_sorted = diff_data.sort_values('占比差异', ascending=False)
    
    # 创建占比差异散点图
    fig_share_diff = px.scatter(
        diff_data_sorted,
        x='实际占比',
        y='预测占比',
        size='销售额',
        color='占比差异',
        hover_name=analysis_dimension == '产品' and '产品代码' or '销售员',
        labels={
            '实际占比': '实际销售占比 (%)',
            '预测占比': '预测销售占比 (%)',
            '占比差异': '占比差异 (%)'
        },
        title=f"{selected_region_for_diff} - {analysis_dimension}销售占比差异分析",
        color_continuous_scale='RdBu_r',
        range_color=[-max(abs(diff_data['占比差异'].min()), abs(diff_data['占比差异'].max())), 
                     max(abs(diff_data['占比差异'].min()), abs(diff_data['占比差异'].max()))]
    )
    
    # 添加参考线 (y=x)
    fig_share_diff.add_shape(
        type="line",
        x0=0,
        x1=max(diff_data['实际占比'].max(), diff_data['预测占比'].max()) * 1.1,
        y0=0,
        y1=max(diff_data['实际占比'].max(), diff_data['预测占比'].max()) * 1.1,
        line=dict(color="black", width=1, dash="dash")
    )
    
    fig_share_diff.update_layout(
        xaxis=dict(title="实际销售占比 (%)", tickformat=".1f"),
        yaxis=dict(title="预测销售占比 (%)", tickformat=".1f")
    )
    
    st.plotly_chart(fig_share_diff, use_container_width=True)
    
    # 添加图表解释
    add_chart_explanation(f"""
    <b>图表解读：</b> 此图分析了{selected_region_for_diff}{analysis_dimension}的销售占比差异，横轴是实际销售占比，纵轴是预测销售占比，气泡大小表示销售额，颜色表示占比差异(蓝色表示低估，红色表示高估)。
    位于对角线上的点表示预测占比与实际占比一致；偏离对角线的点表示预测占比与实际占比存在显著差异。占比差异的绝对值平均为{mean_abs_diff:.2f}%。
    <b>行动建议：</b> 对于占比差异较大的{analysis_dimension}，即使总量预测准确，也可能导致库存错配；分析蓝色点(低估)产品是否出现缺货，红色点(高估)产品是否库存积压；调整预测时关注产品组合占比，而非仅关注总量。
    """)
    
    # 占比差异排名
    st.markdown(f'<div class="sub-header">{selected_region_for_diff} - {analysis_dimension}占比差异排名</div>', unsafe_allow_html=True)
    
    # 按占比差异绝对值降序排序
    diff_data_abs_sorted = diff_data.sort_values(by='占比差异', key=abs, ascending=False)
    
    # 创建条形图
    fig_share_diff_ranking = go.Figure()
    
    # 添加占比差异条
    fig_share_diff_ranking.add_trace(go.Bar(
        x=diff_data_abs_sorted[analysis_dimension == '产品' and '产品代码' or '销售员'],
        y=diff_data_abs_sorted['占比差异'],
        marker_color=np.where(diff_data_abs_sorted['占比差异'] >= 0, 'indianred', 'royalblue'),
        text=[f"{x:+.1f}%" for x in diff_data_abs_sorted['占比差异']],
        textposition='outside'
    ))
    
    fig_share_diff_ranking.update_layout(
        title=f"{selected_region_for_diff} - {analysis_dimension}销售占比差异排名",
        xaxis_title=analysis_dimension == '产品' and "产品代码" or "销售员",
        yaxis_title="占比差异 (%)",
        yaxis=dict(zeroline=True)
    )
    
    st.plotly_chart(fig_share_diff_ranking, use_container_width=True)
    
    # 添加解释
    add_chart_explanation(f"""
    <b>图表解读：</b> 此图展示了{selected_region_for_diff}各{analysis_dimension}销售占比差异的排名，红色表示实际占比高于预测(低估)，蓝色表示实际占比低于预测(高估)。
    占比差异大的{analysis_dimension}可能导致库存错配问题，即使总体预测准确也可能出现某些产品积压而其他产品缺货的情况。
    <b>行动建议：</b> 对于占比差异超过±5%的{analysis_dimension}，重点关注并分析原因；对于连续出现在占比差异排名前列的{analysis_dimension}，考虑调整预测方法；在销售预测会议上，不仅讨论总量预测，还要讨论产品结构预测。
    """)
    
    # 销售员-产品差异热图分析
    if selected_region_for_diff != '全国' and analysis_dimension == '销售员':
        st.markdown(f'<div class="sub-header">{selected_region_for_diff} - 销售员产品差异热图</div>', unsafe_allow_html=True)
        
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
            salesperson_data['实际占比'] = salesperson_data['销售额'] / sp_total_actual * 100 if sp_total_actual > 0 else 0
            salesperson_data['预测占比'] = salesperson_data['预测销售额'] / sp_total_forecast * 100 if sp_total_forecast > 0 else 0
            salesperson_data['占比差异'] = salesperson_data['实际占比'] - salesperson_data['预测占比']
            
            # 按销售额降序排序
            salesperson_data = salesperson_data.sort_values('销售额', ascending=False)
            
            # 创建热图数据
            # 获取前10个产品
            top_products = salesperson_data.head(min(10, len(salesperson_data)))
            
            # 创建热图
            fig_heatmap = go.Figure(data=go.Heatmap(
                z=top_products[['实际占比', '预测占比']].values.T,
                x=top_products['产品代码'],
                y=['实际占比', '预测占比'],
                colorscale='RdBu_r',
                zmid=top_products['实际占比'].mean(),  # 中值点，使色标对称
                text=np.around(top_products[['实际占比', '预测占比']].values.T, 1),
                texttemplate="%{text:.1f}%",
                textfont={"size": 10},
                hoverongaps=False
            ))
            
            fig_heatmap.update_layout(
                title=f"{selected_region_for_diff} - {selected_salesperson} 产品占比热图",
                xaxis_title="产品代码",
                yaxis_title="指标"
            )
            
            st.plotly_chart(fig_heatmap, use_container_width=True)
            
            # 创建差异条形图
            fig_sp_diff = px.bar(
                top_products,
                x='产品代码',
                y='占比差异',
                title=f"{selected_salesperson} 产品占比差异",
                color='占比差异',
                color_continuous_scale='RdBu_r',
                text='占比差异'
            )
            
            fig_sp_diff.update_traces(
                texttemplate='%{text:+.1f}%',
                textposition='outside'
            )
            
            fig_sp_diff.update_layout(
                xaxis_title="产品代码",
                yaxis_title="占比差异 (%)",
                yaxis=dict(zeroline=True)
            )
            
            st.plotly_chart(fig_sp_diff, use_container_width=True)
            
            # 添加图表解释
            add_chart_explanation(f"""
            <b>图表解读：</b> 热图展示了{selected_salesperson}销售的主要产品实际销售占比与预测占比的对比，条形图展示了占比差异。
            红色表示实际占比高于预测(低估)，蓝色表示实际占比低于预测(高估)。通过这些分析可以识别销售员在产品结构预测上的偏差模式。
            <b>行动建议：</b> 对于经常被低估的产品(红色)，建议销售员在预测时适当提高比例；对于经常被高估的产品(蓝色)，建议销售员在预测时适当降低比例；销售主管可根据此分析为销售员提供针对性指导。
            """)
        else:
            st.warning(f"{selected_region_for_diff}区域的{selected_salesperson}没有足够的数据进行分析。")

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
    
    st.plotly_chart(fig_trend, use_container_width=True)
    
    # 添加图表解释
    add_chart_explanation(f"""
    <b>图表解读：</b> 此图展示了{selected_region_for_trend}历史销售额(蓝线)与预测销售额(红线)趋势，以及月度差异率(绿线)。
    通过观察趋势可以发现销售的季节性波动、预测与实际的一致性以及差异率的变化趋势。
    <b>行动建议：</b> 分析差异率较大的月份原因；留意差异率的系统性模式(如是否总是低估或高估特定时期的销售)；根据趋势调整预测模型，提高季节性预测的准确性。
    """)
    
    # 产品历史趋势分析
    st.markdown('<div class="sub-header">产品销售历史趋势</div>', unsafe_allow_html=True)
    
    # 选择产品
    all_products = sorted(processed_data['merged_monthly']['产品代码'].unique())
    selected_product = st.selectbox(
        "选择产品查看历史趋势",
        options=all_products
    )
    
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
        product_trend['销售额差异率'] = (product_trend['销售额'] - product_trend['预测销售额']) / product_trend['销售额'] * 100
        product_trend['数量差异率'] = (product_trend['求和项:数量（箱）'] - product_trend['预计销售量']) / product_trend['求和项:数量（箱）'] * 100
        
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
            title=f"{selected_region_for_trend} - {selected_product} 销售额趋势",
            xaxis_title="月份",
            yaxis=dict(title="销售额 (元)", tickformat=",.0f"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
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
            title=f"{selected_region_for_trend} - {selected_product} 销售量趋势",
            xaxis_title="月份",
            yaxis=dict(title="销售量 (箱)"),
            yaxis2=dict(
                title="差异率 (%)",
                overlaying='y',
                side='right'
            ),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig_product_qty, use_container_width=True)
        
        # 添加图表解释
        add_chart_explanation(f"""
        <b>图表解读：</b> 上图展示了{selected_product}产品在{selected_region_for_trend}的销售额历史趋势，下图展示了销售量趋势和差异率。
        可以观察产品销售的季节性波动、预测准确性的变化以及潜在的增长或下降趋势。绿线代表差异率，有助于识别预测偏离较大的时期。
        <b>行动建议：</b> 根据产品历史趋势调整预测策略；关注差异率的系统性模式，如是否在某些特定月份总是高估或低估；如观察到明显的上升或下降趋势，相应调整备货策略。
        """)
        
        # 计算滚动增长率
        if len(product_trend) > 12:
            # 计算12个月同比增长率
            product_trend['销售量_去年同期'] = product_trend['求和项:数量（箱）'].shift(12)
            product_trend['销售量_同比增长率'] = (product_trend['求和项:数量（箱）'] - product_trend['销售量_去年同期']) / product_trend['销售量_去年同期'] * 100
            
            # 创建增长率图表
            fig_growth_rate = px.line(
                product_trend.dropna(subset=['销售量_同比增长率']),
                x='所属年月',
                y='销售量_同比增长率',
                title=f"{selected_product} 销售量同比增长率",
                markers=True
            )
            
            fig_growth_rate.update_layout(
                xaxis_title="月份",
                yaxis=dict(title="增长率 (%)")
            )
            
            # 添加参考线
            fig_growth_rate.add_shape(
                type="line",
                x0=product_trend['所属年月'].min(),
                x1=product_trend['所属年月'].max(),
                y0=0,
                y1=0,
                line=dict(color="black", width=1, dash="dash")
            )
            
            st.plotly_chart(fig_growth_rate, use_container_width=True)
            
            # 添加图表解释
            add_chart_explanation(f"""
            <b>图表解读：</b> 此图展示了{selected_product}产品销售量的同比增长率，反映了产品需求的年度变化趋势。
            正增长率表示相比去年同期销售上升，负增长率表示下降。增长率的波动和趋势变化是判断产品生命周期阶段的重要指标。
            <b>行动建议：</b> 持续正增长的产品应适当增加备货；增长率下滑的产品需关注市场变化并调整销售策略；增长率长期为负的产品应评估是否进入衰退期，相应调整库存策略。
            """)
    else:
        st.warning(f"没有足够的数据来分析{selected_product}产品在{selected_region_for_trend}的历史趋势。")

# 添加页脚信息
st.markdown("""
<div style="margin-top: 50px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; color: #666; font-size: 0.8rem;">
    <p>预测与实际销售对比分析仪表盘 | 版本 1.0.0 | 最后更新: 2025年4月</p>
    <p>使用Streamlit和Plotly构建 | 数据更新频率: 每月</p>
</div>
""", unsafe_allow_html=True)