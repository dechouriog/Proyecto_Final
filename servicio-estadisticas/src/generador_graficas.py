"""
Generador de gráficas para el reporte de estadísticas.

Usa matplotlib en modo "Agg" (sin display) para crear PNGs en memoria
que después se adjuntan al correo.
"""

import io
import logging

import matplotlib

# Backend sin display - imprescindible en contenedor sin entorno gráfico
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

log = logging.getLogger(__name__)

# Paleta de colores institucional consistente con la app web
COLOR_PRIMARIO = "#003366"
COLOR_SECUNDARIO = "#d4a017"
PALETA_CARRERAS = {
    "Medicina":     "#c0392b",
    "Ingenieria":   "#2980b9",
    "Abogacia":     "#27ae60",
    "Licenciatura": "#8e44ad",
}


def generar_imagenes_graficas(estadisticas: dict) -> dict:
    """
    Genera todas las gráficas del reporte.

    Devuelve un diccionario {nombre_grafica -> bytes_png} listo para
    adjuntar al correo.
    """
    return {
        "grafica_por_comuna":  _grafica_registros_por_comuna(estadisticas),
        "grafica_por_carrera": _grafica_registros_por_carrera(estadisticas),
        "grafica_comuna_carrera": _grafica_comuna_y_carrera(estadisticas),
    }


def _grafica_registros_por_comuna(estadisticas: dict) -> bytes:
    """Gráfica de barras: cantidad de registros por comuna."""
    conteo = estadisticas["conteo_por_comuna"]

    # Aseguramos que las 10 comunas aparezcan aunque tengan 0 registros
    comunas = list(range(1, 11))
    cantidades = [conteo.get(c, 0) for c in comunas]

    figura, eje = plt.subplots(figsize=(10, 6))
    barras = eje.bar(comunas, cantidades, color=COLOR_PRIMARIO, edgecolor="white", linewidth=1.5)

    # Etiquetas con el valor encima de cada barra
    for barra, valor in zip(barras, cantidades):
        if valor > 0:
            eje.text(
                barra.get_x() + barra.get_width() / 2,
                barra.get_height() + max(cantidades) * 0.01,
                str(valor),
                ha="center",
                va="bottom",
                fontweight="bold",
            )

    eje.set_title("Registros por comuna", fontsize=15, fontweight="bold", color=COLOR_PRIMARIO)
    eje.set_xlabel("Número de comuna", fontsize=11)
    eje.set_ylabel("Cantidad de registros", fontsize=11)
    eje.set_xticks(comunas)
    eje.grid(axis="y", linestyle="--", alpha=0.4)
    eje.set_axisbelow(True)

    return _figura_a_bytes(figura)


def _grafica_registros_por_carrera(estadisticas: dict) -> bytes:
    """Gráfica de pastel: distribución por carrera."""
    conteo = estadisticas["conteo_por_carrera"]

    # Filtramos carreras con 0 registros para que el pastel no quede feo
    carreras = [c for c, v in conteo.items() if v > 0]
    cantidades = [conteo[c] for c in carreras]
    colores = [PALETA_CARRERAS.get(c, "#95a5a6") for c in carreras]

    figura, eje = plt.subplots(figsize=(8, 8))

    if not carreras:
        eje.text(0.5, 0.5, "Sin datos",
                  ha="center", va="center", fontsize=18, color="#888")
        eje.set_axis_off()
    else:
        eje.pie(
            cantidades,
            labels=carreras,
            colors=colores,
            autopct=lambda p: f"{p:.1f}%\n({int(round(p * sum(cantidades) / 100))})",
            startangle=90,
            wedgeprops={"edgecolor": "white", "linewidth": 2},
            textprops={"fontsize": 11, "fontweight": "bold"},
        )

    eje.set_title("Distribución por carrera de interés",
                   fontsize=15, fontweight="bold", color=COLOR_PRIMARIO, pad=20)
    return _figura_a_bytes(figura)


def _grafica_comuna_y_carrera(estadisticas: dict) -> bytes:
    """Gráfica de barras apiladas: registros por comuna desglosados por carrera."""
    conteo = estadisticas["conteo_comuna_carrera"]
    carreras_orden = ["Medicina", "Ingenieria", "Abogacia", "Licenciatura"]
    comunas = list(range(1, 11))

    figura, eje = plt.subplots(figsize=(11, 6))

    # Acumulador para apilar las barras
    acumulado_base = [0] * len(comunas)

    for carrera in carreras_orden:
        valores_de_carrera = [
            conteo.get(comuna, {}).get(carrera, 0) for comuna in comunas
        ]
        eje.bar(
            comunas,
            valores_de_carrera,
            bottom=acumulado_base,
            label=carrera,
            color=PALETA_CARRERAS.get(carrera, "#95a5a6"),
            edgecolor="white",
            linewidth=0.8,
        )
        # Actualizamos el acumulado para el siguiente nivel del stack
        acumulado_base = [a + v for a, v in zip(acumulado_base, valores_de_carrera)]

    eje.set_title("Registros por comuna y carrera",
                   fontsize=15, fontweight="bold", color=COLOR_PRIMARIO)
    eje.set_xlabel("Número de comuna", fontsize=11)
    eje.set_ylabel("Cantidad de registros", fontsize=11)
    eje.set_xticks(comunas)
    eje.legend(title="Carrera", loc="upper right", framealpha=0.95)
    eje.grid(axis="y", linestyle="--", alpha=0.4)
    eje.set_axisbelow(True)

    return _figura_a_bytes(figura)


def _figura_a_bytes(figura) -> bytes:
    """Convierte una figura matplotlib a bytes PNG y cierra la figura."""
    buffer_memoria = io.BytesIO()
    figura.tight_layout()
    figura.savefig(buffer_memoria, format="png", dpi=110, bbox_inches="tight")
    plt.close(figura)
    buffer_memoria.seek(0)
    return buffer_memoria.getvalue()
