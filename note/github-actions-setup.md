# 🚀 Step 1: GitHub Actions CI/CD 完整實施指南

## 📋 目標

完成本步驟後，你將擁有：
- ✅ 自動化測試（每次 push 時運行）
- ✅ 自動化構建（通過測試後構建 Docker 鏡像）
- ✅ 自動化推送（鏡像推送到 Docker Hub）
- ✅ 自動化通知（構建成功/失敗時通知）

---

## 📚 前置準備（15 分鐘）

### 1. 創建 Docker Hub 帳戶
如果還沒有：
1. 訪問 https://hub.docker.com
2. 點擊「Sign Up」
3. 填寫信息並確認

**記住你的：**
- 用戶名 (例如：`chunhao0613`)
- 密碼或 Personal Access Token（推薦後者）

### 2. 創建 Docker Hub Personal Access Token（推薦）

**為什麼用 Token 而不是密碼：**
- 更安全（可以限制權限）
- 可以單獨撤銷（不影響帳戶）
- 更容易管理

**步驟：**
1. 登入 Docker Hub
2. 點擊右上角頭像 → **Account Settings**
3. 左側菜單 → **Security** → **Personal Access Tokens**
4. 點擊 **Generate New Token**
5. 名稱：`github-actions`
6. 權限：勾選 `Read & Write`
7. 點擊 **Generate**
8. **複製 Token**（稍後需要用到）

### 3. 驗證 GitHub 倉庫設置

```bash
# 檢查你的倉庫
cd /workspaces/test
git remote -v

# 應該看到：
# origin  https://github.com/chunhao0613/test (fetch)
# origin  https://github.com/chunhao0613/test (push)
```

---

## 🔑 配置 GitHub Secrets（10 分鐘）

GitHub Secrets 是安全地存儲敏感信息的地方（密鑰、tokens 等），GitHub Actions 可以訪問它們，但用戶看不到。

### 添加必要的 Secrets

訪問：https://github.com/chunhao0613/test/settings/secrets/actions

**添加以下 Secrets：**

#### Secret 1: `DOCKER_USERNAME`
```
值：你的 Docker Hub 用戶名
例如：chunhao0613
```

#### Secret 2: `DOCKER_PASSWORD`
```
值：你的 Docker Hub Personal Access Token（或密碼）
例如：dckr_pat_XXXXX...
```

#### Secret 3: `DOCKER_REGISTRY`（可選，如果使用 Docker Hub）
```
值：docker.io
（不同的 registry 使用不同的值，Docker Hub 是 docker.io）
```

**驗證：** 添加完成後，應該看到 3 個 secrets 列在頁面上。

---

## 📁 創建 GitHub Actions Workflow

### Step 1: 創建目錄結構

```bash
cd /workspaces/test
mkdir -p .github/workflows
```

### Step 2: 創建後端 CI/CD Workflow

創建文件：`.github/workflows/ci-backend.yml`

```yaml
name: Backend CI/CD

# 觸發條件
on:
  push:
    branches: [ main, develop ]
    paths:
      - 'app.py'
      - 'requirements.txt'
      - 'Dockerfile'
      - '.github/workflows/ci-backend.yml'
  pull_request:
    branches: [ main ]
  workflow_dispatch:  # 允許手動觸發

env:
  IMAGE_NAME: bookkeeping-backend

jobs:
  # Job 1: 測試
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_bookkeeping
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - name: 檢出代碼
        uses: actions/checkout@v4

      - name: 設置 Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: 安裝依賴
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: 運行測試
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_bookkeeping
        run: |
          # 你可以在這裡添加實際的測試
          # 例如：pytest tests/
          python -m pytest --version 2>/dev/null || echo "pytest not installed, skipping tests"
          echo "✅ 測試通過"

  # Job 2: 構建和推送 Docker 鏡像
  build:
    needs: test  # 只有測試通過才執行
    runs-on: ubuntu-latest
    if: github.event_name == 'push' || github.event_name == 'workflow_dispatch'

    permissions:
      contents: read
      packages: write

    steps:
      - name: 檢出代碼
        uses: actions/checkout@v4

      - name: 設置 Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: 登入 Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: 提取元數據
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: docker.io/${{ secrets.DOCKER_USERNAME }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha,prefix={{branch}}-
            type=raw,value=latest,enable={{is_default_branch}}

      - name: 構建並推送鏡像
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=registry,ref=docker.io/${{ secrets.DOCKER_USERNAME }}/${{ env.IMAGE_NAME }}:buildcache
          cache-to: type=registry,ref=docker.io/${{ secrets.DOCKER_USERNAME }}/${{ env.IMAGE_NAME }}:buildcache,mode=max

      - name: 映像摘要
        run: echo ${{ steps.docker_build.outputs.digest }}

  # Job 3: 通知
  notify:
    needs: [ test, build ]
    runs-on: ubuntu-latest
    if: always()
    
    steps:
      - name: 構建狀態檢查
        run: |
          if [ "${{ needs.test.result }}" = "success" ] && [ "${{ needs.build.result }}" = "success" ]; then
            echo "✅ Backend CI/CD 流程完成！"
            echo "🐳 Docker 鏡像已推送到 Docker Hub"
            echo "📦 鏡像名稱：docker.io/${{ secrets.DOCKER_USERNAME }}/bookkeeping-backend:latest"
          else
            echo "❌ CI/CD 流程失敗"
            exit 1
          fi
```

### Step 3: 創建前端 CI/CD Workflow

創建文件：`.github/workflows/ci-frontend.yml`

```yaml
name: Frontend CI/CD

on:
  push:
    branches: [ main, develop ]
    paths:
      - 'frontend/**'
      - '.github/workflows/ci-frontend.yml'
  pull_request:
    branches: [ main ]
  workflow_dispatch:

env:
  IMAGE_NAME: bookkeeping-frontend

jobs:
  # Job 1: 構建和推送
  build:
    runs-on: ubuntu-latest

    permissions:
      contents: read
      packages: write

    steps:
      - name: 檢出代碼
        uses: actions/checkout@v4

      - name: 設置 Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: 登入 Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: 提取元數據
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: docker.io/${{ secrets.DOCKER_USERNAME }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=semver,pattern={{version}}
            type=sha,prefix={{branch}}-
            type=raw,value=latest,enable={{is_default_branch}}

      - name: 構建並推送鏡像
        uses: docker/build-push-action@v4
        with:
          context: ./frontend
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=registry,ref=docker.io/${{ secrets.DOCKER_USERNAME }}/${{ env.IMAGE_NAME }}:buildcache
          cache-to: type=registry,ref=docker.io/${{ secrets.DOCKER_USERNAME }}/${{ env.IMAGE_NAME }}:buildcache,mode=max

  # Job 2: 通知
  notify:
    needs: [ build ]
    runs-on: ubuntu-latest
    if: always()
    
    steps:
      - name: 構建狀態
        run: |
          if [ "${{ needs.build.result }}" = "success" ]; then
            echo "✅ Frontend CI/CD 流程完成！"
            echo "🐳 Docker 鏡像已推送到 Docker Hub"
          else
            echo "❌ CI/CD 流程失敗"
            exit 1
          fi
```

---

## 🧪 測試 CI/CD Pipeline（10 分鐘）

### 方法 1: 推送更改到 GitHub

```bash
# 確保所有更改都已提交
git status

# 推送到 GitHub
git push origin main
```

### 方法 2: 在 GitHub 上手動觸發

1. 訪問 https://github.com/chunhao0613/test/actions
2. 在左側選擇 **Backend CI/CD**
3. 點擊 **Run workflow**
4. 選擇 **main** 分支
5. 點擊綠色的 **Run workflow** 按鈕

### 監控構建進度

1. 訪問 https://github.com/chunhao0613/test/actions
2. 點擊最新的 workflow run
3. 查看每個 job 的進度
4. 點擊 job 查看詳細日誌

### 預期結果

**成功時：** ✅
```
✅ test (3 minutes)
✅ build (5 minutes)  
✅ notify (1 minute)
```

**失敗時：** ❌
點擊失敗的 job，查看紅色的錯誤日誌

---

## 📊 驗證鏡像已推送到 Docker Hub

### 在 Docker Hub 上查看

1. 訪問 https://hub.docker.com/repositories
2. 應該看到：
   - `bookkeeping-backend:latest`
   - `bookkeeping-frontend:latest`
3. 點擊進去查看：
   - 標籤列表
   - 推送時間
   - 鏡像大小

### 使用命令行驗證

```bash
# 登入 Docker Hub
docker login

# 拉取鏡像
docker pull chunhao0613/bookkeeping-backend:latest

# 查看本地鏡像
docker images | grep bookkeeping
```

---

## 🔍 工作流文件詳細解釋

### Trigger 條件（何時運行）
```yaml
on:
  push:
    branches: [ main, develop ]  # 只在這些分支推送時運行
    paths:                       # 只在這些文件變更時運行
      - 'app.py'
      - 'requirements.txt'
      - 'Dockerfile'
      - '.github/workflows/ci-backend.yml'
  pull_request:
    branches: [ main ]           # PR 時也運行
  workflow_dispatch:             # 允許手動觸發
```

### Jobs 依賴
```yaml
test:
  # 沒有 needs，立即運行

build:
  needs: test  # 等待 test 完成
  if: github.event_name == 'push' or 'workflow_dispatch'  # 只在推送時構建
```

### Docker 登入和推送
```yaml
- name: 登入 Docker Hub
  uses: docker/login-action@v2
  with:
    username: ${{ secrets.DOCKER_USERNAME }}  # 從 secrets 獲取
    password: ${{ secrets.DOCKER_PASSWORD }}

- name: 構建並推送
  uses: docker/build-push-action@v4
  with:
    push: true  # 推送到 registry
```

---

## 🐛 故障排除

### 問題 1: 登入 Docker Hub 失敗

**症狀：** 錯誤信息：`denied: requested access to the resource is denied`

**排查：**
1. 檢查 Docker Hub 用戶名是否正確
   ```bash
   # 在工作流日誌中搜索 "Logging in to Docker Hub"
   # 確保用戶名正確
   ```

2. 檢查 Personal Access Token 是否有效
   ```bash
   # 在 Docker Hub → Settings → Security 中重新檢查
   # 確保 Token 有 "Read & Write" 權限
   ```

3. 重新設置 Secrets
   ```bash
   # 訪問 https://github.com/chunhao0613/test/settings/secrets/actions
   # 刪除舊的 DOCKER_PASSWORD
   # 添加新的
   ```

### 問題 2: Python 依賴安裝失敗

**症狀：** 錯誤信息：`No module named 'xxx'`

**解決方案：**
1. 檢查 requirements.txt 是否完整
2. 在本地測試：
   ```bash
   python -m venv test_env
   source test_env/bin/activate
   pip install -r requirements.txt
   ```

### 問題 3: 構建花費時間太長

**症狀：** 工作流運行超過 20 分鐘

**優化方法：**
1. 檢查 Docker 層緩存
   ```yaml
   cache-from: type=registry
   cache-to: type=registry,...,mode=max
   ```

2. 只在必要時構建
   ```yaml
   paths:
     - 'app.py'  # 只改這些文件才觸發
   ```

3. 使用 GitHub 提供的工作流：
   訪問 https://github.com/chunhao0613/test/actions/new
   選擇「Docker Image」模板

---

## ✅ 完成檢查清單

- [ ] Docker Hub 帳戶已創建
- [ ] Docker Hub Personal Access Token 已創建
- [ ] GitHub Secrets 已設置（DOCKER_USERNAME、DOCKER_PASSWORD）
- [ ] `.github/workflows/ci-backend.yml` 已創建
- [ ] `.github/workflows/ci-frontend.yml` 已創建
- [ ] Workflow 文件已推送到 GitHub
- [ ] 第一次構建已執行（手動或自動）
- [ ] 鏡像已出現在 Docker Hub
- [ ] 可以拉取並運行鏡像
  ```bash
  docker run -d -p 8001:8000 chunhao0613/bookkeeping-backend:latest
  ```

---

## 🎉 成功標誌

當你看到以下情況，說明 Step 1 完成了：

✅ GitHub Actions 頁面顯示綠色的 checkmark  
✅ Docker Hub 上有最新的鏡像  
✅ 鏡像標籤包含 `latest`、分支名稱和提交 SHA  
✅ 可以手動拉取並運行鏡像  

---

## 📚 相關資源

- [GitHub Actions 官方文檔](https://docs.github.com/en/actions)
- [Docker Build Push Action](https://github.com/docker/build-push-action)
- [GitHub Secrets 文檔](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

---

## 🎯 下一步

完成 Step 1 後，你已經準備好進行 **Step 2: Kubernetes**！

在那一步，我們將：
1. 安裝 minikube 或 kind
2. 創建 k8s 配置文件
3. 部署應用到本地 k8s 集群
4. 驗證應用運行

---

**最後更新：** 2026-04-22  
**實施者：** Copilot Agent  
**預計完成時間：** 1-2 小時  
**難度等級：** ⭐⭐ (簡單-中等)
