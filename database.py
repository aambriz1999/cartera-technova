"""
Módulo 1 — Capa de Datos, Seguridad Criptográfica, Ledger Inmutable y Simulador de Tiempo (database.py)
Gestiona la persistencia en SQLite3 (`banco.db`) para Cartera TechNova.
Controles implementados:
  - Restricción `UNIQUE` estricta sobre `username` (correo electrónico) en `usuarios`.
  - Encriptación de contraseñas mediante hash criptográfico `SHA-256` (`hashlib`).
  - Cálculo dinámico en tiempo real del rendimiento acumulado según `dias_transcurridos`:
    `Rendimiento Acumulado = Capital * Tasa Anual * (dias_transcurridos / 365)`.
  - Simulador de tiempo (`simular_paso_del_tiempo(user_id, dias)`) mediante `UPDATE` en `portafolio`.
  - Motor transaccional de inversión (`registrar_inversion`), liquidación con ISR 0.5%
    (`liquidar_inversion`) y Ledger Inmutable (`historial_movimientos`).
"""

from datetime import datetime
import hashlib
from pathlib import Path
import sqlite3
from typing import Any

DB_PATH: Path = Path(__file__).resolve().parent / "banco.db"

TASA_RETENCION_ISR: float = 0.005  # 0.5% de retención de ISR sobre la ganancia

PARAMETROS_BONOS: dict[str, dict[str, float]] = {
    "CETES 28 Días": {"tasa_anual": 11.00, "plazo_dias": 28.0},
    "CETES 91 Días": {"tasa_anual": 11.15, "plazo_dias": 91.0},
    "Udibonos 3 Años": {"tasa_anual": 9.85, "plazo_dias": 1095.0},
    "Bondes F 1 Año": {"tasa_anual": 11.30, "plazo_dias": 364.0},
}


def _obtener_conexion() -> sqlite3.Connection:
    """Crea y retorna una conexión a la base de datos SQLite `banco.db`."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def encriptar_password(password: str) -> str:
    """
    Aplica un hash criptográfico SHA-256 sobre la contraseña en texto plano
    utilizando la librería estándar `hashlib`.
    Nunca se almacenan ni comparan contraseñas en texto plano.
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _calcular_rendimiento_dinamico(
    tipo_bono: str, capital: float, fecha_str: str
) -> tuple[int, float, float]:
    """
    Calcula en tiempo real los días transcurridos desde la fecha de creación de la
    inversión y el rendimiento acumulado según la fórmula:
    Rendimiento Acumulado = Capital * Tasa Anual * (dias_transcurridos / 365)

    Retorna `(dias_transcurridos, tasa_anual_pct, rendimiento_acumulado)`.
    """
    ahora = datetime.now()
    fecha_limpia = (fecha_str or "").strip()
    fecha_creacion = ahora

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            fecha_creacion = datetime.strptime(fecha_limpia, fmt)
            break
        except ValueError:
            continue

    dias_transcurridos = max(0, (ahora - fecha_creacion).days)
    parametros = PARAMETROS_BONOS.get(
        tipo_bono, {"tasa_anual": 11.00, "plazo_dias": 28.0}
    )
    tasa_anual_pct = float(parametros["tasa_anual"])
    tasa_decimal = tasa_anual_pct / 100.0

    # Fórmula estricta: Rendimiento Acumulado = Capital * Tasa Anual * (dias_transcurridos / 365)
    rendimiento_acumulado = round(
        float(capital) * tasa_decimal * (float(dias_transcurridos) / 365.0), 2
    )
    return dias_transcurridos, tasa_anual_pct, rendimiento_acumulado


def iniciar_db() -> None:
    """
    Inicializa la base de datos `banco.db` creando las tablas `usuarios`,
    `portafolio` y `historial_movimientos` (Ledger Inmutable) si aún no existen.
    """
    with _obtener_conexion() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                saldo_disponible REAL NOT NULL DEFAULT 0.0
            )
            """
        )
        cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_usuarios_username_unique
            ON usuarios (username)
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS portafolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                tipo_bono TEXT NOT NULL,
                monto REAL NOT NULL,
                fecha TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES usuarios (id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS historial_movimientos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                tipo_operacion TEXT NOT NULL,
                monto REAL NOT NULL,
                fecha TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES usuarios (id)
            )
            """
        )
        conn.commit()


def registrar_usuario(
    username: str, password: str, saldo_inicial: float = 0.0
) -> tuple[bool, str]:
    """
    Registra un nuevo usuario en la tabla `usuarios` normalizando el correo
    electrónico y encriptando la contraseña con SHA-256 antes de insertar.
    Rechaza cuentas duplicadas mediante la restricción `UNIQUE`.
    """
    correo_normalizado = (username or "").strip().lower()
    if not correo_normalizado:
        return False, "El correo electrónico no puede estar vacío."
    if not password or not password.strip():
        return False, "La contraseña no puede estar vacía."

    try:
        saldo_val = round(float(saldo_inicial), 2)
    except (TypeError, ValueError):
        return False, "El saldo inicial debe ser un número válido."

    if saldo_val < 0.0:
        return False, "El saldo inicial no puede ser negativo."

    iniciar_db()
    password_hash = encriptar_password(password)

    try:
        with _obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO usuarios (username, password, saldo_disponible)
                VALUES (?, ?, ?)
                """,
                (correo_normalizado, password_hash, saldo_val),
            )
            conn.commit()
        return True, f"Cuenta '{correo_normalizado}' registrada exitosamente."
    except sqlite3.IntegrityError:
        return (
            False,
            f"El correo electrónico '{correo_normalizado}' ya se encuentra registrado.",
        )
    except sqlite3.Error as exc:
        return False, f"Error de base de datos al registrar usuario: {exc}"


def validar_login(username: str, password: str) -> dict[str, Any] | None:
    """
    Encripta el password ingresado por el usuario con SHA-256 y lo compara
    con el hash almacenado en la tabla `usuarios`.
    Retorna `{"id": id, "username": username, "saldo_disponible": saldo}` si coincide,
    o `None` en caso contrario.
    """
    correo_normalizado = (username or "").strip().lower()
    if not correo_normalizado or not password:
        return None

    iniciar_db()
    password_hash = encriptar_password(password)

    try:
        with _obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, username, saldo_disponible
                FROM usuarios
                WHERE LOWER(username) = ? AND password = ?
                """,
                (correo_normalizado, password_hash),
            )
            row = cursor.fetchone()
            if row is not None:
                return {
                    "id": int(row[0]),
                    "username": str(row[1]),
                    "saldo_disponible": round(float(row[2]), 2),
                }
    except sqlite3.Error:
        return None

    return None


def obtener_saldo(user_id: int) -> float:
    """Consulta el `saldo_disponible` actual del usuario en `banco.db`."""
    iniciar_db()
    try:
        with _obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT saldo_disponible FROM usuarios WHERE id = ?",
                (int(user_id),),
            )
            row = cursor.fetchone()
            if row is not None:
                return round(float(row[0]), 2)
    except (sqlite3.Error, TypeError, ValueError):
        return 0.0

    return 0.0


def actualizar_saldo(
    user_id: int, monto_delta: float, registrar_movimiento: bool = True
) -> tuple[bool, float, str]:
    """
    Suma (`monto_delta > 0`) o resta (`monto_delta < 0`) dinero al `saldo_disponible`
    del usuario, impidiendo saldos negativos.
    Si `registrar_movimiento=True`, inserta automáticamente el asiento ("Fondeo" o "Retiro")
    en `historial_movimientos` dentro de la misma transacción atómica.
    Retorna `(exito, nuevo_saldo, mensaje)`.
    """
    iniciar_db()
    try:
        delta = round(float(monto_delta), 2)
    except (TypeError, ValueError):
        return False, obtener_saldo(user_id), "El monto especificado no es válido."

    try:
        with _obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT saldo_disponible FROM usuarios WHERE id = ?",
                (int(user_id),),
            )
            row = cursor.fetchone()
            if row is None:
                return False, 0.0, "Usuario no encontrado."

            saldo_actual = round(float(row[0]), 2)
            nuevo_saldo = round(saldo_actual + delta, 2)

            if nuevo_saldo < 0.0:
                return (
                    False,
                    saldo_actual,
                    f"Fondos insuficientes. Saldo disponible: ${saldo_actual:,.2f}",
                )

            cursor.execute(
                "UPDATE usuarios SET saldo_disponible = ? WHERE id = ?",
                (nuevo_saldo, int(user_id)),
            )

            if registrar_movimiento and delta != 0.0:
                tipo_op = "Fondeo" if delta > 0 else "Retiro"
                fecha_op = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute(
                    """
                    INSERT INTO historial_movimientos (user_id, tipo_operacion, monto, fecha)
                    VALUES (?, ?, ?, ?)
                    """,
                    (int(user_id), tipo_op, round(abs(delta), 2), fecha_op),
                )

            conn.commit()
            return (
                True,
                nuevo_saldo,
                f"Saldo actualizado correctamente. Nuevo saldo: ${nuevo_saldo:,.2f}",
            )
    except sqlite3.Error as exc:
        return False, obtener_saldo(user_id), f"Error al actualizar el saldo: {exc}"


def registrar_inversion(
    user_id: int,
    tipo_bono: str,
    monto: float,
    fecha: str | None = None,
) -> tuple[bool, str]:
    """
    Inserta una nueva operación de inversión en la tabla `portafolio` y registra
    automáticamente el movimiento `Compra de Bono` en `historial_movimientos`
    dentro de la misma transacción atómica.
    Retorna `(exito, mensaje)`.
    """
    bono_limpio = (tipo_bono or "").strip()
    if not bono_limpio:
        return False, "El tipo de bono no puede estar vacío."

    try:
        monto_val = round(float(monto), 2)
    except (TypeError, ValueError):
        return False, "El monto de inversión debe ser un número válido."

    if monto_val <= 0.0:
        return False, "El monto de inversión debe ser mayor a cero."

    fecha_registro = (
        fecha.strip()
        if fecha and fecha.strip()
        else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    iniciar_db()
    try:
        with _obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM usuarios WHERE id = ?",
                (int(user_id),),
            )
            if cursor.fetchone() is None:
                return False, "El usuario especificado no existe."

            cursor.execute(
                """
                INSERT INTO portafolio (user_id, tipo_bono, monto, fecha)
                VALUES (?, ?, ?, ?)
                """,
                (int(user_id), bono_limpio, monto_val, fecha_registro),
            )
            cursor.execute(
                """
                INSERT INTO historial_movimientos (user_id, tipo_operacion, monto, fecha)
                VALUES (?, ?, ?, ?)
                """,
                (
                    int(user_id),
                    f"Compra de Bono ({bono_limpio})",
                    monto_val,
                    fecha_registro,
                ),
            )
            conn.commit()
        return True, "Inversión registrada exitosamente"
    except sqlite3.Error as exc:
        return False, f"Error al registrar la inversión: {exc}"


def obtener_portafolio(user_id: int) -> list[dict[str, Any]]:
    """
    Retorna todas las inversiones activas del usuario en la tabla `portafolio`
    ordenadas por fecha descendente, calculando en tiempo real `dias_transcurridos`
    y `rendimiento_acumulado` según la fórmula:
    Rendimiento Acumulado = Capital * Tasa Anual * (dias_transcurridos / 365).
    """
    iniciar_db()
    try:
        with _obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, user_id, tipo_bono, monto, fecha
                FROM portafolio
                WHERE user_id = ?
                ORDER BY fecha DESC, id DESC
                """,
                (int(user_id),),
            )
            filas = cursor.fetchall()
            posiciones: list[dict[str, Any]] = []
            for fila in filas:
                inv_id = int(fila[0])
                usr_id = int(fila[1])
                tipo_bono = str(fila[2])
                monto = round(float(fila[3]), 2)
                fecha_str = str(fila[4])

                dias_trans, tasa_anual, rend_acum = (
                    _calcular_rendimiento_dinamico(
                        tipo_bono=tipo_bono,
                        capital=monto,
                        fecha_str=fecha_str,
                    )
                )

                posiciones.append(
                    {
                        "id": inv_id,
                        "user_id": usr_id,
                        "tipo_bono": tipo_bono,
                        "monto": monto,
                        "fecha": fecha_str,
                        "dias_transcurridos": dias_trans,
                        "tasa_anual": tasa_anual,
                        "rendimiento_acumulado": rend_acum,
                    }
                )
            return posiciones
    except (sqlite3.Error, TypeError, ValueError):
        return []


def simular_paso_del_tiempo(user_id: int, dias: int) -> tuple[bool, str]:
    """
    Simula el paso del tiempo ejecutando un UPDATE en la tabla `portafolio`,
    restando `dias` a la columna `fecha` de todas las posiciones activas del usuario
    para que envejezcan y generen rendimiento acumulado.
    """
    iniciar_db()
    try:
        usr_id = int(user_id)
        dias_simulados = int(dias)
    except (TypeError, ValueError):
        return False, "Parámetros de simulación inválidos."

    if dias_simulados <= 0:
        return False, "La cantidad de días a simular debe ser mayor a cero."

    try:
        with _obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE portafolio
                SET fecha = datetime(fecha, ?)
                WHERE user_id = ?
                """,
                (f"-{dias_simulados} days", usr_id),
            )
            filas_afectadas = cursor.rowcount
            conn.commit()

        if filas_afectadas == 0:
            return (
                False,
                "No tienes posiciones activas en el portafolio para simular el paso del tiempo.",
            )

        return (
            True,
            f"⏱️ Simulación aplicada: el tiempo avanzó {dias_simulados} días para {filas_afectadas} posición(es) activa(s).",
        )
    except sqlite3.Error as exc:
        return False, f"Error al simular el paso del tiempo: {exc}"


def liquidar_inversion(inversion_id: int, user_id: int) -> tuple[bool, str]:
    """
    Liquida una inversión activa del portafolio del usuario:
      1. Verifica que la posición pertenezca al usuario y obtiene su capital, tipo de bono y fecha.
      2. Calcula dinámicamente el Rendimiento Bruto acumulado según los `dias_transcurridos` reales/simulados.
      3. Retiene el 0.5% de ISR sobre la ganancia (Rendimiento Bruto).
      4. En una misma transacción atómica:
         - Elimina la inversión de `portafolio`.
         - Suma el capital neto final (`Capital + Rendimiento Bruto - ISR`) al `saldo_disponible`.
         - Registra el movimiento de `Liquidación` en `historial_movimientos`.

    Retorna `(exito, mensaje_desglose)`.
    """
    iniciar_db()
    try:
        inv_id = int(inversion_id)
        usr_id = int(user_id)
    except (TypeError, ValueError):
        return False, "Identificadores de inversión o usuario inválidos."

    try:
        with _obtener_conexion() as conn:
            cursor = conn.cursor()

            # 1. Buscar la inversión activa perteneciente al usuario
            cursor.execute(
                """
                SELECT id, tipo_bono, monto, fecha
                FROM portafolio
                WHERE id = ? AND user_id = ?
                """,
                (inv_id, usr_id),
            )
            fila_inv = cursor.fetchone()
            if fila_inv is None:
                return (
                    False,
                    "La inversión seleccionada no existe o ya fue liquidada.",
                )

            tipo_bono = str(fila_inv[1])
            capital = round(float(fila_inv[2]), 2)
            fecha_inversion = str(fila_inv[3])

            # 2. Consultar saldo actual del usuario
            cursor.execute(
                "SELECT saldo_disponible FROM usuarios WHERE id = ?",
                (usr_id,),
            )
            fila_user = cursor.fetchone()
            if fila_user is None:
                return False, "El usuario titular no existe."

            saldo_actual = round(float(fila_user[0]), 2)

            # 3. Calcular rendimiento bruto dinámico basado en días transcurridos, retención ISR (0.5%) y total neto
            _, _, rendimiento_bruto = _calcular_rendimiento_dinamico(
                tipo_bono=tipo_bono,
                capital=capital,
                fecha_str=fecha_inversion,
            )
            retencion_isr = round(rendimiento_bruto * TASA_RETENCION_ISR, 2)
            total_depositado = round(
                capital + rendimiento_bruto - retencion_isr, 2
            )
            nuevo_saldo = round(saldo_actual + total_depositado, 2)
            fecha_liq = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 4. Ejecutar baja de la inversión, abono al saldo y registro en Ledger Inmutable en una misma transacción
            cursor.execute(
                "DELETE FROM portafolio WHERE id = ? AND user_id = ?",
                (inv_id, usr_id),
            )
            cursor.execute(
                "UPDATE usuarios SET saldo_disponible = ? WHERE id = ?",
                (nuevo_saldo, usr_id),
            )
            cursor.execute(
                """
                INSERT INTO historial_movimientos (user_id, tipo_operacion, monto, fecha)
                VALUES (?, ?, ?, ?)
                """,
                (
                    usr_id,
                    f"Liquidación ({tipo_bono})",
                    total_depositado,
                    fecha_liq,
                ),
            )
            conn.commit()

            mensaje_desglose = (
                f"Liquidación exitosa. "
                f"Capital: ${capital:,.2f}. "
                f"Rendimiento Bruto: ${rendimiento_bruto:,.2f}. "
                f"Retención ISR (0.5%): -${retencion_isr:,.2f}. "
                f"Total depositado: ${total_depositado:,.2f}"
            )
            return True, mensaje_desglose

    except sqlite3.Error as exc:
        return False, f"Error de base de datos al liquidar la inversión: {exc}"


def obtener_historial(user_id: int) -> list[dict[str, Any]]:
    """
    Devuelve todos los registros del Ledger Inmutable (`historial_movimientos`)
    de un usuario ordenados por fecha descendente.
    """
    iniciar_db()
    try:
        with _obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, user_id, tipo_operacion, monto, fecha
                FROM historial_movimientos
                WHERE user_id = ?
                ORDER BY fecha DESC, id DESC
                """,
                (int(user_id),),
            )
            filas = cursor.fetchall()
            return [
                {
                    "id": int(fila[0]),
                    "user_id": int(fila[1]),
                    "tipo_operacion": str(fila[2]),
                    "monto": round(float(fila[3]), 2),
                    "fecha": str(fila[4]),
                }
                for fila in filas
            ]
    except (sqlite3.Error, TypeError, ValueError):
        return []
