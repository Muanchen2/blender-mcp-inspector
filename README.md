# Blender MCP Inspector

A structured analysis tool for Blender scenes, powered by MCP and AI — focused on animation & rendering.

**Let AI understand your scene before you render.** PBR, NPR, stylized, photoreal — any .blend file, fully comprehended.

If you encounter any bugs or erros,please send me emile :1409634020@qq.com
或者Bilibili直接搜沐安宸，然后私聊我。

## Positioning: AI Reads Blender. Not AI Drives Blender.

| | blender-mcp (community) | Blender MCP Inspector |
|---|---|---|
| Core action | **Operate** Blender (build scenes, create objects, download assets) | **Understand** Blender (read node trees, analyze materials, audit rigs) |
| AI's role | Executor ("make me a sphere") | Analyst ("what's wrong with this material?") |
| Input | Natural language commands | Existing .blend files |
| Output | New 3D content | Structured scene insights |
| Node tree reading | ❌ | ✅ get_node_tree |
| Modifier analysis | ❌ | ✅ get_modifiers |
| Animation / rig | ❌ | ✅ get_animation_data / get_armature_data |
| Render settings | ❌ | ✅ get_render_settings |
| Blender addon | Custom addon.py | Official Blender Lab MCP Bridge |
| Asset downloads | ✅ Poly Haven / Sketchfab | ❌ |

## Use Cases

| Scenario | What it does |
|------|---------|
| Pre-render audit | Verify material node connections, check texture paths, validate render layers |
| Material debugging | Understand complex shader topology, locate broken node links |
| Character animation | Inspect bone hierarchy, IK/FK constraints, keyframe distribution |
| Scene handoff | Pick up someone else's .blend — let AI explain every node and setting |
| Production review | Batch-inspect all modifiers and animation data across a scene |

## Tools (8 total)

| Tool | Function |
|------|------|
| `execute_blender_code` | Execute arbitrary Python code in Blender (universal fallback) |
| `get_scene_info` | Scene overview: object list, poly counts, material summary |
| `get_object_info` | Object details: transform, hierarchy, camera/light parameters |
| `get_node_tree` | **Core** — Material / Compositor / Geometry Nodes / World shader topology |
| `get_modifiers` | Modifier stack + parameters + geometry node associations |
| `get_animation_data` | Action list / keyframes / drivers / NLA |
| `get_armature_data` | Bone hierarchy / constraints / IK setup |
| `get_render_settings` | Cycles/Eevee settings / render layers / passes |

## Quick Start

### Phase 1 — Blender setup (do this yourself, 2 minutes)

**Install the add-on:**
1. Blender → Edit → Preferences → Get Extensions
2. Search "MCP" (by Blender Lab) → Install → Enable

**Enable Online Access:**
1. Blender → Edit → Preferences → System
2. Check **Online Access** (required for the MCP Bridge to work)

### Phase 2 — Project setup (let AI handle this)

Paste this into Claude, OpenCode, or Cursor:

> Clone this project. Read README.md and requirements.txt. Install dependencies with pip, then configure MCP for my AI client. My Blender is at [your Blender path].

The AI will:
- Run `pip install -r requirements.txt`
- Write the correct MCP config for your client
- Tell you when to start the Bridge and trust the server

### Phase 3 — Start & verify

1. Blender → Edit → Preferences → Add-ons → "MCP" → **Start MCP Bridge Server**
2. Trust `blender` in your AI client's connector management
3. Restart the session and ask: *"Show me what's in my Blender scene"*

---

### Manual setup (if not using AI)

### Prerequisites

- Blender 5.1+
- Python 3.10+
- Blender MCP Bridge add-on installed ([download](https://www.blender.org/lab/mcp-server/))
- Blender System Preferences → System → **Online Access** enabled

### 1. Install

```bash
git clone https://github.com/your-username/blender-mcp-inspector.git
cd blender-mcp-inspector
pip install -r requirements.txt
```

### 2. Start the Blender Bridge

Open Blender → Edit → Preferences → Add-ons → "MCP" → **Start MCP Bridge Server**

Or via CLI: `blender --background --online-mode -c blender_mcp`

### 3. Configure AI client

**Claude Desktop** (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "blender": {
      "command": "python",
      "args": ["/path/to/blender_mcp_server.py"]
    }
  }
}
```

**WorkBuddy** (`~/.workbuddy/mcp.json`):
```json
{
  "mcpServers": {
    "blender": {
      "command": "python",
      "args": ["/path/to/blender_mcp_server.py"],
      "env": {
        "BLENDER_HOST": "localhost",
        "BLENDER_PORT": "9876"
      }
    }
  }
}
```

### 4. Trust & verify

Trust `blender` in your AI client's connector management, restart the session, and ask your AI:

> "Show me what's in my Blender scene"

If the AI returns a list of objects from your .blend file, it's working.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Connection closed" / -32000 | Ensure `pip install -r requirements.txt` completed successfully |
| "Connection refused" | Blender is not running, or the MCP Bridge server hasn't been started. Check Blender → Preferences → Add-ons → MCP |
| "Online access must be enabled" | Go to Blender → Edit → Preferences → System → enable Online Access |
| Blender not responding | Restart Blender and re-enable the MCP Bridge server |
| Tool returns timeout | Increase `BLENDER_PORT` env variable timeout, or simplify your request |

## Architecture

```
AI Client → MCP(stdio) → blender_mcp_server.py → TCP(:9876) → Blender MCP Bridge → bpy API
```

## Documentation

- [中文文档](README_zh.md)
- [日本語ドキュメント](README_ja.md)

## License

MIT
