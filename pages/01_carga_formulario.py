"""
01_carga_formulario.py — Carga de nuevos formularios de gasto.
"""
import streamlit as st
from sqlalchemy import text
from datetime import datetime, timezone, timedelta, date
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import require_page_access, get_connection, fmt_currency

#-----------agregar CSS----------------------------------------------   

st.markdown("""
<style>
    /* ── Fondo general ─────────────────────────────────────────── */
    .stApp {
        background-color: #f0f4f8;
    }

    /* ── Título principal ──────────────────────────────────────── */
    h1 {
        color: #1a3a5c;
        font-weight: 700;
        border-bottom: 3px solid #2e86de;
        padding-bottom: 10px;
    }

    /* ── Subtítulos ────────────────────────────────────────────── */
    h2, h3 {
        color: #2e86de;
        font-weight: 600;
        margin-top: 1.2rem;
    }

    /* ── Campos de texto y selectbox ───────────────────────────── */
    div[data-testid="stTextInput"] input,
    div[data-testid="stNumberInput"] input,
    div[data-testid="stTextArea"] textarea,
    div[data-testid="stSelectbox"] select {
        background-color: #ffffff;
        border: 1.5px solid #ccd6e0;
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 0.95rem;
        transition: border-color 0.2s;
    }

    div[data-testid="stTextInput"] input:focus,
    div[data-testid="stNumberInput"] input:focus,
    div[data-testid="stTextArea"] textarea:focus {
        border-color: #2e86de;
        box-shadow: 0 0 0 3px rgba(46,134,222,0.15);
    }

    /* ── Campos deshabilitados ─────────────────────────────────── */
    div[data-testid="stTextInput"] input:disabled {
        background-color: #eef2f7;
        color: #555;
        border-color: #dce3ea;
    }

    /* ── Labels de campos ──────────────────────────────────────── */
    label[data-testid="stWidgetLabel"] p {
        font-weight: 600;
        color: #2c3e50;
        font-size: 0.9rem;
    }

    /* ── Botón principal ───────────────────────────────────────── */
    div[data-testid="stButton"] button[kind="primary"] {
        background: linear-gradient(135deg, #1a3a5c, #2e86de);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 12px 24px;
        font-size: 1rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        transition: transform 0.15s, box-shadow 0.15s;
        box-shadow: 0 4px 12px rgba(46,134,222,0.3);
    }

    div[data-testid="stButton"] button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 18px rgba(46,134,222,0.4);
    }

    div[data-testid="stButton"] button[kind="primary"]:active {
        transform: translateY(0);
    }

    /* ── Botones secundarios ───────────────────────────────────── */
    div[data-testid="stButton"] button[kind="secondary"] {
        border-radius: 8px;
        border: 1.5px solid #2e86de;
        color: #2e86de;
        font-weight: 600;
        transition: all 0.15s;
    }

    div[data-testid="stButton"] button[kind="secondary"]:hover {
        background-color: #e8f4fd;
    }

    /* ── Cajas info / warning / success / error ─────────────────── */
    div[data-testid="stAlert"] {
        border-radius: 10px;
        border-left-width: 5px;
    }

    /* ── Contenedores / secciones ──────────────────────────────── */
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }

    /* ── Divisores ─────────────────────────────────────────────── */
    hr {
        border: none;
        border-top: 2px solid #e0e8f0;
        margin: 1.5rem 0;
    }

    /* ── Checkbox ──────────────────────────────────────────────── */
    div[data-testid="stCheckbox"] label {
        font-weight: 500;
        color: #2c3e50;
    }

    /* ── Sidebar ───────────────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background-color: #1a3a5c;
    }

    section[data-testid="stSidebar"] * {
        color: #e8f0fe !important;
    }

    section[data-testid="stSidebar"] .stButton button {
        background-color: rgba(255,255,255,0.1);
        border: 1px solid rgba(255,255,255,0.3);
        color: white !important;
        border-radius: 8px;
    }

    section[data-testid="stSidebar"] .stButton button:hover {
        background-color: rgba(255,255,255,0.2);
    }

    /* ── Métricas ──────────────────────────────────────────────── */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.07);
        border-left: 4px solid #2e86de;
    }

    div[data-testid="stMetricLabel"] {
        font-size: 0.85rem;
        color: #6b7280;
    }

    div[data-testid="stMetricValue"] {
        font-size: 1.6rem;
        font-weight: 700;
        color: #1a3a5c;
    }
</style>
""", unsafe_allow_html=True)




# ─── Clave para resetear el formulario ────────────────────────────────────
if "form_version" not in st.session_state:
    st.session_state.form_version = 0
if "formulario_guardado" not in st.session_state:
    st.session_state.formulario_guardado = False
require_page_access("formulario")

FECHA_LIMITE = datetime(2026, 5, 6, 8, 00, 0, tzinfo=timezone(timedelta(hours=-3)))
ahora = datetime.now(timezone(timedelta(hours=-3)))

if ahora > FECHA_LIMITE:
    st.error(f"🚫 La carga de formularios solo estaba habilitada hasta el **{FECHA_LIMITE.strftime('%d/%m/%Y a las %H:%M')} hs.**")
    st.stop()

st.title("📝 Carga de Formulario")
st.warning(f"⏰ Fecha límite de carga: **{FECHA_LIMITE.strftime('%d/%m/%Y a las %H:%M')} hs.**")


# Mostrar mensaje de éxito si viene de un submit exitoso
if "success_msg" in st.session_state and st.session_state.success_msg:
    st.success(st.session_state.success_msg)
    st.session_state.success_msg = ""
    st.balloons()

st.divider()
#st.divider()

conn = get_connection()

user_id = st.session_state.get("user_id")
df_user = conn.query(
    "SELECT nombre_apellido, secretaria, sub_secretaria FROM usuarios WHERE id = :id",
    params={"id": user_id}, ttl=0
)

if df_user.empty:
    st.error("No se pudieron cargar los datos del usuario.")
    st.stop()

usuario_datos       = df_user.iloc[0]
secretaria_auto     = str(usuario_datos["secretaria"]     or "").strip()
sub_secretaria_auto = str(usuario_datos["sub_secretaria"] or "").strip()
nombre_auto         = str(usuario_datos["nombre_apellido"] or "").strip()

# ─── Datos del Solicitante ─────────────────────────────────────────────────
st.subheader("📌 Datos del Solicitante")
col1, col2, col3 = st.columns(3)
with col1:
    st.text_input("Nombre del Solicitante", value=nombre_auto, disabled=True)
with col2:
    st.text_input("Secretaría", value=secretaria_auto or "Sin secretaría asignada", disabled=True)
with col3:
    st.text_input("Sub Secretaría", value=sub_secretaria_auto or "—", disabled=True)

# ─── Inicializar items ────────────────────────────────────────────────────
if "items_count" not in st.session_state or st.session_state.get("form_version", 0) != st.session_state.get("items_form_version", -1):
    st.session_state.items_count = 1
    st.session_state.items_form_version = st.session_state.get("form_version", 0)

# ─── Detalle del Bien o Servicio ───────────────────────────────────────────
st.subheader("🛒 Detalle del Bien o Servicio")

items = []
total_general = 0.0

for i in range(st.session_state.items_count):
    with st.container():
        if st.session_state.items_count > 1:
            st.markdown(f"**Ítem {i + 1}**")

        col4, col5 = st.columns([2, 1])
        with col4:
            bien = st.text_input(
                "Bien / Servicio *",
                placeholder="Ej: Resmas A4",
                key=f"bien_{i}_{st.session_state.form_version}"
            )
        with col5:
            unidad_opciones = ["Unidad", "Kilo", "Litro", "Horas", "Dias", "Otro"]
            unidad_sel = st.selectbox(
                "Unidad de Medida *",
                options=unidad_opciones,
                key=f"unidad_sel_{i}_{st.session_state.form_version}"
            )

        if unidad_sel == "Otro":
            unidad_manual = st.text_input(
                "✏️ Especificá la unidad",
                placeholder="Ej: Resma, Metro, Caja...",
                key=f"unidad_manual_{i}_{st.session_state.form_version}"
            )
            unidad_final = unidad_manual.strip()
        else:
            unidad_final = unidad_sel

        col6, col7 = st.columns(2)
        with col6:
            precio = st.number_input(
                "Precio Unitario ($) *",
                min_value=0.01, step=0.01, format="%.2f",
                key=f"precio_{i}_{st.session_state.form_version}"
            )
        with col7:
            cant = st.number_input(
                "Cantidad *",
                min_value=1, step=1,
                key=f"cant_{i}_{st.session_state.form_version}"
            )

        subtotal = precio * cant
        total_general += subtotal
        st.caption(f"Subtotal ítem {i + 1}: $ {subtotal:,.2f}")

        if st.session_state.items_count > 1:
            st.divider()

        items.append({
            "bien_servicio":  bien,
            "unidad_medida":  unidad_final,
            "precio_unitario": precio,
            "cantidad":        cant,
            "subtotal":        subtotal,
        })

# ─── Botones agregar/quitar ítem ───────────────────────────────────────────
col_add, col_del, col_space = st.columns([1, 1, 4])
with col_add:
    if st.button("➕ Agregar ítem", use_container_width=True):
        st.session_state.items_count += 1
        st.rerun()
with col_del:
    if st.session_state.items_count > 1:
        if st.button("➖ Quitar último", use_container_width=True):
            st.session_state.items_count -= 1
            st.rerun()

st.info(f"💰 **Total general estimado: $ {total_general:,.2f}**")

# ─── Clasificación ─────────────────────────────────────────────────────────
st.subheader("📋 Clasificación")
col8, col9 = st.columns(2)
with col8:
    tipo_gasto = st.selectbox(
    "Tipo de Gasto *",
    options=["Esencial", "Serv. Basico", "Politica del gobernador"],
    key=f"tipo_gasto_{st.session_state.form_version}"
    )
with col9:
    prioridad = st.selectbox(
    "Prioridad *",
    options=["Alta", "Media", "Baja"],
    key=f"prioridad_{st.session_state.form_version}"
    )

gasto_escuelas = st.checkbox(
    "🏫 ¿Es gasto destinado a Escuelas?",
    key=f"escuelas_{st.session_state.form_version}"
)

# ─── Fecha ─────────────────────────────────────────────────────────────────
st.subheader("📅 Fecha del Requerimiento")
fecha_requerimiento = st.date_input(
    "Fecha límite del requerimiento (opcional)",
    value=None, min_value=date.today(), format="DD/MM/YYYY",
    key=f"fecha_{st.session_state.form_version}"
)

# ─── Justificación ─────────────────────────────────────────────────────────
st.subheader("📄 Justificación")
justificacion = st.text_area(
    "Justificación del gasto *", height=120,
    placeholder="Describe brevemente por qué se requiere este gasto...",
    key=f"justificacion_{st.session_state.form_version}"
)

st.divider()

# ─── Submit ────────────────────────────────────────────────────────────────
if st.button("💾 Registrar Solicitud", type="primary", use_container_width=True):
    errors = []
    if not nombre_auto:
        errors.append("No se pudo identificar el solicitante.")
    if not secretaria_auto:
        errors.append("Tu usuario no tiene secretaría asignada. Contactá al administrador.")
    for idx, item in enumerate(items):
        if not item["bien_servicio"].strip():
            errors.append(f"El bien/servicio del ítem {idx + 1} es obligatorio.")
        if not item["unidad_medida"]:
            errors.append(f"La unidad de medida del ítem {idx + 1} es obligatoria.")
        if item["precio_unitario"] <= 0:
            errors.append(f"El precio del ítem {idx + 1} debe ser mayor a 0.")
        if item["cantidad"] <= 0:
            errors.append(f"La cantidad del ítem {idx + 1} debe ser mayor a 0.")    
        if len(justificacion.strip()) < 20:
            errors.append("La justificación debe tener al menos 20 caracteres.")

    if errors:
        for err in errors:
            st.error(f"⚠️ {err}")
    else:
        try:
            # Armar lista de items como JSON
            items_json = [
                {
                    "bien_servicio":  item["bien_servicio"].strip(),
                    "unidad_medida":  item["unidad_medida"],
                    "precio_unitario": float(item["precio_unitario"]),
                    "cantidad":        int(item["cantidad"]),
                    "subtotal":        float(item["subtotal"]),
                }
                for item in items if item["bien_servicio"].strip()
            ]

            # El primer ítem se guarda en columnas individuales (compatibilidad)
            # Todos los ítems se guardan en columna items (JSON)
            primer_item = items_json[0]

            sql = text("""
                INSERT INTO formularios
                    (solicitante, secretaria, sub_secretaria,
                     bien_servicio, unidad_medida,
                     precio_unitario, cantidad, justificacion,
                     tipo_gasto, prioridad, gasto_escuelas,
                     fecha_requerimiento, items)
                VALUES
                    (:solicitante, :secretaria, :sub_secretaria,
                     :bien_servicio, :unidad_medida,
                     :precio_unitario, :cantidad, :justificacion,
                     :tipo_gasto, :prioridad, :gasto_escuelas,
                     :fecha_requerimiento, :items)
                RETURNING id
            """)

            import json
            nuevo_id = None
            with conn.session as session:
                result = session.execute(sql, {
                    "solicitante":         nombre_auto,
                    "secretaria":          secretaria_auto,
                    "sub_secretaria":      sub_secretaria_auto or None,
                    "bien_servicio":       primer_item["bien_servicio"],
                    "unidad_medida":       primer_item["unidad_medida"],
                    "precio_unitario":     primer_item["precio_unitario"],
                    "cantidad":            primer_item["cantidad"],
                    "justificacion":       justificacion.strip(),
                    "tipo_gasto":          tipo_gasto,
                    "prioridad":           prioridad,
                    "gasto_escuelas":      bool(gasto_escuelas),
                    "fecha_requerimiento": fecha_requerimiento,
                    "items":               json.dumps(items_json),
                })
                nuevo_id = result.fetchone()[0]
                session.commit()

            # Armar resumen de ítems para el mensaje
            resumen_items = "\n".join([
                f"• {it['bien_servicio']} | {it['unidad_medida']} × {it['cantidad']} | $ {it['subtotal']:,.2f}"
                for it in items_json
            ])

            fecha_str = f" | Fecha requerida: **{fecha_requerimiento.strftime('%d/%m/%Y')}**" if fecha_requerimiento else ""
            st.success(
                f"✅ **Solicitud registrada exitosamente.**\n\n"
                f"ID: **#{nuevo_id}** | Solicitante: **{nombre_auto}** | "
                f"Secretaría: **{secretaria_auto}** | "
                f"Total: **$ {total_general:,.2f}** | Prioridad: **{prioridad}**{fecha_str}\n\n"
                f"**Ítems registrados:**\n{resumen_items}"
            )
            st.balloons()
            st.session_state.form_version += 1
            st.session_state.formulario_guardado = True

        except Exception as e:
            st.error(f"❌ Error al guardar en la base de datos: {e}")

# ─── Botón para cargar nuevo formulario ───────────────────────────────────
if st.session_state.get("formulario_guardado"):
    if st.button("➕ Cargar nuevo formulario", type="secondary", use_container_width=True):
        st.session_state.form_version += 1
        st.session_state.formulario_guardado = False
        st.rerun()
# ─── Ayuda ─────────────────────────────────────────────────────────────────
with st.expander("ℹ️ Ayuda sobre los campos"):
    st.markdown("""
| Campo | Descripción |
|-------|-------------|
| **Secretaría / Sub Secretaría** | Se completan automáticamente con los datos de tu usuario |
| **Unidad de Medida** | Seleccioná de la lista o elegí "Otro" para ingresar una personalizada |
| **Tipo de Gasto** | *Esencial*: indispensable · *Serv. Basico*: servicios base · *Politica del gobernador*: lineamiento político |
| **Prioridad** | *Alta*: urgente/crítico · *Media*: necesario · *Baja*: puede esperar |
| **Fecha límite** | Opcional — dejá en blanco si no tiene fecha límite |
| **Total** | Se calcula automáticamente: Precio Unitario × Cantidad |
""")