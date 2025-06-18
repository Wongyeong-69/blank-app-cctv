import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import os

# 페이지 설정
st.set_page_config(layout="wide", page_title="부산시 데이터 통합 시각화")
st.title("\U0001F4CA 부산시 통합 시각화 대시보드")

# 한글 폰트 설정
font_path = "NanumGothic.ttf"
if not os.path.exists(font_path):
    st.error(f"❌ NanumGothic.ttf 파일이 존재하지 않습니다.\n\n경로: {os.path.abspath(font_path)}")
    st.stop()
fontprop = fm.FontProperties(fname=font_path)
plt.rcParams['axes.unicode_minus'] = False

# 탭 생성
tab1, tab2, tab3, tab4 = st.tabs(["📍 CCTV 지도 + 범죄 비교", "📈 가로등 vs 범죄", "🏠 1인 가구 vs 가로등", "🚓 동별 경찰서 수"])

# TAB 1: CCTV 지도 + 범죄 그래프
with tab1:
    col1, col2 = st.columns([1, 1.5])

    with col1:
        st.subheader("📍 CCTV 위치 분포도")
        try:
            df = pd.read_excel("12_04_08_E_CCTV정보.xlsx", engine="openpyxl")
            cols = df.columns.tolist()
            find = lambda kw: next((c for c in cols if kw in c), None)
            df_vis = df.rename(columns={
                find("설치목적"): "목적",
                find("도로명주소"): "설치장소",
                find("위도"): "위도",
                find("경도"): "경도",
                find("설치연"): "설치연도",
                find("카메라대수"): "대수"
            }).dropna(subset=["위도", "경도"])

            m = folium.Map(location=[df_vis["위도"].mean(), df_vis["경도"].mean()], zoom_start=11)
            marker_cluster = MarkerCluster().add_to(m)
            for _, row in df_vis.iterrows():
                popup = f"<b>목적:</b> {row['목적']}<br><b>장소:</b> {row['설치장소']}<br><b>연도:</b> {row['설치연도']}<br><b>대수:</b> {row['대수']}"
                folium.Marker(location=[row["위도"], row["경도"]],
                              popup=folium.Popup(popup, max_width=300)).add_to(marker_cluster)
            st_folium(m, width=450, height=500)
        except Exception as e:
            st.error(f"❌ CCTV 지도 오류: {e}")

    with col2:
        st.subheader("📊 CCTV 개수 vs 5대 범죄 발생 수")
        try:
            df = pd.read_csv("경찰청 부산광역시경찰청_경찰서별 5대 범죄 발생 현황_20231231.csv", encoding="cp949")
            df.columns = df.columns.str.strip()
            df["5대 범죄 합계"] = df[["살인", "강도", "성범죄",  "폭력"]].sum(axis=1)

            df = df.sort_values("경찰서")

            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(df["경찰서"], df["cctv개수"], label="CCTV 개수", marker='o', color='orange')
            ax.plot(df["경찰서"], df["5대 범죄 합계"], label="범죄 건수", marker='s', color='orangered')

            ax.set_title("지역별 CCTV 개수와 범죄 발생 건수 비교(강도, 살인,성범죄, 폭력)", fontproperties=fontprop, fontsize=16)
            ax.set_xlabel("경찰서", fontproperties=fontprop)
            ax.set_ylabel("건수", fontproperties=fontprop)
            ax.set_xticks(range(len(df)))
            ax.set_xticklabels(df["경찰서"], rotation=45, fontproperties=fontprop)
            ax.legend(prop=fontprop)
            ax.grid(True)
            st.pyplot(fig)
        except Exception as e:
            st.error(f"❌ CCTV/범죄 시각화 오류: {e}")

# TAB 2: 가로등 vs 범죄
with tab2:
    st.subheader("📈 지역별 가로등 수 vs 5대 범죄 발생 수")
    try:
        df_lights = pd.read_csv("가로등현황.csv", encoding="cp949")
        df_crime = pd.read_csv("경찰청_범죄현황.csv", encoding="cp949")
        df_lights.columns = df_lights.columns.str.strip()
        df_crime.columns = df_crime.columns.str.strip()
        df_lights.rename(columns={'관리부서': '지역'}, inplace=True)
        df_lights['지역'] = df_lights['지역'].str.replace(' ', '')
        df_crime['지역'] = df_crime['지역'].str.replace(' ', '')
        merged = pd.merge(
            df_lights[['지역', '합계']],
            df_crime[['지역', '합계']],
            on='지역',
            suffixes=('_가로등', '_범죄')
        )

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(merged['지역'], merged['합계_가로등'], label='가로등 수', marker='o')
        ax.plot(merged['지역'], merged['합계_범죄'], label='범죄 발생 수', marker='s')
        ax.set_xticks(range(len(merged['지역'])))
        ax.set_xticklabels(merged['지역'], rotation=45, fontproperties=fontprop)
        ax.set_ylabel("건수", fontproperties=fontprop)
        ax.set_xlabel("지역", fontproperties=fontprop)
        ax.set_title("지역별 가로등 수와 범죄 발생 수 비교", fontproperties=fontprop)
        ax.legend(prop=fontprop)

        st.pyplot(fig)
    except Exception as e:
        st.error(f"❌ 범죄/가로등 데이터 오류: {e}")

# TAB 3: 1인 가구 vs 가로등
with tab3:
    st.subheader("🏠 1인가구 수 vs 가로등 수")
    try:
        one_person_data = {
            '지역': ['중부', '동래', '영도', '동부', '부산진', '서부', '남부', '해운대',
                   '사상', '금정', '사하', '연제', '강서', '북부', '기장'],
            '1인가구수': [11786, 35220, 20116, 18603, 70609, 20760, 40521, 50516,
                      36299, 40412, 46442, 30846, 17355, 36975, 22500]
        }
        df_one = pd.DataFrame(one_person_data)
        df_lights = pd.read_csv("가로등현황.csv", encoding="cp949")
        df_lights.columns = df_lights.columns.str.strip()
        df_lights.rename(columns={"관리부서": "지역", "합계": "가로등수"}, inplace=True)
        df_lights['지역'] = df_lights['지역'].str.replace(" ", "")
        df_merged = pd.merge(df_one, df_lights[['지역', '가로등수']], on='지역')

        fig1, ax1 = plt.subplots()
        ax1.scatter(df_merged['1인가구수'], df_merged['가로등수'])
        for i in range(len(df_merged)):
            ax1.text(df_merged['1인가구수'][i], df_merged['가로등수'][i],
                     df_merged['지역'][i], fontsize=9, fontproperties=fontprop)
        ax1.set_xlabel("1인가구 수", fontproperties=fontprop)
        ax1.set_ylabel("가로등 수", fontproperties=fontprop)
        ax1.set_title("1인가구 수 vs 가로등 수 (산점도)", fontproperties=fontprop)
        st.pyplot(fig1)

        fig2, ax2 = plt.subplots(figsize=(12, 6))
        index = np.arange(len(df_merged))
        bar_width = 0.4
        ax2.bar(index, df_merged['1인가구수'], bar_width, label='1인가구 수')
        ax2.bar(index + bar_width, df_merged['가로등수'], bar_width, label='가로등 수')
        ax2.set_xticks(index + bar_width / 2)
        ax2.set_xticklabels(df_merged['지역'], rotation=45, fontproperties=fontprop)
        ax2.set_ylabel("건수", fontproperties=fontprop)
        ax2.set_title("지역별 1인가구 수 vs 가로등 수 비교", fontproperties=fontprop)
        ax2.legend(prop=fontprop)
        st.pyplot(fig2)
    except Exception as e:
        st.error(f"❌ 1인가구/가로등 시각화 오류: {e}")

# TAB 4: 동별 경찰서 수
with tab4:
    st.subheader("🚓 부산 동별 경찰서 수")
    try:
        df_police = pd.read_csv("부산동별경찰서.csv", encoding="cp949")
        df_police.columns = df_police.columns.str.strip()
        df_police = df_police.sort_values("개수", ascending=False)

        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(df_police["경찰서"], df_police["개수"], color="skyblue")

        ax.set_xticks(range(len(df_police)))
        ax.set_xticklabels(df_police["경찰서"], rotation=45, fontproperties=fontprop)
        ax.set_xlabel("지역", fontproperties=fontprop)
        ax.set_ylabel("경찰서 수", fontproperties=fontprop)
        ax.set_title("부산 동별 경찰서 수sd", fontproperties=fontprop)

        for i, bar in enumerate(bars):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, height, f"{int(height)}",
                    ha='center', va='bottom', fontproperties=fontprop)

        st.pyplot(fig)
    except Exception as e:
        st.error(f"❌ 경찰서 수 시각화 오류: {e}") 