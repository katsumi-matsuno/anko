# ポモドーロタイマー 実装機能一覧

## バックエンド（Python / Flask）

| # | 機能 | ファイル | 内容 |
|---|------|---------|------|
| 1 | Application Factory | `app.py` | `create_app(config=None)` でFlaskアプリ生成 |
| 2 | メインページ配信 | `app.py` | `GET /` で `index.html` をレンダリング |
| 3 | ポモドーロ完了API | `app.py` | `POST /api/complete` で完了を記録し統計を返却 |
| 4 | 進捗取得API | `app.py` | `GET /api/stats` で今日の完了数・集中時間を返却 |
| 5 | データ保存層 | `store.py` | `MemoryStore` クラス（`add_record`, `get_today_records`, `clear`） |
| 6 | ビジネスロジック層 | `pomodoro_service.py` | `PomodoroService` クラス（`complete_pomodoro`, `get_today_stats`） |

## フロントエンド（HTML / CSS / JavaScript）

| # | 機能 | ファイル | 内容 |
|---|------|---------|------|
| 7 | HTMLテンプレート | `templates/index.html` | カード型レイアウト、SVG円形プログレス、ボタン、進捗表示 |
| 8 | スタイリング | `static/css/style.css` | 紫系テーマ、円形プログレスリング、レスポンシブ対応 |
| 9 | タイマー純粋ロジック | `static/js/timerCore.js` | `TimerCore` クラス（`tick`, `isFinished`, `reset`）DOM非依存 |
| 10 | DOM操作・API連携 | `static/js/timer.js` | `setInterval`カウントダウン、SVG更新、API呼び出し |

## UI動作

| # | 機能 | 詳細 |
|---|------|------|
| 11 | カウントダウン表示 | 残り時間を `MM:SS` 形式で表示（例: `25:00`） |
| 12 | 円形プログレスリング | SVG `stroke-dashoffset` で残り時間を視覚表示 |
| 13 | 開始ボタン | タイマー開始、カウントダウン動作開始 |
| 14 | リセットボタン | タイマーを初期状態に戻す |
| 15 | ステータス表示切替 | 「作業中」「休憩中」の表示切り替え |
| 16 | 作業→休憩の自動切替 | 作業(25分)完了後に短い休憩(5分)へ自動遷移 |
| 17 | ロングブレイク | 4回目の作業完了後に長い休憩(15分)へ遷移 |
| 18 | 完了時のAPI呼び出し | 作業完了時に `POST /api/complete` を送信 |
| 19 | 進捗表示 | 完了回数と合計集中時間（例: `4完了 / 1時間40分`）をリアルタイム更新 |

## テスト

| # | 機能 | ファイル | 内容 |
|---|------|---------|------|
| 20 | Store層テスト | `tests/test_store.py` | MemoryStoreの単体テスト |
| 21 | Service層テスト | `tests/test_service.py` | PomodoroServiceの単体テスト（Store注入） |
| 22 | APIテスト | `tests/test_app.py` | Flask test_clientによるエンドポイントテスト |
| 23 | timerCoreテスト | （jest） | タイマー純粋ロジックのテスト |

## 推奨実装順序

1. **基盤**: Store層 → Service層 → Application Factory + ルーティング（#1〜6）
2. **UI骨組み**: HTMLテンプレート + CSS + タイマーロジック（#7〜10）
3. **動作**: カウントダウン、ボタン操作、プログレスリング（#11〜14）
4. **進捗連携**: API呼び出し + 進捗表示（#18〜19）
5. **状態遷移**: 作業→休憩の自動切替 + ロングブレイク（#15〜17）
6. **テスト**: 各層のテスト整備（#20〜23）
