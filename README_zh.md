# Blender MCP Inspector

一个面向动画与渲染的 Blender MCP 结构化分析工具。

**让 AI 读懂你的场景，在渲染之前。** PBR、NPR、风格化、写实——任何 .blend 工程都能被完整理解。

## 定位：AI 阅读 Blender，而非 AI 操作 Blender

| | blender-mcp (社区版) | Blender MCP Inspector |
|---|---|---|
| 核心动作 | **操控** Blender（建场景、创建物体、下资产） | **理解** Blender（读节点树、分析材质、审计骨架） |
| AI 的角色 | 执行者（"帮我做一个球"） | 分析师（"这个材质有什么问题"） |
| 输入 | 自然语言指令 | 已有的 .blend 文件 |
| 输出 | 新的 3D 内容 | 结构化的场景洞察 |
| 节点树读取 | ❌ | ✅ get_node_tree |
| 修改器分析 | ❌ | ✅ get_modifiers |
| 动画/骨架 | ❌ | ✅ get_animation_data / get_armature_data |
| 渲染设置 | ❌ | ✅ get_render_settings |
| Blender 插件 | 自定义 addon.py | Blender Lab 官方 MCP Bridge |
| 资产下载 | ✅ Poly Haven / Sketchfab | ❌ |

## 典型使用场景

| 场景 | 能做什么 |
|------|---------|
| 渲染前检查 | 审计材质节点连接、验证贴图路径、检查渲染层配置 |
| 材质调试 | 读懂复杂着色器拓扑、定位断开的节点链接 |
| 角色动画 | 查看骨架层级、IK/FK 约束、关键帧分布 |
| 场景交接 | 接手别人的 .blend，AI 帮你快速理解全部节点和设置 |
| 工程审查 | 批量检查场景中所有修改器、动画数据的正确性 |

## 工具列表（8 个）

| 工具 | 功能 |
|------|------|
| `execute_blender_code` | 在 Blender 中执行任意 Python 代码（万能兜底） |
| `get_scene_info` | 场景全貌：物体列表、面数统计、材质概览 |
| `get_object_info` | 物体详情：位置/旋转/缩放/父子关系/相机/灯光参数 |
| `get_node_tree` | **核心** — 材质 / 合成器 / 几何节点 / World 着色器节点树拓扑 |
| `get_modifiers` | 修改器堆栈 + 参数 + 几何节点关联 |
| `get_animation_data` | 动作列表 / 关键帧 / Driver / NLA |
| `get_armature_data` | 骨架层级 / 骨骼约束 / IK 配置 |
| `get_render_settings` | Cycles/Eevee 设置 / 渲染层 / Pass |

## 快速开始

### 第一步 — Blender 端设置（自己来，2 分钟）

**安装官方插件：**
1. Blender → 编辑 → 偏好设置 → 获取扩展
2. 搜索 "MCP"（作者 Blender Lab）→ 安装 → 启用

**开启在线访问：**
1. Blender → 编辑 → 偏好设置 → 系统
2. 勾选 **在线访问（Online Access）**（MCP Bridge 必须）

### 第二步 — 项目安装（交给 AI）

把下面这段话粘贴到 Claude、OpenCode 或 Cursor：

> 克隆这个项目，阅读 README.md 和 requirements.txt，帮我用 pip 安装依赖，然后配置好 MCP。我的 Blender 在 [你的 Blender 路径]。

AI 会自动：
- 执行 `pip install -r requirements.txt`
- 为你的 AI 客户端写入正确的 MCP 配置
- 告诉你何时启动 Bridge、何时信任服务器

### 第三步 — 启动并验证

1. Blender → 编辑 → 偏好设置 → 插件 → "MCP" → **启动 MCP Bridge**
2. 在 AI 客户端的连接器管理中信任 `blender`
3. 重启会话，对 AI 说：*"看看我的 Blender 场景里有什么"*

---

### 手动安装（不使用 AI 的话）

### 前提

- Blender 5.1+
- Python 3.10+
- Blender MCP Bridge 插件已安装（[下载](https://www.blender.org/lab/mcp-server/)）
- Blender 系统偏好设置 → 系统 → **在线访问** 已开启

### 1. 安装项目

```bash
git clone https://github.com/your-username/blender-mcp-inspector.git
cd blender-mcp-inspector
pip install -r requirements.txt
```

### 2. 启动 Blender Bridge

Blender → 编辑 → 偏好设置 → 插件 → "MCP" → **启动 MCP Bridge**

或命令行：`blender --background --online-mode -c blender_mcp`

打开 Blender → 编辑 → 偏好设置 → 插件 → 搜索 "MCP" → 点击「Start MCP Bridge Server」

或命令行：`blender --background --online-mode -c blender_mcp`

### 3. 配置 AI 客户端

**Claude Desktop** (`claude_desktop_config.json`)：
```json
{
  "mcpServers": {
    "blender": {
      "command": "python",
      "args": ["路径/blender_mcp_server.py"]
    }
  }
}
```

**WorkBuddy** (`~/.workbuddy/mcp.json`)：
```json
{
  "mcpServers": {
    "blender": {
      "command": "python",
      "args": ["路径/blender_mcp_server.py"],
      "env": {
        "BLENDER_HOST": "localhost",
        "BLENDER_PORT": "9876"
      }
    }
  }
}
```

### 4. 信任并验证

在 AI 客户端的连接器管理中信任 `blender` MCP Server，重启会话，对 AI 说：

> "看看我的 Blender 场景里有什么"

如果 AI 返回了 .blend 文件中的物体列表，说明成功了。

## 故障排查

| 问题 | 解决方法 |
|------|---------|
| "Connection closed" / -32000 | 确认 `pip install -r requirements.txt` 成功执行 |
| "Connection refused" | Blender 未运行或 MCP Bridge 未启动。检查 Blender → 偏好设置 → 插件 → MCP |
| "Online access must be enabled" | Blender → 编辑 → 偏好设置 → 系统 → 开启在线访问 |
| Blender 无响应 | 重启 Blender，重新开启 MCP Bridge |
| 工具调用超时 | 简化请求，或增大超时时间 |

## 架构

```
AI Client → MCP(stdio) → blender_mcp_server.py → TCP(:9876) → Blender MCP Bridge → bpy API
```

## 文档

- [English](README.md)
- [日本語](README_ja.md)

## 许可证

MIT
