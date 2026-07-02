# Instrucciones de agente — Kit Power BI MCP

Construyes modelos semánticos y dashboards de Power BI contra una instancia
local de Power BI Desktop, usando el MCP `powerbi-modeling` (modelo) y los
CLIs `powerbi-report-author` / `powerbi-desktop` (visuales, en vivo).

## Reglas duras

- El modelo semántico va SOLO por el MCP. Los visuales van SOLO por archivos
  PBIR + CLIs. Nunca escribas TMDL/model.bim a mano.
- Tras cada `table_operations → Create`: `partition_operations → RefreshWithXMLA`
  inmediato (la tabla está vacía hasta refrescar).
- DAX: siempre `DIVIDE()`, nunca `/`. Valida cada medida con
  `dax_query_operations → Execute` antes de darla por buena.
- En definiciones de columnas: dataType de fechas es `DateTime` (no `date`);
  `type date` va solo dentro de la expresión M.
- Tabla de medidas `_Measures`: `daxExpression: ROW("placeholder", BLANK())`,
  SIN array `columns`.
- Relaciones 1:1: `crossFilteringBehavior: "BothDirections"` obligatorio.
- Antes de asumir nombres de herramientas o formatos: descubre en vivo
  (`ListLocalInstances`, `catalog describe <tipo>`, `validate`).

## Reglas de visuales (PBIR) — violarlas rompe el render

1. `$schema` de visual.json: `visualContainer/2.10.0`. Si dudas del formato,
   pide al usuario crear UN visual a mano en Desktop, guárdalo y copia el
   formato exacto del archivo generado.
2. NUNCA pongas `"active": true` en projections → tabla sin filas.
3. NUNCA pre-declares `filterConfig` en slicers → selección espuria aleatoria.
   En visuales de datos sí va: un filtro por campo (`Categorical` columnas,
   `Advanced` medidas).
4. `pages.json` debe existir ANTES de que Desktop abra el proyecto por primera
   vez, o Desktop regenera las carpetas de página y borra los visuales.
5. Usa `scripts/build_visuals.py` como generador base (formato ya validado).
   Tipos probados: card, clusteredBarChart, clusteredColumnChart, lineChart,
   tableEx, slicer, textbox.

## Flujo por fases

1. **Entorno**: `powerbi-desktop status` (¿Desktop abierto con .pbip?). Si el
   proyecto es .pbix, el usuario debe convertirlo: Guardar como → .pbip.
2. **Conexión**: `ListLocalInstances` → `Connect` al puerto local.
3. **Modelo**: tablas (M desde CSV, ruta absoluta, `Columns=N` exacto,
   UTF-8, QuoteStyle.Csv) → refresh → relaciones (dims primero, evita rutas
   ambiguas) → `_Measures` → medidas → validación DAX contra conteos fuente.
4. **Dashboard en vivo** (ciclo, sin cerrar Desktop):
   editar PBIR → `powerbi-report-author validate <dir .Report>` →
   `powerbi-desktop reload --pid <pid>` → `screenshot-all` → revisar capturas
   tú mismo → iterar. Serial por PID, nunca en paralelo.
5. **Cierre**: `ExportToBimFile` de respaldo; recuerda al usuario `Ctrl+S`
   en Desktop (los cambios de modelo viven en memoria hasta guardar).

## Checkpoints que SÍ requieren al usuario

- Convertir .pbix → .pbip (GUI).
- Guardar (`Ctrl+S`) en Desktop.
- Aprobar el servidor MCP al iniciar sesión.
- Reiniciar el cliente si se editó `.mcp.json`.

Todo lo demás (abrir Desktop, recargar, verificar con screenshots) lo haces
tú con los CLIs, sin pedir pasos manuales.
