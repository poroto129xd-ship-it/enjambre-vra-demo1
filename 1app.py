import streamlit as st
import folium
from folium import plugins
from streamlit_folium import st_folium
import time
import pandas as pd
from datetime import date
import urllib.parse
import requests
import base64
import math
from twilio.rest import Client

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Enjambre VRA | Plataforma Integral", page_icon="🚁", layout="wide")

# --- FUNCIÓN PARA CARGAR IMAGEN DE FONDO ---
def cargar_imagen_base64(ruta_imagen):
    try:
        with open(ruta_imagen, "rb") as archivo:
            return base64.b64encode(archivo.read()).decode()
    except FileNotFoundError:
        return None

# --- 🚀 HACK DE JAVASCRIPT: CURSOR DE HORMIGA ESTÁTICO (CSS PURO) ---
st.markdown("""
    <style>
    body, .stApp, [data-testid="stAppViewContainer"], * {
        cursor: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='32' height='32'><text y='24' font-size='24'>🐜</text></svg>") 16 16, auto !important;
    }
    
    .sensor-verde { background-color: #d4edda; color: #155724; padding: 15px; border-radius: 8px; border-left: 5px solid #28a745; text-align: center; margin-bottom: 10px;}
    .sensor-amarillo { background-color: #fff3cd; color: #856404; padding: 15px; border-radius: 8px; border-left: 5px solid #ffc107; text-align: center; margin-bottom: 10px;}
    .sensor-rojo { background-color: #f8d7da; color: #721c24; padding: 15px; border-radius: 8px; border-left: 5px solid #dc3545; text-align: center; font-weight: bold; margin-bottom: 10px;}
    .horario-auto { background-color: #e2e3e5; color: #383d41; padding: 10px; border-radius: 5px; border-left: 5px solid #6c757d; margin-bottom: 5px;}
    .whatsapp-btn { background-color: #25D366; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block; text-align: center; width: 100%;}
    .whatsapp-btn:hover { background-color: #128C7E; color: white;}
    </style>
""", unsafe_allow_html=True)

# --- DISEÑO VISUAL: FONDO AGRÍCOLA ANIMADO ---
fondo_base64 = cargar_imagen_base64("assets/fondo_campo.jpg")

if fondo_base64:
    fondo_css = f"""
    background-image:
        linear-gradient(rgba(0, 25, 10, 0.72), rgba(0, 40, 18, 0.84)),
        url("data:image/jpg;base64,{fondo_base64}");
    background-size: 115%;
    background-position: center;
    background-attachment: fixed;
    animation: moverFondoCampo 28s ease-in-out infinite alternate;
    """
else:
    fondo_css = """
    background:
        radial-gradient(circle at top left, rgba(34,197,94,0.35), transparent 35%),
        radial-gradient(circle at bottom right, rgba(132,204,22,0.25), transparent 35%),
        linear-gradient(135deg, #052e16 0%, #064e3b 45%, #022c22 100%);
    """

st.markdown(f"""
<style>
#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}
header {{ background: transparent !important; }}
.stApp {{ {fondo_css} color: white; }}
@keyframes moverFondoCampo {{
    0% {{ background-position: center center; background-size: 115%; }}
    50% {{ background-position: center top; background-size: 122%; }}
    100% {{ background-position: center bottom; background-size: 118%; }}
}}
.stApp::before {{
    content: ""; position: fixed; top: 0; left: 0; width: 200%; height: 200%;
    pointer-events: none; z-index: 0;
    background-image:
        radial-gradient(circle, rgba(134, 239, 172, 0.20) 2px, transparent 3px),
        radial-gradient(circle, rgba(187, 247, 208, 0.14) 1px, transparent 3px),
        radial-gradient(circle, rgba(34, 197, 94, 0.12) 2px, transparent 4px);
    background-size: 120px 120px, 180px 180px, 250px 250px;
    animation: particulasCampo 35s linear infinite;
}}
@keyframes particulasCampo {{
    0% {{ transform: translate(0, 0); }}
    100% {{ transform: translate(-250px, -350px); }}
}}
.block-container {{ position: relative; z-index: 2; padding-top: 2rem; padding-bottom: 2rem; }}
[data-testid="stForm"] {{ background: rgba(0, 45, 20, 0.58); padding: 28px; border-radius: 24px; border: 1px solid rgba(187, 247, 208, 0.28); backdrop-filter: blur(14px); box-shadow: 0 20px 60px rgba(0, 0, 0, 0.38); }}
[data-testid="stMetric"] {{ background: rgba(0, 45, 20, 0.42); padding: 18px; border-radius: 18px; border: 1px solid rgba(187, 247, 208, 0.20); box-shadow: 0 12px 35px rgba(0, 0, 0, 0.24); }}
button[data-baseweb="tab"] {{ background: rgba(0, 45, 20, 0.42); border-radius: 14px; color: white; margin-right: 8px; border: 1px solid rgba(187, 247, 208, 0.18); }}
button[data-baseweb="tab"]:hover {{ background: rgba(34, 197, 94, 0.25); }}
h1, h2, h3, h4, p, label, span {{ color: white; }}
.stTextInput input, .stNumberInput input, .stSelectbox div, .stMultiSelect div {{ border-radius: 12px; }}
.stButton > button {{ border-radius: 14px; font-weight: 700; border: none; background: linear-gradient(135deg, #22c55e, #15803d); color: white; box-shadow: 0 8px 25px rgba(34, 197, 94, 0.25); }}
.stButton > button:hover {{ background: linear-gradient(135deg, #16a34a, #166534); color: white; transform: scale(1.01); }}
[data-testid="stDataFrame"], [data-testid="stAlert"] {{ border-radius: 18px; }}
section[data-testid="stSidebar"] {{ background: rgba(2, 44, 34, 0.94); border-right: 1px solid rgba(187, 247, 208, 0.20); }}
</style>
""", unsafe_allow_html=True)

# --- HOJAS ANIMADAS ---
st.markdown("""
<style>
.hojas-animadas { position: fixed; inset: 0; pointer-events: none; z-index: 1; overflow: hidden; }
.hoja { position: absolute; top: -10%; font-size: 24px; opacity: 0.45; animation: caerHojas 16s linear infinite; }
.hoja:nth-child(1) { left: 5%; animation-delay: 0s; }
.hoja:nth-child(2) { left: 18%; animation-delay: 3s; }
.hoja:nth-child(3) { left: 33%; animation-delay: 6s; }
.hoja:nth-child(4) { left: 50%; animation-delay: 1s; }
.hoja:nth-child(5) { left: 66%; animation-delay: 4s; }
.hoja:nth-child(6) { left: 82%; animation-delay: 8s; }
.hoja:nth-child(7) { left: 92%; animation-delay: 11s; }
@keyframes caerHojas { 0% { transform: translateY(-10vh) translateX(0) rotate(0deg); } 50% { transform: translateY(55vh) translateX(35px) rotate(180deg); } 100% { transform: translateY(120vh) translateX(-25px) rotate(360deg); } }
</style>
<div class="hojas-animadas"><div class="hoja">🌿</div><div class="hoja">🍃</div><div class="hoja">🌱</div><div class="hoja">🍃</div><div class="hoja">🌿</div><div class="hoja">🌱</div><div class="hoja">🍃</div></div>
""", unsafe_allow_html=True)

# --- 🚀 BASE DE DATOS PLAS (CHILE) ---
DB_CULTIVOS_PLAS = {
    "Cerezas": {"agua_m2": 4.5, "color": "#d32f2f"},          
    "Uva Vinífera": {"agua_m2": 2.5, "color": "#7b1fa2"},     
    "Paltos": {"agua_m2": 6.0, "color": "#388e3c"},           
    "Nogales": {"agua_m2": 5.5, "color": "#795548"},          
    "Maíz": {"agua_m2": 4.0, "color": "#fbc02d"},             
    "Trigo": {"agua_m2": 3.0, "color": "#ffa000"},            
    "Arándanos": {"agua_m2": 3.5, "color": "#1976d2"},        
    "Cítricos": {"agua_m2": 4.0, "color": "#cddc39"},
    "Tomates": {"agua_m2": 5.0, "color": "#e64a19"}           
}

# --- MEMORIA DEL SISTEMA ---
if 'paso' not in st.session_state: st.session_state.paso = 'login'
if 'usuario' not in st.session_state: st.session_state.usuario = {}
if 'parcela_area' not in st.session_state: st.session_state.parcela_area = 0
if 'cultivos_mapeados' not in st.session_state: st.session_state.cultivos_mapeados = {} 
if 'registro_diario' not in st.session_state: st.session_state.registro_diario = []
if 'poligono_coords' not in st.session_state: st.session_state.poligono_coords = None
if 'centro_mapa' not in st.session_state: st.session_state.centro_mapa = [-33.456, -70.650]
if 'mapa_buscador_inicial' not in st.session_state: st.session_state.mapa_buscador_inicial = [-33.456, -70.650]
if 'clima_real' not in st.session_state: st.session_state.clima_real = {"temp": 0, "hum": 0, "viento": 0}

# 🔥 MEMORIA PERMANENTE DEL DRON Y AHORRO DE AGUA
if 'total_litros_hoy' not in st.session_state: st.session_state.total_litros_hoy = 0
if 'total_litros_tradicional' not in st.session_state: st.session_state.total_litros_tradicional = 0
if 'ruta_dron_actual' not in st.session_state: st.session_state.ruta_dron_actual = []
if 'color_dron_actual' not in st.session_state: st.session_state.color_dron_actual = "cyan"
if 'mostrar_animacion_dron' not in st.session_state: st.session_state.mostrar_animacion_dron = False
if 'patron_animacion' not in st.session_state: st.session_state.patron_animacion = ""

# --- 🚀 FUNCIONES MATEMÁTICAS ---
def calcular_area_poligono(coords):
    if not coords or len(coords) < 3: return 0
    R = 6378137
    lats = [p[1] for p in coords]
    mean_lat = math.radians(sum(lats) / len(lats))
    pts_meters = [(R * math.radians(p[0]) * math.cos(mean_lat), R * math.radians(p[1])) for p in coords]
    area = 0
    for i in range(len(pts_meters)):
        j = (i + 1) % len(pts_meters)
        area += pts_meters[i][0] * pts_meters[j][1]
        area -= pts_meters[j][0] * pts_meters[i][1]
    return abs(area) / 2.0

def enviar_whatsapp_twilio(mensaje, telefono_destino):
    try:
        required_secrets = ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE"]
        if [s for s in required_secrets if s not in st.secrets]: return False, "Faltan secrets"
        client = Client(st.secrets["TWILIO_ACCOUNT_SID"], st.secrets["TWILIO_AUTH_TOKEN"])
        message = client.messages.create(body=mensaje, from_=st.secrets["TWILIO_PHONE"], to=f"whatsapp:+{telefono_destino}")
        return True, message.sid
    except Exception as e: return False, str(e)

def buscar_ubicacion(direccion):
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(direccion)}&format=json&limit=1"
        res = requests.get(url, headers={'User-Agent': 'EnjambreVRADemo/1.0'}).json()
        if res: return [float(res[0]['lat']), float(res[0]['lon'])]
    except: pass
    return None

def obtener_clima_real(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=relative_humidity_2m"
        res = requests.get(url).json()
        return {"temp": res["current_weather"]["temperature"], "hum": res["hourly"]["relative_humidity_2m"][0], "viento": res["current_weather"]["windspeed"]}
    except: return {"temp": 13.8, "hum": 73, "viento": 1.7}

def calcular_ruta_patron(coords_zona, patron, lat_base, lon_base):
    if not coords_zona: return []
    c_lat, c_lon = sum(p[0] for p in coords_zona)/len(coords_zona), sum(p[1] for p in coords_zona)/len(coords_zona)
    ruta = [[lat_base, lon_base], [c_lat, c_lon]]
    if patron == "Perimetral (Bordes)":
        ruta.extend(coords_zona)
        ruta.append(coords_zona[0])
    elif patron == "Zig-Zag (Cobertura Total)":
        lats = [p[0] for p in coords_zona]; max_lat, min_lat = max(lats), min(lats); paso_lat = (max_lat - min_lat) / 6 
        poly = coords_zona + [coords_zona[0]]
        for i in range(1, 6):
            lat_act = max_lat - (i * paso_lat); intersecciones = []
            for j in range(len(poly)-1):
                p1, p2 = poly[j], poly[j+1]
                if (p1[0] <= lat_act < p2[0]) or (p2[0] <= lat_act < p1[0]):
                    if p2[0] != p1[0]: intersecciones.append(p1[1] + (lat_act - p1[0]) * (p2[1] - p1[1]) / (p2[0] - p1[0]))
            intersecciones.sort()
            if len(intersecciones) >= 2:
                if i % 2 == 0: ruta.extend([[lat_act, intersecciones[0]], [lat_act, intersecciones[-1]]])
                else: ruta.extend([[lat_act, intersecciones[-1]], [lat_act, intersecciones[0]]])
    ruta.append([lat_base, lon_base])
    return ruta

# ==========================================
# FASE 1: REGISTRO
# ==========================================
if st.session_state.paso == 'login':
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🌱 Enjambre VRA")
        st.subheader("Acceso Administrativo")
        with st.form("registro_form"):
            nombre = st.text_input("Nombre Completo")
            telefono = st.text_input("WhatsApp (Ej: 56912345678)")
            submit = st.form_submit_button("Ingresar", type="primary", use_container_width=True)
            if submit and nombre and telefono:
                st.session_state.usuario = {'nombre': nombre, 'telefono': ''.join(filter(str.isdigit, telefono))}
                st.session_state.paso = 'onboarding_mapa'; st.rerun()

# ==========================================
# FASE 2: DELIMITACIÓN TOTAL
# ==========================================
elif st.session_state.paso == 'onboarding_mapa':
    st.header(f"Bienvenido {st.session_state.usuario.get('nombre', '')} - Perímetro Predial")
    tab_dir, tab_coord = st.tabs(["📍 Por Dirección", "🧭 Por Coordenadas"])
    with tab_dir:
        c_s, c_b = st.columns([3, 1])
        with c_s: dir_b = st.text_input("Ingrese ubicación:")
        with c_b: 
            st.write(""); 
            if st.button("Buscar"): 
                coords = buscar_ubicacion(dir_b)
                if coords: st.session_state.mapa_buscador_inicial = coords; st.rerun()
    with tab_coord:
        c_lat, c_lon, c_btn = st.columns([2, 2, 1])
        with c_lat: lat_b = st.number_input("Latitud:", value=st.session_state.mapa_buscador_inicial[0], format="%.5f")
        with c_lon: lon_b = st.number_input("Longitud:", value=st.session_state.mapa_buscador_inicial[1], format="%.5f")
        with c_btn: 
            st.write(""); 
            if st.button("Ir Coordenadas"): st.session_state.mapa_buscador_inicial = [lat_b, lon_b]; st.rerun()

    st.write("📍 **Dibuje el perímetro total de su campo (Polígono/Rectángulo):**")
    m_dibujo = folium.Map(location=st.session_state.mapa_buscador_inicial, zoom_start=15, tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", attr="Esri")
    draw = plugins.Draw(export=True, draw_options={'polyline':False, 'circle':False, 'marker':False, 'circlemarker':False}).add_to(m_dibujo)
    m_data = st_folium(m_dibujo, height=450, use_container_width=True, key="dibujo_total")
    
    if m_data and m_data.get("all_drawings"):
        st.session_state.poligono_coords = m_data["all_drawings"][0]["geometry"]["coordinates"][0]
        area_calc = calcular_area_poligono(st.session_state.poligono_coords)
        st.success(f"✅ Perímetro detectado: **{area_calc:,.1f} m²**")
        if st.button("Confirmar Perímetro Predial ➡️", type="primary"):
            st.session_state.parcela_area = int(area_calc)
            pts = [[p[1], p[0]] for p in st.session_state.poligono_coords[:-1]]
            st.session_state.centro_mapa = [sum(p[0] for p in pts)/len(pts), sum(p[1] for p in pts)/len(pts)]
            st.session_state.clima_real = obtener_clima_real(st.session_state.centro_mapa[0], st.session_state.centro_mapa[1])
            st.session_state.paso = 'onboarding_cultivos'; st.rerun()

# ==========================================
# FASE 3: MAPEADOR INTERACTIVO PLAS
# ==========================================
elif st.session_state.paso == 'onboarding_cultivos':
    st.header("🌾 Fase PLAS: Mapeo de Sectores Productivos")
    st.write(f"Área Disponible: **{st.session_state.parcela_area:,} m²**")
    
    col_ctrl, col_map = st.columns([1, 2])
    
    with col_ctrl:
        st.subheader("1. Seleccionar Tipo de Planta")
        tipo_cultivo = st.selectbox("Base de Datos PLAS (Chile):", list(DB_CULTIVOS_PLAS.keys()))
        req_h = DB_CULTIVOS_PLAS[tipo_cultivo]['agua_m2']
        color_c = DB_CULTIVOS_PLAS[tipo_cultivo]['color']
        
        st.info(f"Requerimiento PLAS: **{req_h} L/m²**")
        st.write("2. Dibuje el sector de este cultivo en el mapa.")
        
        if st.button("💾 GUARDAR SECTOR MAPEADO", use_container_width=True):
            if 'temp_coords' in st.session_state and st.session_state.temp_coords:
                area_s = calcular_area_poligono(st.session_state.temp_coords)
                st.session_state.cultivos_mapeados[f"{tipo_cultivo}_{time.time()}"] = {
                    'nombre': tipo_cultivo,
                    'coords': [[p[1], p[0]] for p in st.session_state.temp_coords],
                    'area': area_s,
                    'agua': area_s * req_h,
                    'color': color_c
                }
                st.success(f"Sector de {tipo_cultivo} guardado con éxito.")
                st.rerun()
            else: st.warning("Por favor, dibuje el polígono del sector antes de guardar.")

        st.markdown("---")
        st.subheader("Sectores Registrados:")
        for k, v in st.session_state.cultivos_mapeados.items():
            st.write(f"• **{v['nombre']}**: {v['area']:,.0f} m²")
        
        if st.session_state.cultivos_mapeados:
            if st.button("✅ FINALIZAR MAPEADO E IR AL DASHBOARD", type="primary", use_container_width=True):
                st.session_state.cultivos_asignados = {v['nombre']: v['area'] for v in st.session_state.cultivos_mapeados.values()}
                st.session_state.agua_requerida_total = sum(v['agua'] for v in st.session_state.cultivos_mapeados.values())
                st.session_state.paso = 'dashboard'; st.rerun()

    with col_map:
        st.markdown("**Interactúe con el mapa para delimitar los sectores:**")
        m_plas = folium.Map(location=st.session_state.centro_mapa, zoom_start=16, tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", attr="Esri")
        
        if st.session_state.poligono_coords:
            folium.Polygon(locations=[[p[1], p[0]] for p in st.session_state.poligono_coords], color="white", weight=2, dash_array='5, 5', fill=False).add_to(m_plas)
        
        for k, v in st.session_state.cultivos_mapeados.items():
            folium.Polygon(locations=v['coords'], color=v['color'], fill=True, fill_opacity=0.6, tooltip=v['nombre']).add_to(m_plas)

        draw_plas = plugins.Draw(export=True, draw_options={'polyline':False, 'circle':False, 'marker':False, 'circlemarker':False}).add_to(m_plas)
        m_res = st_folium(m_plas, height=550, use_container_width=True, key="mapeador_plas")
        
        if m_res and m_res.get("all_drawings"):
            st.session_state.temp_coords = m_res["all_drawings"][-1]["geometry"]["coordinates"][0]

# ==========================================
# FASE 4: DASHBOARD PRINCIPAL
# ==========================================
elif st.session_state.paso == 'dashboard':
    st.title(f"📊 Dashboard | Admin: {st.session_state.usuario.get('nombre', '')}")
    
    pts_t = [[p[1], p[0]] for p in st.session_state.poligono_coords[:-1]]
    n_pts = len(pts_t); c = st.session_state.centro_mapa; t1, t2 = n_pts//3, 2*(n_pts//3)
    zonas_v = {"Toda la Parcela": pts_t, "Zona Óptima": [c]+pts_t[0:t1+1]+[c], "Zona Media": [c]+pts_t[t1:t2+1]+[c], "Zona Crítica": [c]+pts_t[t2:]+[pts_t[0], c]}

    with st.sidebar:
        st.header("🕒 Cronograma Operativo")
        st.markdown('<div class="horario-auto">💧 <b>05:30 AM</b> - Riego General</div>', unsafe_allow_html=True)
        st.markdown('<div class="horario-auto">🧪 <b>08:00 AM</b> - Aplicación Vitaminas</div>', unsafe_allow_html=True)
        st.markdown('<div class="horario-auto">🛡️ <b>06:00 PM</b> - Control Antiplagas</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🌱 Sensores", "🚁 Logística Dron", "📈 Reporte Maestro"])
    
    with tab1:
        temp_r, hum_r, vent_r = st.session_state.clima_real["temp"], st.session_state.clima_real["hum"], st.session_state.clima_real["viento"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Temperatura", f"{temp_r}°C", "Sensory"); c2.metric("Humedad", f"{hum_r}%", "IoT"); c3.metric("Viento", f"{vent_r} km/h", "Drone Safe"); c4.metric("Radiación", "Normal", "Óptimo")
        st.markdown("---")
        
        list_m = list(st.session_state.cultivos_mapeados.values())
        if len(list_m) > 0:
            num_cols = len(list_m) + 1 
            cols_s = st.columns(num_cols)
            for i, sector in enumerate(list_m):
                clase_css = "sensor-verde" if i % 2 == 0 else "sensor-amarillo"
                humedad_sim = "68%" if i % 2 == 0 else "45%"
                with cols_s[i]: st.markdown(f'<div class="{clase_css}"><b>{sector["nombre"]}</b><br>{sector["area"]:,.0f} m²<br>Humedad: {humedad_sim}</div>', unsafe_allow_html=True)
            with cols_s[-1]: st.markdown('<div class="sensor-rojo"><b>🚨 Riesgo Global</b><br>Humedad: 15%</div>', unsafe_allow_html=True)
        else:
            cols_s = st.columns(3)
            with cols_s[0]: st.markdown('<div class="sensor-verde"><b>Sector A: No asignado</b><br>0 m²</div>', unsafe_allow_html=True)
            with cols_s[1]: st.markdown('<div class="sensor-amarillo"><b>Sector B: No asignado</b><br>0 m²</div>', unsafe_allow_html=True)
            with cols_s[2]: st.markdown('<div class="sensor-rojo"><b>🚨 Riesgo Global</b><br>Humedad: 15%</div>', unsafe_allow_html=True)

    with tab2:
        st.header("Centro de Mando")
        col_c, col_m = st.columns([1, 2])
        
        with col_c:
            hora_actual = st.slider("Reloj (Simulador):", 0, 23, 14, format="%d:00 hrs")
            tipo_m = st.radio("Misión:", ["Riego de Emergencia", "Nutrición (Proteínas)", "Tratamiento (Anti-plagas)"])
            zona_o = st.selectbox("Objetivo:", list(zonas_v.keys()))
            
            patron_vuelo = st.selectbox("Patrón de Despliegue Táctico:", ["Zig-Zag (Cobertura Total)", "Perimetral (Bordes)"])
            
            es_riesgoso = (tipo_m == "Riego de Emergencia" and 10 <= hora_actual <= 18)
            boton_deshabilitado = es_riesgoso and not st.checkbox("Declaro entender los riesgos térmicos.")
            
            if st.button("🚀 DESPLEGAR DRON", type="primary", disabled=boton_deshabilitado, use_container_width=True):
                
                # 🚀 LÓGICA DE AHORRO HÍDRICO REAL (VRA ULV vs TRACTOR TRADICIONAL)
                agua_base = st.session_state.agua_requerida_total
                factor_zona = 1.0 if zona_o == "Toda la Parcela" else 0.333
                
                if tipo_m == "Riego de Emergencia":
                    litros_trad = agua_base * 1.15 * factor_zona # 100% + 15% escorrentía
                    litros_vr = agua_base * 0.12 * factor_zona   # Dron usa 12% para hidratación foliar
                elif tipo_m == "Nutrición (Proteínas)":
                    litros_trad = (agua_base * 0.20) * factor_zona 
                    litros_vr = (agua_base * 0.20) * 0.10 * factor_zona # Ahorro 90% mezcla foliar
                else: # Anti-plagas
                    litros_trad = (agua_base * 0.15) * factor_zona
                    litros_vr = (agua_base * 0.15) * 0.08 * factor_zona

                litros_trad = round(litros_trad, 1)
                litros_vr = round(litros_vr, 1)

                st.session_state.total_litros_tradicional += litros_trad
                st.session_state.total_litros_hoy += litros_vr
                
                st.session_state.color_dron_actual = "cyan" if tipo_m == "Riego de Emergencia" else ("orange" if tipo_m == "Nutrición (Proteínas)" else "red")
                st.session_state.ruta_dron_actual = calcular_ruta_patron(zonas_v[zona_o], patron_vuelo, c[0], c[1])
                
                st.session_state.mostrar_animacion_dron = True
                st.session_state.patron_animacion = patron_vuelo
                
                with st.spinner(f"🛰️ Conectando telemetría VRA. Trazando ruta hacia {zona_o}..."):
                    time.sleep(1.5)
                
                st.session_state.registro_diario.append({"Hora": f"{hora_actual}:00", "Misión": tipo_m, "Zona": zona_o, "Agua": f"{litros_vr} L"})
                st.rerun() 
                
        with col_m:
            if st.session_state.get('mostrar_animacion_dron', False):
                st.session_state.mostrar_animacion_dron = False 
                
                if "Zig-Zag" in st.session_state.patron_animacion:
                    kf_dron = """
                    0% { top: 5%; left: 5%; transform: scaleX(1); }
                    20% { top: 5%; left: 85%; transform: scaleX(1); }
                    21% { top: 35%; left: 85%; transform: scaleX(-1); }
                    40% { top: 35%; left: 5%; transform: scaleX(-1); }
                    41% { top: 65%; left: 5%; transform: scaleX(1); }
                    60% { top: 65%; left: 85%; transform: scaleX(1); }
                    61% { top: 90%; left: 85%; transform: scaleX(-1); }
                    80% { top: 90%; left: 5%; transform: scaleX(-1); }
                    100% { top: 50%; left: 45%; transform: scaleX(1); }
                    """
                else: 
                    kf_dron = """
                    0% { top: 5%; left: 5%; transform: rotate(0deg); }
                    25% { top: 5%; left: 85%; transform: rotate(90deg); }
                    50% { top: 85%; left: 85%; transform: rotate(180deg); }
                    75% { top: 85%; left: 5%; transform: rotate(270deg); }
                    100% { top: 5%; left: 5%; transform: rotate(360deg); }
                    """
                
                st.markdown(f"""
                <div style="position: relative; width: 100%; height: 0px; z-index: 999999;">
                    <div style="position: absolute; font-size: 45px; animation: droneTacticalFlight 10s linear forwards; pointer-events: none; filter: drop-shadow(2px 4px 4px rgba(0,0,0,0.5));">
                        🚁
                    </div>
                </div>
                <style>
                @keyframes droneTacticalFlight {{ {kf_dron} }}
                </style>
                """, unsafe_allow_html=True)
                
                st.success("✅ Misión VRA finalizada con éxito. Trayectoria guardada en bitácora.")
            
            map_d = folium.Map(location=c, zoom_start=16, tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", attr="Esri")
            
            for s in st.session_state.cultivos_mapeados.values():
                folium.Polygon(locations=s['coords'], color=s['color'], weight=1, fill=True, fill_opacity=0.2, tooltip=f"Cultivo: {s['nombre']}").add_to(map_d)
            
            if "Zona Óptima" in zonas_v and len(zonas_v["Zona Óptima"]) > 2:
                folium.Polygon(locations=zonas_v["Zona Óptima"], color="#28a745", weight=2, fill=True, fill_color="#28a745", fill_opacity=0.45, tooltip="Zona Óptima (>60% Humedad)").add_to(map_d)
                folium.Polygon(locations=zonas_v["Zona Media"], color="#ffc107", weight=2, fill=True, fill_color="#ffc107", fill_opacity=0.45, tooltip="Zona Media (40-60% Humedad)").add_to(map_d)
                folium.Polygon(locations=zonas_v["Zona Crítica"], color="#dc3545", weight=2, fill=True, fill_color="#dc3545", fill_opacity=0.55, tooltip="Zona Crítica (<30% Humedad)").add_to(map_d)

            if st.session_state.ruta_dron_actual: 
                plugins.AntPath(locations=st.session_state.ruta_dron_actual, color=st.session_state.color_dron_actual, weight=5, dash_array=[10, 20], delay=800, pulse_color='white').add_to(map_d)
            
            st_folium(map_d, height=450, use_container_width=True)

    with tab3:
        st.header("Reporte Ejecutivo Twilio")
        st.dataframe(pd.DataFrame(st.session_state.registro_diario), use_container_width=True)
        
        v_r = sum(1 for r in st.session_state.registro_diario if r["Misión"] == "Riego de Emergencia")
        v_n = sum(1 for r in st.session_state.registro_diario if r["Misión"] == "Nutrición (Proteínas)")
        v_p = sum(1 for r in st.session_state.registro_diario if r["Misión"] == "Tratamiento (Anti-plagas)")
        alerta_z = "Requiere Atención" if hum_r > 40 else "CRÍTICO - Alerta Hídrica"
        
        detalles_sectores = ""
        for v in st.session_state.cultivos_mapeados.values():
            detalles_sectores += f"  🌱 {v['nombre']}: {v['area']:,.0f} m² | 💧 Req Base: {v['agua']:,.1f} L\n"
        
        if not detalles_sectores: detalles_sectores = "  • Sin sectores mapeados\n"
        
        ahorro_litros = st.session_state.total_litros_tradicional - st.session_state.total_litros_hoy
        ahorro_porcentaje = (ahorro_litros / st.session_state.total_litros_tradicional * 100) if st.session_state.total_litros_tradicional > 0 else 0
            
        msg_profesional = f"""*📋 REPORTE EJECUTIVO - ENJAMBRE VRA* 🚁🌱
-----------------------------------
*👤 Gerente Agrícola:* {st.session_state.usuario.get('nombre', '')}
*📍 Área Total del Predio:* {st.session_state.parcela_area:,.0f} m²

*🗺️ SECTORES PRODUCTIVOS (PLAS)*
{detalles_sectores.strip()}

*☁️ CONDICIONES AGROCLIMÁTICAS*
🌡️ Temp: {temp_r}°C | 💧 Humedad: {hum_r}% | 💨 Viento: {vent_r} km/h

*📊 ESTADO HÍDRICO DEL SUELO*
🟢 Sectores Óptimos: Estable (>60%)
🟡 Sectores Medios: Estrés Leve (40-60%)
🔴 Zona Crítica: {alerta_z} (<30%)

*🚀 OPERACIONES REALIZADAS HOY*
🚁 Total Vuelos Desplegados: {len(st.session_state.registro_diario)}
  • 💧 Riegos de Emergencia: {v_r}
  • 💊 Nutrición (Proteínas): {v_n}
  • 🛡️ Tratamiento (Antiplagas): {v_p}

*💰 IMPACTO Y OPTIMIZACIÓN DE RECURSOS (VRA vs TRADICIONAL)*
🚜 Consumo Método Tradicional: {st.session_state.total_litros_tradicional:,.1f} Litros
🎯 Consumo Hídrico Dron VRA: {st.session_state.total_litros_hoy:,.1f} Litros
📉 Ahorro Hídrico Logrado: {ahorro_litros:,.1f} Litros ({ahorro_porcentaje:.1f}%)

_Generado automáticamente por Inteligencia Geoespacial PLAS._"""
        
        st.text_area("Mensaje Twilio:", value=msg_profesional, height=450, disabled=True)
        if st.button("🚀 ENVIAR REPORTE OFICIAL POR TWILIO", type="primary", use_container_width=True):
            exito, sid = enviar_whatsapp_twilio(msg_profesional, st.session_state.usuario.get('telefono', ''))
            if exito: st.success(f"Reporte enviado con éxito al celular registrado. SID: {sid}")
            else: st.error(f"Error de envío. Revisa credenciales: {sid}")
