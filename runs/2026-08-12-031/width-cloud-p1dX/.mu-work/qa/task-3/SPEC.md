{
  "definitions": ["俳句: 日本語の三行詩ではなく1行で書く短詩。ここでは内容の質は問わない"],
  "criteria": [
    {"text": "poem_a.md に「- 」で始まる行が3行ある", "run": "Get-Content poem_a.md", "expect": "- "},
    {"text": "poem_b.md に「- 」で始まる行が3行ある", "run": "Get-Content poem_b.md", "expect": "- "}
  ],
  "spec": "2つの独立した成果物を作る。(1) poem_a.md — 春を詠んだ日本語の俳句を3句。1行に1句、行頭を「- 」にする。(2) poem_b.md — 秋を詠んだ日本語の俳句を3句。1行に1句、行頭を「- 」にする。poem_a.md と poem_b.md は互いに依存しない独立した作業である（どちらを先に作ってもよい）。"
}
