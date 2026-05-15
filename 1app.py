 
import streamlit as st
import folium
from folium import plugins
from streamlit_folium import st_folium
import time
import pandas as pd
from datetime import date
import urllib.parse
import requests

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Enjambre VRA | Plataforma Integral", page_icon="🚁", layout="wide")

st.markdown("""
    <style>
    .sensor-verde { background-color: #d4edda; color: #155724; padding: 15px; border-radius: 8px; border-left: 5px solid #28a745; text-align: center; }
    .sensor-amarillo { background-color: #fff3cd; color: #856404; padding: 15px; border-radius: 8px; border-left: 5px solid #ffc107; text-align: center; }
    .sensor-rojo { background-color: #f8d7da; color: #721c24; padding: 15px; border-radius: 8px; border-left: 5px solid #dc3545; text-align: center; font-weight: bold;}
    .whatsapp-btn { background-color: #25D366; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block; text-align: center; width: 100%;}
    </style>
""", unsafe_allow_html=True)

# Variables de Memoria
if 'paso' not in st.session_state: st.session_state.paso = 'login'
if 'usuario' not in st.session_state: st.session_state.usuario = {}
if 'parcela_area' not in st.session_state: st.session_state.parcela_area = 0
if 'cultivos_asignados' not in st.session_state: st.session_state.cultivos_asignados = {}
if 'registro_diario' not in st.session_state: st.session_state.registro_diario = []
if 'poligono_coords' not in st.session_state: st.session_state.poligono_coords = None
if 'clima_real' not in st.session_state: st.session_state.clima_real = {"temp": 0, "hum": 0, "viento": 0}
if 'total_litros_hoy' not in st.session_state: st.session_state.total_litros_hoy = 0

DB_CULTIVOS = ["Cerezas", "Uva Vinífera", "Paltos", "Nogales", "Maíz", "Trigo", "Arándanos"]

def obtener_clima_real(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=relative_humidity_2m"
        respuesta = requests.get(url).json()
        temp = respuesta["current_weather"]["temperature"]
        viento = respuesta["current_weather"]["windspeed"]
        humedad = respuesta["hourly"]["relative_humidity_2m"][0]
        return {"temp": temp, "hum": humedad, "viento": viento}
    except:
        return {"temp": 28.5, "hum": 35, "viento": 12.0}

# --- FASE 1: REGISTRO ---
if st.session_state.paso == 'login':
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🌱 Enjambre VRA")
        st.subheader("Configuración de Administrador")
        with st.form("registro_form"):
            nombre = st.text_input("Nombre Completo")
            email = st.text_input("Correo Electrónico")
            telefono = st.text_input("Número de Teléfono (Ej: 56912345678)")
            password = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Ingresar al Sistema", type="primary", use_container_width=True)
            if submit and nombre and email and telefono:
                st.session_state.usuario = {'nombre': nombre, 'email': email, 'telefono': telefono}
                st.session_state.paso = 'onboarding_mapa'
                st.rerun()

# --- FASE 2: MAPA ---
elif st.session_state.paso == 'onboarding_mapa':
    st.header(f"Bienvenido {st.session_state.usuario['nombre']} - Delimitación Satelital")
    st.write("📍 Dibuje su parcela en el mapa para iniciar el cálculo hídrico.")
    mapa_dibujo = folium.Map(location=[-33.456, -70.650], zoom_start=15, tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", attr="Esri")
    draw = plugins.Draw(export=True, position='topleft', draw_options={'polyline':False, 'marker':False, 'circle':False})
    draw.add_to(mapa_dibujo)
    mapa_data = st_folium(mapa_dibujo, width=1000, height=400, key="dibujo_inicial")
    
    area_ingresada = st.number_input("Área total del predio (m²):", min_value=100, value=5000)
    
    if st.button("Confirmar Terreno ➡️", type="primary"):
        st.session_state.parcela_area = area_ingresada
        lat_clima, lon_clima = -33.456, -70.650
        if mapa_data and mapa_data.get("all_drawings"):
            dibujo = mapa_data["all_drawings"][0]
            st.session_state.poligono_coords = dibujo["geometry"]["coordinates"][0]
            lon_clima, lat_clima = st.session_state.poligono_coords[0][0], st.session_state.poligono_coords[0][1]
        st.session_state.clima_real = obtener_clima_real(lat_clima, lon_clima)
        st.session_state.paso = 'onboarding_cultivos'
        st.rerun()

# --- FASE 3: CULTIVOS ---
elif st.session_state.paso == 'onboarding_cultivos':
    st.header("🌾 Distribución de Plantaciones")
    cultivos_seleccionados = st.multiselect("Seleccione cultivos:", DB_CULTIVOS)
    if cultivos_seleccionados:
        area_asignada_total = 0
        asignaciones = {}
        for c in cultivos_seleccionados:
            m2 = st.number_input(f"Metros cuadrados para {c}:", min_value=0, max_value=st.session_state.parcela_area, step=100)
            asignaciones[c] = m2
            area_asignada_total += m2
        if area_asignada_total <= st.session_state.parcela_area and area_asignada_total > 0:
            if st.button("✅ Acceder al Dashboard", type="primary"):
                st.session_state.cultivos_asignados = asignaciones
                st.session_state.paso = 'dashboard'
                st.rerun()
        elif area_asignada_total > st.session_state.parcela_area:
            st.error("Área excedida.")

# --- FASE 4: DASHBOARD ---
elif st.session_state.paso == 'dashboard':
    st.title(f"📊 Dashboard Enjambre VRA | Admin: {st.session_state.usuario['nombre']}")
    tab1, tab2, tab3 = st.tabs(["🌱 1. IoT & Suelo", "🚁 2. Logística Dron", "📈 3. Bitácora & WhatsApp"])

    with tab1:
        st.header("Monitoreo Inteligente")
        c = st.columns(4)
        c[0].metric("Temperatura", f"{st.session_state.clima_real['temp']}°C")
        c[1].metric("Humedad", f"{st.session_state.clima_real['hum']}%")
        c[2].metric("Viento", f"{st.session_state.clima_real['viento']} km/h")
        c[3].metric("Área Total", f"{st.session_state.parcela_area} m²")

    with tab2:
        st.header("Centro de Mando VRA")
        col_ctrl, col_map = st.columns([1, 2])
        with col_ctrl:
            hora = st.slider("Reloj:", 0, 23, 14)
            tipo = st.radio("Misión:", ["Riego de Emergencia", "Proteínas", "Anti-plagas"])
            riesgo = (tipo == "Riego de Emergencia" and 10 <= hora <= 18)
            disable = riesgo and not st.checkbox("Entiendo los riesgos de quemadura foliar.")
            
            if st.button("🚀 Iniciar Vuelo", type="primary", disabled=disable, use_container_width=True):
                # CÁLCULO DE LITROS (0.5 L por m2)
                litros_usados = st.session_state.parcela_area * 0.5 if tipo == "Riego de Emergencia" else 0
                st.session_state.total_litros_hoy += litros_usados
                
                with st.spinner("Procesando..."):
                    time.sleep(1)
                    st.success(f"Misión completada. Agua utilizada: {litros_usados} Litros.")
                    st.session_state.registro_diario.append({
                        "Hora": f"{hora}:00", 
                        "Acción": tipo, 
                        "Litros Agua": f"{litros_usados} L",
                        "Estado": "Finalizado",
                        "Área": f"{st.session_state.parcela_area} m²"
                    })
        with col_map:
            mapa = folium.Map(location=[-33.456, -70.650], zoom_start=15, tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", attr="Esri")
            if st.session_state.poligono_coords:
                folium.Polygon(locations=[[p[1], p[0]] for p in st.session_state.poligono_coords], color="cyan", fill=True, opacity=0.4).add_to(mapa)
            st_folium(mapa, width=700, height=400)

    with tab3:
        st.header("Bitácora de Optimización de Recursos")
        st.dataframe(pd.DataFrame(st.session_state.registro_diario), use_container_width=True)
        
        msg = f"*REPORTE ENJAMBRE VRA*\nAdmin: {st.session_state.usuario['nombre']}\nÁrea: {st.session_state.parcela_area} m2\n*CONSUMO HÍDRICO HOY: {st.session_state.total_litros_hoy} Litros*"
        st.text_area("Mensaje:", msg)
        link = f"https://api.whatsapp.com/send?phone={st.session_state.usuario['telefono']}&text={urllib.parse.quote(msg)}"
        st.markdown(f'<a href="{link}" target="_blank" class="whatsapp-btn">📲 Enviar Reporte de Consumo</a>', unsafe_allow_html=True)
