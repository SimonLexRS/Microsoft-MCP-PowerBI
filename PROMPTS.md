# Prompts de ejemplo

## Prompt de implementación (copiar en Claude o ChatGPT)

Pega este prompt en tu asistente de IA (Claude Code, Claude, ChatGPT u otro
agente con acceso a terminal) para que instale y configure el kit completo en
tu equipo desde cero:

```
Quiero implementar el kit Microsoft-MCP-PowerBI en este equipo Windows para
construir modelos y dashboards de Power BI con IA. Sigue estos pasos y
verifica cada uno antes de continuar:

1. Verifica los requisitos: Windows, Power BI Desktop instalado (si falta,
   indícame el link https://aka.ms/pbidesktop y espera), y Node.js 20+
   (`node --version`).
2. Clona el kit: git clone https://github.com/SimonLexRS/Microsoft-MCP-PowerBI.git
   y entra a la carpeta.
3. Instala los CLIs de autoría:
   npm install -g @microsoft/powerbi-report-authoring-cli @microsoft/powerbi-desktop-bridge-cli
   y verifica que `powerbi-report-author --version` y `powerbi-desktop --version` respondan.
4. Configura el servidor MCP según mi cliente de IA (el repo trae .mcp.json
   para Claude Code y config/claude_desktop_config.json para Claude Desktop;
   para otros clientes usa: comando npx, args
   ["-y","@microsoft/powerbi-modeling-mcp@latest","--start","--skipconfirmation"],
   transporte stdio). Dime si necesito reiniciar la sesión del cliente.
5. Si mi cliente soporta skills, instala el skill del repo copiando la carpeta
   skills/powerbi-mcp a mi directorio de skills (~/.claude/skills/ en Claude Code).
6. Pídeme abrir Power BI Desktop con un archivo nuevo, guardarlo como proyecto
   .pbip (si no aparece la opción, actívala en Opciones > Funciones de vista
   previa) y dejarlo abierto.
7. Prueba de humo: lista las instancias locales de Power BI Desktop con el MCP
   y conéctate; después corre `powerbi-desktop status` y muéstrame el PID.
8. Cuando todo funcione, dame un resumen de qué quedó instalado y los prompts
   de ejemplo del archivo PROMPTS.md del repo para empezar a trabajar.

Lee INSTALL.md y MANUAL.md del repo ante cualquier duda o error — el MANUAL
tiene la tabla de errores conocidos con sus fixes.
```

> En asistentes sin acceso a terminal (ChatGPT web, Claude web), el asistente
> te dictará los comandos para que los ejecutes tú y le pegues la salida.

---

Los siguientes prompts asumen el kit ya configurado y Power BI Desktop
abierto con un `.pbip`.

## Conexión y diagnóstico

```
Lista las instancias locales de Power BI Desktop y conéctate a la que tiene mi informe abierto.
```

```
Muéstrame todas las tablas, relaciones y medidas del modelo actual.
```

```
Ejecuta un DAX que me diga cuántas filas tiene cada tabla del modelo.
```

## Análisis y carga de datos (EDA + ETL + modelo)

```
Analiza los CSV de la carpeta ./data: perfila nulos, duplicados e integridad
referencial entre las claves, y proponme un modelo estrella (dim/fact).
No cargues nada todavía — primero muéstrame el diseño.
```

```
Carga los CSV de ./data/processed como tablas del modelo usando el MCP:
crea cada tabla con Power Query M (UTF-8, QuoteStyle.Csv), refréscala
inmediatamente, y verifica los conteos de filas con DAX contra los CSV.
```

```
Crea las relaciones del modelo estrella: cada dimensión al hecho por su id,
cardinalidad uno-a-muchos, filtro en una sola dirección.
```

## Medidas DAX

```
Crea una tabla _Measures y estas medidas: Total Ventas, Ticket Promedio,
% Margen (usa DIVIDE, nunca /), Ventas Año Anterior y Crecimiento %.
Valida cada una ejecutándola con DAX antes de darla por buena.
```

```
La medida [% Margen] devuelve blank. Diagnostica: ¿la tabla está refrescada?
¿las relaciones filtran en la dirección correcta?
```

## Dashboard (edición en vivo, sin cerrar Desktop)

```
Crea una página "Resumen Ejecutivo": fila de 4 KPIs arriba (tarjetas),
un gráfico de barras de ventas por categoría, una tabla de detalle y un
slicer de región. Valida los archivos con powerbi-report-author, recarga
el reporte abierto con powerbi-desktop reload y verifica con un screenshot.
```

```
Agrega una página de análisis temporal: línea de ventas por fecha y columnas
por trimestre. Después de recargar, muéstrame la captura para revisarla.
```

```
En la página 2, ordena las barras de mayor a menor y cambia la tabla por una
matriz por región/mes. Recarga en vivo y compárame el antes y el después.
```

## Verificación y entrega

```
Toma screenshots de todas las páginas y revisa: ¿algún visual en blanco,
algún slicer con selección que no debería tener, algún total que no cuadre
con los datos fuente?
```

```
Exporta el modelo a un archivo .bim como respaldo y dime qué falta para que
guarde el proyecto final.
```

## Consejos de prompting

- **Pide verificación explícita**: "valida con DAX", "muéstrame el screenshot" —
  el agente tiene las herramientas para auto-verificarse; úsalas.
- **Una fase por vez**: modelo primero, dashboard después. El reload en vivo
  solo cubre visuales; el modelo va directo por el MCP.
- **Ante un visual roto**: pide al agente crear ese visual a mano una vez en
  Desktop, guardarlo, y copiar el formato exacto del archivo generado (es la
  técnica con la que se descubrieron los fixes del [MANUAL](MANUAL.md#errores-conocidos-y-sus-fixes)).
- **Recuerda guardar**: los cambios de modelo viven en la memoria de Desktop
  hasta que presiones `Ctrl+S`.
