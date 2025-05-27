# pages/预测库存分析.py - 智能库存预警分析系统（优化版）
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
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

# 统一的增强CSS样式 - 优化版
st.markdown("""
<style>
    /* 导入Google字体 */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* 全局字体和背景 */
    .stApp {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background-attachment: fixed;
    }
    
    /* 添加浮动粒子背景动画 */
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
    
    /* 主容器背景 */
    .main .block-container {
        background: rgba(255,255,255,0.98) !important;
        border-radius: 20px;
        padding: 2rem;
        margin-top: 2rem;
        box-shadow: 0 20px 60px rgba(0,0,0,0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    /* 页面标题样式 */
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
        transform: perspective(1000px) rotateX(0deg);
        transition: transform 0.3s ease;
    }
    
    .page-header:hover {
        transform: perspective(1000px) rotateX(-2deg) scale(1.02);
        box-shadow: 
            0 25px 50px rgba(102, 126, 234, 0.5),
            0 10px 30px rgba(0,0,0,0.15);
    }
    
    .page-header::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(45deg, transparent, rgba(255,255,255,0.15), transparent);
        animation: shimmer 3s linear infinite;
    }
    
    .page-header::after {
        content: '✨';
        position: absolute;
        top: 10%;
        right: 10%;
        font-size: 2rem;
        animation: sparkle 1.5s ease-in-out infinite;
    }
    
    @keyframes glow {
        from { box-shadow: 0 20px 40px rgba(102, 126, 234, 0.4), 0 5px 15px rgba(0,0,0,0.1); }
        to { box-shadow: 0 25px 50px rgba(102, 126, 234, 0.6), 0 8px 20px rgba(0,0,0,0.15); }
    }
    
    @keyframes sparkle {
        0%, 100% { transform: scale(1) rotate(0deg); opacity: 1; }
        50% { transform: scale(1.3) rotate(180deg); opacity: 0.7; }
    }
    
    @keyframes gradientShift {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    @keyframes shimmer {
        0% { transform: translateX(-100%) translateY(-100%) rotate(45deg); }
        100% { transform: translateX(100%) translateY(100%) rotate(45deg); }
    }
    
    @keyframes fadeInScale {
        from { 
            opacity: 0; 
            transform: translateY(-50px) scale(0.8) rotateX(-10deg); 
        }
        to { 
            opacity: 1; 
            transform: translateY(0) scale(1) rotateX(0deg); 
        }
    }
    
    .page-title {
        font-size: 3.2rem;
        font-weight: 800;
        margin-bottom: 1rem;
        line-height: 1.1;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .page-subtitle {
        font-size: 1.3rem;
        font-weight: 400;
        opacity: 0.9;
        margin-top: 0.5rem;
    }
    
    /* 指标卡片样式 */
    .metric-card {
        background: rgba(255,255,255,0.95) !important;
        padding: 2.5rem 2rem;
        border-radius: 25px;
        box-shadow: 
            0 15px 35px rgba(0,0,0,0.08),
            0 5px 15px rgba(0,0,0,0.03),
            inset 0 1px 0 rgba(255,255,255,0.9);
        text-align: center;
        height: 100%;
        transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        animation: slideUpStagger 1s ease-out;
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(255,255,255,0.3);
        backdrop-filter: blur(10px);
        border-left: 4px solid #667eea;
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(102, 126, 234, 0.1), transparent);
        transition: left 0.8s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-15px) scale(1.05) rotateY(5deg);
        box-shadow: 
            0 30px 60px rgba(0,0,0,0.15),
            0 15px 30px rgba(102, 126, 234, 0.2);
        border-color: rgba(102, 126, 234, 0.3);
        animation: pulse 1.5s infinite;
    }
    
    .metric-card:hover::before {
        left: 100%;
    }
    
    @keyframes slideUpStagger {
        from { 
            opacity: 0; 
            transform: translateY(60px) scale(0.8) rotateX(-15deg); 
        }
        to { 
            opacity: 1; 
            transform: translateY(0) scale(1) rotateX(0deg); 
        }
    }
    
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(102, 126, 234, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(102, 126, 234, 0); }
        100% { box-shadow: 0 0 0 0 rgba(102, 126, 234, 0); }
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
        animation: textGradient 4s ease infinite, bounce 2s ease-in-out infinite;
        line-height: 1;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    @keyframes bounce {
        0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
        40% { transform: translateY(-3px); }
        60% { transform: translateY(-2px); }
    }
    
    @keyframes textGradient {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    .metric-label {
        color: #374151;
        font-size: 1.1rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }
    
    .metric-description {
        color: #6b7280;
        font-size: 0.9rem;
        margin-top: 0.8rem;
        font-weight: 500;
        font-style: italic;
    }
    
    /* 图表容器样式 - 优化版 */
    .chart-container {
        background: rgba(255,255,255,0.96) !important;
        border-radius: 20px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 
            0 10px 25px rgba(0,0,0,0.06),
            0 4px 10px rgba(0,0,0,0.03);
        border: 1px solid rgba(255,255,255,0.3);
        animation: chartFadeIn 1.2s ease-out;
        backdrop-filter: blur(10px);
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
        border-left: 3px solid #667eea;
    }
    
    .chart-container:hover {
        transform: translateY(-5px);
        box-shadow: 
            0 15px 35px rgba(0,0,0,0.1),
            0 8px 15px rgba(102, 126, 234, 0.15);
        border-left-color: #764ba2;
    }
    
    @keyframes chartFadeIn {
        from { 
            opacity: 0; 
            transform: translateY(20px); 
        }
        to { 
            opacity: 1; 
            transform: translateY(0); 
        }
    }
    
    .chart-title {
        font-size: 1.4rem;
        font-weight: 700;
        color: #333;
        margin-bottom: 1rem;
        text-align: center;
        background: linear-gradient(45deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* 洞察框样式 */
    .insight-box {
        background: rgba(255,255,255,0.96) !important;
        border-left: 4px solid #667eea;
        border-radius: 15px;
        padding: 1.5rem;
        margin-top: 1rem;
        box-shadow: 0 8px 20px rgba(0,0,0,0.06);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.3);
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
    }
    
    .insight-box:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 25px rgba(102, 126, 234, 0.15);
        border-color: rgba(102, 126, 234, 0.4);
    }
    
    .insight-title {
        font-weight: 700;
        color: #333;
        margin-bottom: 0.8rem;
        font-size: 1.1rem;
    }
    
    .insight-content {
        color: #666;
        line-height: 1.6;
        font-size: 1rem;
    }
    
    /* 标签页样式增强 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 15px;
        background: rgba(248, 250, 252, 0.95) !important;
        padding: 1rem;
        border-radius: 20px;
        box-shadow: 
            inset 0 2px 4px rgba(0,0,0,0.06),
            0 4px 8px rgba(0,0,0,0.04);
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
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
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
        color: white;
        border: none;
        transform: translateY(-3px) scale(1.02);
        box-shadow: 
            0 15px 40px rgba(102, 126, 234, 0.4),
            0 5px 15px rgba(0,0,0,0.1);
        animation: activeTab 0.5s ease;
    }
    
    @keyframes activeTab {
        0% { transform: scale(0.95); }
        50% { transform: scale(1.1); }
        100% { transform: scale(1.02); }
    }
    
    /* 页脚样式 - 修改为白色小字体 */
    .footer-text {
        text-align: center;
        color: rgba(255, 255, 255, 0.8) !important;
        font-family: "Inter", sans-serif;
        font-size: 0.75rem !important;
        margin-top: 2rem;
        padding: 1rem;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* 动画卡片延迟 */
    .metric-card:nth-child(1) { animation-delay: 0.1s; }
    .metric-card:nth-child(2) { animation-delay: 0.2s; }
    .metric-card:nth-child(3) { animation-delay: 0.3s; }
    .metric-card:nth-child(4) { animation-delay: 0.4s; }
    .metric-card:nth-child(5) { animation-delay: 0.5s; }
    .metric-card:nth-child(6) { animation-delay: 0.6s; }
    .metric-card:nth-child(7) { animation-delay: 0.7s; }
    .metric-card:nth-child(8) { animation-delay: 0.8s; }
    
    /* 响应式设计 */
    @media (max-width: 768px) {
        .metric-value {
            font-size: 2.5rem;
        }
        .metric-card {
            padding: 2rem 1.5rem;
        }
        .page-header {
            padding: 2rem 1rem;
        }
        .page-title {
            font-size: 2.5rem;
        }
    }
    
    /* 特殊风险等级颜色 */
    .risk-extreme { border-left-color: #ff4757 !important; }
    .risk-high { border-left-color: #ff6348 !important; }
    .risk-medium { border-left-color: #ffa502 !important; }
    .risk-low { border-left-color: #2ed573 !important; }
    .risk-minimal { border-left-color: #5352ed !important; }
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
    """加载和处理所有数据 - 仅使用真实数据"""
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
            # 获取单价
            price_match = price_df[price_df['产品代码'] == current_material]
            current_price = price_match['单价'].iloc[0] if len(price_match) > 0 else 100
        elif pd.notna(row['生产日期']) and current_material:
            # 这是批次信息行
            prod_date = pd.to_datetime(row['生产日期'])
            quantity = row['数量'] if pd.notna(row['数量']) else 0
            batch_no = row['生产批号'] if pd.notna(row['生产批号']) else ''
            
            # 计算库龄
            age_days = (datetime.now() - prod_date).days
            
            # 确定风险等级
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
            
            # 计算预期损失
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
    
    # 计算预测准确率
    forecast_accuracy = calculate_forecast_accuracy(shipment_df, forecast_df)
    
    # 计算关键指标
    metrics = calculate_key_metrics(processed_inventory, forecast_accuracy)
    
    return processed_inventory, forecast_accuracy, shipment_df, forecast_df, metrics, product_name_map

def calculate_forecast_accuracy(shipment_df, forecast_df):
    """计算预测准确率"""
    try:
        # 按月份和产品聚合实际销量
        shipment_monthly = shipment_df.groupby([
            shipment_df['订单日期'].dt.to_period('M'),
            '产品代码'
        ])['求和项:数量（箱）'].sum().reset_index()
        shipment_monthly['年月'] = shipment_monthly['订单日期'].dt.to_timestamp()
        
        # 合并预测和实际数据
        merged = forecast_df.merge(
            shipment_monthly,
            left_on=['所属年月', '产品代码'],
            right_on=['年月', '产品代码'],
            how='inner'
        )
        
        # 计算预测准确率
        merged['预测误差'] = abs(merged['预计销售量'] - merged['求和项:数量（箱）'])
        merged['预测准确率'] = 1 - (merged['预测误差'] / (merged['求和项:数量（箱）'] + 1))
        merged['预测准确率'] = merged['预测准确率'].clip(0, 1)
        
        return merged
    except:
        return pd.DataFrame()

def calculate_key_metrics(processed_inventory, forecast_accuracy):
    """计算关键指标 - 仅使用真实数据"""
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
    
    # 风险分布统计
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

# 创建图表函数
def create_risk_distribution_pie(processed_inventory):
    """创建风险等级分布饼图"""
    risk_counts = processed_inventory['风险等级'].value_counts()
    
    colors = [
        COLOR_SCHEME['risk_extreme'],   # 极高风险
        COLOR_SCHEME['risk_high'],      # 高风险  
        COLOR_SCHEME['risk_medium'],    # 中风险
        COLOR_SCHEME['risk_low'],       # 低风险
        COLOR_SCHEME['risk_minimal']    # 极低风险
    ]
    
    fig = go.Figure(data=[go.Pie(
        labels=risk_counts.index,
        values=risk_counts.values,
        hole=.4,
        marker_colors=colors,
        textinfo='label+percent+value',
        textfont_size=12,
        hovertemplate="<b>%{label}</b><br>" +
                      "批次数: %{value}<br>" +
                      "占比: %{percent}<br>" +
                      "<extra></extra>"
    )])
    
    fig.update_layout(
        title="库存风险等级分布",
        title_x=0.5,
        font=dict(size=14, family="Inter, sans-serif"),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.1,
            xanchor="center",
            x=0.5
        ),
        height=350,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

def create_risk_value_analysis(processed_inventory):
    """创建风险价值分析图"""
    risk_value = processed_inventory.groupby('风险等级')['批次价值'].sum() / 1000000
    
    colors = [
        COLOR_SCHEME['risk_extreme'],
        COLOR_SCHEME['risk_high'],
        COLOR_SCHEME['risk_medium'], 
        COLOR_SCHEME['risk_low'],
        COLOR_SCHEME['risk_minimal']
    ]
    
    fig = go.Figure(data=[go.Bar(
        x=risk_value.index,
        y=risk_value.values,
        marker_color=colors,
        text=[f'¥{v:.1f}M' for v in risk_value.values],
        textposition='auto',
        textfont=dict(color='white', size=12, family="Inter, sans-serif"),
        hovertemplate="<b>%{x}</b><br>" +
                      "价值: ¥%{y:.1f}M<br>" +
                      "<extra></extra>"
    )])
    
    fig.update_layout(
        title="各风险等级价值分布",
        title_x=0.5,
        xaxis_title="风险等级",
        yaxis_title="价值 (百万元)",
        font=dict(size=14, family="Inter, sans-serif"),
        height=350,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(248, 250, 252, 0.8)',
        xaxis=dict(gridcolor='rgba(200,200,200,0.3)'),
        yaxis=dict(gridcolor='rgba(200,200,200,0.3)')
    )
    
    return fig

def create_age_distribution(processed_inventory):
    """创建库龄分布图"""
    fig = go.Figure(data=[go.Histogram(
        x=processed_inventory['库龄'],
        nbinsx=20,
        marker_color=COLOR_SCHEME['primary'],
        opacity=0.7,
        hovertemplate="库龄范围: %{x}<br>" +
                      "批次数: %{y}<br>" +
                      "<extra></extra>"
    )])
    
    # 添加风险阈值线
    fig.add_vline(x=30, line_dash="dash", line_color=COLOR_SCHEME['risk_low'], 
                  annotation_text="低风险阈值(30天)")
    fig.add_vline(x=60, line_dash="dash", line_color=COLOR_SCHEME['risk_medium'], 
                  annotation_text="中风险阈值(60天)")
    fig.add_vline(x=90, line_dash="dash", line_color=COLOR_SCHEME['risk_high'], 
                  annotation_text="高风险阈值(90天)")
    fig.add_vline(x=120, line_dash="dash", line_color=COLOR_SCHEME['risk_extreme'], 
                  annotation_text="极高风险阈值(120天)")
    
    fig.update_layout(
        title="库存批次库龄分布",
        title_x=0.5,
        xaxis_title="库龄 (天)",
        yaxis_title="批次数量",
        font=dict(size=14, family="Inter, sans-serif"),
        height=350,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(248, 250, 252, 0.8)',
        xaxis=dict(gridcolor='rgba(200,200,200,0.3)'),
        yaxis=dict(gridcolor='rgba(200,200,200,0.3)')
    )
    
    return fig

def create_high_risk_bubble(processed_inventory):
    """创建高风险批次气泡图 - 修复版本"""
    high_risk_data = processed_inventory[
        processed_inventory['风险等级'].isin(['极高风险', '高风险'])
    ].head(20)
    
    if high_risk_data.empty:
        # 返回空图表
        fig = go.Figure()
        fig.update_layout(
            title="高风险批次优先级分析 (无数据)",
            title_x=0.5,
            height=350,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(248, 250, 252, 0.8)'
        )
        return fig
    
    fig = go.Figure()
    
    for risk_level, color in [('极高风险', COLOR_SCHEME['risk_extreme']), 
                              ('高风险', COLOR_SCHEME['risk_high'])]:
        risk_subset = high_risk_data[high_risk_data['风险等级'] == risk_level]
        if not risk_subset.empty:
            try:
                # 确保数据质量
                quantities = risk_subset['数量'].fillna(100).astype(float)
                quantities = np.where(quantities <= 0, 100, quantities)
                quantities = np.where(np.isfinite(quantities), quantities, 100)
                
                # 计算marker size，确保在合理范围内
                marker_sizes = np.clip(quantities / 10, 8, 50)
                marker_sizes = np.where(np.isfinite(marker_sizes), marker_sizes, 15)
                
                # 确保所有必要字段存在且有效
                x_values = risk_subset['库龄'].fillna(0).astype(float)
                y_values = risk_subset['批次价值'].fillna(0).astype(float)
                product_names = risk_subset['产品名称'].fillna('未知产品').astype(str)
                
                fig.add_trace(go.Scatter(
                    x=x_values,
                    y=y_values,
                    mode='markers',
                    name=risk_level,
                    marker=dict(
                        size=marker_sizes.tolist(),
                        sizemode='diameter',
                        sizemin=8,
                        sizemax=50,
                        color=color,
                        opacity=0.8,
                        line=dict(width=2, color='white')
                    ),
                    text=product_names,
                    hovertemplate="<b>%{text}</b><br>" +
                                  "库龄: %{x}天<br>" +
                                  "价值: ¥%{y:,.0f}<br>" +
                                  "数量: %{customdata}箱<br>" +
                                  "<extra></extra>",
                    customdata=quantities.tolist()
                ))
            except Exception as e:
                print(f"处理{risk_level}数据时出错: {e}")
                continue
    
    fig.update_layout(
        title="高风险批次优先级分析 (气泡大小=数量)",
        title_x=0.5,
        xaxis_title="库龄 (天)",
        yaxis_title="批次价值 (元)",
        font=dict(size=14, family="Inter, sans-serif"),
        height=350,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(248, 250, 252, 0.8)',
        xaxis=dict(gridcolor='rgba(200,200,200,0.3)'),
        yaxis=dict(gridcolor='rgba(200,200,200,0.3)')
    )
    
    return fig

def create_forecast_accuracy_trend(forecast_accuracy):
    """创建预测准确率趋势图"""
    if forecast_accuracy.empty:
        fig = go.Figure()
        fig.update_layout(
            title="预测准确率月度趋势 (无数据)",
            title_x=0.5,
            xaxis_title="月份",
            yaxis_title="预测准确率 (%)",
            font=dict(size=14, family="Inter, sans-serif"),
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(248, 250, 252, 0.8)',
            annotations=[
                dict(
                    text="暂无预测数据",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    xanchor='center', yanchor='middle',
                    font=dict(size=20, color="gray")
                )
            ]
        )
        return fig
    
    monthly_acc = forecast_accuracy.groupby(
        forecast_accuracy['所属年月'].dt.to_period('M')
    )['预测准确率'].mean().reset_index()
    monthly_acc['年月'] = monthly_acc['所属年月'].dt.to_timestamp()
    
    fig = go.Figure(data=[go.Scatter(
        x=monthly_acc['年月'],
        y=monthly_acc['预测准确率'] * 100,
        mode='lines+markers',
        name='预测准确率',
        line=dict(color=COLOR_SCHEME['primary'], width=3),
        marker=dict(size=8, color=COLOR_SCHEME['primary'])
    )])
    
    # 添加目标线
    fig.add_hline(y=85, line_dash="dash", line_color="red", 
                  annotation_text="目标线 85%")
    
    fig.update_layout(
        title="预测准确率月度趋势",
        title_x=0.5,
        xaxis_title="月份",
        yaxis_title="预测准确率 (%)",
        font=dict(size=14, family="Inter, sans-serif"),
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(248, 250, 252, 0.8)',
        xaxis=dict(gridcolor='rgba(200,200,200,0.3)'),
        yaxis=dict(gridcolor='rgba(200,200,200,0.3)')
    )
    
    return fig

# 加载数据
with st.spinner('🔄 正在加载数据...'):
    processed_inventory, forecast_accuracy, shipment_df, forecast_df, metrics, product_name_map = load_and_process_data()

# 页面标题
st.markdown("""
<div class="page-header">
    <h1 class="page-title">📦 智能库存预警分析系统</h1>
    <p class="page-subtitle">数据驱动的库存风险管理与促销决策支持平台</p>
</div>
""", unsafe_allow_html=True)

# 创建标签页
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 核心指标总览",
    "🎯 风险分布分析", 
    "💡 预测准确性",
    "📋 批次详情"
])

# 标签1：核心指标总览
with tab1:
    st.markdown("### 🎯 关键绩效指标")
    
    # 第一行指标
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

# 标签2：风险分布分析（优化布局）
with tab2:
    st.markdown("### 🎯 库存风险分布分析")
    
    # 风险分布饼图 - 单列显示（信息密度高）
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown('<h3 class="chart-title">📊 风险等级分布全景</h3>', unsafe_allow_html=True)
    
    risk_pie_fig = create_risk_distribution_pie(processed_inventory)
    st.plotly_chart(risk_pie_fig, use_container_width=True)
    
    # 风险分布洞察
    st.markdown(f"""
    <div class="insight-box">
        <div class="insight-title">📊 风险分布洞察</div>
        <div class="insight-content">
            • 极高风险: {metrics['risk_counts']['extreme']}个批次 ({metrics['risk_counts']['extreme']/metrics['total_batches']*100:.1f}%) &nbsp;&nbsp;
            • 高风险: {metrics['risk_counts']['high']}个批次 ({metrics['risk_counts']['high']/metrics['total_batches']*100:.1f}%)<br>
            • 高风险批次价值占比: {metrics['high_risk_value_ratio']:.1f}% &nbsp;&nbsp;
            • 建议优先处理极高风险和高风险批次，预计通过促销可回收资金: ¥{metrics['high_risk_value']*0.8:.1f}M
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 库龄分布 + 价值分析 - 两列显示
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">📈 库龄分布分析</h3>', unsafe_allow_html=True)
        
        age_dist_fig = create_age_distribution(processed_inventory)
        st.plotly_chart(age_dist_fig, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">💰 风险价值分析</h3>', unsafe_allow_html=True)
        
        risk_value_fig = create_risk_value_analysis(processed_inventory)
        st.plotly_chart(risk_value_fig, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 高风险批次优先级矩阵 - 单列显示（需要更大空间）
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown('<h3 class="chart-title">🎯 高风险批次优先级矩阵</h3>', unsafe_allow_html=True)
    
    try:
        bubble_fig = create_high_risk_bubble(processed_inventory)
        st.plotly_chart(bubble_fig, use_container_width=True)
    except Exception as e:
        st.error(f"气泡图生成失败: {e}")
    
    # 处理优先级建议
    total_high_risk = metrics['risk_counts']['extreme'] + metrics['risk_counts']['high']
    st.markdown(f"""
    <div class="insight-box">
        <div class="insight-title">🎯 处理优先级建议</div>
        <div class="insight-content">
            • 优先处理右上角的高库龄、高价值批次，气泡大小代表批次数量，越大的批次清库难度越高<br>
            • 总计{total_high_risk}个高风险批次需要紧急处理，建议制定差异化促销策略：极高风险7折，高风险8折<br>
            • 预计损失金额: ¥{processed_inventory["预期损失"].sum()/1000000:.1f}M，通过及时促销可避免{((processed_inventory["预期损失"].sum() * 0.7)/1000000):.1f}M损失
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# 标签3：预测准确性（整合多个分析维度）
with tab3:
    st.markdown("### 📈 销售预测准确性综合分析")
    
    # 预测准确率趋势 - 单列显示
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown('<h3 class="chart-title">📊 预测准确率趋势</h3>', unsafe_allow_html=True)
    
    forecast_trend_fig = create_forecast_accuracy_trend(forecast_accuracy)
    st.plotly_chart(forecast_trend_fig, use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 预测改进建议 + 准确率分布 - 两列显示
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">🎯 预测改进建议</h3>', unsafe_allow_html=True)
        
        current_acc = metrics['forecast_accuracy']
        if current_acc > 0:
            improvement_potential = 85 - current_acc
            
            st.markdown(f"""
            <div style="text-align: center; padding: 2rem;">
                <div style="font-size: 3rem; background: linear-gradient(135deg, {COLOR_SCHEME['primary']}, {COLOR_SCHEME['secondary']}); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                    {current_acc:.1f}%
                </div>
                <div style="font-size: 1.2rem; color: #666; margin-bottom: 1rem;">
                    当前预测准确率
                </div>
                <div style="font-size: 1rem; color: #888;">
                    距离目标85%还有{improvement_potential:.1f}%的提升空间
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="text-align: center; padding: 2rem;">
                <div style="font-size: 3rem; color: #999;">
                    暂无数据
                </div>
                <div style="font-size: 1.2rem; color: #666; margin-bottom: 1rem;">
                    预测准确率
                </div>
                <div style="font-size: 1rem; color: #888;">
                    需要导入预测数据进行分析
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="insight-box">
            <div class="insight-title">📊 改进建议</div>
            <div class="insight-content">
                • 加强季节性因子分析<br>
                • 提升历史数据权重<br>
                • 增加市场趋势调研<br>
                • 优化预测模型算法
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">📈 预测准确率分布</h3>', unsafe_allow_html=True)
        
        if not forecast_accuracy.empty:
            # 创建预测误差分布图
            fig = go.Figure(data=[go.Histogram(
                x=forecast_accuracy['预测准确率'] * 100,
                nbinsx=20,
                marker_color=COLOR_SCHEME['primary'],
                opacity=0.7
            )])
            
            fig.update_layout(
                title="准确率分布情况",
                xaxis_title="预测准确率 (%)",
                yaxis_title="频次",
                height=300,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(248, 250, 252, 0.8)',
                font=dict(family="Inter, sans-serif")
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.markdown("""
            <div style="text-align: center; padding: 3rem; color: #666;">
                <h3>暂无预测数据</h3>
                <p>请上传预测数据文件以查看分布分析</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 预测vs实际对比分析 - 单列显示
    if not forecast_accuracy.empty:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">🔍 预测vs实际销售对比</h3>', unsafe_allow_html=True)
        
        # 按产品汇总预测vs实际
        product_comparison = forecast_accuracy.groupby('产品代码').agg({
            '求和项:数量（箱）': 'sum',
            '预计销售量': 'sum',
            '预测准确率': 'mean'
        }).reset_index()
        
        # 计算差异率
        product_comparison['差异率'] = (
            (product_comparison['求和项:数量（箱）'] - product_comparison['预计销售量']) / 
            product_comparison['求和项:数量（箱）'] * 100
        )
        
        # 创建散点图
        fig = go.Figure()
        
        # 添加散点
        fig.add_trace(go.Scatter(
            x=product_comparison['求和项:数量（箱）'],
            y=product_comparison['预计销售量'],
            mode='markers',
            marker=dict(
                size=10,
                color=product_comparison['预测准确率'] * 100,
                colorscale='RdYlGn',
                colorbar=dict(title="准确率 (%)"),
                showscale=True
            ),
            text=product_comparison['产品代码'],
            hovertemplate='产品: %{text}<br>实际: %{x}箱<br>预测: %{y}箱<br>准确率: %{marker.color:.1f}%<extra></extra>'
        ))
        
        # 添加理想线 (y=x)
        max_val = max(product_comparison['求和项:数量（箱）'].max(), product_comparison['预计销售量'].max())
        fig.add_trace(go.Scatter(
            x=[0, max_val],
            y=[0, max_val],
            mode='lines',
            line=dict(dash='dash', color='red'),
            name='理想预测线',
            hovertemplate='理想预测线<extra></extra>'
        ))
        
        fig.update_layout(
            xaxis_title="实际销售量 (箱)",
            yaxis_title="预测销售量 (箱)",
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(248, 250, 252, 0.8)'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 预测分析洞察
        st.markdown(f"""
        <div class="insight-box">
            <div class="insight-title">🔍 预测分析洞察</div>
            <div class="insight-content">
                • 共分析{len(product_comparison)}个产品的预测表现，平均准确率{product_comparison['预测准确率'].mean()*100:.1f}%<br>
                • 散点图中越接近红色虚线的产品预测越准确，颜色越绿表示准确率越高<br>
                • 建议重点关注偏离理想线较远且颜色偏红的产品，优化其预测模型
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

# 标签4：批次详情
with tab4:
    st.markdown("### 📋 库存批次详细信息")
    
    # 筛选控件
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
    
    # 应用筛选
    filtered_data = processed_inventory.copy()
    
    if risk_filter != '全部':
        filtered_data = filtered_data[filtered_data['风险等级'] == risk_filter]
    
    filtered_data = filtered_data[
        (filtered_data['批次价值'] >= min_value) &
        (filtered_data['库龄'] <= max_age)
    ]
    
    # 显示筛选结果统计
    st.markdown(f"""
    <div class="insight-box">
        <div class="insight-title">📊 筛选结果</div>
        <div class="insight-content">
            筛选出{len(filtered_data)}个批次，总价值¥{filtered_data['批次价值'].sum()/1000000:.2f}M，
            平均库龄{filtered_data['库龄'].mean():.0f}天
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 显示数据表格
    if not filtered_data.empty:
        # 重新排序列并格式化
        display_columns = ['物料', '产品名称', '生产日期', '生产批号', '数量', '库龄', '风险等级', '批次价值', '处理建议']
        display_data = filtered_data[display_columns].copy()
        
        # 格式化数值
        display_data['批次价值'] = display_data['批次价值'].apply(lambda x: f"¥{x:,.0f}")
        display_data['生产日期'] = display_data['生产日期'].dt.strftime('%Y-%m-%d')
        
        # 按风险等级和价值排序
        risk_order = {'极高风险': 0, '高风险': 1, '中风险': 2, '低风险': 3, '极低风险': 4}
        display_data['风险排序'] = display_data['风险等级'].map(risk_order)
        display_data = display_data.sort_values(['风险排序', '库龄'], ascending=[True, False])
        display_data = display_data.drop('风险排序', axis=1)
        
        st.dataframe(
            display_data,
            use_container_width=True,
            height=400
        )
        
        # 下载按钮
        csv = display_data.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 下载筛选结果",
            data=csv,
            file_name=f"库存分析_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.warning("没有符合筛选条件的数据")

# 页脚 - 修改为白色小字体
st.markdown("---")
st.markdown(
    f"""
    <div class="footer-text">
        🚀 Powered by Streamlit & Plotly | 智能数据分析平台 | 最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}
    </div>
    """,
    unsafe_allow_html=True
)
