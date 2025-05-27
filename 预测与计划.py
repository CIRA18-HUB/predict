# pages/预测库存分析.py - 智能库存预警分析系统
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')

# 页面配置
st.set_page_config(
    page_title="智能库存预警系统",
    page_icon="📦",
    layout="wide"
)

# 检查登录状态
if 'authenticated' not in st.session_state or not st.session_state.authenticated:
    st.error("请先登录系统")
    st.switch_page("登陆界面haha.py")
    st.stop()

# 统一的增强CSS样式
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    .stApp {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background-attachment: fixed;
    }
    
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
            radial-gradient(circle at 25% 25%, rgba(255,255,255,0.1) 2px, transparent 2px),
            radial-gradient(circle at 75% 75%, rgba(255,255,255,0.1) 2px, transparent 2px);
        background-size: 100px 100px;
        animation: float 20s linear infinite;
        pointer-events: none;
        z-index: -1;
    }
    
    @keyframes float {
        0% { transform: translateY(0px) translateX(0px); }
        25% { transform: translateY(-20px) translateX(10px); }
        50% { transform: translateY(0px) translateX(-10px); }
        75% { transform: translateY(-10px) translateX(5px); }
        100% { transform: translateY(0px) translateX(0px); }
    }
    
    .main .block-container {
        background: rgba(255,255,255,0.98) !important;
        border-radius: 20px;
        padding: 2rem;
        margin-top: 2rem;
        box-shadow: 0 20px 60px rgba(0,0,0,0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    .page-header {
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #667eea 100%);
        background-size: 200% 200%;
        color: white;
        padding: 3rem 2rem;
        border-radius: 25px;
        margin-bottom: 2rem;
        animation: gradientShift 4s ease infinite, fadeInScale 1.5s ease-out, glow 2s ease-in-out infinite alternate;
        box-shadow: 
            0 20px 40px rgba(102, 126, 234, 0.4),
            0 5px 15px rgba(0,0,0,0.1),
            inset 0 1px 0 rgba(255,255,255,0.1);
        position: relative;
        overflow: hidden;
    }
    
    @keyframes gradientShift {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    @keyframes fadeInScale {
        from { opacity: 0; transform: translateY(-50px) scale(0.8); }
        to { opacity: 1; transform: translateY(0) scale(1); }
    }
    
    @keyframes glow {
        from { box-shadow: 0 20px 40px rgba(102, 126, 234, 0.4), 0 5px 15px rgba(0,0,0,0.1); }
        to { box-shadow: 0 25px 50px rgba(102, 126, 234, 0.6), 0 8px 20px rgba(0,0,0,0.15); }
    }
    
    .page-title {
        font-size: 3.2rem;
        font-weight: 800;
        margin-bottom: 1rem;
        line-height: 1.1;
    }
    
    .page-subtitle {
        font-size: 1.3rem;
        font-weight: 400;
        opacity: 0.9;
    }
    
    /* 统一的卡片容器样式 */
    .metric-card, .analysis-card {
        background: rgba(255,255,255,0.96) !important;
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 1.5rem;
        box-shadow: 
            0 15px 35px rgba(0,0,0,0.08),
            0 5px 15px rgba(0,0,0,0.03),
            inset 0 1px 0 rgba(255,255,255,0.9);
        border: 1px solid rgba(255,255,255,0.3);
        animation: slideUpStagger 1s ease-out;
        backdrop-filter: blur(10px);
        position: relative;
        overflow: hidden;
        transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        border-left: 4px solid #667eea;
    }
    
    .metric-card {
        text-align: center;
        height: 100%;
    }
    
    .metric-card::before, .analysis-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(102, 126, 234, 0.1), transparent);
        transition: left 0.8s ease;
    }
    
    .metric-card:hover, .analysis-card:hover {
        transform: translateY(-10px) scale(1.02);
        box-shadow: 
            0 30px 60px rgba(0,0,0,0.15),
            0 15px 30px rgba(102, 126, 234, 0.2);
        border-color: rgba(102, 126, 234, 0.3);
    }
    
    .metric-card:hover::before, .analysis-card:hover::before {
        left: 100%;
    }
    
    @keyframes slideUpStagger {
        from { opacity: 0; transform: translateY(60px) scale(0.8); }
        to { opacity: 1; transform: translateY(0) scale(1); }
    }
    
    .metric-value {
        font-size: 3.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #667eea 100%);
        background-size: 200% 200%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 1rem;
        animation: textGradient 4s ease infinite;
        line-height: 1;
    }
    
    @keyframes textGradient {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    .metric-label {
        color: #374151 !important;
        font-size: 1.1rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }
    
    .metric-description {
        color: #6b7280 !important;
        font-size: 0.9rem;
        margin-top: 0.8rem;
        font-weight: 500;
        font-style: italic;
    }
    
    .chart-title {
        font-size: 1.4rem;
        font-weight: 700;
        color: #333 !important;
        margin-bottom: 1rem;
        text-align: center;
        background: linear-gradient(45deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .insight-box {
        background: rgba(255,255,255,0.96) !important;
        border-left: 4px solid #667eea;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: #333 !important;
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
    }
    
    .insight-box:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 25px rgba(102, 126, 234, 0.15);
    }
    
    .insight-title {
        font-weight: 700;
        color: #333 !important;
        margin-bottom: 0.8rem;
        font-size: 1.1rem;
    }
    
    .insight-content {
        color: #666 !important;
        line-height: 1.6;
        font-size: 1rem;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 15px;
        background: rgba(248, 250, 252, 0.95) !important;
        padding: 1rem;
        border-radius: 20px;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.06), 0 4px 8px rgba(0,0,0,0.04);
        backdrop-filter: blur(10px);
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 65px;
        padding: 0 35px;
        background: rgba(255,255,255,0.95) !important;
        border-radius: 15px;
        border: 1px solid rgba(102, 126, 234, 0.15);
        font-weight: 700;
        font-size: 1rem;
        transition: all 0.4s ease;
        position: relative;
        overflow: hidden;
        box-shadow: 0 4px 8px rgba(0,0,0,0.05);
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        transform: translateY(-5px) scale(1.05);
        box-shadow: 0 15px 30px rgba(102, 126, 234, 0.2);
        border-color: rgba(102, 126, 234, 0.4);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none;
        transform: translateY(-3px) scale(1.02);
        box-shadow: 0 15px 40px rgba(102, 126, 234, 0.4), 0 5px 15px rgba(0,0,0,0.1);
    }
    
    /* 特殊风险等级颜色 */
    .risk-extreme { border-left-color: #ff4757 !important; }
    .risk-high { border-left-color: #ff6348 !important; }
    .risk-medium { border-left-color: #ffa502 !important; }
    .risk-low { border-left-color: #2ed573 !important; }
    .risk-minimal { border-left-color: #5352ed !important; }
    
    /* 页脚样式优化 */
    .footer-text {
        text-align: center;
        color: rgba(255, 255, 255, 0.8) !important;
        font-family: "Inter", sans-serif;
        font-size: 0.8rem !important;
        margin-top: 2rem;
        padding: 1rem;
        background: rgba(102, 126, 234, 0.1);
        border-radius: 10px;
        backdrop-filter: blur(5px);
    }
    
    /* 动画延迟 */
    .metric-card:nth-child(1) { animation-delay: 0.1s; }
    .metric-card:nth-child(2) { animation-delay: 0.2s; }
    .metric-card:nth-child(3) { animation-delay: 0.3s; }
    .metric-card:nth-child(4) { animation-delay: 0.4s; }
    
    /* 响应式设计 */
    @media (max-width: 768px) {
        .metric-value { font-size: 2.5rem; }
        .metric-card { padding: 2rem 1.5rem; }
        .page-header { padding: 2rem 1rem; }
        .page-title { font-size: 2.5rem; }
    }
</style>
""", unsafe_allow_html=True)

# 配色方案
COLOR_SCHEME = {
    'primary': '#667eea',
    'secondary': '#764ba2', 
    'risk_extreme': '#ff4757',
    'risk_high': '#ff6348',
    'risk_medium': '#ffa502',
    'risk_low': '#2ed573',
    'risk_minimal': '#5352ed',
    'chart_colors': ['#667eea', '#ff6b9d', '#c44569', '#ffc75f', '#f8b500', '#845ec2', '#4e8397', '#00c9a7']
}

# 数据加载函数
@st.cache_data
def load_and_process_data():
    """加载和处理所有数据"""
    # 读取数据文件
    shipment_df = pd.read_excel('2409~250224出货数据.xlsx')
    forecast_df = pd.read_excel('2409~2502人工预测.xlsx') 
    inventory_df = pd.read_excel('含批次库存0221(2).xlsx')
    price_df = pd.read_excel('单价.xlsx')
    
    # 处理日期
    shipment_df['订单日期'] = pd.to_datetime(shipment_df['订单日期'])
    forecast_df['所属年月'] = pd.to_datetime(forecast_df['所属年月'], format='%Y-%m')
    
    # 创建产品代码到名称的映射
    product_name_map = {}
    for idx, row in inventory_df.iterrows():
        if pd.notna(row['物料']) and pd.notna(row['描述']) and isinstance(row['物料'], str) and row['物料'].startswith('F'):
            product_name_map[row['物料']] = row['描述']
    
    # 处理库存数据
    batch_data = []
    current_material = None
    current_desc = None
    current_price = 0
    
    for idx, row in inventory_df.iterrows():
        if pd.notna(row['物料']) and isinstance(row['物料'], str) and row['物料'].startswith('F'):
            current_material = row['物料']
            current_desc = row['描述']
            price_match = price_df[price_df['产品代码'] == current_material]
            current_price = price_match['单价'].iloc[0] if len(price_match) > 0 else 100
        elif pd.notna(row['生产日期']) and current_material:
            prod_date = pd.to_datetime(row['生产日期'])
            quantity = row['数量'] if pd.notna(row['数量']) else 0
            batch_no = row['生产批号'] if pd.notna(row['生产批号']) else ''
            
            age_days = (datetime.now() - prod_date).days
            
            if age_days >= 120:
                risk_level = '极高风险'
                risk_color = COLOR_SCHEME['risk_extreme']
                risk_advice = '🚨 立即7折清库'
            elif age_days >= 90:
                risk_level = '高风险'
                risk_color = COLOR_SCHEME['risk_high'] 
                risk_advice = '⚠️ 建议8折促销'
            elif age_days >= 60:
                risk_level = '中风险'
                risk_color = COLOR_SCHEME['risk_medium']
                risk_advice = '📢 适度9折促销'
            elif age_days >= 30:
                risk_level = '低风险'
                risk_color = COLOR_SCHEME['risk_low']
                risk_advice = '✅ 正常销售'
            else:
                risk_level = '极低风险'
                risk_color = COLOR_SCHEME['risk_minimal']
                risk_advice = '🌟 新鲜库存'
            
            if age_days >= 120:
                expected_loss = quantity * current_price * 0.3
            elif age_days >= 90:
                expected_loss = quantity * current_price * 0.2
            elif age_days >= 60:
                expected_loss = quantity * current_price * 0.1
            else:
                expected_loss = 0
            
            batch_data.append({
                '物料': current_material,
                '产品名称': current_desc,
                '生产日期': prod_date,
                '生产批号': batch_no,
                '数量': quantity,
                '库龄': age_days,
                '风险等级': risk_level,
                '风险颜色': risk_color,
                '处理建议': risk_advice,
                '单价': current_price,
                '批次价值': quantity * current_price,
                '预期损失': expected_loss
            })
    
    processed_inventory = pd.DataFrame(batch_data)
    forecast_accuracy = calculate_forecast_accuracy(shipment_df, forecast_df)
    metrics = calculate_key_metrics(processed_inventory, forecast_accuracy)
    
    return processed_inventory, forecast_accuracy, shipment_df, forecast_df, metrics, product_name_map

def calculate_forecast_accuracy(shipment_df, forecast_df):
    """计算预测准确率"""
    try:
        shipment_monthly = shipment_df.groupby([
            shipment_df['订单日期'].dt.to_period('M'),
            '产品代码'
        ])['求和项:数量（箱）'].sum().reset_index()
        shipment_monthly['年月'] = shipment_monthly['订单日期'].dt.to_timestamp()
        
        merged = forecast_df.merge(
            shipment_monthly,
            left_on=['所属年月', '产品代码'],
            right_on=['年月', '产品代码'],
            how='inner'
        )
        
        merged['预测误差'] = abs(merged['预计销售量'] - merged['求和项:数量（箱）'])
        merged['预测准确率'] = 1 - (merged['预测误差'] / (merged['求和项:数量（箱）'] + 1))
        merged['预测准确率'] = merged['预测准确率'].clip(0, 1)
        
        return merged
    except:
        return pd.DataFrame()

def calculate_key_metrics(processed_inventory, forecast_accuracy):
    """计算关键指标"""
    total_batches = len(processed_inventory)
    high_risk_batches = len(processed_inventory[processed_inventory['风险等级'].isin(['极高风险', '高风险'])])
    high_risk_ratio = (high_risk_batches / total_batches * 100) if total_batches > 0 else 0
    
    total_inventory_value = processed_inventory['批次价值'].sum() / 1000000
    high_risk_value = processed_inventory[
        processed_inventory['风险等级'].isin(['极高风险', '高风险'])
    ]['批次价值'].sum()
    high_risk_value_ratio = (high_risk_value / processed_inventory['批次价值'].sum() * 100) if processed_inventory['批次价值'].sum() > 0 else 0
    
    avg_age = processed_inventory['库龄'].mean()
    forecast_acc = forecast_accuracy['预测准确率'].mean() * 100 if not forecast_accuracy.empty else 0
    
    risk_counts = processed_inventory['风险等级'].value_counts().to_dict()
    
    return {
        'total_batches': int(total_batches),
        'high_risk_batches': int(high_risk_batches),
        'high_risk_ratio': round(high_risk_ratio, 1),
        'total_inventory_value': round(total_inventory_value, 2),
        'high_risk_value_ratio': round(high_risk_value_ratio, 1),
        'avg_age': round(avg_age, 0),
        'forecast_accuracy': round(forecast_acc, 1) if forecast_acc > 0 else 0,
        'high_risk_value': round(high_risk_value / 1000000, 1),
        'risk_counts': {
            'extreme': risk_counts.get('极高风险', 0),
            'high': risk_counts.get('高风险', 0),
            'medium': risk_counts.get('中风险', 0),
            'low': risk_counts.get('低风险', 0),
            'minimal': risk_counts.get('极低风险', 0)
        }
    }

# 预测分析相关函数
def process_forecast_data(shipment_df, forecast_df):
    """处理预测数据"""
    # 转换日期格式
    shipment_df['所属年月'] = shipment_df['订单日期'].dt.strftime('%Y-%m')
    forecast_df['所属年月'] = forecast_df['所属年月'].dt.strftime('%Y-%m')
    
    # 按月份、区域、产品码汇总数据
    actual_monthly = shipment_df.groupby(['所属年月', '所属区域', '产品代码']).agg({
        '求和项:数量（箱）': 'sum'
    }).reset_index()

    forecast_monthly = forecast_df.groupby(['所属年月', '所属区域', '产品代码']).agg({
        '预计销售量': 'sum'
    }).reset_index()

    # 合并数据
    merged_monthly = pd.merge(
        actual_monthly,
        forecast_monthly,
        on=['所属年月', '所属区域', '产品代码'],
        how='outer'
    ).fillna(0)

    # 计算准确率
    merged_monthly['数量准确率'] = merged_monthly.apply(
        lambda row: max(0, 1 - abs(row['求和项:数量（箱）'] - row['预计销售量']) / (row['求和项:数量（箱）'] + 1)),
        axis=1
    )

    return merged_monthly

def create_risk_analysis_dashboard(processed_inventory):
    """创建紧凑的风险分析仪表盘"""
    # 风险分布数据
    risk_counts = processed_inventory['风险等级'].value_counts()
    risk_value = processed_inventory.groupby('风险等级')['批次价值'].sum() / 1000000
    
    colors = [COLOR_SCHEME['risk_extreme'], COLOR_SCHEME['risk_high'], 
              COLOR_SCHEME['risk_medium'], COLOR_SCHEME['risk_low'], COLOR_SCHEME['risk_minimal']]
    
    # 创建2x2子图
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("风险等级分布", "各风险等级价值分布", "库存批次库龄分布", "高风险批次分析"),
        specs=[[{"type": "pie"}, {"type": "bar"}],
               [{"type": "histogram"}, {"type": "scatter"}]],
        vertical_spacing=0.12,
        horizontal_spacing=0.1
    )
    
    # 1. 风险等级分布饼图
    fig.add_trace(go.Pie(
        labels=risk_counts.index,
        values=risk_counts.values,
        hole=.4,
        marker_colors=colors,
        textinfo='label+percent',
        showlegend=False
    ), row=1, col=1)
    
    # 2. 风险等级价值分布
    fig.add_trace(go.Bar(
        x=risk_value.index,
        y=risk_value.values,
        marker_color=colors,
        text=[f'¥{v:.1f}M' for v in risk_value.values],
        textposition='auto',
        showlegend=False
    ), row=1, col=2)
    
    # 3. 库龄分布直方图
    fig.add_trace(go.Histogram(
        x=processed_inventory['库龄'],
        nbinsx=15,
        marker_color=COLOR_SCHEME['primary'],
        opacity=0.7,
        showlegend=False
    ), row=2, col=1)
    
    # 4. 高风险批次散点图
    high_risk_data = processed_inventory[
        processed_inventory['风险等级'].isin(['极高风险', '高风险'])
    ].head(20)
    
    if not high_risk_data.empty:
        fig.add_trace(go.Scatter(
            x=high_risk_data['库龄'],
            y=high_risk_data['批次价值'],
            mode='markers',
            marker=dict(
                size=np.clip(high_risk_data['数量']/15, 8, 30),
                color=high_risk_data['风险等级'].map({
                    '极高风险': COLOR_SCHEME['risk_extreme'],
                    '高风险': COLOR_SCHEME['risk_high']
                }),
                opacity=0.8,
                line=dict(width=1, color='white')
            ),
            text=high_risk_data['产品名称'],
            showlegend=False
        ), row=2, col=2)
    
    # 更新布局
    fig.update_layout(
        height=700,
        title_text="库存风险综合分析仪表盘",
        title_x=0.5,
        title_font=dict(size=20, color='#333'),
        showlegend=False
    )
    
    # 添加库龄阈值线
    fig.add_vline(x=30, line_dash="dash", line_color=COLOR_SCHEME['risk_low'], row=2, col=1)
    fig.add_vline(x=60, line_dash="dash", line_color=COLOR_SCHEME['risk_medium'], row=2, col=1)
    fig.add_vline(x=90, line_dash="dash", line_color=COLOR_SCHEME['risk_high'], row=2, col=1)
    fig.add_vline(x=120, line_dash="dash", line_color=COLOR_SCHEME['risk_extreme'], row=2, col=1)
    
    return fig

def create_forecast_dashboard(merged_data):
    """创建预测分析仪表盘 - 按照附件维度"""
    # 计算各项指标
    # 1. 全国准确率趋势
    monthly_national = merged_data.groupby('所属年月').agg({
        '求和项:数量（箱）': 'sum',
        '预计销售量': 'sum'
    }).reset_index()
    monthly_national['准确率'] = monthly_national.apply(
        lambda row: max(0, 1 - abs(row['求和项:数量（箱）'] - row['预计销售量']) / (row['求和项:数量（箱）'] + 1)) * 100,
        axis=1
    )
    
    # 2. 区域准确率对比
    regional_accuracy = merged_data.groupby('所属区域').agg({
        '求和项:数量（箱）': 'sum',
        '预计销售量': 'sum'
    }).reset_index()
    regional_accuracy['准确率'] = regional_accuracy.apply(
        lambda row: max(0, 1 - abs(row['求和项:数量（箱）'] - row['预计销售量']) / (row['求和项:数量（箱）'] + 1)) * 100,
        axis=1
    )
    
    # 3. 产品准确率分析
    product_accuracy = merged_data.groupby('产品代码').agg({
        '求和项:数量（箱）': 'sum',
        '预计销售量': 'sum'
    }).reset_index()
    product_accuracy['准确率'] = product_accuracy.apply(
        lambda row: max(0, 1 - abs(row['求和项:数量（箱）'] - row['预计销售量']) / (row['求和项:数量（箱）'] + 1)) * 100,
        axis=1
    )
    product_accuracy = product_accuracy.nlargest(10, '求和项:数量（箱）')
    
    # 4. 预测准确率分布
    accuracy_distribution = merged_data['数量准确率'] * 100
    
    # 创建2x2子图布局
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("预测准确率月度趋势", "各区域预测准确率对比", "TOP10产品预测准确率", "预测准确率分布"),
        specs=[[{"type": "scatter"}, {"type": "bar"}],
               [{"type": "bar"}, {"type": "histogram"}]],
        vertical_spacing=0.12,
        horizontal_spacing=0.1
    )
    
    # 1. 月度趋势
    fig.add_trace(go.Scatter(
        x=monthly_national['所属年月'],
        y=monthly_national['准确率'],
        mode='lines+markers',
        name='准确率',
        line=dict(color=COLOR_SCHEME['primary'], width=3),
        marker=dict(size=8),
        showlegend=False
    ), row=1, col=1)
    
    # 添加目标线
    fig.add_hline(y=85, line_dash="dash", line_color="red", row=1, col=1)
    
    # 2. 区域对比
    colors_regional = [COLOR_SCHEME['risk_low'] if acc > 85 else 
                      COLOR_SCHEME['risk_medium'] if acc > 75 else 
                      COLOR_SCHEME['risk_high'] for acc in regional_accuracy['准确率']]
    
    fig.add_trace(go.Bar(
        x=regional_accuracy['所属区域'],
        y=regional_accuracy['准确率'],
        marker_color=colors_regional,
        text=[f'{acc:.1f}%' for acc in regional_accuracy['准确率']],
        textposition='auto',
        showlegend=False
    ), row=1, col=2)
    
    fig.add_hline(y=85, line_dash="dash", line_color="red", row=1, col=2)
    
    # 3. 产品准确率
    colors_product = [COLOR_SCHEME['risk_low'] if acc > 85 else 
                     COLOR_SCHEME['risk_medium'] if acc > 75 else 
                     COLOR_SCHEME['risk_high'] for acc in product_accuracy['准确率']]
    
    fig.add_trace(go.Bar(
        y=product_accuracy['产品代码'],
        x=product_accuracy['准确率'],
        orientation='h',
        marker_color=colors_product,
        text=[f'{acc:.1f}%' for acc in product_accuracy['准确率']],
        textposition='auto',
        showlegend=False
    ), row=2, col=1)
    
    # 4. 准确率分布
    fig.add_trace(go.Histogram(
        x=accuracy_distribution,
        nbinsx=20,
        marker_color=COLOR_SCHEME['secondary'],
        opacity=0.7,
        showlegend=False
    ), row=2, col=2)
    
    # 更新布局
    fig.update_layout(
        height=700,
        title_text="销售预测准确性综合分析仪表盘",
        title_x=0.5,
        title_font=dict(size=20, color='#333'),
        showlegend=False
    )
    
    return fig

# 加载数据
with st.spinner('🔄 正在加载数据...'):
    processed_inventory, forecast_accuracy, shipment_df, forecast_df, metrics, product_name_map = load_and_process_data()

# 页面标题
st.markdown("""
<div class="page-header">
    <h1 class="page-title">📦 智能库存预警分析系统</h1>
    <p class="page-subtitle">数据驱动的库存风险管理与预测分析决策支持平台</p>
</div>
""", unsafe_allow_html=True)

# 创建标签页
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 核心指标总览",
    "🎯 风险分布分析", 
    "💡 销售预测准确性分析",
    "📋 批次详情"
])

# 标签1：核心指标总览
with tab1:
    st.markdown("### 🎯 关键绩效指标")
    
    # 指标卡片 - 紧凑布局
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{metrics['total_batches']:,}</div>
            <div class="metric-label">📦 总批次数</div>
            <div class="metric-description">当前库存批次总数</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        health_score = 100 - metrics['high_risk_ratio']
        health_class = "risk-low" if health_score > 80 else "risk-medium" if health_score > 60 else "risk-high"
        st.markdown(f"""
        <div class="metric-card {health_class}">
            <div class="metric-value">{health_score:.1f}%</div>
            <div class="metric-label">💚 库存健康度</div>
            <div class="metric-description">{'健康' if health_score > 80 else '需关注' if health_score > 60 else '风险'}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">¥{metrics['total_inventory_value']:.1f}M</div>
            <div class="metric-label">💰 库存总价值</div>
            <div class="metric-description">全部库存价值统计</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        risk_class = "risk-extreme" if metrics['high_risk_ratio'] > 25 else "risk-high" if metrics['high_risk_ratio'] > 15 else "risk-medium"
        st.markdown(f"""
        <div class="metric-card {risk_class}">
            <div class="metric-value">{metrics['high_risk_ratio']:.1f}%</div>
            <div class="metric-label">⚠️ 高风险占比</div>
            <div class="metric-description">需要紧急处理的批次</div>
        </div>
        """, unsafe_allow_html=True)
    
    # 第二行指标
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        age_class = "risk-extreme" if metrics['avg_age'] > 90 else "risk-high" if metrics['avg_age'] > 60 else "risk-medium" if metrics['avg_age'] > 30 else "risk-low"
        st.markdown(f"""
        <div class="metric-card {age_class}">
            <div class="metric-value">{metrics['avg_age']:.0f}天</div>
            <div class="metric-label">⏰ 平均库龄</div>
            <div class="metric-description">库存批次平均天数</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col6:
        forecast_class = "risk-low" if metrics['forecast_accuracy'] > 85 else "risk-medium" if metrics['forecast_accuracy'] > 75 else "risk-high"
        st.markdown(f"""
        <div class="metric-card {forecast_class}">
            <div class="metric-value">{metrics['forecast_accuracy']:.1f}%</div>
            <div class="metric-label">🎯 预测准确率</div>
            <div class="metric-description">销售预测精度水平</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col7:
        st.markdown(f"""
        <div class="metric-card risk-extreme">
            <div class="metric-value">¥{metrics['high_risk_value']:.1f}M</div>
            <div class="metric-label">🚨 高风险价值</div>
            <div class="metric-description">高风险批次总价值</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col8:
        turnover_rate = 365 / metrics['avg_age'] if metrics['avg_age'] > 0 else 0
        turnover_class = "risk-low" if turnover_rate > 10 else "risk-medium" if turnover_rate > 6 else "risk-high"
        st.markdown(f"""
        <div class="metric-card {turnover_class}">
            <div class="metric-value">{turnover_rate:.1f}</div>
            <div class="metric-label">🔄 周转率</div>
            <div class="metric-description">年库存周转次数</div>
        </div>
        """, unsafe_allow_html=True)

# 标签2：风险分布分析 - 紧凑布局
with tab2:
    st.markdown("### 🎯 库存风险分布全景分析")
    
    # 单个紧凑的仪表盘
    st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
    risk_dashboard = create_risk_analysis_dashboard(processed_inventory)
    st.plotly_chart(risk_dashboard, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 关键洞察
    st.markdown(f"""
    <div class="insight-box">
        <div class="insight-title">📊 综合风险分析洞察</div>
        <div class="insight-content">
            • <strong>风险分布：</strong>极高风险 {metrics['risk_counts']['extreme']}个批次 ({metrics['risk_counts']['extreme']/metrics['total_batches']*100:.1f}%)，高风险 {metrics['risk_counts']['high']}个批次 ({metrics['risk_counts']['high']/metrics['total_batches']*100:.1f}%)<br>
            • <strong>价值影响：</strong>高风险批次价值占比 {metrics['high_risk_value_ratio']:.1f}%，总计¥{metrics['high_risk_value']:.1f}M<br>
            • <strong>紧急建议：</strong>立即处理极高风险批次，通过7-8折促销预计可回收资金¥{metrics['high_risk_value']*0.8:.1f}M<br>
            • <strong>优先级：</strong>右上角气泡图显示高库龄高价值批次应优先处理，气泡大小代表数量
        </div>
    </div>
    """, unsafe_allow_html=True)

# 标签3：预测准确性分析 - 完全按照附件维度
with tab3:
    st.markdown("### 📈 销售预测准确性综合分析")
    
    # 处理预测数据
    if not forecast_accuracy.empty and not shipment_df.empty and not forecast_df.empty:
        merged_data = process_forecast_data(shipment_df, forecast_df)
        
        if not merged_data.empty:
            # 计算关键指标
            total_actual = merged_data['求和项:数量（箱）'].sum()
            total_forecast = merged_data['预计销售量'].sum()
            overall_accuracy = max(0, 1 - abs(total_actual - total_forecast) / (total_actual + 1)) * 100
            
            # 关键指标展示
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{total_actual:,.0f}</div>
                    <div class="metric-label">📊 实际销售量</div>
                    <div class="metric-description">总销量(箱)</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{total_forecast:,.0f}</div>
                    <div class="metric-label">🎯 预测销售量</div>
                    <div class="metric-description">总预测(箱)</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                accuracy_class = "risk-low" if overall_accuracy > 85 else "risk-medium" if overall_accuracy > 75 else "risk-high"
                st.markdown(f"""
                <div class="metric-card {accuracy_class}">
                    <div class="metric-value">{overall_accuracy:.1f}%</div>
                    <div class="metric-label">🎯 整体准确率</div>
                    <div class="metric-description">全国预测精度</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                improvement_potential = max(0, 85 - overall_accuracy)
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{improvement_potential:.1f}%</div>
                    <div class="metric-label">📈 提升空间</div>
                    <div class="metric-description">距离目标85%</div>
                </div>
                """, unsafe_allow_html=True)
            
            # 预测分析仪表盘
            st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
            forecast_dashboard = create_forecast_dashboard(merged_data)
            st.plotly_chart(forecast_dashboard, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # 改进建议
            st.markdown(f"""
            <div class="insight-box">
                <div class="insight-title">💡 预测改进建议</div>
                <div class="insight-content">
                    • <strong>整体表现：</strong>当前准确率{overall_accuracy:.1f}%，{'已达到目标' if overall_accuracy >= 85 else '需要改进'}<br>
                    • <strong>重点关注：</strong>加强季节性因子分析，提升历史数据权重<br>
                    • <strong>区域优化：</strong>针对准确率低于75%的区域制定专项改进计划<br>
                    • <strong>产品优化：</strong>重点提升TOP10产品的预测精度，增加市场趋势调研
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("数据处理中，暂无可分析的预测数据")
    else:
        st.warning("缺少必要的预测数据文件，请检查数据源")

# 标签4：批次详情
with tab4:
    st.markdown("### 📋 库存批次详细信息")
    
    # 筛选器
    st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        risk_filter = st.selectbox(
            "选择风险等级",
            options=['全部'] + list(processed_inventory['风险等级'].unique()),
            index=0
        )
    
    with col2:
        min_value = st.number_input(
            "最小批次价值",
            min_value=0,
            max_value=int(processed_inventory['批次价值'].max()),
            value=0
        )
    
    with col3:
        max_age = st.number_input(
            "最大库龄(天)",
            min_value=0,
            max_value=int(processed_inventory['库龄'].max()),
            value=int(processed_inventory['库龄'].max())
        )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 应用筛选
    filtered_data = processed_inventory.copy()
    
    if risk_filter != '全部':
        filtered_data = filtered_data[filtered_data['风险等级'] == risk_filter]
    
    filtered_data = filtered_data[
        (filtered_data['批次价值'] >= min_value) &
        (filtered_data['库龄'] <= max_age)
    ]
    
    # 筛选结果
    st.markdown(f"""
    <div class="insight-box">
        <div class="insight-title">📊 筛选结果统计</div>
        <div class="insight-content">
            筛选出 <strong>{len(filtered_data)}</strong> 个批次，总价值 <strong>¥{filtered_data['批次价值'].sum()/1000000:.2f}M</strong>，
            平均库龄 <strong>{filtered_data['库龄'].mean():.0f}</strong> 天
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 数据表格
    if not filtered_data.empty:
        st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
        display_columns = ['物料', '产品名称', '生产日期', '生产批号', '数量', '库龄', '风险等级', '批次价值', '处理建议']
        display_data = filtered_data[display_columns].copy()
        
        display_data['批次价值'] = display_data['批次价值'].apply(lambda x: f"¥{x:,.0f}")
        display_data['生产日期'] = display_data['生产日期'].dt.strftime('%Y-%m-%d')
        
        risk_order = {'极高风险': 0, '高风险': 1, '中风险': 2, '低风险': 3, '极低风险': 4}
        display_data['风险排序'] = display_data['风险等级'].map(risk_order)
        display_data = display_data.sort_values(['风险排序', '库龄'], ascending=[True, False])
        display_data = display_data.drop('风险排序', axis=1)
        
        st.dataframe(display_data, use_container_width=True, height=400)
        
        csv = display_data.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 下载筛选结果",
            data=csv,
            file_name=f"库存分析_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("没有符合筛选条件的数据")

# 页脚
st.markdown("---")
st.markdown(
    f"""
    <div class="footer-text">
        <p>🚀 Powered by Streamlit & Plotly | 智能数据分析平台 | 最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    </div>
    """,
    unsafe_allow_html=True
)
