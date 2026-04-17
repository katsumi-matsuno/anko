# ポモドーロタイマー Webアプリケーション アーキテクチャ

## 概要

Flask + HTML/CSS/JavaScript によるポモドーロタイマー Web アプリケーション。
ユニットテストのしやすさを重視し、各層を分離した設計とする。

## UI 仕様

| 要素 | 内容 |
|------|------|
| ステータス表示 | 「作業中」「休憩中」の切り替え表示 |
| 円形プログレスリング | 残り時間を視覚的に表示（SVG `stroke-dashoffset` で実装） |
| 操作ボタン | 「開始」「リセット」 |
| 今日の進捗 | 完了回数、合計集中時間 |

### タイマーの状態遷移

```
IDLE → WORKING(25分) → SHORT_BREAK(5分) → WORKING → ...
                            ↓ (4回目)
                       LONG_BREAK(15分)
```

## ディレクトリ構成

```
1.pomodoro/
├── app.py                  # create_app() + ルーティング
├── pomodoro_service.py     # ビジネスロジック
├── store.py                # データ保存層
├── static/
│   ├── css/
│   │   └── style.css       # スタイル（円形プログレス、ボタン等）
│   └── js/
│       ├── timerCore.js    # タイマー純粋ロジック（DOM 非依存）
│       └── timer.js        # DOM 操作・API 呼び出し
├── templates/
│   └── index.html          # メインページテンプレート
└── tests/
    ├── test_app.py         # API エンドポイントのテスト
    ├── test_service.py     # ビジネスロジックのテスト
    └── test_store.py       # データ保存層のテスト
```

## レイヤー設計

### 1. バックエンド

#### ルーティング（`app.py`）

Application Factory パターンを採用し、テストごとにアプリインスタンスを生成可能にする。

- `create_app(config=None)` — アプリ生成関数
- `GET /` — `index.html` をレンダリング
- `POST /api/complete` — ポモドーロ完了を記録
- `GET /api/stats` — 今日の進捗（完了数・集中時間）を返却

#### ビジネスロジック（`pomodoro_service.py`）

Flask に依存しない純粋な Python クラス。HTTP なしで単体テスト可能。

- `PomodoroService.__init__(store)` — Store を注入
- `PomodoroService.complete_pomodoro(duration_minutes)` — 完了記録 + 統計返却
- `PomodoroService.get_today_stats()` — 今日の完了数・合計集中時間を返却

#### データ保存層（`store.py`）

データアクセスを抽象化し、テスト間の状態分離と将来の DB 移行を容易にする。
初期実装はインメモリ（リスト）で保持し、必要に応じて SQLite 等に移行する。

- `MemoryStore.add_record(duration_minutes)` — 完了記録を追加
- `MemoryStore.get_today_records()` — 今日の記録一覧を返却
- `MemoryStore.clear()` — 全記録をクリア

### 2. フロントエンド

タイマーのカウントダウンは **クライアント側で完結** させる。

#### タイマー純粋ロジック（`timerCore.js`）

DOM に依存しない純粋ロジック。Node.js 環境（jest 等）でテスト可能。

- `TimerCore(durationSec)` — 初期化
- `TimerCore.tick()` — 1秒進める、残り時間を返す
- `TimerCore.isFinished()` — 完了判定
- `TimerCore.reset()` — リセット

#### DOM 操作・API 呼び出し（`timer.js`）

`timerCore.js` を利用し、UI 更新と API 呼び出しを担当。

- `setInterval` で1秒ごとにカウントダウン
- 残り時間に応じて SVG 円弧（プログレスリング）を更新
- 完了時に `POST /api/complete` を呼び出し、進捗表示を更新

### 3. UI（HTML + CSS）

- 円形プログレスは SVG の `stroke-dashoffset` で実装
- レスポンシブ対応は `max-width` + `margin: auto` のカード型レイアウト
- カラーテーマは紫系（`#6C63FF` 付近）をベース

## 状態管理

```
フロントエンド（timer.js）         バックエンド（app.py）
┌─────────────────────────┐    ┌──────────────────┐
│ タイマー残り時間          │    │ 完了回数          │
│ 現在のモード(作業/休憩)    │─完了→│ 合計集中時間       │
│ 開始/停止状態            │    │                  │
└─────────────────────────┘    └──────────────────┘
```

- タイマーのリアルタイム状態はフロントエンドのみで管理
- 永続化が必要な進捗データのみバックエンドで管理

## テスト方針

| テスト対象 | テスト手法 | ポイント |
|-----------|-----------|---------|
| `store.py` | pytest | `MemoryStore` を直接インスタンス化してテスト |
| `pomodoro_service.py` | pytest | `MemoryStore` を注入し、HTTP なしでテスト |
| `app.py` | pytest + Flask `test_client` | `create_app({"TESTING": True})` でインスタンス生成 |
| `timerCore.js` | jest | DOM なしで純粋ロジックをテスト |

## 実装の優先順位

1. Flask + 静的ファイル配信の骨組み（Application Factory）
2. Store 層 + Service 層の実装
3. タイマー UI（円形プログレス + カウントダウン）
4. 開始 / リセットボタンの動作
5. 進捗記録 API と表示
6. 作業 → 休憩の自動切り替え
7. テストの整備
