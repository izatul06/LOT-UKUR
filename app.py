import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
from shapely.geometry import Polygon, Point
import numpy as np
import folium
from streamlit_folium import folium_static
from pyproj import Transformer
import json
import os
from folium.plugins import MiniMap

# --- 1. SISTEM LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_name = ""

def check_login(username, password):
    users = {"1": "Izatul", "2": "Faseha", "3": "Aleeya"}
    if username in users and password == "admin123":
        st.session_state.logged_in = True
        st.session_state.user_name = users[username]
        return True
    return False

if not st.session_state.logged_in:
    st.set_page_config(page_title="Login - Analisis Ukur", page_icon="🔒")
    st.title("🔒 Log Masuk Sistem Ukur")
    with st.form("login_form"):
        u = st.text_input("Username (Nombor sahaja)")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Masuk"):
            if check_login(u, p): st.rerun()
            else: st.error("Username atau Password salah!")
    
    st.markdown("---")
    with st.expander("❓ Lupa kata laluan? Klik di sini untuk kemaskini"):
        st.markdown('### 🔑 Kemaskini Kata Laluan')
        with st.form("reset_password_form"):
            user_id = st.text_input("Sahkan ID Pengguna:")
            new_pass = st.text_input("Kata Laluan Baharu:", type="password")
            confirm_pass = st.text_input("Sahkan Kata Laluan Baharu:", type="password")
            if st.form_submit_button("Simpan"):
                if new_pass == confirm_pass and user_id: st.success("Berjaya dikemaskini!")
    st.stop()

# --- 2. APLIKASI UTAMA ---
st.set_page_config(page_title="Analisis Ukur Pro", layout="wide")

def dd_to_dms(dd):
    dd = abs(dd)
    minutes, seconds = divmod(dd * 3600, 60)
    degrees, minutes = divmod(minutes, 60)
    return f"{int(degrees)}° {int(minutes):02d}' {int(seconds):02d}\""

# --- [BAHAGIAN LOGO POLI & TAJUK] ---
col_logo, col_title = st.columns([1, 6])
with col_logo:
    logo_file = "LOGOPOLI.png" 
    if os.path.exists(logo_file):
        st.image(logo_file, width=100)
    else:
        st.markdown("## 📐")

with col_title:
    st.markdown("## Analisis Pelan Poligon (EPSG:4390)")

uploaded_file = st.file_uploader("Upload fail CSV anda", type=['csv'])

# --- SIDEBAR YANG LEBIH GEMPAK ---
with st.sidebar:
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #ff4b4b 0%, #ff8f8f 100%); padding: 20px; border-radius: 15px; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(255, 75, 75, 0.3);">
        <p style="margin: 0; font-size: 14px; color: white; opacity: 0.9;">Selamat Datang,</p>
        <h2 style="margin: 0; color: white; font-size: 24px; font-weight: 700;">👋 {st.session_state.user_name}</h2>
        <div style="height: 2px; background: rgba(255,255,255,0.3); margin: 10px 0;"></div>
        <p style="margin: 0; font-size: 12px; color: white; font-style: italic;">Sistem Analisis Ukur Pro v2.0</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown("### 📋 **Maklumat Lot**")
        no_lot = st.text_input("No. Lot", "Lot 11487", help="Masukkan nombor lot rujukan")
        nama_pemilik = st.text_input("Nama Pemilik", "Ali Bin Abu", help="Masukkan nama pemilik tanah")
    
    st.markdown("---")
    
    st.markdown("### ⚙️ **Konfigurasi Pelan**")
    with st.expander("🔍 Larasan Visual", expanded=True):
        font_size = st.slider("Saiz Tulisan (pt)", 6, 20, 10)
        show_poly = st.toggle("Paparkan Poligon", value=True)
        show_area = st.toggle("Paparkan Maklumat Lot", value=True)
    
    st.markdown("---")
    
    st.markdown("### 🎨 **Tema Visual**")
    c1, c2 = st.columns(2)
    with c1:
        poly_color = st.color_picker("Garis", "#FFFF00") 
    with c2:
        fill_color = st.color_picker("Isian", "#FFFF00")
    fill_opac = st.select_slider("Ketelusan (Opacity)", options=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0], value=0.2)

    if uploaded_file is not None:
        st.markdown("---")
        st.markdown("### 🚀 **Tindakan**")
        df_side = pd.read_csv(uploaded_file)
        uploaded_file.seek(0)
        if 'E' in df_side.columns and 'N' in df_side.columns:
            coords_list = list(zip(df_side['E'], df_side['N']))
            poly_obj = Polygon(coords_list)
            
            feat_poly = {
                "type": "Feature",
                "properties": {"Luas_sqm": round(poly_obj.area, 3), "Perimeter": round(poly_obj.length, 3)},
                "geometry": json.loads(gpd.GeoSeries([poly_obj]).to_json())['features'][0]['geometry']
            }
            feat_points = []
            for _, r in df_side.iterrows():
                p_feat = {
                    "type": "Feature",
                    "properties": {"STN": int(r['STN']), "Easting": float(r['E']), "Northing": float(r['N'])},
                    "geometry": {"type": "Point", "coordinates": [float(r['E']), float(r['N'])]}
                }
                feat_points.append(p_feat)
            
            full_export = {"type": "FeatureCollection", "features": [feat_poly] + feat_points}
            st.download_button(label="📥 Download GeoJSON (QGIS)", data=json.dumps(full_export), file_name="export_ukur_pro.geojson", use_container_width=True, type="primary")

    st.sidebar.markdown("<br>" * 2, unsafe_allow_html=True)
    if st.button("🚪 Log Keluar", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

# --- PROSES DATA ---
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    if 'E' in df.columns and 'N' in df.columns:
        coords = list(zip(df['E'], df['N']))
        poly_geom = Polygon(coords)
        centroid = poly_geom.centroid
        luas = poly_geom.area
        perimeter = poly_geom.length

        tab_pelan, tab_satelit, tab_jadual = st.tabs(["📊 Pelan Teknikal", "🌍 Google Satellite", "📋 Jadual Data"])

        with tab_pelan:
            fig, ax = plt.subplots(figsize=(10, 10))
            if show_poly:
                gpd.GeoDataFrame(index=[0], geometry=[poly_geom]).plot(ax=ax, facecolor=fill_color, edgecolor=poly_color, alpha=fill_opac)
            
            if show_area:
                # Label maklumat di tengah poligon (Pelan Teknikal)
                info_tengah = f"{no_lot}\n{nama_pemilik}\n{luas:.1f} m²\nPerimeter: {perimeter:.3f} m"
                ax.text(centroid.x, centroid.y, info_tengah, fontsize=font_size, fontweight='bold', ha='center', va='center',
                        bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.5'))
            
            for i in range(len(df)):
                p1, p2 = df.iloc[i], df.iloc[(i + 1) % len(df)]
                mid_e, mid_n = (p1['E'] + p2['E']) / 2, (p1['N'] + p2['N']) / 2
                angle_plt = np.degrees(np.arctan2(p2['N'] - p1['N'], p2['E'] - p1['E']))
                if angle_plt > 90: angle_plt -= 180
                elif angle_plt < -90: angle_plt += 180
                
                ax.text(mid_e, mid_n, f"{dd_to_dms(np.degrees(np.arctan2(p2['E'] - p1['E'], p2['N'] - p1['N'])) % 360)}\n{np.sqrt((p2['E']-p1['E'])**2+(p2['N']-p1['N'])**2):.3f}m", 
                        fontsize=font_size-2, ha='center', va='center', rotation=angle_plt)
                ax.text(p1['E'], p1['N']+0.3, f"{int(p1['STN'])}", fontsize=font_size, fontweight='bold')
            ax.set_aspect('equal')
            try:
                st.pyplot(fig)
            except:
                st.error("Gagal render pelan.")
            finally:
                plt.close(fig)

        with tab_satelit:
            transformer = Transformer.from_crs("epsg:4390", "epsg:4326", always_xy=True)
            c_lon, c_lat = transformer.transform(centroid.x, centroid.y)
            m = folium.Map(location=[c_lat, c_lon], zoom_start=20, max_zoom=22)
            folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google', name='Google Hybrid', max_zoom=22).add_to(m)
            
            minimap = MiniMap(toggle_display=True, position='bottomright', width=150, height=150)
            m.add_child(minimap)
            
            fg_poly = folium.FeatureGroup(name="Poligon").add_to(m)
            fg_stn = folium.FeatureGroup(name="Stesen").add_to(m)
            fg_data = folium.FeatureGroup(name="Data").add_to(m)

            if show_poly:
                folium.Polygon(locations=[[transformer.transform(x, y)[1], transformer.transform(x, y)[0]] for x, y in coords], color=poly_color, fill=True, fill_color=fill_color, fill_opacity=fill_opac).add_to(fg_poly)

            if show_area:
                # Pop-up maklumat lot di tengah poligon (Satelit)
                popup_content = f"""
                <div style="font-family: Arial; font-size: 14px; width: 200px;">
                    <h4 style="margin:0; color:#ff4b4b;">Maklumat Lot</h4>
                    <hr style="margin: 5px 0;">
                    <b>No Lot:</b> {no_lot}<br>
                    <b>Pemilik:</b> {nama_pemilik}<br>
                    <b>Luas:</b> {luas:.1f} m²<br>
                    <b>Perimeter:</b> {perimeter:.3f} m
                </div>
                """
                folium.Marker(
                    [c_lat, c_lon],
                    popup=folium.Popup(popup_content, max_width=250),
                    icon=folium.DivIcon(html=f"""
                        <div style="font-family: Arial; font-weight: bold; color: white; text-shadow: 2px 2px 4px black; text-align: center; width: 100px; margin-left: -50px;">
                            {no_lot}<br>{luas:.1f} m²
                        </div>
                    """)
                ).add_to(fg_poly)

            for i in range(len(df)):
                p1, p2 = df.iloc[i], df.iloc[(i + 1) % len(df)]
                lon1, lat1 = transformer.transform(p1['E'], p1['N'])
                lon2, lat2 = transformer.transform(p2['E'], p2['N'])
                
                stn_popup_html = f"<div style='font-family: Arial; font-size: 12px;'><b>STESEN {int(p1['STN'])}</b><br>E: {p1['E']:.3f}<br>N: {p1['N']:.3f}</div>"
                folium.Marker([lat1, lon1], popup=folium.Popup(stn_popup_html, max_width=200), icon=folium.DivIcon(html=f'<div style="font-size:{font_size}pt; color:white; font-weight:bold; background:black; border-radius:50%; width:22px; height:22px; line-height:22px; text-align:center; border:1px solid white;">{int(p1["STN"])}</div>')).add_to(fg_stn)
                
                mid_lat, mid_lon = (lat1 + lat2) / 2, (lon1 + lon2) / 2
                angle_css = -np.degrees(np.arctan2(p2['N'] - p1['N'], p2['E'] - p1['E']))
                if angle_css > 90: angle_css -= 180
                elif angle_css < -90: angle_css += 180
                folium.Marker([mid_lat, mid_lon], icon=folium.DivIcon(html=f'''<div style="transform: rotate({angle_css}deg); text-align: center; width: 150px; margin-left: -75px;"><div style="font-size: {font_size-2}pt; color: #00FF00; font-weight: bold; text-shadow: 1px 1px 2px black;">{dd_to_dms(np.degrees(np.arctan2(p2['E'] - p1['E'], p2['N'] - p1['N'])) % 360)}</div><div style="font-size: {font_size-2}pt; color: yellow; font-weight: bold; text-shadow: 1px 1px 2px black;">{np.sqrt((p2['E']-p1['E'])**2+(p2['N']-p1['N'])**2):.3f}m</div></div>''')).add_to(fg_data)

            folium.LayerControl().add_to(m)
            folium_static(m, width=1000)

        with tab_jadual:
            # --- SEKSYEN RINGKASAN DATA ---
            st.markdown("### 📊 Ringkasan Analisis")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Jumlah Stesen", len(df))
            with c2:
                st.metric("Jumlah Luas", f"{luas:.3f} m²")
            with c3:
                st.metric("Perimeter", f"{poly_geom.length:.3f} m")
            
            st.markdown("---")
            
            # --- JADUAL TERPERINCI ---
            st.markdown("### 📋 Data Cerapan Poligon")
            data_list = []
            for i in range(len(df)):
                p1, p2 = df.iloc[i], df.iloc[(i + 1) % len(df)]
                latit, dipat = p2['N'] - p1['N'], p2['E'] - p1['E']
                bearing = np.degrees(np.arctan2(dipat, latit)) % 360
                dist = np.sqrt(latit**2 + dipat**2)
                data_list.append({
                    "Dari": int(p1['STN']), 
                    "Ke": int(p2['STN']), 
                    "Bearing": dd_to_dms(bearing), 
                    "Jarak (m)": round(dist, 3), 
                    "Latit (ΔN)": round(latit, 3), 
                    "Dipat (ΔE)": round(dipat, 3)
                })
            st.table(pd.DataFrame(data_list))
