# MV BRAIN Hermes Adapter

MV BRAIN Hermes Adapter는 기존 [`mv-brain`](https://github.com/hyuk-ju/mv-brain) 프로젝트를 Hermes나 MCP 클라이언트에서 써볼 수 있게 만든 작은 어댑터입니다.

요즘 에이전트 쪽에서 CLI와 MCP가 같이 많이 쓰이고 있는데, 이 repo는 둘 다 지원합니다.

- 터미널에서 직접 쓰는 **CLI 도구**
- Hermes 같은 에이전트가 호출하는 **MCP 서버**

즉, 일반 사용자는 `mv-brain-hermes` 명령어로 바로 실행할 수 있고, 에이전트 환경에서는 MCP tool로 같은 기능을 호출할 수 있습니다.

## 왜 만들었나

MV BRAIN은 뮤직비디오 편집 워크플로우를 위한 local-first 프로젝트입니다.

많은 클립 중에서 쓸만한 장면을 찾고, 자연어로 검색하고, 편집자가 이어받을 수 있는 러프컷 자료를 만드는 쪽에 초점을 두고 있습니다.

`mv-brain-hermes`는 그중 일부 기능을 더 가볍게 분리해서, Hermes 같은 에이전트가 사용할 수 있게 만든 버전입니다.

완성 영상을 자동으로 만들어주는 도구라기보다는, 편집자가 다음 단계에서 바로 쓸 수 있는 중간 산출물을 정리하는 도구에 가깝습니다.

## 지금 되는 것

- demo 클립 메타데이터 생성
- 로컬 클립 메타데이터 검색
- JSON/CSV 컷리스트 export
- 러프컷 순서를 담은 `preview_manifest.json` 생성
- 에이전트/편집자 handoff용 clip pack 저장
- 선택적으로 ffmpeg를 이용한 MP4 클립 추출
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
```

MCP로 노출되는 기능은 다음과 같습니다.

- `list_clips`
- `search_clips`
- `export_cutlist`
- `export_clip_pack`
- `export_clips`
- `export_preview_manifest`

정리하면, CLI는 사람이 터미널에서 쓰는 입구고, MCP는 Hermes 같은 에이전트가 같은 기능을 호출하는 입구입니다.

## 범위

이 repo는 무거운 영상 분석을 직접 하는 본체가 아닙니다.

장면 분석, caption, embedding, reference matching 같은 더 큰 기능은 메인 [`mv-brain`](https://github.com/hyuk-ju/mv-brain) 쪽의 영역입니다.

이 adapter는 그 결과로 나온 클립 메타데이터를 검색하고, 컷리스트와 러프컷 자료로 내보내고, 에이전트가 접근할 수 있게 만드는 얇은 연결 레이어입니다.

## 보안/프라이버시

- 데모에는 API key가 필요 없습니다.
- `.env`, 생성된 미디어, 로컬 데이터 폴더는 git에서 제외합니다.
- MP4 렌더링은 명시적으로 `--render`를 줄 때만 실행됩니다.
- 렌더링은 입력 메타데이터에 적힌 로컬 파일 경로만 읽습니다.
- 실제 개인 영상이나 provider 호출 없이도 기본 데모를 확인할 수 있습니다.
