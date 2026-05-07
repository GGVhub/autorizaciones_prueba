"""
00_mi_cuenta.py — Perfil del usuario, cambio de contraseña y administración.
Acceso: todos los perfiles.
"""
import streamlit as st
from sqlalchemy import text
from datetime import timezone, timedelta
import hashlib
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import require_login, get_connection

require_login()

conn = get_connection()
ARG  = timezone(timedelta(hours=-3))

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

PERFIL_LABELS = {
    1: "👑 Secretaria General",
    2: "✅ Titular Serv. Administrativo",
    3: "📋 Administración",
    4: "📋 Compras",
    5: "✅ Autoridad de Área",
    6: "📝 Requiriente",
}

user_id = st.session_state.get("user_id")

df_user = conn.query(
    "SELECT * FROM usuarios WHERE id = :id",
    params={"id": user_id},
    ttl=0
)

if df_user.empty:
    st.error("No se encontró el usuario.")
    st.stop()

user    = df_user.iloc[0]
profile = int(st.session_state.get("user_profile", 0))

try:
    ultimo = pd.to_datetime(user["ultimo_acceso"], utc=True)\
               .tz_convert(ARG).strftime("%d/%m/%Y %H:%M")
except:
    ultimo = "—"

# ══════════════════════════════════════════════════════════════════════════
# MI CUENTA
# ══════════════════════════════════════════════════════════════════════════
st.title("👤 Mi Cuenta")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 📋 Datos del perfil")
    st.markdown(f"**Nombre:** {user['nombre_apellido']}")
    st.markdown(f"**Usuario:** `{user['usuario']}`")
    st.markdown(f"**Perfil:** {PERFIL_LABELS.get(profile, str(profile))}")
    st.markdown(f"**Nivel:** {user.get('nivel') or '—'}")
    st.markdown(f"**Secretaría:** {user.get('secretaria') or '—'}")
    if user.get("sub_secretaria"):
        st.markdown(f"**Sub Secretaría:** {user['sub_secretaria']}")
    st.markdown(f"**Último acceso:** {ultimo}")

with col2:
    st.markdown("#### 🔐 Cambiar mi contraseña")
    with st.form("form_cambio_pass"):
        actual  = st.text_input("Contraseña actual",          type="password")
        nueva1  = st.text_input("Nueva contraseña",           type="password", help="Mínimo 6 caracteres")
        nueva2  = st.text_input("Repetir nueva contraseña",   type="password")
        guardar = st.form_submit_button("💾 Actualizar contraseña", type="primary", use_container_width=True)

    if guardar:
        if not actual or not nueva1 or not nueva2:
            st.error("Completá todos los campos.")
        elif hash_password(actual) != str(user["password_hash"]).strip():
            st.error("❌ La contraseña actual es incorrecta.")
        elif len(nueva1) < 6:
            st.error("La nueva contraseña debe tener al menos 6 caracteres.")
        elif nueva1 != nueva2:
            st.error("Las contraseñas nuevas no coinciden.")
        elif nueva1 == actual:
            st.error("La nueva contraseña debe ser diferente a la actual.")
        else:
            try:
                with conn.session as session:
                    session.execute(
                        text("UPDATE usuarios SET password_hash = :h, debe_cambiar_pass = FALSE WHERE id = :id"),
                        {"h": hash_password(nueva1), "id": user_id}
                    )
                    session.commit()
                st.session_state.debe_cambiar_pass = False
                st.success("✅ Contraseña actualizada correctamente.")
            except Exception as e:
                st.error(f"❌ Error: {e}")

# ══════════════════════════════════════════════════════════════════════════
# PANEL ADMINISTRADOR — solo perfil 1
# ══════════════════════════════════════════════════════════════════════════
if profile != (1,2):
    st.stop()

st.divider()
st.title("🛠️ Panel de Administrador")

# ─── Tabla de usuarios ─────────────────────────────────────────────────────
st.subheader("👥 Usuarios del sistema")

df_users = conn.query(
    """SELECT id, nombre_apellido, usuario, nivel, profile,
              activo, debe_cambiar_pass, ultimo_acceso
       FROM usuarios ORDER BY nombre_apellido""",
    ttl=0
)

df_users["ultimo_acceso"] = pd.to_datetime(
    df_users["ultimo_acceso"], utc=True, errors="coerce"
).dt.tz_convert(ARG).dt.strftime("%d/%m/%Y %H:%M").fillna("Nunca")

df_users["profile"] = df_users["profile"].map(
    lambda x: PERFIL_LABELS.get(int(x), str(x))
)
df_users["activo"]           = df_users["activo"].apply(lambda x: "✅" if x else "❌")
df_users["debe_cambiar_pass"] = df_users["debe_cambiar_pass"].apply(lambda x: "⚠️ Sí" if x else "No")

df_users.columns = ["ID", "Nombre", "Usuario", "Nivel", "Perfil", "Activo", "Debe cambiar pass", "Último acceso"]

st.dataframe(df_users, use_container_width=True, hide_index=True)

st.divider()

# ─── Resetear contraseña ───────────────────────────────────────────────────
st.subheader("🔑 Resetear contraseña")
st.caption("La contraseña se resetea a **cambiar123** y el usuario deberá cambiarla al próximo ingreso.")

# Cargar lista de usuarios para el selectbox
df_lista = conn.query(
    "SELECT id, nombre_apellido, usuario FROM usuarios ORDER BY nombre_apellido",
    ttl=0
)

opciones = {
    f"{row['nombre_apellido']} (@{row['usuario']})": int(row["id"])
    for _, row in df_lista.iterrows()
}

col_r1, col_r2, col_r3 = st.columns([3, 2, 1])

with col_r1:
    seleccion = st.selectbox(
        "Seleccioná el usuario",
        options=list(opciones.keys()),
        index=None,
        placeholder="Elegí un usuario..."
    )

with col_r2:
    nueva_pass_admin = st.text_input(
        "Nueva contraseña",
        value="cambiar123",
        help="Por defecto se usa 'cambiar123'"
    )

with col_r3:
    st.markdown("<br>", unsafe_allow_html=True)
    resetear = st.button("🔄 Resetear", type="primary", use_container_width=True)

if resetear:
    if not seleccion:
        st.warning("Seleccioná un usuario primero.")
    elif len(nueva_pass_admin) < 6:
        st.error("La contraseña debe tener al menos 6 caracteres.")
    else:
        uid = opciones[seleccion]
        try:
            with conn.session as session:
                session.execute(
                    text("""UPDATE usuarios
                            SET password_hash     = :h,
                                debe_cambiar_pass = TRUE
                            WHERE id = :id"""),
                    {"h": hash_password(nueva_pass_admin), "id": uid}
                )
                session.commit()
            st.success(f"✅ Contraseña reseteada para **{seleccion}**. Deberá cambiarla al ingresar.")
        except Exception as e:
            st.error(f"❌ Error: {e}")

st.divider()

# ─── Resetear TODOS ────────────────────────────────────────────────────────
st.subheader("⚠️ Resetear TODOS los usuarios")
st.caption("Útil para inicios de ciclo o cuando se pierde el acceso masivamente.")

with st.expander("Expandí para resetear todos"):
    st.warning("Esta acción resetea la contraseña de **todos los usuarios** a `cambiar123`.")
    confirmar_todos = st.checkbox("Confirmo que quiero resetear todas las contraseñas")

    if st.button("🔄 Resetear todos", type="primary", disabled=not confirmar_todos):
        try:
            hashed = hash_password("cambiar123")
            with conn.session as session:
                session.execute(
                    text("UPDATE usuarios SET password_hash = :h, debe_cambiar_pass = TRUE"),
                    {"h": hashed}
                )
                session.commit()
            st.success(f"✅ Contraseñas reseteadas para todos los usuarios. Hash usado: `{hashed}`")
        except Exception as e:
            st.error(f"❌ Error: {e}")

st.divider()

# ─── Activar / Desactivar usuario ──────────────────────────────────────────
st.subheader("🔒 Activar / Desactivar usuario")

col_a1, col_a2, col_a3 = st.columns([3, 1, 1])

with col_a1:
    seleccion_activo = st.selectbox(
        "Seleccioná el usuario",
        options=list(opciones.keys()),
        index=None,
        placeholder="Elegí un usuario...",
        key="sel_activo"
    )
with col_a2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("✅ Activar", use_container_width=True):
        if not seleccion_activo:
            st.warning("Seleccioná un usuario.")
        else:
            uid = opciones[seleccion_activo]
            with conn.session as session:
                session.execute(text("UPDATE usuarios SET activo = TRUE WHERE id = :id"), {"id": uid})
                session.commit()
            st.success(f"✅ Usuario **{seleccion_activo}** activado.")
            st.rerun()

with col_a3:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("❌ Desactivar", use_container_width=True):
        if not seleccion_activo:
            st.warning("Seleccioná un usuario.")
        else:
            uid = opciones[seleccion_activo]
            with conn.session as session:
                session.execute(text("UPDATE usuarios SET activo = FALSE WHERE id = :id"), {"id": uid})
                session.commit()
            st.success(f"✅ Usuario **{seleccion_activo}** desactivado.")
            st.rerun()



st.divider()
st.subheader("➕ Agregar nuevo usuario")

with st.form("form_nuevo_usuario"):
    col_n1, col_n2 = st.columns(2)
    with col_n1:
        nu_nombre    = st.text_input("Nombre y Apellido *")
        nu_usuario   = st.text_input("Usuario *", placeholder="nombre.apellido")
        nu_secretaria = st.text_input("Secretaría")
        nu_sub        = st.text_input("Sub Secretaría")
    with col_n2:
        nu_nivel   = st.selectbox("Nivel", ["Requiriente", "Compras", "Administracion",
                                            "Autoridad de area", "Titular Serv. Administrativo",
                                            "Secretaria General"])
        nu_profile = st.selectbox("Perfil", [6, 5, 4, 3, 2, 1],
                                  format_func=lambda x: f"{x} — {PERFIL_LABELS.get(x,'')}")
        nu_pass    = st.text_input("Contraseña inicial", value="cambiar123")

    crear = st.form_submit_button("➕ Crear usuario", type="primary", use_container_width=True)

if crear:
    if not nu_nombre.strip() or not nu_usuario.strip():
        st.error("Nombre y usuario son obligatorios.")
    else:
        check = conn.query(
            "SELECT id FROM usuarios WHERE usuario = :u",
            params={"u": nu_usuario.strip().lower()},
            ttl=0
        )
        if not check.empty:
            st.error(f"El usuario **{nu_usuario}** ya existe.")
        else:
            try:
                with conn.session as session:
                    session.execute(text("""
                        INSERT INTO usuarios
                            (nombre_apellido, usuario, password_hash,
                             secretaria, sub_secretaria, nivel, profile,
                             activo, debe_cambiar_pass)
                        VALUES
                            (:nombre, :usuario, :hash,
                             :secretaria, :sub, :nivel, :profile,
                             TRUE, TRUE)
                    """), {
                        "nombre":    nu_nombre.strip(),
                        "usuario":   nu_usuario.strip().lower(),
                        "hash":      hash_password(nu_pass),
                        "secretaria": nu_secretaria.strip() or None,
                        "sub":       nu_sub.strip() or None,
                        "nivel":     nu_nivel,
                        "profile":   nu_profile,
                    })
                    session.commit()
                st.success(f"✅ Usuario **{nu_usuario}** creado. Contraseña inicial: `{nu_pass}`")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")