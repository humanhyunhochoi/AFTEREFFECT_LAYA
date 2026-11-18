# LAYA AE Graphics

**한국어 명령으로 만드는 After Effects 반복 그래픽 도구.**

[hyun2xyz/AFTEREFFECT_LAYA](https://github.com/hyun2xyz/AFTEREFFECT_LAYA)를 기반으로
방사형 배열, 물결 격자, 윤곽선, 흩뿌리기, 텍스트 배열, 잔상, 순차 등장 기능을 추가한
개인 확장판입니다. Python 표준 라이브러리와 고정 JSX로 실행하며, 그래픽 명령에 별도
AI 모델이나 pip 패키지가 필요하지 않습니다.

## 반복 그래픽 7종

| 기능 | 조절할 수 있는 값 | 생성 결과 |
| --- | --- | --- |
| 방사형 배열 | 개수, 반지름, 도형, 크기, 회전속도, 색 | 편집 가능한 원형 패턴 |
| 물결 격자 | 행·열, 간격, 크기, 진폭, 속도, 시드 | 시간에 따라 흔들리는 점 격자 |
| 윤곽선 | 선 개수, 반지름, 간격, 왜곡, 두께, 속도, 시드 | 유기적인 등고선 애니메이션 |
| 흩뿌리기 | 개수, 크기 범위, 분포, 팔레트, 시드 | 재현 가능한 도형 필드 |
| 텍스트 배열 | 문구, 행·열, 가로·세로 간격, 글자크기, 회전, 색 | 타일별 편집 가능한 텍스트 |
| 잔상 | 복제 수, 시간 간격, 불투명도 감쇠 | 선택한 2D 레이어의 지연된 변형 |
| 순차 등장 | 시간차, 소요 시간, 이동량, 순서, 시드 | 선택 레이어의 위치·불투명도 키프레임 |

설치를 마친 뒤 AE에서 작업할 컴포지션을 선택하고 사용합니다.

```sh
laya-ae '방사형 패턴 개수 48 반지름 230 회전속도 12'
laya-ae '흔들리는 격자 행 10 열 18 간격 56 속도 0.25 시드 7'
laya-ae '윤곽선 패턴 선 40개 반지름 320 왜곡 60'
laya-ae '도형 흩뿌리기 개수 100 팔레트 네온 시드 42'
laya-ae '텍스트 반복 "WAVE" 행 5 열 6'
laya-ae '선택 레이어 잔상 만들어줘 개수 12 간격 0.08 감쇠 0.84'
laya-ae '선택 레이어들 0.05초 간격으로 등장시켜줘'
laya-ae --list
```

잔상은 움직이는 2D 레이어 하나, 순차 등장은 정적인 2D 레이어 둘 이상을 선택합니다.
기존 위치·불투명도 애니메이션이 있으면 순차 등장은 실행 전에 거절합니다.
생성 명령을 다시 실행하면 새로운 그래픽을 추가합니다.

**[전체 옵션과 예시 → docs/graphics.md](docs/graphics.md)**

## 이 확장판 받기

```sh
git clone https://github.com/humanhyunhochoi/AFTEREFFECT_LAYA.git
cd AFTEREFFECT_LAYA
python3.13 -B scripts/setup_environment.py --prepare
.venv/bin/python -B scripts/setup_environment.py --check
.venv/bin/python -B scripts/terminal.py --dry-run '윤곽선 패턴 선 40개 왜곡 60'
```

실제 실행에는 정식 AE 24 이상과 스크립트 파일 쓰기 권한이 필요합니다.
운영체제별 AE 경로·권한 설정은 아래 설치 안내를 따릅니다. `laya-ae` 실행기는
`scripts/install_terminal.py --install`로 선택 설치하며, 설치 전에도 `scripts/terminal.py`를
프로젝트 `.venv`의 Python으로 실행할 수 있습니다.

검증: Python 3.13.18에서 자동 테스트 65개와 별도 소스 폴더 실행 검사를 통과했고,
macOS AE 26.5에서 7종 그래픽의 실제 도형·텍스트·표현식·키프레임과 갤러리 화면을
확인했습니다. Windows의 실제 AE 앱 실행은 미검증입니다. [검증 범위](docs/validation.md).

소스·문서·테스트를 공유합니다. 개인 AE 프로젝트, 영상·이미지, 가상환경, 머신별 경로,
모델 가중치는 포함하지 않습니다. 원본 MIT 라이선스와 출처 고지는 유지합니다.

## 설치 및 원본 수업 안내

**빈 Mac·Windows에서 설치 안내부터 첫 After Effects 명령까지.**
Codex·Claude Code와 함께 작은 스크립트를 읽고 바꾸며 배우는 수업용 출발점입니다.

공통강의의 Git 세팅을 마친 뒤 이 저장소를 내 GitHub 계정에 **포크**해서 받고
→ 받은 폴더를 로컬 Codex에서 열기 → **[START-HERE.md](START-HERE.md)**.
전역 스킬 설치는 필요하지 않습니다. 내 작업은 내 포크에 push하고 강사 업데이트는 pull로 받습니다.

첫 실습은 **Python3.13(또는3.12) + 정식 AE24 이상**만 준비합니다.
기본 조작은 Python 표준 라이브러리와 고정 JSX로 실행하며, pip 패키지·모델 가중치·
MCP·서버·Homebrew를 설치하지 않아도 됩니다. Adobe 앱/라이선스는 별도입니다.

```sh
# Mac 예시: 설치 안내를 마친 뒤, 이 폴더에서
.venv/bin/python -B scripts/terminal.py 컴포지션 19201090 만들어줘
.venv/bin/python -B scripts/terminal.py 배경 색 초록색으로 바꿔줘
```

Windows에서는 `.\.venv\Scripts\python.exe`로 같은 스크립트를 실행합니다.
선택 설치한 `laya-ae`/`laya-ae.cmd`로도 같은 문장을 쓸 수 있습니다.
이미 Laya-Mac이 있는 Mac만 기존 `laya`와 연결할 수 있습니다.
`comp 1920 1080`, `애프터이펙트 컴포지션 1920 1080`, `컴포지션 19201080`도
생성 명령입니다. 기존 터미널의 `laya`가 시스템 상태만 출력하면
[셸 연결 확인](docs/commands.md#기존-터미널이-시스템-상태만-보여-줄-때)을 따릅니다.

| 순서 | 지금 읽을 문서 |
| --- | --- |
| 0. 포크해서 받기·업데이트 | [fork-and-update](docs/fork-and-update.md) |
| 1. 설치·시작 문장 | [START-HERE](START-HERE.md) |
| 2. 현재 OS 준비 | [Mac](docs/setup-macos.md) · [Windows](docs/setup-windows.md) |
| 3. 첫 컴프와 초록 배경 | [첫 수업](docs/first-lesson.md) |
| 4. 필요한 명령 하나 | [명령어 목록](docs/commands.md) |
| 반복 그래픽 7종 | [방사형·물결·윤곽선·흩뿌리기·텍스트·잔상·순차 등장](docs/graphics.md) |
| 5. 요청했을 때만 로컬 분류 | [선택 Laya](docs/laya.md) |
| 실제로 확인한 범위 | [validation](docs/validation.md) |

`19201090`은 **1920×1090**, 생략한 값은30fps/10초입니다. 명령은 현재 활성 컴프와
선택 레이어를 대상으로 하며 `--dry-run`은 앱을 바꾸지 않습니다. 배경색 명령은
컴포지션 설정을 바꿉니다. 불투명한 렌더 배경 레이어를 자동으로 만들지 않습니다.

Laya는 Jev와 비슷한 구조화된 판단을 제공하는 독립 오픈 모델입니다. 이 starter에서는
애매한 짧은 요청의 분류에만 선택적으로 씁니다. 명확한 지원 명령은 모델을 호출하지
않으며, 자유로운 한국어로 AE의 모든 기능을 조작하는 도구는 아닙니다.
토큰 절감률을 약속하거나 Laya 추천을 실행 승인으로 사용하지 않습니다.

Mac은 AE의 `DoScriptFile`, Windows는 `AfterFX.exe -r`로 고정 JSX를 전달하고 native
결과 파일을 읽습니다. 자동 저장·닫기·삭제·렌더는 제공하지 않습니다. 실패·부분 실행·
결과 미확인에는 같은 job을 재전송하지 않습니다.

공용 Python 코드와 Mac AE의 실제 확인을 구분합니다. Windows AE 앱은 수강생 컴퓨터에서
첫 native 검수를 합니다. 원본·개인 작업·모델은 Git에 올리지 않습니다.

새 기능은 한 번에 하나씩, 학생의 실제 요청과 검수 결과를 바탕으로 추가하세요.
이 폴더 전체가 프로젝트 스킬이며 다른 개인 하네스를 설치하지 않습니다.
