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
try:
    creds_dict = dict(st.secrets["gcp_service_account"])
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
except:
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

# --- АВТОМАТИЧЕСКОЕ ПРИВЕДЕНИЕ ДАТ К DATETIME ---
date_columns = []
for col in df.columns:
    if 'дата' in col.lower() or 'date' in col.lower() or 'день' in col.lower():
        try:
            df[col] = pd.to_datetime(df[col], errors='coerce')
            date_columns.append(col)
        except:
            pass

# --- UI ---
st.set_page_config(
    page_title="Дашборд поставок", 
    layout="wide",
    page_icon="📦",
    initial_sidebar_state="expanded"
)

# --- СОВРЕМЕННЫЙ CSS ДИЗАЙН ---
st.markdown("""
    <style>
    /* Основной фон - темный градиент */
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    }
    
    /* Карточки метрик - стеклянный эффект */
    .metric-card {
        background: rgba(255,255,255,0.08);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 25px;
        border: 1px solid rgba(255,255,255,0.2);
        box-shadow: 0 8px 32px 0 rgba(31,38,135,0.37);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        background: rgba(255,255,255,0.12);
        border-color: rgba(255,255,255,0.4);
    }
    
    /* Заголовок с неоновым эффектом */
    .main-title {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5em;
        font-weight: 800;
        text-align: center;
        margin-bottom: 30px;
        text-shadow: 0 0 30px rgba(250,112,154,0.3);
        letter-spacing: -0.02em;
    }
    
    /* Кастомные стили для вкладок */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(255,255,255,0.05);
        border-radius: 12px;
        padding: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 24px;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* Стили для селекторов */
    .stSelectbox > div > div {
        background: rgba(255,255,255,0.1);
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 12px;
        color: white;
    }
    
    /* Стили для кнопок */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 10px 24px;
        font-weight: 600;
        transition: all 0.3s;
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102,126,234,0.4);
    }
    
    /* Чекбокс */
    .stCheckbox > div {
        background: rgba(255,255,255,0.1);
        border-radius: 10px;
        padding: 8px;
    }
    
    /* Таблица */
    .stDataFrame {
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    /* Сайдбар */
    .css-1d391kg {
        background: rgba(0,0,0,0.6);
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255,255,255,0.1);
    }
    
    /* Текст в сайдбаре */
    .sidebar-content {
        color: white;
    }
    
    /* Метрики */
    [data-testid="stMetricValue"] {
        font-size: 2.5rem;
        font-weight: 800;
    }
    </style>
""", unsafe_allow_html=True)

# Заголовок
st.markdown('<p class="main-title">📦 NWL Logistics Dashboard</p>', unsafe_allow_html=True)

# --- Боковая панель с фильтрами ---
with st.sidebar:
    st.markdown("### 🎮 Управление дашбордом")
    st.markdown("---")
    
    # Фильтр по юр лицу
    if "Юр лицо" in df.columns:
        companies = ["Все компании"] + sorted(list(df["Юр лицо"].unique()))
        selected_company = st.selectbox("🏢 Выберите юр лицо", companies)
        
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
    
    # Статистика
    st.markdown("### 📊 Статистика")
    st.metric("📋 Записей в фильтре", f"{len(filtered_df):,}")
    st.metric("🏢 Юр лиц в фильтре", filtered_df["Юр лицо"].nunique() if "Юр лицо" in filtered_df.columns else 0)
    
    if date_columns:
        st.markdown("---")
        st.markdown("### 📅 Доступные даты")
        for col in date_columns[:3]:
            st.caption(f"✅ {col}")
    
    st.markdown("---")
    st.markdown("🔄 **Последнее обновление**")
    st.caption(datetime.now().strftime("%d.%m.%Y %H:%M:%S"))

# --- KPI в карточках (без Всего SKU)---
col1, col2, col3 = st.columns(3)

# Всего заказов
with col1:
    st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 0.9em; opacity: 0.8; margin-bottom: 10px;">📋 ВСЕГО ЗАКАЗОВ</div>
            <div style="font-size: 2.5em; font-weight: bold; background: linear-gradient(135deg, #fff 0%, #a8c0ff 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{len(filtered_df):,}</div>
        </div>
    """, unsafe_allow_html=True)

# Просрочки
with col2:
    if "Разница day" in filtered_df.columns:
        late_count = len(filtered_df[filtered_df["Разница day"] < 0])
        late_gradient = "#ff6b6b" if late_count > 0 else "#51cf66"
        st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 0.9em; opacity: 0.8; margin-bottom: 10px;">⚠️ ПРОСРОЧКИ</div>
                <div style="font-size: 2.5em; font-weight: bold; color: {late_gradient};">{late_count}</div>
            </div>
        """, unsafe_allow_html=True)

# Среднее отклонение
with col3:
    if "Разница day" in filtered_df.columns:
        avg_diff = filtered_df["Разница day"].mean()
        diff_color = "#ff6b6b" if avg_diff < 0 else "#51cf66"
        st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 0.9em; opacity: 0.8; margin-bottom: 10px;">📈 СР. ОТКЛОНЕНИЕ</div>
                <div style="font-size: 2.5em; font-weight: bold; color: {diff_color};">{avg_diff:.1f} дн</div>
            </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# --- Вкладки ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Дашборд", "⚠️ Просрочки", "📈 Аналитика", "🎨 Визуализации"])

with tab1:
    st.subheader("📋 Детальная таблица поставок")
    st.dataframe(filtered_df, use_container_width=True, height=450, 
                 column_config={
                     "Разница day": st.column_config.NumberColumn("Отклонение", format="%.0f дн")
                 })

with tab2:
    if "Разница day" in filtered_df.columns:
        st.subheader("⚠️ Просроченные поставки")
        late_df = filtered_df[filtered_df["Разница day"] < 0]
        
        if len(late_df) > 0:
            st.error(f"🔔 Обнаружено {len(late_df)} просроченных поставок")
            st.dataframe(late_df, use_container_width=True, height=350)
            
            # Гистограмма просрочек
            fig = px.histogram(late_df, x="Разница day", 
                              title="Распределение просрочек по дням",
                              color_discrete_sequence=["#ff6b6b"],
                              labels={"Разница day": "Отклонение (дни)", "count": "Кол-во поставок"},
                              template="plotly_dark")
            fig.update_layout(showlegend=False, height=450, plot_bgcolor='rgba(0,0,0,0)')
            fig.update_traces(marker_line_width=0)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.success("🎉 Отлично! Нет просроченных поставок!")

with tab3:
    st.subheader("📊 Аналитика поставок")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if "Юр лицо" in filtered_df.columns and "Кол-во sku" in filtered_df.columns:
            sku_by_company = filtered_df.groupby("Юр лицо")["Кол-во sku"].sum().sort_values(ascending=True)
            
            fig = px.bar(sku_by_company, 
                        x=sku_by_company.values, 
                        y=sku_by_company.index,
                        orientation='h',
                        title="📦 SKU по компаниям",
                        color=sku_by_company.values,
                        color_continuous_scale="Viridis",
                        labels={"x": "Количество SKU", "y": ""},
                        template="plotly_dark")
            fig.update_layout(height=450, plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if "Разница day" in filtered_df.columns:
            status_df = pd.DataFrame({
                "Статус": ["✅ В срок", "⚠️ Просрочено"],
                "Количество": [
                    len(filtered_df[filtered_df["Разница day"] >= 0]),
                    len(filtered_df[filtered_df["Разница day"] < 0])
                ]
            })
            
            fig = px.pie(status_df, values="Количество", names="Статус",
                        title="Статус выполнения поставок",
                        color_discrete_sequence=["#51cf66", "#ff6b6b"],
                        hole=0.4,
                        template="plotly_dark")
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(height=450)
            st.plotly_chart(fig, use_container_width=True)
    
    # Тренд по датам (если есть даты)
    if date_columns:
        st.markdown("---")
        st.subheader("📅 Динамика поставок")
        date_col = st.selectbox("Выберите дату для анализа", date_columns)
        
        if date_col in filtered_df.columns:
            temp_df = filtered_df.dropna(subset=[date_col])
            if len(temp_df) > 0:
                temp_df['Год'] = temp_df[date_col].dt.year
                temp_df['Месяц'] = temp_df[date_col].dt.month
                monthly_stats = temp_df.groupby(['Год', 'Месяц']).size().reset_index(name='Количество')
                monthly_stats['Период'] = monthly_stats['Год'].astype(str) + '-' + monthly_stats['Месяц'].astype(str).str.zfill(2)
                
                fig = px.line(monthly_stats, x='Период', y='Количество',
                             title=f"Динамика поставок по {date_col}",
                             markers=True,
                             template="plotly_dark")
                fig.update_traces(line_color="#667eea", marker_color="#764ba2", marker_size=10)
                fig.update_layout(height=400, plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.subheader("🎨 Продвинутые визуализации")
    
    # Числовые колонки
    numeric_cols = filtered_df.select_dtypes(include=[np.number]).columns.tolist()
    
    if len(numeric_cols) > 1:
        col1, col2 = st.columns(2)
        
        with col1:
            x_axis = st.selectbox("📊 Ось X", numeric_cols, key="scatter_x")
            y_axis = st.selectbox("📈 Ось Y", numeric_cols, key="scatter_y")
            
            fig = px.scatter(filtered_df, x=x_axis, y=y_axis,
                            title=f"Корреляция: {x_axis} vs {y_axis}",
                            trendline="ols",
                            color_discrete_sequence=["#667eea"],
                            template="plotly_dark")
            fig.update_traces(marker=dict(size=10, opacity=0.7))
            fig.update_layout(height=450, plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            selected_col = st.selectbox("📦 Выберите метрику", numeric_cols)
            fig = px.box(filtered_df, y=selected_col,
                        title=f"Распределение {selected_col}",
                        color_discrete_sequence=["#764ba2"],
                        template="plotly_dark")
            fig.update_layout(height=450, plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
    
    # Тепловая карта корреляции
    if len(numeric_cols) > 2:
        st.markdown("---")
        st.subheader("🔥 Тепловая карта корреляций")
        corr_matrix = filtered_df[numeric_cols].corr()
        fig = px.imshow(corr_matrix, 
                       text_auto=True, 
                       aspect="auto",
                       color_continuous_scale="RdBu_r",
                       title="Матрица корреляций",
                       template="plotly_dark")
        fig.update_layout(height=500, plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

# --- Footer ---
st.markdown("---")
st.markdown("""
    <div style="text-align: center; padding: 20px; color: rgba(255,255,255,0.6);">
        <p>✨ Дашборд создан с Streamlit | Автоматическое обновление данных | Design by NWL</p>
    </div>
""", unsafe_allow_html=True)
