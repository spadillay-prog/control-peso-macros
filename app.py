import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
import os

# ==========================================
# SEGURIDAD: CONTROL DE ACCESO
# ==========================================
def verificar_acceso():
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False

    if not st.session_state.autenticado:
        st.title("🔒 Acceso Privado")
        st.caption("Panel personal de control nutricional y composición corporal.")
        clave_ingresada = st.text_input("Ingresa tu contraseña:", type="password")
        if st.button("Ingresar", use_container_width=True):
            clave_correcta = st.secrets.get("APP_PASSWORD", "Carla2019")
            if clave_ingresada == clave_correcta:
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta. Inténtalo de nuevo.")
        st.stop()

verificar_acceso()
st.set_page_config(
    page_title="Control Nutricional & Composición",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

FILE_HISTORICO = "historico_corporal.csv"
FILE_COMIDAS = "registro_comidas_detalle.csv"
FILE_DIARIO = "resumen_diario_macros.csv"

ESTATURA_M = 1.91
CAL_MIN, CAL_MAX = 1950, 2050
PROT_MIN = 140

# Catálogo completo: Básicos + Eventos / Antojos
CATALOGO = {
    # Básicos y Proteínas
    "Pechuga de pollo a la plancha (g)": {"tipo": "g", "cal": 1.65, "p": 0.31, "c": 0.0, "g": 0.036},
    "Pechuga de pollo en Airfryer (g)": {"tipo": "g", "cal": 1.70, "p": 0.32, "c": 0.0, "g": 0.038},
    "Huevo entero (u)": {"tipo": "u", "cal": 72.0, "p": 6.3, "c": 0.4, "g": 4.8},
    "Clara de huevo (u)": {"tipo": "u", "cal": 17.0, "p": 3.6, "c": 0.2, "g": 0.1},
    "Jurel al agua enlatado (g)": {"tipo": "g", "cal": 1.30, "p": 0.21, "c": 0.0, "g": 0.05},
    "Tilapia / Pescado blanco (g)": {"tipo": "g", "cal": 0.96, "p": 0.20, "c": 0.0, "g": 0.017},
    "Whey Protein QNT (g)": {"tipo": "g", "cal": 3.83, "p": 0.816, "c": 0.066, "g": 0.05},
    "Loncoleche Protein en polvo (g)": {"tipo": "g", "cal": 4.00, "p": 0.525, "c": 0.375, "g": 0.05},
    "Atún Van Camps al agua (lata 104g drenado)": {"tipo": "u", "cal": 112, "p": 26.0, "c": 1.4, "g": 0.2},
    "Cacao amargo en polvo (g)": {"tipo": "g", "cal": 3.10, "p": 0.20, "c": 0.21, "g": 0.14},
    # Carbohidratos y Frutas
    "Avena integral (g)": {"tipo": "g", "cal": 3.75, "p": 0.13, "c": 0.60, "g": 0.07},
    "Pan integral (g)": {"tipo": "g", "cal": 2.50, "p": 0.09, "c": 0.45, "g": 0.03},
    "Arroz cocido (g)": {"tipo": "g", "cal": 1.30, "p": 0.027, "c": 0.28, "g": 0.003},
    "Papas cocidas (g)": {"tipo": "g", "cal": 0.87, "p": 0.02, "c": 0.201, "g": 0.001},
    "Manzana roja (u mediana ~150g)": {"tipo": "u", "cal": 78.0, "p": 0.4, "c": 20.7, "g": 0.3},
    "Frutos rojos / Berries (g)": {"tipo": "g", "cal": 0.50, "p": 0.01, "c": 0.11, "g": 0.004},
    "Plátano (u mediana ~100g)": {"tipo": "u", "cal": 89.0, "p": 1.1, "c": 22.8, "g": 0.3},
    "Naranja (u mediana ~130g)": {"tipo": "u", "cal": 62.0, "p": 1.2, "c": 15.4, "g": 0.2},
    "Pera (u mediana ~160g)": {"tipo": "u", "cal": 85.0, "p": 0.6, "c": 22.0, "g": 0.2},
    "Frutillas (g)": {"tipo": "g", "cal": 0.33, "p": 0.007, "c": 0.077, "g": 0.003},
    "Mandarina (u mediana ~80g)": {"tipo": "u", "cal": 40.0, "p": 0.6, "c": 10.0, "g": 0.2},
    "Kiwi (u mediana ~75g)": {"tipo": "u", "cal": 42.0, "p": 0.8, "c": 10.1, "g": 0.4},
    "Yoghurt Protein+ Sabor Natural (155g)": {"tipo": "u", "cal": 105.4, "p": 10.2, "c": 9.8, "g": 2.8},
    "Linaza molida": {"tipo": "g", "cal": 5.34, "p": 0.183, "c": 0.02, "g": 0.422},
    "Pino de soya casero cocinado": {"tipo": "g", "cal": 1.11, "p": 0.121, "c": 0.088, "g": 0.03},
    
    # Lácteos y Grasas Saludables
    "Leche descremada Colún (ml)": {"tipo": "g", "cal": 0.32, "p": 0.031, "c": 0.047, "g": 0.001},
    "Yogurt Oikos Griego Natural (pote 150g)": {"tipo": "u", "cal": 135.0, "p": 7.0, "c": 7.5, "g": 8.0},
    "Semillas de chía (g)": {"tipo": "g", "cal": 4.86, "p": 0.165, "c": 0.42, "g": 0.31},
    "Aceite de oliva / vegetal (cda ~10g)": {"tipo": "u", "cal": 88.0, "p": 0.0, "c": 0.0, "g": 10.0},
    "Aceite en spray (1 spray ~0.3ml)": {"tipo": "u", "cal": 2.7, "p": 0.0, "c": 0.0, "g": 0.3},
    "Palta (g)": {"tipo": "g", "cal": 1.60, "p": 0.02, "c": 0.085, "g": 0.147},
    
    # Verduras / Extras
    "Alcachofa cocida (u mediana)": {"tipo": "u", "cal": 55.0, "p": 3.5, "c": 12.0, "g": 0.2},
   "Sopa espárragos sobre (1 taza / porción)": {"tipo": "u", "cal": 55.0, "p": 1.2, "c": 9.5, "g": 1.5},
    "Hojas verdes (lechuga, espinaca)": {"tipo": "u", "cal": 0.0, "p": 0.0, "c": 0.0, "g": 0.0},
    "Sopa de verduras casera": {"tipo": "g", "cal": 0.40, "p": 0.011, "c": 0.08, "g": 0.007},
    
    # Antojos, Salidas y Eventos Sociales
    "Bombón Frac (u)": {"tipo": "u", "cal": 60.0, "p": 0.6, "c": 7.2, "g": 3.3},
    "Cerveza rubia tradicional (lata/botella 350ml)": {"tipo": "u", "cal": 150.0, "p": 1.5, "c": 12.5, "g": 0.0},
    "Cerveza IPA o artesanal (copa/vaso 350ml)": {"tipo": "u", "cal": 210.0, "p": 2.0, "c": 18.0, "g": 0.0},
    "Cerveza Sin Alcohol (lata 350ml)": {"tipo": "u", "cal": 70.0, "p": 1.0, "c": 15.0, "g": 0.0},
    "Vino tinto (copa 150ml)": {"tipo": "u", "cal": 125.0, "p": 0.1, "c": 3.8, "g": 0.0},
    "Pizza tradicional (1 porción/slice grande)": {"tipo": "u", "cal": 270.0, "p": 11.0, "c": 32.0, "g": 10.0},
    "Hamburguesa tradicional con queso (unidad)": {"tipo": "u", "cal": 550.0, "p": 28.0, "c": 40.0, "g": 31.0},
    "Papas fritas porción mediana (120g)": {"tipo": "u", "cal": 365.0, "p": 4.0, "c": 48.0, "g": 17.0}
    "Empanada de pino casera al horno": {"tipo": "g", "cal": 2.35, "p": 0.085, "c": 0.24, "g": 0.11},
}

def init_df(filename, cols):
    if os.path.exists(filename):
        df = pd.read_csv(filename)
        if "fecha" in df.columns:
            df["fecha"] = pd.to_datetime(df["fecha"]).dt.date
        return df
    return pd.DataFrame(columns=cols)

df_hist = init_df(FILE_HISTORICO, ["fecha", "peso_kg", "grasa_pct", "musculo_pct", "kg_grasa", "kg_musculo", "imc", "notas"])
df_comidas = init_df(FILE_COMIDAS, ["fecha", "tiempo", "alimento", "cantidad", "calorias", "proteina_g", "carbos_g", "grasas_g"])
df_diario = init_df(FILE_DIARIO, ["fecha", "calorias", "proteina_g", "carbos_g", "grasas_g"])

st.title("⚡ Control Corporal & Nutricional")

# ==========================================
# BARRA LATERAL: IMPORTAR EXCEL & PESAJE
# ==========================================
with st.sidebar:
    st.header("📂 Tu Histórico Excel")
    archivo = st.file_uploader("Sube tu archivo .xlsx", type=["xlsx", "xls"])
    if archivo is not None:
        try:
            raw_excel = pd.read_excel(archivo)
            st.write("Columnas:", list(raw_excel.columns))
            c_f = st.selectbox("Fecha", raw_excel.columns)
            c_p = st.selectbox("Peso (kg)", raw_excel.columns)
            c_g = st.selectbox("% Grasa", ["No incluir"] + list(raw_excel.columns))
            c_m = st.selectbox("% Músculo", ["No incluir"] + list(raw_excel.columns))
            
            if st.button("📥 Importar Histórico"):
                temp = pd.DataFrame()
                temp["fecha"] = pd.to_datetime(raw_excel[c_f]).dt.date
                temp["peso_kg"] = pd.to_numeric(raw_excel[c_p], errors="coerce")
                temp["grasa_pct"] = pd.to_numeric(raw_excel[c_g], errors="coerce") if c_g != "No incluir" else None
                temp["musculo_pct"] = pd.to_numeric(raw_excel[c_m], errors="coerce") if c_m != "No incluir" else None
                
                # Derivadas automáticas
                temp["imc"] = (temp["peso_kg"] / (ESTATURA_M ** 2)).round(2)
                temp["kg_grasa"] = ((temp["peso_kg"] * temp["grasa_pct"]) / 100.0).round(2) if c_g != "No incluir" else None
                temp["kg_musculo"] = ((temp["peso_kg"] * temp["musculo_pct"]) / 100.0).round(2) if c_m != "No incluir" else None
                temp["notas"] = "Excel Histórico"
                
                df_hist = pd.concat([df_hist, temp]).drop_duplicates(subset=["fecha"], keep="last").sort_values("fecha")
                df_hist.to_csv(FILE_HISTORICO, index=False)
                st.success("¡Datos históricos cargados!")
                st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

    st.markdown("---")
    st.header("⚖️ Registrar Pesaje Semanal / Diario")
    with st.form("form_peso"):
        f_reg = st.date_input("Fecha", value=date.today())
        p_reg = st.number_input("Peso (kg)", min_value=40.0, max_value=160.0, value=85.0, step=0.1)
        g_reg = st.number_input("% Grasa (ej: 22.5)", min_value=0.0, max_value=60.0, value=20.0, step=0.1)
        m_reg = st.number_input("% Músculo (ej: 42.0)", min_value=0.0, max_value=80.0, value=40.0, step=0.1)
        n_reg = st.text_input("Nota", placeholder="Pesaje en ayunas")
        
        if st.form_submit_button("Guardar Medición"):
            imc_val = round(p_reg / (ESTATURA_M ** 2), 2)
            kg_g_val = round((p_reg * g_reg) / 100.0, 2)
            kg_m_val = round((p_reg * m_reg) / 100.0, 2)
            
            nueva_fila = {
                "fecha": f_reg, "peso_kg": p_reg, "grasa_pct": g_reg,
                "musculo_pct": m_reg, "kg_grasa": kg_g_val, "kg_musculo": kg_m_val,
                "imc": imc_val, "notas": n_reg
            }
            df_hist = df_hist[df_hist["fecha"] != f_reg]
            df_hist = pd.concat([df_hist, pd.DataFrame([nueva_fila])], ignore_index=True).sort_values("fecha")
            df_hist.to_csv(FILE_HISTORICO, index=False)
            st.success("¡Pesaje y composición registrados!")
            st.rerun()

# ==========================================
# PESTAÑAS PRINCIPALES
# ==========================================
tab_diario, tab_graficos, tab_tablas = st.tabs(["🍽️️ Registro del Día", "📈 Métricas & Gráficos", "📋 Historial"])

# --- TAB 1: REGISTRO DIARIO Y COMPENSACIÓN ---
with tab_diario:
    dia_sel = st.date_input("Fecha a gestionar", value=date.today(), key="dia_activo")
    
    # Filtrar comidas del día
    comidas_hoy = df_comidas[df_comidas["fecha"] == dia_sel].copy() if not df_comidas.empty else pd.DataFrame()
    
    tot_cal = round(comidas_hoy["calorias"].sum(), 1) if not comidas_hoy.empty else 0.0
    tot_prot = round(comidas_hoy["proteina_g"].sum(), 1) if not comidas_hoy.empty else 0.0
    tot_carb = round(comidas_hoy["carbos_g"].sum(), 1) if not comidas_hoy.empty else 0.0
    tot_fat = round(comidas_hoy["grasas_g"].sum(), 1) if not comidas_hoy.empty else 0.0
    
    # Tarjetas superiores estilo Dashboard
    c1, c2, c3, c4 = st.columns(4)
    cal_delta = tot_cal - CAL_MIN
    prot_delta = tot_prot - PROT_MIN
    
    c1.metric("🔥 Calorías Consumidas", f"{tot_cal} kcal", delta=f"{int(cal_delta)} vs piso (1.950)")
    c2.metric("🥩 Proteína Acumulada", f"{tot_prot} g", delta=f"{int(prot_delta)} vs piso (140g)")
    c3.metric("🍞 Carbohidratos", f"{tot_carb} g")
    c4.metric("🥑 Grasas", f"{tot_fat} g")
    
    # Calculadora de "Margen / Compensación"
    st.markdown("#### 🎯 Estado de Metas y Compensación")
    cal_pendientes_min = max(0.0, CAL_MIN - tot_cal)
    cal_pendientes_max = max(0.0, CAL_MAX - tot_cal)
    prot_pendiente = max(0.0, PROT_MIN - tot_prot)
    
    if tot_cal > CAL_MAX:
        st.warning(f"⚠️ Te pasaste por **{int(tot_cal - CAL_MAX)} kcal** del techo diario. Prioriza cena liviana en hojas verdes y proteína magra.")
    elif tot_cal >= CAL_MIN:
        st.success(f"✅ ¡Estás en la ventana óptima de déficit! ({tot_cal} kcal). Margen restante hasta el techo: **{int(cal_pendientes_max)} kcal**.")
    else:
        st.info(f"💡 Te faltan entre **{int(cal_pendientes_min)} y {int(cal_pendientes_max)} kcal** para alcanzar tu rango objetivo. Proteína restante para cumplir el piso: **{int(prot_pendiente)} g**.")

    st.markdown("---")
    
    # Formulario para agregar comidas por bloque
    st.subheader("➕ Agregar Alimento por Tiempo de Comida")
    col_t1, col_t2, col_t3, col_t4 = st.columns([2, 3, 2, 2])
    
    with col_t1:
        tiempo_sel = st.selectbox("Momento", ["Desayuno", "Almuerzo", "Merienda", "Cena", "Evento / Social"])
    with col_t2:
        alimento_sel = st.selectbox("Alimento / Producto", list(CATALOGO.keys()))
    with col_t3:
        info_al = CATALOGO[alimento_sel]
        label_unid = "Unidades / Porciones" if info_al["tipo"] == "u" else "Gramos o ml"
        val_ini = 1.0 if info_al["tipo"] == "u" else 100.0
        cant_sel = st.number_input(label_unid, min_value=0.1, value=val_ini, step=1.0)
    with col_t4:
        st.write("")
        st.write("")
        if st.button("Añadir al Plato", use_container_width=True):
            factor = cant_sel if info_al["tipo"] == "u" else (cant_sel)
            c_calc = round(info_al["cal"] * factor, 1)
            p_calc = round(info_al["p"] * factor, 1)
            car_calc = round(info_al["c"] * factor, 1)
            g_calc = round(info_al["g"] * factor, 1)
            
            nueva_comida = {
                "fecha": dia_sel, "tiempo": tiempo_sel, "alimento": alimento_sel,
                "cantidad": cant_sel, "calorias": c_calc, "proteina_g": p_calc,
                "carbos_g": car_calc, "grasas_g": g_calc
            }
            df_comidas = pd.concat([df_comidas, pd.DataFrame([nueva_comida])], ignore_index=True)
            df_comidas.to_csv(FILE_COMIDAS, index=False)
            
            # Actualizar resumen diario
            sub_d = df_comidas[df_comidas["fecha"] == dia_sel]
            res_dia = {
                "fecha": dia_sel, "calorias": round(sub_d["calorias"].sum(), 1),
                "proteina_g": round(sub_d["proteina_g"].sum(), 1),
                "carbos_g": round(sub_d["carbos_g"].sum(), 1),
                "grasas_g": round(sub_d["grasas_g"].sum(), 1)
            }
            df_diario = df_diario[df_diario["fecha"] != dia_sel]
            df_diario = pd.concat([df_diario, pd.DataFrame([res_dia])], ignore_index=True).sort_values("fecha")
            df_diario.to_csv(FILE_DIARIO, index=False)
            st.rerun()

# Desglose del día por bloques con edición interactiva y eliminación
    if not comidas_hoy.empty:
        st.markdown("### 📋 Desglose del Día")
        st.caption("💡 Puedes editar la cantidad directamente en la casilla o marcar la casilla de la izquierda y presionar la tecla Supr/Delete para eliminar un alimento.")
        
        # Tabla editable interactiva
        cols_mostrar = ["tiempo", "alimento", "cantidad", "calorias", "proteina_g", "carbos_g", "grasas_g"]
        comidas_editables = comidas_hoy[cols_mostrar].copy()
        
        df_editado = st.data_editor(
            comidas_editables,
            column_config={
                "tiempo": st.column_config.SelectboxColumn("Momento", options=["Desayuno", "Almuerzo", "Merienda", "Cena", "Evento / Social"], required=True),
                "alimento": st.column_config.TextColumn("Alimento", disabled=True),
                "cantidad": st.column_config.NumberColumn("Cantidad", min_value=0.1, step=1.0, required=True),
                "calorias": st.column_config.NumberColumn("Calorías", disabled=True),
                "proteina_g": st.column_config.NumberColumn("Proteína", disabled=True),
                "carbos_g": st.column_config.NumberColumn("Carbos", disabled=True),
                "grasas_g": st.column_config.NumberColumn("Grasas", disabled=True),
            },
            num_rows="dynamic",
            use_container_width=True,
            key="editor_comidas"
        )
        
        c_ed1, c_ed2 = st.columns([3, 4])
        with c_ed1:
            if st.button("🔄 Aplicar Cambios / Recalcular", use_container_width=True):
                # Recalcular macros según los nuevos valores de cantidad ingresados
                nuevas_filas = []
                for _, row in df_editado.iterrows():
                    alim = row["alimento"]
                    if alim in CATALOGO:
                        info = CATALOGO[alim]
                        cant = float(row["cantidad"])
                        factor = cant if info["tipo"] == "u" else (cant / 100.0 if info.get("div100") else cant)
                        nuevas_filas.append({
                            "fecha": dia_sel,
                            "tiempo": row["tiempo"],
                            "alimento": alim,
                            "cantidad": cant,
                            "calorias": round(info["cal"] * factor, 1),
                            "proteina_g": round(info["p"] * factor, 1),
                            "carbos_g": round(info["c"] * factor, 1),
                            "grasas_g": round(info["g"] * factor, 1),
                        })
                
                # Reemplazar en la base de datos completa
                df_comidas = df_comidas[df_comidas["fecha"] != dia_sel]
                if nuevas_filas:
                    df_comidas = pd.concat([df_comidas, pd.DataFrame(nuevas_filas)], ignore_index=True)
                df_comidas.to_csv(FILE_COMIDAS, index=False)
                
                # Actualizar resumen diario
                df_diario = df_diario[df_diario["fecha"] != dia_sel]
                if nuevas_filas:
                    df_sub = pd.DataFrame(nuevas_filas)
                    res_dia = {
                        "fecha": dia_sel,
                        "calorias": round(df_sub["calorias"].sum(), 1),
                        "proteina_g": round(df_sub["proteina_g"].sum(), 1),
                        "carbos_g": round(df_sub["carbos_g"].sum(), 1),
                        "grasas_g": round(df_sub["grasas_g"].sum(), 1)
                    }
                    df_diario = pd.concat([df_diario, pd.DataFrame([res_dia])], ignore_index=True).sort_values("fecha")
                df_diario.to_csv(FILE_DIARIO, index=False)
                
                st.success("¡Datos actualizados y macros recalculados!")
                st.rerun()

        with c_ed2:
            if st.button("🗑️ Borrar todo el día"):
                df_comidas = df_comidas[df_comidas["fecha"] != dia_sel]
                df_comidas.to_csv(FILE_COMIDAS, index=False)
                df_diario = df_diario[df_diario["fecha"] != dia_sel]
                df_diario.to_csv(FILE_DIARIO, index=False)
                st.rerun()
# --- TAB 2: GRÁFICOS Y ANÁLISIS ---
with tab_graficos:
    if not df_hist.empty:
        df_h = df_hist.sort_values("fecha").copy()
        
        st.subheader("1. Evolución del Peso & IMC")
        df_h["ma_peso"] = df_h["peso_kg"].rolling(window=3, min_periods=1).mean()
        
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=df_h["fecha"], y=df_h["peso_kg"], mode="lines+markers", name="Peso real (kg)", line=dict(color="#42a5f5", width=2)))
        fig1.add_trace(go.Scatter(x=df_h["fecha"], y=df_h["ma_peso"], mode="lines", name="Tendencia Suavizada", line=dict(color="#1565c0", width=3)))
        fig1.add_trace(go.Scatter(x=df_h["fecha"], y=df_h["imc"], mode="lines+markers", name="IMC", yaxis="y2", line=dict(color="#ab47bc", dash="dot")))
        
        fig1.update_layout(
            height=380, hovermode="x unified",
            yaxis=dict(title="Peso (kg)"),
            yaxis2=dict(title="IMC", overlaying="y", side="right"),
            margin=dict(l=10, r=10, t=30, b=20)
        )
        st.plotly_chart(fig1, use_container_width=True)
        
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.subheader("2. Porcentajes (%) Grasa vs Músculo")
            fig2 = go.Figure()
            if "grasa_pct" in df_h.columns:
                fig2.add_trace(go.Scatter(x=df_h["fecha"], y=df_h["grasa_pct"], name="% Grasa", line=dict(color="#ef5350", width=2)))
            if "musculo_pct" in df_h.columns:
                fig2.add_trace(go.Scatter(x=df_h["fecha"], y=df_h["musculo_pct"], name="% Músculo", line=dict(color="#66bb6a", width=2)))
            fig2.update_layout(height=340, yaxis_title="Porcentaje (%)", margin=dict(l=10, r=10, t=30, b=20))
            st.plotly_chart(fig2, use_container_width=True)
            
        with col_g2:
            st.subheader("3. Kilos Netos: Grasa (kg) vs Músculo (kg)")
            fig3 = go.Figure()
            if "kg_grasa" in df_h.columns and df_h["kg_grasa"].notna().any():
                fig3.add_trace(go.Bar(x=df_h["fecha"], y=df_h["kg_grasa"], name="Kg de Grasa", marker_color="#ff7043"))
            if "kg_musculo" in df_h.columns and df_h["kg_musculo"].notna().any():
                fig3.add_trace(go.Bar(x=df_h["fecha"], y=df_h["kg_musculo"], name="Kg de Músculo", marker_color="#42b883"))
            fig3.update_layout(height=340, barmode="group", yaxis_title="Kilos (kg)", margin=dict(l=10, r=10, t=30, b=20))
            st.plotly_chart(fig3, use_container_width=True)

    if not df_diario.empty:
        st.subheader("4. Consumo Calórico Diario vs Ventana Objetivo")
        df_d = df_diario.sort_values("fecha")
        fig4 = go.Figure()
        fig4.add_trace(go.Bar(x=df_d["fecha"], y=df_d["calorias"], name="Calorías consumidas", marker_color="#ffa726"))
        fig4.add_hline(y=CAL_MIN, line_dash="dash", line_color="green", annotation_text="Piso 1.950 kcal")
        fig4.add_hline(y=CAL_MAX, line_dash="dash", line_color="red", annotation_text="Techo 2.050 kcal")
        fig4.update_layout(height=320, yaxis_title="kcal", margin=dict(l=10, r=10, t=30, b=20))
        st.plotly_chart(fig4, use_container_width=True)

# --- TAB 3: TABLAS HISTÓRICAS ---
with tab_tablas:
    st.subheader("Historial Corporal (Peso, Grasa, Músculo e IMC)")
    st.dataframe(df_hist.sort_values("fecha", ascending=False), use_container_width=True)
    st.subheader("Historial Nutricional Diario Consolidado")
    st.dataframe(df_diario.sort_values("fecha", ascending=False), use_container_width=True)
