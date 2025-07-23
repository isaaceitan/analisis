import streamlit as st
import pandas as pd
import plotly.express as px

# Simple password protection
PASSWORD = "abolu123"

st.title("🔒 Acceso restringido")

input_pass = st.text_input("Introduce la contraseña:", type="password")

# Cargar datos
df = pd.read_excel('formato.xlsx', engine='openpyxl')

# Procesamiento
df['Monto'] = pd.to_numeric(df['Monto'], errors='coerce')
month_map = {'Enero':1,'Febrero':2,'Marzo':3,'Abril':4,'Mayo':5,'Junio':6,'Julio':7,
             'Agosto':8,'Septiembre':9,'Octubre':10,'Noviembre':11,'Diciembre':12}
df['Fecha'] = df['Mes_Año'].apply(lambda x: pd.Timestamp(int(x.split()[1]), month_map[x.split()[0]], 1) if isinstance(x,str) and len(x.split())==2 else pd.NaT)
df = df.dropna(subset=['Fecha'])
df['Año'] = df['Fecha'].dt.year
df['Mes'] = df['Fecha'].dt.month
df['Semestre'] = df['Mes'].apply(lambda m: 1 if m <= 6 else 2)

st.title("📊 Análisis de Ventas 2024 vs 2025")

# Ventas por semestre
st.subheader("🧾 Resumen por Semestre")

# Totales por semestre
semestres = df.groupby(['Año', 'Semestre'])['Monto'].sum().unstack(fill_value=0)
s1_2024 = semestres.loc[2024, 1] if 2024 in semestres.index else 0
s2_2024 = semestres.loc[2024, 2] if 2024 in semestres.index else 0
s1_2025 = semestres.loc[2025, 1] if 2025 in semestres.index else 0
s2_2025 = semestres.loc[2025, 2] if 2025 in semestres.index else 0

# Mostrar métricas de cada semestre
col1, col2, col3, col4 = st.columns(4)
col1.metric("Semestre 1 - 2024", f"${s1_2024:,.0f}")
col2.metric("Semestre 1 - 2025", f"${s1_2025:,.0f}")
col3.metric("Semestre 2 - 2024", f"${s2_2024:,.0f}")
col4.metric("Semestre 2 - 2025", f"${s2_2025:,.0f}")

# Comparativo anual
st.subheader("📊 Comparativo Total Anual")

total_2024 = s1_2024 + s2_2024
total_2025 = s1_2025 + s2_2025
falta = total_2024 - total_2025
porcentaje = (falta / total_2024 * 100) if total_2024 > 0 else 0

# Dinámica de color e ícono
if falta > 0:
    delta = f"-{porcentaje:.1f}%"
    texto_falta = f"${falta:,.0f}"
else:
    delta = "✅ Superado"
    texto_falta = "🎉"

col5, col6, col7 = st.columns(3)
col5.metric("Total 2024", f"${total_2024:,.0f}")
col6.metric("Total 2025", f"${total_2025:,.0f}")
col7.metric("Falta para superar 2024", texto_falta, delta)

# Ventas mensuales
# Agrupar ventas por mes y año
monthly = df.groupby(['Mes', 'Año'])['Monto'].sum().reset_index()

# Convertir año a string para que Plotly lo trate como categoría
monthly['Año'] = monthly['Año'].astype(str)

# Mostrar gráfico de barras agrupadas
st.subheader("📅 Ventas Mensuales Comparativas")

fig_month_bar = px.bar(
    monthly,
    x='Mes',
    y='Monto',
    color='Año',
    barmode='group',
    text_auto='.2s',
    title='Comparación mensual de ventas entre 2024 y 2025',
    labels={'Monto': 'Monto', 'Mes': 'Mes'}
)

fig_month_bar.update_layout(
    xaxis=dict(tickmode='linear', tick0=1, dtick=1),
    bargap=0.25
)

st.plotly_chart(fig_month_bar)

# # Ventas Ene-Mar por Fuente
# first3_2025 = df[(df['Año']==2025) & (df['Mes']<=3)]
# source_3m = first3_2025.groupby('Fuente')['Monto'].sum().reset_index()
# st.subheader("Ventas Ene-Mar 2025 por Fuente")
# st.plotly_chart(px.bar(source_3m, x='Fuente', y='Monto', title='Ventas Ene-Mar por Fuente'))

# Análisis de SKUs
skus_2024 = set(df[df['Año']==2024]['SKU'])
skus_2025 = set(df[df['Año']==2025]['SKU'])
nuevo_count = len(skus_2025 - skus_2024)
aband_count = len(skus_2024 - skus_2025)
const_count = len(skus_2024 & skus_2025)
st.subheader("Análisis de SKUs")
col1, col2, col3 = st.columns(3)
col1.metric("Nuevos", nuevo_count)
col2.metric("Abandonados", aband_count)
col3.metric("Mantenidos del 2024", const_count)

# Cambios en SKUs por cliente
# Agrupar los SKUs comprados por cliente y año
client_sku_2024 = df[df['Año'] == 2024].groupby('Cliente')['SKU'].apply(set)
client_sku_2025 = df[df['Año'] == 2025].groupby('Cliente')['SKU'].apply(set)

# Unir todos los clientes
todos_los_clientes = sorted(set(client_sku_2024.index).union(client_sku_2025.index))

# Construir tabla
records = []
for client in todos_los_clientes:
    s24 = client_sku_2024.get(client, set())
    s25 = client_sku_2025.get(client, set())
    total_2024 = len(s24)
    total_2025 = len(s25)
    nuevos = len(s25 - s24)
    abandonados = len(s24 - s25)
    constantes = len(s24 & s25)
    records.append((client, total_2024, total_2025, nuevos, abandonados, constantes))

client_change = pd.DataFrame(records, columns=[
    'Cliente', '#SKUs 2024', '#SKUs 2025', 'Nuevos', 'Abandonados', 'Constantes'
])

# Mostrar en Streamlit
st.subheader("Cambios en SKUs por Cliente")
st.dataframe(client_change)

st.subheader("📈 Crecimiento por Cliente y Vendedor (Solo Semestre 1)")

# Filtrar solo semestre 1
sem1_df = df[df['Semestre'] == 1]

# --- CLIENTES SEMESTRE 1 ---
client_sem1 = sem1_df.groupby(['Cliente', 'Año'])['Monto'].sum().unstack(fill_value=0).reset_index()
client_sem1 = client_sem1.rename(columns={2024: 'Monto 2024', 2025: 'Monto 2025'})

# Calcular crecimiento
client_sem1['% Crecimiento'] = ((client_sem1['Monto 2025'] - client_sem1['Monto 2024']) /
                                client_sem1['Monto 2024'].replace(0, pd.NA)) * 100

# Separar nuevos de existentes
nuevos = client_sem1[client_sem1['% Crecimiento'].isna()].copy()
existentes = client_sem1[client_sem1['% Crecimiento'].notna()].copy()

# Formato
existentes['% Crecimiento'] = existentes['% Crecimiento'].round(2)
nuevos['% Crecimiento'] = "Cliente nuevo"

# Contar
st.metric("🆕 Clientes nuevos en 2025 (Semestre 1)", len(nuevos))

# Mostrar tablas separadas
st.subheader("👥 Crecimiento por Cliente (Semestre 1)")
st.dataframe(existentes[['Cliente', 'Monto 2024', 'Monto 2025', '% Crecimiento']].sort_values(by='% Crecimiento', ascending=False))

st.subheader("🆕 Clientes Nuevos en 2025 (Semestre 1)")
st.dataframe(nuevos[['Cliente', 'Monto 2024', 'Monto 2025', '% Crecimiento']].sort_values(by='Monto 2025', ascending=False))

# -------------------- VENDEDORES --------------------
vend_sem1 = sem1_df.groupby(['Vendedor', 'Año'])['Monto'].sum().unstack(fill_value=0).reset_index()
vend_sem1 = vend_sem1.rename(columns={2024: 'Monto 2024', 2025: 'Monto 2025'})
vend_sem1['% Crecimiento'] = ((vend_sem1['Monto 2025'] - vend_sem1['Monto 2024']) /
                              vend_sem1['Monto 2024'].replace(0, pd.NA)) * 100

st.subheader("🧑‍💼 Crecimiento por Vendedor (Semestre 1)")
st.dataframe(vend_sem1[['Vendedor', 'Monto 2024', 'Monto 2025', '% Crecimiento']])

# =========================
# ANÁLISIS DETALLADO - CLIENTE
# =========================
with st.expander("🧭 Análisis detallado por Cliente"):
    st.markdown("Selecciona un cliente para ver su historial comparativo 2024 vs 2025, estado (nuevo / no ha comprado), vendedor asignado, SKUs y evolución mensual.")

    # --- Validar columnas mínimas ---
    required_cols = ['Cliente', 'Año', 'Mes', 'Monto', 'SKU']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        st.error(f"Faltan columnas requeridas para el análisis por cliente: {missing}")
    else:
        # Lista completa de clientes (orden alfabético)
        clientes = sorted(df['Cliente'].dropna().unique())
        sel_cliente = st.selectbox("Elige un cliente:", clientes, index=0)

        # Filtrado
        df_c = df[df['Cliente'] == sel_cliente].copy()

        # Totales por año
        total_2024_c = df_c.loc[df_c['Año'] == 2024, 'Monto'].sum()
        total_2025_c = df_c.loc[df_c['Año'] == 2025, 'Monto'].sum()

        # Estado del cliente
        compro_2024 = total_2024_c > 0
        compro_2025 = total_2025_c > 0
        if (not compro_2024) and compro_2025:
            estado_cliente = "🆕 **Cliente nuevo (primera compra en 2025)**"
        elif compro_2024 and (not compro_2025):
            estado_cliente = "⛔ **No ha comprado en 2025**"
        else:
            estado_cliente = "✔️ Cliente con compras en ambos años" if (compro_2024 and compro_2025) else "— Sin compras registradas"

        st.markdown(estado_cliente)

        # Vendedor(es) asociado(s)
        if 'Vendedor' in df_c.columns:
            vendedores_cliente = sorted(df_c['Vendedor'].dropna().unique())
            vendedores_str = ", ".join(map(str, vendedores_cliente)) if vendedores_cliente else "—"
        else:
            vendedores_str = "No disponible"
        st.markdown(f"**Vendedor(es):** {vendedores_str}")

        st.markdown("---")

        # ----- Métricas Totales -----
        falta_c = total_2024_c - total_2025_c
        if total_2024_c > 0:
            pct_falta_c = falta_c / total_2024_c * 100
        else:
            pct_falta_c = 0

        colA, colB, colC = st.columns(3)
        colA.metric("Total 2024", f"${total_2024_c:,.0f}")
        colB.metric("Total 2025", f"${total_2025_c:,.0f}")
        if falta_c > 0:
            colC.metric("Falta para superar 2024", f"${falta_c:,.0f}", f"-{pct_falta_c:.1f}%")
        else:
            colC.metric("Falta para superar 2024", "🎉", "✅ Superado")

        st.markdown("---")

        # ----- Gráfico mensual del cliente -----
        monthly_c = (df_c.groupby(['Mes', 'Año'])['Monto']
                        .sum()
                        .reset_index())
        monthly_c['Año'] = monthly_c['Año'].astype(str)

        fig_month_c = px.bar(
            monthly_c,
            x='Mes',
            y='Monto',
            color='Año',
            barmode='group',
            text_auto='.2s',
            title=f"Ventas mensuales de {sel_cliente} (2024 vs 2025)",
            labels={'Mes': 'Mes', 'Monto': 'Monto'}
        )
        fig_month_c.update_layout(
            height=400,
            xaxis=dict(tickmode='linear', tick0=1, dtick=1),
            margin=dict(t=50, b=40)
        )
        st.plotly_chart(fig_month_c, use_container_width=True)

        st.markdown("---")

        # ----- Resumen SKUs -----
        skus_2024_c = set(df_c.loc[df_c['Año'] == 2024, 'SKU'])
        skus_2025_c = set(df_c.loc[df_c['Año'] == 2025, 'SKU'])
        nuevos_c = skus_2025_c - skus_2024_c
        abandonados_c = skus_2024_c - skus_2025_c
        constantes_c = skus_2024_c & skus_2025_c

        colS1, colS2, colS3, colS4, colS5 = st.columns(5)
        colS1.metric("#SKUs 2024", len(skus_2024_c))
        colS2.metric("#SKUs 2025", len(skus_2025_c))
        colS3.metric("Nuevos", len(nuevos_c))
        colS4.metric("Abandonados", len(abandonados_c))
        colS5.metric("Constantes", len(constantes_c))

        st.markdown("#### Detalle de SKUs")

        # Selector de vista SKU
        sku_view = st.radio(
            "¿Qué SKUs quieres ver?",
            options=["2024", "2025", "Nuevos", "Abandonados", "Constantes"],
            horizontal=True
        )

        # Función para armar tabla SKU detallada
        def _tabla_sku(df_filtrado):
            """
            Devuelve dataframe con SKU + métricas (Monto, Cantidad si existe).
            """
            cols_agg = {'Monto': 'sum'}
            if 'Cantidad' in df_filtrado.columns:
                cols_agg['Cantidad'] = 'sum'
            t = df_filtrado.groupby('SKU').agg(cols_agg).reset_index()
            # Orden monto descendente
            t = t.sort_values('Monto', ascending=False)
            return t

        if sku_view == "2024":
            df_s = df_c[df_c['Año'] == 2024]
            st.caption("SKUs comprados en 2024.")
            st.dataframe(_tabla_sku(df_s))
        elif sku_view == "2025":
            df_s = df_c[df_c['Año'] == 2025]
            st.caption("SKUs comprados en 2025.")
            st.dataframe(_tabla_sku(df_s))
        elif sku_view == "Nuevos":
            df_s = df_c[(df_c['Año'] == 2025) & (df_c['SKU'].isin(nuevos_c))]
            st.caption("SKUs nuevos (comprados en 2025, no en 2024).")
            st.dataframe(_tabla_sku(df_s))
        elif sku_view == "Abandonados":
            df_s = df_c[(df_c['Año'] == 2024) & (df_c['SKU'].isin(abandonados_c))]
            st.caption("SKUs abandonados (comprados en 2024, no en 2025).")
            st.dataframe(_tabla_sku(df_s))
        else:  # Constantes
            df_s_24 = df_c[(df_c['Año'] == 2024) & (df_c['SKU'].isin(constantes_c))]
            df_s_25 = df_c[(df_c['Año'] == 2025) & (df_c['SKU'].isin(constantes_c))]

            # Unir montos 2024/2025 por SKU
            t24 = df_s_24.groupby('SKU')['Monto'].sum().rename('Monto 2024')
            t25 = df_s_25.groupby('SKU')['Monto'].sum().rename('Monto 2025')
            t = pd.concat([t24, t25], axis=1).fillna(0).reset_index()
            t['% Cambio'] = ((t['Monto 2025'] - t['Monto 2024']) /
                             t['Monto 2024'].replace(0, pd.NA)) * 100
            t['% Cambio'] = t['% Cambio'].round(2)
            st.caption("SKUs constantes (comprados en ambos años).")
            st.dataframe(t)

# =========================
# ANÁLISIS DETALLADO - VENDEDOR
# =========================
with st.expander("👤 Análisis detallado por Vendedor"):
    st.markdown("Selecciona un vendedor para ver su desempeño, evolución mensual, y los SKUs vendidos en 2024 vs 2025.")

    if 'Vendedor' not in df.columns:
        st.error("⚠️ No se encontró una columna de 'Vendedor' en el DataFrame.")
    else:
        # Lista de vendedores
        vendedores = sorted(df['Vendedor'].dropna().unique())
        sel_vendedor = st.selectbox("Elige un vendedor:", vendedores)

        df_v = df[df['Vendedor'] == sel_vendedor].copy()

        # Totales por año
        total_2024_v = df_v[df_v['Año'] == 2024]['Monto'].sum()
        total_2025_v = df_v[df_v['Año'] == 2025]['Monto'].sum()

        # Estado vendedor
        vend_2024 = total_2024_v > 0
        vend_2025 = total_2025_v > 0
        if not vend_2024 and vend_2025:
            estado_v = "🆕 **Vendedor nuevo (solo ha vendido en 2025)**"
        elif vend_2024 and not vend_2025:
            estado_v = "⛔ **No ha vendido en 2025**"
        else:
            estado_v = "✔️ Ventas en ambos años" if vend_2024 and vend_2025 else "— Sin ventas"

        st.markdown(estado_v)

        # Clientes atendidos
        clientes_v = sorted(df_v['Cliente'].dropna().unique())
        st.markdown(f"**Clientes atendidos:** {len(clientes_v)}")

        st.markdown("---")

        # Métricas
        falta_v = total_2024_v - total_2025_v
        if total_2024_v > 0:
            pct_falta_v = falta_v / total_2024_v * 100
        else:
            pct_falta_v = 0

        colV1, colV2, colV3 = st.columns(3)
        colV1.metric("Total 2024", f"${total_2024_v:,.0f}")
        colV2.metric("Total 2025", f"${total_2025_v:,.0f}")
        if falta_v > 0:
            colV3.metric("Falta para superar 2024", f"${falta_v:,.0f}", f"-{pct_falta_v:.1f}%")
        else:
            colV3.metric("Falta para superar 2024", "🎉", "✅ Superado")

        st.markdown("---")

        # Gráfico mensual
        monthly_v = df_v.groupby(['Mes', 'Año'])['Monto'].sum().reset_index()
        monthly_v['Año'] = monthly_v['Año'].astype(str)

        fig_v = px.bar(
            monthly_v,
            x='Mes',
            y='Monto',
            color='Año',
            barmode='group',
            text_auto='.2s',
            title=f"Ventas mensuales de {sel_vendedor} (2024 vs 2025)"
        )
        fig_v.update_layout(
            height=400,
            xaxis=dict(tickmode='linear', tick0=1, dtick=1),
            margin=dict(t=50, b=40)
        )
        st.plotly_chart(fig_v, use_container_width=True)

        st.markdown("---")

        # SKUs vendidos
        skus_2024_v = set(df_v[df_v['Año'] == 2024]['SKU'])
        skus_2025_v = set(df_v[df_v['Año'] == 2025]['SKU'])

        nuevos_v = skus_2025_v - skus_2024_v
        abandonados_v = skus_2024_v - skus_2025_v
        constantes_v = skus_2024_v & skus_2025_v

        colVS1, colVS2, colVS3, colVS4, colVS5 = st.columns(5)
        colVS1.metric("#SKUs 2024", len(skus_2024_v))
        colVS2.metric("#SKUs 2025", len(skus_2025_v))
        colVS3.metric("Nuevos", len(nuevos_v))
        colVS4.metric("Abandonados", len(abandonados_v))
        colVS5.metric("Constantes", len(constantes_v))

        st.markdown("#### Detalle de SKUs vendidos")

        view_v = st.radio(
            "¿Qué SKUs quieres ver?",
            options=["2024", "2025", "Nuevos", "Abandonados", "Constantes"],
            horizontal=True,
            key="vendedor_skus"
        )

        def _tabla_sku_v(df_sub):
            cols = {'Monto': 'sum'}
            if 'Cantidad' in df_sub.columns:
                cols['Cantidad'] = 'sum'
            t = df_sub.groupby('SKU').agg(cols).reset_index()
            t = t.sort_values('Monto', ascending=False)
            return t

        if view_v == "2024":
            df_s = df_v[df_v['Año'] == 2024]
            st.caption("SKUs vendidos en 2024.")
            st.dataframe(_tabla_sku_v(df_s))
        elif view_v == "2025":
            df_s = df_v[df_v['Año'] == 2025]
            st.caption("SKUs vendidos en 2025.")
            st.dataframe(_tabla_sku_v(df_s))
        elif view_v == "Nuevos":
            df_s = df_v[(df_v['Año'] == 2025) & (df_v['SKU'].isin(nuevos_v))]
            st.caption("SKUs nuevos (vendidos solo en 2025).")
            st.dataframe(_tabla_sku_v(df_s))
        elif view_v == "Abandonados":
            df_s = df_v[(df_v['Año'] == 2024) & (df_v['SKU'].isin(abandonados_v))]
            st.caption("SKUs abandonados (vendidos en 2024 pero no en 2025).")
            st.dataframe(_tabla_sku_v(df_s))
        else:
            df_24 = df_v[(df_v['Año'] == 2024) & (df_v['SKU'].isin(constantes_v))]
            df_25 = df_v[(df_v['Año'] == 2025) & (df_v['SKU'].isin(constantes_v))]

            t24 = df_24.groupby('SKU')['Monto'].sum().rename('Monto 2024')
            t25 = df_25.groupby('SKU')['Monto'].sum().rename('Monto 2025')
            t = pd.concat([t24, t25], axis=1).fillna(0).reset_index()
            t['% Cambio'] = ((t['Monto 2025'] - t['Monto 2024']) /
                             t['Monto 2024'].replace(0, pd.NA)) * 100
            t['% Cambio'] = t['% Cambio'].round(2)
            st.caption("SKUs constantes (vendidos en ambos años).")
            st.dataframe(t)

