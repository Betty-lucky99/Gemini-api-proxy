import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import json
import os
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# --- 页面配置 ---
st.set_page_config(
    page_title="Gemini API Proxy",
    page_icon="🌠",
    layout="wide",
    initial_sidebar_state="collapsed"  # 默认折叠侧边栏，移动端友好
)

# --- 日志配置 ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- API配置 ---
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')

if 'streamlit.io' in os.getenv('STREAMLIT_SERVER_HEADLESS', ''):
    API_BASE_URL = os.getenv('API_BASE_URL', 'https://your-app.onrender.com')


# --- API调用函数 ---
def call_api(endpoint: str, method: str = 'GET', data: Any = None, timeout: int = 30) -> Optional[Dict]:
    """统一API调用函数"""
    url = f"{API_BASE_URL}{endpoint}"

    try:
        spinner_message = "加载中..." if method == 'GET' else "保存中..."
        with st.spinner(spinner_message):
            if method == 'GET':
                response = requests.get(url, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, timeout=timeout)
            else:
                raise ValueError(f"不支持的方法: {method}")

            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"API错误: {response.status_code}")
                return None

    except requests.exceptions.Timeout:
        st.error("请求超时，请重试。")
        return None
    except requests.exceptions.ConnectionError:
        st.error("无法连接到API服务。")
        return None
    except Exception as e:
        st.error(f"API错误: {str(e)}")
        return None


def wake_up_service():
    """唤醒服务"""
    try:
        response = requests.get(f"{API_BASE_URL}/wake", timeout=10)
        if response.status_code == 200:
            st.success("服务已激活")
            return True
    except:
        pass
    return False


def check_service_health():
    """检查服务健康状态"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None


# --- 健康检测函数 ---
def check_all_keys_health():
    """一键检测所有Key健康状态"""
    result = call_api('/admin/health/check-all', 'POST', timeout=60)
    return result


def get_health_summary():
    """获取健康状态汇总"""
    result = call_api('/admin/health/summary')
    return result


# --- 自动清理功能函数 ---
def get_cleanup_status():
    """获取自动清理状态"""
    return call_api('/admin/cleanup/status')


def update_cleanup_config(config_data):
    """更新自动清理配置"""
    return call_api('/admin/cleanup/config', 'POST', config_data)


def manual_cleanup():
    """手动执行清理"""
    return call_api('/admin/cleanup/manual', 'POST')


# --- 故障转移配置函数 ---
def get_failover_config():
    """获取故障转移配置"""
    return call_api('/admin/config/failover')


def update_failover_config(config_data):
    """更新故障转移配置"""
    return call_api('/admin/config/failover', 'POST', config_data)


def get_failover_stats():
    """获取故障转移统计信息"""
    return call_api('/admin/failover/stats')


# --- 缓存函数 ---
@st.cache_data(ttl=30)
def get_cached_stats():
    """获取缓存的统计数据"""
    return call_api('/admin/stats')


@st.cache_data(ttl=60)
def get_cached_status():
    """获取缓存的服务状态"""
    return call_api('/status')


@st.cache_data(ttl=30)
def get_cached_model_config(model_name: str):
    """获取缓存的模型配置"""
    return call_api(f'/admin/models/{model_name}')


@st.cache_data(ttl=30)
def get_cached_gemini_keys():
    """获取缓存的Gemini密钥列表"""
    return call_api('/admin/keys/gemini')


@st.cache_data(ttl=30)
def get_cached_user_keys():
    """获取缓存的用户密钥列表"""
    return call_api('/admin/keys/user')


@st.cache_data(ttl=30)
def get_cached_health_summary():
    """获取缓存的健康状态汇总"""
    return get_health_summary()


@st.cache_data(ttl=60)
def get_cached_cleanup_status():
    """获取缓存的自动清理状态"""
    return get_cleanup_status()


@st.cache_data(ttl=30)
def get_cached_failover_config():
    """获取缓存的故障转移配置"""
    return get_failover_config()


@st.cache_data(ttl=60)
def get_cached_failover_stats():
    """获取缓存的故障转移统计"""
    return get_failover_stats()


# --- 密钥管理函数 ---
def mask_key(key: str, show_full: bool = False) -> str:
    """密钥掩码处理"""
    if show_full:
        return key

    if key.startswith('sk-'):
        # 用户密钥格式: sk-xxxxxxxx...
        if len(key) > 10:
            return f"{key[:6]}{'•' * (len(key) - 10)}{key[-4:]}"
        return key
    elif key.startswith('AIzaSy'):
        # Gemini密钥格式: AIzaSyxxxxxxx...
        if len(key) > 12:
            return f"{key[:8]}{'•' * (len(key) - 12)}{key[-4:]}"
        return key
    else:
        # 其他格式
        if len(key) > 8:
            return f"{key[:4]}{'•' * (len(key) - 8)}{key[-4:]}"
        return key


def delete_key(key_type: str, key_id: int) -> bool:
    """删除密钥"""
    endpoint = f'/admin/keys/{key_type}/{key_id}'
    result = call_api(endpoint, 'DELETE')
    return result and result.get('success', False)


def toggle_key_status(key_type: str, key_id: int) -> bool:
    """切换密钥状态"""
    endpoint = f'/admin/keys/{key_type}/{key_id}/toggle'
    result = call_api(endpoint, 'POST')
    return result and result.get('success', False)


def get_health_status_color(health_status: str) -> str:
    """获取健康状态颜色"""
    status_colors = {
        'healthy': '#10b981',  # 绿色
        'unhealthy': '#ef4444',  # 红色
        'unknown': '#f59e0b'  # 黄色
    }
    return status_colors.get(health_status, '#6b7280')  # 默认灰色


def format_health_status(health_status: str) -> str:
    """格式化健康状态显示"""
    status_map = {
        'healthy': '正常',
        'unhealthy': '异常',
        'unknown': '未知'
    }
    return status_map.get(health_status, health_status)


# --- 玻璃拟态风格CSS ---
st.markdown("""
<style>
    /* 移动端检测脚本 */
    script {
        display: none;
    }

    /* 全局字体和基础设置 */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro SC", "SF Pro Display", "Helvetica Neue", "PingFang SC", "Microsoft YaHei UI", sans-serif;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }

    /* 页面背景 */
    .stApp {
        background: linear-gradient(135deg, 
            #e0e7ff 0%, 
            #f3e8ff 25%, 
            #fce7f3 50%, 
            #fef3c7 75%, 
            #dbeafe 100%
        );
        background-size: 400% 400%;
        animation: gradient-shift 20s ease infinite;
        min-height: 100vh;
        overflow-x: hidden;
    }

    @keyframes gradient-shift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* 主内容区域 */
    .block-container {
        background: rgba(255, 255, 255, 0.25);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 24px;
        border: 1px solid rgba(255, 255, 255, 0.4);
        box-shadow: 
            0 20px 60px rgba(0, 0, 0, 0.05),
            0 8px 32px rgba(0, 0, 0, 0.03),
            inset 0 1px 0 rgba(255, 255, 255, 0.5);
        padding: 1.5rem;
        margin: 1rem;
        max-width: 1440px;
        position: relative;
        overflow: visible;
        min-height: auto;
    }

    /* 媒体查询 */
    @media (max-width: 768px) {
        .block-container {
            padding: 1rem;
            margin: 0.5rem;
            border-radius: 16px;
        }

        /* 隐藏侧边栏按钮 */
        .stSidebar .stButton {
            margin-bottom: 0.5rem;
        }

        /* 标题 */
        h1 {
            font-size: 1.875rem !important;
            margin-bottom: 1rem !important;
        }

        h2 {
            font-size: 1.5rem !important;
            margin-top: 1.5rem !important;
            margin-bottom: 0.75rem !important;
        }

        h3 {
            font-size: 1.125rem !important;
            margin-top: 1rem !important;
            margin-bottom: 0.5rem !important;
        }

        /* 卡片间距 */
        [data-testid="metric-container"] {
            margin-bottom: 0.75rem;
            padding: 1rem 1.25rem;
        }

        /* 按钮 */
        .stButton > button {
            width: 100%;
            margin-bottom: 0.5rem;
            font-size: 0.875rem;
            padding: 0.625rem 1rem;
        }

        /* 表单间距 */
        .stForm {
            margin-bottom: 1rem;
        }

        /* 输入框 */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stSelectbox > div > div > select,
        .stTextArea > div > div > textarea {
            font-size: 16px !important; /* 防止iOS缩放 */
            padding: 0.75rem 1rem !important;
        }

        /* 标签页 */
        .stTabs [data-testid="stTabBar"] {
            gap: 0.5rem;
            padding: 0;
            margin-bottom: 1rem;
            overflow-x: auto;
            scrollbar-width: none;
            -ms-overflow-style: none;
        }

        .stTabs [data-testid="stTabBar"]::-webkit-scrollbar {
            display: none;
        }

        .stTabs [data-testid="stTabBar"] button {
            padding: 0.875rem 1.25rem;
            font-size: 0.875rem;
            white-space: nowrap;
            min-width: auto;
        }

        /* Alert */
        [data-testid="stAlert"] {
            padding: 0.75rem 1rem !important;
            margin: 0.5rem 0 !important;
            border-radius: 12px !important;
            font-size: 0.875rem !important;
        }
    }

    /* 超小屏幕 */
    @media (max-width: 480px) {
        .block-container {
            padding: 0.75rem;
            margin: 0.25rem;
            border-radius: 12px;
        }

        /* 超小屏幕下的度量卡片 */
        [data-testid="metric-container"] {
            padding: 0.875rem 1rem;
        }

        [data-testid="metric-container"] > div:nth-child(2) {
            font-size: 1.875rem;
        }

        /* 超小屏幕下的按钮 */
        .stButton > button {
            font-size: 0.8125rem;
            padding: 0.5rem 0.875rem;
        }

        /* 超小屏幕下的标题 */
        h1 {
            font-size: 1.5rem !important;
        }

        h2 {
            font-size: 1.25rem !important;
        }

        h3 {
            font-size: 1rem !important;
        }
    }

    .block-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, 
            transparent, 
            rgba(255, 255, 255, 0.6) 50%, 
            transparent
        );
    }

    /* 度量卡片玻璃效果 */
    [data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.4);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        padding: 1.5rem 1.75rem;
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.5);
        box-shadow: 
            0 12px 40px rgba(0, 0, 0, 0.05),
            0 4px 16px rgba(0, 0, 0, 0.03),
            inset 0 1px 0 rgba(255, 255, 255, 0.6);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }

    [data-testid="metric-container"]::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, 
            transparent, 
            rgba(255, 255, 255, 0.8) 50%, 
            transparent
        );
    }

    [data-testid="metric-container"]:hover {
        transform: translateY(-4px) scale(1.02);
        box-shadow: 
            0 20px 60px rgba(0, 0, 0, 0.08),
            0 8px 32px rgba(0, 0, 0, 0.05),
            inset 0 1px 0 rgba(255, 255, 255, 0.7);
        border-color: rgba(255, 255, 255, 0.6);
        background: rgba(255, 255, 255, 0.5);
    }

    /* 移动端触摸 */
    @media (max-width: 768px) {
        /* 卡片悬停动画 */
        [data-testid="metric-container"]:hover {
            transform: translateY(-2px) scale(1.01);
        }

        [data-testid="metric-container"]:active {
            transform: scale(0.98);
            transition: transform 0.15s ease;
        }

        /* 按钮动画 */
        .stButton > button:hover {
            transform: translateY(-1px);
        }

        .stButton > button:active {
            transform: scale(0.98);
            transition: transform 0.1s ease;
        }

        /* 导航项动画 */
        section[data-testid="stSidebar"] .stRadio > div > label:hover {
            transform: translateX(3px);
        }

        section[data-testid="stSidebar"] .stRadio > div > label:active {
            transform: scale(0.98);
            transition: transform 0.1s ease;
        }

        /* Logo动画 */
        .sidebar-logo:hover {
            transform: translateY(-1px) scale(1.01);
        }

        .sidebar-logo:active {
            transform: scale(0.98);
            transition: transform 0.1s ease;
        }

        /* 状态卡片动画 */
        .sidebar-status-card:hover {
            transform: translateY(-1px);
        }

        .sidebar-status-card:active {
            transform: scale(0.98);
            transition: transform 0.1s ease;
        }

        /* 密钥卡片动画 */
        div[data-testid="stHorizontalBlock"]:hover {
            transform: translateY(-1px) scale(1.005);
        }

        div[data-testid="stHorizontalBlock"]:active {
            transform: scale(0.98);
            transition: transform 0.1s ease;
        }

        /* 链接动画 */
        .sidebar-footer-link:hover {
            transform: translateY(-0.5px);
        }

        .sidebar-footer-link:active {
            background: rgba(255, 255, 255, 0.15);
            transform: scale(0.98);
            transition: all 0.1s ease;
        }

        /* 标签页动画 */
        .stTabs [data-testid="stTabBar"] button:hover {
            transform: translateY(-0.5px);
        }

        .stTabs [data-testid="stTabBar"] button:active {
            background: rgba(255, 255, 255, 0.5);
            transform: scale(0.98);
            transition: all 0.1s ease;
        }

        /* 输入框聚焦动画 */
        .stTextInput > div > div > input:focus,
        .stNumberInput > div > div > input:focus,
        .stSelectbox > div > div > select:focus,
        .stTextArea > div > div > textarea:focus {
            transform: translateY(-0.5px);
        }

        /* 状态标签保留动画 */
        .status-badge:hover {
            transform: translateY(-1px) scale(1.02);
        }

        .status-badge:active {
            transform: scale(0.98);
            transition: transform 0.1s ease;
        }
    }

    /* 度量值样式 */
    [data-testid="metric-container"] > div:nth-child(1) {
        font-size: 0.8125rem;
        font-weight: 600;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.5rem;
    }

    [data-testid="metric-container"] > div:nth-child(2) {
        font-size: 2.25rem;
        font-weight: 700;
        color: #1f2937;
        line-height: 1.1;
        background: linear-gradient(135deg, #1f2937 0%, #4f46e5 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    [data-testid="metric-container"] > div:nth-child(3) {
        font-size: 0.8125rem;
        font-weight: 500;
        margin-top: 0.75rem;
        color: #6b7280;
    }

    /* 侧边栏设计 */
    section[data-testid="stSidebar"] {
        background: linear-gradient(135deg, 
            rgba(99, 102, 241, 0.12) 0%,
            rgba(168, 85, 247, 0.08) 25%,
            rgba(59, 130, 246, 0.1) 50%,
            rgba(139, 92, 246, 0.08) 75%,
            rgba(99, 102, 241, 0.12) 100%
        );
        backdrop-filter: blur(24px);
        -webkit-backdrop-filter: blur(24px);
        border-right: 1px solid rgba(255, 255, 255, 0.15);
        box-shadow: 
            4px 0 32px rgba(0, 0, 0, 0.08),
            0 0 0 1px rgba(255, 255, 255, 0.08) inset;
        position: relative;
        overflow: hidden;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    /* 移动端侧边栏宽度调整 */
    @media (max-width: 768px) {
        section[data-testid="stSidebar"] {
            width: 280px !important;
            z-index: 999;
            transform: translateX(0);
            transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        section[data-testid="stSidebar"] > div:nth-child(1) > div:nth-child(2) {
            padding: 1.5rem 1rem;
            position: relative;
        }
    }

    /* 侧边栏动态背景 */
    section[data-testid="stSidebar"]::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: 
            radial-gradient(circle at 20% 20%, rgba(99, 102, 241, 0.2) 0%, transparent 50%),
            radial-gradient(circle at 80% 80%, rgba(168, 85, 247, 0.15) 0%, transparent 50%),
            radial-gradient(circle at 40% 60%, rgba(59, 130, 246, 0.18) 0%, transparent 50%);
        opacity: 0.7;
        animation: float 20s ease-in-out infinite alternate;
        pointer-events: none;
    }

    @keyframes float {
        0% { transform: translate(0px, 0px) rotate(0deg); opacity: 0.7; }
        50% { transform: translate(-10px, -10px) rotate(1deg); opacity: 0.9; }
        100% { transform: translate(5px, -5px) rotate(-1deg); opacity: 0.7; }
    }

    /* 侧边栏内容区域 */
    section[data-testid="stSidebar"] > div:nth-child(1) > div:nth-child(2) {
        padding: 2rem 1.5rem;
        height: 100%;
        display: flex;
        flex-direction: column;
        position: relative;
        z-index: 2;
    }

    /* Logo区域玻璃效果 */
    .sidebar-logo {
        display: flex;
        align-items: center;
        gap: 0.875rem;
        padding: 1.25rem 1rem;
        margin-bottom: 1.5rem;
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.15);
        box-shadow: 
            0 12px 40px rgba(0, 0, 0, 0.08),
            inset 0 1px 0 rgba(255, 255, 255, 0.2);
        position: relative;
        overflow: hidden;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }

    /* 移动端Logo调整 */
    @media (max-width: 768px) {
        .sidebar-logo {
            padding: 1rem 0.875rem;
            margin-bottom: 1rem;
            border-radius: 16px;
        }

        .sidebar-logo-icon {
            font-size: 2rem !important;
        }

        .sidebar-logo-title {
            font-size: 1.125rem !important;
        }

        .sidebar-logo-subtitle {
            font-size: 0.75rem !important;
        }
    }

    .sidebar-logo::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, 
            transparent, 
            rgba(255, 255, 255, 0.15) 50%, 
            transparent
        );
        transition: left 0.8s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .sidebar-logo:hover {
        transform: translateY(-2px) scale(1.02);
        box-shadow: 
            0 16px 48px rgba(0, 0, 0, 0.12),
            inset 0 1px 0 rgba(255, 255, 255, 0.25);
        background: rgba(255, 255, 255, 0.12);
    }

    /* 移动端禁用Logo悬停动画 */
    @media (max-width: 768px) {
        .sidebar-logo:hover {
            transform: none;
        }
    }

    .sidebar-logo:hover::before {
        left: 100%;
    }

    .sidebar-logo-icon {
        font-size: 2.5rem;
        line-height: 1;
        filter: drop-shadow(0 0 12px rgba(99, 102, 241, 0.8));
        animation: pulse-glow 3s ease-in-out infinite;
    }

    @keyframes pulse-glow {
        0%, 100% { filter: drop-shadow(0 0 12px rgba(99, 102, 241, 0.8)); }
        50% { filter: drop-shadow(0 0 24px rgba(99, 102, 241, 1)); }
    }

    .sidebar-logo-title {
        font-size: 1.375rem;
        font-weight: 700;
        letter-spacing: -0.025em;
        color: white;
        text-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
    }

    .sidebar-logo-subtitle {
        font-size: 0.875rem;
        color: rgba(255, 255, 255, 0.8);
        text-shadow: 0 1px 4px rgba(0, 0, 0, 0.3);
    }

    /* 玻璃分割线 */
    .sidebar-divider {
        height: 1px;
        background: linear-gradient(90deg, 
            transparent, 
            rgba(255, 255, 255, 0.25) 20%, 
            rgba(255, 255, 255, 0.5) 50%, 
            rgba(255, 255, 255, 0.25) 80%, 
            transparent
        );
        margin: 1.5rem 0;
        position: relative;
    }

    /* 移动端分割线调整 */
    @media (max-width: 768px) {
        .sidebar-divider {
            margin: 1rem 0;
        }
    }

    .sidebar-divider::after {
        content: '';
        position: absolute;
        top: 1px;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, 
            transparent, 
            rgba(255, 255, 255, 0.15) 50%, 
            transparent
        );
    }

    /* 导航区域标题 */
    .sidebar-section-title {
        font-size: 0.875rem;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.7);
        text-transform: uppercase;
        letter-spacing: 0.15em;
        padding: 0 1rem 0.75rem 1rem;
        margin-bottom: 0.5rem;
        text-shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
        position: relative;
    }

    /* 移动端导航标题调整 */
    @media (max-width: 768px) {
        .sidebar-section-title {
            font-size: 0.75rem;
            padding: 0 0.75rem 0.5rem 0.75rem;
            margin-bottom: 0.25rem;
        }
    }

    .sidebar-section-title::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 1rem;
        right: 1rem;
        height: 1px;
        background: linear-gradient(90deg, 
            rgba(255, 255, 255, 0.25), 
            rgba(255, 255, 255, 0.08)
        );
    }

    /* 导航容器 */
    section[data-testid="stSidebar"] .stRadio {
        background: transparent !important;
        padding: 0 !important;
        margin: 0 !important;
        border: none !important;
    }

    section[data-testid="stSidebar"] .stRadio > div {
        gap: 0.5rem !important;
        background: transparent !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    /* 移动端导航间距调整 */
    @media (max-width: 768px) {
        section[data-testid="stSidebar"] .stRadio > div {
            gap: 0.375rem !important;
        }
    }

    /* 导航项玻璃效果 */
    section[data-testid="stSidebar"] .stRadio > div > label {
        font-size: 1rem !important;
        font-weight: 500 !important;
        color: rgba(255, 255, 255, 0.9) !important;
        padding: 1rem 1.25rem !important;
        border-radius: 16px !important;
        cursor: pointer !important;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
        display: flex !important;
        align-items: center !important;
        gap: 0.875rem !important;
        margin: 0.375rem 0 !important;
        position: relative !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        width: 100% !important;
        box-sizing: border-box !important;
        overflow: hidden !important;
        text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3) !important;
        box-shadow: 
            0 4px 16px rgba(0, 0, 0, 0.06),
            inset 0 1px 0 rgba(255, 255, 255, 0.12) !important;
        -webkit-tap-highlight-color: transparent !important; /* 移除iOS点击高亮 */
    }

    /* 移动端导航项调整 */
    @media (max-width: 768px) {
        section[data-testid="stSidebar"] .stRadio > div > label {
            font-size: 0.875rem !important;
            padding: 0.875rem 1rem !important;
            margin: 0.25rem 0 !important;
            border-radius: 14px !important;
        }
    }

    /* 导航项内容发光边框 */
    section[data-testid="stSidebar"] .stRadio > div > label::before {
        content: '';
        position: absolute;
        inset: 0;
        border-radius: 16px;
        padding: 1px;
        background: linear-gradient(135deg, 
            rgba(255, 255, 255, 0.25) 0%, 
            rgba(255, 255, 255, 0.08) 25%,
            transparent 50%,
            rgba(255, 255, 255, 0.08) 75%,
            rgba(255, 255, 255, 0.25) 100%
        );
        mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
        mask-composite: exclude;
        opacity: 0;
        transition: opacity 0.4s ease;
    }

    /* 悬停效果 */
    section[data-testid="stSidebar"] .stRadio > div > label:hover {
        background: rgba(255, 255, 255, 0.12) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        color: white !important;
        transform: translateX(6px) translateY(-2px) !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
        box-shadow: 
            0 12px 32px rgba(0, 0, 0, 0.1),
            0 4px 16px rgba(99, 102, 241, 0.2),
            inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
    }

    /* 移动端禁用导航悬停动画 */
    @media (max-width: 768px) {
        section[data-testid="stSidebar"] .stRadio > div > label:hover {
            transform: none !important;
        }

        section[data-testid="stSidebar"] .stRadio > div > label:active {
            transform: scale(0.98) !important;
            transition: transform 0.1s ease !important;
        }
    }

    section[data-testid="stSidebar"] .stRadio > div > label:hover::before {
        opacity: 1;
    }

    /* 选中状态玻璃效果 */
    section[data-testid="stSidebar"] .stRadio input[type="radio"]:checked + label {
        background: linear-gradient(135deg, 
            rgba(99, 102, 241, 0.3) 0%, 
            rgba(168, 85, 247, 0.25) 50%,
            rgba(99, 102, 241, 0.3) 100%
        ) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        color: white !important;
        font-weight: 600 !important;
        border: 1px solid rgba(255, 255, 255, 0.25) !important;
        box-shadow: 
            0 12px 40px rgba(99, 102, 241, 0.25),
            0 6px 20px rgba(0, 0, 0, 0.1),
            inset 0 1px 0 rgba(255, 255, 255, 0.25),
            inset 0 -1px 0 rgba(0, 0, 0, 0.1) !important;
        transform: translateX(4px) !important;
    }

    /* 移动端选中状态不移动 */
    @media (max-width: 768px) {
        section[data-testid="stSidebar"] .stRadio input[type="radio"]:checked + label {
            transform: none !important;
        }
    }

    /* 选中状态发光边框 */
    section[data-testid="stSidebar"] .stRadio input[type="radio"]:checked + label::after {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        width: 4px;
        height: 100%;
        border-radius: 0 2px 2px 0;
        background: linear-gradient(180deg, 
            #6366f1 0%, 
            #a855f7 50%,
            #6366f1 100%
        );
        box-shadow: 
            0 0 16px rgba(99, 102, 241, 1),
            0 0 32px rgba(99, 102, 241, 0.6);
        animation: glow-pulse 2s ease-in-out infinite;
    }

    @keyframes glow-pulse {
        0%, 100% { 
            box-shadow: 
                0 0 16px rgba(99, 102, 241, 1),
                0 0 32px rgba(99, 102, 241, 0.6);
        }
        50% { 
            box-shadow: 
                0 0 24px rgba(99, 102, 241, 1),
                0 0 48px rgba(99, 102, 241, 0.8),
                0 0 64px rgba(99, 102, 241, 0.4);
        }
    }

    /* 隐藏radio按钮 */
    section[data-testid="stSidebar"] .stRadio input[type="radio"] {
        display: none !important;
    }

    /* 状态指示器玻璃卡片 */
    .sidebar-status {
        margin-top: auto;
        padding-top: 1.5rem;
    }

    /* 移动端状态调整 */
    @media (max-width: 768px) {
        .sidebar-status {
            padding-top: 1rem;
        }
    }

    .sidebar-status-card {
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 16px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 
            0 8px 24px rgba(0, 0, 0, 0.08),
            inset 0 1px 0 rgba(255, 255, 255, 0.12);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }

    /* 移动端状态卡片调整 */
    @media (max-width: 768px) {
        .sidebar-status-card {
            padding: 1rem;
            margin-bottom: 0.75rem;
            border-radius: 14px;
        }
    }

    .sidebar-status-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, 
            transparent, 
            rgba(255, 255, 255, 0.4) 50%, 
            transparent
        );
    }

    .sidebar-status-card:hover {
        background: rgba(255, 255, 255, 0.12);
        border-color: rgba(255, 255, 255, 0.2);
        transform: translateY(-2px);
        box-shadow: 
            0 12px 32px rgba(0, 0, 0, 0.12),
            inset 0 1px 0 rgba(255, 255, 255, 0.18);
    }

    /* 移动端禁用状态卡片悬停 */
    @media (max-width: 768px) {
        .sidebar-status-card:hover {
            transform: none;
        }
    }

    .sidebar-status-title {
        font-size: 0.875rem;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.75);
        margin-bottom: 0.5rem;
        text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
    }

    /* 移动端状态标题调整 */
    @media (max-width: 768px) {
        .sidebar-status-title {
            font-size: 0.75rem;
            margin-bottom: 0.375rem;
        }
    }

    .sidebar-status-content {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .sidebar-status-indicator {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        flex-shrink: 0;
        position: relative;
        box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.25);
    }

    .sidebar-status-indicator.online {
        background: #10b981;
        box-shadow: 
            0 0 16px rgba(16, 185, 129, 0.8),
            0 0 0 2px rgba(255, 255, 255, 0.25);
        animation: online-pulse 2s ease-in-out infinite;
    }

    .sidebar-status-indicator.offline {
        background: #ef4444;
        box-shadow: 
            0 0 16px rgba(239, 68, 68, 0.8),
            0 0 0 2px rgba(255, 255, 255, 0.25);
    }

    @keyframes online-pulse {
        0%, 100% { 
            box-shadow: 
                0 0 16px rgba(16, 185, 129, 0.8),
                0 0 0 2px rgba(255, 255, 255, 0.25);
        }
        50% { 
            box-shadow: 
                0 0 24px rgba(16, 185, 129, 1),
                0 0 40px rgba(16, 185, 129, 0.6),
                0 0 0 2px rgba(255, 255, 255, 0.35);
        }
    }

    .sidebar-status-text {
        font-size: 1rem;
        color: white;
        font-weight: 500;
        text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
    }

    /* 移动端状态文字调整 */
    @media (max-width: 768px) {
        .sidebar-status-text {
            font-size: 0.875rem;
        }
    }

    /* 版本信息 */
    .sidebar-footer {
        padding-top: 1rem;
        border-top: 1px solid rgba(255, 255, 255, 0.12);
        margin-top: 1rem;
        position: relative;
    }

    /* 移动端版本信息调整 */
    @media (max-width: 768px) {
        .sidebar-footer {
            padding-top: 0.75rem;
            margin-top: 0.75rem;
        }
    }

    .sidebar-footer::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, 
            transparent, 
            rgba(255, 255, 255, 0.25) 50%, 
            transparent
        );
    }

    .sidebar-footer-content {
        display: flex;
        flex-direction: column;
        gap: 0.375rem;
        padding: 0 0.5rem;
    }

    /* 移动端版本信息内容调整 */
    @media (max-width: 768px) {
        .sidebar-footer-content {
            gap: 0.25rem;
            padding: 0 0.25rem;
        }
    }

    .sidebar-footer-item {
        font-size: 0.875rem;
        color: rgba(255, 255, 255, 0.6);
        display: flex;
        align-items: center;
        gap: 0.5rem;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
    }

    /* 移动端版本信息项调整 */
    @media (max-width: 768px) {
        .sidebar-footer-item {
            font-size: 0.75rem;
            gap: 0.375rem;
        }
    }

    .sidebar-footer-link {
        color: rgba(255, 255, 255, 0.75);
        text-decoration: none;
        transition: all 0.3s ease;
        padding: 0.25rem 0.5rem;
        border-radius: 6px;
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        -webkit-tap-highlight-color: transparent; 
    }

    .sidebar-footer-link:hover {
        color: white;
        background: rgba(255, 255, 255, 0.12);
        text-shadow: 0 0 12px rgba(255, 255, 255, 0.6);
        transform: translateY(-1px);
    }

    /* 移动端禁用链接悬停动画 */
    @media (max-width: 768px) {
        .sidebar-footer-link:hover {
            transform: none;
        }

        .sidebar-footer-link:active {
            background: rgba(255, 255, 255, 0.15);
        }
    }

    /* 按钮玻璃效果 */
    .stButton > button {
        border-radius: 14px;
        font-weight: 500;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid rgba(99, 102, 241, 0.3);
        font-size: 0.9375rem;
        padding: 0.75rem 1.5rem;
        letter-spacing: 0.02em;
        background: rgba(99, 102, 241, 0.1);
        color: #4f46e5;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        box-shadow: 
            0 8px 24px rgba(99, 102, 241, 0.15),
            inset 0 1px 0 rgba(255, 255, 255, 0.4);
        position: relative;
        overflow: hidden;
        -webkit-tap-highlight-color: transparent; 
        min-height: 44px; 
    }

    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, 
            transparent, 
            rgba(255, 255, 255, 0.3) 50%, 
            transparent
        );
        transition: left 0.6s ease;
    }

    .stButton > button:hover {
        background: rgba(99, 102, 241, 0.2);
        transform: translateY(-3px) scale(1.02);
        box-shadow: 
            0 12px 36px rgba(99, 102, 241, 0.25),
            inset 0 1px 0 rgba(255, 255, 255, 0.5);
        border-color: rgba(99, 102, 241, 0.4);
        color: #4338ca;
    }

    /* 按钮 */
    @media (max-width: 768px) {
        .stButton > button:hover {
            transform: none;
        }

        .stButton > button:active {
            transform: scale(0.98);
            transition: transform 0.1s ease;
        }
    }

    .stButton > button:hover::before {
        left: 100%;
    }

    .stButton > button:active {
        transform: translateY(-1px) scale(0.98);
    }

    /* 输入框 */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > select,
    .stTextArea > div > div > textarea {
        background: rgba(255, 255, 255, 0.6) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(99, 102, 241, 0.2) !important;
        border-radius: 12px !important;
        font-size: 0.9375rem !important;
        padding: 0.875rem 1.25rem !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 
            0 8px 24px rgba(0, 0, 0, 0.05),
            inset 0 1px 0 rgba(255, 255, 255, 0.4) !important;
        color: #1f2937 !important;
        min-height: 44px !important; 
    }

    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder {
        color: #6b7280 !important;
    }

    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus,
    .stTextArea > div > div > textarea:focus {
        background: rgba(255, 255, 255, 0.8) !important;
        border-color: rgba(99, 102, 241, 0.5) !important;
        box-shadow: 
            0 0 0 3px rgba(99, 102, 241, 0.1),
            0 12px 32px rgba(0, 0, 0, 0.08),
            inset 0 1px 0 rgba(255, 255, 255, 0.5) !important;
        outline: none !important;
        transform: translateY(-1px);
    }

    /* 移动端输入框聚焦优化 */
    @media (max-width: 768px) {
        .stTextInput > div > div > input:focus,
        .stNumberInput > div > div > input:focus,
        .stSelectbox > div > div > select:focus,
        .stTextArea > div > div > textarea:focus {
            transform: none;
        }
    }

    /* 健康状态标签玻璃效果 */
    .status-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.8125rem;
        font-weight: 500;
        line-height: 1;
        white-space: nowrap;
        min-width: 3.5rem;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.4);
        box-shadow: 
            0 6px 20px rgba(0, 0, 0, 0.06),
            inset 0 1px 0 rgba(255, 255, 255, 0.4);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    /* 移动端状态标签调整 */
    @media (max-width: 768px) {
        .status-badge {
            padding: 0.375rem 0.75rem;
            font-size: 0.75rem;
            min-width: 3rem;
            border-radius: 16px;
        }
    }

    .status-badge:hover {
        transform: translateY(-2px) scale(1.05);
        box-shadow: 
            0 12px 32px rgba(0, 0, 0, 0.08),
            inset 0 1px 0 rgba(255, 255, 255, 0.5);
    }

    /* 移动端禁用状态标签悬停 */
    @media (max-width: 768px) {
        .status-badge:hover {
            transform: none;
        }
    }

    .status-healthy {
        background: rgba(16, 185, 129, 0.15);
        color: #065f46;
        border-color: rgba(16, 185, 129, 0.3);
    }

    .status-unhealthy {
        background: rgba(239, 68, 68, 0.15);
        color: #991b1b;
        border-color: rgba(239, 68, 68, 0.3);
    }

    .status-unknown {
        background: rgba(245, 158, 11, 0.15);
        color: #92400e;
        border-color: rgba(245, 158, 11, 0.3);
    }

    .status-active {
        background: rgba(59, 130, 246, 0.15);
        color: #1e40af;
        border-color: rgba(59, 130, 246, 0.3);
    }

    .status-inactive {
        background: rgba(107, 114, 128, 0.15);
        color: #374151;
        border-color: rgba(107, 114, 128, 0.3);
    }

    /* 密钥卡片玻璃效果 */
    div[data-testid="stHorizontalBlock"] {
        background: rgba(255, 255, 255, 0.4);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.5);
        border-radius: 16px;
        padding: 1.25rem;
        margin: 0.75rem 0;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 
            0 10px 32px rgba(0, 0, 0, 0.06),
            inset 0 1px 0 rgba(255, 255, 255, 0.5);
        position: relative;
        overflow: hidden;
    }

    /* 移动端密钥卡片调整 */
    @media (max-width: 768px) {
        div[data-testid="stHorizontalBlock"] {
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 14px;
        }
    }

    div[data-testid="stHorizontalBlock"]::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, 
            transparent, 
            rgba(255, 255, 255, 0.8) 50%, 
            transparent
        );
    }

    div[data-testid="stHorizontalBlock"]:hover {
        transform: translateY(-3px) scale(1.01);
        box-shadow: 
            0 16px 48px rgba(0, 0, 0, 0.08),
            inset 0 1px 0 rgba(255, 255, 255, 0.6);
        border-color: rgba(255, 255, 255, 0.6);
        background: rgba(255, 255, 255, 0.5);
    }

    /* 移动端禁用密钥卡片悬停 */
    @media (max-width: 768px) {
        div[data-testid="stHorizontalBlock"]:hover {
            transform: none;
        }
    }

    /* 密钥代码显示 */
    .key-code {
        background: rgba(255, 255, 255, 0.3);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        padding: 0.75rem 1rem;
        border-radius: 10px;
        font-family: 'SF Mono', Monaco, 'Cascadia Mono', monospace;
        font-size: 0.875rem;
        color: #1f2937;
        overflow: hidden;
        text-overflow: ellipsis;
        border: 1px solid rgba(255, 255, 255, 0.4);
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.3);
        word-break: break-all; 
    }

    /* 移动端密钥代码调整 */
    @media (max-width: 768px) {
        .key-code {
            font-size: 0.75rem;
            padding: 0.625rem 0.875rem;
            border-radius: 8px;
        }
    }

    .key-id {
        font-weight: 600;
        color: #374151;
        min-width: 2.5rem;
    }

    /* 移动端密钥ID调整 */
    @media (max-width: 768px) {
        .key-id {
            min-width: 2rem;
            font-size: 0.875rem;
        }
    }

    .key-meta {
        font-size: 0.8125rem;
        color: #6b7280;
        margin-top: 0.375rem;
    }

    /* 移动端密钥元数据调整 */
    @media (max-width: 768px) {
        .key-meta {
            font-size: 0.75rem;
            margin-top: 0.25rem;
        }
    }

    /* 标签页玻璃效果 */
    .stTabs [data-testid="stTabBar"] {
        gap: 1.5rem;
        border-bottom: 1px solid rgba(99, 102, 241, 0.2);
        padding: 0;
        margin-bottom: 1.5rem;
        background: rgba(255, 255, 255, 0.3);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-radius: 16px 16px 0 0;
        border: 1px solid rgba(255, 255, 255, 0.4);
        border-bottom: none;
        box-shadow: 
            0 4px 16px rgba(0, 0, 0, 0.04),
            inset 0 1px 0 rgba(255, 255, 255, 0.4);
        overflow-x: auto; 
        scrollbar-width: none;
        -ms-overflow-style: none;
    }

    .stTabs [data-testid="stTabBar"]::-webkit-scrollbar {
        display: none;
    }

    .stTabs [data-testid="stTabBar"] button {
        font-weight: 500;
        color: #6b7280;
        padding: 1rem 1.5rem;
        border-bottom: 2px solid transparent;
        font-size: 0.9375rem;
        letter-spacing: 0.02em;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border-radius: 12px 12px 0 0;
        background: transparent;
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        white-space: nowrap; 
        min-width: auto;
        flex-shrink: 0; 
    }

    .stTabs [data-testid="stTabBar"] button:hover {
        background: rgba(255, 255, 255, 0.4);
        color: #374151;
        transform: translateY(-1px);
    }

    /* 移动端标签页悬停优化 */
    @media (max-width: 768px) {
        .stTabs [data-testid="stTabBar"] button:hover {
            transform: none;
        }

        .stTabs [data-testid="stTabBar"] button:active {
            background: rgba(255, 255, 255, 0.5);
        }
    }

    .stTabs [data-testid="stTabBar"] button[aria-selected="true"] {
        color: #1f2937;
        border-bottom-color: #6366f1;
        background: rgba(255, 255, 255, 0.5);
        box-shadow: 
            0 -4px 12px rgba(99, 102, 241, 0.15),
            inset 0 1px 0 rgba(255, 255, 255, 0.4);
    }

    /* Alert消息玻璃效果 */
    [data-testid="stAlert"] {
        border: none !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border-radius: 14px !important;
        border: 1px solid rgba(255, 255, 255, 0.4) !important;
        box-shadow: 
            0 8px 24px rgba(0, 0, 0, 0.06),
            inset 0 1px 0 rgba(255, 255, 255, 0.4) !important;
        padding: 1rem 1.25rem !important;
        margin: 0.75rem 0 !important;
    }

    [data-testid="stAlert"][kind="info"] {
        background: rgba(59, 130, 246, 0.1) !important;
        color: #1e40af !important;
        border-color: rgba(59, 130, 246, 0.3) !important;
    }

    [data-testid="stAlert"][kind="success"] {
        background: rgba(16, 185, 129, 0.1) !important;
        color: #065f46 !important;
        border-color: rgba(16, 185, 129, 0.3) !important;
    }

    [data-testid="stAlert"][kind="warning"] {
        background: rgba(245, 158, 11, 0.1) !important;
        color: #92400e !important;
        border-color: rgba(245, 158, 11, 0.3) !important;
    }

    [data-testid="stAlert"][kind="error"] {
        background: rgba(239, 68, 68, 0.1) !important;
        color: #991b1b !important;
        border-color: rgba(239, 68, 68, 0.3) !important;
    }

    /* 图表容器玻璃效果 */
    .js-plotly-plot .plotly {
        border-radius: 16px;
        overflow: hidden;
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        background: rgba(255, 255, 255, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.5);
        box-shadow: 
            0 12px 40px rgba(0, 0, 0, 0.05),
            inset 0 1px 0 rgba(255, 255, 255, 0.4);
        pointer-events: none;
        user-select: none; 
    }

    /* 禁用图表内部元素的交互 */
    .js-plotly-plot .plotly svg,
    .js-plotly-plot .plotly canvas,
    .js-plotly-plot .plotly .plotly-plot,
    .js-plotly-plot .plotly .svg-container {
        pointer-events: none !important;
        touch-action: none !important;
        user-select: none !important;
    }

    /* 移动端图表调整 */
    @media (max-width: 768px) {
        .js-plotly-plot .plotly {
            border-radius: 14px;
        }
    }

    /* 表格玻璃效果 */
    .stDataFrame {
        border-radius: 14px;
        overflow: hidden;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        background: rgba(255, 255, 255, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.4);
        box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.05),
            inset 0 1px 0 rgba(255, 255, 255, 0.4);
    }

    /* 移动端表格调整 */
    @media (max-width: 768px) {
        .stDataFrame {
            border-radius: 12px;
            font-size: 0.875rem;
        }
    }

    /* 标题样式 */
    h1, h2, h3 {
        color: #1f2937;
    }

    h1 {
        background: linear-gradient(135deg, #1f2937 0%, #4f46e5 50%, #7c3aed 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2.5rem;
        font-weight: 700;
        letter-spacing: -0.025em;
        margin-bottom: 0.5rem;
    }

    h2 {
        font-size: 1.875rem;
        font-weight: 600;
        letter-spacing: -0.02em;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }

    h3 {
        font-size: 1.25rem;
        font-weight: 600;
        letter-spacing: -0.01em;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
    }

    /* 页面副标题 */
    .page-subtitle {
        font-size: 1rem;
        color: #6b7280;
        margin-bottom: 1.5rem;
        font-weight: 400;
    }

    /* 移动端页面副标题调整 */
    @media (max-width: 768px) {
        .page-subtitle {
            font-size: 0.875rem;
            margin-bottom: 1rem;
        }
    }

    /* 分割线玻璃效果 */
    hr {
        margin: 1.5rem 0 !important;
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, 
            transparent, 
            rgba(99, 102, 241, 0.3) 20%, 
            rgba(99, 102, 241, 0.5) 50%, 
            rgba(99, 102, 241, 0.3) 80%, 
            transparent
        ) !important;
        position: relative;
    }

    /* 移动端分割线调整 */
    @media (max-width: 768px) {
        hr {
            margin: 1rem 0 !important;
        }
    }

    hr::after {
        content: '';
        position: absolute;
        top: 1px;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, 
            transparent, 
            rgba(255, 255, 255, 0.3) 50%, 
            transparent
        );
    }

    .main .block-container {
        max-height: none !important;
        overflow: visible !important;
    }

    .stApp > div {
        overflow: visible !important;
    }

    body {
        overflow-x: hidden;
        overflow-y: auto;
    }

    .stApp {
        overflow-x: hidden;
        overflow-y: auto;
    }

    /* 自定义滚动条 */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }

    /* 移动端隐藏滚动条 */
    @media (max-width: 768px) {
        ::-webkit-scrollbar {
            width: 0px;
            height: 0px;
        }
    }

    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 3px;
    }

    ::-webkit-scrollbar-thumb {
        background: rgba(99, 102, 241, 0.3);
        border-radius: 3px;
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
    }

    ::-webkit-scrollbar-thumb:hover {
        background: rgba(99, 102, 241, 0.5);
    }

    /* 选择文本样式 */
    ::selection {
        background: rgba(99, 102, 241, 0.2);
        color: #1f2937;
    }

    ::-moz-selection {
        background: rgba(99, 102, 241, 0.2);
        color: #1f2937;
    }

    /* 移动端顶部导航栏隐藏按钮优化 */
    @media (max-width: 768px) {
        /* 侧边栏切换按钮样式 */
        button[kind="secondary"] {
            background: rgba(99, 102, 241, 0.1) !important;
            backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important;
            border: 1px solid rgba(99, 102, 241, 0.3) !important;
            border-radius: 12px !important;
            box-shadow: 
                0 4px 16px rgba(99, 102, 241, 0.15),
                inset 0 1px 0 rgba(255, 255, 255, 0.4) !important;
            color: #4f46e5 !important;
            font-weight: 500 !important;
            min-height: 44px !important;
        }
    }

    /* 移动端性能优化 */
    @media (max-width: 768px) {
        * {
            -webkit-tap-highlight-color: transparent;
            -webkit-touch-callout: none;
        }

        /* 允许文本和特定元素的选择 */
        input, textarea, .key-code, [data-testid="stAlert"], p, span, div {
            -webkit-user-select: text !important;
            -khtml-user-select: text !important;
            -moz-user-select: text !important;
            -ms-user-select: text !important;
            user-select: text !important;
        }

        /* 按钮和导航保持不可选择 */
        button, .stRadio label, .sidebar-logo {
            -webkit-user-select: none !important;
            -khtml-user-select: none !important;
            -moz-user-select: none !important;
            -ms-user-select: none !important;
            user-select: none !important;
        }

        .stApp {
            overflow-x: hidden;
            overflow-y: auto;
        }
    }

    /* 移动端横屏适配 */
    @media (max-width: 1024px) and (orientation: landscape) {
        .block-container {
            padding: 1rem;
            margin: 0.5rem;
        }

        [data-testid="metric-container"] {
            padding: 1rem 1.25rem;
        }

        h1 {
            font-size: 2rem !important;
        }

        h2 {
            font-size: 1.5rem !important;
        }
    }

    /* 状态卡片样式 */
    .status-card-style {
        background: rgba(255, 255, 255, 0.4);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.5);
        border-radius: 16px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 
            0 10px 32px rgba(0, 0, 0, 0.06),
            inset 0 1px 0 rgba(255, 255, 255, 0.5);
    }
</style>
""", unsafe_allow_html=True)


# --- 获取服务状态函数 ---
@st.cache_data(ttl=10)
def get_service_status():
    """获取服务状态，用于侧边栏显示"""
    try:
        health = check_service_health()
        stats = get_cached_stats()
        if health and stats:
            return {
                'online': True,
                'active_keys': stats.get('active_gemini_keys', 0),
                'healthy_keys': stats.get('healthy_gemini_keys', 0)
            }
    except:
        pass
    return {'online': False, 'active_keys': 0, 'healthy_keys': 0}


# --- 玻璃拟态侧边栏 ---
with st.sidebar:
    # Logo区域
    st.markdown('''
    <div class="sidebar-logo">
        <div class="sidebar-logo-icon">🌠</div>
        <div class="sidebar-logo-text">
            <div class="sidebar-logo-title">Gemini Proxy</div>
            <div class="sidebar-logo-subtitle">多Key智能轮询系统</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

    # 导航标题
    st.markdown('<div class="sidebar-section-title">主菜单</div>', unsafe_allow_html=True)

    # 创建带图标的导航选项
    nav_options = {
        "🏠 控制台": "控制台",
        "⚙️ 模型配置": "模型配置",
        "🔑 密钥管理": "密钥管理",
        "🔧 系统设置": "系统设置"
    }

    # 使用自定义HTML为导航项添加图标
    page_display = st.radio(
        "导航",
        list(nav_options.keys()),
        label_visibility="collapsed",
        key="nav_radio"
    )

    # 转换显示值为实际页面值
    page = nav_options[page_display]

    # 添加状态指示器
    st.markdown('<div class="sidebar-status">', unsafe_allow_html=True)

    # 服务状态
    service_status = get_service_status()
    status_class = "online" if service_status['online'] else "offline"
    status_text = "在线" if service_status['online'] else "离线"

    st.markdown(f'''
    <div class="sidebar-status-card">
        <div class="sidebar-status-title">服务状态</div>
        <div class="sidebar-status-content">
            <div class="sidebar-status-indicator {status_class}"></div>
            <div class="sidebar-status-text">{status_text}</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    # API密钥状态
    if service_status['online']:
        st.markdown(f'''
        <div class="sidebar-status-card">
            <div class="sidebar-status-title">API 密钥</div>
            <div class="sidebar-status-content">
                <div class="sidebar-status-text">{service_status['healthy_keys']} / {service_status['active_keys']} 正常</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # 底部信息
    st.markdown(f'''
    <div class="sidebar-footer">
        <div class="sidebar-footer-content">
            <div class="sidebar-footer-item">
                <span>版本 v1.3.2</span>
            </div>
            <div class="sidebar-footer-item">
                <a href="{API_BASE_URL}/docs" target="_blank" class="sidebar-footer-link">API 文档</a>
                <span>·</span>
                <a href="https://github.com/arain119" target="_blank" class="sidebar-footer-link">GitHub</a>
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

# --- 主页面内容 ---
if page == "控制台":
    st.title("控制台")
    st.markdown('<p class="page-subtitle">实时监控服务运行状态和使用情况</p>', unsafe_allow_html=True)

    # 获取统计数据
    stats_data = get_cached_stats()
    status_data = get_cached_status()

    if not stats_data or not status_data:
        st.error("无法获取服务数据，请检查服务连接")
        st.stop()

    # 健康状态提示和刷新按钮
    st.markdown('<div class="health-status-row">', unsafe_allow_html=True)
    col1, col2 = st.columns([11, 1])

    with col1:
        health_summary = stats_data.get('health_summary', {})
        if health_summary:
            total_active = health_summary.get('total_active', 0)
            healthy_count = health_summary.get('healthy', 0)
            unhealthy_count = health_summary.get('unhealthy', 0)

            if unhealthy_count > 0:
                st.error(f"发现 {unhealthy_count} 个异常密钥，共 {total_active} 个激活密钥")
            elif healthy_count > 0:
                st.success(f"所有 {healthy_count} 个密钥运行正常")
            else:
                st.info("暂无激活的密钥")

    with col2:
        if st.button("⟳", help="刷新数据", key="refresh_dashboard"):
            st.cache_data.clear()
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # 核心指标
    st.markdown("### 核心指标")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        gemini_keys = stats_data.get('active_gemini_keys', 0)
        healthy_gemini = stats_data.get('healthy_gemini_keys', 0)
        st.metric(
            "Gemini密钥",
            gemini_keys,
            delta=f"{healthy_gemini} 正常"
        )

    with col2:
        user_keys = stats_data.get('active_user_keys', 0)
        total_user = stats_data.get('user_keys', 0)
        st.metric(
            "用户密钥",
            user_keys,
            delta=f"共 {total_user} 个"
        )

    with col3:
        models = stats_data.get('supported_models', [])
        st.metric("支持模型", len(models))

    with col4:
        thinking_status = "启用" if status_data.get('thinking_enabled', False) else "禁用"
        st.metric("思考功能", thinking_status)

    # 使用率分析
    st.markdown("### 使用率分析")

    usage_stats = stats_data.get('usage_stats', {})
    if usage_stats and models:
        # 准备数据
        model_data = []
        for model in models:
            stats = usage_stats.get(model, {'minute': {'requests': 0}, 'day': {'requests': 0}})

            model_config_data = get_cached_model_config(model)
            if not model_config_data:
                rpm_limit = 10 if 'flash' in model else 5
                rpd_limit = 250 if 'flash' in model else 100
            else:
                rpm_limit = model_config_data.get('total_rpm_limit', 10)
                rpd_limit = model_config_data.get('total_rpd_limit', 250)

            rpm_used = stats['minute']['requests']
            rpm_percent = (rpm_used / rpm_limit * 100) if rpm_limit > 0 else 0

            rpd_used = stats['day']['requests']
            rpd_percent = (rpd_used / rpd_limit * 100) if rpd_limit > 0 else 0

            model_data.append({
                'Model': model,
                'RPM Used': rpm_used,
                'RPM Limit': rpm_limit,
                'RPM %': rpm_percent,
                'RPD Used': rpd_used,
                'RPD Limit': rpd_limit,
                'RPD %': rpd_percent
            })

        if model_data:
            df = pd.DataFrame(model_data)

            # 创建图表
            col1, col2 = st.columns(2)

            with col1:
                fig_rpm = go.Figure()
                fig_rpm.add_trace(go.Bar(
                    x=df['Model'],
                    y=df['RPM %'],
                    text=[f"{x:.1f}%" for x in df['RPM %']],
                    textposition='outside',
                    marker_color='rgba(99, 102, 241, 0.8)',
                    marker_line=dict(width=0),
                    hovertemplate='<b>%{x}</b><br>使用率: %{y:.1f}%<br>当前: %{customdata[0]:,}<br>限制: %{customdata[1]:,}<extra></extra>',
                    customdata=df[['RPM Used', 'RPM Limit']].values
                ))
                fig_rpm.update_layout(
                    title="每分钟请求数 (RPM)",
                    title_font=dict(size=16, color='#1f2937', family='-apple-system, BlinkMacSystemFont'),
                    yaxis_title="使用率 (%)",
                    yaxis_range=[0, max(100, df['RPM %'].max() * 1.2) if len(df) > 0 else 100],
                    height=340,
                    showlegend=False,
                    plot_bgcolor='rgba(255, 255, 255, 0.3)',
                    paper_bgcolor='rgba(255, 255, 255, 0.3)',
                    font=dict(family='-apple-system, BlinkMacSystemFont', color='#374151', size=12),
                    yaxis=dict(gridcolor='rgba(107, 114, 128, 0.2)', zerolinecolor='rgba(107, 114, 128, 0.3)',
                               color='#374151'),
                    xaxis=dict(linecolor='rgba(107, 114, 128, 0.3)', color='#374151'),
                    bargap=0.4,
                    margin=dict(l=0, r=0, t=50, b=0)
                )
                st.plotly_chart(fig_rpm, use_container_width=True, config={
                    'displayModeBar': False,
                    'staticPlot': True,  # 禁用所有交互
                    'scrollZoom': False,
                    'doubleClick': False,
                    'showTips': False,
                    'displaylogo': False,
                    'modeBarButtonsToRemove': ['select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d',
                                               'resetScale2d']
                })

            with col2:
                fig_rpd = go.Figure()
                fig_rpd.add_trace(go.Bar(
                    x=df['Model'],
                    y=df['RPD %'],
                    text=[f"{x:.1f}%" for x in df['RPD %']],
                    textposition='outside',
                    marker_color='rgba(16, 185, 129, 0.8)',
                    marker_line=dict(width=0),
                    hovertemplate='<b>%{x}</b><br>使用率: %{y:.1f}%<br>当前: %{customdata[0]:,}<br>限制: %{customdata[1]:,}<extra></extra>',
                    customdata=df[['RPD Used', 'RPD Limit']].values
                ))
                fig_rpd.update_layout(
                    title="每日请求数 (RPD)",
                    title_font=dict(size=16, color='#1f2937', family='-apple-system, BlinkMacSystemFont'),
                    yaxis_title="使用率 (%)",
                    yaxis_range=[0, max(100, df['RPD %'].max() * 1.2) if len(df) > 0 else 100],
                    height=340,
                    showlegend=False,
                    plot_bgcolor='rgba(255, 255, 255, 0.3)',
                    paper_bgcolor='rgba(255, 255, 255, 0.3)',
                    font=dict(family='-apple-system, BlinkMacSystemFont', color='#374151', size=12),
                    yaxis=dict(gridcolor='rgba(107, 114, 128, 0.2)', zerolinecolor='rgba(107, 114, 128, 0.3)',
                               color='#374151'),
                    xaxis=dict(linecolor='rgba(107, 114, 128, 0.3)', color='#374151'),
                    bargap=0.4,
                    margin=dict(l=0, r=0, t=50, b=0)
                )
                st.plotly_chart(fig_rpd, use_container_width=True, config={
                    'displayModeBar': False,
                    'staticPlot': True,  # 禁用所有交互
                    'scrollZoom': False,
                    'doubleClick': False,
                    'showTips': False,
                    'displaylogo': False,
                    'modeBarButtonsToRemove': ['select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d',
                                               'resetScale2d']
                })

            # 详细数据表
            with st.expander("查看详细数据"):
                display_df = df[['Model', 'RPM Used', 'RPM Limit', 'RPM %', 'RPD Used', 'RPD Limit', 'RPD %']].copy()
                display_df.columns = ['模型', '分钟请求', '分钟限制', '分钟使用率', '日请求', '日限制', '日使用率']
                display_df['分钟使用率'] = display_df['分钟使用率'].apply(lambda x: f"{x:.1f}%")
                display_df['日使用率'] = display_df['日使用率'].apply(lambda x: f"{x:.1f}%")
                st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("暂无使用数据")

elif page == "密钥管理":
    st.title("密钥管理")
    st.markdown('<p class="page-subtitle">管理 Gemini API 密钥和用户访问令牌</p>', unsafe_allow_html=True)

    # 刷新按钮
    col1, col2 = st.columns([10, 1])
    with col2:
        if st.button("⟳", help="刷新数据", key="refresh_keys"):
            st.cache_data.clear()
            st.rerun()

    tab1, tab2 = st.tabs(["Gemini 密钥", "用户密钥"])

    with tab1:
        st.markdown("#### 添加新密钥")

        with st.form("add_gemini_key"):
            new_key = st.text_area(
                "Gemini API 密钥",
                height=120,
                placeholder="AIzaSy...\n\n支持批量添加：\n- 多个密钥可用逗号、分号或换行符分隔\n- 示例：AIzaSy123..., AIzaSy456...; AIzaSy789...",
                help="从 Google AI Studio 获取。支持批量添加：用逗号、分号、换行符或多个空格分隔多个密钥"
            )
            submitted = st.form_submit_button("添加密钥", type="primary")

            if submitted and new_key:
                result = call_api('/admin/config/gemini-key', 'POST', {'key': new_key})
                if result:
                    if result.get('success'):
                        # 显示成功消息
                        st.success(result.get('message', '密钥添加成功'))

                        # 如果是批量添加，显示详细结果
                        total_processed = result.get('total_processed', 1)
                        if total_processed > 1:
                            successful = result.get('successful_adds', 0)
                            failed = result.get('failed_adds', 0)

                            # 创建详细信息展开器
                            with st.expander(f"查看详细结果 (处理了 {total_processed} 个密钥)", expanded=failed > 0):
                                if successful > 0:
                                    st.markdown("**✅ 成功添加的密钥：**")
                                    success_details = [detail for detail in result.get('details', []) if '✅' in detail]
                                    for detail in success_details:
                                        st.markdown(f"- {detail}")

                                if result.get('duplicate_keys'):
                                    st.markdown("**⚠️ 重复的密钥：**")
                                    for duplicate in result.get('duplicate_keys', []):
                                        st.warning(f"- {duplicate}")

                                if result.get('invalid_keys'):
                                    st.markdown("**❌ 无效的密钥：**")
                                    for invalid in result.get('invalid_keys', []):
                                        st.error(f"- {invalid}")

                        st.cache_data.clear()
                        time.sleep(1)
                        st.rerun()
                    else:
                        # 显示失败消息和详细信息
                        st.error(result.get('message', '添加失败'))

                        # 显示失败详情
                        if result.get('invalid_keys'):
                            with st.expander("查看失败详情"):
                                st.markdown("**格式错误的密钥：**")
                                for invalid in result.get('invalid_keys', []):
                                    st.write(f"- {invalid}")

                        if result.get('duplicate_keys'):
                            with st.expander("重复的密钥"):
                                for duplicate in result.get('duplicate_keys', []):
                                    st.write(f"- {duplicate}")
                else:
                    st.error("网络错误，请重试")

        st.markdown('<hr style="margin: 2rem 0;">', unsafe_allow_html=True)

        # 现有密钥
        col1, col2, col3 = st.columns([4, 1, 1])
        with col1:
            st.markdown("#### 现有密钥")
        with col2:
            if st.button("健康检测", help="检测所有密钥状态", key="health_check_gemini"):
                with st.spinner("检测中..."):
                    result = check_all_keys_health()
                    if result and result.get('success'):
                        st.success(result['message'])
                        st.cache_data.clear()
                        time.sleep(1)
                        st.rerun()
        with col3:
            show_full_keys = st.checkbox("显示完整", key="show_gemini_full")

        # 获取密钥列表
        gemini_keys_data = get_cached_gemini_keys()
        if gemini_keys_data and gemini_keys_data.get('success'):
            gemini_keys = gemini_keys_data.get('keys', [])

            if gemini_keys:
                # 统计信息
                active_count = len([k for k in gemini_keys if k.get('status') == 1])
                healthy_count = len(
                    [k for k in gemini_keys if k.get('status') == 1 and k.get('health_status') == 'healthy'])

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f'<div style="color: #374151; font-weight: 500;">共 {len(gemini_keys)} 个密钥</div>',
                                unsafe_allow_html=True)
                with col2:
                    st.markdown(f'<div style="color: #374151; font-weight: 500;">激活 {active_count} 个</div>',
                                unsafe_allow_html=True)
                with col3:
                    st.markdown(f'<div style="color: #059669; font-weight: 500;">正常 {healthy_count} 个</div>',
                                unsafe_allow_html=True)

                valid_keys = []
                invalid_count = 0

                for key_info in gemini_keys:
                    # 验证数据完整性
                    if (isinstance(key_info, dict) and
                            'id' in key_info and
                            'key' in key_info and
                            'status' in key_info and
                            key_info['id'] is not None and
                            key_info['key'] is not None):
                        valid_keys.append(key_info)
                    else:
                        invalid_count += 1

                # 如果有无效数据，给出提示
                if invalid_count > 0:
                    st.warning(f"发现 {invalid_count} 个数据不完整的密钥，已跳过显示")

                # 渲染有效的密钥
                for key_info in valid_keys:
                    try:
                        # 创建一个容器来包含整个密钥卡片
                        container = st.container()
                        with container:
                            # 使用列布局来实现卡片内的元素
                            col1, col2, col3, col4, col5, col6 = st.columns([0.5, 3.5, 0.9, 0.9, 0.8, 0.8])

                            with col1:
                                st.markdown(f'<div class="key-id">#{key_info.get("id", "N/A")}</div>',
                                            unsafe_allow_html=True)

                            with col2:
                                st.markdown(f'''
                                <div>
                                    <div class="key-code">{mask_key(key_info.get('key', ''), show_full_keys)}</div>
                                    <div class="key-meta">
                                        {f"成功率 {key_info.get('success_rate', 1.0) * 100:.1f}% · 响应时间 {key_info.get('avg_response_time', 0.0):.2f}s · 请求数 {key_info.get('total_requests', 0)}"
                                if key_info.get('total_requests', 0) > 0 else "尚未使用"}
                                    </div>
                                </div>
                                ''', unsafe_allow_html=True)

                            with col3:
                                st.markdown(f'''
                                <span class="status-badge status-{key_info.get('health_status', 'unknown')}">
                                    {format_health_status(key_info.get('health_status', 'unknown'))}
                                </span>
                                ''', unsafe_allow_html=True)

                            with col4:
                                st.markdown(f'''
                                <span class="status-badge status-{'active' if key_info.get('status', 0) == 1 else 'inactive'}">
                                    {'激活' if key_info.get('status', 0) == 1 else '禁用'}
                                </span>
                                ''', unsafe_allow_html=True)

                            with col5:
                                key_id = key_info.get('id')
                                status = key_info.get('status', 0)
                                if key_id is not None:
                                    toggle_text = "禁用" if status == 1 else "激活"
                                    if st.button(toggle_text, key=f"toggle_g_{key_id}", use_container_width=True):
                                        if toggle_key_status('gemini', key_id):
                                            st.success("状态已更新")
                                            st.cache_data.clear()
                                            time.sleep(1)
                                            st.rerun()

                            with col6:
                                if key_id is not None:
                                    if st.button("删除", key=f"del_g_{key_id}", use_container_width=True):
                                        if delete_key('gemini', key_id):
                                            st.success("删除成功")
                                            st.cache_data.clear()
                                            time.sleep(1)
                                            st.rerun()

                    except Exception as e:
                        # 异常时显示错误信息而不是空白
                        st.error(f"渲染密钥 #{key_info.get('id', '?')} 时出错: {str(e)}")

                # 如果没有有效密钥
                if not valid_keys:
                    st.warning("所有密钥数据都不完整，请检查数据源")

            else:
                st.info("暂无密钥，请添加第一个 Gemini API 密钥")
        else:
            st.error("无法获取密钥列表")

    with tab2:
        st.markdown("#### 生成访问密钥")

        with st.form("generate_user_key"):
            key_name = st.text_input("密钥名称", placeholder="例如：生产环境、测试环境")
            submitted = st.form_submit_button("生成新密钥", type="primary")

            if submitted:
                name = key_name if key_name else '未命名'
                result = call_api('/admin/config/user-key', 'POST', {'name': name})
                if result and result.get('success'):
                    new_key = result.get('key')
                    st.success("密钥生成成功")
                    st.warning("请立即保存此密钥，它不会再次显示")
                    st.code(new_key, language=None)

                    with st.expander("使用示例"):
                        st.code(f"""
import openai

client = openai.OpenAI(
    api_key="{new_key}",
    base_url="{API_BASE_URL}/v1"
)

response = client.chat.completions.create(
    model="gemini-2.5-flash",
    messages=[{{"role": "user", "content": "Hello"}}]
)
                        """, language="python")

                    st.cache_data.clear()

        st.markdown('<hr style="margin: 2rem 0;">', unsafe_allow_html=True)

        # 现有密钥
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown("#### 现有密钥")
        with col2:
            show_full_user_keys = st.checkbox("显示完整", key="show_user_full")

        # 获取用户密钥
        user_keys_data = get_cached_user_keys()
        if user_keys_data and user_keys_data.get('success'):
            user_keys = user_keys_data.get('keys', [])

            if user_keys:
                active_count = len([k for k in user_keys if k['status'] == 1])
                st.markdown(
                    f'<div style="color: #6b7280; font-weight: 500; margin-bottom: 1rem;">共 {len(user_keys)} 个密钥，{active_count} 个激活</div>',
                    unsafe_allow_html=True)

                for key_info in user_keys:
                    container = st.container()
                    with container:
                        # 使用列布局来实现卡片内的元素
                        col1, col2, col3, col4, col5 = st.columns([0.5, 3.5, 0.9, 0.8, 0.8])

                        with col1:
                            st.markdown(f'<div class="key-id">#{key_info["id"]}</div>', unsafe_allow_html=True)

                        with col2:
                            st.markdown(f'''
                            <div>
                                <div class="key-code">{mask_key(key_info['key'], show_full_user_keys)}</div>
                                <div class="key-meta">
                                    {f"名称: {key_info['name']}" if key_info.get('name') else "未命名"} · 
                                    {f"最后使用: {key_info['last_used'][:16]}" if key_info.get('last_used') else "从未使用"}
                                </div>
                            </div>
                            ''', unsafe_allow_html=True)

                        with col3:
                            st.markdown(f'''
                            <span class="status-badge status-{'active' if key_info['status'] == 1 else 'inactive'}">
                                {'激活' if key_info['status'] == 1 else '停用'}
                            </span>
                            ''', unsafe_allow_html=True)

                        with col4:
                            toggle_text = "停用" if key_info['status'] == 1 else "激活"
                            if st.button(toggle_text, key=f"toggle_u_{key_info['id']}", use_container_width=True):
                                if toggle_key_status('user', key_info['id']):
                                    st.success("状态已更新")
                                    st.cache_data.clear()
                                    time.sleep(1)
                                    st.rerun()

                        with col5:
                            if st.button("删除", key=f"del_u_{key_info['id']}", use_container_width=True):
                                if delete_key('user', key_info['id']):
                                    st.success("删除成功")
                                    st.cache_data.clear()
                                    time.sleep(1)
                                    st.rerun()

            else:
                st.info("暂无用户密钥")

elif page == "模型配置":
    st.title("模型配置")
    st.markdown('<p class="page-subtitle">调整模型参数和使用限制</p>', unsafe_allow_html=True)

    stats_data = get_cached_stats()
    status_data = get_cached_status()

    if not stats_data or not status_data:
        st.error("无法获取数据")
        st.stop()

    models = status_data.get('models', [])
    if not models:
        st.warning("暂无可用模型")
        st.stop()

    # 信息提示
    st.info('显示的限制针对单个 API Key，总限制会根据健康密钥数量自动倍增')

    for model in models:
        st.markdown(f"### {model}")

        current_config = get_cached_model_config(model)
        if not current_config or not current_config.get('success'):
            st.warning(f"无法加载模型配置")
            continue

        with st.form(f"model_config_{model}"):
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                rpm = st.number_input(
                    "RPM (每分钟请求)",
                    min_value=1,
                    value=current_config.get('single_api_rpm_limit', 10 if 'flash' in model else 5),
                    key=f"rpm_{model}"
                )

            with col2:
                rpd = st.number_input(
                    "RPD (每日请求)",
                    min_value=1,
                    value=current_config.get('single_api_rpd_limit', 250 if 'flash' in model else 100),
                    key=f"rpd_{model}"
                )

            with col3:
                tpm = st.number_input(
                    "TPM (每分钟令牌)",
                    min_value=1000,
                    value=current_config.get('single_api_tpm_limit', 250000),
                    key=f"tpm_{model}"
                )

            with col4:
                status_options = {1: "激活", 0: "禁用"}
                current_status = current_config.get('status', 1)
                new_status = st.selectbox(
                    "状态",
                    options=list(status_options.values()),
                    index=0 if current_status == 1 else 1,
                    key=f"status_{model}"
                )

            if st.form_submit_button("保存配置", type="primary", use_container_width=True):
                update_data = {
                    "single_api_rpm_limit": rpm,
                    "single_api_rpd_limit": rpd,
                    "single_api_tpm_limit": tpm,
                    "status": 1 if new_status == "激活" else 0
                }

                result = call_api(f'/admin/models/{model}', 'POST', data=update_data)
                if result and result.get('success'):
                    st.success("配置已保存")
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("保存失败")

elif page == "系统设置":
    st.title("系统设置")
    st.markdown('<p class="page-subtitle">配置高级功能和系统参数</p>', unsafe_allow_html=True)

    stats_data = get_cached_stats()
    status_data = get_cached_status()

    if not stats_data or not status_data:
        st.error("无法获取配置数据")
        st.stop()

    # 包含故障转移配置的标签页
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "思考模式", "提示词注入", "流式模式", "负载均衡", "故障转移", "自动清理", "系统信息", "防检测"
    ])

    with tab1:
        st.markdown("#### 思考模式配置")
        st.markdown("启用推理功能以提高复杂查询的响应质量")

        thinking_config = stats_data.get('thinking_config', {})

        # 状态概览卡片
        current_status = "已启用" if thinking_config.get('enabled', False) else "已禁用"
        status_color = "#10b981" if thinking_config.get('enabled', False) else "#6b7280"

        st.markdown(f'''
        <div style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(168, 85, 247, 0.1) 100%); 
                    border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h5 style="margin: 0; color: #374151; font-size: 1.1rem;">当前状态</h5>
                    <p style="margin: 0.5rem 0 0 0; color: #6b7280; font-size: 0.9rem;">
                        思考预算: {thinking_config.get('budget', -1)} | 
                        包含过程: {'是' if thinking_config.get('include_thoughts', False) else '否'}
                    </p>
                </div>
                <div style="background: {status_color}; color: white; padding: 0.5rem 1rem; border-radius: 8px; font-weight: 500;">
                    {current_status}
                </div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

        with st.form("thinking_config_form"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**基础配置**")
                thinking_enabled = st.checkbox(
                    "启用思考模式",
                    value=thinking_config.get('enabled', False),
                    help="开启后模型会进行推理思考以提供更准确的回答"
                )

                include_thoughts = st.checkbox(
                    "在响应中包含思考过程",
                    value=thinking_config.get('include_thoughts', False),
                    help="用户可以看到模型的思考过程"
                )

            with col2:
                st.markdown("**思考预算配置**")
                budget_options = {
                    "自动": -1,
                    "禁用": 0,
                    "低 (4k)": 4096,
                    "中 (8k)": 8192,
                    "Flash最大 (24k)": 24576,
                    "Pro最大 (32k)": 32768
                }

                current_budget = thinking_config.get('budget', -1)
                selected_option = next((k for k, v in budget_options.items() if v == current_budget), "自动")

                budget_option = st.selectbox(
                    "思考预算",
                    options=list(budget_options.keys()),
                    index=list(budget_options.keys()).index(selected_option),
                    help="控制模型思考的深度和复杂度"
                )

            # 配置说明
            st.markdown("**配置说明**")
            st.info("思考模式会增加响应时间，但能显著提高复杂问题的回答质量。建议在需要深度分析的场景中启用。")

            if st.form_submit_button("保存配置", type="primary", use_container_width=True):
                update_data = {
                    "enabled": thinking_enabled,
                    "budget": budget_options[budget_option],
                    "include_thoughts": include_thoughts
                }

                result = call_api('/admin/config/thinking', 'POST', data=update_data)
                if result and result.get('success'):
                    st.success("配置已保存")
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()

    with tab2:
        st.markdown("#### 提示词注入配置")
        st.markdown("为所有请求自动添加自定义指令，实现统一的行为控制")

        inject_config = stats_data.get('inject_config', {})

        # 状态概览
        current_enabled = inject_config.get('enabled', False)
        current_position = inject_config.get('position', 'system')
        position_names = {
            'system': '系统消息',
            'user_prefix': '用户消息前',
            'user_suffix': '用户消息后'
        }

        st.markdown(f'''
        <div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.1) 100%); 
                    border: 1px solid rgba(16, 185, 129, 0.2); border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h5 style="margin: 0; color: #374151; font-size: 1.1rem;">注入状态</h5>
                    <p style="margin: 0.5rem 0 0 0; color: #6b7280; font-size: 0.9rem;">
                        位置: {position_names.get(current_position, '未知')} | 
                        内容长度: {len(inject_config.get('content', ''))} 字符
                    </p>
                </div>
                <div style="background: {'#10b981' if current_enabled else '#6b7280'}; color: white; padding: 0.5rem 1rem; border-radius: 8px; font-weight: 500;">
                    {'已启用' if current_enabled else '已禁用'}
                </div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

        with st.form("inject_prompt_form"):
            col1, col2 = st.columns([1, 1])

            with col1:
                st.markdown("**注入配置**")
                inject_enabled = st.checkbox(
                    "启用提示词注入",
                    value=inject_config.get('enabled', False),
                    help="开启后所有请求都会自动注入指定的提示词"
                )

                position_options = {
                    'system': '系统消息',
                    'user_prefix': '用户消息前',
                    'user_suffix': '用户消息后'
                }

                position = st.selectbox(
                    "注入位置",
                    options=list(position_options.keys()),
                    format_func=lambda x: position_options[x],
                    index=list(position_options.keys()).index(inject_config.get('position', 'system')),
                    help="选择提示词在消息中的插入位置"
                )

            with col2:
                st.markdown("**位置说明**")
                position_descriptions = {
                    'system': "作为系统消息发送，具有最高优先级，影响模型的整体行为",
                    'user_prefix': "添加到用户消息开头，用于设置对话的上下文",
                    'user_suffix': "添加到用户消息结尾，用于补充额外的指令"
                }

                current_desc = position_descriptions.get(position, "")
                st.info(current_desc)

            st.markdown("**提示词内容**")
            content = st.text_area(
                "提示词内容",
                value=inject_config.get('content', ''),
                height=120,
                placeholder="输入自定义提示词...",
                help="输入要注入的提示词内容，支持多行文本"
            )

            # 字符统计
            char_count = len(content)
            if char_count > 0:
                st.caption(f"当前字符数: {char_count}")

            if st.form_submit_button("保存配置", type="primary", use_container_width=True):
                update_data = {
                    "enabled": inject_enabled,
                    "content": content,
                    "position": position
                }

                result = call_api('/admin/config/inject-prompt', 'POST', data=update_data)
                if result and result.get('success'):
                    st.success("配置已保存")
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()

    with tab3:
        st.markdown("#### 流式模式配置")
        st.markdown("控制API响应的流式输出行为")

        stream_mode_config = stats_data.get('stream_mode_config', {})
        current_mode = stream_mode_config.get('mode', 'auto')

        # 状态概览
        mode_names = {
            'auto': '自动模式',
            'stream': '强制流式',
            'non_stream': '强制非流式'
        }

        st.markdown(f'''
        <div style="background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(37, 99, 235, 0.1) 100%); 
                    border: 1px solid rgba(59, 130, 246, 0.2); border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h5 style="margin: 0; color: #374151; font-size: 1.1rem;">当前模式</h5>
                    <p style="margin: 0.5rem 0 0 0; color: #6b7280; font-size: 0.9rem;">
                        影响所有API响应的输出方式
                    </p>
                </div>
                <div style="background: #3b82f6; color: white; padding: 0.5rem 1rem; border-radius: 8px; font-weight: 500;">
                    {mode_names.get(current_mode, '未知')}
                </div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

        with st.form("stream_mode_form"):
            col1, col2 = st.columns([1, 1])

            with col1:
                st.markdown("**模式选择**")
                mode_options = {
                    'auto': '自动模式',
                    'stream': '强制流式',
                    'non_stream': '强制非流式'
                }

                selected_mode = st.selectbox(
                    "流式输出模式",
                    options=list(mode_options.keys()),
                    format_func=lambda x: mode_options[x],
                    index=list(mode_options.keys()).index(current_mode),
                    help="选择API响应的流式输出策略"
                )

            with col2:
                st.markdown("**模式说明**")
                mode_descriptions = {
                    'auto': "根据用户请求参数决定，提供最佳的兼容性",
                    'stream': "所有响应都使用流式输出，适合实时交互场景",
                    'non_stream': "所有响应都等待完整生成，适合批处理场景"
                }

                st.info(mode_descriptions[selected_mode])

            # 性能影响说明
            st.markdown("**性能影响**")
            if selected_mode == 'stream':
                st.success("流式模式可以提供更快的首字响应时间，提升用户体验")
            elif selected_mode == 'non_stream':
                st.warning("非流式模式会增加响应延迟，但能确保完整的响应内容")
            else:
                st.info("自动模式提供最佳的兼容性，推荐在大多数情况下使用")

            if st.form_submit_button("保存配置", type="primary", use_container_width=True):
                update_data = {
                    "mode": selected_mode
                }

                result = call_api('/admin/config/stream-mode', 'POST', data=update_data)
                if result and result.get('success'):
                    st.success("配置已保存")
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("保存失败")

    with tab4:
        st.markdown("#### 负载均衡策略")
        st.markdown("选择API密钥的负载均衡算法")

        # 获取当前策略
        all_configs = call_api('/admin/config')
        current_strategy = 'adaptive'

        if all_configs and all_configs.get('success'):
            system_configs = all_configs.get('system_configs', [])
            for config in system_configs:
                if config['key'] == 'load_balance_strategy':
                    current_strategy = config['value']
                    break

        # 状态概览
        strategy_names = {
            'adaptive': '自适应策略',
            'least_used': '最少使用策略',
            'round_robin': '轮询策略'
        }

        st.markdown(f'''
        <div style="background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(124, 58, 237, 0.1) 100%); 
                    border: 1px solid rgba(139, 92, 246, 0.2); border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h5 style="margin: 0; color: #374151; font-size: 1.1rem;">当前策略</h5>
                    <p style="margin: 0.5rem 0 0 0; color: #6b7280; font-size: 0.9rem;">
                        影响API密钥的选择和分发机制
                    </p>
                </div>
                <div style="background: #8b5cf6; color: white; padding: 0.5rem 1rem; border-radius: 8px; font-weight: 500;">
                    {strategy_names.get(current_strategy, '未知')}
                </div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

        with st.form("load_balance_form"):
            col1, col2 = st.columns([1, 1])

            with col1:
                st.markdown("**策略选择**")
                strategy_options = {
                    'adaptive': '自适应策略',
                    'least_used': '最少使用策略',
                    'round_robin': '轮询策略'
                }

                strategy = st.selectbox(
                    "负载均衡策略",
                    options=list(strategy_options.keys()),
                    format_func=lambda x: strategy_options[x],
                    index=list(strategy_options.keys()).index(current_strategy),
                    help="选择API密钥的负载均衡算法"
                )

            with col2:
                st.markdown("**策略特性**")
                strategy_features = {
                    'adaptive': "智能考虑响应时间、成功率和负载情况",
                    'least_used': "确保所有密钥的使用频率均匀分布",
                    'round_robin': "简单轮询，适合性能相近的密钥"
                }

                st.info(strategy_features[strategy])

            # 详细说明
            st.markdown("**策略说明**")
            strategy_descriptions = {
                'adaptive': "根据密钥的响应时间、成功率和当前负载智能选择最优密钥。推荐在密钥性能差异较大时使用。",
                'least_used': "优先选择使用次数最少的密钥，确保所有密钥的使用均匀分布。适合需要均衡使用所有密钥的场景。",
                'round_robin': "按顺序轮流使用密钥，算法简单高效。适合所有密钥性能相近的环境。"
            }

            st.markdown(f"**{strategy_options[strategy]}**: {strategy_descriptions[strategy]}")

            if st.form_submit_button("保存策略", type="primary", use_container_width=True):
                result = call_api('/admin/config', 'POST', {
                    'load_balance_strategy': strategy
                })
                if result and result.get('success'):
                    st.success(f"负载均衡策略已更新为：{strategy_options[strategy]}")
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()

    with tab5:  # 故障转移配置标签页
        st.markdown("#### 故障转移配置")
        st.markdown("配置API密钥的故障转移策略")

        # 获取当前配置
        failover_config_data = get_cached_failover_config()

        if not failover_config_data or not failover_config_data.get('success'):
            st.error("无法获取故障转移配置")
        else:
            current_config = failover_config_data.get('config', {})
            stats_info = failover_config_data.get('stats', {})

            # 状态概览
            fast_enabled = current_config.get('fast_failover_enabled', True)


            st.markdown(f'''
            <div style="background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(220, 38, 38, 0.1) 100%); 
                        border: 1px solid rgba(239, 68, 68, 0.2); border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h5 style="margin: 0; color: #374151; font-size: 1.1rem;">故障转移状态</h5>
                        <p style="margin: 0.5rem 0 0 0; color: #6b7280; font-size: 0.9rem;">
                            模式: {'快速转移' if fast_enabled else '传统重试'}
                        </p>
                    </div>
                    <div style="background: {'#10b981' if fast_enabled else '#f59e0b'}; color: white; padding: 0.5rem 1rem; border-radius: 8px; font-weight: 500;">
                        {'快速模式' if fast_enabled else '传统模式'}
                    </div>
                </div>
            </div>
            ''', unsafe_allow_html=True)

            # 关键指标
            col1, col2, col3 = st.columns(3)

            with col1:
                available_keys = stats_info.get('available_keys', 0)
                st.metric(
                    "可用密钥",
                    f"{available_keys} 个",
                    help="当前可用的API密钥数量"
                )

            with col2:
                healthy_keys = stats_info.get('healthy_keys', 0)
                st.metric(
                    "健康密钥",
                    f"{healthy_keys} 个",
                    delta=f"{healthy_keys - (available_keys - healthy_keys)} 个正常" if available_keys > 0 else None,
                    help="当前健康状态的密钥数量"
                )



            # 配置表单
            st.markdown("##### 转移策略配置")

            with st.form("failover_config_form"):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**核心配置**")

                    # 快速故障转移开关
                    fast_failover_enabled = st.checkbox(
                        "启用快速故障转移",
                        value=current_config.get('fast_failover_enabled', True),
                        help="失败时立即切换到下一个密钥，而不是重试当前密钥"
                    )



                with col2:
                    st.markdown("**高级配置**")

                    # 后台健康检测
                    background_health_check = st.checkbox(
                        "启用后台健康检测",
                        value=current_config.get('background_health_check', True),
                        help="密钥失败后在后台进行健康状态检测"
                    )

                    # 健康检测延迟
                    health_check_delay = st.slider(
                        "健康检测延迟 (秒)",
                        min_value=1,
                        max_value=60,
                        value=current_config.get('health_check_delay', 5),
                        help="密钥失败后延迟多长时间开始健康检测"
                    )

                # 配置预览
                st.markdown("**配置预览**")
                if fast_failover_enabled:
                    st.success("快速模式：失败时立即切换密钥，最大化响应速度")
                else:
                    st.info("传统模式：使用重试机制，适合网络不稳定的环境")

                # 提交按钮
                col1, col2 = st.columns(2)
                with col1:
                    save_config = st.form_submit_button(
                        "保存配置",
                        type="primary",
                        use_container_width=True
                    )

                with col2:
                    refresh_stats = st.form_submit_button(
                        "刷新统计",
                        use_container_width=True
                    )

                # 处理表单提交
                if save_config:
                    config_data = {
                        'fast_failover_enabled': fast_failover_enabled,
                        'background_health_check': background_health_check,
                        'health_check_delay': health_check_delay
                    }

                    result = update_failover_config(config_data)
                    if result and result.get('success'):
                        st.success("故障转移配置已保存")
                        st.info("新配置将在下次请求时生效")
                        st.cache_data.clear()
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("配置保存失败，请重试")

                if refresh_stats:
                    st.cache_data.clear()
                    st.rerun()

    with tab6:  # 自动清理标签页
        st.markdown("#### 自动清理配置")
        st.markdown("智能识别并自动移除连续异常的API密钥")

        # 获取当前配置和状态
        cleanup_status = get_cached_cleanup_status()

        if not cleanup_status or not cleanup_status.get('success'):
            st.error("无法获取自动清理状态，请检查后端服务连接")
        else:
            is_enabled = cleanup_status.get('auto_cleanup_enabled', False)
            days_threshold = cleanup_status.get('days_threshold', 3)
            at_risk_keys = cleanup_status.get('at_risk_keys', [])

            # 状态概览
            st.markdown(f'''
            <div style="background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(217, 119, 6, 0.1) 100%); 
                        border: 1px solid rgba(245, 158, 11, 0.2); border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h5 style="margin: 0; color: #374151; font-size: 1.1rem;">清理状态</h5>
                        <p style="margin: 0.5rem 0 0 0; color: #6b7280; font-size: 0.9rem;">
                            阈值: {days_threshold} 天 | 
                            风险密钥: {len(at_risk_keys)} 个 | 
                            执行时间: 每日 02:00 UTC
                        </p>
                    </div>
                    <div style="background: {'#10b981' if is_enabled else '#6b7280'}; color: white; padding: 0.5rem 1rem; border-radius: 8px; font-weight: 500;">
                        {'已启用' if is_enabled else '已禁用'}
                    </div>
                </div>
            </div>
            ''', unsafe_allow_html=True)

            # 关键指标
            col1, col2, col3 = st.columns(3)

            with col1:
                critical_keys = [k for k in at_risk_keys if k.get('consecutive_unhealthy_days', 0) >= days_threshold]
                st.metric(
                    "待清理密钥",
                    f"{len(critical_keys)} 个",
                    delta="下次清理" if len(critical_keys) > 0 else "无需清理",
                    delta_color="inverse" if len(critical_keys) > 0 else "normal"
                )

            with col2:
                warning_keys = [k for k in at_risk_keys if k.get('consecutive_unhealthy_days', 0) < days_threshold]
                st.metric(
                    "风险密钥",
                    f"{len(warning_keys)} 个",
                    delta="需要关注" if len(warning_keys) > 0 else "状态良好",
                    delta_color="inverse" if len(warning_keys) > 0 else "normal"
                )

            with col3:
                min_checks = cleanup_status.get('min_checks_per_day', 5)
                st.metric(
                    "最少检测次数",
                    f"{min_checks} 次/天",
                    help="密钥每日需要达到的最少检测次数"
                )

            # 风险预警区域
            if at_risk_keys:
                st.markdown("##### 风险密钥预警")

                if len(critical_keys) > 0:
                    st.error(f"🔥 {len(critical_keys)} 个密钥将在下次清理时被移除")

                if len(warning_keys) > 0:
                    st.warning(f"⚠️ {len(warning_keys)} 个密钥处于风险状态")

                # 风险Keys详细列表
                with st.expander("查看风险密钥详情", expanded=len(critical_keys) > 0):
                    # 表头
                    st.markdown('''
                    <div style="display: grid; grid-template-columns: 0.5fr 2.5fr 1fr 1fr 1.5fr; gap: 1rem; 
                                padding: 0.75rem 1rem; background: rgba(99, 102, 241, 0.1); border-radius: 8px; 
                                font-weight: 600; color: #374151; margin-bottom: 0.5rem;">
                        <div>ID</div>
                        <div>API Key</div>
                        <div>异常天数</div>
                        <div>风险等级</div>
                        <div>预计清理时间</div>
                    </div>
                    ''', unsafe_allow_html=True)

                    # 数据行
                    for key in at_risk_keys:
                        key_id = key.get('id', 'N/A')
                        key_preview = key.get('key', 'Unknown')
                        consecutive_days = key.get('consecutive_unhealthy_days', 0)
                        days_until_removal = key.get('days_until_removal', 0)

                        # 风险等级判断
                        if consecutive_days >= days_threshold:
                            risk_level = "🔥 极高"
                            risk_color = "#ef4444"
                            time_text = "下次清理"
                            time_color = "#ef4444"
                        elif consecutive_days >= days_threshold - 1:
                            risk_level = "⚠️ 高"
                            risk_color = "#f59e0b"
                            time_text = f"{days_until_removal}天后"
                            time_color = "#f59e0b"
                        else:
                            risk_level = "🟡 中"
                            risk_color = "#f59e0b"
                            time_text = f"{days_until_removal}天后"
                            time_color = "#6b7280"

                        st.markdown(f'''
                        <div style="display: grid; grid-template-columns: 0.5fr 2.5fr 1fr 1fr 1.5fr; gap: 1rem; 
                                    padding: 0.75rem 1rem; background: rgba(255, 255, 255, 0.4); 
                                    border: 1px solid rgba(255, 255, 255, 0.3); border-radius: 8px; 
                                    margin-bottom: 0.5rem; align-items: center;">
                            <div style="font-weight: 500;">#{key_id}</div>
                            <div style="font-family: monospace; background: rgba(255, 255, 255, 0.3); 
                                        padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.875rem;">{key_preview}</div>
                            <div style="text-align: center; font-weight: 500; color: {risk_color};">{consecutive_days}天</div>
                            <div style="color: {risk_color}; font-weight: 500;">{risk_level}</div>
                            <div style="color: {time_color}; font-weight: 500;">{time_text}</div>
                        </div>
                        ''', unsafe_allow_html=True)

            else:
                st.success("✅ 所有密钥状态良好，无需清理")

            # 配置管理区域
            st.markdown("##### 清理配置")

            # 配置表单
            with st.form("auto_cleanup_config_form"):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**基础设置**")

                    cleanup_enabled = st.checkbox(
                        "启用自动清理",
                        value=cleanup_status.get('auto_cleanup_enabled', False),
                        help="启用后将在每日凌晨2点自动检查并移除连续异常的密钥"
                    )

                    days_threshold = st.slider(
                        "连续异常天数阈值",
                        min_value=1,
                        max_value=10,
                        value=cleanup_status.get('days_threshold', 3),
                        help="连续异常超过此天数的密钥将被自动移除"
                    )

                    min_checks_per_day = st.slider(
                        "每日最少检测次数",
                        min_value=1,
                        max_value=50,
                        value=cleanup_status.get('min_checks_per_day', 5),
                        help="只有检测次数达到此值的密钥才会被纳入清理考虑"
                    )

                with col2:
                    st.markdown("**清理预览**")

                    # 预计影响分析
                    if cleanup_enabled:
                        estimated_removals = len(
                            [k for k in at_risk_keys if k.get('consecutive_unhealthy_days', 0) >= days_threshold])

                        if estimated_removals > 0:
                            st.error(f"当前配置将清理 {estimated_removals} 个密钥")
                        else:
                            st.success("当前配置下无密钥需要清理")

                        st.info("执行时间：每天凌晨 02:00 UTC")
                    else:
                        st.info("自动清理已禁用")

                    # 安全保障
                    st.markdown("**安全保障**")
                    st.caption("• 始终保留至少1个健康密钥")
                    st.caption("• 检测次数不足的密钥不会被误删")
                    st.caption("• 被清理的密钥可手动恢复")

                # 操作按钮
                col1, col2 = st.columns(2)

                with col1:
                    save_config = st.form_submit_button(
                        "保存配置",
                        type="primary",
                        use_container_width=True
                    )

                with col2:
                    manual_cleanup = st.form_submit_button(
                        "立即执行清理",
                        use_container_width=True
                    )

                # 处理表单提交
                if save_config:
                    config_data = {
                        'enabled': cleanup_enabled,
                        'days_threshold': days_threshold,
                        'min_checks_per_day': min_checks_per_day
                    }

                    result = update_cleanup_config(config_data)
                    if result and result.get('success'):
                        st.success("配置已保存")
                        st.info("新配置将在下次定时清理时生效")
                        st.cache_data.clear()
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("配置保存失败，请重试")

                if manual_cleanup:
                    if at_risk_keys:
                        critical_keys = [k for k in at_risk_keys if
                                         k.get('consecutive_unhealthy_days', 0) >= days_threshold]

                        if critical_keys:
                            st.warning("即将清理以下密钥：")
                            for key in critical_keys:
                                st.write(f"• Key #{key.get('id')}: {key.get('key')}")

                            with st.spinner("执行清理中..."):
                                result = manual_cleanup()
                                if result and result.get('success'):
                                    st.success("手动清理已完成")
                                    st.cache_data.clear()
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("清理执行失败")
                        else:
                            st.info("没有达到清理条件的密钥")
                    else:
                        st.info("当前无需清理的密钥")

            # 详细规则说明
            with st.expander("详细规则说明"):
                st.markdown("""
                ### 清理触发条件

                密钥被自动清理需要**同时满足**以下条件：
                - 连续异常天数 ≥ 设定阈值
                - 每日检测次数 ≥ 最少检测次数
                - 单日成功率 < 10%
                - 自动清理功能已启用

                ### 安全保护机制

                - **保留策略**: 始终保留至少1个健康密钥
                - **检测保护**: 检测次数不足的密钥不会被清理
                - **软删除**: 被清理的密钥只是禁用，可手动恢复
                - **历史保存**: 保留所有检测历史用于问题排查

                ### 建议配置

                - **保守**: 阈值 5-7 天，适合稳定环境
                - **标准**: 阈值 3-5 天，适合大多数场景
                - **激进**: 阈值 1-3 天，适合对质量要求极高的场景
                """)

    with tab7:
        st.markdown("#### 系统信息")
        st.markdown("查看系统运行状态和资源使用情况")

        # 系统概览
        python_version = status_data.get('python_version', 'Unknown').split()[0]
        version = status_data.get('version', '1.3.2')
        uptime_hours = status_data.get('uptime_seconds', 0) // 3600

        st.markdown(f'''
        <div style="background: linear-gradient(135deg, rgba(107, 114, 128, 0.1) 0%, rgba(75, 85, 99, 0.1) 100%); 
                    border: 1px solid rgba(107, 114, 128, 0.2); border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h5 style="margin: 0; color: #374151; font-size: 1.1rem;">系统状态</h5>
                    <p style="margin: 0.5rem 0 0 0; color: #6b7280; font-size: 0.9rem;">
                        版本: {version} | Python: {python_version} | 运行时间: {uptime_hours} 小时
                    </p>
                </div>
                <div style="background: #10b981; color: white; padding: 0.5rem 1rem; border-radius: 8px; font-weight: 500;">
                    运行中
                </div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("##### 服务信息")

            # 服务信息表格
            service_info = {
                "Python版本": python_version,
                "系统版本": version,
                "运行时间": f"{uptime_hours} 小时",
                "支持模型": len(status_data.get('models', [])),
                "API端点": f"{API_BASE_URL}"
            }

            for key, value in service_info.items():
                st.markdown(f"**{key}**: {value}")

        with col2:
            st.markdown("##### 资源使用")

            # 资源使用指标
            memory_mb = status_data.get('memory_usage_mb', 0)
            cpu_percent = status_data.get('cpu_percent', 0)

            # 内存使用
            st.metric(
                "内存使用",
                f"{memory_mb:.1f} MB",
                delta=f"{memory_mb / 1024:.1f} GB" if memory_mb > 1024 else None
            )

            # CPU使用
            st.metric(
                "CPU使用率",
                f"{cpu_percent:.1f}%",
                delta="正常" if cpu_percent < 80 else "偏高",
                delta_color="normal" if cpu_percent < 80 else "inverse"
            )

        # 支持的模型列表
        st.markdown("##### 支持的模型")
        models = status_data.get('models', [])
        if models:
            # 创建模型网格布局
            cols = st.columns(3)
            for i, model in enumerate(models):
                with cols[i % 3]:
                    st.markdown(f'''
                    <div style="background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.2); 
                                border-radius: 8px; padding: 0.75rem; margin-bottom: 0.5rem; text-align: center;">
                        <div style="font-weight: 500; color: #1e40af;">{model}</div>
                    </div>
                    ''', unsafe_allow_html=True)
        else:
            st.info("暂无支持的模型信息")

        # 健康检查链接
        st.markdown("##### 快速链接")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f'''
            <a href="{API_BASE_URL}/health" target="_blank" style="display: block; text-decoration: none;">
                <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2); 
                            border-radius: 8px; padding: 1rem; text-align: center; color: #065f46; font-weight: 500;">
                    健康检查
                </div>
            </a>
            ''', unsafe_allow_html=True)

        with col2:
            st.markdown(f'''
            <a href="{API_BASE_URL}/docs" target="_blank" style="display: block; text-decoration: none;">
                <div style="background: rgba(99, 102, 241, 0.1); border: 1px solid rgba(99, 102, 241, 0.2); 
                            border-radius: 8px; padding: 1rem; text-align: center; color: #4338ca; font-weight: 500;">
                    API文档
                </div>
            </a>
            ''', unsafe_allow_html=True)

        with col3:
            st.markdown(f'''
            <a href="{API_BASE_URL}/status" target="_blank" style="display: block; text-decoration: none;">
                <div style="background: rgba(139, 92, 246, 0.1); border: 1px solid rgba(139, 92, 246, 0.2); 
                            border-radius: 8px; padding: 1rem; text-align: center; color: #6d28d9; font-weight: 500;">
                    系统状态
                </div>
            </a>
            ''', unsafe_allow_html=True)

    with tab8:
        st.markdown("#### 防检测配置")
        st.markdown("管理自动化检测防护功能")

        # 获取防检测配置
        anti_detection_data = call_api('/admin/config/anti-detection', 'GET')
        
        if anti_detection_data:
            anti_detection_config = anti_detection_data.get('config', {})
            current_enabled = anti_detection_config.get('anti_detection_enabled', True)
            current_disable_for_tools = anti_detection_config.get('disable_for_tools', True) 
            current_token_threshold = anti_detection_config.get('token_threshold', 5000)
            stats = anti_detection_data.get('statistics', {})
            
            # 状态概览卡片
            status_text = "已启用" if current_enabled else "已禁用"
            status_color = "#10b981" if current_enabled else "#ef4444"
            
            st.markdown(f'''
            <div style="background: linear-gradient(135deg, rgba(34, 197, 94, 0.1) 0%, rgba(59, 130, 246, 0.1) 100%); 
                        border: 1px solid rgba(34, 197, 94, 0.2); border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h5 style="margin: 0; color: #374151; font-size: 1.1rem;">防检测状态</h5>
                        <p style="margin: 0.5rem 0 0 0; color: #6b7280; font-size: 0.9rem;">
                            工具调用时: {"禁用" if current_disable_for_tools else "启用"} | 
                            生效阈值: {current_token_threshold} tokens
                        </p>
                    </div>
                    <div style="background: {status_color}; color: white; padding: 0.5rem 1rem; border-radius: 8px; font-weight: 500;">
                        {status_text}
                    </div>
                </div>
            </div>
            ''', unsafe_allow_html=True)

            with st.form("anti_detection_form"):
                st.markdown("**基础配置**")
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    enabled = st.checkbox(
                        "启用防检测功能",
                        value=current_enabled,
                        help="开启后将在合适的情况下自动应用防检测处理"
                    )
                    
                with col2:
                    disable_for_tools = st.checkbox(
                        "工具调用时禁用防检测",
                        value=current_disable_for_tools,
                        help="在进行工具调用时自动禁用防检测，避免影响工具响应"
                    )

                st.markdown("**高级配置**")
                token_threshold = st.number_input(
                    "Token阈值",
                    min_value=1000,
                    max_value=50000,
                    value=current_token_threshold,
                    step=500,
                    help="只有当消息token数超过此阈值时才应用防检测处理"
                )

                # 统计信息
                if stats:
                    st.markdown("**使用统计**")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric(
                            "处理次数",
                            stats.get('processed_count', 0),
                            help="累计应用防检测处理的次数"
                        )
                    
                    with col2:
                        st.metric(
                            "符号注入次数", 
                            stats.get('symbol_injections', 0),
                            help="累计注入的防检测符号数量"
                        )
                    
                    with col3:
                        avg_time = stats.get('average_processing_time_ms', 0)
                        st.metric(
                            "平均处理时间",
                            f"{avg_time:.1f}ms",
                            help="平均防检测处理耗时"
                        )

                col1, col2 = st.columns([1, 1])
                
                with col1:
                    if st.form_submit_button("保存配置", type="primary", use_container_width=True):
                        update_data = {
                            'enabled': enabled,
                            'disable_for_tools': disable_for_tools,
                            'token_threshold': token_threshold
                        }
                        
                        result = call_api('/admin/config/anti-detection', 'POST', data=update_data)
                        if result and result.get('success'):
                            st.success("防检测配置已更新")
                            clear_cache()
                            st.rerun()
                        else:
                            st.error("更新防检测配置失败")
                
                with col2:
                    if st.form_submit_button("测试防检测", use_container_width=True):
                        test_result = call_api('/admin/test/anti-detection', 'POST')
                        if test_result and test_result.get('success'):
                            st.success("防检测功能测试成功")
                            with st.expander("测试结果详情"):
                                st.json(test_result)
                        else:
                            st.error("防检测功能测试失败")

        else:
            st.error("无法获取防检测配置数据")

# --- 页脚 ---
st.markdown(
    f"""
    <div style='text-align: center; color: rgba(255, 255, 255, 0.7); font-size: 0.8125rem; margin-top: 4rem; padding: 2rem 0; border-top: 1px solid rgba(255, 255, 255, 0.15); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); background: rgba(255, 255, 255, 0.05); border-radius: 16px 16px 0 0; text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);'>
        <a href='{API_BASE_URL}/health' target='_blank' style='color: rgba(255, 255, 255, 0.8); text-decoration: none; transition: all 0.3s ease; padding: 0.25rem 0.5rem; border-radius: 6px; backdrop-filter: blur(4px); -webkit-backdrop-filter: blur(4px);' onmouseover='this.style.color="white"; this.style.background="rgba(255, 255, 255, 0.1)"; this.style.textShadow="0 0 8px rgba(255, 255, 255, 0.5)";' onmouseout='this.style.color="rgba(255, 255, 255, 0.8)"; this.style.background="transparent"; this.style.textShadow="none";'>健康检查</a> · 
        <span style='color: rgba(255, 255, 255, 0.6);'>{API_BASE_URL}</span> ·
        <span style='color: rgba(255, 255, 255, 0.6);'>v1.3.2</span>
    </div>
    """,
    unsafe_allow_html=True
)
