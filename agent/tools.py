# agent/tools.py — Herramientas del agente
# Generado por AgentKit

"""
Herramientas específicas del negocio de CH Veterinario.
Estas funciones extienden las capacidades del agente más allá de responder texto:
agendar citas/reservaciones y tomar pedidos de productos.
"""

import os
import json
import yaml
import logging
from datetime import datetime

logger = logging.getLogger("agentkit")

CITAS_PATH = "citas.json"
PEDIDOS_PATH = "pedidos.json"


def cargar_info_negocio() -> dict:
    """Carga la información del negocio desde business.yaml."""
    try:
        with open("config/business.yaml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error("config/business.yaml no encontrado")
        return {}


def obtener_horario() -> dict:
    """Retorna el horario de atención del negocio."""
    info = cargar_info_negocio()
    return {
        "horario": info.get("negocio", {}).get("horario", "No disponible"),
        "esta_abierto": True,  # TODO: calcular según hora actual y horario
    }


def buscar_en_knowledge(consulta: str) -> str:
    """
    Busca información relevante en los archivos de /knowledge.
    Retorna el contenido más relevante encontrado.
    """
    resultados = []
    knowledge_dir = "knowledge"

    if not os.path.exists(knowledge_dir):
        return "No hay archivos de conocimiento disponibles."

    for archivo in os.listdir(knowledge_dir):
        ruta = os.path.join(knowledge_dir, archivo)
        if archivo.startswith(".") or not os.path.isfile(ruta):
            continue
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                contenido = f.read()
                # Búsqueda simple por coincidencia de texto
                if consulta.lower() in contenido.lower():
                    resultados.append(f"[{archivo}]: {contenido[:500]}")
        except (UnicodeDecodeError, IOError):
            continue

    if resultados:
        return "\n---\n".join(resultados)
    return "No encontré información específica sobre eso en mis archivos."


def _leer_registro(ruta: str) -> list[dict]:
    """Lee un archivo JSON de registros (citas o pedidos), o retorna lista vacía."""
    if not os.path.exists(ruta):
        return []
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _guardar_registro(ruta: str, registros: list[dict]):
    """Guarda la lista de registros en el archivo JSON."""
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(registros, f, ensure_ascii=False, indent=2)


# ── Agendar citas / reservaciones ──────────────────────────────────
# Cubre: consultas veterinarias, estética canina, vacunación y pensión.

def agendar_cita(telefono: str, servicio: str, mascota: str, fecha: str, hora: str) -> dict:
    """
    Agenda una cita o reservación para el cliente.

    Args:
        telefono: Número de contacto del dueño
        servicio: Tipo de servicio ("consulta", "estetica", "vacunacion", "pension")
        mascota: Nombre (y opcionalmente especie/raza) de la mascota
        fecha: Fecha solicitada (ej: "2026-08-02")
        hora: Hora solicitada (ej: "11:00am")

    Returns:
        Diccionario con el detalle de la cita agendada y su id.
    """
    citas = _leer_registro(CITAS_PATH)
    cita = {
        "id": len(citas) + 1,
        "telefono": telefono,
        "servicio": servicio,
        "mascota": mascota,
        "fecha": fecha,
        "hora": hora,
        "estado": "confirmada",
        "creado": datetime.utcnow().isoformat(),
    }
    citas.append(cita)
    _guardar_registro(CITAS_PATH, citas)
    logger.info(f"Cita agendada: {cita}")
    return cita


def cancelar_cita(cita_id: int) -> bool:
    """Cancela una cita existente por su id. Retorna True si se encontró y canceló."""
    citas = _leer_registro(CITAS_PATH)
    for cita in citas:
        if cita["id"] == cita_id:
            cita["estado"] = "cancelada"
            _guardar_registro(CITAS_PATH, citas)
            return True
    return False


def listar_citas(telefono: str) -> list[dict]:
    """Lista las citas activas de un cliente por su número de teléfono."""
    citas = _leer_registro(CITAS_PATH)
    return [c for c in citas if c["telefono"] == telefono and c["estado"] == "confirmada"]


# ── Tomar pedidos de productos ─────────────────────────────────────
# Cubre: juguetes, croquetas y demás productos para mascotas.

def agregar_al_carrito(telefono: str, producto: str, cantidad: int) -> dict:
    """
    Agrega un producto al pedido en curso de un cliente.

    Args:
        telefono: Número de contacto del cliente
        producto: Nombre del producto (ej: "croquetas para perro adulto")
        cantidad: Cantidad solicitada

    Returns:
        Diccionario con el detalle del item agregado.
    """
    pedidos = _leer_registro(PEDIDOS_PATH)
    item = {
        "id": len(pedidos) + 1,
        "telefono": telefono,
        "producto": producto,
        "cantidad": cantidad,
        "estado": "en_carrito",
        "creado": datetime.utcnow().isoformat(),
    }
    pedidos.append(item)
    _guardar_registro(PEDIDOS_PATH, pedidos)
    logger.info(f"Producto agregado al carrito: {item}")
    return item


def ver_carrito(telefono: str) -> list[dict]:
    """Retorna los items en el carrito (aún no confirmados) de un cliente."""
    pedidos = _leer_registro(PEDIDOS_PATH)
    return [p for p in pedidos if p["telefono"] == telefono and p["estado"] == "en_carrito"]


def confirmar_pedido(telefono: str) -> dict:
    """Confirma todos los items en carrito de un cliente y los marca como pedido confirmado."""
    pedidos = _leer_registro(PEDIDOS_PATH)
    items_confirmados = []
    for p in pedidos:
        if p["telefono"] == telefono and p["estado"] == "en_carrito":
            p["estado"] = "confirmado"
            items_confirmados.append(p)
    _guardar_registro(PEDIDOS_PATH, pedidos)
    return {"telefono": telefono, "items": items_confirmados}
