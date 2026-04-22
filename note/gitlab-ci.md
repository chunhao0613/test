# GitLab CI 教學與操作紀錄（整合版）

這份文件改成你要的完整型態：

1. 先實作並解釋（從我是怎麼建構出 GitLab CI 開始）
2. 再教學（逐步照做）
3. 最後展現問題解決（檢修流程）

---

## 一、先實作並解釋（建構思路）

### 1. 我是怎麼建構這份 GitLab CI 的

我先把目標拆成三個最小能力，再映射到 CI 檔案：

1. 只在需要時 build（避免每次都浪費時間）
2. build 前先檢查路徑（提早失敗、錯誤清楚）
3. build 成功後 push 到 Docker Hub（標準化交付）

對應到 GitLab CI 的設計如下：

- `.gitlab-ci.yml` 放在 repo 根目錄
- 使用 `stages: [verify, build]`
- `verify` stage 做路徑檢查
- `build` stage 做 Docker build + push
- 用 CI 變數保存敏感資訊（`DOCKER_USERNAME`、`DOCKER_PASSWORD`）

### 2. 先決定檔案與資料夾結構

GitLab CI 最少只需要一個檔案：

```text
.
├─ .gitlab-ci.yml
├─ Dockerfile
├─ app.py
├─ requirements.txt
└─ frontend/
   ├─ Dockerfile
   ├─ index.html
   └─ nginx.conf
```

如果後續 pipeline 變大，建議進階拆分（可選）：

```text
.
├─ .gitlab-ci.yml
└─ .gitlab/
   └─ ci/
      ├─ backend.yml
      └─ frontend.yml
```

這樣做的原因：

- 根檔 `.gitlab-ci.yml` 保持短小，容易看總覽
- 子檔拆分後，每個服務（backend/frontend）可獨立維護

### 3. 實作版 `.gitlab-ci.yml`（可直接用）

```yaml
stages:
  - verify
  - build

variables:
  DOCKER_TLS_CERTDIR: ""
  BACKEND_IMAGE: "$DOCKER_USERNAME/bookkeeping-backend"
  FRONTEND_IMAGE: "$DOCKER_USERNAME/bookkeeping-frontend"

default:
  image: docker:27
  services:
    - docker:27-dind
  before_script:
    - echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin

verify_paths:
  stage: verify
  script:
    - test -f Dockerfile || (echo "Dockerfile missing" && exit 1)
    - test -d frontend || (echo "frontend directory missing" && exit 1)
    - test -f frontend/Dockerfile || (echo "frontend/Dockerfile missing" && exit 1)

build_backend:
  stage: build
  needs: ["verify_paths"]
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
      changes:
        - Dockerfile
        - app.py
        - requirements.txt
  script:
    - docker build -t "$BACKEND_IMAGE:$CI_COMMIT_SHORT_SHA" .
    - docker tag "$BACKEND_IMAGE:$CI_COMMIT_SHORT_SHA" "$BACKEND_IMAGE:latest"
    - docker push "$BACKEND_IMAGE:$CI_COMMIT_SHORT_SHA"
    - docker push "$BACKEND_IMAGE:latest"

build_frontend:
  stage: build
  needs: ["verify_paths"]
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
      changes:
        - frontend/**
  script:
    - docker build -t "$FRONTEND_IMAGE:$CI_COMMIT_SHORT_SHA" ./frontend
    - docker tag "$FRONTEND_IMAGE:$CI_COMMIT_SHORT_SHA" "$FRONTEND_IMAGE:latest"
    - docker push "$FRONTEND_IMAGE:$CI_COMMIT_SHORT_SHA"
    - docker push "$FRONTEND_IMAGE:latest"
```

### 4. 為什麼這樣寫（逐段理由）

- `stages: verify -> build`：先驗證再 build，失敗更早、成本更低
- `docker:dind`：讓 runner 裡能跑 Docker build/push
- `before_script docker login`：所有 job 共用登入邏輯，避免重複
- `rules + changes`：只在真的有影響時才 build，節省 pipeline 時間
- `commit sha + latest` 雙標籤：
  - `latest` 給快速部署
  - `sha` 給可追溯與回滾

### 5. 同場加映：GitHub Actions yml 怎麼寫

你的理解是對的：GitHub 有變更後會觸發 action，內容由 `.github/workflows/*.yml` 決定。

範例（backend）：

```yaml
name: Backend CI/CD

on:
  push:
    branches: [main]
    paths:
      - 'app.py'
      - 'requirements.txt'
      - 'Dockerfile'
      - '.github/workflows/ci-backend.yml'
  workflow_dispatch:

env:
  IMAGE_NAME: bookkeeping-backend

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Buildx
        uses: docker/setup-buildx-action@v3

      - name: Docker Login
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Verify paths
        run: |
          test -f Dockerfile || (echo "Dockerfile missing" && exit 1)

      - name: Build and Push
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: docker.io/${{ secrets.DOCKER_USERNAME }}/${{ env.IMAGE_NAME }}:latest
```

重點：GitHub Actions 會知道要登入 Docker，完全是因為這份 yml 有 `Docker Login` 這段。

---

## 二、教學（逐步照做）

### 步驟 1：建立（或確認）目錄與檔案

```bash
cd /workspaces/test
mkdir -p frontend
test -f Dockerfile
test -f frontend/Dockerfile
```

目的：先確保 build context 存在，避免進 CI 才報錯。

### 步驟 2：建立 `.gitlab-ci.yml`

```bash
cd /workspaces/test
cat > .gitlab-ci.yml <<'YAML'
stages:
  - verify
  - build

variables:
  DOCKER_TLS_CERTDIR: ""
  BACKEND_IMAGE: "$DOCKER_USERNAME/bookkeeping-backend"
  FRONTEND_IMAGE: "$DOCKER_USERNAME/bookkeeping-frontend"

default:
  image: docker:27
  services:
    - docker:27-dind
  before_script:
    - echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin

verify_paths:
  stage: verify
  script:
    - test -f Dockerfile || (echo "Dockerfile missing" && exit 1)
    - test -d frontend || (echo "frontend directory missing" && exit 1)
    - test -f frontend/Dockerfile || (echo "frontend/Dockerfile missing" && exit 1)

build_backend:
  stage: build
  needs: ["verify_paths"]
  script:
    - docker build -t "$BACKEND_IMAGE:$CI_COMMIT_SHORT_SHA" .
    - docker push "$BACKEND_IMAGE:$CI_COMMIT_SHORT_SHA"

build_frontend:
  stage: build
  needs: ["verify_paths"]
  script:
    - docker build -t "$FRONTEND_IMAGE:$CI_COMMIT_SHORT_SHA" ./frontend
    - docker push "$FRONTEND_IMAGE:$CI_COMMIT_SHORT_SHA"
YAML
```

### 步驟 3：設定 GitLab CI/CD Variables

到 GitLab 專案頁面：

- `Settings -> CI/CD -> Variables`
- 新增 `DOCKER_USERNAME`
- 新增 `DOCKER_PASSWORD`（Docker Hub token）
- `DOCKER_PASSWORD` 建議設定 `Masked + Protected`

### 步驟 4：推送並觸發 pipeline

```bash
cd /workspaces/test
git add .gitlab-ci.yml
git commit -m "ci: add gitlab pipeline for backend and frontend"
git push origin main
```

### 步驟 5：驗證結果

在 GitLab 檢查 `CI/CD -> Pipelines`：

1. `verify_paths` 綠色
2. `build_backend` 綠色
3. `build_frontend` 綠色

再到 Docker Hub 檢查是否有新 tag（`<short_sha>` / `latest`）。

---

## 三、問題解決展示（檢修手冊）

### 問題 A：`open Dockerfile: no such file or directory`

原因：Runner checkout 的 commit 裡沒有 `Dockerfile`。

檢查：

```bash
git fetch origin
git ls-tree -r --name-only origin/main | grep '^Dockerfile$'
```

修正：

```bash
git add Dockerfile
git commit -m "fix: add missing Dockerfile"
git push origin main
```

### 問題 B：`path "./frontend" not found`

原因：`frontend` 目錄沒被推上去，或 `context` 寫錯。

檢查：

```bash
git fetch origin
git ls-tree -r --name-only origin/main | grep '^frontend/'
```

修正：

```bash
git add frontend
git commit -m "fix: add frontend build context"
git push origin main
```

### 問題 C：Docker 登入失敗

症狀：`denied: requested access to the resource is denied`

檢查：

1. `DOCKER_USERNAME` 是否正確
2. `DOCKER_PASSWORD` 是否為有效 token
3. token 是否有 push 權限

修正：更新 GitLab Variables 後重跑 pipeline。

### 問題 D：為什麼本機有檔案，CI 還是說找不到

核心原因：CI 看的是「觸發那次 commit」的快照，不是你目前工作目錄。

建議：

```bash
git status
git log --oneline -n 3
git push origin main
```

確保你要的檔案真的在已推送的 commit。

### 問題 E：怎麼預防這些錯誤再發生

1. 在 pipeline 最前面做 `verify_paths`
2. 使用 `rules:changes`，避免不必要 job
3. 每次改 CI 先看 `git status` 再 push
4. image 同時打 `sha` 與 `latest` 標籤

---

## 快速結論

你剛剛的理解是對的：

1. 有變更觸發 CI
2. CI 行為由 YAML 決定
3. runner 依 YAML 執行每一步
4. Secrets/Variables 提供認證

所以「為什麼明明沒檔案卻知道要 docker login」的答案是：

- 登入動作是你寫進 YAML 的
- 找不到檔案則是該次 commit 快照不完整

兩者同時成立，不衝突。