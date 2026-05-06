# MV BRAIN Hermes Adapter

MV BRAIN Hermes Adapter는 기존 [`mv-brain`](https://github.com/hyuk-ju/mv-brain) 프로젝트의 클립 분석 결과를 Hermes나 MCP 클라이언트에서 검색하고, 바로 받을 수 있는 **MP4 클립 묶음**으로 내보내기 위한 어댑터입니다.

요즘 에이전트 쪽에서 CLI와 MCP가 같이 많이 쓰이고 있는데, 이 repo는 둘 다 지원합니다.

- 터미널에서 직접 쓰는 **CLI 도구**
- Hermes 같은 에이전트가 호출하는 **MCP 서버**

즉, 일반 사용자는 `mv-brain-hermes` 명령어로 바로 실행할 수 있고, 에이전트 환경에서는 MCP tool로 같은 기능을 호출할 수 있습니다.

## 왜 만들었나

MV BRAIN은 뮤직비디오 편집 워크플로우를 위한 local-first 프로젝트입니다.

많은 클립 중에서 쓸만한 장면을 찾고, 자연어로 검색하고, 최종적으로는 에이전트가 선택한 구간을 **MP4 파일로 잘라서 내려받을 수 있게** 만드는 쪽에 초점을 둡니다.

`mv-brain-hermes`는 특히 로컬 PC가 아니라 서버/Hermes 환경에서 작업하는 경우를 고려합니다. 영상 원본은 Google Drive, rclone, 서버 폴더, NAS 같은 곳에서 가져오고, Hermes는 분석된 클립 메타데이터를 검색한 뒤 필요한 구간만 MP4로 export합니다.

이번 버전의 목표는 편집툴별 프로젝트 연동이 아닙니다. **에이전트가 찾은 후보 구간을 MP4로 받을 수 있게 하는 것**이 1차 목표입니다.

## 지금 되는 것

- demo 클립 메타데이터 생성
- 로컬 또는 서버의 클립 메타데이터 검색
- Google Drive/rclone 등으로 가져온 영상 파일 경로 사용
- JSON/CSV 컷리스트 export
- MP4 렌더링 전 rough preview manifest 생성
- 선택 구간을 ffmpeg로 MP4 클립으로 추출
- MP4 export 결과를 `render_manifest.json`으로 기록
- Hermes/MCP tool로 호출

## 빠른 데모

실제 영상, Qdrant, API key, 클라우드 provider 없이 실행할 수 있습니다.

```bash
python3 -m pip install -e '.[test]'
mv-brain-hermes demo --out data/demo/clips.json
mv-brain-hermes search "neon chorus dance" --clips data/demo/clips.json
mv-brain-hermes export-pack "chorus" --clips data/demo/clips.json --out exports/chorus-pack
```

`export-pack`을 실행하면 대략 이런 파일들이 저장됩니다.

```text
cutlist.json          # 에이전트/스크립트가 읽기 좋은 구조화 컷 목록
cutlist.csv           # 사람이 스프레드시트로 보기 좋은 컷 목록
preview_manifest.json # 러프컷 순서와 타임라인 정보
README.md             # export pack 설명
```

## 영상 가져오기: 로컬 PC가 아닐 때

Hermes는 꼭 영상이 있는 로컬 PC에서만 도는 게 아닙니다. 서버, 원격 머신, 개인 워크스테이션, NAS 근처에서 돌 수도 있습니다.

그래서 이 버전은 “편집 프로그램으로 바로 넘기기”보다 **영상 원본을 작업 머신으로 가져오고, 필요한 구간만 MP4로 export하는 흐름**을 우선합니다.

추천 입력 방식:

```text
Google Drive / Dropbox / NAS / 서버 폴더
  -> rclone 또는 Drive Desktop으로 작업 머신에 동기화
  -> mv-brain ingest
  -> Qdrant clip archive
  -> mv-brain-hermes snapshot-qdrant
  -> Hermes가 검색 후 MP4 export
```

Google Drive를 쓰는 경우 예시:

```bash
# rclone 설정은 한 번만 진행
rclone config

# Drive 폴더를 서버/작업 머신으로 복사
rclone copy gdrive:mv-footage ./videos

# 메인 MV BRAIN에서 분석/임베딩/Qdrant 저장
cd ../mv-brain
mv-brain ingest ./videos/*.mp4

# Hermes adapter에서 Qdrant snapshot 생성
cd ../mv-brain-hermes
PYTHONPATH=../mv-brain mv-brain-hermes snapshot-qdrant \
  --out data/mvbrain/clips.json

# 검색된 후보 구간을 MP4로 export
mv-brain-hermes export-clips "chorus dance" \
  --clips data/mvbrain/clips.json \
  --out exports/chorus-mp4 \
  --limit 3 \
  --render
```

## 현재 스택

현재 repo는 일부러 가볍게 만들어둔 Python adapter입니다.

- Python 3.11+
- 표준 라이브러리 기반 CLI: `argparse`, `json`, `csv`, `pathlib`, `subprocess`
- 패키징: `setuptools`, `pyproject.toml`
- MCP 서버: `mcp.server.fastmcp.FastMCP` (`mcp` extra 설치 시 사용)
- 테스트: `pytest`
- 선택 렌더링: `ffmpeg`
- 입력 데이터: 로컬 `clips.json` 메타데이터 파일
- 출력 데이터: `cutlist.json`, `cutlist.csv`, `preview_manifest.json`, `README.md`, 선택적 MP4 파일과 `render_manifest.json`

## 기존 MV BRAIN과의 차이

메인 [`mv-brain`](https://github.com/hyuk-ju/mv-brain)은 더 큰 앱입니다.

메인 프로젝트 쪽에는 Gemini/Google 계열 분석, embedding, Qdrant 저장소, provider key 설정, 웹 UI 같은 더 무거운 기능들이 들어갑니다.

이 adapter는 그 핵심 기술을 다시 복사해서 따로 구현하지 않습니다. 대신 **메인 MV BRAIN이 만든 Qdrant clip archive를 portable `clips.json` snapshot으로 받아와서 Hermes/MCP가 바로 검색하고 export할 수 있게** 연결합니다.

기본 흐름은 이렇습니다.

```text
mv-brain ingest/search/embedding/Qdrant
  -> mv-brain-hermes snapshot-qdrant
  -> data/mvbrain/clips.json
  -> Hermes/MCP search/export-pack/export-clips
```

그래서 현재 기준으로는:

- Google/Gemini embedding 직접 호출: 메인 `mv-brain` 담당
- Qdrant 저장/임베딩 생성: 메인 `mv-brain` 담당
- Qdrant clip archive snapshot export: 있음 (`snapshot-qdrant`)
- provider auth/API key 관리: 메인 `mv-brain` 또는 사용자의 Hermes 환경 담당
- 로컬 `clips.json` 기반 keyword/label/description 검색: 있음
- Hermes/MCP tool 호출: 있음
- CLI export: 있음
- 선택적 ffmpeg MP4 clip render: 있음

즉 이 repo는 “MV BRAIN 전체 기능의 복사본”이 아니라, MV BRAIN의 분석 결과를 Hermes가 쓸 수 있게 만드는 adapter입니다.

## CLI인가 MCP인가?

둘 다입니다.

기본적으로는 CLI 패키지입니다.

```bash
mv-brain-hermes search "chorus dance" --clips data/demo/clips.json
mv-brain-hermes export-pack "chorus" --clips data/demo/clips.json --out exports/chorus-pack
```

동시에 MCP 서버도 포함되어 있어서 Hermes 같은 에이전트가 tool로 호출할 수 있습니다.

```yaml
mcp_servers:
  mvbrain:
    command: "python3"
    args:
      - "-m"
      - "mv_brain_hermes.mcp_server"
    env:
      MV_BRAIN_CLIPS_PATH: "/path/to/clips.json"
      MV_BRAIN_EXPORT_ROOT: "/path/to/exports"
```

MCP write tool은 `MV_BRAIN_EXPORT_ROOT` 안에만 파일을 쓰도록 제한하는 것을 권장합니다. MCP에서 MP4 렌더링을 허용하려면 `MV_BRAIN_ENABLE_RENDER=1`을 명시적으로 설정하세요.

MCP로 노출되는 기능은 다음과 같습니다.

- `list_clips`
- `search_clips`
- `export_cutlist`
- `export_clip_pack`
- `export_clips`
- `export_preview_manifest`
- `snapshot_qdrant`

정리하면, CLI는 사람이 터미널에서 쓰는 입구고, MCP는 Hermes 같은 에이전트가 같은 기능을 호출하는 입구입니다.

## Hermes 온보딩 파일 생성

Hermes가 repo를 받은 뒤 바로 쓸 수 있도록 skill 초안, MCP config snippet, quickstart를 생성할 수 있습니다.

```bash
mv-brain-hermes init-hermes \
  --out hermes_onboarding \
  --repo-path "$(pwd)" \
  --clips "$(pwd)/data/mvbrain/clips.json"
```

생성되는 파일:

```text
hermes_onboarding/skill/SKILL.md
hermes_onboarding/mcp_config.yaml
hermes_onboarding/QUICKSTART.md
```

`SKILL.md`는 Hermes skills 폴더에 복사하거나, repo 안에서 참고용으로 사용할 수 있습니다.

## 범위

이 repo는 무거운 영상 분석을 직접 하는 본체가 아닙니다.

장면 분석, caption, embedding, reference matching 같은 더 큰 기능은 메인 [`mv-brain`](https://github.com/hyuk-ju/mv-brain) 쪽의 영역입니다.

이 adapter는 그 결과로 나온 클립 메타데이터를 검색하고, 필요한 구간을 MP4로 export하고, 에이전트가 접근할 수 있게 만드는 연결 레이어입니다.

이번 버전에서는 편집툴별 프로젝트 export는 우선순위에서 뺍니다. 우선 누구나 받을 수 있는 MP4 결과물을 만드는 흐름에 집중합니다.

## 보안/프라이버시

- 데모에는 API key가 필요 없습니다.
- `.env`, 생성된 미디어, 로컬 데이터 폴더는 git에서 제외합니다.
- MP4 렌더링은 명시적으로 `--render`를 줄 때만 실행됩니다.
- 렌더링은 입력 메타데이터에 적힌 로컬 파일 경로만 읽습니다.
- 실제 개인 영상이나 provider 호출 없이도 기본 데모를 확인할 수 있습니다.
