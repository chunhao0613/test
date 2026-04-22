# 簡單記帳專案規劃

## 目標
建立一個刻意保持簡單的全端記帳系統，讓重點放在學習 Docker、Docker Compose、Kubernetes、Helm 與基本 SRE 實作，而不是複雜的商業功能。

## 建議技術棧
- 前端：React + Vite
- 後端：FastAPI
- 資料庫：PostgreSQL
- 驗證：JWT 搭配 httpOnly cookie
- 部署：Docker、Docker Compose、Kubernetes、Helm
- CI/CD：GitLab CI、Jenkins
- 監控：Prometheus
- 日誌：ELK
- 事件應變：incident-response

## 功能範圍
### 必做
- 使用者註冊
- 使用者登入 / 登出
- 收入與支出記錄 CRUD
- 簡單月報與總覽
- 健康檢查 endpoint

### 暫不做
- 多帳戶 / 多人協作
- 銀行串接
- 付款流程
- 排程任務
- 快取、訊息佇列、微服務拆分

## 系統設計
### 前端
前端只負責畫面與 API 呼叫，維持薄薄一層。

建議頁面：
- 登入 / 註冊頁
- 記帳清單頁
- 新增 / 編輯表單
- 月總覽儀表板

### 後端
後端是整個系統的商業邏輯中心。

建議 API：
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/logout`
- `GET /health`
- `GET /transactions`
- `POST /transactions`
- `PATCH /transactions/{id}`
- `DELETE /transactions/{id}`
- `GET /summary/monthly`

### 資料庫
保持 schema 最小化。

建議資料表：
- `users`
- `transactions`
- 視需要加 `categories`

## SRE 練習點
這個專案的核心價值是拿來練部署與維運，因此第一版就應該保留這些面向：
- Docker image 建置
- Docker Compose 本機整合啟動
- Kubernetes Deployment / Service / Ingress
- Helm chart 打包與參數化
- GitLab CI 與 Jenkins pipeline 實作
- readiness / liveness probe
- 環境變數注入
- Secret 與 ConfigMap 管理
- 資料庫 migration 流程
- 結構化 log
- Prometheus metrics 與告警
- ELK 集中式日誌收集與查詢
- 資源 requests / limits
- incident-response 流程設計與故障演練，例如 DB 掛掉、設定錯誤、rollout 回滾

## 可觀測性與應變
這一塊重點不是做大型平台，而是把最小可用的監控、日誌與應變流程補齊，讓專案可以真的拿來演練。

### 監控
- 服務健康與延遲指標
- API 請求量、錯誤率、回應時間
- 資料庫連線與資源使用狀況

### 日誌
- JSON 結構化 log
- 請求追蹤欄位與錯誤上下文
- 透過 ELK 集中查詢與分析

### 事件應變
- 告警觸發後的排查步驟
- DB 異常、設定錯誤、容器重啟與回滾流程
- 事件記錄與事後檢討模板

## 推薦實作順序
1. 先做後端 API 與資料庫 schema。
2. 再做前端最小畫面。
3. 接著補 Docker 與 Compose。
4. 再包成 Kubernetes 與 Helm。
5. 補 GitLab CI 或 Jenkins 的自動化流程。
6. 接著加入 Prometheus、ELK 與基本告警。
7. 最後補測試、健康檢查與 incident-response 文件。

## 初版資料模型
### users
- id
- email
- password_hash
- created_at

### transactions
- id
- user_id
- type: income / expense
- amount
- category
- note
- happened_at
- created_at

## 初版驗證項目
- 本機可用 Docker Compose 一鍵啟動
- 註冊與登入可正常運作
- 收支資料可新增、查詢、修改、刪除
- 月總覽可正確顯示
- GitLab CI 或 Jenkins pipeline 可成功執行
- Prometheus 可抓到基本 metrics
- ELK 可查到結構化日誌
- Helm template 與 lint 可通過
- K8s 部署後 probes 可正常運作
- 可完成至少一次 incident-response 故障演練

## 建議原則
- 先做單體，不拆微服務
- 先把部署、設定、健康檢查做好，再考慮加功能
- UI 保持簡單，避免把時間花在非 SRE 核心項目
- 所有額外功能都應該以「是否有助於練習部署與維運」來判斷是否加入
