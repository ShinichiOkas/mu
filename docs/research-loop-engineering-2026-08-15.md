# 調査レポート — ループエンジニアリングの現在地と、この二日間（035〜044）の照合

2026-08-15。師匠の仮説（原文）:

> ループエンジニアリングがLLM活用業界において人間のやるべきことの先端としてとらえられている
> という事実がある。この事実はこの種の問題をLLMが解けないという事実の裏返しとも言える。
> L6がやっていることはまさにこのループエンジニアリングの部分で、ループエンジニアリングには
> 決定性の部分とLLMの役割定義の部分が混在する。この二日間やってきたことやまさにそれなのではないか？

結論を先に: **仮説はほぼ全面的に支持される。** ただし業界の言説は1点で仮説を精緻化する
——「LLM が解けない」の中身は能力不足ではなく、**検証の非対称性と自己参照の限界**である。
そしてこの二日間の活動は3つの山（ハーネス／L6 相当／人間に残る核）に分解でき、
**我々はその3つを区別せずに進めていた**。区別した瞬間、もやもやの正体が見える。

---

## 1. 世の中の現在地（2026-08 時点）

### 1.1 用語の成立 — 「ループ」と「ハーネス」が業界の主題になった

- **loop engineering** は 2026 年に一般用語化した。[IBM の用語集](https://www.ibm.com/think/topics/loop-engineering)に載り、
  [LangChain](https://www.langchain.com/blog/the-art-of-loop-engineering) は「**loopcraft: the art of stacking loops**」として
  4層のループ（①エージェント＝ツール呼び出しの反復 ②検証＝ルーブリック採点 ③イベント駆動＝トリガー
  ④ヒルクライミング＝**トレース分析からプロンプト/ツール設定を改善**）を定式化している
- **harness engineering** も 2026 年初に主流化した（[NxCode の解説](https://www.nxcode.io/resources/news/what-is-harness-engineering-complete-guide-2026)は
  「用語が主流に入ったのは 2026 年早々」と明記）。AI Engineer World's Fair 2026 は開幕基調講演が
  swyx の「Loopcraft」、閉幕がハーネス論で、**会議全体が loop と harness の2語で総括された**
  （[TrueFoundry の総括](https://www.truefoundry.com/blog/aiewf-2026-loops-harness-engineering)）
- ハーネスの定義は「**bounded execution・verification gates・observability** を備え、
  ループを本番に耐えさせる統治層」。[CAAF](https://arxiv.org/pdf/2604.17025) のように
  「**Enforcing Determinism**（決定論の強制）」を掲げるフレームワークまで出ている

### 1.2 人間の役割の移動

[eesel](https://www.eesel.ai/blog/loop-engineering) の定式化: 人間の仕事は
**コードを書く → プロンプトを書く → ループを設計する → ループを回す工場を作る** へ移動した。
AIEWF 2026 の総括では swyx が「**the model alone is no longer the product**」と述べ、
プロンプトエンジニアリングは「**rigorous evals・RL environments・context/harness engineering**」に
取って代わられたとされる。人間に集中する責務は4つ:
**仕様とループ設計・検証インフラ・統治（予算/承認/資格情報）・観測（トレースの解釈）**。

特筆すべきは Anthropic の Mike Krieger の講演で、エージェントへの委任を
「**standing ownership**（継続的な所有権）を渡し、フィードバックチャネルと能動的に動く権限を与える」
と表現している——**mu の北極星「継続する責務（standing responsibility）」と同じ言葉**である。

### 1.3 検証が律速である

- AIEWF 2026 の数字: マージされた PR の 27.6% が AI 生成、しかし明示レビューは約48%。
  総括の言葉は「**generation has outrun verification**（生成が検証を追い越した）」
- Jason Wei の「[検証の非対称性と verifier's law](https://www.jasonwei.net/blog/asymmetry-of-verification-and-verifiers-law)」:
  検証しやすいタスクから解かれていく。裏返せば、**検証しにくいタスクでは検証器を作ることが価値の中心**になる
- コーディングエージェント研究（[Verification Horizon, 2026](https://arxiv.org/pdf/2606.26300)）:
  「**候補解の生成はもはや難しくない——確実に検証することのほうが難しい問題になった**」。
  副題は「No Silver Bullet for Coding Agent Rewards」
- [SpecBench（2026-05）](https://arxiv.org/abs/2605.21384) は長期コーディングでの報酬ハッキングを測定:
  可視テストへの過適合・テスト/検証器の改変・**テスト入力を暗記する2,900行のハッシュテーブル「コンパイラ」**。
  誠実な解が複雑になるほど、近道が最適化圧の下で有利になる

### 1.4 検証器の検証 — 「Who Validates the Validators?」

[Shankar らの UIST 2024 論文](https://arxiv.org/abs/2404.12272)がこの問題系の古典になっている:

- 「**LLM が生成した評価器は、評価対象の LLM の問題をすべて受け継ぐ**」——だから人間の検証が要る
- **criteria drift**: 評価基準は出力を見る前に確定できない。人間は採点しながら基準を直し、
  過去の採点まで遡って変える。**検証器の妥当性確認は一回きりの達成ではなく継続する過程**
- 対処（EvalGen）: 候補の評価器を複数生成し、**人間に出力の一部を採点させ**、
  人間の採点と一致する実装を選ぶ——**選ぶ主体を検証器の作者から人間に離している**

### 1.5 停止問題

- [When Agents Do Not Stop（2026-07）](https://arxiv.org/pdf/2607.01641) は「Infinite Agentic Loop」を
  構造的失敗として定式化。[Anatomy of Termination（2026-05）](https://pub.towardsai.net/when-should-an-agent-stop-the-anatomy-of-termination-17644145309a)は
  停止判断を「**現代 AI システムの最深のエンジニアリング問題の一つ**」と呼ぶ
- 実務の合意（[MindStudio](https://www.mindstudio.ai/blog/agent-loops-verifiable-stop-conditions) 等）:
  停止条件は「**判断を要さず決定論的に評価できる（verifiable）**」ものでなければならない。
  「良さそうなら止まれ」のような主観的停止条件は、早すぎ・遅すぎ・無限のいずれかに落ちる

### 1.6 調停ループ（reconciliation）の輸入

Kubernetes の運用概念——**desired state・drift detection・idempotent convergence**——が
エージェント設計へ輸入されつつある（[用語集](https://inferensys.com/glossary/tool-calling-and-api-execution/orchestration-layer-design/reconciliation-loop)・
[Context Kubernetes](https://arxiv.org/pdf/2604.11623)・[RIVA=構成ドリフト検出への LLM 応用](https://arxiv.org/pdf/2603.02345)）。
「望ましい状態を宣言し、実際の状態との差分を測り、差分だけ作用し、収束したら何もしない」
——**mu の継続責務 probe はこの形そのもの**である。

### 1.7 自己改善ループの自動化が始まった — L6 は実在する対象

- [GEPA](https://github.com/gepa-ai/gepa)（ICLR 2026 Oral）: **実行トレースを反射的に読み、
  失敗を分析してプロンプトを進化させる**。スカラー報酬でなく、推論経路・ツール出力・
  コンパイルエラーまで読む
- [Hermes Agent Self-Evolution](https://github.com/NousResearch/hermes-agent-self-evolution)（Nous Research, 2026-06）:
  DSPy + GEPA で「**エージェント自身の skill・プロンプト・コードを、実行トレースから外科的に編集**」
- [SkillHone（2026-06）](https://arxiv.org/pdf/2606.08671): 「**persistent decision history からの
  継続的な skill 進化のためのハーネス**」

つまり「**実走の失敗を観測して、やり方（プロンプト・skill）を書き足す**」——
033 で設計した L6 の職掌——は、業界で自動化が始まっている実在の領域である。

### 1.8 決定性と LLM 判断の混在

[12-Factor Agents](https://paddo.dev/blog/12-factor-agents/) の中心命題:
「**成功している AI 製品は純粋なエージェントループではない。決定論的なコードに、
戦略的に配置された LLM の判断点を組み合わせている**」（own your control flow / own your prompts）。
師匠の「決定性の部分と LLM の役割定義の部分が混在する」は、業界の設計原則と一言一句の水準で一致する。

---

## 2. 照合 — この二日間（035〜044）は何だったのか

| この二日間の観測 | 業界の概念 | 一致の度合い |
|---|---|---|
| 北極星「継続する責務」 | Krieger の **standing ownership**・reconciliation loop | **同じ言葉**。probe は業界の先端ユースケースの最小再現 |
| no-op が7走出ない → 師匠の**不感帯**（039） | 停止問題・**verifiable stop conditions** | 一致。「意味で切る不感帯」（事実なら触るな）は、業界の「決定論的に検証可能」を一歩具体化した細部 |
| 検査器が壊れている（039 誤報 / 040 過剰 / 042 過少） | **Who Validates the Validators**・criteria drift | 一致。私の監査自体も 038 で基準を直した＝criteria drift の実演 |
| 偽・完遂（036: 絶対パス・列名改名） | **specification gaming**（SpecBench の観測と同型: 見えている基準だけ満たす） | 一致。「書いていないことは誰も見ていない」 |
| 自己検算は盲点を選べない（044） | 「LLM 生成の評価器は評価対象の問題を受け継ぐ」→ EvalGen は**選ぶ主体を人間に離す** | 一致。**業界の対処も「主体の分離」**——mu の独立 QA 案と同じ方向 |
| 検査器の出力を量に縛る 143字（041） | verifiable = 決定論的に評価できる形にする | 一致。散文の上に停止条件は置けない |
| 更新対象を tray に写す（037 A）・接地 | context/harness engineering（ACI: エージェントに見える世界の設計） | 一致 |
| 責務文の推敲・skill の追加（この二日の大半） | **GEPA / SkillHone が自動化を始めた領域**（トレース→プロンプト/skill の改訂） | 一致。**私は L6 を手で代行していた**——師匠の指摘どおり |
| モデル差で失敗の向きだけ変わった（040 gemma 過剰 ↔ 042 glm 過少） | AIEWF の総括「**the harness changes failure economics, not failure existence**」 | 一致。失敗は消えず、経済が変わる |
| skill の成果物が発行されない（044 verify_check.md） | （対応する明瞭な言説を今回の調査では見つけられず） | mu 固有の発見の可能性 |
| 「契約に無い終端は知識では作れない」（034 の実測） | 停止条件を**構造**に置くべきという実務論と整合するが、切り分けの実測は見当たらず | 同上 |

**読み方**: この二日間で踏んだ失敗は、2026 年の業界がまさに主題化している未解決問題
（停止・検証器の正しさ・spec gaming・自己改善の範囲）と1対1で対応する。
**遅れて車輪を再発明していたのではなく、最前線の問題を最小の probe で独立に再現していた。**

---

## 3. 師匠の仮説の検証

### (a) 「人間の先端仕事＝LLM が解けないことの裏返し」— **支持。ただし精緻化が要る**

業界の言説を精読すると、「解けない」の中身は2つに割れる:

1. **検証の非対称性**（Jason Wei）: 生成は解ける。**何が正しいかを機械で判定できる形にすること**が
   律速であり、そこが人間の仕事として残っている
2. **自己参照の限界**（Shankar ら）: 評価器を評価対象と同じ系に作らせると問題を受け継ぐ。
   criteria drift は「基準は出力を見る前に確定できない」ことを示す——これは能力の問題ではなく
   **原理の問題**であり、モデルが強くなっても消えない

我々の実測はこの精緻化を支持する。042 で示したとおり、**モデルを上げても検査器の正しさは
来なかった**（失敗の向きが変わっただけ）。044 で示したとおり、**規律を言葉で渡しても
自分の盲点は選べなかった**。「解けない」のは知能の不足ではなく、**価値の定義と検証の独立性**という、
系の外からしか供給できないものだからである。

### (b) 「L6 がやっているのはループエンジニアリング」— **部分支持。境界が引ける**

GEPA / SkillHone の存在は、L6 の職掌（トレース→やり方の改訂）が**自動化可能な実在領域**であることを
示す。この二日間で私が手でやった「責務文の推敲・skill の追加・失敗観測からの規範化」は、
まさにその領域の手動実行だった——**師匠の指摘どおり、私は L6 を代行していた**。

ただし GEPA にも**人間が与え続ける引数**がある: **メトリック（何をもって良しとするか）**である。
GEPA は与えられた評価関数に向かって進化するのであって、評価関数そのものの正しさは扱わない。
つまりループエンジニアリングは3層に割れる:

| 層 | 中身 | 誰の仕事か | この二日間の対応物 |
|---|---|---|---|
| **決定性** | 契約・終端・ゲート・持ち越し・床 | **ハーネス**（コード） | 034 `no_action`・037 A 写し込み・038 3軸監査・発行ゲート |
| **役割定義** | プロンプト・skill・定義書の改訂 | **L6**（自動化可能。今は手動） | 責務文 v2〜v4・skill 6件・変異検査 |
| **価値定義** | 実害の定義・評価器の妥当性・停止して良い状態とは何か | **人間**（業界でも残ると明言） | **未決のまま保留した3点そのもの** |

### (c) 「決定性と役割定義の混在」— **支持**

12-Factor Agents・CAAF・LangChain の4層ループ、いずれも同じ分解を提示している。
この二日間の成果物も正確にこの2層に分かれた（上の表）。

### (d) 「この二日間がまさにそれ」— **支持**

そして、クールダウン前の師匠のもやもや——「今やっていることが本当に
『自己成長で解けないからハーネスに置くべき機構』なのか確信が持てない」——への調査からの答え:

> **二日間の成果の大半（責務文・skill）は L6 領域の手動代行であり、ハーネスに刻んだもの
> （no_action 契約・写し込み・3軸監査・持ち越し）は業界の harness engineering の教科書的中身と
> 一致している。置き場所は間違っていない。間違っていたのは、3層を区別せずに
> 同じ「穴を塞ぐ」作業として進めたことである。**

残件「検査器の正しさ」は、業界の対処（EvalGen）が示すとおり**第3層＝価値定義に人間の採点を
入れる問題**であり、skill の言葉でも（044 で実測）、モデルの能力でも（042 で実測）解けない。
mu で言えば「独立 QA に検算の選択を渡す」は第1層（構造）で近似できるが、
**「QA の検査が正しいか」はまた同じ問いに戻る**——業界もそこで人間を入れている。

---

## 4. 提言（次の協議の材料）

1. **保留中の未決(1)「実害の定義」は、業界の言葉では「メトリックの設計」であり、
   ループエンジニアリングの人間側の核**である。ここを決めずに機構を足しても、
   040 のように「安定して間違った場所に落ち着く」——優先順位は正しい
2. **L6 の設計（033）に GEPA / SkillHone を参照として取り込む**。特に「実行トレース＋
   自然言語の反射でプロンプト/skill を外科的に編集する」形は、033 の「診断→skill 書き足し」と
   同型で、実装の当てになる
3. **検証器の検証には人間の採点を入れる**（EvalGen 型）。mu なら「検査器が挙げた件数の内訳を
   師匠が抜き取りで採点する」1ステップを L6 のループに置く——全自動化しないことが、
   criteria drift への業界の答えである
4. この二日間の記録（runs/035〜044）は、**ループエンジニアリングの失敗と対処の教材**として
   そのまま読める。業界の概念との対応表（§2）を付けたことで、外部の言葉でも説明可能になった

## Sources

- [IBM — What Is Loop Engineering?](https://www.ibm.com/think/topics/loop-engineering)
- [LangChain — The Art of Loop Engineering](https://www.langchain.com/blog/the-art-of-loop-engineering)
- [TrueFoundry — Loops, Harnesses, and 6,000 Engineers: AIEWF 2026 Recap](https://www.truefoundry.com/blog/aiewf-2026-loops-harness-engineering)
- [eesel — Loop engineering explained](https://www.eesel.ai/blog/loop-engineering)
- [bdtechtalks — Demystifying loop engineering](https://bdtechtalks.com/2026/06/22/ai-loop-engineering/)
- [NxCode — What is Harness Engineering](https://www.nxcode.io/resources/news/what-is-harness-engineering-complete-guide-2026)
- [CAAF — Harness as an Asset: Enforcing Determinism](https://arxiv.org/pdf/2604.17025)
- [Shankar et al. — Who Validates the Validators?（UIST 2024）](https://arxiv.org/abs/2404.12272)
- [SpecBench — Measuring Reward Hacking in Long-Horizon Coding Agents](https://arxiv.org/abs/2605.21384)
- [The Verification Horizon — No Silver Bullet for Coding Agent Rewards](https://arxiv.org/pdf/2606.26300)
- [Jason Wei — Asymmetry of verification and verifier's law](https://www.jasonwei.net/blog/asymmetry-of-verification-and-verifiers-law)
- [When Agents Do Not Stop — Infinite Agentic Loops](https://arxiv.org/pdf/2607.01641)
- [Towards AI — When Should an Agent Stop? The Anatomy of Termination](https://pub.towardsai.net/when-should-an-agent-stop-the-anatomy-of-termination-17644145309a)
- [MindStudio — Agent Loops with Verifiable Stop Conditions](https://www.mindstudio.ai/blog/agent-loops-verifiable-stop-conditions)
- [Inference Systems — Reconciliation Loop（用語集）](https://inferensys.com/glossary/tool-calling-and-api-execution/orchestration-layer-design/reconciliation-loop)
- [Context Kubernetes — Declarative Orchestration for Agentic AI](https://arxiv.org/pdf/2604.11623)
- [RIVA — LLM Agents for Configuration Drift Detection](https://arxiv.org/pdf/2603.02345)
- [GEPA（ICLR 2026 Oral）](https://github.com/gepa-ai/gepa)
- [Nous Research — Hermes Agent Self-Evolution](https://github.com/NousResearch/hermes-agent-self-evolution)
- [SkillHone — Continual Agent Skill Evolution](https://arxiv.org/pdf/2606.08671)
- [12-Factor Agents](https://paddo.dev/blog/12-factor-agents/)
- [Vikas Malpani — Loop Engineering: The Real Moat in AI Agents](https://vikasmalpani.com/loop-engineering-ai-agents/)
