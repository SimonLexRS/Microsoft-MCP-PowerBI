# Microsoft MCP PowerBI — Kit de integración para agentes de IA

[![Visitas](https://hits.seeyoufarm.com/api/count/incr/badge.svg?url=https%3A%2F%2Fgithub.com%2FSimonLexRS%2FMicrosoft-MCP-PowerBI&title=visitas&edge_flat=false)](https://github.com/SimonLexRS/Microsoft-MCP-PowerBI)
[![Descargas npm — MCP](https://img.shields.io/npm/dm/%40microsoft%2Fpowerbi-modeling-mcp?label=descargas%20powerbi-modeling-mcp)](https://www.npmjs.com/package/@microsoft/powerbi-modeling-mcp)
[![Descargas npm — Authoring CLI](https://img.shields.io/npm/dm/%40microsoft%2Fpowerbi-report-authoring-cli?label=descargas%20report-authoring-cli)](https://www.npmjs.com/package/@microsoft/powerbi-report-authoring-cli)
[![Descargas npm — Desktop Bridge](https://img.shields.io/npm/dm/%40microsoft%2Fpowerbi-desktop-bridge-cli?label=descargas%20desktop-bridge-cli)](https://www.npmjs.com/package/@microsoft/powerbi-desktop-bridge-cli)
[![Stars](https://img.shields.io/github/stars/SimonLexRS/Microsoft-MCP-PowerBI?style=flat)](https://github.com/SimonLexRS/Microsoft-MCP-PowerBI/stargazers)
[![Licencia](https://img.shields.io/github/license/SimonLexRS/Microsoft-MCP-PowerBI)](LICENSE)

Kit completo para que un agente de IA (Claude, Copilot, Cursor u otro cliente
MCP) construya **modelos semánticos y dashboards de Power BI de punta a punta**
contra una instancia local de Power BI Desktop — incluyendo **edición de
visuales en vivo, sin cerrar el archivo**.

Este kit integra y documenta tres herramientas oficiales de Microsoft
(el mérito de los paquetes es de Microsoft; este repo aporta la configuración,
el flujo de trabajo validado, los errores conocidos y sus fixes, y los
manuales para replicarlo en cualquier equipo):

| Componente | Paquete | Rol |
|---|---|---|
| **Servidor MCP** | [`@microsoft/powerbi-modeling-mcp`](https://www.npmjs.com/package/@microsoft/powerbi-modeling-mcp) | Modelo semántico: tablas, relaciones, medidas DAX, consultas — vía XMLA contra Power BI Desktop |
| **CLI de autoría** | [`@microsoft/powerbi-report-authoring-cli`](https://www.npmjs.com/package/@microsoft/powerbi-report-authoring-cli) | Validación de archivos PBIR y catálogo de visuales |
| **CLI puente Desktop** | [`@microsoft/powerbi-desktop-bridge-cli`](https://www.npmjs.com/package/@microsoft/powerbi-desktop-bridge-cli) | Abrir, **recargar en vivo** y capturar screenshots del reporte abierto |

## Capacidades

### Modelo semántico (vía MCP — 21 grupos de herramientas)

| Grupo | Herramientas | Qué permite |
|---|---|---|
| Conexión | `connection_operations` | Detectar instancias locales de Desktop y conectarse |
| Tablas y datos | `table_operations`, `partition_operations` | Crear tablas desde CSV (Power Query M), refrescar datos |
| Relaciones | `relationship_operations` | Crear/activar relaciones 1:N y 1:1 con dirección de filtro |
| Medidas y DAX | `measure_operations`, `dax_query_operations`, `function_operations` | Crear medidas, validar y ejecutar DAX en vivo |
| Columnas | `column_operations`, `user_hierarchy_operations` | Columnas calculadas, renombrado, jerarquías |
| Modelo | `model_operations`, `database_operations` | Refresh global, exportar TMDL/BIM, desplegar a Fabric |
| Avanzadas | `calculation_group_operations`, `calendar_operations`, `perspective_operations`, `security_role_operations`, `culture_operations`, `object_translation_operations`, `named_expression_operations`, `query_group_operations`, `trace_operations`, `transaction_operations` | Grupos de cálculo, calendarios, RLS, traducciones, trazas |

### Dashboard (vía CLIs — edición en vivo)

| Comando | Qué hace |
|---|---|
| `powerbi-report-author validate <dir .Report>` | Valida schema, estructura, IDs, roles y enums de los archivos PBIR **antes** de tocar Desktop |
| `powerbi-report-author catalog describe <tipo>` | Roles y propiedades reales de cada tipo de visual (sin adivinar) |
| `powerbi-desktop open <archivo.pbip>` | Abre el proyecto en Power BI Desktop |
| `powerbi-desktop status` | Instancias abiertas, PID, páginas del reporte |
| `powerbi-desktop reload --pid <pid>` | **Recarga los visuales en el Desktop abierto, sin cerrarlo** |
| `powerbi-desktop screenshot-all --pid <pid> --output-dir <dir>` | Captura todas las páginas para verificación automática |

## Arquitectura

```
┌─────────────────────┐        MCP (stdio)         ┌──────────────────────────┐
│   Agente de IA      │ ─────────────────────────► │ powerbi-modeling-mcp     │
│ (Claude / Copilot / │                            │  └─► XMLA :puerto local  │
│  Cursor / otro)     │        CLI (shell)         ├──────────────────────────┤
│                     │ ─────────────────────────► │ powerbi-desktop-bridge   │──┐
│                     │ ─────────────────────────► │ powerbi-report-authoring │  │
└─────────────────────┘                            └──────────────────────────┘  │
        │  escribe archivos PBIR (visual.json, pages.json)                       │
        ▼                                                                        ▼
┌──────────────────────────────┐   reload en vivo   ┌──────────────────────────┐
│ Proyecto .pbip en disco      │ ◄───────────────── │  Power BI Desktop        │
│  ├─ *.Report/ (visuales)     │                    │  (archivo ABIERTO)       │
│  └─ *.SemanticModel/ (TMDL)  │                    └──────────────────────────┘
└──────────────────────────────┘
```

## Inicio rápido

```bash
# 1. Requisitos: Windows + Power BI Desktop + Node.js 20+
npm install -g @microsoft/powerbi-report-authoring-cli @microsoft/powerbi-desktop-bridge-cli

# 2. Clonar este kit y abrir el agente desde la carpeta
git clone https://github.com/SimonLexRS/Microsoft-MCP-PowerBI.git
cd Microsoft-MCP-PowerBI
claude   # el .mcp.json activa el servidor powerbi-modeling automáticamente

# 3. Abrir Power BI Desktop con un proyecto .pbip y pedirle al agente:
#    "Lista las instancias locales de Power BI Desktop y conéctate"
```

Guía de instalación completa por cliente (Claude Code, Claude Desktop,
VS Code Copilot, Cursor, cliente genérico): **[INSTALL.md](INSTALL.md)**
Manual de uso completo con el flujo validado y errores conocidos: **[MANUAL.md](MANUAL.md)**
Prompts de ejemplo listos para copiar: **[PROMPTS.md](PROMPTS.md)**

## Qué aporta este kit sobre los paquetes crudos

1. **`.mcp.json` y configs listos** para cada cliente de IA (el flag
   `--skipconfirmation` es obligatorio y no es obvio — sin él toda escritura
   falla).
2. **El flujo de dashboard en vivo** (validate → reload → screenshot) que
   permite iterar visuales sin cerrar Power BI Desktop.
3. **Tres errores críticos documentados con fix** que rompen el render de
   visuales escritos por agentes (ver [MANUAL.md](MANUAL.md#errores-conocidos-y-sus-fixes)) —
   descubiertos comparando contra archivos generados por el propio Desktop.
4. **`scripts/build_visuals.py`**: generador de páginas/visuales PBIR
   (KPI cards, barras, columnas, líneas, tablas, slicers) con el formato
   exacto que Power BI Desktop 2.155+ acepta.
5. **`CLAUDE.md`** con las instrucciones de agente: al abrir este repo en
   Claude Code, el agente ya sabe el flujo completo sin explicárselo.

## Requisitos

- Windows 10/11 (Power BI Desktop es solo Windows)
- [Power BI Desktop](https://aka.ms/pbidesktop) (gratuito, versión jun-2026+)
- [Node.js 20+](https://nodejs.org) (el MCP corre vía `npx`)
- Python 3.10+ (opcional, solo para `scripts/build_visuals.py`)
- Sin credenciales cloud: todo corre local contra Power BI Desktop

---

**Autor:** Simon Rodriguez — [LinkedIn](https://www.linkedin.com/in/srodriguezxs/)

Los paquetes npm integrados son propiedad de Microsoft. Este kit se
distribuye bajo licencia [MIT](LICENSE).
