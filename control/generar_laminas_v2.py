"""Láminas V2 desde meshes medidos: no construye, renderiza ni modifica el modelo.

Ejecutar tras construir V2 y, preferiblemente, generar sus vistas ortográficas:
  python control/generar_laminas_v2.py --require-ortho

El informe es un cotejo visual documentado. No hereda el APTO ni los controles V1.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "modelo/python_deps"))

import fitz
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon as Patch, Rectangle
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (Image, PageBreak, Paragraph, SimpleDocTemplate,
                               Spacer, Table, TableStyle)
from shapely.geometry import LineString, Polygon
from shapely.ops import polygonize, unary_union

WALL = "#b73534"
NEW = "#b96b00"
SOURCE = "#194ca8"
USER = "#9b5700"
ARCHITECTURE = {"muro_vivienda", "forjado", "peto", "marquesina",
                "carpinteria", "vidrio", "cielorraso"}
ALZADOS = [
    # id, horizontal axis/sign, depth axis, far-to-near ordering,
    # original PDF38 horizontal origin/floor (pt), crop (pt), viewing direction
    ("puerta_principal", 1, -1, 0, True, 952.04, 194.92,
     (280, 80, 835, 212), "+X; izquierda imagen = fondo, derecha = vial"),
    ("lateral_porche", 1, 1, 0, False, 220.76, 514.48,
     (260, 398, 925, 532), "−X; izquierda imagen = vial, derecha = fondo"),
    ("vial_publico", 0, 1, 1, True, 385.28, 353.92,
     (415, 244, 655, 372), "+Y; izquierda imagen = calle privada lateral"),
    ("trasero", 0, -1, 1, False, 722.96, 661.84,
     (450, 553, 690, 680), "−Y; izquierda imagen = jardín lateral de terraza"),
]


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def local(path):
    path = Path(path)
    return (path if path.is_absolute() else ROOT / path).resolve()


def relative(path):
    return str(Path(path).resolve().relative_to(ROOT))


def mesh_slice(obj, z):
    """Intersección horizontal de las caras reales; no usa la huella esperada."""
    lines = []
    vertices = obj["vertices"]
    for face in obj["caras"]:
        crossings = []
        for i, idx in enumerate(face):
            a, b = vertices[idx], vertices[face[(i + 1) % len(face)]]
            if (a[2] - z) * (b[2] - z) < 0:
                t = (z - a[2]) / (b[2] - a[2])
                p = (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))
                if not any(math.dist(p, q) < 1e-9 for q in crossings):
                    crossings.append(p)
        if len(crossings) == 2 and math.dist(*crossings) > 1e-9:
            lines.append(LineString(crossings))
    return (unary_union(list(polygonize(unary_union(lines))))
            if lines else Polygon())


def mesh_xy(obj):
    faces = []
    for face in obj["caras"]:
        if len(face) < 3:
            continue
        poly = Polygon([(obj["vertices"][i][0], obj["vertices"][i][1])
                        for i in face])
        if poly.area > 1e-10:
            faces.append(poly.buffer(0))
    return unary_union(faces)


def polygons(geometry):
    if geometry.is_empty:
        return []
    if geometry.geom_type == "Polygon":
        return [geometry]
    return [p for g in geometry.geoms for p in polygons(g)]


def fill(ax, geometry, color, alpha=1, edgecolor=None, linewidth=.45):
    for poly in polygons(geometry):
        ax.add_patch(Patch(list(poly.exterior.coords), facecolor=color,
                           edgecolor=edgecolor or color, alpha=alpha,
                           linewidth=linewidth))
        for hole in poly.interiors:
            ax.add_patch(Patch(list(hole.coords), facecolor="white",
                               edgecolor=edgecolor or color, alpha=alpha,
                               linewidth=linewidth))


def outline(ax, geometry, color, linewidth=.6, linestyle="-"):
    for poly in polygons(geometry):
        ax.plot(*poly.exterior.xy, color=color, lw=linewidth, ls=linestyle)
        for ring in poly.interiors:
            xy = list(ring.coords)
            ax.plot([p[0] for p in xy], [p[1] for p in xy],
                    color=color, lw=linewidth, ls=linestyle)


def page_array(page, clip=None, scale=2):
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=clip, alpha=False)
    return np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)


def save_figure(fig, path):
    fig.savefig(path, dpi=190, facecolor="white", bbox_inches="tight")
    plt.close(fig)


def require_v2(measurements, final_pdf, objects):
    if measurements.get("version") != 2 or measurements.get("revision") != "V2":
        raise ValueError("Mediciones sin revisión V2: no se usarán los archivos copiados de V1.")
    if measurements.get("fuente_sha256") != sha256(final_pdf):
        raise ValueError("El SHA del PDF final no coincide con la fuente de las mediciones.")
    names = {o["nombre"] for o in objects}
    mandatory = {"P_interior_trastero_norte_dintel", "P_porton_trastero_sur_dintel"}
    if not mandatory.issubset(names):
        raise ValueError("Falta la geometría de los huecos nuevos del trastero.")
    old = [n for n in names if n.startswith(("Pilar_pergola_", "Viga_pergola_"))]
    if old:
        raise ValueError("Aún hay pilares/vigas de la pérgola sustituida: " + ", ".join(old))
    seqs = {o.get("seqno_pdf_v2") for o in objects}
    if not {1759, 1761, 1763, 1765, 59509, 59511}.issubset(seqs):
        raise ValueError("Las mediciones no incluyen los seis paños del trastero definitivo.")


def ortho_registry(path, blend_hash, measurements_hash, require=False):
    if not path.exists():
        if require:
            raise ValueError("Falta el registro ortográfico V2. Ejecutar vistas_control_v2.py primero.")
        return None
    reg = read_json(path)
    if reg.get("revision") != "V2":
        raise ValueError("El registro ortográfico no corresponde a V2.")
    if reg.get("modelo_sha256",reg.get("fuentes",{}).get("modelo_sha256")) != blend_hash:
        raise ValueError("Las ortográficas pertenecen a otra versión del .blend.")
    if reg.get("mediciones_sha256",reg.get("fuentes",{}).get("mediciones_sha256")) != measurements_hash:
        raise ValueError("Las ortográficas pertenecen a otras mediciones.")
    views = reg.get("vistas", [])
    if require and len(views) < 5:
        raise ValueError("El registro V2 tiene menos de cinco vistas ortográficas.")
    for view in views:
        view.setdefault("archivo",view.get("png"));view.setdefault("sha256",view.get("png_sha256"))
        image = local(view["archivo"])
        if not image.is_file() or not image.is_relative_to(ROOT / "control/visual_v2"):
            raise ValueError("Ruta de ortográfica ausente o ajena a visual_v2: " + str(image))
        if view.get("sha256") and view["sha256"] != sha256(image):
            raise ValueError("La ortográfica cambió después de su registro: " + image.name)
    return reg


def top_sheet(objects, audit, final_doc, output, z):
    factor = audit["factor_m_por_pt"]
    origin = audit["registro"]["origen_modelo_v1_pdf_pt"]
    offset = audit["registro"]["planta_izquierda_a_v1_pdf_pt"]
    # No ajuste libre: conversión única del plano izquierdo registrado +112,68 pt.
    ox, oy = origin[0] - offset[0], origin[1] - offset[1]
    clip = fitz.Rect(70, 44, 465, 790)
    extent = [(clip.x0 - ox) * factor, (clip.x1 - ox) * factor,
              (oy - clip.y1) * factor, (oy - clip.y0) * factor]
    source_walls = unary_union([Polygon(poly) for wall in audit["muros"]
                               for poly in wall["poligonos_xy_m"]])
    base_walls = unary_union([mesh_slice(o, z) for o in objects
                             if o.get("seqno_pdf_v2") is not None
                             and o["categoria"] == "muro_vivienda"])
    actual_parcel = unary_union([mesh_xy(o) for o in objects if o["categoria"] == "parcela"])
    actual_pool = unary_union([mesh_xy(o) for o in objects if o["categoria"] == "piscina"])
    fig, axes = plt.subplots(1, 2, figsize=(11.7, 12.1))
    for ax in axes:
        ax.set_aspect("equal")
        ax.set_xlim(-1.2, 20)
        ax.set_ylim(-1, 39)
        ax.set_xlabel("X · m")
        ax.set_ylabel("Y · m")
        ax.grid(alpha=.12)
    axes[1].imshow(page_array(final_doc[0], clip), extent=extent, alpha=.82)
    trastero_seqs = set(audit["trastero"]["muros_seqno_pdf"])
    for ax in axes:
        outline(ax, actual_parcel, "#202020", 1)
        fill(ax, actual_pool, "#b4e6ed", .50 if ax is axes[1] else 1)
        for obj in objects:
            if obj["categoria"] not in {"muro_vivienda","tendedero"}:
                continue
            color = NEW if obj.get("seqno_pdf_v2") in trastero_seqs or "trastero" in obj["nombre"].lower() else WALL
            cut = mesh_slice(obj, z)
            if ax is axes[1]:
                outline(ax, cut, color, .8)
            else:
                fill(ax, cut, color, .85)
        # Carpinterías son las mallas medidas. No recrear símbolos de puerta.
        for obj in objects:
            if obj["categoria"] in {"carpinteria", "vidrio"}:
                outline(ax, mesh_slice(obj, z), "#253944", .45)
        if ax is axes[1]:
            outline(ax, source_walls, SOURCE, .4, "--")
    axes[0].set_title(f"Modelo V2: corte horizontal real Z={z:.2f} m\nMuros existentes rojo · trastero ocre")
    axes[1].set_title("PDF definitivo página1, planta izquierda + mesh medido\nRegistro X +112,68 pt · sin reescala ni ajuste visual")
    fig.text(.5, .014,
             "La cota directa prevalece sobre residuos gráficos. Líneas azules: rellenos del PDF; rojo/ocre: mesh.\n"
             "El cerramiento parcelario aquí se muestra por su lindero documental; las ortográficas 3D están en hojas separadas.",
             ha="center", fontsize=8)
    fig.subplots_adjust(bottom=.065, wspace=.19)
    path = output / "01_planta_superposicion_final.png"
    save_figure(fig, path)
    parcel_ref = Polygon(audit["parcela"]["poligono_xy_m"])
    pool_ref = Polygon(audit["piscina"]["poligono_xy_m"])
    return path, {
        "corte_z_m": z,
        "transformacion": {"factor_m_por_pt": factor, "origen_pdf_izquierdo_pt": [ox, oy],
                           "x": "(u − 92,96) × 0,05291666666666667", "y": "(770,32 − v) × 0,05291666666666667"},
        "muros_vector_vs_mesh": {"area_vector_m2": source_walls.area,
                                "area_mesh_m2": base_walls.area,
                                "diferencia_simetrica_m2": source_walls.symmetric_difference(base_walls).area,
                                "hausdorff_m": source_walls.hausdorff_distance(base_walls),
                                "alcance": "Paños base con seqno del PDF; excluye dinteles/antepechos añadidos por Z. Sin criterio APTO."},
        "parcela": {"area_mesh_m2": actual_parcel.area, "area_vector_m2": parcel_ref.area,
                    "hausdorff_m": actual_parcel.hausdorff_distance(parcel_ref)},
        "piscina": {"area_mesh_m2": actual_pool.area, "area_vector_m2": pool_ref.area,
                    "hausdorff_m": actual_pool.hausdorff_distance(pool_ref),
                    "criterio": "Cotas directas 3,50×5,00; residual vectorial registrado, sin profundidad ni nivel de agua definido."},
    }


def elevation_sheet(spec, objects, audit, basic_doc, output):
    name, haxis, sign, daxis, reverse, origin, floor, clip_rect, direction = spec
    faces = []
    new_seqs = set(audit["trastero"]["muros_seqno_pdf"])
    for obj in objects:
        if obj["categoria"] not in ARCHITECTURE:
            continue
        new = (obj.get("seqno_pdf_v2") in new_seqs or "trastero" in obj["nombre"].lower())
        for face in obj["caras"]:
            vertices = [obj["vertices"][i] for i in face]
            coordinates = [(sign * v[haxis], v[2]) for v in vertices]
            if Polygon(coordinates).area < 1e-9:
                continue
            faces.append((sum(v[daxis] for v in vertices) / len(vertices),
                          coordinates, obj["categoria"], new))
    if not faces:
        raise ValueError("No hay caras proyectables del modelo V2.")
    faces.sort(key=lambda x: x[0], reverse=reverse)
    fig, axes = plt.subplots(2, 1, figsize=(12, 6.3))
    for _, coordinates, category, new in faces:
        color = ("#4f707b" if category == "vidrio" else "#30383e" if category == "carpinteria"
                 else "#e8d2a8" if new else "#eeeeea")
        axes[0].add_patch(Patch(coordinates, facecolor=color,
                               edgecolor=NEW if new else "#535353", linewidth=.25))
    clip = fitz.Rect(*clip_rect)
    factor = audit["factor_m_por_pt"]
    extent = [(clip.x0 - origin) * factor, (clip.x1 - origin) * factor,
              (floor - clip.y1) * factor, (floor - clip.y0) * factor]
    axes[1].imshow(page_array(basic_doc[37], clip), extent=extent)
    x0 = min(min(p[0] for p in face[1]) for face in faces) - .75
    x1 = max(max(p[0] for p in face[1]) for face in faces) + .75
    tb = Polygon(audit["trastero"]["contorno_exterior"]["poligono_xy_m"]).bounds
    ends = [sign * tb[haxis], sign * tb[haxis + 2]]
    # Banda documental, no sustitución de la geometría: identifica el cambio V2.
    for ax in axes:
        ax.set_aspect("equal")
        ax.set_xlim(x0, x1)
        ax.set_ylim(-.45, 5.8)
        ax.axhline(0, color="black", linewidth=.4)
        ax.set_ylabel("Z · m")
        ax.add_patch(Rectangle((min(ends), -.2), abs(ends[1] - ends[0]), 4.7,
                               fill=False, edgecolor=NEW, linestyle="--", linewidth=.65))
    axes[0].set_title("Modelo V2: " + name.replace("_", " ") + " · mirada " + direction, fontsize=10)
    axes[1].set_title("Alzado básico PDF38: referencia del edificio existente · trastero V2 no dibujado aquí", fontsize=10)
    axes[1].set_xlabel("Coordenada horizontal del modelo · m")
    fig.text(.5, .014,
             "Banda ocre: ámbito del trastero añadido. Sus Z 3,35/3,70/4,40 y huecos 2,03/2,50 proceden del usuario.\n"
             "El PDF definitivo sólo aporta XY. El cotejo no exige coincidir con la pérgola antigua del alzado básico.",
             ha="center", fontsize=8)
    fig.subplots_adjust(bottom=.19, hspace=.48)
    path = output / ("alzado_" + name + ".png")
    save_figure(fig, path)
    return path


def geometry_rows(objects, audit):
    by_seq = {}
    by_name = {o["nombre"]: o for o in objects}
    for o in objects:
        if o.get("seqno_pdf_v2") is not None:
            by_seq.setdefault(o["seqno_pdf_v2"], []).append(o)

    def bounds(seq):
        return unary_union([mesh_xy(o) for o in by_seq[seq]]).bounds

    w, e, n, s = bounds(1763), bounds(59509), bounds(1759), bounds(1765)
    internal_width, internal_depth = e[0] - w[2], n[1] - s[3]
    pool = unary_union([mesh_xy(o) for o in objects if o["categoria"] == "piscina"])
    parcel = unary_union([mesh_xy(o) for o in objects if o["categoria"] == "parcela"])
    rows = []

    def row(label, value, target, status, source):
        rows.append({"elemento": label, "modelo": value, "referencia": target,
                     "diferencia": None if target is None else value - target,
                     "obtencion": status, "fuente": source})

    row("Trastero ancho interior m", internal_width, 7.15, "Cota directa", "PDF final1")
    row("Trastero fondo interior m", internal_depth, 3.94, "Cota directa", "PDF final1")
    row("Trastero fondo hasta exterior sur m", n[1] - s[1], 4.19, "Cota directa", "PDF final1")
    nh = by_name["P_interior_trastero_norte_dintel"]["bbox_xyz"]
    sh = by_name["P_porton_trastero_sur_dintel"]["bbox_xyz"]
    row("Trastero hueco norte ancho m", nh[3] - nh[0], .96, "Cota directa", "PDF final1")
    row("Trastero portón sur ancho m", sh[3] - sh[0],
        audit["trastero"]["porton_sur"]["ancho_vector_m"], "Calculada del vector", "PDF final1")
    row("Trastero superficie interior más umbral m²",
        internal_width * internal_depth + (sh[3] - sh[0]) * (sh[4] - sh[1]),
        29.17, "Deducción del cómputo; no forzar perímetro", "Etiqueta PDF final1")
    pb = pool.bounds
    row("Piscina ancho XY m", pb[2] - pb[0], 3.5, "Cota directa", "PDF final1")
    row("Piscina largo XY m", pb[3] - pb[1], 5.0, "Cota directa", "PDF final1")
    row("Piscina superficie XY m²", pool.area, 17.5, "Cotas directas", "PDF final1")
    row("Parcela área del trazo m²", parcel.area, 635.60,
        "Vector del lindero; área rotulada no fuerza contorno", "Básico memoria / PDF final1")
    for opening in (o for o in objects if o["nombre"].endswith("_dintel")
                    and o["nombre"] not in {"P_interior_trastero_norte_dintel", "P_porton_trastero_sur_dintel"}):
        box = opening["bbox_xyz"]
        row(opening["nombre"].removesuffix("_dintel") + " ancho de hueco m",
            max(box[3] - box[0], box[4] - box[1]), None,
            "Mesh medido; comparar con tabla numérica V2", opening.get("fuente", ""))
    return rows


def level_rows(objects):
    by_name = {o["nombre"]: o for o in objects}
    rows = []

    def row(label, actual, expected, origin, source, objname):
        rows.append({"elemento": label, "z_modelo_m": actual, "z_referencia_m": expected,
                     "diferencia_m": actual - expected, "origen": origin,
                     "fuente": source, "objetos": objname})

    groups = [
        ("Suelo vivienda", "Suelo_vivienda", 2, 0, "Básico", "Datum PDF38/39"),
        ("Jardín", "Jardin_cesped", 5, -.15, "Básico", "PDF38/39"),
        ("Forjado inferior edificio existente", "Forjado_cubierta_3_35_3_70", 2, 3.35, "Básico", "PDF38/39"),
        ("Forjado superior edificio existente", "Forjado_cubierta_3_35_3_70", 5, 3.7, "Básico", "PDF38/39"),
        ("Cielorraso sólo vivienda existente", "Cielorraso_vivienda_existente_3_20", 5, 3.2, "Calculada del básico", "Secciones1/3; no se aplica al trastero"),
        ("Peto bajo existente", "Peto_bajo_N", 5, 4.4, "Básico", "PDF38/39"),
        ("Portal existente coronación", "Peto_portal_W", 5, 4.75, "Básico", "PDF38/39"),
        ("Peto alto existente", "Peto_central_N", 5, 5.1, "Básico", "PDF38/39"),
        ("Trastero forjado inferior", "Forjado_cubierta_3_35_3_70", 2, 3.35, "Usuario V2", "Confirmación expresa del usuario; forjado continuo"),
        ("Trastero forjado superior", "Forjado_cubierta_3_35_3_70", 5, 3.7, "Usuario V2", "Confirmación expresa del usuario; forjado continuo"),
        ("Trastero puerta norte dintel", "P_interior_trastero_norte_dintel", 2, 2.03, "Usuario V2", "Confirmación expresa del usuario"),
        ("Trastero portón frontal dintel", "P_porton_trastero_sur_dintel", 2, 2.5, "Usuario V2", "Confirmación expresa del usuario"),
    ]
    for label, prefix, axis, expected, origin, source in groups:
        items = [o for o in objects if o["nombre"] == prefix or o["nombre"].startswith(prefix + "_")]
        if not items:
            raise ValueError("No se encuentra el mesh de nivel: " + prefix)
        actual = min(o["bbox_xyz"][axis] for o in items) if axis == 2 else max(o["bbox_xyz"][axis] for o in items)
        row(label, actual, expected, origin, source, ", ".join(o["nombre"] for o in items))
    petos = [o for o in objects if o["nombre"].startswith("Peto_trastero_")]
    if len(petos) < 3:
        raise ValueError("Faltan petos del trastero V2.")
    for o in petos:
        row(o["nombre"] + " coronación", o["bbox_xyz"][5], 4.4, "Usuario V2",
            "Confirmación expresa del usuario", o["nombre"])
    return rows


def section_sheet(rows, basic_doc, output):
    fig, axes = plt.subplots(1, 2, figsize=(15, 10), width_ratios=[1.12, 1.8])
    ax = axes[0]
    for i, row in enumerate(rows):
        color = USER if row["origen"] == "Usuario V2" else SOURCE
        ax.plot([i - .30, i + .30], [row["z_referencia_m"]] * 2, color=color, linewidth=1.1)
        ax.scatter([i], [row["z_modelo_m"]], color="black", marker="x", s=22, linewidths=.8)
    ax.set_xticks(range(len(rows)), [row["elemento"] for row in rows], rotation=90, fontsize=7)
    ax.set_ylim(-.5, 5.65)
    ax.set_ylabel("Z · m")
    ax.grid(axis="y", alpha=.25)
    ax.set_title("Cotas extraídas de los meshes V2\n× negro modelo · azul básico · ocre usuario V2", fontsize=10)
    axes[1].imshow(page_array(basic_doc[38], scale=1.6))
    axes[1].axis("off")
    axes[1].set_title("Secciones originales PDF39\nReferencia de la geometría existente; no muestran el trastero definitivo", fontsize=10)
    fig.text(.5, .015,
             "Comparación de niveles, no sección constructiva inventada. No se documenta un cielorraso nuevo del trastero.\n"
             "La discrepancia de ancho del paño alto entre planta y trasero/sección3 permanece identificada en el control numérico.",
             ha="center", fontsize=9)
    fig.subplots_adjust(left=.06, right=.98, bottom=.27, top=.92, wspace=.18)
    path = output / "secciones_niveles_fuentes_v2.png"
    save_figure(fig, path)
    return path


def write_csv(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


def image_flowable(path, max_width=742, max_height=457):
    with PILImage.open(path) as img:
        width, height = img.size
    scale = min(max_width / width, max_height / height)
    return Image(str(path), width=width * scale, height=height * scale)


def report(output, top, elevations, section, rows, levels, ortho, measurements, blend_hash):
    styles = getSampleStyleSheet()
    styles["BodyText"].fontSize = 9
    styles["BodyText"].leading = 12
    story = []

    def p(text, style="BodyText"):
        story.append(Paragraph(text, styles[style]))
        story.append(Spacer(1, 6))

    p("Calle Macarena · cotejo visual V2", "Title")
    p("Planta definitiva con trastero · modelo 1:1 · geometría de los meshes reales")
    p("Este documento no hereda ningún resultado APTO ni la cuenta de controles de V1. "
      "El resultado numérico V2 debe evaluarse por separado antes de los renders fotográficos.")
    p("Planta: página1 izquierda del PDF definitivo, registrada +112,68 pt en X, escala nominal fija "
      "1:150 = 0,05291666666666667 m/pt. Una cota escrita prevalece sobre su pequeño residual gráfico; "
      "por ello el contorno medido no se deforma para ocultar diferencias del dibujo.")
    p("Alzados y secciones: páginas38 y39 del básico. Comparan la geometría existente. "
      "La antigua pérgola se sustituye por el trastero del plano final: el volumen nuevo no puede "
      "coincidir con las vistas antiguas en ese ámbito.")
    p("Trastero: inferior/superior del forjado 3,35/3,70 m, coronación de peto 4,40 m, "
      "puerta norte 2,03 m y portón frontal 2,50 m son confirmaciones expresas del usuario V2. "
      "Estas alturas no están escritas en el PDF definitivo.")
    p("Persisten datos no definidos: profundidad/fondo de piscina, niveles reales de agua y peldaños, "
      "mecanismo y despiece del portón, capas/pendientes de cubierta y cielorraso del trastero. "
      "Mobiliario, vehículos, vegetación, materiales y luminarias son visualización.")
    p("Identidad del modelo: SHA256 " + blend_hash, "Code")
    p("Mediciones revisión " + escape(str(measurements["revision"])) + "; documento generado " +
      datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
    story.append(PageBreak())
    p("Planta del mesh y superposición con el plano definitivo", "Heading1")
    story.append(image_flowable(top, max_height=480))
    story.append(PageBreak())
    for name, image in elevations:
        p("Alzado · " + name.replace("_", " "), "Heading1")
        story.append(image_flowable(image, max_height=466))
        story.append(PageBreak())
    p("Niveles del modelo y secciones originales", "Heading1")
    story.append(image_flowable(section, max_height=476))
    story.append(PageBreak())
    if ortho:
        for view in ortho["vistas"]:
            p("Vista ortográfica V2 · " + escape(view.get("titulo", view["id"])), "Heading1")
            p("Fuente: mismo .blend y mismas mediciones que este informe. " +
              escape(view.get("alcance", "Vista analítica de control")))
            story.append(image_flowable(local(view["archivo"]), max_height=450))
            story.append(PageBreak())
    else:
        p("Vistas ortográficas 3D pendientes", "Heading2")
        p("No se han incorporado imágenes de V1. Generar vistas_control_v2.py y repetir "
          "con --require-ortho para cerrar este documento de control visual.")
    p("Geometría principal · valores medidos", "Heading1")
    table_data = [["Elemento", "Modelo", "Referencia", "Diferencia", "Obtención / fuente"]]
    for r in rows:
        table_data.append([Paragraph(escape(r["elemento"]), styles["BodyText"]),
                           f'{r["modelo"]:.5f}',
                           "—" if r["referencia"] is None else f'{r["referencia"]:.5f}',
                           "—" if r["diferencia"] is None else f'{r["diferencia"]:+.6f}',
                           Paragraph(escape(r["obtencion"] + " · " + r["fuente"]), styles["BodyText"])])
    table = Table(table_data, colWidths=[225, 75, 75, 75, 292], repeatRows=1)
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5eaf0")),
                               ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                               ("FONTSIZE", (0, 0), (-1, -1), 8),
                               ("VALIGN", (0, 0), (-1, -1), "TOP"),
                               ("GRID", (0, 0), (-1, -1), .3, colors.lightgrey)]))
    story.append(table)
    story.append(PageBreak())
    p("Niveles · origen de las referencias", "Heading1")
    level_data = [["Elemento", "Z modelo", "Z referencia", "Diferencia", "Origen"]]
    for r in levels:
        level_data.append([Paragraph(escape(r["elemento"]), styles["BodyText"]),
                           f'{r["z_modelo_m"]:.5f}', f'{r["z_referencia_m"]:.2f}',
                           f'{r["diferencia_m"]:+.6f}',
                           Paragraph(escape(r["origen"] + " · " + r["fuente"]), styles["BodyText"])])
    table = Table(level_data, colWidths=[225, 75, 75, 75, 292], repeatRows=1)
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5eaf0")),
                               ("FONTSIZE", (0, 0), (-1, -1), 8),
                               ("VALIGN", (0, 0), (-1, -1), "TOP"),
                               ("GRID", (0, 0), (-1, -1), .3, colors.lightgrey)]))
    story.append(table)
    SimpleDocTemplate(str(output / "informe_visual_v2.pdf"), pagesize=landscape(A4),
                      rightMargin=50, leftMargin=50, topMargin=30, bottomMargin=30).build(story)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, default=ROOT / "Calle_Macarena_modelo_1a1.blend")
    parser.add_argument("--mediciones", type=Path, default=ROOT / "control/mediciones_mesh_real.json")
    parser.add_argument("--ortho-registro", type=Path, default=ROOT / "control/visual_v2/ortograficas/registro_v2.json")
    parser.add_argument("--require-ortho", action="store_true")
    parser.add_argument("--corte-z", type=float, default=1.2)
    args = parser.parse_args()
    blend, measurements_path = local(args.blend), local(args.mediciones)
    final_pdf = ROOT / "fuentes/planta_final_proyecto_obra.pdf"
    basic_pdf = ROOT / "fuentes/proyecto_basico.pdf"
    audit_path = ROOT / "analisis_v2/auditoria_planta_final.json"
    heights_audit = ROOT / "analisis_v2/auditoria_alturas_trastero.json"
    confirmation_path = ROOT / "modelo/confirmaciones_usuario_v2.json"
    for path in (blend, measurements_path, final_pdf, basic_pdf, audit_path,
                 heights_audit, confirmation_path):
        if not path.is_file() or not path.is_relative_to(ROOT):
            raise ValueError("Fuente ausente o fuera de V2: " + str(path))
    if not 0 < args.corte_z < 2.03:
        raise ValueError("Usar 0<Z<2,03 para mostrar ambos huecos nuevos sin interceptar su dintel.")
    audit = read_json(audit_path)
    measurements = read_json(measurements_path)
    objects = measurements["objetos"]
    require_v2(measurements, final_pdf, objects)
    confirmed = read_json(confirmation_path)
    if confirmed.get("fuente_planta", {}).get("sha256") != sha256(final_pdf):
        raise ValueError("Las confirmaciones V2 no identifican el PDF final actual.")
    blend_hash = sha256(blend)
    measurements_hash = sha256(measurements_path)
    ortho_path = local(args.ortho_registro)
    ortho = ortho_registry(ortho_path, blend_hash, measurements_hash, args.require_ortho)
    output = ROOT / "control/visual_v2/laminas"
    output.mkdir(parents=True, exist_ok=True)
    with fitz.open(final_pdf) as final_doc, fitz.open(basic_pdf) as basic_doc:
        if len(final_doc) != 1 or len(basic_doc) < 39:
            raise ValueError("Número de páginas inesperado en las fuentes V2/básico.")
        top, stats = top_sheet(objects, audit, final_doc, output, args.corte_z)
        elevations = [(spec[0], elevation_sheet(spec, objects, audit, basic_doc, output))
                      for spec in ALZADOS]
        rows = geometry_rows(objects, audit)
        levels = level_rows(objects)
        section = section_sheet(levels, basic_doc, output)
    write_csv(output / "tabla_geometria_visual_v2.csv", rows)
    write_csv(output / "tabla_niveles_fuentes_v2.csv", levels)
    report(output, top, elevations, section, rows, levels, ortho, measurements, blend_hash)
    files = [top, *(p for _, p in elevations), section,
             output / "tabla_geometria_visual_v2.csv", output / "tabla_niveles_fuentes_v2.csv",
             output / "informe_visual_v2.pdf"]
    manifest = {
        "revision": "V2", "fecha_utc": datetime.now(timezone.utc).isoformat(),
        "alcance": "Documentación y cotejo visual; sin dictamen APTO y sin reutilizar controles/láminas V1.",
        "modelo": relative(blend), "modelo_sha256": blend_hash,
        "mediciones": relative(measurements_path), "mediciones_sha256": measurements_hash,
        "fuentes": [{"archivo": relative(p), "sha256": sha256(p)}
                    for p in (final_pdf, basic_pdf, audit_path, heights_audit, confirmation_path)],
        "ortograficas": None if ortho is None else {"registro": relative(ortho_path), "sha256": sha256(ortho_path), "vistas": len(ortho["vistas"])},
        "estadisticas_documentales": stats,
        "niveles": levels,
        "salidas": [{"archivo": relative(p), "sha256": sha256(p)} for p in files],
        "secciones": "Se comparan cotas medidas con las secciones originales. No se inventan trazas de corte nuevas.",
        "limites": ["PDF final sin Z propias; trastero Z confirmado usuario",
                    "Piscina sin profundidad, contrahuellas ni nivel real de agua",
                    "Portón sin mecanismo/despiece definido",
                    "No se define cielorraso del trastero",
                    "Diferencia paño alto planta/trasero/sección3 del básico"]}
    (output / "registro_laminas_v2.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"informe": relative(output / "informe_visual_v2.pdf"),
                      "revision": "V2", "ortograficas": 0 if ortho is None else len(ortho["vistas"]),
                      "dictamen": "sin dictamen; revisar control numérico V2"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
