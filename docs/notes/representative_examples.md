# Representative Examples

These examples are selected from `outputs/metrics/disagreement_cases.csv` for the final report discussion.

## 1. Acceptable alias penalized by entity metric

- id: `Q11271903_1`
- model: `gpt4o_mini`
- entity type: `Fictional entity`
- source: In which television series does the fictional character Juice Ortiz appear?
- reference: 가상의 캐릭터 주스 오티즈는 어떤 텔레비전 시리즈에 출연하나요?
- reference mention: `주스 오티즈`
- prediction: "주스 오르티즈"라는 가상의 캐릭터는 어떤 TV 시리즈에 등장하나요?
- human label: `acceptable` / `acceptable_alias`
- automatic pattern: `entity_metric_too_harsh_on_acceptable_output`
- why it matters: A Korean-valid alias or variant is acceptable to humans but fails strict mention matching.

## 2. General metric too harsh

- id: `Q850042_0`
- model: `gpt4o`
- entity type: `Place of worship`
- source: Is Uppsala Cathedral open to the public?
- reference: 웁살라 대성당은 대중에게 개방되어 있습니까?
- reference mention: `웁살라 대성당`
- prediction: 웁살라 대성당은 일반인에게 공개되어 있나요?
- human label: `acceptable` / `correct`
- automatic pattern: `general_metric_too_harsh_on_acceptable_output`
- why it matters: The translation is human-acceptable, but chrF/BLEU-style overlap is low.

## 3. Both metrics too harsh

- id: `Q2031786_0`
- model: `gpt4o_mini`
- entity type: `Musical work`
- source: What year was Piano Sonata No. 9 composed?
- reference: 피아노 소나타 9번은 몇 년도에 작곡되었나요?
- reference mention: `피아노 소나타 9번`
- prediction: 피아노 소나타 제9번은 언제 작곡되었나요?
- human label: `acceptable` / `correct`
- automatic pattern: `both_metrics_too_harsh_on_acceptable_output`
- why it matters: Both general and entity metrics reject an output that Korean annotation accepts.

## 4. Wrong Korean rendering strategy

- id: `Q1067463_0`
- model: `gpt4o_mini`
- entity type: `Place of worship`
- source: 2) What type of place is Koutloumousiou monastery?
- reference: 2) 쿠틀루무시우 수도원은 어떤 곳인가요?
- reference mention: `쿠틀루무시우 수도원`
- prediction: 2) 쿨투룸무시우 수도원은 어떤 종류의 장소인가요?
- human label: `borderline` / `wrong_rendering_strategy`
- automatic pattern: `borderline_human_general_pass_entity_fail`
- why it matters: The entity is recognizable, but the Korean form is judged to use the wrong rendering strategy.

## 5. Adaptation needed

- id: `Q1167579_1`
- model: `gpt4o`
- entity type: `Movie`
- source: Who directed the 1995 movie Village of the Damned?
- reference: 1995년 영화 저주받은 마을 를 감독한 사람은 누구입니까?
- reference mention: `저주받은 마을`
- prediction: 1995년 영화 "Village of the Damned"의 감독은 누구인가요?
- human label: `borderline` / `wrong_rendering_strategy`
- automatic pattern: `borderline_human_general_pass_entity_fail`
- why it matters: The case needs Korean cultural/title adaptation rather than direct translation alone.

## 6. Preserve-English case

- id: `Q48835523_2`
- model: `gpt4o_mini`
- entity type: `Musical work`
- source: When was On Wings of Song composed?
- reference: 노래의 날개 위에 은 언제 작곡되었나요?
- reference mention: `노래의 날개 위에`
- prediction: "On Wings of Song"는 언제 작곡되었나요?
- human label: `acceptable` / `correct`
- automatic pattern: `both_metrics_too_harsh_on_acceptable_output`
- why it matters: Acronyms or source forms may be better preserved in Korean context.

## 7. Metric misses human rejection

- id: `Q19938912_0`
- model: `gpt4o_mini`
- entity type: `Book`
- source: What does BnF stand for in BnF authorities for books?
- reference: BnF는 책의 BnF 당국 에서 무엇을 의미하나요?
- reference mention: `BnF 당국`
- prediction: BnF는 도서에 대한 BnF 권한에서 무엇을 의미합니까?
- human label: `unacceptable` / `wrong_rendering_strategy`
- automatic pattern: `general_metric_miss_human_rejection`
- why it matters: An automatic metric passes an output that humans reject.

## 8. Borderline strategy-sensitive case

- id: `Q3492886_1`
- model: `gpt4o_mini`
- entity type: `Artwork`
- source: Who is the author of Specters of Marx?
- reference: 마르크스의 유령들의 저자는 누구인가요?
- reference mention: `마르크스의 유령들`
- prediction: "스펙터들"의 저자는 누구인가요?
- human label: `borderline` / `partial_entity_error`
- automatic pattern: `borderline_human_general_pass_entity_fail`
- why it matters: The output is not simply right or wrong; entity strategy is the issue.
