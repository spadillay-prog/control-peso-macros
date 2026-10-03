import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
import os

st.set_page_config(page_title="Control Corporal & Nutrición", page_icon="📊", layout="wide")

FILE_HISTORICO = "historico_corporal.csv"
FILE_CONSUMO = "consumo_diario.csv"

# Catálogo predefinido con tus alimentos habituales
CATALOGO_ALIMENTOS = {
    "Huevo entero (u)": {"tipo": "unidad", "cal": 72, "p": 6.3, "c": 0.4, "g": 4.8},
    "Pechuga de pollo cocida (g)": {"tipo": "gramos", "cal": 165, "p": 31.0, "c": 0.0, "g": 3.6},
    "Pan integral (g)": {"tipo": "gramos", "cal": 250, "p": 9.0, "c": 45.0, "g": 3.0},
    "Avena integral (g)": {"tipo": "gramos", "cal": 375, "p": 13.0, "c": 60.0, "g": 7.0},
    "Whey Protein QNT (g)": {"tipo": "gramos", "cal": 383, "p": 81.6, "c": 6.6, "g": 5.0},
    "Leche descremada Colún (ml)": {"tipo": "gramos", "cal": 32, "p": 3.1, "c": 4.7, "g": 0.1},
    "Loncoleche Protein en polvo (g)": {"tipo": "gramos", "cal": 400, "p": 52.5, "c": 37.5, "g": 5.0},
    "Papas cocidas (g)": {"tipo": "gramos", "cal": 87, "p": 2.0, "c": 20.1, "g": 0.1},
    "Semillas de chía (g)": {"tipo": "gramos", "cal": 486, "p": 16.5, "c": 42.0, "g": 31.0},
    "Frutos rojos / Berries (g)": {"tipo": "gramos", "cal": 50, "p": 1.0, "c": 11.0, "g": 0.4},
    "Manzana roja (u mediana ~150g)": {"tipo": "unidad", "cal": 78, "p": 0.4, "c": 20.7, "g": 0.3},
    "Bombón Frac (u)": {"tipo": "unidad", "cal": 60, "p": 0.6, "c": 7.2, "g": 3.3},
    "Aceite en spray (1 spray ~0.3ml)": {"tipo": "unidad", "cal": 2.7, "p": 0.0, "c": 0.0, "g": 0.3},
    "Alcachofa cocida (u mediana)": {"tipo": "unidad", "cal": 55, "p": 3.5, "c": 12.0, "g": 0.2},
    "Sopa espárragos sobre (taza/porción)": {"tipo": "unidad", "cal": 55, "p": 1.2, "c": 9.5, "g": 1.5}
}

def cargar_historico():
    if os.path.exists(FILE_HISTORICO):
        df = pd.read_csv(FILE_HISTORICO)
        df["fecha"] = pd.to_datetime(df["fecha"]).dt.date
        return df
    return pd.DataFrame(columns=["fecha", "peso_kg", "grasa_pct", "musculo_kg", "notas"])

def cargar_consumo():
    if os.path.exists(FILE_CONSUMO):
        df = pd.read_csv(FILE_CONSUMO)
        df["fecha"] = pd.to_datetime(df["fecha"]).dt.date
        return df
    return pd.DataFrame(columns=["fecha", "calorias", "proteina_g", "carbos_g", "grasas_g"])

df_hist = cargar_historico()
df_cons = cargar_consumo()

st.title("Panel de Control: Peso, Composición & Nutrición")

# Barra lateral
with st.sidebar:
    st.header("📂 Subir Excel Histórico")
    archivo_subido = st.file_uploader("Arrastra tu archivo .xlsx", type=["xlsx", "xls"])
    if archivo_subido is not None:
        try:
            excel_df = pd.read_excel(archivo_subido)
            st.write("Columnas detectadas:", list(excel_df.columns))
            c_fecha = st.selectbox("Columna de Fecha", excel_df.columns)
            c_peso = st.selectbox("Columna de Peso (kg)", excel_df.columns)
            c_grasa = st.selectbox("Columna de % Grasa", ["No incluir"] + list(excel_df.columns))
            c_musc = st.selectbox("Columna de Músculo", ["No incluir"] + list(excel_df.columns))
            
            if st.button("Procesar e Importar"):
                df_nuevo = pd.DataFrame()
                df_nuevo["fecha"] = pd.to_datetime(excel_df[c_fecha]).dt.date
                df_nuevo["peso_kg"] = pd.to_numeric(excel_df[c_peso], errors="coerce")
                df_nuevo["grasa_pct"] = pd.to_numeric(excel_df[c_grasa], errors="coerce") if c_grasa != "No incluir" else None
                df_nuevo["musculo_kg"] = pd.to_numeric(excel_df[c_musc], errors="coerce") if c_musc != "No incluir" else None
                df_nuevo["notas"] = "Importado"
                
                df_hist = pd.concat([df_hist, df_nuevo]).drop_duplicates(subset=["fecha"], keep="last").sort_values("fecha")
                df_hist.to_csv(FILE_HISTORICO, index=False)
                st.success("¡Datos históricos importados exitosamente!")
                st.rerun()
        except Exception as e:
            st.error(f"Error al leer: {e}")

    st.markdown("---")
    st.header("⚖️ Registro Corporal Diario")
    with st.form("form_corporal"):
        f_corp = st.date_input("Fecha", value=date.today(), key="f_corp")
        p_corp = st.number_input("Peso en ayunas (kg)", min_value=40.0, max_value=160.0, value=85.0, step=0.1)
        g_corp = st.number_input("% Grasa (opcional)", min_value=0.0, max_value=60.0, value=20.0, step=0.1)
        m_corp = st.number_input("Músculo kg (opcional)", min_value=0.0, max_value=100.0, value=65.0, step=0.1)
        n_corp = st.text_input("Nota del día", placeholder="Día de piernas / pesaje normal")
        if st.form_submit_button("Guardar Pesaje"):
            nuevo_c = {"fecha": f_corp, "peso_kg": p_corp, "grasa_pct": g_corp, "musculo_kg": m_corp, "notas": n_corp}
            df_hist = df_hist[df_hist["fecha"] != f_corp]
            df_hist = pd.concat([df_hist, pd.DataFrame([nuevo_c])], ignore_index=True).sort_values("fecha")
            df_hist.to_csv(FILE_HISTORICO, index=False)
            st.success("Pesaje guardado.")
            st.rerun()

tab_calc, tab_graf, tab_datos = st.tabs(["🥣 Calculadora de Comidas", "📈 Gráficos y Tendencias", "📋 Historial Completo"])

with tab_calc:
    st.subheader("Calculadora Rápida de Alimentos")
    st.caption("Selecciona tus alimentos habituales. Las hojas verdes (lechuga, espinaca) son libres y no requieren registro.")
    
    fecha_comida = st.date_input("Fecha para registrar comidas", value=date.today(), key="f_comida")
    
    if "comidas_temp" not in st.session_state:
        st.session_state.comidas_temp = []

    c1, c2, c3 = st.columns([3, 2, 2])
    with c1:
        alim_elegido = st.selectbox("Alimento", list(CATALOGO_ALIMENTOS.keys()))
    with c2:
        info_al = CATALOGO_ALIMENTOS[alim_elegido]
        label_cant = "Unidades" if info_al["tipo"] == "unidad" else "Gramos o ml"
        val_default = 1.0 if info_al["tipo"] == "unidad" else 100.0
        cant = st.number_input(f"Cantidad ({label_cant})", min_value=0.1, value=val_default, step=1.0)
    with c3:
        st.write("")
        st.write("")
        if st.button("➕ Añadir Alimento"):
            factor = cant if info_al["tipo"] == "unidad" else (cant / 100.0)
            st.session_state.comidas_temp.append({
                "alimento": alim_elegido,
                "cantidad": cant,
                "cal": round(info_al["cal"] * factor, 1),
                "p": round(info_al["p"] * factor, 1),
                "c": round(info_al["c"] * factor, 1),
                "g": round(info_al["g"] * factor, 1)
            })

    if st.session_state.comidas_temp:
        df_temp = pd.DataFrame(st.session_state.comidas_temp)
        st.dataframe(df_temp, use_container_width=True)
        
        tot_c = round(df_temp["cal"].sum(), 1)
        tot_p = round(df_temp["p"].sum(), 1)
        tot_car = round(df_temp["c"].sum(), 1)
        tot_g = round(df_temp["g"].sum(), 1)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Calorías Totales", f"{tot_c} kcal", delta=f"{int(tot_c - 2000)} vs meta")
        m2.metric("Proteína Total", f"{tot_p} g", delta=f"{int(tot_p - 140)} vs piso")
        m3.metric("Carbohidratos", f"{tot_car} g")
        m4.metric("Grasas", f"{tot_g} g")

        b1, b2 = st.columns([2, 5])
        with b1:
            if st.button("💾 Guardar Día Nutricional"):
                nuevo_consumo = {
                    "fecha": fecha_comida,
                    "calorias": tot_c,
                    "proteina_g": tot_p,
                    "carbos_g": tot_car,
                    "grasas_g": tot_g
                }
                df_cons = df_cons[df_cons["fecha"] != fecha_comida]
                df_cons = pd.concat([df_cons, pd.DataFrame([nuevo_consumo])], ignore_index=True).sort_values("fecha")
                df_cons.to_csv(FILE_CONSUMO, index=False)
                st.session_state.comidas_temp = []
                st.success("Día registrado con éxito.")
                st.rerun()
        with b2:
            if st.button("🗑️ Borrar lista"):
                st.session_state.comidas_temp = []
                st.rerun()

with tab_graf:
    if not df_hist.empty:
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.subheader("Peso y Media Móvil (7 días)")
            df_h_plot = df_hist.sort_values("fecha").copy()
            df_h_plot["ma7"] = df_h_plot["peso_kg"].rolling(7, min_periods=1).mean()
            
            fig_p = go.Figure()
            fig_p.add_trace(go.Scatter(x=df_h_plot["fecha"], y=df_h_plot["peso_kg"], mode="markers+lines", name="Peso real", line=dict(color="#64b5f6")))
            fig_p.add_trace(go.Scatter(x=df_h_plot["fecha"], y=df_h_plot["ma7"], mode="lines", name="Tendencia 7d", line=dict(color="#0d47a1", width=3)))
            fig_p.update_layout(height=350, yaxis_title="kg", margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig_p, use_container_width=True)

        with col_g2:
            st.subheader("% Grasa vs Músculo (kg)")
            fig_comp = go.Figure()
            if "grasa_pct" in df_h_plot.columns and df_h_plot["grasa_pct"].notna().any():
                fig_comp.add_trace(go.Scatter(x=df_h_plot["fecha"], y=df_h_plot["grasa_pct"], name="% Grasa", line=dict(color="#e53935")))
            if "musculo_kg" in df_h_plot.columns and df_h_plot["musculo_kg"].notna().any():
                fig_comp.add_trace(go.Scatter(x=df_h_plot["fecha"], y=df_h_plot["musculo_kg"], name="Músculo (kg)", line=dict(color="#43a047"), yaxis="y2"))
            
            fig_comp.update_layout(
                height=350,
                yaxis=dict(title="% Grasa", titlefont=dict(color="#e53935")),
                yaxis2=dict(title="Músculo (kg)", titlefont=dict(color="#43a047"), overlaying="y", side="right"),
                margin=dict(l=20, r=20, t=30, b=20)
            )
            st.plotly_chart(fig_comp, use_container_width=True)

    if not df_cons.empty:
        st.subheader("Calorías Consumidas vs Rango Objetivo")
        df_c_plot = df_cons.sort_values("fecha")
        fig_cal = go.Figure()
        fig_cal.add_trace(go.Bar(x=df_c_plot["fecha"], y=df_c_plot["calorias"], name="Calorías consumidas", marker_color="#ffb74d"))
        fig_cal.add_hline(y=1950, line_dash="dash", line_color="green", annotation_text="Piso (1.950 kcal)")
        fig_cal.add_hline(y=2050, line_dash="dash", line_color="red", annotation_text="Techo (2.050 kcal)")
        fig_cal.update_layout(height=320, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_cal, use_container_width=True)

with tab_datos:
    st.subheader("Historial Corporal Registrado")
    st.dataframe(df_hist.sort_values("fecha", ascending=False), use_container_width=True)
    st.subheader("Historial Nutricional Diario")
    st.dataframe(df_cons.sort_values("fecha", ascending=False), use_container_width=True)
