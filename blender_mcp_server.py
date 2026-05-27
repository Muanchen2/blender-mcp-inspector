# blender_mcp_server.py
# 轻量级 MCP Server：桥接 AI 客户端与 Blender MCP Bridge
#
# 环境变量：
#   BLENDER_HOST  — Blender Bridge 地址，默认 localhost
#   BLENDER_PORT  — Blender Bridge 端口，默认 9876

import asyncio
import json
import os
import socket
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# ── 配置 ──────────────────────────────────────────────────
BLENDER_HOST = os.environ.get("BLENDER_HOST", "localhost")
BLENDER_PORT = int(os.environ.get("BLENDER_PORT", "9876"))
CONNECT_TIMEOUT = 5.0
RECV_TIMEOUT = 30.0


# ── TCP 通信 ──────────────────────────────────────────────

def _send_to_blender(code: str, strict_json: bool = True) -> dict[str, Any]:
    request = json.dumps({"type": "execute", "code": code, "strict_json": strict_json}) + "\0"
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(CONNECT_TIMEOUT)
    try:
        sock.connect((BLENDER_HOST, BLENDER_PORT))
        sock.settimeout(RECV_TIMEOUT)
        sock.sendall(request.encode("utf-8"))
        buf = bytearray()
        while b"\0" not in buf:
            chunk = sock.recv(4096)
            if not chunk:
                break
            buf.extend(chunk)

        if b"\0" not in buf:
            return {"status": "error", "message": "Blender 未返回完整响应"}
        return json.loads(bytes(buf[:buf.index(b"\0")]))
    except (socket.timeout, TimeoutError):
        return {"status": "error", "message": f"连接 Blender 超时（{BLENDER_HOST}:{BLENDER_PORT}），Blender 的 MCP Bridge 是否已启动？"}
    except ConnectionRefusedError:
        return {"status": "error", "message": f"无法连接 Blender（{BLENDER_HOST}:{BLENDER_PORT}），请先启动 Blender 并在偏好设置中开启 MCP Bridge"}
    except OSError as e:
        return {"status": "error", "message": f"网络错误: {e}"}
    finally:
        sock.close()


def _format_result(result: dict[str, Any]) -> str:
    if result.get("status") == "error":
        msg = result.get("message", "未知错误")
        for key in ("stdout", "stderr"):
            if result.get(key):
                msg += f"\n\n--- {key} ---\n{result[key]}"
        return f"[Blender 错误] {msg}"
    data = result.get("result", {})
    out = json.dumps(data, ensure_ascii=False, indent=2)
    for key in ("stdout", "stderr"):
        if result.get(key):
            out += f"\n\n--- {key} ---\n{result[key]}"
    return out


# ── 工具执行函数 ──────────────────────────────────────────

def _run_scene_info():
    code = """
import bpy
result = {
    "scene_name": bpy.context.scene.name,
    "object_count": len(bpy.data.objects),
    "objects": [],
    "render_engine": bpy.context.scene.render.engine,
    "current_frame": bpy.context.scene.frame_current,
    "frame_start": bpy.context.scene.frame_start,
    "frame_end": bpy.context.scene.frame_end,
}
for obj in bpy.data.objects:
    info = {"name": obj.name, "type": obj.type, "location": [round(v, 3) for v in obj.location], "visible": not obj.hide_viewport}
    if obj.type == "MESH":
        info["vertices"] = len(obj.data.vertices) if obj.data else 0
        info["polygons"] = len(obj.data.polygons) if obj.data else 0
        info["materials"] = [m.name for m in obj.data.materials] if obj.data else []
    result["objects"].append(info)
result
"""
    return _send_to_blender(code)


def _run_object_info(object_name: str):
    code = f"""
import bpy
obj = bpy.data.objects.get("{object_name.replace('"', '\\"')}")
if obj is None:
    result = {{"error": "找不到物体: {object_name.replace('"', '\\"')}"}}
else:
    result = {{"name": obj.name, "type": obj.type, "location": [round(v, 3) for v in obj.location],
        "rotation_euler": [round(v, 3) for v in obj.rotation_euler], "scale": [round(v, 3) for v in obj.scale],
        "visible": not obj.hide_viewport, "visible_in_render": not obj.hide_render,
        "parent": obj.parent.name if obj.parent else None, "children": [c.name for c in obj.children],
        "modifiers": [{{"name": m.name, "type": m.type}} for m in obj.modifiers]}}
    if obj.type == "MESH" and obj.data:
        result["vertices"] = len(obj.data.vertices)
        result["edges"] = len(obj.data.edges)
        result["polygons"] = len(obj.data.polygons)
        result["materials"] = [m.name for m in obj.data.materials]
    if obj.type == "CAMERA" and obj.data:
        result["lens"] = obj.data.lens
        result["sensor_width"] = obj.data.sensor_width
    if obj.type == "LIGHT" and obj.data:
        result["light_type"] = obj.data.type
        result["energy"] = obj.data.energy
        result["color"] = list(obj.data.color)
result
"""
    return _send_to_blender(code)


def _run_node_tree(source_type: str, source_name: str):
    code = f"""
import bpy, json, math
def _ser(v):
    if v is None: return None
    if isinstance(v, (int, str, bool)): return v
    if isinstance(v, float):
        if math.isnan(v) or math.isinf(v): return str(v)
        return round(v, 6)
    if hasattr(v, 'to_list'): return list(v)
    if hasattr(v, '__iter__') and hasattr(v, '__len__') and not isinstance(v, str):
        try: return [round(x, 6) if isinstance(x, float) else x for x in v]
        except: pass
    try:
        s = str(v)
        return s[:200] + '...' if len(s) > 200 else s
    except: return None
def _get_nt(nt):
    if nt is None: return {{"error": "节点树为空"}}
    nodes = []
    for node in nt.nodes:
        nd = {{"name": node.name, "label": node.label if node.label else node.name, "type": node.type,
            "location": [round(node.location.x, 1), round(node.location.y, 1)], "inputs": [], "outputs": []}}
        for sock in node.inputs:
            sd = {{"name": sock.name, "socket_type": sock.type, "enabled": sock.enabled}}
            if sock.is_linked:
                sd["linked_from"] = {{"node": sock.links[0].from_node.name, "socket": sock.links[0].from_socket.name}}
            elif hasattr(sock, 'default_value'):
                sd["default_value"] = _ser(sock.default_value)
            nd["inputs"].append(sd)
        for sock in node.outputs:
            sd = {{"name": sock.name, "socket_type": sock.type, "enabled": sock.enabled}}
            sd["linked_to"] = [{{"node": l.to_node.name, "socket": l.to_socket.name}} for l in sock.links]
            nd["outputs"].append(sd)
        nodes.append(nd)
    links = []
    for link in nt.links:
        links.append({{"from_node": link.from_node.name, "from_socket": link.from_socket.name, "to_node": link.to_node.name, "to_socket": link.to_socket.name}})
    return {{"type": nt.bl_idname, "node_count": len(nt.nodes), "link_count": len(nt.links), "nodes": nodes, "links": links}}
st = "{source_type.replace('"', '\\"')}"
sn = "{source_name.replace('"', '\\"')}"
if st == "material":
    mat = bpy.data.materials.get(sn)
    if mat is None: result = {{"error": f"找不到材质: {{sn}}"}}
    else:
        result = _get_nt(mat.node_tree)
        result["material_name"] = mat.name
elif st == "compositor":
    scene = bpy.context.scene
    if not scene.use_nodes: result = {{"error": "合成器节点未启用"}}
    else:
        result = _get_nt(scene.node_tree)
        result["scene_name"] = scene.name
elif st == "geometry":
    ng = bpy.data.node_groups.get(sn)
    if ng is None: result = {{"error": f"找不到几何节点组: {{sn}}"}}
    else:
        result = _get_nt(ng)
        result["node_group_name"] = ng.name
elif st == "world":
    world = bpy.context.scene.world
    if world is None or not world.use_nodes: result = {{"error": "世界着色器节点未启用"}}
    else:
        result = _get_nt(world.node_tree)
        result["world_name"] = world.name
else:
    result = {{"error": f"未知 source_type: {{st}}, 可选: material, compositor, geometry, world"}}
result
"""
    return _send_to_blender(code)


def _run_modifiers(object_name: str):
    code = f"""
import bpy, json, math
def _ser(v):
    if v is None: return None
    if isinstance(v, (int, str, bool)): return v
    if isinstance(v, float):
        if math.isnan(v) or math.isinf(v): return str(v)
        return round(v, 6)
    if hasattr(v, 'to_list'): return list(v)
    if hasattr(v, '__iter__') and hasattr(v, '__len__') and not isinstance(v, str):
        try: return [round(x, 6) if isinstance(x, float) else x for x in v]
        except: pass
    try:
        s = str(v)
        return s[:200] + '...' if len(s) > 200 else s
    except: return None
obj = bpy.data.objects.get("{object_name.replace('"', '\\"')}")
if obj is None:
    result = {{"error": "找不到物体: {object_name.replace('"', '\\"')}"}}
else:
    mods = []
    for m in obj.modifiers:
        md = {{"name": m.name, "type": m.type, "show_viewport": m.show_viewport, "show_render": m.show_render, "stack_index": list(obj.modifiers).index(m)}}
        params = {{}}
        for attr in dir(m):
            if attr.startswith('_') or attr.startswith('bl_') or attr.startswith('rna_'): continue
            if attr in ('type', 'name'): continue
            try:
                val = getattr(m, attr)
                if callable(val): continue
                params[attr] = _ser(val)
            except: pass
        md["parameters"] = params
        if m.type == 'NODES' and m.node_group:
            md["node_group"] = m.node_group.name
        mods.append(md)
    result = {{"object": obj.name, "modifier_count": len(obj.modifiers), "modifiers": mods}}
result
"""
    return _send_to_blender(code)


def _run_animation_data(object_name: str):
    code = f"""
import bpy, json
on = "{object_name.replace('"', '\\"')}"
if on:
    obj = bpy.data.objects.get(on)
    if obj is None:
        result = {{"error": f"找不到物体: {{on}}"}}
    else:
        ad = obj.animation_data
        if ad is None: result = {{"object": obj.name, "has_animation": False}}
        else:
            info = {{"object": obj.name, "has_animation": True}}
            if ad.action:
                act = ad.action
                info["action"] = {{"name": act.name, "frame_range": [round(act.frame_range[0]), round(act.frame_range[1])], "fcurve_count": len(act.fcurves), "fcurves": []}}
                for fc in act.fcurves:
                    kfs = [{{"frame": round(kf.co[0], 1), "value": round(kf.co[1], 4), "interpolation": kf.interpolation}} for kf in fc.keyframe_points]
                    info["action"]["fcurves"].append({{"data_path": fc.data_path, "array_index": fc.array_index, "keyframe_count": len(fc.keyframe_points), "keyframes": kfs[:20]}})
            if ad.nla_tracks:
                info["nla_tracks"] = [{{"name": t.name, "strip_count": len(t.strips)}} for t in ad.nla_tracks]
            if ad.drivers:
                info["driver_count"] = len(ad.drivers)
                info["drivers"] = [{{"data_path": d.data_path, "array_index": d.array_index}} for d in ad.drivers[:50]]
            result = info
else:
    actions = []
    for act in bpy.data.actions:
        actions.append({{"name": act.name, "frame_range": [round(act.frame_range[0]), round(act.frame_range[1])], "fcurve_count": len(act.fcurves)}})
    result = {{"action_count": len(bpy.data.actions), "scene_frame": bpy.context.scene.frame_current, "scene_frame_range": [bpy.context.scene.frame_start, bpy.context.scene.frame_end], "actions": actions}}
result
"""
    return _send_to_blender(code)


def _run_armature_data(armature_name: str):
    code = f"""
import bpy, json
obj = bpy.data.objects.get("{armature_name.replace('"', '\\"')}")
if obj is None or obj.type != 'ARMATURE':
    result = {{"error": "找不到骨架或不是 Armature 类型: {armature_name.replace('"', '\\"')}"}}
else:
    arm = obj.data
    bones_info = []
    for bone in arm.bones:
        bd = {{"name": bone.name, "parent": bone.parent.name if bone.parent else None, "children": [c.name for c in bone.children],
            "head": [round(v, 4) for v in bone.head_local], "tail": [round(v, 4) for v in bone.tail_local],
            "roll": round(bone.roll, 4), "length": round(bone.length, 4), "use_deform": bone.use_deform,
            "use_connect": bone.use_connect, "use_inherit_rotation": bone.use_inherit_rotation}}
        bd["constraints"] = [{{"name": c.name, "type": c.type, "influence": round(c.influence, 3), "mute": c.mute}}
            for c in obj.pose.bones[bone.name].constraints] if bone.name in obj.pose.bones else []
        bd["has_ik"] = any(c.type == 'IK' for c in obj.pose.bones[bone.name].constraints) if bone.name in obj.pose.bones else False
        bones_info.append(bd)
    root_bones = [b.name for b in arm.bones if b.parent is None]
    result = {{"armature_name": obj.name, "bone_count": len(arm.bones), "root_bones": root_bones, "bones": bones_info}}
result
"""
    return _send_to_blender(code)


def _run_render_settings():
    code = """
import bpy, json
scene = bpy.context.scene
render = scene.render
view_layers = []
for vl in scene.view_layers:
    vld = {"name": vl.name, "use": vl.use, "samples": vl.samples, "passes": {}}
    for attr in dir(vl):
        if attr.startswith('use_pass_'):
            try: vld["passes"][attr.replace('use_pass_', '')] = getattr(vl, attr)
            except: pass
    view_layers.append(vld)
result = {"engine": render.engine, "resolution": {"x": render.resolution_x, "y": render.resolution_y, "percentage": render.resolution_percentage},
    "frame": {"current": scene.frame_current, "start": scene.frame_start, "end": scene.frame_end, "step": scene.frame_step},
    "output": {"filepath": render.filepath, "file_format": render.image_settings.file_format, "color_mode": render.image_settings.color_mode, "color_depth": render.image_settings.color_depth},
    "film": {"transparent": render.film_transparent, "exposure": render.exposure}, "view_layers": view_layers}
if render.engine == 'CYCLES':
    c = scene.cycles
    result["cycles"] = {"samples": c.samples, "preview_samples": c.preview_samples, "use_denoising": c.use_denoising, "denoiser": c.denoiser, "max_bounces": c.max_bounces,
        "diffuse_bounces": c.diffuse_bounces, "glossy_bounces": c.glossy_bounces, "transmission_bounces": c.transmission_bounces,
        "use_adaptive_sampling": c.use_adaptive_sampling, "adaptive_threshold": c.adaptive_threshold, "device": c.device if hasattr(c, 'device') else "CPU"}
if render.engine in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
    e = scene.eevee
    result["eevee"] = {"taa_samples": e.taa_samples, "use_gtao": e.use_gtao, "use_bloom": e.use_bloom, "use_ssr": e.use_ssr, "use_motion_blur": e.use_motion_blur}
result
"""
    return _send_to_blender(code)


# ── MCP Server ────────────────────────────────────────────

server = Server("blender-mcp")

_TOOLS = [
    Tool(
        name="execute_blender_code",
        description="在 Blender 中执行任意 Python 代码。必须将结果存入 result 变量（dict 类型）。不要调用 sys.exit() 或 bpy.ops.wm.quit_blender()。",
        inputSchema={
            "type": "object",
            "properties": {"code": {"type": "string", "description": "要执行的 Python 代码"}},
            "required": ["code"],
        },
    ),
    Tool(
        name="get_scene_info",
        description="获取当前 Blender 场景的基本信息，包括物体列表、材质列表、面数统计、渲染设置概览。",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="get_object_info",
        description="获取指定物体的详细信息：位置、旋转、缩放、父子关系、修改器列表、顶点/面数（网格）、相机参数、灯光参数。",
        inputSchema={
            "type": "object",
            "properties": {"object_name": {"type": "string", "description": "物体名称"}},
            "required": ["object_name"],
        },
    ),
    Tool(
        name="get_node_tree",
        description="读取 Blender 节点树的完整拓扑结构（节点列表+端口+连接关系）。支持材质着色器(source_type='material')、合成器(source_type='compositor')、几何节点(source_type='geometry')、世界着色器(source_type='world')。",
        inputSchema={
            "type": "object",
            "properties": {
                "source_type": {"type": "string", "enum": ["material", "compositor", "geometry", "world"], "description": "节点树类型"},
                "source_name": {"type": "string", "description": "材质名或几何节点组名（compositor/world 时忽略）"},
            },
            "required": ["source_type"],
        },
    ),
    Tool(
        name="get_modifiers",
        description="获取指定物体的所有修改器及其详细参数，包括堆叠顺序、启用状态、几何节点关联。",
        inputSchema={
            "type": "object",
            "properties": {"object_name": {"type": "string", "description": "物体名称"}},
            "required": ["object_name"],
        },
    ),
    Tool(
        name="get_animation_data",
        description="获取动画数据。指定 object_name 返回该物体的动作+关键帧+Driver；不指定则返回场景中所有动作的概览。",
        inputSchema={
            "type": "object",
            "properties": {"object_name": {"type": "string", "description": "物体名称（可选，为空则返回全局动作列表）"}},
        },
    ),
    Tool(
        name="get_armature_data",
        description="获取骨架（Armature）的完整结构：骨骼层级、约束、IK设置。适用于角色动画。",
        inputSchema={
            "type": "object",
            "properties": {"armature_name": {"type": "string", "description": "骨架物体名称"}},
            "required": ["armature_name"],
        },
    ),
    Tool(
        name="get_render_settings",
        description="获取当前场景的完整渲染设置：引擎(Cycles/Eevee)、采样数、输出、渲染层、渲染通道(Passes)。",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
]


@server.list_tools()
async def list_tools() -> list[Tool]:
    return _TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    raw: dict[str, Any]
    if name == "execute_blender_code":
        raw = await asyncio.to_thread(_send_to_blender, arguments["code"], True)
    elif name == "get_scene_info":
        raw = await asyncio.to_thread(_run_scene_info)
    elif name == "get_object_info":
        raw = await asyncio.to_thread(_run_object_info, arguments["object_name"])
    elif name == "get_node_tree":
        raw = await asyncio.to_thread(_run_node_tree, arguments.get("source_type", "material"), arguments.get("source_name", ""))
    elif name == "get_modifiers":
        raw = await asyncio.to_thread(_run_modifiers, arguments["object_name"])
    elif name == "get_animation_data":
        raw = await asyncio.to_thread(_run_animation_data, arguments.get("object_name", ""))
    elif name == "get_armature_data":
        raw = await asyncio.to_thread(_run_armature_data, arguments["armature_name"])
    elif name == "get_render_settings":
        raw = await asyncio.to_thread(_run_render_settings)
    else:
        raw = {"status": "error", "message": f"未知工具: {name}"}

    text = _format_result(raw)
    return [TextContent(type="text", text=text)]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
