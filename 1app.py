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
from folium.elements import MacroElement
from jinja2 import Template

# ==========================================
# 1. CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(page_title="Enjambre VRA | AI Digital Twin", page_icon="🚁", layout="wide")

def cargar_imagen_base64(ruta_imagen):
    try:
        with open(ruta_imagen, "rb") as archivo:
            return base64.b64encode(archivo.read()).decode()
    except FileNotFoundError:
        return None

# ==========================================
# 2. ESTILOS CSS Y HACKS VISUALES
# ==========================================
# Cursor de hormiga estático (URL-encoded seguro)
st.markdown("""
    <style>
    body, .stApp, [data-testid="stAppViewContainer"], * {
        cursor: url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='32' height='32'%3E%3Ctext y='24' font-size='24'%3E🐜%3C/text%3E%3C/svg%3E") 16 16, auto !important;
    }
    
    .sensor-verde { background-color: #d4edda; color: #155724; padding: 15px; border-radius: 8px; border-left: 5px solid #28a745; text-align: center; margin-bottom: 10px;}
    .sensor-amarillo { background-color: #fff3cd; color: #856404; padding: 15px; border-radius: 8px; border-left: 5px solid #ffc107; text-align: center; margin-bottom: 10px;}
    .sensor-rojo { background-color: #f8d7da; color: #721c24; padding: 15px; border-radius: 8px; border-left: 5px solid #dc3545; text-align: center; font-weight: bold; margin-bottom: 10px;}
    .horario-auto { background-color: #e2e3e5; color: #383d41; padding: 10px; border-radius: 5px; border-left: 5px solid #6c757d; margin-bottom: 5px;}
    .whatsapp-btn { background-color: #25D366; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block; text-align: center; width: 100%;}
    .whatsapp-btn:hover { background-color: #128C7E; color: white;}
    .ai-card { background: rgba(255, 255, 255, 0.05); padding: 20px; border-radius: 15px; border: 1px solid rgba(34, 197, 94, 0.3); backdrop-filter: blur(10px); margin-bottom: 15px;}
    [data-testid="stChatMessage"] { background: rgba(0, 20, 10, 0.85); border-radius: 10px; border: 1px solid rgba(34, 197, 94, 0.4); padding: 15px; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# Fondo agrícola animado
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
        radial-gradient(circle, rgba(134, 239, 172, 0.1) 2px, transparent 3px),
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

# Animación de Hojas
st.markdown("""
<div style="position:fixed; inset:0; pointer-events:none; z-index:1; overflow:hidden;">
    <div class="hoja" style="position:absolute; top:-10%; left:5%; animation: caerHojas 16s linear infinite;">🌿</div>
    <div class="hoja" style="position:absolute; top:-10%; left:25%; animation: caerHojas 18s linear infinite;">🍃</div>
    <div class="hoja" style="position:absolute; top:-10%; left:50%; animation: caerHojas 14s linear infinite;">🌱</div>
    <div class="hoja" style="position:absolute; top:-10%; left:75%; animation: caerHojas 20s linear infinite;">🌿</div>
</div>
<style>
@keyframes caerHojas { 
    0% { transform: translateY(-10vh) rotate(0deg); } 
    100% { transform: translateY(120vh) rotate(360deg); } 
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. BASE DE DATOS Y MEMORIA DEL SISTEMA
# ==========================================
DB_CULTIVOS_PLAS = {
    "Cerezas": {"agua_m2": 4.5, "color": "#d32f2f", "yield_base": 12.0, "price_ton": 2500},          
    "Uva Vinífera": {"agua_m2": 2.5, "color": "#7b1fa2", "yield_base": 15.0, "price_ton": 1800},     
    "Paltos": {"agua_m2": 6.0, "color": "#388e3c", "yield_base": 10.0, "price_ton": 3200},           
    "Nogales": {"agua_m2": 5.5, "color": "#795548", "yield_base": 8.0, "price_ton": 4500},          
    "Maíz": {"agua_m2": 4.0, "color": "#fbc02d", "yield_base": 18.0, "price_ton": 850},             
    "Trigo": {"agua_m2": 3.0, "color": "#ffa000", "yield_base": 7.0, "price_ton": 600},            
    "Arándanos": {"agua_m2": 3.5, "color": "#1976d2", "yield_base": 14.0, "price_ton": 5500},        
    "Cítricos": {"agua_m2": 4.0, "color": "#cddc39", "yield_base": 25.0, "price_ton": 1200},
    "Tomates": {"agua_m2": 5.0, "color": "#e64a19", "yield_base": 40.0, "price_ton": 950}           
}

# Inicialización segura de variables de estado
if 'paso' not in st.session_state: 
    st.session_state.paso = 'login'
if 'usuario' not in st.session_state: 
    st.session_state.usuario = {}
if 'parcela_area' not in st.session_state: 
    st.session_state.parcela_area = 0
if 'cultivos_mapeados' not in st.session_state: 
    st.session_state.cultivos_mapeados = {} 
if 'registro_diario' not in st.session_state: 
    st.session_state.registro_diario = []
if 'poligono_coords' not in st.session_state: 
    st.session_state.poligono_coords = None
if 'centro_mapa' not in st.session_state: 
    st.session_state.centro_mapa = [-33.456, -70.650]
if 'mapa_buscador_inicial' not in st.session_state: 
    st.session_state.mapa_buscador_inicial = [-33.456, -70.650]
if 'clima_real' not in st.session_state: 
    st.session_state.clima_real = {"temp": 0, "hum": 0, "viento": 0}
if 'total_litros_hoy' not in st.session_state: 
    st.session_state.total_litros_hoy = 0
if 'total_litros_tradicional' not in st.session_state: 
    st.session_state.total_litros_tradicional = 0
if 'ruta_dron_actual' not in st.session_state: 
    st.session_state.ruta_dron_actual = []
if 'color_dron_actual' not in st.session_state: 
    st.session_state.color_dron_actual = "cyan"
if 'mostrar_animacion_dron' not in st.session_state: 
    st.session_state.mostrar_animacion_dron = False
if 'patron_animacion' not in st.session_state: 
    st.session_state.patron_animacion = ""

# Memoria del Consultor IA
if 'chat_history' not in st.session_state: 
    st.session_state.chat_history = [
        {
            "role": "assistant", 
            "content": "👋 ¡Hola! Soy **Agri-Brain**, el núcleo analítico de Enjambre VRA. Conozco cada metro cuadrado de tu campo, el clima actual y la bitácora de vuelo de los drones.\n\n Puedes preguntarme cosas como:\n- *¿Cuánto espacio libre me queda?*\n- *¿Cuánto hemos ahorrado en agua?*\n- *¿Qué pasará con la temperatura mañana?*\n- *¿Cómo van mis ganancias (ROI)?*"
        }
    ]

# ==========================================
# 4. FUNCIONES Y CLASES CORE
# ==========================================
class MoveDrone(MacroElement):
    """Clase para inyectar un dron animado en el mapa Folium usando Leaflet.js"""
    def __init__(self, coords):
        super().__init__()
        self.coords = coords
        self._template = Template(u"""
        {% macro script(this, kwargs) %}
        var coords = {{ this.coords }};
        if(coords.length > 0){
            var droneIcon = L.divIcon({
                html: '<div style="font-size:35px; text-shadow: 2px 2px 4px rgba(0,0,0,0.5); margin-top:-20px; margin-left:-20px;">🚁</div>', 
                className: 'empty'
            });
            var droneMarker = L.marker(coords[0], {icon: droneIcon}).addTo({{this._parent.get_name()}});
            var i = 0;
            function animateDrone() {
                if (i < coords.length) {
                    droneMarker.setLatLng(coords[i]); 
                    i++;
                    setTimeout(animateDrone, 350);
                }
            }
            setTimeout(animateDrone, 500);
        }
        {% endmacro %}
        """)

def punto_en_poligono(x, y, poligono):
    """Algoritmo de Ray-Casting para determinar si un punto está dentro de un polígono"""
    n = len(poligono)
    inside = False
    p1x, p1y = poligono[0]
    for i in range(n + 1):
        p2x, p2y = poligono[i % n]
        if y > min(p1y, p2y) and y <= max(p1y, p2y) and x <= max(p1x, p2x):
            if p1y != p2y: 
                xints = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
            if p1x == p2x or x <= xints: 
                inside = not inside
        p1x, p1y = p2x, p2y
    return inside

def calcular_area_poligono(coords):
    """Calcula el área de un polígono esférico en metros cuadrados"""
    if not coords or len(coords) < 3: 
        return 0
    R = 6378137
    lats = [p[1] for p in coords]
    mean_lat = math.radians(sum(lats) / len(lats))
    pts_meters = [(R * math.radians(p[0]) * math.cos(mean_lat), R * math.radians(p[1])) for p in coords]
    
    area = 0
    n = len(pts_meters)
    for i in range(n):
        j = (i + 1) % n
        area += pts_meters[i][0] * pts_meters[j][1]
        area -= pts_meters[j][0] * pts_meters[i][1]
    return abs(area) / 2.0

def calcular_area_interseccion(poly_crop, poly_main):
    """Aproximación por grilla para calcular solo el área que está DENTRO del predio principal"""
    area_bruta = calcular_area_poligono(poly_crop)
    if area_bruta == 0: 
        return 0
        
    min_x = min(p[0] for p in poly_crop)
    max_x = max(p[0] for p in poly_crop)
    min_y = min(p[1] for p in poly_crop)
    max_y = max(p[1] for p in poly_crop)
    
    p_crop = 0
    p_ambos = 0
    grid = 80
    dx = (max_x - min_x) / grid
    dy = (max_y - min_y) / grid
    
    if dx == 0 or dy == 0: 
        return area_bruta
        
    for i in range(grid):
        for j in range(grid):
            x = min_x + i * dx
            y = min_y + j * dy
            if punto_en_poligono(x, y, poly_crop):
                p_crop += 1
                if punto_en_poligono(x, y, poly_main): 
                    p_ambos += 1
                    
    if p_crop > 0:
        return area_bruta * (p_ambos / p_crop)
    else:
        return 0

def enviar_whatsapp_twilio(mensaje, telefono_destino):
    """Envía un mensaje de WhatsApp a través de la API de Twilio"""
    try:
        required_secrets = ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE"]
        for s in required_secrets:
            if s not in st.secrets:
                return False, f"Falta el secret: {s}"
                
        client = Client(st.secrets["TWILIO_ACCOUNT_SID"], st.secrets["TWILIO_AUTH_TOKEN"])
        message = client.messages.create(
            body=mensaje, 
            from_=st.secrets["TWILIO_PHONE"], 
            to=f"whatsapp:+{telefono_destino}"
        )
        return True, message.sid
    except Exception as e: 
        return False, str(e)

def buscar_ubicacion(direccion):
    """Busca las coordenadas de una ciudad o dirección usando OpenStreetMap"""
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(direccion)}&format=json&limit=1"
        res = requests.get(url, headers={'User-Agent': 'EnjambreVRADemo/1.0'}).json()
        if res: 
            return [float(res[0]['lat']), float(res[0]['lon'])]
    except: 
        pass
    return None

def obtener_clima_real(lat, lon):
    """Obtiene datos meteorológicos en tiempo real de Open-Meteo"""
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=relative_humidity_2m"
        res = requests.get(url).json()
        return {
            "temp": res["current_weather"]["temperature"], 
            "hum": res["hourly"]["relative_humidity_2m"][0], 
            "viento": res["current_weather"]["windspeed"]
        }
    except: 
        return {"temp": 13.8, "hum": 73, "viento": 1.7}

def calcular_ruta_patron(coords_zona, patron, lat_base, lon_base):
    """Calcula la ruta matemática que debe seguir el dron"""
    if not coords_zona: 
        return []
        
    c_lat = sum(p[0] for p in coords_zona) / len(coords_zona)
    c_lon = sum(p[1] for p in coords_zona) / len(coords_zona)
    ruta = [[lat_base, lon_base], [c_lat, c_lon]]
    
    if patron == "Perimetral (Bordes)":
        ruta.extend(coords_zona)
        ruta.append(coords_zona[0])
    elif patron == "Zig-Zag (Cobertura Total)":
        lats = [p[0] for p in coords_zona]
        max_lat = max(lats)
        min_lat = min(lats)
        paso_lat = (max_lat - min_lat) / 6 
        poly = coords_zona + [coords_zona[0]]
        
        for i in range(1, 6):
            lat_act = max_lat - (i * paso_lat)
            intersecciones = []
            for j in range(len(poly)-1):
                p1 = poly[j]
                p2 = poly[j+1]
                if (p1[0] <= lat_act < p2[0]) or (p2[0] <= lat_act < p1[0]):
                    if p2[0] != p1[0]: 
                        x_int = p1[1] + (lat_act - p1[0]) * (p2[1] - p1[1]) / (p2[0] - p1[0])
                        intersecciones.append(x_int)
            intersecciones.sort()
            
            if len(intersecciones) >= 2:
                if i % 2 == 0: 
                    ruta.extend([[lat_act, intersecciones[0]], [lat_act, intersecciones[-1]]])
                else: 
                    ruta.extend([[lat_act, intersecciones[-1]], [lat_act, intersecciones[0]]])
                    
    ruta.append([lat_base, lon_base])
    return ruta


# ==========================================
# 5. LÓGICA DE INTERFAZ Y PESTAÑAS (FASES)
# ==========================================

# ------------------------------------------
# FASE 1: REGISTRO
# ------------------------------------------
if st.session_state.paso == 'login':
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🌱 Enjambre VRA")
        st.subheader("Acceso Administrativo Real-Time")
        with st.form("registro_form"):
            nombre = st.text_input("Nombre Completo")
            telefono = st.text_input("WhatsApp (Ej: 56912345678)")
            submit = st.form_submit_button("Ingresar al Sistema", type="primary", use_container_width=True)
            
            if submit and nombre and telefono:
                tel_limpio = ''.join(filter(str.isdigit, telefono))
                st.session_state.usuario = {'nombre': nombre, 'telefono': tel_limpio}
                st.session_state.paso = 'onboarding_mapa'
                st.rerun()

# ------------------------------------------
# FASE 2: DELIMITACIÓN TOTAL
# ------------------------------------------
elif st.session_state.paso == 'onboarding_mapa':
    st.header(f"Bienvenido {st.session_state.usuario.get('nombre', '')} - Perímetro Predial")
    
    tab_dir, tab_coord = st.tabs(["📍 Por Dirección", "🧭 Por Coordenadas"])
    
    with tab_dir:
        c_s, c_b = st.columns([3, 1])
        with c_s: 
            dir_b = st.text_input("Ingrese ubicación (Ej: Quillota, Chile):")
        with c_b: 
            st.write("") 
            if st.button("Buscar Dirección", use_container_width=True): 
                coords = buscar_ubicacion(dir_b)
                if coords: 
                    st.session_state.mapa_buscador_inicial = coords
                    st.rerun()
                else:
                    st.error("No se encontró la dirección.")
                    
    with tab_coord:
        c_lat, c_lon, c_btn = st.columns([2, 2, 1])
        with c_lat: 
            lat_b = st.number_input("Latitud:", value=st.session_state.mapa_buscador_inicial[0], format="%.5f")
        with c_lon: 
            lon_b = st.number_input("Longitud:", value=st.session_state.mapa_buscador_inicial[1], format="%.5f")
        with c_btn: 
            st.write("") 
            if st.button("Ir a Coordenadas", use_container_width=True): 
                st.session_state.mapa_buscador_inicial = [lat_b, lon_b]
                st.rerun()

    st.write("📍 **Dibuje el perímetro total de su campo usando las herramientas (Polígono/Rectángulo):**")
    
    m_dibujo = folium.Map(location=st.session_state.mapa_buscador_inicial, zoom_start=15, tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", attr="Esri")
    opciones_dibujo = {'polyline': False, 'circle': False, 'marker': False, 'circlemarker': False}
    draw = plugins.Draw(export=True, draw_options=opciones_dibujo)
    draw.add_to(m_dibujo)
    
    m_data = st_folium(m_dibujo, height=450, use_container_width=True, key="dibujo_total")
    
    if m_data and m_data.get("all_drawings"):
        st.session_state.poligono_coords = m_data["all_drawings"][0]["geometry"]["coordinates"][0]
        area_calc = calcular_area_poligono(st.session_state.poligono_coords)
        
        st.success(f"✅ Perímetro detectado exitosamente: **{area_calc:,.1f} m²**")
        
        if st.button("Confirmar Perímetro Predial ➡️", type="primary"):
            st.session_state.parcela_area = int(area_calc)
            
            # Formateamos los puntos y sacamos el centro
            pts = [[p[1], p[0]] for p in st.session_state.poligono_coords[:-1]]
            c_lat = sum(p[0] for p in pts) / len(pts)
            c_lon = sum(p[1] for p in pts) / len(pts)
            st.session_state.centro_mapa = [c_lat, c_lon]
            
            # Obtenemos clima inicial
            st.session_state.clima_real = obtener_clima_real(c_lat, c_lon)
            st.session_state.paso = 'onboarding_cultivos'
            st.rerun()

# ------------------------------------------
# FASE 3: MAPEADOR INTERACTIVO PLAS
# ------------------------------------------
elif st.session_state.paso == 'onboarding_cultivos':
    st.header("🌾 Fase PLAS: Mapeo de Sectores Productivos")
    st.write(f"Área Predial Disponible: **{st.session_state.parcela_area:,.0f} m²**")
    
    col_ctrl, col_map = st.columns([1, 2])
    
    with col_ctrl:
        st.subheader("1. Seleccionar Tipo de Planta")
        tipo_cultivo = st.selectbox("Base de Datos PLAS (Chile):", list(DB_CULTIVOS_PLAS.keys()))
        req_h = DB_CULTIVOS_PLAS[tipo_cultivo]['agua_m2']
        color_c = DB_CULTIVOS_PLAS[tipo_cultivo]['color']
        
        st.info(f"Requerimiento Hídrico PLAS: **{req_h} Litros / m²**")
        st.write("2. Dibuje el sector correspondiente a este cultivo en el mapa.")
        
        if st.button("💾 GUARDAR SECTOR MAPEADO", use_container_width=True):
            if 'temp_coords' in st.session_state and st.session_state.temp_coords:
                area_real_adentro = calcular_area_interseccion(st.session_state.temp_coords, st.session_state.poligono_coords)
                
                if area_real_adentro > 0:
                    id_sector = f"{tipo_cultivo}_{time.time()}"
                    st.session_state.cultivos_mapeados[id_sector] = {
                        'nombre': tipo_cultivo,
                        'coords': [[p[1], p[0]] for p in st.session_state.temp_coords],
                        'area': area_real_adentro,
                        'agua': area_real_adentro * req_h,
                        'color': color_c
                    }
                    
                    area_dibujada = calcular_area_poligono(st.session_state.temp_coords)
                    if area_real_adentro < (area_dibujada * 0.98):
                        st.warning(f"⚠️ Nota de Corrección: Parte del dibujo estaba fuera del límite. Se ajustó y validó a {area_real_adentro:,.0f} m² internos.")
                    else:
                        st.success(f"✅ Sector de {tipo_cultivo} guardado exitosamente ({area_real_adentro:,.0f} m²).")
                    st.rerun()
                else: 
                    st.error("❌ ERROR: El polígono está completamente fuera del predio. Dibújalo adentro.")
            else: 
                st.warning("⚠️ Por favor, dibuje el polígono del sector en el mapa antes de guardar.")

        st.markdown("---")
        st.subheader("Sectores Registrados:")
        for k, v in st.session_state.cultivos_mapeados.items():
            st.write(f"• **{v['nombre']}**: {v['area']:,.0f} m²")
        
        if st.session_state.cultivos_mapeados:
            if st.button("✅ FINALIZAR MAPEADO E IR AL DASHBOARD", type="primary", use_container_width=True):
                st.session_state.paso = 'dashboard'
                st.rerun()

    with col_map:
        st.markdown("**Interactúe con el mapa para delimitar sus cultivos:**")
        m_plas = folium.Map(location=st.session_state.centro_mapa, zoom_start=16, tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", attr="Esri")
        
        # Perímetro principal (guía)
        if st.session_state.poligono_coords:
            pts_main = [[p[1], p[0]] for p in st.session_state.poligono_coords]
            folium.Polygon(locations=pts_main, color="white", weight=2, dash_array='5, 5', fill=False).add_to(m_plas)
        
        # Sectores ya guardados
        for k, v in st.session_state.cultivos_mapeados.items():
            folium.Polygon(locations=v['coords'], color=v['color'], fill=True, fill_opacity=0.6, tooltip=v['nombre']).add_to(m_plas)

        opciones_dibujo = {'polyline': False, 'circle': False, 'marker': False, 'circlemarker': False}
        plugins.Draw(export=True, draw_options=opciones_dibujo).add_to(m_plas)
        
        m_res = st_folium(m_plas, height=550, use_container_width=True, key="mapeador_plas")
        
        # Guardar coordenadas temporales al dibujar
        if m_res and m_res.get("all_drawings"):
            st.session_state.temp_coords = m_res["all_drawings"][-1]["geometry"]["coordinates"][0]

# ------------------------------------------
# FASE 4: DASHBOARD PRINCIPAL
# ------------------------------------------
elif st.session_state.paso == 'dashboard':
    
    # Declaración de variables globales ordenadas para todo el Dashboard
    area_t = st.session_state.parcela_area
    area_u = sum(v['area'] for v in st.session_state.cultivos_mapeados.values())
    area_l = max(0, area_t - area_u)
    
    clima = st.session_state.clima_real
    tr = clima["temp"]
    hr = clima["hum"]
    vr = clima["viento"]
    
    st.title(f"📊 Dashboard Enjambre VRA | Admin: {st.session_state.usuario.get('nombre', '')}")
    
    # Cálculo geométrico de Zonas de Riesgo Matemáticas (Tercio superior, medio, inferior)
    pts_t = [[p[1], p[0]] for p in st.session_state.poligono_coords[:-1]]
    n_pts = len(pts_t)
    c = st.session_state.centro_mapa
    t1 = n_pts // 3
    t2 = 2 * (n_pts // 3)
    
    zonas_v = {
        "Toda la Parcela": pts_t, 
        "Zona Óptima": [c] + pts_t[0:t1+1] + [c], 
        "Zona Media": [c] + pts_t[t1:t2+1] + [c], 
        "Zona Crítica": [c] + pts_t[t2:] + [pts_t[0], c]
    }

    # Barra lateral
    with st.sidebar:
        st.header("🕒 Cronograma Operativo")
        st.markdown('<div class="horario-auto">💧 <b>05:30 AM</b> - Riego General</div>', unsafe_allow_html=True)
        st.markdown('<div class="horario-auto">🧪 <b>08:00 AM</b> - Aplicación Vitaminas</div>', unsafe_allow_html=True)
        st.markdown('<div class="horario-auto">🛡️ <b>06:00 PM</b> - Control Antiplagas</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.header("📊 Balance de Superficie")
        st.write(f"**📍 Área Total:** {area_t:,.0f} m²")
        st.write(f"**✅ Área Usada:** {area_u:,.0f} m²")
        
        for k, v in st.session_state.cultivos_mapeados.items():
            st.markdown(f"<div style='padding-left: 20px; font-size: 14px;'>🌱 {v['nombre']}: {v['area']:,.0f} m²</div>", unsafe_allow_html=True)
            
        st.write(f"**⬜ Área Libre:** {area_l:,.0f} m²")
        
        progreso = min(area_u / area_t, 1.0) if area_t > 0 else 0.0
        st.progress(progreso)

    # Pestañas Principales
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🌱 Sensores", "🚁 Logística Dron", "📈 Reporte Maestro", "📉 Gemelo Digital (IA)", "🤖 Consultor IA"])
    
    # ------------------------------------------
    # PESTAÑA 1: SENSORES
    # ------------------------------------------
    with tab1:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Temperatura", f"{tr}°C")
        c2.metric("Humedad", f"{hr}%")
        c3.metric("Viento", f"{vr} km/h")
        c4.metric("Radiación", "Normal")
        st.markdown("---")
        
        list_m = list(st.session_state.cultivos_mapeados.values())
        if len(list_m) > 0:
            cols_s = st.columns(len(list_m))
            for i, sector in enumerate(list_m):
                # Intercalar estilos CSS para diferenciar visualmente los sensores
                clase_css = "sensor-verde" if i % 2 == 0 else "sensor-amarillo"
                humedad_sim = "68%" if i % 2 == 0 else "45%"
                with cols_s[i]: 
                    st.markdown(f'<div class="{clase_css}"><b>{sector["nombre"]}</b><br>{sector["area"]:,.0f} m²<br>Humedad: {humedad_sim}</div>', unsafe_allow_html=True)
        else:
            st.info("ℹ️ No hay sectores mapeados. Regresa a la fase anterior para configurar tus cultivos.")

    # ------------------------------------------
    # PESTAÑA 2: CENTRO DE MANDO (DRON)
    # ------------------------------------------
    with tab2:
        st.header("Centro de Mando Logístico VRA")
        col_c, col_m = st.columns([1, 2])
        
        with col_c:
            hora_actual = st.slider("Reloj (Simulador):", 0, 23, 14, format="%d:00 hrs")
            tipo_m = st.radio("Misión a Desplegar:", ["Riego de Emergencia", "Nutrición (Proteínas)", "Tratamiento (Anti-plagas)"])
            zona_o = st.selectbox("Objetivo Estratégico:", list(zonas_v.keys()))
            patron_vuelo = st.selectbox("Patrón de Vuelo:", ["Zig-Zag (Cobertura Total)", "Perimetral (Bordes)"])
            
            es_riesgoso = (tipo_m == "Riego de Emergencia" and 10 <= hora_actual <= 18)
            boton_deshabilitado = es_riesgoso and not st.checkbox("Declaro entender los riesgos térmicos de regar a esta hora.")
            
            if st.button("🚀 DESPLEGAR DRON", type="primary", disabled=boton_deshabilitado, use_container_width=True):
                agua_base = sum(v['agua'] for v in st.session_state.cultivos_mapeados.values()) if st.session_state.cultivos_mapeados else 0
                factor_zona = 1.0 if zona_o == "Toda la Parcela" else 0.333
                
                # Lógica de física de fluidos y ahorro
                if tipo_m == "Riego de Emergencia":
                    litros_trad = agua_base * 1.15 * factor_zona 
                    litros_vr = agua_base * 0.12 * factor_zona   
                elif tipo_m == "Nutrición (Proteínas)":
                    litros_trad = (agua_base * 0.20) * factor_zona 
                    litros_vr = (agua_base * 0.20) * 0.10 * factor_zona 
                else: 
                    litros_trad = (agua_base * 0.15) * factor_zona
                    litros_vr = (agua_base * 0.15) * 0.08 * factor_zona

                st.session_state.total_litros_tradicional += round(litros_trad, 1)
                st.session_state.total_litros_hoy += round(litros_vr, 1)
                
                st.session_state.color_dron_actual = "cyan" if tipo_m == "Riego de Emergencia" else ("orange" if tipo_m == "Nutrición (Proteínas)" else "red")
                st.session_state.ruta_dron_actual = calcular_ruta_patron(zonas_v[zona_o], patron_vuelo, c[0], c[1])
                
                st.session_state.mostrar_animacion_dron = True
                st.session_state.patron_animacion = patron_vuelo
                
                with st.spinner(f"🛰️ Conectando telemetría VRA. Trazando ruta hacia {zona_o}..."):
                    time.sleep(1.5)
                
                st.session_state.registro_diario.append({"Hora": f"{hora_actual}:00", "Misión": tipo_m, "Zona": zona_o, "Agua": f"{round(litros_vr, 1)} L"})
                st.rerun() 
                
        with col_m:
            map_d = folium.Map(location=c, zoom_start=16, tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", attr="Esri")
            
            # Capa 1: Cultivos mapeados (Fondo)
            for s in st.session_state.cultivos_mapeados.values():
                folium.Polygon(locations=s['coords'], color=s['color'], weight=1, fill=True, fill_opacity=0.2, tooltip=f"Cultivo: {s['nombre']}").add_to(map_d)
            
            # Capa 2: Triángulos de Riesgo (Superficie)
            if "Zona Óptima" in zonas_v and len(zonas_v["Zona Óptima"]) > 2:
                folium.Polygon(locations=zonas_v["Zona Óptima"], color="#28a745", weight=2, fill=True, fill_color="#28a745", fill_opacity=0.45, tooltip="Zona Óptima (>60% Humedad)").add_to(map_d)
                folium.Polygon(locations=zonas_v["Zona Media"], color="#ffc107", weight=2, fill=True, fill_color="#ffc107", fill_opacity=0.45, tooltip="Zona Media (40-60% Humedad)").add_to(map_d)
                folium.Polygon(locations=zonas_v["Zona Crítica"], color="#dc3545", weight=2, fill=True, fill_color="#dc3545", fill_opacity=0.55, tooltip="Zona Crítica (<30% Humedad)").add_to(map_d)

            # Capa 3: Ruta del Dron y Animación
            if st.session_state.ruta_dron_actual: 
                plugins.AntPath(locations=st.session_state.ruta_dron_actual, color=st.session_state.color_dron_actual, weight=5, dash_array=[10, 20], delay=800, pulse_color='white').add_to(map_d)
                
                if st.session_state.get('mostrar_animacion_dron', False):
                    map_d.get_root().add_child(MoveDrone(st.session_state.ruta_dron_actual))
                    st.session_state.mostrar_animacion_dron = False
            
            st_folium(map_d, height=450, use_container_width=True)

    # ------------------------------------------
    # PESTAÑA 3: REPORTE TWILIO Y ROI
    # ------------------------------------------
    with tab3:
        st.header("Reporte Ejecutivo Operacional")
        st.dataframe(pd.DataFrame(st.session_state.registro_diario), use_container_width=True)
        
        v_r = sum(1 for r in st.session_state.registro_diario if r["Misión"] == "Riego de Emergencia")
        v_n = sum(1 for r in st.session_state.registro_diario if r["Misión"] == "Nutrición (Proteínas)")
        v_p = sum(1 for r in st.session_state.registro_diario if r["Misión"] == "Tratamiento (Anti-plagas)")
        
        alerta_z = "Requiere Atención" if hr > 40 else "CRÍTICO - Alerta Hídrica"
        
        detalles_sectores = ""
        for v in st.session_state.cultivos_mapeados.values():
            detalles_sectores += f"  🌱 {v['nombre']}: {v['area']:,.0f} m² | 💧 Req Base: {v['agua']:,.1f} L\n"
        
        if not detalles_sectores: 
            detalles_sectores = "  • Sin sectores mapeados\n"
        
        ahorro_litros = st.session_state.total_litros_tradicional - st.session_state.total_litros_hoy
        ahorro_porcentaje = (ahorro_litros / st.session_state.total_litros_tradicional * 100) if st.session_state.total_litros_tradicional > 0 else 0
            
        msg_profesional = f"""*📋 REPORTE EJECUTIVO - ENJAMBRE VRA* 🚁🌱
-----------------------------------
*👤 Gerente Agrícola:* {st.session_state.usuario.get('nombre', '')}
*📍 Área Total del Predio:* {area_t:,.0f} m²

*🗺️ SECTORES PRODUCTIVOS (PLAS)*
{detalles_sectores.strip()}

*☁️ CONDICIONES AGROCLIMÁTICAS*
🌡️ Temp: {tr}°C | 💧 Humedad: {hr}% | 💨 Viento: {vr} km/h

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
        
        st.text_area("Mensaje Twilio Pre-visualización:", value=msg_profesional, height=450, disabled=True)
        
        if st.button("🚀 ENVIAR REPORTE OFICIAL POR TWILIO", type="primary", use_container_width=True):
            exito, sid = enviar_whatsapp_twilio(msg_profesional, st.session_state.usuario.get('telefono', ''))
            if exito: 
                st.success(f"Reporte enviado con éxito al celular registrado. SID: {sid}")
            else: 
                st.error(f"Error de envío. Revisa tus credenciales de Twilio: {sid}")

    # ------------------------------------------
    # PESTAÑA 4: GEMELO DIGITAL (IA)
    # ------------------------------------------
    with tab4:
        st.header("📉 Gemelo Digital: Proyección de Cosecha (IA)")
        st.markdown('<div class="ai-card"><h3>Simulador de Rendimiento Predictivo</h3>Ajuste el presupuesto hídrico para ver cómo la IA de Enjambre VRA predice su producción y rentabilidad final.</div>', unsafe_allow_html=True)
        
        inversion = st.select_slider("Factor de Optimización de Vuelo VRA:", options=["Mínimo", "Tradicional", "Optimizado VRA", "Máximo Rendimiento"], value="Optimizado VRA")
        eficiencia = {"Mínimo": 0.4, "Tradicional": 0.75, "Optimizado VRA": 1.0, "Máximo Rendimiento": 0.95}[inversion]
        
        datos_sim = []
        for v in st.session_state.cultivos_mapeados.values():
            db = DB_CULTIVOS_PLAS.get(v['nombre'], {"yield_base": 10, "price_ton": 1000})
            ton_esperadas = (v['area'] / 10000) * db['yield_base'] * eficiencia
            ganancia = ton_esperadas * db['price_ton']
            
            datos_sim.append({
                "Cultivo": v['nombre'], 
                "Área (m²)": f"{v['area']:,.0f}", 
                "Cosecha (Ton)": f"{ton_esperadas:,.1f}", 
                "Ingresos Est. ($)": f"${ganancia:,.0f}"
            })
            
        if datos_sim:
            # Recrear un dataframe limpio para el gráfico de barras sin strings formateados
            df_crudo = pd.DataFrame([{ "Cultivo": d["Cultivo"], "Cosecha (Ton)": float(d["Cosecha (Ton)"].replace(',', '')) } for d in datos_sim])
            
            c1, c2 = st.columns(2)
            with c1: 
                st.subheader("Predicción de Producción")
                st.bar_chart(df_crudo.set_index("Cultivo")["Cosecha (Ton)"])
            with c2: 
                st.subheader("Proyección Económica (ROI)")
                st.dataframe(pd.DataFrame(datos_sim), use_container_width=True, hide_index=True)
                
            st.success(f"💡 Sugerencia IA: Mantener el escenario '{inversion}' para maximizar el ROI foliar sin causar estrés hídrico en las plantas.")
        else: 
            st.warning("Debe mapear sectores productivos en la Fase 3 para poder generar el Gemelo Digital.")

    # ------------------------------------------
    # PESTAÑA 5: CONSULTOR IA
    # ------------------------------------------
    with tab5:
        st.header("🤖 Consultor Agrotecnológico (IA)")
        st.markdown('<div class="ai-card">Haga consultas directas sobre su predio en lenguaje natural. Agri-Brain analiza la telemetría, el clima y sus datos financieros en tiempo real.</div>', unsafe_allow_html=True)
        
        contenedor_chat = st.container(height=450)
        
        with contenedor_chat:
            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
                
        prompt = st.chat_input("Consulta a la IA (ej: 'cuanto espacio libre me queda', 'cuánto ahorré de agua', 'dame un reporte general')...")
        
        if prompt:
            # 1. Registrar mensaje del usuario
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            prompt_lower = prompt.lower()
            respuesta_ia = ""
            
            # 2. MOTOR NLP DE EVALUACIÓN
            if any(palabra in prompt_lower for palabra in ["espacio", "area", "área", "terreno", "tamaño", "metros", "m2", "utilizado", "libre", "cuanto uso", "cuánto uso"]):
                porc_uso = (area_u / area_t * 100) if area_t > 0 else 0
                respuesta_ia = f"🗺️ **Análisis de Superficie Georreferenciada:**\n\n- **Área Total del Predio:** {area_t:,.0f} m².\n- **Área Cultivada (Usada):** {area_u:,.0f} m².\n- **Área Disponible (Libre):** {area_l:,.0f} m².\n\nActualmente tienes {len(st.session_state.cultivos_mapeados)} sectores productivos registrados. Tienes un **{porc_uso:.1f}%** de tu terreno optimizado y mapeado en PLAS."

            elif any(palabra in prompt_lower for palabra in ["clima", "tiempo", "temperatura", "mañana", "pronostico", "pronóstico", "viento", "calor", "frio"]):
                if "mañana" in prompt_lower or "futuro" in prompt_lower:
                    temp_manana = tr + 2.5
                    respuesta_ia = f"☁️ **Pronóstico (Simulado para Mañana):**\nBasado en los modelos de telemetría, se espera que la temperatura ascienda a los **{temp_manana:.1f}°C**, con vientos estables de {vr} km/h. \n\n💡 *Sugerencia VRA:* Planifica riegos temprano por la mañana para evitar pérdida por evaporación."
                else:
                    respuesta_ia = f"☁️ **Condiciones Actuales en Terreno:**\n- Temperatura: **{tr}°C**\n- Viento: **{vr} km/h**\n- Humedad Ambiental: **{hr}%**\n\nCon estos parámetros actuales, nos encontramos en una ventana operativa segura para vuelos VRA."

            elif any(palabra in prompt_lower for palabra in ["cultivo", "plantas", "sembrado", "que tengo", "sectores"]):
                if st.session_state.cultivos_mapeados:
                    det = "\n".join([f"- 🌱 **{v['nombre']}**: {v['area']:,.0f} m²" for v in st.session_state.cultivos_mapeados.values()])
                    respuesta_ia = f"🌾 **Tus Cultivos Actuales Mapeados:**\n{det}\n\nRevisa la pestaña 'Logística Dron' para visualizar la ubicación geográfica y el nivel de estrés de cada uno."
                else:
                    respuesta_ia = "Aún no has mapeado ningún cultivo. Regresa a la Fase 3 (PLAS) para dibujar tus sectores productivos."

            elif any(palabra in prompt_lower for palabra in ["agua", "ahorro", "litros", "riego", "gasto", "consumo"]):
                ahorro_neto = st.session_state.total_litros_tradicional - st.session_state.total_litros_hoy
                if st.session_state.total_litros_tradicional > 0:
                    porc = (ahorro_neto / st.session_state.total_litros_tradicional * 100)
                    respuesta_ia = f"💧 **Reporte de Ahorro Hídrico:**\nHasta el momento, el dron VRA ha inyectado estratégicamente **{st.session_state.total_litros_hoy:,.1f} Litros**.\n\nCon un tractor tradicional, el gasto estimado habría sido de {st.session_state.total_litros_tradicional:,.1f} Litros.\n\n✅ **Has ahorrado:** {ahorro_neto:,.1f} Litros (**{porc:.1f}% de optimización**)."
                else:
                    respuesta_ia = "💧 Aún no has despachado el dron en la plataforma. Dirígete a la pestaña 'Centro de Mando' y realiza un despliegue para comenzar a calcular tu ahorro hídrico."

            elif any(palabra in prompt_lower for palabra in ["cosecha", "plata", "ganancia", "roi", "dinero", "produccion", "producción"]):
                cultivos_lista = ", ".join([v['nombre'] for v in st.session_state.cultivos_mapeados.values()]) if st.session_state.cultivos_mapeados else "Ninguno"
                respuesta_ia = f"📈 **Proyección Económica:**\nAl trabajar con los {area_t:,.0f} m² de tu predio, enfocado en tus siembras de *{cultivos_lista}*, el modelo de Inteligencia Artificial proyecta un alza significativa en el calibre final de tu cosecha si mantienes el régimen VRA. Te recomiendo visualizar los montos exactos en Dólares ($) en la pestaña 'Gemelo Digital'."

            elif any(palabra in prompt_lower for palabra in ["resumen", "estado", "general", "como vamos", "cómo vamos", "informe"]):
                ahorro_neto = st.session_state.total_litros_tradicional - st.session_state.total_litros_hoy
                respuesta_ia = f"📊 **Resumen Ejecutivo Inmediato:**\n- **Área Total Evaluada:** {area_t:,.0f} m².\n- **Superficie Productiva:** {area_u:,.0f} m².\n- **Clima de Operaciones:** {tr}°C.\n- **Vuelos VRA:** {len(st.session_state.registro_diario)} misiones logradas.\n- **Agua Ahorrada al Planeta:** {ahorro_neto:,.1f} Litros.\n\n🚀 La granja inteligente funciona a la perfección."

            else:
                respuesta_ia = "🤖 **Agri-Brain:** No pude detectar tu intención. Intenta preguntarme directamente sobre:\n- 🗺️ Mi espacio o área.\n- 💧 El ahorro de agua o riego.\n- ☁️ El clima de hoy o mañana.\n- 🌾 Mis cultivos registrados.\n- 📈 El estado financiero o resumen general."
            
            # 3. Guardar y refrescar
            st.session_state.chat_history.append({"role": "assistant", "content": respuesta_ia})
            st.rerun()
