# 웹사이트 게시

정적 웹사이트 파일을 `gh-pages` 브랜치에 올립니다. 개발 기본 브랜치는 변경하지 않습니다.

## GitHub에서 최초 1회

저장소 관리자 계정으로 다음 설정을 선택하세요.

1. https://github.com/jeon-bong-hwan/desktop-tutorial/settings/pages
2. Build and deployment → Source: **Deploy from a branch**
3. Branch: **gh-pages**, 폴더: **/ (root)** → Save
4. GitHub가 표시하는 배포 완료와 Visit site 주소를 확인합니다.

예상 주소: https://jeon-bong-hwan.github.io/desktop-tutorial/

이 주소는 Pages 활성화 및 배포 완료 전에는 작동하지 않을 수 있습니다. GitHub 설정이 비활성화되거나 권한/요금제 제한 안내가 나오면 해당 조건을 먼저 해결해야 합니다. 비공개 저장소라도 Pages 사이트는 요금제·설정에 따라 공개될 수 있으므로 게시 범위를 확인하세요. 현재 배포 자료는 사용자가 제공한 두 공공데이터 파일에서 화면에 필요한 항목만 추린 것입니다.

## 이후 업데이트

Python 3, Node.js, origin에 대한 Git 쓰기 권한이 있는 개발 환경에서:

```sh
npm run deploy
```

테스트 → 빌드 → gh-pages 파일 업로드를 수행합니다. 최초 GitHub Pages 활성화는 대신 수행하지 못합니다. Pages 활성화 뒤에는 gh-pages 갱신으로 게시가 시작됩니다.

별도의 GitHub Actions 방식도 `.github/workflows/pages.yml`에 제공하지만, 위 브랜치 방식과 동시에 선택할 필요는 없습니다. Codex 환경의 게시와 이 웹사이트 배포는 별개입니다.
