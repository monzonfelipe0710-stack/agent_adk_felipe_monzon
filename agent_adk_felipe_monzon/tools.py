"""Herramientas utilizadas por el agente ADK."""
import json
import math
from pathlib import Path
from typing import Any

from ddgs import DDGS

KNOWLEDGE_PATH = Path(__file__).with_name("knowledge_base.json")

BITS_POR_PRECISION = {
    "FP32": 32,
    "FP16": 16,
    "BF16": 16,
    "INT8": 8,
    "INT4": 4,
}


def _validar_texto(valor: str, nombre: str, max_len: int = 500) -> str | None:
    if not isinstance(valor, str):
        return f"Error: {nombre} debe ser texto."
    valor = valor.strip()
    if not valor:
        return f"Error: {nombre} no puede estar vacío."
    if len(valor) > max_len:
        return f"Error: {nombre} supera el máximo de {max_len} caracteres."
    return None


def buscar_en_web(query: str, max_results: int = 5) -> dict[str, Any]:
    """Busca información actualizada en Internet usando DuckDuckGo.

    Args:
        query: Consulta concreta que se desea buscar.
        max_results: Cantidad de resultados solicitados, entre 1 y 8.
    """
    error = _validar_texto(query, "query", 300)
    if error:
        return {"ok": False, "mensaje": error, "resultados": []}
    if isinstance(max_results, bool) or not isinstance(max_results, int):
        return {"ok": False, "mensaje": "max_results debe ser un número entero.", "resultados": []}
    if not 1 <= max_results <= 8:
        return {"ok": False, "mensaje": "max_results debe estar entre 1 y 8.", "resultados": []}

    try:
        resultados = DDGS().text(query, max_results=max_results)
        normalizados = [
            {
                "titulo": item.get("title", ""),
                "url": item.get("href", ""),
                "resumen": item.get("body", ""),
            }
            for item in (resultados or [])
        ]
        if not normalizados:
            return {"ok": True, "mensaje": "La búsqueda no devolvió resultados.", "resultados": []}
        return {"ok": True, "mensaje": f"Se encontraron {len(normalizados)} resultados.", "resultados": normalizados}
    except Exception as exc:
        return {"ok": False, "mensaje": f"No se pudo completar la búsqueda: {type(exc).__name__}. Verificá la conexión e intentá nuevamente.", "resultados": []}


def consultar_base_conocimiento(query: str) -> dict[str, Any]:
    """Consulta la base local de conceptos sobre ADK y cuantización.

    Args:
        query: Palabras o pregunta sobre un concepto del material de estudio.
    """
    error = _validar_texto(query, "query", 300)
    if error:
        return {"ok": False, "mensaje": error, "coincidencias": []}

    try:
        datos = json.loads(KNOWLEDGE_PATH.read_text(encoding="utf-8"))
        terminos = [t.lower() for t in query.split() if len(t) > 2]
        coincidencias = []
        for entrada in datos.get("entries", []):
            texto = " ".join([
                entrada.get("title", ""),
                " ".join(entrada.get("keywords", [])),
                entrada.get("content", ""),
            ]).lower()
            puntaje = sum(1 for termino in terminos if termino in texto)
            if puntaje:
                coincidencias.append((puntaje, entrada))
        coincidencias.sort(key=lambda par: par[0], reverse=True)
        resultados = [
            {"titulo": item["title"], "contenido": item["content"]}
            for _, item in coincidencias[:4]
        ]
        if not resultados:
            return {"ok": True, "mensaje": "No se encontraron coincidencias en la base local. Podés reformular la consulta o solicitar una búsqueda web.", "coincidencias": []}
        return {"ok": True, "mensaje": f"Se encontraron {len(resultados)} conceptos relacionados.", "coincidencias": resultados}
    except FileNotFoundError:
        return {"ok": False, "mensaje": "No se encontró knowledge_base.json.", "coincidencias": []}
    except (json.JSONDecodeError, OSError) as exc:
        return {"ok": False, "mensaje": f"No se pudo leer la base local: {type(exc).__name__}.", "coincidencias": []}


def _calcular_bytes(parametros_billones: float, precision: str) -> int:
    bits = BITS_POR_PRECISION[precision]
    return math.ceil(parametros_billones * 1_000_000_000 * bits / 8)


def _formatear_bytes(cantidad: int) -> dict[str, float]:
    return {
        "GB_decimal": round(cantidad / 1_000_000_000, 2),
        "GiB": round(cantidad / (1024 ** 3), 2),
    }


def estimar_memoria_modelo(parametros_billones: float, precision: str = "FP16") -> dict[str, Any]:
    """Estima la memoria teórica necesaria para almacenar los pesos de un LLM.

    Args:
        parametros_billones: Cantidad de parámetros expresada en miles de millones (por ejemplo, 7 para 7B).
        precision: FP32, FP16, BF16, INT8 o INT4.
    """
    if isinstance(parametros_billones, bool) or not isinstance(parametros_billones, (int, float)):
        return {"ok": False, "mensaje": "La cantidad de parámetros debe ser numérica."}
    if not 0 < parametros_billones <= 2000:
        return {"ok": False, "mensaje": "La cantidad de parámetros debe ser mayor que 0 y no superar 2000B."}
    if not isinstance(precision, str):
        return {"ok": False, "mensaje": "La precisión debe ser texto."}
    precision = precision.strip().upper()
    if precision not in BITS_POR_PRECISION:
        return {"ok": False, "mensaje": f"Precisión inválida. Opciones: {', '.join(BITS_POR_PRECISION)}."}

    memoria = _formatear_bytes(_calcular_bytes(float(parametros_billones), precision))
    return {
        "ok": True,
        "parametros": f"{parametros_billones:g}B",
        "precision": precision,
        "bits_por_parametro": BITS_POR_PRECISION[precision],
        "memoria_teorica_pesos": memoria,
        "advertencia": "Estimación de los pesos únicamente. El uso real es mayor por contexto, caché KV, activaciones, buffers y overhead del runtime.",
    }


def comparar_precisiones(parametros_billones: float) -> dict[str, Any]:
    """Compara la memoria teórica de los pesos en distintas precisiones.

    Args:
        parametros_billones: Cantidad de parámetros expresada en miles de millones (por ejemplo, 7 para 7B).
    """
    if isinstance(parametros_billones, bool) or not isinstance(parametros_billones, (int, float)):
        return {"ok": False, "mensaje": "La cantidad de parámetros debe ser numérica."}
    if not 0 < parametros_billones <= 2000:
        return {"ok": False, "mensaje": "La cantidad de parámetros debe ser mayor que 0 y no superar 2000B."}

    base = _calcular_bytes(float(parametros_billones), "FP16")
    filas = []
    for precision in BITS_POR_PRECISION:
        bytes_pesos = _calcular_bytes(float(parametros_billones), precision)
        ahorro = (1 - bytes_pesos / base) * 100
        filas.append({
            "precision": precision,
            "bits": BITS_POR_PRECISION[precision],
            **_formatear_bytes(bytes_pesos),
            "ahorro_vs_FP16_porcentaje": round(ahorro, 1),
        })
    return {
        "ok": True,
        "parametros": f"{parametros_billones:g}B",
        "comparacion": filas,
        "nota": "Valores teóricos para los pesos; el consumo real incluye memoria adicional.",
    }
