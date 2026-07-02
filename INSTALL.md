# Instalación e integración por cliente de IA

## Requisitos previos (todos los clientes)

1. **Windows 10/11** — Power BI Desktop es exclusivo de Windows.
2. **Power BI Desktop** — [Microsoft Store](https://aka.ms/pbidesktop) (recomendado,
   se auto-actualiza) o descarga directa. Versión mínima probada: 2.155 (jun 2026).
3. **Node.js 20 o superior** — [nodejs.org](https://nodejs.org), instalar LTS con
   "Add to PATH". Verificar: `node --version` y `npx --version`.
4. **Habilitar proyectos .pbip en Power BI Desktop** (si no aparece la opción):
   `Archivo > Opciones y configuración > Opciones > Funciones de vista previa` →
   activar "Power BI Project (.pbip) save option" → reiniciar Desktop.
5. **CLIs de autoría** (para el flujo de dashboard en vivo):
   ```bash
   npm install -g @microsoft/powerbi-report-authoring-cli @microsoft/powerbi-desktop-bridge-cli
   ```
   Verificar: `powerbi-report-author --version` y `powerbi-desktop --version`.

> El servidor MCP (`@microsoft/powerbi-modeling-mcp`) **no se instala a mano**:
> el cliente de IA lo lanza vía `npx` con la configuración de abajo.

---

## Claude Code (CLI / VS Code)

Este repo ya incluye el [`.mcp.json`](.mcp.json) en la raíz:

```json
{
  "mcpServers": {
    "powerbi-modeling": {
      "command": "npx",
      "args": ["-y", "@microsoft/powerbi-modeling-mcp@latest", "--start", "--skipconfirmation"]
    }
  }
}
```

**Pasos:**
1. Clonar el repo y abrir una terminal **en la carpeta del repo** (Claude Code
   solo carga `.mcp.json` del directorio donde se inicia).
2. Ejecutar `claude`. Al arrancar pedirá aprobar el servidor `powerbi-modeling` — aceptar.
3. Verificar: preguntarle al agente *"Lista las instancias locales de Power BI Desktop"*.
   Si Power BI Desktop está abierto con un archivo cargado, debe devolver la instancia.

> **`--skipconfirmation` es obligatorio.** Sin ese flag, todas las operaciones de
> escritura fallan con "user declined to confirm".

> **Cambios en `.mcp.json` requieren reiniciar la sesión** de Claude Code
> (los servidores MCP de proyecto se cargan al inicio, no hay hot-reload).

**Skill (recomendado):** instala el skill del kit para que Claude conozca el
flujo completo sin explicárselo en cada sesión:

```bash
mkdir -p ~/.claude/skills/powerbi-mcp
cp skills/powerbi-mcp/SKILL.md ~/.claude/skills/powerbi-mcp/
```

Se activa automáticamente con pedidos como "carga estos datos en Power BI" o
explícitamente con `/powerbi-mcp`.

## Claude Desktop (app de escritorio)

Editar el archivo de configuración (`%APPDATA%\Claude\claude_desktop_config.json`
en Windows) y agregar el bloque de [`config/claude_desktop_config.json`](config/claude_desktop_config.json):

```json
{
  "mcpServers": {
    "powerbi-modeling": {
      "command": "npx",
      "args": ["-y", "@microsoft/powerbi-modeling-mcp@latest", "--start", "--skipconfirmation"]
    }
  }
}
```

Reiniciar Claude Desktop. Las herramientas aparecen con el prefijo `powerbi-modeling`.

> Claude Desktop no ejecuta comandos de shell, así que el flujo de dashboard en
> vivo (CLIs `validate`/`reload`/`screenshot`) no está disponible ahí — solo el
> modelado semántico vía MCP. Para el flujo completo usar Claude Code.

## VS Code — GitHub Copilot (agent mode)

Copilot lee el mismo formato `.mcp.json` en la raíz del workspace. Abrir la
carpeta del repo en VS Code, luego `Ctrl+Shift+P` → **MCP: List Servers** para
verificar que `powerbi-modeling` está corriendo (buscar "Skip Confirmation:
Enabled" en el output). Si se editó la config: **Developer: Reload Window**.

## Cursor

`Cursor Settings > MCP > Add new global MCP server`, o crear `.cursor/mcp.json`
en el proyecto con el mismo contenido del `.mcp.json` de este repo.

## Cualquier otro cliente MCP (genérico, stdio)

El servidor es un proceso stdio estándar. Configuración equivalente:

- **Comando:** `npx`
- **Argumentos:** `-y @microsoft/powerbi-modeling-mcp@latest --start --skipconfirmation`
- **Transporte:** stdio
- **Variables de entorno:** ninguna (no requiere credenciales — opera contra
  la instancia local de Power BI Desktop vía XMLA)

---

## Checklist de verificación post-instalación

- [ ] `node --version` ≥ 20
- [ ] `powerbi-report-author --version` y `powerbi-desktop --version` responden
- [ ] Power BI Desktop abre y tiene la opción "Guardar como > Power BI project files (*.pbip)"
- [ ] El cliente de IA lista las herramientas `powerbi-modeling` (21 grupos)
- [ ] Con Desktop abierto (archivo cargado), `ListLocalInstances` devuelve la instancia
- [ ] `powerbi-desktop status` muestra la instancia con su PID y páginas

Si algo falla, ver la sección de solución de problemas en [MANUAL.md](MANUAL.md#solución-de-problemas).
