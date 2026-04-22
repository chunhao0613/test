# 🎯 Bookkeeping 應用 - 完整技術棧學習路徑

## 現狀分析

### 已完成 ✅
- ✅ Docker Compose 本地開發環境
- ✅ Prometheus 監控系統
- ✅ 基礎應用（FastAPI + PostgreSQL + Nginx）

### 待實現 📋
- ⏳ GitHub Actions (CI/CD)
- ⏳ Kubernetes (容器編排)
- ⏳ Helm (k8s 包管理)
- ⏳ Jenkins (企業級 CI/CD，可選)
- ⏳ ELK (日誌聚合)

---

## 📚 推薦學習順序與依賴關係

```
週期 1 - 基礎 CI/CD
├─ Step 1️⃣ : GitHub Actions CI/CD
│   └─ 目標：自動化測試、構建、推送鏡像
│   └─ 時間：3-4 小時
│   └─ 成果：GitHub 上有完整的 CI/CD Pipeline
│
週期 2 - 容器編排
├─ Step 2️⃣ : Kubernetes (k8s) 基礎
│   └─ 前置：完成 GitHub CI
│   └─ 目標：將應用遷移到 k8s 集群
│   └─ 時間：6-8 小時
│   └─ 成果：應用在本地 k8s (minikube/kind) 上運行
│
├─ Step 3️⃣ : Helm 包管理
│   └─ 前置：完成 k8s 基礎
│   └─ 目標：創建 Helm charts 簡化部署
│   └─ 時間：3-4 小時
│   └─ 成果：一條命令部署整個應用堆棧
│
週期 3 - 企業級工具
├─ Step 4️⃣ : Jenkins (可選)
│   └─ 目標：建立自己的 CI/CD 伺服器
│   └─ 時間：4-5 小時
│   └─ 成果：Jenkins 上有完整的 Pipeline
│
├─ Step 5️⃣ : ELK 日誌堆棧
│   └─ 前置：完成 k8s（ELK 運行在 k8s 中）
│   └─ 目標：集中收集和分析所有日誌
│   └─ 時間：4-5 小時
│   └─ 成果：完整的可觀測性堆棧
```

---

## 🔄 技術依賴與流程圖

### 數據流與組件關係

```
┌─────────────────┐
│  開發人員       │  push code
└────────┬────────┘
         │
         ↓
┌─────────────────────────────────────────┐
│     GitHub Actions (Step 1)             │
│  ├─ Run Tests                           │
│  ├─ Build Docker Image                  │
│  └─ Push to Docker Registry             │
└────────┬────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────┐
│     Kubernetes Cluster (Step 2)         │
│  ├─ minikube / kind (開發環境)          │
│  ├─ 應用 Pod (FastAPI)                  │
│  ├─ 數據庫 Pod (PostgreSQL)             │
│  ├─ Prometheus Pod                      │
│  └─ ELK Stack (Step 5)                  │
└────────┬────────────────────────────────┘
         │
    ┌────┴────┐
    │          │
    ↓          ↓
Helm      Jenkins
(Step 3)  (Step 4)
```

---

## 📖 詳細學習路徑

### Step 1️⃣ : GitHub Actions CI/CD (優先度：🔴 最高)

**為什麼先做：**
- 無依賴，立即開始
- 建立自動化基礎，之後的步驟都需要它
- 快速看到成果（3-4 小時）

**學習內容：**
```
• GitHub Actions 基礎
  ├─ Workflow 文件結構 (.github/workflows/)
  ├─ 觸發事件 (push, pull_request, schedule)
  ├─ Jobs 和 Steps 的概念
  └─ Secrets 管理 (Docker Hub 認證)

• 構建實際 Pipeline
  ├─ 運行單元測試
  ├─ 構建 Docker 鏡像
  ├─ 推送到 Docker Hub
  └─ 通知結果

• 實施內容
  ├─ 為 backend 創建 CI workflow
  ├─ 為 frontend 創建 CI workflow  
  └─ 設置環境變數和 secrets
```

**預期成果：**
- Push code 時自動運行測試
- 通過測試後自動構建 Docker 鏡像
- 鏡像自動推送到 Docker Hub
- 失敗時通知開發者

**時間估計：** 3-4 小時  
**難度：** ⭐⭐ (簡單-中等)

---

### Step 2️⃣ : Kubernetes 基礎 (優先度：🟠 高)

**前置條件：**
- ✅ Docker 知識（你已有）
- ✅ GitHub Actions 工作中（Step 1 完成）

**為什麼在 Step 2：**
- 建立在 Docker 之上，是編排基礎
- ELK 需要在 k8s 上部署（Step 5 依賴）
- 掌握 k8s 是現代應用部署的必備

**學習內容：**
```
• 本地 k8s 環境
  ├─ 選擇：minikube 或 kind
  ├─ 安裝和基本操作
  └─ 儀表板訪問

• k8s 核心概念
  ├─ Pod（最小單位）
  ├─ Deployment（應用部署）
  ├─ Service（網路暴露）
  ├─ ConfigMap & Secrets（配置）
  ├─ PersistentVolume（持久化）
  └─ Namespaces（隔離）

• 遷移應用到 k8s
  ├─ 編寫 Deployment YAML
  ├─ 編寫 Service YAML
  ├─ 編寫 StatefulSet (PostgreSQL)
  ├─ 設置環境變數和密鑰
  └─ 驗證應用運行
```

**預期成果：**
- 應用在本地 k8s 集群上運行
- 所有 4 個容器（backend、frontend、db、prometheus）都在 k8s 上
- 理解 k8s 的基本工作原理

**時間估計：** 6-8 小時  
**難度：** ⭐⭐⭐ (中等)

---

### Step 3️⃣ : Helm 包管理 (優先度：🟠 高)

**前置條件：**
- ✅ k8s 基礎（Step 2 完成）

**為什麼在 Step 3：**
- 建立在 k8s 之上
- 簡化複雜的 k8s 部署
- 實現「一鍵部署」

**學習內容：**
```
• Helm 基礎
  ├─ Helm vs 手寫 YAML
  ├─ Chart 結構
  ├─ Values 文件和模板
  └─ Package 和 Release

• 創建自己的 Helm Chart
  ├─ 設計 Chart 結構
  ├─ 編寫 templates/
  │   ├─ Deployment.yaml
  │   ├─ Service.yaml
  │   ├─ ConfigMap.yaml
  │   └─ Secret.yaml
  ├─ 編寫 values.yaml
  └─ 編寫 Chart.yaml

• Helm 操作
  ├─ helm install
  ├─ helm upgrade
  ├─ helm rollback
  └─ helm delete
```

**預期成果：**
- 創建完整的 Helm Chart
- 一條命令：`helm install bookkeeping .`
- 簡化應用部署和管理

**時間估計：** 3-4 小時  
**難度：** ⭐⭐ (簡單-中等)

---

### Step 4️⃣ : Jenkins (可選) (優先度：🟡 中-低)

**前置條件：**
- ✅ GitHub Actions 基礎（Step 1 完成）
- ✅ k8s 或 Docker（任一即可）

**為什麼可選：**
- GitHub Actions 已經提供 CI/CD
- Jenkins 適合「自建服務器」場景
- 可以跳過或最後再做

**學習內容（如果選擇做）：**
```
• Jenkins 安裝與配置
  ├─ Docker 或 k8s 上部署
  ├─ 基本配置（安全、插件）
  └─ 與 GitHub 集成

• Jenkins Pipeline
  ├─ 聲明式 Pipeline
  ├─ 腳本式 Pipeline
  └─ 與 k8s 集成（動態 Agents）

• 遷移 GitHub Actions → Jenkins
  ├─ 複製相同的構建邏輯
  ├─ 設置自動觸發
  └─ 配置通知
```

**預期成果：**
- 自己的 Jenkins 伺服器
- 完整的 Pipeline 配置
- 備選的 CI/CD 方案

**時間估計：** 4-5 小時  
**難度：** ⭐⭐⭐ (中等)

---

### Step 5️⃣ : ELK 日誌堆棧 (優先度：🟠 高)

**前置條件：**
- ✅ k8s 基礎（Step 2 完成）
- ✅ Prometheus 知識（你已有）

**為什麼在 Step 5：**
- 依賴 k8s 作為部署基礎
- 完善可觀測性（已有 Prometheus 指標）
- 企業級應用的必備

**學習內容：**
```
• ELK Stack 概念
  ├─ Elasticsearch - 日誌存儲和搜索
  ├─ Logstash - 日誌收集和處理
  └─ Kibana - 日誌查詢和可視化

• 在 k8s 上部署 ELK
  ├─ 部署 Elasticsearch 集群
  ├─ 部署 Logstash
  ├─ 部署 Kibana
  └─ 配置持久化存儲

• 應用日誌集成
  ├─ FastAPI 應用輸出結構化日誌
  ├─ Nginx 日誌轉發
  ├─ PostgreSQL 日誌轉發
  └─ 在 Kibana 中查詢和分析

• Kibana 使用
  ├─ Index Pattern 配置
  ├─ 構建 Dashboard
  ├─ 日誌搜索和過濾
  └─ 設置告警
```

**預期成果：**
- ELK 運行在 k8s 上
- 應用所有日誌集中管理
- 完整的可觀測性堆棧（指標 + 日誌）

**時間估計：** 4-5 小時  
**難度：** ⭐⭐⭐⭐ (中等偏難)

---

## 📊 學習時間表總結

| Step | 技術 | 時間 | 難度 | 依賴 | 優先度 |
|------|------|------|------|------|--------|
| 1 | GitHub Actions | 3-4h | ⭐⭐ | 無 | 🔴 最高 |
| 2 | Kubernetes | 6-8h | ⭐⭐⭐ | Step 1 | 🟠 高 |
| 3 | Helm | 3-4h | ⭐⭐ | Step 2 | 🟠 高 |
| 4 | Jenkins | 4-5h | ⭐⭐⭐ | Step 1 | 🟡 可選 |
| 5 | ELK | 4-5h | ⭐⭐⭐⭐ | Step 2 | 🟠 高 |

**總計：** 20-26 小時（如果跳過 Jenkins：16-21 小時）

---

## 🚀 立即開始：Step 1 - GitHub Actions

### 為什麼從 GitHub Actions 開始
1. ✅ 無依賴 - 可以立即開始
2. ✅ 快速勝利 - 3-4 小時看到成果
3. ✅ 基礎設施 - 為後續步驟奠定基礎
4. ✅ GitHub 集成 - 天然與你的代碼庫整合

### 預期成果（完成 Step 1 後）
```
當你 push code 到 GitHub 時：
  ↓
自動運行測試
  ↓
自動構建 Docker 鏡像
  ↓
自動推送到 Docker Hub
  ↓
(未來) 自動部署到 k8s
```

### 準備工作
- [ ] GitHub 帳戶（你已有）
- [ ] Docker Hub 帳戶（用於推送鏡像）
- [ ] GitHub Personal Access Token（用於認證）

---

## 📝 下一個文檔

**當前位置：** 學習路徑規劃  
**下一個文檔：** `github-actions-setup.md` - Step 1 的詳細實施指南

---

**最後更新：** 2026-04-22  
**規劃者：** Copilot Agent  
**下一步行動：** 開始 GitHub Actions 設置
