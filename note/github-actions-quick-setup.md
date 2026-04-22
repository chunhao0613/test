# 🔑 Step 1 快速設置：GitHub Secrets 配置

## ⚠️ 重要：必須立即完成此步驟

GitHub Actions workflow 已推送，但在 Secrets 配置完成前，構建會失敗。

---

## 📋 檢查清單

### 1️⃣ 前往 GitHub Repository Settings

```
訪問：https://github.com/chunhao0613/test/settings/secrets/actions
```

或按以下步驟：
1. 訪問 https://github.com/chunhao0613/test
2. 點擊 **Settings**（設置）
3. 左側菜單 → **Secrets and variables**
4. 選擇 **Actions**

---

### 2️⃣ 添加 Docker Hub Secrets

#### Secret 1: `DOCKER_USERNAME`

| 字段 | 值 |
|------|-----|
| **Name** | `DOCKER_USERNAME` |
| **Secret** | 你的 Docker Hub 用戶名 |
| **例如** | `chunhao0613` |

**步驟：**
1. 點擊 **New repository secret**
2. Name：輸入 `DOCKER_USERNAME`
3. Secret：輸入你的 Docker Hub 用戶名
4. 點擊 **Add secret**

---

#### Secret 2: `DOCKER_PASSWORD`

| 字段 | 值 |
|------|-----|
| **Name** | `DOCKER_PASSWORD` |
| **Secret** | Docker Hub Personal Access Token |
| **重要** | 使用 Token，不要用密碼 |

**如果還沒有 Personal Access Token：**

1. 訪問 https://hub.docker.com/settings/security
2. 點擊 **Personal Access Tokens** → **Generate New Token**
3. 名稱：`github-actions`
4. 權限：勾選 ✅ `Read & Write`
5. 點擊 **Generate**
6. **複製 Token**（只會顯示一次！）

**添加 Secret：**
1. 點擊 **New repository secret**
2. Name：輸入 `DOCKER_PASSWORD`
3. Secret：粘貼你的 Personal Access Token
4. 點擊 **Add secret**

---

## ✅ 驗證 Secrets 已設置

訪問 https://github.com/chunhao0613/test/settings/secrets/actions

應該看到：

```
✅ DOCKER_USERNAME  (Updated X minutes ago)
✅ DOCKER_PASSWORD  (Updated X minutes ago)
```

---

## 🚀 現在測試 CI/CD Pipeline

### 方法 1: 自動觸發（推薦）

在你的終端機運行：

```bash
cd /workspaces/test

# 進行一個小改動
echo "# GitHub Actions Test" >> README.md

# 提交和推送
git add README.md
git commit -m "test: trigger GitHub Actions"
git push origin main
```

然後訪問：https://github.com/chunhao0613/test/actions

應該看到新的 workflow run 正在執行。

### 方法 2: 手動觸發

1. 訪問 https://github.com/chunhao0613/test/actions
2. 選擇 **Backend CI/CD** 或 **Frontend CI/CD**
3. 點擊 **Run workflow**
4. 選擇 **main** 分支
5. 點擊綠色的 **Run workflow**

---

## 📊 監控構建進度

### 實時查看

1. 訪問 https://github.com/chunhao0613/test/actions
2. 點擊最新的 workflow run（應該看到黃色的執行中圖標）
3. 每個 job 的進度會實時更新

### 預期的執行時間

| 階段 | 時間 |
|------|------|
| 檢出代碼 | 10 秒 |
| 設置 Docker | 20 秒 |
| 登入 Docker Hub | 5 秒 |
| 構建鏡像 | 2-5 分鐘（第一次較長） |
| 推送鏡像 | 1-2 分鐘 |
| 完成 | 1 秒 |
| **總計** | **3-8 分鐘** |

---

## ✅ 成功標誌

當構建成功時，你會看到：

```
✅ build
  ├─ 📥 檢出代碼
  ├─ 🔧 設置 Docker Buildx
  ├─ 🔐 登入 Docker Hub
  ├─ 📊 提取元數據
  ├─ 🐳 構建並推送鏡像
  └─ ✅ 完成
     Output: ✅ Backend 構建成功！
             🐳 鏡像名稱：docker.io/chunhao0613/bookkeeping-backend:latest
```

---

## 🔍 常見問題排除

### ❌ 問題 1: 登入失敗

**錯誤信息：**
```
Error response from daemon: Get "https://registry-1.docker.io/v2/": denied: requested access to the resource is denied
```

**原因：** Docker Hub 用戶名或 Token 錯誤

**解決方案：**
1. 檢查 DOCKER_USERNAME 是否正確
2. 重新生成 Personal Access Token（可能過期）
3. 確保 Token 有 "Read & Write" 權限
4. 更新 GitHub Secrets

### ❌ 問題 2: 構建失敗

**檢查步驟：**
1. 點擊 workflow run
2. 查看紅色的失敗步驟
3. 閱讀錯誤信息
4. 常見原因：
   - Dockerfile 有語法錯誤
   - 依賴包安裝失敗
   - 端口或配置衝突

**解決方案：**
在本地測試 Dockerfile：
```bash
docker build -t test-backend .
docker run -it test-backend
```

### ❌ 問題 3: 推送後沒有觸發 workflow

**檢查：**
1. 文件是否確實改變了（檢查 `paths` 配置）
2. Workflow 文件語法是否正確
3. 推送是否是到 `main` 分支

**快速測試：**
```bash
git push origin main
# 等待 30 秒
# 訪問 https://github.com/chunhao0613/test/actions
```

---

## 🎯 驗證鏡像已推送到 Docker Hub

### 在 Web 上驗證

1. 訪問 https://hub.docker.com/repositories
2. 應該看到：
   ```
   bookkeeping-backend:latest
   bookkeeping-frontend:latest
   (如果兩個都成功推送)
   ```
3. 點擊進去查看標籤、推送時間、大小等

### 使用命令行驗證

```bash
# 登入 Docker Hub
docker login

# 拉取並運行鏡像
docker pull chunhao0613/bookkeeping-backend:latest
docker run -d -p 8001:8000 chunhao0613/bookkeeping-backend:latest
curl http://127.0.0.1:8001/health
```

---

## 📋 下一步

### 立即完成
- [ ] 添加 DOCKER_USERNAME secret
- [ ] 添加 DOCKER_PASSWORD secret
- [ ] 觸發第一次構建（推送或手動）
- [ ] 驗證鏡像出現在 Docker Hub

### 本週完成
- [ ] 在團隊中分享 GitHub Actions 設置
- [ ] 添加單元測試（Step 1 進階）
- [ ] 設置分支保護規則

### 下週完成
- [ ] 進行 Step 2: Kubernetes
- [ ] 創建 k8s 部署配置

---

## 📞 快速參考

| 任務 | URL |
|------|-----|
| 查看 Actions | https://github.com/chunhao0613/test/actions |
| 設置 Secrets | https://github.com/chunhao0613/test/settings/secrets/actions |
| Docker Hub | https://hub.docker.com/repositories |
| 查看 Workflow 文件 | https://github.com/chunhao0613/test/blob/main/.github/workflows/ |

---

## 🎉 成功檢查清單

- [ ] 2 個 Secrets 已添加
- [ ] GitHub Actions 頁面顯示綠色 ✅
- [ ] Docker Hub 上有新鏡像
- [ ] 可以拉取並運行鏡像
- [ ] Step 1 完成！

---

**最後更新：** 2026-04-22  
**預計完成時間：** 15 分鐘（設置 Secrets） + 8 分鐘（首次構建）  
**總計：** ~30 分鐘完成 Step 1
