# 과제2 · 에이전트와 함께 만드는 URL 단축기

2026-2 **고급알고리즘**(SIT2001-01) 과제2의 **시작 저장소**입니다.
채팅창에 묻고 복사·붙여넣기 하던 방식에서 벗어나, Codespace 안의 에이전트가
저장소를 읽고, 파일을 고치고, 테스트를 직접 돌리게 하는 방법을 익힙니다.

- 과제 안내: [lec-algorithm.github.io/lecture/article/hw2-2026](https://lec-algorithm.github.io/lecture/article/hw2-2026/)
- 수업 슬라이드: [lec-algorithm.github.io/lecture/slides/hw2-2026](https://lec-algorithm.github.io/lecture/slides/hw2-2026/)
- 해시 테이블 복습: [주제 08 해시 테이블](https://lec-algorithm.github.io/lecture/course/topic-08-hashing/)

## 시작하기

1. 이 저장소 상단의 **Use this template** → **Create a new repository**
2. 저장소 이름은 `algorithms-hw2`처럼 정합니다. 공개(Public)로 만듭니다.
3. 만들어진 **내 저장소**에서 **Code** → **Codespaces** 탭 → **Create codespace on main**
4. 왼쪽 막대의 Copilot 아이콘을 눌러 채팅 창을 열고, 창 아래쪽에서 **Agent** 모드를 고릅니다.

## 들어 있는 것

| 파일 | 하는 일 |
| --- | --- |
| `SPEC.md` | 명세 틀. 에이전트가 초안을 쓰고 **본인이 고칩니다** |
| `src/` · `tests/` · `experiments/` | 비어 있습니다. 수업에서 채웁니다 |
| `tools/catchup.sh` | 수업 중 놓친 단계를 따라잡는 스크립트 |
| `Makefile` | `make test` · `make serve` · `make experiment` |

정답 코드는 들어 있지 않습니다. 에이전트는 작업 공간의 파일을 읽으므로, 정답이
옆에 있으면 그대로 베껴 와서 연습이 되지 않습니다.

## 명령

컨테이너 안(Codespaces 터미널)에서 실행합니다.

| 하고 싶은 것 | 명령 |
| --- | --- |
| 테스트 | `make test` |
| 웹 서버 (포트 8000) | `make serve` |
| 충돌 실험 | `make experiment` |
| 놓친 단계 따라잡기 | `sh tools/catchup.sh <단계 번호>` |

외부 라이브러리는 쓰지 않습니다. Python 표준 모듈만으로 충분합니다.

### 두 충돌 처리 방식 비교

홈 화면에서 **개별 체이닝** 또는 **선형 탐지**를 선택해 URL을 줄일 수 있습니다.
`/table?strategy=chaining`과 `/table?strategy=linear`에서 각각의 해시 테이블과
탐색 과정을 확인할 수 있습니다. 짧은 링크 경로는 체이닝이 `/c/<코드>`,
선형 탐지가 `/l/<코드>`입니다.

충돌과 실패 탐색을 비교하려면 홈 화면의 **예제 URL 6개 넣기**를 누르세요.
같은 버킷으로 해시되는 링크가 두 테이블에 추가되고, 각 테이블 화면에는 없는 URL을
찾아보는 실패 탐색 예제가 표시됩니다. 검색 URL을 바꿔 직접 비교할 수도 있습니다.

Codespaces에서는 컨테이너 설정을 적용한 뒤 포트 8000이 자동으로 브라우저에 열리며 공개로 설정됩니다.
8000번 포트가 이미 사용 중이면 `make serve PORT=18000`으로 실행하세요. 이 대체 포트도
자동 전달 및 공개로 설정되어 있습니다. 공개 포트는 링크를 아는 누구나 접속할 수
있으므로 시연이 끝나면 공개 범위를 Private으로 바꾸거나 서버를 종료하세요.
데이터는 메모리에만 있어 서버를 재시작하면 사라집니다.

## 로컬에서 하기

```sh
git clone https://github.com/<본인 계정>/<내 저장소>.git
cd <내 저장소>
docker compose up -d
docker compose exec lab bash
```

**이후 모든 `docker compose` 명령은 이 폴더에서 칩니다.**
