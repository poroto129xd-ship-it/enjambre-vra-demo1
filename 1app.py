import streamlit as st
import folium
from folium import plugins
from streamlit_folium import st_folium
import time
import pandas as pd
from datetime import date

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Enjambre VRA | Plataforma Integral", page_icon="🚁", layout="wide")

st.markdown("""
    <style>
    .sensor-verde { background-color: #d4edda; color: #155724; padding: 15px; border-radius: 8px; border-left: 5px solid #28a745; text-align: center; }
    .sensor-amarillo { background-color: #fff3cd; color: #856404; padding: 15px; border-radius: 8px; border-left: 5px solid #ffc107; text-align: center; }
    .sensor-rojo { background-color: #f8d7da; color: #721c24; padding: 15px; border-radius: 8px; border-left: 5px solid #dc3545; text-align: center; font-weight: bold;}
    .whatsapp-msg { background-color: #e5ddd5; padding: 15px; border-radius: 10px; font-family: monospace; border: 1px solid #d1d1d1; }
    </style>
""", unsafe_allow_html=True)

# Variables de Memoria
if 'paso' not in st.session_state: st.session_state.paso = 'login'
if 'usuario' not in st.session_state: st.session_state.usuario = {}
if 'parcela_area' not in st.session_state: st.session_state.parcela_area = 0
if 'cultivos_asignados' not in st.session_state: st.session_state.cultivos_asignados = {}
if 'registro_diario' not in st.session_state: st.session_state.registro_diario = []

DB_CULTIVOS = ["Cerezas", "Uva Vinífera", "Paltos", "Nogales", "Maíz", "Trigo", "Arándanos"]

# ==========================================
# FASE 1: REGISTRO DE USUARIO
# ==========================================
if st.session_state.paso == 'login':
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🌱 Enjambre VRA")
        st.subheader("Cree su cuenta de administrador")
        with st.form("registro_form"):
            nombre = st.text_input("Nombre Completo")
            email = st.text_input("Correo Electrónico (Cualquier proveedor)")
            telefono = st.text_input("Número de Teléfono (WhatsApp)")
            password = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Crear Cuenta e Ingresar", type="primary", use_container_width=True)
            
            if submit and nombre and email and telefono:
                st.session_state.usuario = {'nombre': nombre, 'email': email, 'telefono': telefono}
                st.session_state.paso = 'onboarding_mapa'
                st.rerun()

# ==========================================
# FASE 2: DIBUJO DE PARCELA Y ÁREA
# ==========================================
elif st.session_state.paso == 'onboarding_mapa':
    st.header(f"Bienvenido {st.session_state.usuario['nombre']} - Delimitación Satelital")
    st.write("📍 **Paso 1:** Utilice la herramienta de polígono ⬠ (arriba a la izquierda del mapa) para dibujar las líneas de su parcela real.")
    
    # Mapa con herramientas de dibujo habilitadas
    mapa_dibujo = folium.Map(location=[-33.456, -70.650], zoom_start=16, tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", attr="Esri")
    draw = plugins.Draw(export=True, position='topleft', draw_options={'polyline':False, 'circlemarker':False, 'marker':False, 'circle':False})
    draw.add_to(mapa_dibujo)
    st_folium(mapa_dibujo, width=1000, height=400)
    
    st.write("📍 **Paso 2:** Ingrese el área total de la zona que acaba de demarcar.")
    area_ingresada = st.number_input("Área total del predio (m²):", min_value=100, max_value=1000000, value=5000, step=100)
    
    if st.button("Confirmar Área y Continuar ➡️", type="primary"):
        st.session_state.parcela_area = area_ingresada
        st.session_state.paso = 'onboarding_cultivos'
        st.rerun()

# ==========================================
# FASE 3: DISTRIBUCIÓN DE CULTIVOS (Validación estricta)
# ==========================================
elif st.session_state.paso == 'onboarding_cultivos':
    st.header("🌾 Distribución de Plantaciones")
    st.write(f"Usted cuenta con un total de **{st.session_state.parcela_area} m²** registrados.")
    
    cultivos_seleccionados = st.multiselect("Seleccione todos los tipos de cultivos presentes en su parcela:", DB_CULTIVOS)
    
    if cultivos_seleccionados:
        st.write("Distribuye el espacio para cada plantación:")
        area_asignada_total = 0
        asignaciones_temporales = {}
        
        for cultivo in cultivos_seleccionados:
            m2 = st.number_input(f"Metros cuadrados para {cultivo}:", min_value=0, max_value=st.session_state.parcela_area, value=0, step=100)
            asignaciones_temporales[cultivo] = m2
            area_asignada_total += m2
        
        # Barra de progreso visual
        porcentaje_uso = min(area_asignada_total / st.session_state.parcela_area, 1.0)
        st.progress(porcentaje_uso)
        st.write(f"Total asignado: **{area_asignada_total} m²** de **{st.session_state.parcela_area} m²**")
        
        # Reglas de validación para poder avanzar
        if area_asignada_total > st.session_state.parcela_area:
            st.error("❌ Error: Has superado el límite de tu parcela. Reduce los metros de algún cultivo.")
        elif area_asignada_total == 0:
            st.warning("⚠️ Debes asignar al menos 1 metro cuadrado para continuar.")
        else:
            if st.button("✅ Confirmar Distribución y Acceder al Sistema", type="primary"):
                st.session_state.cultivos_asignados = asignaciones_temporales
                st.session_state.paso = 'dashboard'
                
                # Cargar el registro base del día
                st.session_state.registro_diario = [
                    {"Hora": "06:00", "Sector": "General", "Acción": "Monitoreo Inicial", "Estado": "🟢 Óptimo", "Observación": "Humedad inicial 60%"},
                    {"Hora": "10:30", "Sector": "Cultivo Crítico", "Acción": "Alerta IoT", "Estado": "🔴 Crítico", "Observación": "Caída de humedad. Estrés detectado."},
                ]
                st.rerun()

# ==========================================
# FASE 4: DASHBOARD PRINCIPAL (3 Pestañas)
# ==========================================
elif st.session_state.paso == 'dashboard':
    st.title(f"📊 Dashboard Enjambre VRA | Admin: {st.session_state.usuario['nombre']}")
    
    tab1, tab2, tab3 = st.tabs(["🌱 1. Sensores y Suelo (IoT)", "🚁 2. Logística Dron", "📈 3. Reporte Diario y Evaluación"])
    
    # ---------------- PESTAÑA 1: SENSORES ----------------
    with tab1:
        st.header("Monitoreo en Tiempo Real (Integración Weenat)")
        clima_cols = st.columns(4)
        clima_cols[0].metric("Temperatura Actual", "28°C", "Alta radiación")
        clima_cols[1].metric("Humedad Relativa", "35%", "-5%")
        clima_cols[2].metric("Viento", "12 km/h", "Óptimo para vuelo")
        clima_cols[3].metric("Radiación UV", "Muy Alta", "Riesgo foliar")
        
        st.markdown("---")
        st.subheader("📡 Estado de Plantaciones por Sector")
        
        nombres_cultivos = list(st.session_state.cultivos_asignados.keys())
        zonas = st.columns(3)
        
        # Generar las alertas basadas en lo que el usuario seleccionó
        if len(nombres_cultivos) > 0:
            with zonas[0]:
                st.markdown(f'<div class="sensor-verde"><b>Zona A ({nombres_cultivos[0]})</b><br>Humedad: 68%<br>Área: {st.session_state.cultivos_asignados[nombres_cultivos[0]]} m2<br>Estado: Óptimo</div>', unsafe_allow_html=True)
        if len(nombres_cultivos) > 1:
            with zonas[1]:
                st.markdown(f'<div class="sensor-amarillo"><b>Zona B ({nombres_cultivos[1]})</b><br>Humedad: 45%<br>Área: {st.session_state.cultivos_asignados[nombres_cultivos[1]]} m2<br>Estado: Estrés leve</div>', unsafe_allow_html=True)
        
        with zonas[2]:
            st.markdown('<div class="sensor-rojo"><b>🚨 Zona de Riesgo</b><br>Humedad: 22% & Plaga<br>Estado: CRÍTICO<br>Requiere Dron Inmediato</div>', unsafe_allow_html=True)

    # ---------------- PESTAÑA 2: DRON Y RESTRICCIONES ----------------
    with tab2:
        st.header("Centro de Mando Logístico VRA")
        col_ctrl, col_map = st.columns([1, 2])
        
        with col_ctrl:
            hora_actual = st.slider("Simulador de Reloj:", min_value=0, max_value=23, value=14, format="%d:00 hrs")
            tipo_mision = st.radio("Acción a ejecutar:", ["Riego (Agua)", "Nutrición (Proteínas)", "Tratamiento (Anti-plagas)"])
            
            # LÓGICA DE EMERGENCIA Y RESTRICCIÓN
            es_riesgoso = (tipo_mision == "Riego (Agua)" and 10 <= hora_actual <= 18)
            boton_deshabilitado = False
            
            if es_riesgoso:
                st.error("⚠️ ADVERTENCIA CRÍTICA: Desplegar riego a esta hora quemará la plantación por efecto lupa solar.")
                acepta_riesgo = st.checkbox("Declaro que entiendo los riesgos y autorizo el despliegue manual.")
                if not acepta_riesgo:
                    boton_deshabilitado = True # Deshabilita el botón si no firma
            
            if st.button("🚀 Forzar Despliegue Manual", type="primary", disabled=boton_deshabilitado, use_container_width=True):
                with st.spinner("Sincronizando ruta..."):
                    time.sleep(1.5)
                    st.success(f"Dron en vuelo. Misión: {tipo_mision}")
                    
                    # Agregar al registro diario automáticamente
                    nuevo_registro = {
                        "Hora": f"{hora_actual}:00", 
                        "Sector": "Zona de Riesgo", 
                        "Acción": f"Dron: {tipo_mision}", 
                        "Estado": "🟡 Riesgo Asumido" if es_riesgoso else "🟢 Completado", 
                        "Observación": "Despliegue manual forzado por admin." if es_riesgoso else "Operación estándar."
                    }
                    st.session_state.registro_diario.append(nuevo_registro)
        
        with col_map:
            mapa_dron = folium.Map(location=[-33.456, -70.650], zoom_start=16, tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", attr="Esri")
            st_folium(mapa_dron, width=700, height=400)

    # ---------------- PESTAÑA 3: REPORTABILIDAD (TABLA) ----------------
    with tab3:
        st.header("Bitácora Diaria y Desempeño")
        st.write("Registro histórico de la jornada y evaluación de la parcela.")
        
        # Convertir el registro en memoria a un DataFrame profesional
        df_registro = pd.DataFrame(st.session_state.registro_diario)
        
        # Mostrar la tabla estilizada
        st.dataframe(df_registro, use_container_width=True)
        
        st.markdown("---")
        st.subheader("📲 Evaluación y Exportación")
        
        resumen_bot = f"""*REPORTE ENJAMBRE VRA* 🚁
Hola {st.session_state.usuario['nombre']}, resumen del predio:
- Área cubierta: {st.session_state.parcela_area} m2
- Estado de humedad general: ESTABLE
- Atención: Requiere revisión en Zona de Riesgo.
- Vuelos realizados: {len(st.session_state.registro_diario) - 2} hoy."""
        
        col_w1, col_w2 = st.columns(2)
        with col_w1:
            st.text_area("Mensaje de WhatsApp a enviar:", value=resumen_bot, height=150)
            if st.button("Enviar Resumen por WhatsApp", type="primary"):
                st.success(f"Enviado al {st.session_state.usuario['telefono']}")
        with col_w2:
            st.write("¿Evaluación manual del día?")
            evaluacion = st.text_input("Agregar notas de desempeño para el gerente:")
            if st.button("Guardar en Bitácora"):
                st.info("Nota de evaluación agregada al servidor.")
