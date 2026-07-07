<p align="center">
  <img src="assets/banner.png" alt="Fable Workflow" width="100%">
</p>

<h1 align="center">Fable Workflow</h1>

<p align="center">
  어떤 모델(Opus·Sonnet·Haiku·Fable)에게도 Anthropic의 Fable처럼 일하게 만드는
  이식 가능한 에이전트 스킬입니다. 핵심은 <b>"만들기 전에 모르는 것(unknown)을 먼저 드러낸다"</b>입니다.
</p>

<p align="center">
  <a href="README.md">English</a> · <b>한국어</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="MIT">
  <img src="https://img.shields.io/badge/format-SKILL.md-purple" alt="SKILL.md">
  <img src="https://img.shields.io/badge/models-Opus%20%C2%B7%20Sonnet%20%C2%B7%20Haiku%20%C2%B7%20Fable-orange" alt="models">
</p>

---

## 이게 뭔가요

`fable-workflow`는 Anthropic의 Fable 계열 모델과 일하는 작업 방법을 재사용 가능한 [`SKILL.md`](SKILL.md) 하나로 정리한 것입니다. Claude Code, Cursor, 또는 어떤 에이전트 프레임워크에도 그대로 넣을 수 있습니다.

요즘 모델은 스스로 방대한 해답 공간을 탐색할 만큼 강력합니다. 그래서 병목은 더 이상 *모델의 능력*이 아니라, **모델이 움직이기 전에 내 머릿속 지도가 실제 현실과 얼마나 맞는가**입니다. 스펙이 말하지 않은 지점 하나하나가 **unknown**(모델이 정하지 않은 결정 지점)이고, 그냥 두면 모델은 이를 **말없이 임의로 결정**해 버립니다. 이 스킬은 모델이 그 unknown들을 **먼저 드러내게** 한 뒤에 만들게 합니다.

## 핵심 한 가지

> **지도는 영토가 아니다.** 내 계획·스펙·프롬프트는 *지도*이고, 실제 코드베이스와 제약은 *영토*입니다. 둘이 어긋나는 지점이 바로 **unknown**입니다. 모델이 추측하게 두지 말고, 그 결정을 명시적으로 내리세요.

## 작업 루프

1. **족쇄 풀기(Unhobble)** — 기억이 아니라 도구를 쓰게 합니다. 세기·열거·조회는 *스크립트로* 풀게 하세요.
2. **모르는 것 찾기** — 만들기 전에: 블라인드 스팟 패스, 나를 인터뷰시키기, 취향 결정은 여러 변형(N개) 제시, 스펙 대신 레퍼런스(다른 지도) 주기.
3. **만들면서 이탈 기록** — 마주친 unknown과 그때의 선택을 ASSUMPTIONS / NOTES 목록으로 남깁니다.
4. **루프 안에 남기** — 병합 전 모델이 나를 퀴즈로 확인하게 해서, 내가 작업을 계속 주도하도록 합니다.

전체 방법은 [`SKILL.md`](SKILL.md), 복사해서 바로 쓰는 프롬프트는 [`prompts.md`](prompts.md)를 참고하세요.

## 설치

### Claude Code — 플러그인 (권장)
```shell
/plugin marketplace add joey114132/fable-workflow-skill
/plugin install fable-workflow
```

### Claude Code — 수동 복사
```bash
git clone https://github.com/joey114132/fable-workflow-skill.git
./fable-workflow-skill/install.sh ~/your-project/.claude/skills
```
또는 `SKILL.md` + `prompts.md`를 `~/your-project/.claude/skills/fable-workflow/`에 복사하세요. Claude Code는 `SKILL.md`를 자동으로 찾아 `description`을 보고 발동합니다.

### Cursor
```bash
git clone https://github.com/joey114132/fable-workflow-skill.git
mkdir -p .cursor/rules
cp fable-workflow-skill/integrations/cursor/fable-workflow.mdc .cursor/rules/
```
Cursor가 규칙의 `description`을 보고 필요할 때(agent-requested) 자동으로 불러옵니다.

### Antigravity · Codex · Aider · Zed 등 AGENTS.md 지원 에이전트
이식용 규칙 파일을 프로젝트 루트에 복사하세요:
```bash
cp fable-workflow-skill/integrations/AGENTS.md ./AGENTS.md
```
Antigravity는 `.agents/rules/`에 두거나, 전역 규칙은 `~/.gemini/GEMINI.md`도 읽습니다.

모든 어댑터와 툴별 상세는 [`integrations/`](integrations/)를 보세요.

## 벤치마크

이 스킬이 실제로 모델의 행동을 바꿀까요? 일부러 모호하게 쓴 스펙(*"우리 API를 분당 100요청으로 제한해줘"* — 아키텍처를 바꿀 만한 unknown이 약 8개 숨어 있음)으로, 클라우드와 로컬을 합쳐 여덟 모델을 스킬 있음/없음으로 나눠 A/B 테스트했습니다:

![벤치마크](benchmark/bench.png)

| 모델 | 종류 | 스킬 없음 | 스킬 있음 | Δ |
|---|---|:---:|:---:|:---:|
| llama3:8b | local | 8 | 27 | **+19** |
| qwen2.5:7b | local | 44 | 54 | +10 |
| gemma3:4b | local | 50 | 38 | **−12** |
| **Haiku 4.5** | cloud | 66 | 81 | **+15** |
| qwen3.6 | local | 82 | 87 | +5 |
| **Sonnet 5** | cloud | 91 | 98 | +7 |
| **Opus 4.8** | cloud | 95 | 98 | +3 |
| **Fable 5** | cloud | 96 | 100 | +4 |

**답변·사고 품질**을 100점 만점으로, Thinking /50 + Answer /50로 나눠 채점했습니다([상세 기준·세부 점수](benchmark/RESULTS.md)). 이 스킬은 **추론 증폭기이지 코딩 증폭기가 아닙니다** — *사고* 품질은 **모든** 모델에서 오르지만(+2~+18), *답변* 품질은 모델이 그 계획을 이미 구현할 수 있을 때만 오릅니다(약한 로컬 모델은 제자리 또는 하락 — gemma3의 **−12**는 n=1 편차 아티팩트, RESULTS 참고). 총점 향상이 가장 큰 건 "능력은 있으나 덜 추론하던" 모델입니다(llama3:8b +19, Haiku 4.5 +15). Fable 5는 도움 없이도 **96점**입니다 — 거저 받은 100점이 아닙니다.

전체 방법론·채점 기준·모델별 근거·한계는 **[benchmark/RESULTS.md](benchmark/RESULTS.md)** 를 보세요.

## 저장소 구조

```
fable-workflow-skill/
├── SKILL.md            # 스킬 본체 (그대로 드롭인, 방법론 원본)
├── prompts.md          # 복사해서 쓰는 프롬프트 템플릿
├── integrations/       # 다른 툴용 어댑터
│   ├── AGENTS.md       # Antigravity · Codex · Aider · Zed · Jules …
│   └── cursor/fable-workflow.mdc
├── install.sh          # .claude/skills 디렉터리로 스킬 복사
├── benchmark/
│   ├── RESULTS.md      # 모델 간 A/B 평가
│   └── bench.png       # 결과 차트
├── assets/banner.png
├── README.md           # English
└── README.ko.md        # 한국어
```

## 참고

이 저장소는 하나의 작업 방법을 스킬로 포장한 것이며, Anthropic의 공식 배포물이 아닙니다.

## 라이선스

[MIT](LICENSE)
