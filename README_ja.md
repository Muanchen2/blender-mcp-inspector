# Blender MCP Inspector

アニメーションとレンダリングのための Blender MCP 構造化分析ツール。

**レンダリング前に、AI にあなたのシーンを理解させる。** PBR、NPR、スタイライズド、フォトリアル——どんな .blend ファイルも完全に把握できます。

## ポジショニング：AI は Blender を「読む」。AI は Blender を「操作しない」。

| | blender-mcp (コミュニティ版) | Blender MCP Inspector |
|---|---|---|
| 主な動作 | Blender を**操作**（シーン構築、オブジェクト作成、アセットDL） | Blender を**理解**（ノードツリー読取、マテリアル分析、リグ監査） |
| AI の役割 | 実行者（「球体を作って」） | 分析者（「このマテリアルの問題点は？」） |
| 入力 | 自然言語の指示 | 既存の .blend ファイル |
| 出力 | 新しい 3D コンテンツ | 構造化されたシーンの洞察 |
| ノードツリー読取 | ❌ | ✅ get_node_tree |
| モディファイア分析 | ❌ | ✅ get_modifiers |
| アニメーション/リグ | ❌ | ✅ get_animation_data / get_armature_data |
| レンダー設定 | ❌ | ✅ get_render_settings |
| Blender アドオン | 独自 addon.py | Blender Lab 公式 MCP Bridge |
| アセットDL | ✅ Poly Haven / Sketchfab | ❌ |

## ユースケース

| シーン | できること |
|------|---------|
| レンダー前チェック | マテリアルノード接続の検証、テクスチャパスの確認、レンダーレイヤー設定の監査 |
| マテリアルデバッグ | 複雑なシェーダートポロジーの理解、切断されたノードリンクの発見 |
| キャラクターアニメーション | ボーン階層、IK/FK コンストレイント、キーフレーム分布の確認 |
| シーン引継ぎ | 他人の .blend を受け取ったとき、AI が全ノードと設定を説明 |
| プロダクションレビュー | シーン内の全モディファイアとアニメーションデータの一括チェック |

## ツール一覧（8 個）

| ツール | 機能 |
|------|------|
| `execute_blender_code` | Blender 内で任意の Python コードを実行（万能フォールバック） |
| `get_scene_info` | シーン概要：オブジェクト一覧、ポリゴン数、マテリアルサマリー |
| `get_object_info` | オブジェクト詳細：位置/回転/スケール/親子関係/カメラ/ライト |
| `get_node_tree` | **コア** — マテリアル / コンポジター / ジオメトリノード / ワールドシェーダーのトポロジー |
| `get_modifiers` | モディファイアスタック + パラメータ + ジオメトリノード関連 |
| `get_animation_data` | アクション一覧 / キーフレーム / ドライバー / NLA |
| `get_armature_data` | ボーン階層 / コンストレイント / IK 設定 |
| `get_render_settings` | Cycles/Eevee 設定 / レンダーレイヤー / パス |

## クイックスタート

### フェーズ 1 — Blender 側の設定（自分で、2 分）

**アドオンをインストール：**
1. Blender → 編集 → プリファレンス → 拡張機能を取得
2. "MCP" を検索（Blender Lab 作）→ インストール → 有効化

**オンラインアクセスを有効化：**
1. Blender → 編集 → プリファレンス → システム
2. **オンラインアクセス** にチェック（MCP Bridge に必須）

### フェーズ 2 — プロジェクト設定（AI に任せる）

Claude、OpenCode、Cursor に以下を貼り付け：

> このプロジェクトをクローンし、README.md と requirements.txt を読んで、pip で依存関係をインストールし、MCP 設定を行って。Blender のパスは [Blenderのパス]。

AI が自動で：
- `pip install -r requirements.txt` を実行
- AI クライアント用の MCP 設定ファイルを作成
- Bridge 起動とサーバー信頼のタイミングを案内

### フェーズ 3 — 起動と確認

1. Blender → 編集 → プリファレンス → アドオン → "MCP" → **MCP Bridge を起動**
2. AI クライアントのコネクター管理で `blender` を信頼
3. セッションを再起動し、AI に *「Blender シーンに何がある？」* と聞く

---

### 手動セットアップ（AI を使わない場合）

### 前提条件

- Blender 5.1+
- Python 3.10+
- Blender MCP Bridge アドオンをインストール（[ダウンロード](https://www.blender.org/lab/mcp-server/)）
- Blender システム設定 → システム → **オンラインアクセス** を有効化

### 1. プロジェクトをインストール

```bash
git clone https://github.com/your-username/blender-mcp-inspector.git
cd blender-mcp-inspector
pip install -r requirements.txt
```

### 2. Blender Bridge を起動

Blender → 編集 → プリファレンス → アドオン → "MCP" → **MCP Bridge を起動**

または CLI：`blender --background --online-mode -c blender_mcp`

Blender を開く → 編集 → プリファレンス → アドオン → "MCP" を検索 → 「Start MCP Bridge Server」をクリック

または CLI：`blender --background --online-mode -c blender_mcp`

### 3. AI クライアントの設定

**Claude Desktop** (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "blender": {
      "command": "python",
      "args": ["パス/blender_mcp_server.py"]
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
      "args": ["パス/blender_mcp_server.py"],
      "env": {
        "BLENDER_HOST": "localhost",
        "BLENDER_PORT": "9876"
      }
    }
  }
}
```

### 4. 信頼と確認

AI クライアントのコネクター管理で `blender` を信頼し、セッションを再起動。AI にこう聞いてみて：

> 「Blender シーンに何がある？」

AI が .blend ファイルのオブジェクト一覧を返せば成功です。

## トラブルシューティング

| 問題 | 解決方法 |
|------|---------|
| "Connection closed" / -32000 | `pip install -r requirements.txt` が正常に完了したか確認 |
| "Connection refused" | Blender が起動していない、または MCP Bridge が開始されていません。Blender → プリファレンス → アドオン → MCP を確認 |
| "Online access must be enabled" | Blender → 編集 → プリファレンス → システム → オンラインアクセスを有効にする |
| Blender が応答しない | Blender を再起動し、MCP Bridge を再度有効にする |
| ツールがタイムアウトする | リクエストを簡略化するか、タイムアウト時間を延長 |

## アーキテクチャ

```
AI Client → MCP(stdio) → blender_mcp_server.py → TCP(:9876) → Blender MCP Bridge → bpy API
```

## ドキュメント

- [English](README.md)
- [中文文档](README_zh.md)

## ライセンス

MIT
