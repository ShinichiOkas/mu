ITEM 1: PASS — poem_a.md に「- 」で始まる行が3行あることを確認した。Get-Content poem_a.md | Where-Object { $_ -match '^\s*- ' } | Measure-Object の Count が 3 で、内容に春のテーマ（春の風、鶯等）を含む。
ITEM 2: PASS — poem_b.md に「- 」で始まる行が3行あることを確認した。Get-Content poem_b.md | Where-Object { $_ -match '^\s*- ' } | Measure-Object の Count が 3 で、内容に秋のテーマ（コスモス、赤い葉など）を含む。
