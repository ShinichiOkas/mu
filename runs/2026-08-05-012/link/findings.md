# Ollama Structured Outputs (構造化出力) についての調査結果

## 参照した公式ドキュメント
- https://docs.ollama.com/capabilities/structured-outputs

## 要点
1. **JSON Schema による出力制御**: `format` パラメータに JSON Schema を指定することで、モデルのレスポンスを特定の構造（JSON）に強制させることができる。これにより、データの抽出や一貫した応答の維持が可能になる。
2. **柔軟な指定方法**: 
   - 単に `"format": "json"` と指定して JSON 形式で出力させる。
   - 詳細な JSON Schema オブジェクトを `format` フィールドに渡して、プロパティや型を厳密に定義する。
3. **ライブラリ連携による効率化**: Python では `Pydantic` の `model_json_schema()` を、JavaScript では `Zod` の `toJSONSchema()` を使用してスキーマを生成し、`format` に渡すことで、型の定義からバリデーションまでを効率的に実装できる。
