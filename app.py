import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import os
import calendar

# Configuración de la página
st.set_page_config(page_title="Alo - Control de Ventas y Cartera", layout="wide")

# Archivo local para persistencia de datos
DB_FILE = "base_datos_alo_ventas.json"

MARCAS_CELULARES = ["Samsung", "Motorola", "Xiaomi", "Oppo", "Realme", "Infinix", "Honor", "Tecno", "Vivo", "Nubia"]

# Inicializar datos por defecto
def cargar_datos():
    if os.path.exists(DB_FILE):
        try:
            df_base = pd.read_json(DB_FILE)
            return {
                "ventas": df_base.get("ventas", pd.Series([[]])).iloc[0] if "ventas" in df_base else [],
                "meta_unidades": int(df_base.get("meta_unidades", pd.Series([100])).iloc[0]) if "meta_unidades" in df_base else 100
            }
        except Exception:
            pass
    return {
        "ventas": [],
        "meta_unidades": 100
    }

def guardar_datos(data):
    df = pd.DataFrame([data])
    df.to_json(DB_FILE)

db = cargar_datos()

# Inicializar sesión de administrador para cartera y admin
if "cartera_autenticado" not in st.session_state:
    st.session_state["cartera_autenticado"] = False

st.sidebar.title("Menú Principal - Alo")
menu = st.sidebar.radio("Ir a:", [
    "Dashboard", 
    "Registro de Ventas", 
    "Gestión de Cartera",
    "Módulo Admin"
])

st.sidebar.markdown("---")
st.sidebar.info(f"Mes Actual: {datetime.date.today().strftime('%B %Y')}")

# ================= 1. DASHBOARD =================
if menu == "Dashboard":
    st.title("📊 Dashboard General - Alo")
    st.markdown("---")
    
    ventas = db["ventas"]
    total_unidades = len(ventas)
    meta_uni = db["meta_unidades"]
    
    cumplimiento_uni = (total_unidades / meta_uni * 100) if meta_uni > 0 else 0
    
    hoy = datetime.date.today()
    dia_actual = hoy.day
    _, total_dias_mes = calendar.monthrange(hoy.year, hoy.month)
    
    proyeccion_uni = int((total_unidades / dia_actual * total_dias_mes)) if dia_actual > 0 else 0
    proyeccion_cumplimiento = (proyeccion_uni / meta_uni * 100) if meta_uni > 0 else 0
    unidades_restantes = max(0, meta_uni - total_unidades)

    col1, col2, col3 = st.columns(3)
    col1.metric("Meta del Mes", f"{meta_uni} unds")
    col2.metric("Ventas a la Fecha", f"{total_unidades} unds", f"{cumplimiento_uni:.1f}% Cumplimiento")
    col3.metric("Proyección de Cumplimiento", f"{proyeccion_cumplimiento:.1f}%")

    col4, col5 = st.columns(2)
    col4.metric("Proyección de Unidades", f"{proyeccion_uni} unds")
    col5.metric("Unidades Faltantes", f"{unidades_restantes} unds")

    st.markdown("---")
    if ventas:
        df_dash = pd.DataFrame(ventas)
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Ventas por Marca")
            fig_marca = px.pie(df_dash, names="marca", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_marca, use_container_width=True)
        with c2:
            st.subheader("Ventas por Día")
            df_fechas = df_dash.groupby("fecha").size().reset_index(name="cantidad")
            fig_fecha = px.bar(df_fechas, x="fecha", y="cantidad", title="Unidades Registradas por Fecha")
            st.plotly_chart(fig_fecha, use_container_width=True)
    else:
        st.info("Aún no hay ventas registradas para mostrar gráficos.")

# ================= 2. REGISTRO DE VENTAS =================
elif menu == "Registro de Ventas":
    st.title("🛒 Módulo de Registro de Ventas")
    st.markdown("---")
    
    with st.form("form_registro_venta", clear_on_submit=True):
        fecha_venta = st.date_input("Fecha de la venta:", datetime.date.today())
        nombre_cliente = st.text_input("Nombre del cliente:")
        documento = st.text_input("Documento:")
        telefono = st.text_input("Teléfono de contacto:")
        marca = st.selectbox("Marca:", MARCAS_CELULARES)
        modelo = st.text_input("Modelo:")
        imei = st.text_input("IMEI:")
        valor_cuota = st.number_input("Valor de cuota:", min_value=0.0, step=1000.0)
        
        btn_guardar = st.form_submit_button("Registrar Venta")
        
        if btn_guardar:
            if not nombre_cliente or not documento or not imei or not modelo:
                st.error("Por favor completa los campos obligatorios (Cliente, Documento, IMEI, Modelo).")
            else:
                nueva_venta = {
                    "id": int(datetime.datetime.now().timestamp() * 1000),
                    "fecha": str(fecha_venta),
                    "nombreCliente": nombre_cliente,
                    "documento": documento,
                    "telefono": telefono,
                    "marca": marca,
                    "modelo": modelo,
                    "imei": imei,
                    "valorCuota": valor_cuota,
                    "pagado": False,
                    "fechaPagoRealizado": None
                }
                db["ventas"].append(nueva_venta)
                guardar_datos(db)
                st.success("¡Venta registrada con éxito!")

# ================= 3. GESTIÓN DE CARTERA (PROTEGIDO) =================
elif menu == "Gestión de Cartera":
    st.title("💰 Módulo Gestión de Cartera")
    st.markdown("⚠️ *Sección protegida con contraseña de administrador.*")
    
    if not st.session_state["cartera_autenticado"]:
        pass_cartera = st.text_input("Ingrese la Contraseña de Administrador", type="password", key="pass_mod_cartera")
        if pass_cartera == "admin123":
            st.session_state["cartera_autenticado"] = True
            st.rerun()
        elif pass_cartera != "":
            st.error("Contraseña incorrecta.")
            
    if st.session_state["cartera_autenticado"]:
        st.success("Acceso concedido al módulo de cartera.")
        if st.button("🔒 Cerrar Sesión de Cartera"):
            st.session_state["cartera_autenticado"] = False
            st.rerun()
            
        st.markdown("---")
        
        if not db["ventas"]:
            st.info("No hay ventas registradas para gestionar cartera.")
        else:
            hoy_date = datetime.date.today()
            
            lista_hoy = []
            lista_mora = []
            lista_general = []
            
            for idx, v in enumerate(db["ventas"]):
                f_venta = datetime.datetime.strptime(v["fecha"], "%Y-%m-%d").date()
                f_pago_objetivo = f_venta + datetime.timedelta(days=14)
                
                estado = "Al día"
                if v["pagado"]:
                    estado = "Pagado"
                elif hoy_date == f_pago_objetivo:
                    estado = "Debe pagar hoy"
                    lista_hoy.append((idx, v))
                elif hoy_date > f_pago_objetivo:
                    estado = "En mora"
                    lista_mora.append((idx, v))
                else:
                    estado = "Pendiente de primer pago"
                    
                v_gen = v.copy()
                v_gen["estadoCartera"] = estado
                v_gen["fechaPagoEsperada"] = str(f_pago_objetivo)
                lista_general.append(v_gen)

            tab1, tab2, tab3 = st.tabs(["🟢 Deben Pagar Hoy", "🔴 En Mora", "📋 Lista General y Filtros"])
            
            with tab1:
                st.subheader("Clientes que deben pagar hoy (Día 14)")
                if not lista_hoy:
                    st.info("No hay clientes programados para pago el día de hoy.")
                else:
                    for idx, cliente in lista_hoy:
                        col_info, col_btn = st.columns([4, 1])
                        with col_info:
                            st.write(f"**Cliente:** {cliente['nombreCliente']} | **Doc:** {cliente['documento']} | **Tel:** {cliente['telefono']} | **Cuota:** ${cliente['valorCuota']:,.0f} | **Modelo:** {cliente['modelo']}")
                        with col_btn:
                            if st.button("Marcar que pagó", key=f"pago_hoy_{idx}"):
                                db["ventas"][idx]["pagado"] = True
                                db["ventas"][idx]["fechaPagoRealizado"] = str(hoy_date)
                                guardar_datos(db)
                                st.success(f"¡Pago registrado para {cliente['nombreCliente']}!")
                                st.rerun()
                                
            with tab2:
                st.subheader("Clientes en Mora (Más de 14 días sin pago)")
                if not lista_mora:
                    st.info("¡Excelente! No hay clientes en mora.")
                else:
                    for idx, cliente in lista_mora:
                        col_info, col_btn = st.columns([4, 1])
                        with col_info:
                            f_v = datetime.datetime.strptime(cliente["fecha"], "%Y-%m-%d").date()
                            dias_transcurridos = (hoy_date - (f_v + datetime.timedelta(days=14))).days
                            st.write(f"**Cliente:** {cliente['nombreCliente']} | **Doc:** {cliente['documento']} | **Tel:** {cliente['telefono']} | **Atraso:** {dias_transcurridos} días | **Cuota:** ${cliente['valorCuota']:,.0f}")
                        with col_btn:
                            if st.button("Ya realizó su pago", key=f"pago_mora_{idx}"):
                                db["ventas"][idx]["pagado"] = True
                                db["ventas"][idx]["fechaPagoRealizado"] = str(hoy_date)
                                guardar_datos(db)
                                st.success(f"¡Pago registrado y sacado de mora para {cliente['nombreCliente']}!")
                                st.rerun()
                                
            with tab3:
                st.subheader("Lista General de Cartera y Filtros")
                df_gen = pd.DataFrame(lista_general)
                
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    busqueda_doc = st.text_input("Buscar por Documento del Cliente:")
                with col_b2:
                    filtro_estado = st.selectbox("Filtrar por Estado:", ["TODOS", "Al día", "Pendiente de primer pago", "Debe pagar hoy", "En mora", "Pagado"])
                
                df_filtrado = df_gen.copy()
                if busqueda_doc.strip():
                    df_filtrado = df_filtrado[df_filtrado["documento"].astype(str).str.contains(busqueda_doc.strip(), case=False, na=False)]
                if filtro_estado != "TODOS":
                    df_filtrado = df_filtrado[df_filtrado["estadoCartera"] == filtro_estado]
                    
                st.markdown(f"**Resultados encontrados:** {len(df_filtrado)}")
                st.dataframe(df_filtrado[["fecha", "nombreCliente", "documento", "telefono", "marca", "modelo", "imei", "valorCuota", "fechaPagoEsperada", "estadoCartera"]], use_container_width=True)

# ================= 4. MÓDULO ADMIN =================
elif menu == "Módulo Admin":
    st.title("⚙️ Módulo de Administración - Alo")
    st.markdown("---")
    
    password_admin = st.text_input("Contraseña de Administrador", type="password")
    
    if password_admin == "admin123":
        st.success("Acceso concedido.")
        st.markdown("---")
        
        with st.form("form_meta_alo"):
            nueva_meta = st.number_input("Meta de Unidades del Mes", value=int(db["meta_unidades"]), step=1)
            btn_m = st.form_submit_button("Actualizar Meta")
            if btn_m:
                db["meta_unidades"] = int(nueva_meta)
                guardar_datos(db)
                st.success("¡Meta actualizada correctamente!")
                
        st.markdown("---")
        st.subheader("🗑️ Eliminar Venta o Crédito Mal Registrado")
        if db["ventas"]:
            st.markdown("Ingresa el **ID** único de la venta que deseas eliminar (puedes ver el ID en el listado de abajo):")
            id_eliminar = st.number_input("ID de la venta a eliminar:", step=1, format="%d")
            if st.button("Eliminar Venta Seleccionada"):
                antes = len(db["ventas"])
                db["ventas"] = [v for v in db["ventas"] if v.get("id") != int(id_eliminar)]
                if len(db["ventas"]) < antes:
                    guardar_datos(db)
                    st.success("¡Venta/Crédito eliminado correctamente del sistema!")
                    st.rerun()
                else:
                    st.error("No se encontró ninguna venta con ese ID.")
        else:
            st.info("No hay ventas registradas para eliminar.")
                
        st.markdown("---")
        st.subheader("Base de Datos General de Ventas")
        if db["ventas"]:
            st.dataframe(pd.DataFrame(db["ventas"]), use_container_width=True)
        else:
            st.info("No hay ventas registradas.")
    elif password_admin != "":
        st.error("Contraseña incorrecta.")
        
