"""Generador de paginas y visuales PBIR para proyectos Power BI (.pbip).

Formato validado contra archivos visual.json generados por el propio
Power BI Desktop (build 2.155+, jun 2026). Reglas criticas incorporadas:
  1. $schema = visualContainer/2.10.0
  2. Sin "active" en projections (deja tablas tableEx sin filas)
  3. Sin filterConfig en slicers (causa seleccion espuria aleatoria);
     en visuales de datos SI va: un filtro por campo usado.

Uso:
  1. Editar REPORT_DIR y PAGE_DEFS al final del archivo.
  2. Ejecutar con Power BI Desktop abierto:  python build_visuals.py [claves...]
  3. Validar:   powerbi-report-author validate "<REPORT_DIR>"
  4. Recargar:  powerbi-desktop reload --pid <pid>
  5. Verificar: powerbi-desktop screenshot-all --pid <pid> --output-dir shots/
"""
import json
import secrets
import sys
from pathlib import Path

# ----------------------------------------------------------------------------
# CONFIGURACION — ajustar a tu proyecto
# ----------------------------------------------------------------------------
ROOT = Path(__file__).parent.parent          # raiz del proyecto .pbip
REPORT_DIR = "MiInforme.Report"              # carpeta <nombre>.Report
MEASURES_TABLE = "_Measures"                 # tabla contenedora de medidas

PAGES = ROOT / REPORT_DIR / "definition" / "pages"

SCHEMA_VC = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.10.0/schema.json"
PAGE_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json"


def hexid():
    return secrets.token_hex(10)  # ids de 20 caracteres hex, como los de Desktop


# ------------------------------ campos ---------------------------------------

def col_field(entity, prop):
    return {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}


def meas_field(prop):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": MEASURES_TABLE}}, "Property": prop}}


def filter_entry(field):
    """filterConfig por campo: Categorical para columnas, Advanced para medidas."""
    ftype = "Categorical" if "Column" in field else "Advanced"
    return {"name": hexid(), "field": field, "type": ftype}


def proj(field, ref):
    # nunca incluir "active" — ver regla 2 del encabezado
    return {"field": field, "queryRef": ref, "nativeQueryRef": ref.split(".", 1)[1]}


def col_proj(entity, prop):
    return proj(col_field(entity, prop), f"{entity}.{prop}")


def meas_proj(prop):
    return proj(meas_field(prop), f"{MEASURES_TABLE}.{prop}")


# ------------------------------ visuales -------------------------------------

def visual_json(name, position, visual, all_fields):
    d = {"$schema": SCHEMA_VC, "name": name, "position": position, "visual": visual}
    if all_fields:
        d["filterConfig"] = {"filters": [filter_entry(f) for f in all_fields]}
    return d


def v_textbox(text, font_size="20pt"):
    return {
        "visualType": "textbox",
        "objects": {"general": [{"properties": {"paragraphs": [{
            "textRuns": [{"value": text, "textStyle": {"fontWeight": "bold", "fontSize": font_size}}],
            "horizontalTextAlignment": "center",
        }]}}]},
    }, []


def v_card(measure):
    return {
        "visualType": "card",
        "query": {"queryState": {"Values": {"projections": [meas_proj(measure)]}}},
        "drillFilterOtherVisuals": True,
    }, [meas_field(measure)]


def v_bar(entity, category, measure, horizontal=True, chart_type=None):
    return {
        "visualType": chart_type or ("clusteredBarChart" if horizontal else "clusteredColumnChart"),
        "query": {"queryState": {
            "Category": {"projections": [col_proj(entity, category)]},
            "Y": {"projections": [meas_proj(measure)]},
        }},
        "drillFilterOtherVisuals": True,
    }, [col_field(entity, category), meas_field(measure)]


def v_line(entity, category, measure):
    return v_bar(entity, category, measure, chart_type="lineChart")


def v_table(cols):
    """cols: lista de ("col", entidad, columna) o ("meas", None, medida)."""
    projections, fields = [], []
    for kind, entity, prop in cols:
        if kind == "col":
            projections.append(col_proj(entity, prop))
            fields.append(col_field(entity, prop))
        else:
            projections.append(meas_proj(prop))
            fields.append(meas_field(prop))
    return {
        "visualType": "tableEx",
        "query": {"queryState": {"Values": {"projections": projections}}},
        "drillFilterOtherVisuals": True,
    }, fields


def v_slicer_dropdown(entity, prop):
    # sin filterConfig — ver regla 3 del encabezado
    return {
        "visualType": "slicer",
        "query": {"queryState": {"Values": {"projections": [col_proj(entity, prop)]}}},
        "objects": {
            "data": [{"properties": {"mode": {"expr": {"Literal": {"Value": "'Dropdown'"}}}}}],
            "general": [{"properties": {"orientation": {"expr": {"Literal": {"Value": "1D"}}}}}],
        },
        "drillFilterOtherVisuals": True,
    }, []


# ------------------------------ paginas --------------------------------------

def page_json(name, display_name):
    return {
        "$schema": PAGE_SCHEMA, "name": name, "displayName": display_name,
        "displayOption": "FitToPage", "height": 720, "width": 1280,
    }


registry_lines = []


def write_page(page_name, display_name, visuals_specs):
    page_dir = PAGES / page_name
    page_dir.mkdir(parents=True, exist_ok=True)
    (page_dir / "page.json").write_text(
        json.dumps(page_json(page_name, display_name), ensure_ascii=False, indent=2), encoding="utf-8")
    visuals_dir = page_dir / "visuals"
    visuals_dir.mkdir(exist_ok=True)
    registry_lines.append(f"\n## Pagina: {display_name} (`{page_name}`)\n")
    for label, position, (visual, fields) in visuals_specs:
        vname = hexid()
        (visuals_dir / vname).mkdir(exist_ok=True)
        (visuals_dir / vname / "visual.json").write_text(
            json.dumps(visual_json(vname, position, visual, fields), ensure_ascii=False, indent=2),
            encoding="utf-8")
        registry_lines.append(f"- `{vname}`: {label}")


# ----------------------------------------------------------------------------
# DEFINICION DE PAGINAS — reemplazar por las tuyas
# Layout de referencia (lienzo 1280x720): titulo y=0 h=60; fila de KPIs y=70
# h=110 (5 tarjetas: x=20,268,516,764,1012 / w=228, ultima 248); contenido
# y=200 h=490.
# ----------------------------------------------------------------------------
PAGE_DEFS = {
    "ejemplo": (hexid(), "Pagina de Ejemplo", [
        ("Titulo", {"x": 0, "y": 0, "z": 0, "width": 1280, "height": 60, "tabOrder": 0},
         v_textbox("Mi Dashboard")),
        ("KPI", {"x": 20, "y": 70, "z": 0, "width": 228, "height": 110, "tabOrder": 1},
         v_card("Total Ventas")),
        ("Barras por categoria", {"x": 20, "y": 200, "z": 0, "width": 620, "height": 490, "tabOrder": 2},
         v_bar("dim_producto", "categoria", "Total Ventas")),
        ("Slicer", {"x": 660, "y": 200, "z": 0, "width": 300, "height": 90, "tabOrder": 3},
         v_slicer_dropdown("dim_region", "region")),
    ]),
}


def main():
    requested = sys.argv[1:] or list(PAGE_DEFS)
    for key in requested:
        write_page(*PAGE_DEFS[key])

    new_hexes = [PAGE_DEFS[k][0] for k in requested]
    pages_file = PAGES / "pages.json"
    existing = json.loads(pages_file.read_text(encoding="utf-8"))["pageOrder"] if pages_file.exists() else []
    order = existing + [h for h in new_hexes if h not in existing]
    pages_file.write_text(json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json",
        "pageOrder": order,
        "activePageName": order[0],
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    registry_file = ROOT / "visual_registry.md"
    header = "" if registry_file.exists() else "# Visual Registry\n"
    prev = registry_file.read_text(encoding="utf-8") if registry_file.exists() else ""
    registry_file.write_text(prev + header + "\n".join(registry_lines), encoding="utf-8")
    print("Paginas creadas:", requested, "->", new_hexes)


if __name__ == "__main__":
    main()
