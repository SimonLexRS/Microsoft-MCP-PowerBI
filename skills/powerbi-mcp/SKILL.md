---
name: powerbi-mcp
description: Construye modelos semanticos y dashboards de Power BI contra Power BI Desktop local, usando el MCP powerbi-modeling (tablas, relaciones, medidas DAX) y los CLIs powerbi-report-author / powerbi-desktop (visuales PBIR con validacion, recarga en vivo y screenshots). Se activa con "/powerbi-mcp" explicito o con intencion como "carga estos datos en power bi", "crea un dashboard en power bi", "agrega una pagina al informe", "crea medidas DAX", "conecta a power bi desktop".
---

# Skill: Power BI MCP — modelo semántico + dashboards en vivo

Construyes modelos semánticos y dashboards de Power BI de punta a punta contra
una instancia local de Power BI Desktop, con el archivo abierto todo el tiempo.

## Precondiciones (verificar antes de empezar)

1. Windows con Power BI Desktop abierto y un proyecto **.pbip** cargado
   (si es .pbix: el usuario debe hacer `Guardar como > Power BI project files`).
2. Servidor MCP `powerbi-modeling` conectado (config en `.mcp.json` del kit:
   `npx -y @microsoft/powerbi-modeling-mcp@latest --start --skipconfirmation`).
3. CLIs instalados: `powerbi-report-author --version` y `powerbi-desktop --version`.
   Si faltan: `npm i -g @microsoft/powerbi-report-authoring-cli @microsoft/powerbi-desktop-bridge-cli`.

## División de responsabilidades (regla central)

- **Modelo semántico** (tablas, relaciones, medidas, DAX) → SOLO herramientas
  MCP. Los cambios van a la instancia viva; no requieren reload.
- **Visuales y páginas** (PBIR) → SOLO archivos JSON + CLIs. El MCP no tiene
  ninguna herramienta de reporte.

## Flujo

### 1. Conexión
`connection_operations → ListLocalInstances` → `Connect` con
`data source=localhost:<puerto>;Application Name=MCP-PBIModeling`.
El puerto cambia en cada apertura de Desktop: reconectar si Desktop se reinició.

### 2. Modelo semántico
- Tabla desde CSV: `table_operations → Create` con expresión M
  (`Csv.Document(File.Contents("C:\\ruta\\absoluta.csv"), [Delimiter=",",
  Columns=<N exacto>, Encoding=65001, QuoteStyle=QuoteStyle.Csv])` +
  `Table.PromoteHeaders` + `Table.TransformColumnTypes`).
  En el array `columns`: dataType de fechas es `DateTime` (no `date`).
- **Refresh inmediato tras cada Create**: `partition_operations →
  RefreshWithXMLA` (refreshType Full) — la tabla está vacía hasta refrescar.
- Relaciones: dimensión = lado One, `crossFilteringBehavior: "Single"`
  (1:1 → `"BothDirections"` obligatorio). Evitar rutas ambiguas.
- Medidas: tabla `_Measures` (`daxExpression: ROW("placeholder", BLANK())`,
  sin `columns`) → `measure_operations → Create` en lote → siempre `DIVIDE()`.
- Validar todo con `dax_query_operations → Execute` contra conteos fuente.
- Respaldo: `database_operations → ExportToBimFile`.

### 3. Dashboard en vivo (ciclo)
```
editar archivos PBIR (usar scripts/build_visuals.py del kit como generador)
→ powerbi-report-author validate "<dir .Report>"     (0 errores o volver a editar)
→ powerbi-desktop status                              (obtener PID)
→ powerbi-desktop reload --pid <pid>                  (recarga sin cerrar Desktop)
→ powerbi-desktop screenshot-all --pid <pid> --output-dir shots/
→ leer las capturas y verificar uno mismo             (iterar si hace falta)
```
Serial por PID; nunca reload y screenshot en paralelo.

### Reglas PBIR que rompen el render si se violan
1. `$schema` de visual.json: `visualContainer/2.10.0`. Ante formato dudoso,
   pedir al usuario crear UN visual a mano, guardarlo y copiar ese formato.
2. Nunca `"active": true` en projections → tableEx queda sin filas.
3. Nunca `filterConfig` en slicers → selección espuria aleatoria. En visuales
   de datos sí: un filtro por campo (Categorical columnas, Advanced medidas).
4. `pages.json` debe existir antes de la primera apertura del proyecto.
5. Tipos validados: card, clusteredBarChart, clusteredColumnChart, lineChart,
   tableEx, slicer, textbox. Otros: `catalog describe <tipo>` primero.

### 4. Cierre
Recordar al usuario `Ctrl+S` en Desktop (el modelo vive en memoria hasta
guardar). Entregable .pbix: `Archivo > Guardar como > Power BI Desktop file`.

## Checkpoints que sí requieren al usuario
Convertir .pbix→.pbip, guardar con Ctrl+S, aprobar el MCP al iniciar sesión.
Todo lo demás (abrir Desktop, validar, recargar, verificar capturas) lo hace
el agente solo.
