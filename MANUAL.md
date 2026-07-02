# Manual de uso completo

Flujo validado de punta a punta: CSVs crudos → modelo semántico → dashboard
multipágina, con Power BI Desktop abierto todo el tiempo.

## Fase 0 — Preparación

1. Crear un reporte en blanco en Power BI Desktop y guardarlo como **proyecto**:
   `Archivo > Guardar como > Power BI project files (*.pbip)`. Esto genera:
   ```
   MiInforme.pbip
   MiInforme.Report/          ← definición del reporte (PBIR: páginas y visuales)
   MiInforme.SemanticModel/   ← modelo semántico (TMDL)
   ```
2. Dejar el `.pbip` **abierto** en Power BI Desktop (el MCP se conecta a la
   instancia local viva; sin Desktop abierto, `ListLocalInstances` devuelve vacío).
3. (Recomendado) Preparar los datos: CSVs limpios, con encabezados, en una
   carpeta estable (las tablas del modelo referencian la ruta absoluta).

## Fase 1 — Conexión

```
connection_operations → ListLocalInstances
   → devuelve puerto y connectionString de cada Desktop abierto
connection_operations → Connect
   connectionString: "data source=localhost:<puerto>;Application Name=MCP-PBIModeling"
```

## Fase 2 — Modelo semántico

### 2.1 Crear tablas desde CSV

`table_operations → Create` con una expresión Power Query M por tabla:

```
let
    Source = Csv.Document(File.Contents("C:\\ruta\\absoluta\\tabla.csv"),
        [Delimiter=",", Columns=<N>, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    ChangedTypes = Table.TransformColumnTypes(PromotedHeaders, {
        {"id", Int64.Type}, {"nombre", type text}, {"monto", type number},
        {"fecha", type date}, {"activo", type logical}
    })
in
    ChangedTypes
```

Reglas duras (validadas empíricamente):
- `Columns=<N>` debe coincidir **exactamente** con el número de columnas del CSV.
- Rutas Windows absolutas con backslashes escapados (`\\`).
- `QuoteStyle.Csv` y `Encoding=65001` (UTF-8) siempre.
- En el array `columns` de la definición, el dataType para fechas es
  **`DateTime`** (no `date` — valores válidos: String, Int64, Double,
  DateTime, Decimal, Boolean); en la expresión M sí es `type date`.
- **Refrescar inmediatamente después de crear cada tabla** — está vacía hasta
  entonces:
  ```
  partition_operations → RefreshWithXMLA
     refreshDefinitions: [{ "tableName": "tabla", "refreshType": "Full" }]
  ```
- Verificar conteos con DAX:
  ```
  dax_query_operations → Execute
     query: EVALUATE ROW("filas", COUNTROWS(tabla))
  ```

### 2.2 Relaciones

`relationship_operations → Create` — la dimensión es el lado "uno":

```
fromTable: "fact_ventas",  fromColumn: "producto_id"   ← lado muchos
toTable:   "dim_producto", toColumn:   "producto_id"   ← lado uno
fromCardinality: "Many", toCardinality: "One"
crossFilteringBehavior: "Single"       ← "BothDirections" OBLIGATORIO en 1:1
```

- Crear **todas las tablas antes** que cualquier relación.
- Evitar rutas ambiguas: si dos tablas de hechos comparten dimensiones, no las
  relaciones también entre sí (el motor rechaza la relación con "ambiguous paths").
- Patrón para relaciones dobles (ej. partido→equipo local y visitante): en vez
  de relaciones inactivas + `USERELATIONSHIP`, despivotar en el ETL a grano
  entidad-evento (2 filas por partido) — una sola relación activa, cero DAX especial.

### 2.3 Medidas

1. Crear una tabla contenedora (sin array `columns` — falla si se incluye):
   ```
   table_operations → Create
      name: "_Measures", daxExpression: ROW("placeholder", BLANK())
   ```
   y refrescarla.
2. Crear las medidas en lote:
   ```
   measure_operations → Create
      definitions: [
        { "name": "Total Ventas", "tableName": "_Measures",
          "expression": "SUM(fact_ventas[monto])", "formatString": "#,##0.00" },
        { "name": "% Margen", "tableName": "_Measures",
          "expression": "DIVIDE([Ganancia], [Total Ventas])", "formatString": "0.0%" }
      ]
   ```
   Usar siempre `DIVIDE()` para ratios, nunca `/`.
3. Validar contra valores conocidos:
   ```
   dax_query_operations → Execute
      query: EVALUATE ROW("v", [Total Ventas])
   ```

### 2.4 Respaldo y guardado

- Snapshot del modelo: `database_operations → ExportToBimFile`.
- Los cambios del MCP viven en la memoria de Desktop: pedir al usuario
  **`Ctrl+S`** en Power BI Desktop para persistirlos al proyecto.

## Fase 3 — Dashboard (edición en vivo)

Los visuales NO se crean vía MCP (ninguna herramienta del MCP toca el layer de
reporte). Se escriben como archivos JSON (formato PBIR) y se recargan en vivo:

### El ciclo

```
1. Escribir/editar archivos en MiInforme.Report/definition/pages/
2. powerbi-report-author validate "MiInforme.Report"     ← ¿errores? → volver a 1
3. powerbi-desktop status                                 ← obtener el PID
4. powerbi-desktop reload --pid <pid>                     ← recarga SIN cerrar Desktop
5. powerbi-desktop screenshot-all --pid <pid> --output-dir shots/
6. Revisar las capturas → ¿algo mal? → volver a 1
```

### Estructura de archivos

```
MiInforme.Report/definition/pages/
├── pages.json                        ← pageOrder + activePageName (OBLIGATORIO)
└── <pageId 20-hex>/
    ├── page.json                     ← nombre, tamaño (1280×720), displayOption
    └── visuals/
        └── <visualId 20-hex>/
            └── visual.json           ← tipo, posición, query, filterConfig
```

Usar `scripts/build_visuals.py` de este repo como generador — produce el
formato exacto validado. Tipos probados: `card`, `clusteredBarChart`,
`clusteredColumnChart`, `lineChart`, `tableEx`, `slicer`, `textbox`.
Para otros tipos: `powerbi-report-author catalog describe <tipo>` da los
roles reales (nunca adivinar).

## Errores conocidos y sus fixes

Descubiertos comparando archivos escritos a mano contra los que genera el
propio Power BI Desktop (build 2.155, jun 2026):

| # | Síntoma | Causa | Fix |
|---|---|---|---|
| 1 | "Error al representar el informe. Cannot read properties of undefined (reading 'queryName')" al abrir | `visual.json` con formato/versión de schema que el motor no resuelve | Usar `$schema` **visualContainer/2.10.0** y `filterConfig` con un filtro por campo usado (tipo `Categorical` para columnas, `Advanced` para medidas). Ante la duda: crear UN visual a mano en Desktop, guardarlo y copiar su formato exacto |
| 2 | Tabla `tableEx` muestra encabezados pero **cero filas** | `"active": true` en alguna projection | No incluir `active` en ninguna projection — Desktop no lo escribe |
| 3 | Slicer arranca con una **selección espuria aleatoria** (distinta en cada carga) que filtra toda la página | `filterConfig` pre-declarado en el slicer | No incluir `filterConfig` en slicers — Desktop lo crea en runtime |

Otros errores frecuentes:

| Síntoma | Fix |
|---|---|
| "user declined to confirm" en toda escritura MCP | Falta `--skipconfirmation` en la config del servidor; reiniciar sesión del cliente |
| `ListLocalInstances` devuelve vacío | Power BI Desktop no está abierto o no tiene archivo cargado; abrirlo primero |
| Medidas devuelven blank | Tabla sin refrescar: `RefreshWithXMLA` tras cada Create |
| "Invalid DataType 'date'" al crear tabla | En `columns` usar `DateTime`; `type date` va solo en la expresión M |
| "Columns cannot be specified for calculated tables" | Quitar el array `columns` de tablas con `daxExpression` |
| Relación 1:1 rechazada | `crossFilteringBehavior` debe ser `BothDirections` |
| Desktop regenera páginas y borra visuales | Escribir siempre `pages.json` antes de la primera apertura del proyecto |
| El tema no se recarga con `reload` | Los temas se cachean por nombre: renombrar el archivo de tema o cerrar/reabrir Desktop |

## Solución de problemas

1. **El MCP no aparece en el cliente** → el cliente debe iniciarse desde la
   carpeta que contiene `.mcp.json`; reiniciar sesión/ventana tras cambios.
2. **`npx` no encontrado** → reinstalar Node.js con "Add to PATH", reiniciar la terminal.
3. **`reload` falla** → correr `validate` primero: Desktop rechaza PBIR inválido.
   Ejecutar reload y screenshot **en serie** (nunca en paralelo) por PID.
4. **Cambios de modelo no aparecen tras `reload`** → `reload` solo cubre PBIR
   (visuales); el modelo va por MCP directo a la instancia viva, no necesita reload.
5. **Todo falla de forma rara** → cerrar Desktop, verificar que no queden
   procesos `PBIDesktop.exe` colgados, reabrir el `.pbip` y reconectar el MCP
   (el puerto XMLA cambia en cada apertura).
