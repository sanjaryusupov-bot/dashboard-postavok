import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
import json

# --- настройки ---
SPREADSHEET_ID = "1SLBGBaxjXarnsYq96dY5b1hcUp4iC-Bu9c65G0kjvv8"
WORKSHEET_NAME = "Поставки на NWL"

# --- АВТОРИЗАЦИЯ ДЛЯ ОНЛАЙН ВЕРСИИ ---
# Берем credentials из secrets (для Streamlit Cloud)
try:
    # Пытаемся получить credentials из st.secrets (для онлайн версии)
    creds_dict = dict(st.secrets["gcp_service_account"])
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
except:
    # Если нет secrets (локальная версия), используем файл
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)

# --- подключение к таблице ---
sheet = client.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)

data = sheet.get_all_records()
df = pd.DataFrame(data)

# --- очистка данных ---
df = df.fillna(0)

# --- конвертация колонки Разница day в числовой формат ---
if "Разница day" in df.columns:
    df["Разница day"] = pd.to_numeric(df["Разница day"], errors="coerce").fillna(0)

# --- UI ---
st.set_page_config(
    page_title="Дашборд поставок", 
    layout="wide",
    page_icon="📦",
    initial_sidebar_state="expanded"
)

# Остальной код из предыдущего ответа (со всей стилизацией и графиками)
# ... (здесь вставьте остальной код из моего предыдущего ответа)
# Кастомный CSS для крутого дизайна
st.markdown("""
    <style>
    /* Градиентный фон */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Карточки метрик */
    .metric-card {
        background: rgba(255,255,255,0.95);
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 8px 32px 0 rgba(31,38,135,0.37);
        backdrop-filter: blur(4px);
        border: 1px solid rgba(255,255,255,0.18);
        transition: transform 0.3s;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
    }
    
    /* Заголовок */
    .main-title {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3em;
        font-weight: bold;
        text-align: center;
        margin-bottom: 30px;
    }
    
    /* Кастомный селектор */
    .stSelectbox > div > div {
        background: rgba(255,255,255,0.9);
        border-radius: 10px;
    }
    
    /* Таблица */
    .stDataFrame {
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Боковая панель */
    .css-1d391kg {
        background: rgba(255,255,255,0.95);
        backdrop-filter: blur(10px);
    }
    </style>
""", unsafe_allow_html=True)

# Заголовок
st.markdown('<p class="main-title">📦 Дашборд поставок NWL</p>', unsafe_allow_html=True)

# --- Боковая панель с фильтрами и информацией ---
with st.sidebar:
    st.markdown("### 🎛️ Управление")
    st.markdown("---")
    
    # Фильтр по юр лицу в сайдбаре
    if "Юр лицо" in df.columns:
        companies = ["Все компании"] + list(df["Юр лицо"].unique())
        selected_company = st.selectbox("🏢 Выбери юр лицо", companies)
        
        if selected_company != "Все компании":
            filtered_df = df[df["Юр лицо"] == selected_company]
        else:
            filtered_df = df
    else:
        filtered_df = df
    
    st.markdown("---")
    
    # Дополнительные фильтры
    if "Разница day" in df.columns:
        show_only_late = st.checkbox("⚠️ Показать только просрочки")
        if show_only_late:
            filtered_df = filtered_df[filtered_df["Разница day"] < 0]
    
    st.markdown("---")
    
    # Статистика по фильтру
    st.markdown("### 📊 Текущий фильтр")
    st.metric("Количество записей", len(filtered_df))
    
    if "Кол-во sku" in filtered_df.columns:
        total_sku = filtered_df["Кол-во sku"].sum() if filtered_df["Кол-во sku"].dtype in ['int64', 'float64'] else 0
        st.metric("Всего SKU", f"{int(total_sku):,}".replace(",", " "))
    
    st.markdown("---")
    st.markdown("🔄 **Последнее обновление:**")
    st.caption(datetime.now().strftime("%d.%m.%Y %H:%M:%S"))

# --- KPI в крутых карточках ---
col1, col2, col3, col4 = st.columns(4)

# Всего заказов
with col1:
    st.markdown(f"""
        <div class="metric-card">
            <h3 style="margin:0; color:#667eea;">📋 Всего заказов</h3>
            <p style="font-size: 2em; margin:10px 0; font-weight:bold;">{len(filtered_df):,}</p>
        </div>
    """, unsafe_allow_html=True)

# Всего SKU
with col2:
    if "Кол-во sku" in filtered_df.columns and filtered_df["Кол-во sku"].dtype in ['int64', 'float64']:
        total_sku = filtered_df["Кол-во sku"].sum()
        st.markdown(f"""
            <div class="metric-card">
                <h3 style="margin:0; color:#667eea;">📦 Всего SKU</h3>
                <p style="font-size: 2em; margin:10px 0; font-weight:bold;">{int(total_sku):,}</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div class="metric-card">
                <h3 style="margin:0; color:#667eea;">📦 Всего SKU</h3>
                <p style="font-size: 2em; margin:10px 0; font-weight:bold;">0</p>
            </div>
        """, unsafe_allow_html=True)

# Просрочки
with col3:
    if "Разница day" in filtered_df.columns:
        late_count = len(filtered_df[filtered_df["Разница day"] < 0])
        late_color = "#ff6b6b" if late_count > 0 else "#51cf66"
        st.markdown(f"""
            <div class="metric-card">
                <h3 style="margin:0; color:{late_color};">⚠️ Просрочки</h3>
                <p style="font-size: 2em; margin:10px 0; font-weight:bold;">{late_count}</p>
            </div>
        """, unsafe_allow_html=True)

# Среднее отклонение
with col4:
    if "Разница day" in filtered_df.columns:
        avg_diff = filtered_df["Разница day"].mean()
        diff_color = "#ff6b6b" if avg_diff < 0 else "#51cf66"
        st.markdown(f"""
            <div class="metric-card">
                <h3 style="margin:0; color:{diff_color};">📈 Ср. отклонение</h3>
                <p style="font-size: 2em; margin:10px 0; font-weight:bold;">{avg_diff:.1f} дн</p>
            </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# --- Вкладки для организации контента ---
tab1, tab2, tab3, tab4 = st.tabs(["📋 Данные", "⚠️ Просрочки", "📊 Аналитика", "🎨 Тренды"])

with tab1:
    st.subheader("📋 Детальная таблица поставок")
    st.dataframe(filtered_df, use_container_width=True, height=400)

with tab2:
    if "Разница day" in filtered_df.columns:
        st.subheader("⚠️ Просроченные поставки")
        late_df = filtered_df[filtered_df["Разница day"] < 0]
        
        if len(late_df) > 0:
            st.warning(f"Найдено {len(late_df)} просроченных поставок")
            st.dataframe(late_df, use_container_width=True, height=300)
            
            # Добавим цветовую индикацию отклонений
            if "Разница day" in late_df.columns:
                st.markdown("### Распределение просрочек")
                fig = px.histogram(late_df, x="Разница day", 
                                  title="Гистограмма просрочек",
                                  color_discrete_sequence=["#ff6b6b"],
                                  labels={"Разница day": "Отклонение (дни)"})
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.success("✅ Отлично! Нет просроченных поставок!")

with tab3:
    st.subheader("📊 Аналитика поставок")
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        if "Юр лицо" in filtered_df.columns and "Кол-во sku" in filtered_df.columns:
            sku_by_company = filtered_df.groupby("Юр лицо")["Кол-во sku"].sum().sort_values(ascending=True)
            
            fig = px.bar(sku_by_company, 
                        x=sku_by_company.values, 
                        y=sku_by_company.index,
                        orientation='h',
                        title="📊 SKU по компаниям",
                        color=sku_by_company.values,
                        color_continuous_scale="Viridis",
                        labels={"x": "Количество SKU", "y": "Юридическое лицо"})
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    with col_chart2:
        if "Разница day" in filtered_df.columns:
            # Отклонения по дням
            diff_counts = filtered_df["Разница day"].value_counts().sort_index().head(20)
            
            fig = px.line(x=diff_counts.index, y=diff_counts.values,
                         title="Отклонения по дням",
                         labels={"x": "Отклонение (дни)", "y": "Количество поставок"},
                         markers=True)
            fig.update_traces(line_color="#764ba2", marker_color="#667eea", marker_size=8)
            st.plotly_chart(fig, use_container_width=True)
    
    # Добавим круговую диаграмму статусов
    if "Разница day" in filtered_df.columns:
        status_df = pd.DataFrame({
            "Статус": ["В срок", "Просрочено"],
            "Количество": [
                len(filtered_df[filtered_df["Разница day"] >= 0]),
                len(filtered_df[filtered_df["Разница day"] < 0])
            ]
        })
        
        fig = px.pie(status_df, values="Количество", names="Статус",
                    title="Статус выполнения поставок",
                    color_discrete_sequence=["#51cf66", "#ff6b6b"],
                    hole=0.3)
        st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.subheader("🎨 Тренды и визуализации")
    
    # Добавим тепловую карту если есть числовые колонки
    numeric_cols = filtered_df.select_dtypes(include=[np.number]).columns.tolist()
    
    if len(numeric_cols) > 1:
        col1, col2 = st.columns(2)
        
        with col1:
            # Scatter plot
            x_axis = st.selectbox("Выбери ось X", numeric_cols, key="scatter_x")
            y_axis = st.selectbox("Выбери ось Y", numeric_cols, key="scatter_y")
            
            fig = px.scatter(filtered_df, x=x_axis, y=y_axis,
                            title=f"Корреляция: {x_axis} vs {y_axis}",
                            trendline="ols",
                            color_discrete_sequence=["#667eea"])
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Box plot
            selected_col = st.selectbox("Выбери колонку для Box plot", numeric_cols)
            fig = px.box(filtered_df, y=selected_col,
                        title=f"Распределение {selected_col}",
                        color_discrete_sequence=["#764ba2"])
            st.plotly_chart(fig, use_container_width=True)
    
    # Добавим календарь для просрочек если есть даты
    date_cols = filtered_df.select_dtypes(include=['datetime64', 'object']).columns.tolist()
    if date_cols:
        st.markdown("### 📅 Анализ по датам")
        st.info("ℹ️ Для работы с датами необходимо привести колонки к формату datetime")

# --- Footer ---
st.markdown("---")
st.markdown("""
    <div style="text-align: center; padding: 20px; color: #ffffff;">
        <p>🚀 Дашборд создан с использованием Streamlit | Данные обновляются автоматически</p>
    </div>
""", unsafe_allow_html=True)