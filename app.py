import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
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
    
    /* Карточки метрик */
    .metric-card {
        background: rgba(255,255,255,0.12);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 25px;
        border: 1px solid rgba(255,255,255,0.25);
        box-shadow: 0 8px 32px 0 rgba(31,38,135,0.37);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        background: rgba(255,255,255,0.18);
        border-color: rgba(255,255,255,0.4);
    }
    
    .metric-card div {
        color: white !important;
    }
    
    /* Заголовок */
    .main-title {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5em;
        font-weight: 800;
        text-align: center;
        margin-bottom: 30px;
        text-shadow: 0 0 30px rgba(250,112,154,0.3);
    }
    
    /* Стили для всех subheader (белый цвет) */
    .stSubheader, h2, h3 {
        color: white !important;
        font-weight: 700 !important;
    }
    
    /* Вкладки */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 24px;
        font-weight: 600;
        color: rgba(255,255,255,0.8);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* Селекторы */
    .stSelectbox > div > div {
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.25);
        border-radius: 12px;
        color: white !important;
    }
    
    .stSelectbox label {
        color: white !important;
    }
    
    /* Кнопки */
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
        background: rgba(255,255,255,0.08);
        border-radius: 10px;
        padding: 8px;
    }
    
    .stCheckbox label {
        color: white !important;
    }
    
    /* Таблица */
    .stDataFrame {
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    /* Сайдбар - ТЕМНЫЙ ФОН */
    .css-1d391kg {
        background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 100%) !important;
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(102,126,234,0.3);
    }
    
    /* Текст в сайдбаре */
    .css-1d391kg, .css-1d391kg p, .css-1d391kg label {
        color: black !important;
    }
    
    .css-1d391kg h1, .css-1d391kg h2, .css-1d391kg h3 {
        color: black !important;
    }
    
    /* Метрики */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 800;
        color: black !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: rgba(255,255,255,0.8) !important;
    }
    
    /* Информационные сообщения */
    .stAlert {
        background: rgba(0,0,0,0.6);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.2);
        color: black !important;
    }
    
    /* Стиль для кнопки деталей */
    .details-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: black;
        padding: 8px 16px;
        border-radius: 10px;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s;
        font-size: 0.85em;
        margin-top: 10px;
    }
    
    .details-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102,126,234,0.4);
    }
    </style>
""", unsafe_allow_html=True)

# Заголовок
st.markdown('<p class="main-title">📦 Magnit Cosmetik: NWL</p>', unsafe_allow_html=True)

# --- Поиск колонки с датой прибытия ---
delivery_date_col = None
for col in df.columns:
    if 'прибытие' in col.lower() or 'план' in col.lower():
        delivery_date_col = col
        break

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
    
    # Ожидается сегодня поставок
    st.markdown("### 📅 Ожидается сегодня")
    
    # Состояние для отображения деталей
    if 'show_expected_details' not in st.session_state:
        st.session_state.show_expected_details = False
    
    if delivery_date_col and delivery_date_col in df.columns:
        today = datetime.now().date()
        expected_today = df[pd.to_datetime(df[delivery_date_col], errors='coerce').dt.date == today]
        expected_count = len(expected_today)
        
        if expected_count > 0:
            st.markdown(f"""
                <div style="background: linear-gradient(135deg, rgba(102,126,234,0.25) 0%, rgba(118,75,162,0.25) 100%); 
                            border-radius: 15px; padding: 15px; text-align: center; 
                            border: 1px solid rgba(102,126,234,0.5);
                            margin-bottom: 10px;">
                    <div style="font-size: 2.5em;">🚚</div>
                    <div style="font-size: 2em; font-weight: bold; color: #667eea;">{expected_count}</div>
                    <div style="font-size: 0.9em; margin-top: 5px;">поставок ожидается</div>
                    <div style="font-size: 0.8em; opacity: 0.8;">сегодня, {today.strftime('%d.%m.%Y')}</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Кнопка для показа деталей
            if st.button(f"📋 Показать детали ({expected_count} поставок)", key="show_details_btn"):
                st.session_state.show_expected_details = not st.session_state.show_expected_details
            
            # Детальная таблица ожидаемых поставок
            if st.session_state.show_expected_details:
                st.markdown("---")
                st.markdown("### 📋 Детали ожидаемых поставок")
                
                # Выбираем важные колонки для отображения
                display_columns = []
                important_cols = ['Юр лицо', 'Поставщик', '№ заказа', 'Кол-во sku', delivery_date_col, 'Разница day']
                
                for col in important_cols:
                    if col in expected_today.columns:
                        display_columns.append(col)
                
                # Добавляем другие колонки если нет важных
                if len(display_columns) < 3:
                    display_columns = expected_today.columns.tolist()[:6]
                
                expected_display = expected_today[display_columns].copy()
                
                # Показываем таблицу
                st.dataframe(expected_display, use_container_width=True, height=300)
                
                # Дополнительная статистика
                st.markdown("---")
                col1, col2 = st.columns(2)
                with col1:
                    if "Кол-во sku" in expected_today.columns:
                        total_sku = expected_today["Кол-во sku"].sum() if expected_today["Кол-во sku"].dtype in ['int64', 'float64'] else 0
                        st.metric("📦 Всего SKU", f"{int(total_sku):,}")
                with col2:
                    if "Юр лицо" in expected_today.columns:
                        unique_companies = expected_today["Юр лицо"].nunique()
                        st.metric("🏢 Компаний", unique_companies)
        else:
            st.info("✅ На сегодня поставок не запланировано")
            st.session_state.show_expected_details = False
    else:
        st.info("ℹ️ Колонка с датой прибытия не найдена")
        st.session_state.show_expected_details = False
    
    st.markdown("---")
    
    # Статистика выполнения поставок
    st.markdown("### 📊 Статистика выполнения")
    
    if "Разница day" in filtered_df.columns:
        total = len(filtered_df)
        on_time = len(filtered_df[filtered_df["Разница day"] >= 0])
        late = len(filtered_df[filtered_df["Разница day"] < 0])
        on_time_percent = (on_time / total * 100) if total > 0 else 0
        
        st.markdown(f"""
            <div style="background: rgba(81,207,102,0.15); border-radius: 12px; padding: 12px; margin: 8px 0; border-left: 3px solid #51cf66;">
                <div style="font-size: 0.85em; opacity: 0.8;">✅ ПРИЕХАЛО ВОВРЕМЯ</div>
                <div style="font-size: 1.8em; font-weight: bold; color: #51cf66;">{on_time}</div>
                <div style="font-size: 0.9em; opacity: 0.8;">{on_time_percent:.1f}% от всех</div>
            </div>
            
            <div style="background: rgba(255,107,107,0.15); border-radius: 12px; padding: 12px; margin: 8px 0; border-left: 3px solid #ff6b6b;">
                <div style="font-size: 0.85em; opacity: 0.8;">⚠️ ПРОСРОЧИЛОСЬ</div>
                <div style="font-size: 1.8em; font-weight: bold; color: #ff6b6b;">{late}</div>
                <div style="font-size: 0.9em; opacity: 0.8;">{(late/total*100) if total>0 else 0:.1f}% от всех</div>
            </div>
            
            <div style="background: rgba(102,126,234,0.15); border-radius: 12px; padding: 12px; margin: 8px 0; border-left: 3px solid #667eea;">
                <div style="font-size: 0.85em; opacity: 0.8;">📦 ВСЕГО ПОСТАВОК</div>
                <div style="font-size: 1.8em; font-weight: bold; color: #667eea;">{total}</div>
            </div>
        """, unsafe_allow_html=True)
        
        if late > 0:
            avg_late_days = filtered_df[filtered_df["Разница day"] < 0]["Разница day"].mean()
            max_late_days = filtered_df[filtered_df["Разница day"] < 0]["Разница day"].min()
            st.markdown(f"""
                <div style="background: rgba(255,255,255,0.08); border-radius: 12px; padding: 12px; margin-top: 12px;">
                    <div style="font-size: 0.85em; margin-bottom: 8px;">📉 ДЕТАЛИ ПРОСРОЧЕК</div>
                    <div style="font-size: 0.9em;">Средняя просрочка: <span style="color: #ff6b6b; font-weight: bold;">{abs(avg_late_days):.1f} дней</span></div>
                    <div style="font-size: 0.9em;">Макс. просрочка: <span style="color: #ff6b6b; font-weight: bold;">{abs(max_late_days):.0f} дней</span></div>
                </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("🔄 **Последнее обновление**")
    st.caption(datetime.now().strftime("%d.%m.%Y %H:%M:%S"))

# --- KPI в карточках (3 метрики)---
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 0.9em; opacity: 0.85; margin-bottom: 10px;">📋 ВСЕГО ЗАКАЗОВ</div>
            <div style="font-size: 2.8em; font-weight: bold; background: linear-gradient(135deg, #fff 0%, #a8c0ff 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{len(filtered_df):,}</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    if "Разница day" in filtered_df.columns:
        late_count = len(filtered_df[filtered_df["Разница day"] < 0])
        st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 0.9em; opacity: 0.85; margin-bottom: 10px;">⚠️ ПРОСРОЧКИ</div>
                <div style="font-size: 2.8em; font-weight: bold; color: #ff6b6b;">{late_count}</div>
            </div>
        """, unsafe_allow_html=True)

with col3:
    if "Разница day" in filtered_df.columns:
        avg_diff = filtered_df["Разница day"].mean()
        diff_color = "#ff6b6b" if avg_diff < 0 else "#51cf66"
        st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 0.9em; opacity: 0.85; margin-bottom: 10px;">📈 СР. ОТКЛОНЕНИЕ</div>
                <div style="font-size: 2.8em; font-weight: bold; color: {diff_color};">{avg_diff:.1f} дн</div>
            </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# --- Вкладки с белыми заголовками ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Дашборд", "⚠️ Просрочки", "📈 Аналитика", "🎨 Визуализации"])

with tab1:
    st.markdown('<h3 style="color: white;">📋 Данные поставщика</h3>', unsafe_allow_html=True)
    st.dataframe(filtered_df, use_container_width=True, height=450, 
                 column_config={
                     "Разница day": st.column_config.NumberColumn("Отклонение", format="%.0f дн")
                 })

with tab2:
    if "Разница day" in filtered_df.columns:
        st.markdown('<h3 style="color: white;">⚠️ Просроченные поставки</h3>', unsafe_allow_html=True)
        late_df = filtered_df[filtered_df["Разница day"] < 0]
        
        if len(late_df) > 0:
            st.error(f"🔔 Обнаружено {len(late_df)} просроченных поставок")
            st.dataframe(late_df, use_container_width=True, height=350)
            
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
    st.markdown('<h3 style="color: white;">📊 Аналитика поставок</h3>', unsafe_allow_html=True)
    
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
            fig.update_traces(marker_line_width=0)
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
            fig.update_traces(textposition='inside', textinfo='percent+label', 
                            textfont=dict(color='white', size=14))
            fig.update_layout(height=450)
            st.plotly_chart(fig, use_container_width=True)
    
    if date_columns:
        st.markdown("---")
        st.markdown('<h3 style="color: white;">📅 Динамика поставок</h3>', unsafe_allow_html=True)
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
    st.markdown('<h3 style="color: white;">🎨 Продвинутые визуализации</h3>', unsafe_allow_html=True)
    
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
            fig.update_traces(marker=dict(size=12, opacity=0.6, line=dict(width=1, color='white')))
            fig.update_layout(height=450, plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            selected_col = st.selectbox("📦 Выберите метрику", numeric_cols)
            fig = px.box(filtered_df, y=selected_col,
                        title=f"Распределение {selected_col}",
                        color_discrete_sequence=["#764ba2"],
                        template="plotly_dark")
            fig.update_traces(marker=dict(color='#667eea'))
            fig.update_layout(height=450, plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
    
    if len(numeric_cols) > 2:
        st.markdown("---")
        st.markdown('<h3 style="color: white;">🔥 Тепловая карта корреляций</h3>', unsafe_allow_html=True)
        corr_matrix = filtered_df[numeric_cols].corr()
        fig = px.imshow(corr_matrix, 
                       text_auto=True, 
                       aspect="auto",
                       color_continuous_scale="RdBu_r",
                       title="Матрица корреляций",
                       template="plotly_dark")
        fig.update_layout(height=500, plot_bgcolor='rgba(0,0,0,0)')
        fig.update_traces(textfont=dict(color='white', size=10))
        st.plotly_chart(fig, use_container_width=True)

# --- Footer ---
st.markdown("---")
st.markdown("""
    <div style="text-align: center; padding: 20px; color: rgba(255,255,255,0.7);">
        <p>✨ Дашборд создан с Streamlit | Автоматическое обновление данных | NWL Logistics</p>
    </div>
""", unsafe_allow_html=True)
