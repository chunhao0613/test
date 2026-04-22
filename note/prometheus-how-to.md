# 🚀 Prometheus 操作指南

## 快速開始

### 1. 訪問 Prometheus UI
```bash
# 打開瀏覽器
http://127.0.0.1:9090
```

### 2. 檢查系統狀態
```bash
# 查看所有容器
docker compose ps

# 檢查後端日誌
docker compose logs backend

# 查看 Prometheus 日誌
docker compose logs prometheus
```

### 3. 測試指標收集
```bash
# 查看原始指標
curl http://127.0.0.1:8000/metrics

# 只看自定義指標
curl http://127.0.0.1:8000/metrics | grep http_requests

# 查詢 Prometheus
curl 'http://127.0.0.1:9090/api/v1/query?query=http_requests_total'
```

---

## UI 操作教程

### Targets 頁面（目標狀態）
1. 點擊上方 **Status** → **Targets**
2. 查看 "backend" 任務
3. 應該看到綠色 "UP" 指示

### Graph 頁面（查詢和可視化）
1. 點擊上方 **Graph**
2. 在搜索框中輸入指標名稱
3. 按 **Execute** 按鈕

**常用查詢：**
```promql
# 查看所有請求計數
http_requests_total

# 只看成功的請求
http_requests_total{status="200"}

# 只看 /metrics 端點
http_requests_total{endpoint="/metrics"}

# 計算請求速率（每分鐘）
rate(http_requests_total[1m])

# 查看請求延遲分佈
histogram_quantile(0.95, http_request_duration_seconds_bucket)
```

---

## 生成流量進行測試

### 方法 1：手動操作
```bash
# 訪問前端
http://127.0.0.1

# 操作：
# 1. 點擊「註冊」按鈕
# 2. 輸入郵箱和密碼
# 3. 登入
# 4. 創建一些交易記錄
# 5. 返回 Prometheus 查看指標更新
```

### 方法 2：使用 curl 腳本
```bash
#!/bin/bash
# 快速生成 100 個請求

for i in {1..100}; do
  curl -s http://127.0.0.1/health > /dev/null
  curl -s http://127.0.0.1/metrics > /dev/null
done

echo "✅ 生成了 100 個請求，檢查 Prometheus 查看數據"
```

---

## 指標解釋

### 1. `http_requests_total` - 請求計數器
**類型：** Counter（只能增加）
**標籤：**
- `method` - HTTP 方法（GET、POST 等）
- `endpoint` - 請求路徑（/auth/login、/transactions 等）
- `status` - 響應狀態碼（200、401、404 等）

**用途：** 統計特定時期內的總請求數

**示例：**
```
http_requests_total{endpoint="/auth/login",method="POST",status="200"} 42
```
表示：有 42 個成功的登入請求

---

### 2. `http_request_duration_seconds` - 請求延遲直方圖
**類型：** Histogram（測量值分佈）
**內容：**
- `_bucket` - 延遲分佈（0.005s, 0.01s, 0.025s... 等）
- `_count` - 請求總數
- `_sum` - 所有延遲的總和

**用途：** 分析應用性能

**示例查詢：**
```promql
# 計算平均響應時間
rate(http_request_duration_seconds_sum[1m]) / rate(http_request_duration_seconds_count[1m])

# 計算 P99 延遲（99% 的請求在此時間內完成）
histogram_quantile(0.99, http_request_duration_seconds_bucket)
```

---

## 常見操作

### 查看錯誤率
```promql
# 所有錯誤請求（4xx 和 5xx）
http_requests_total{status=~"4..|5.."}

# 計算錯誤率百分比
100 * (sum(rate(http_requests_total{status=~"4..|5.."}[5m])) / sum(rate(http_requests_total[5m])))
```

### 監控特定端點
```promql
# /auth/login 的請求速率
rate(http_requests_total{endpoint="/auth/login"}[1m])

# /auth/login 的失敗次數
http_requests_total{endpoint="/auth/login",status=~"4..|5.."}
```

### 追蹤特定用戶操作
```promql
# 所有 POST 請求（創建/修改操作）
http_requests_total{method="POST"}

# DELETE 請求數量
http_requests_total{method="DELETE"}
```

---

## 故障排除

### 問題 1：Prometheus 顯示 "no targets"
**症狀：** Targets 頁面為空或顯示 "DOWN"

**排查步驟：**
1. 檢查 backend 是否運行：
   ```bash
   docker compose ps
   ```
2. 檢查 prometheus.yml 配置：
   ```bash
   cat prometheus.yml
   ```
3. 驗證 /metrics 端點：
   ```bash
   curl http://127.0.0.1:8000/metrics
   ```
4. 檢查 Docker 網路連接：
   ```bash
   docker compose exec prometheus ping backend
   ```

### 問題 2：/metrics 返回 404
**症狀：** 訪問 http://127.0.0.1:8000/metrics 出現 404 錯誤

**解決方案：**
1. 確認 app.py 中有 /metrics 路由
2. 重啟後端容器：
   ```bash
   docker compose restart backend
   ```

### 問題 3：Prometheus 空白查詢結果
**症狀：** PromQL 查詢執行但沒有返回數據

**排查步驟：**
1. 檢查時間範圍（數據必須在時間範圍內）
2. 確認指標名稱拼寫正確
3. 等待足夠的數據積累（至少一個抓取週期）
4. 生成一些請求流量：
   ```bash
   curl http://127.0.0.1/health -s > /dev/null
   ```

---

## 架構回顧

### 數據流
```
┌─────────────┐
│  FastAPI    │  自動計數所有請求
│   應用      │  (中間件)
└──────┬──────┘
       │ GET /metrics
       ↓
┌─────────────────────┐
│  Prometheus-client  │  格式化為 Prometheus 文本格式
│   庫導出指標        │
└──────┬──────────────┘
       │ http://backend:8000/metrics
       ↓
┌──────────────┐
│  Prometheus  │  每 15 秒抓取一次
│   伺服器    │
└──────┬───────┘
       │
       ↓
┌──────────────┐
│  時間序列    │  PromQL 查詢
│  數據庫      │  和可視化
└──────────────┘
```

### 關鍵配置文件
- **prometheus.yml** - Prometheus 伺服器配置
  - 定義抓取間隔（15 秒）
  - 指定目標（backend:8000）
  - 設置指標路徑（/metrics）

- **app.py** - FastAPI 應用
  - 導入 prometheus-client
  - 定義 Counter 和 Histogram
  - 添加中間件攔截請求
  - 暴露 /metrics 端點

- **compose.yaml** - Docker Compose
  - Prometheus 服務定義
  - 端口映射（9090）
  - 持久化存儲（prometheus_data 卷）

---

## 下一步學習路線

### 現在你知道的
✅ Prometheus 如何收集指標  
✅ 如何在 FastAPI 中暴露指標  
✅ 如何查詢和可視化數據  

### 建議的學習順序

1. **立即**
   - 在 UI 中嘗試各種 PromQL 查詢
   - 觀察實時指標變化

2. **本週**
   - 添加應用特定的業務指標
   - 設置基本的告警規則

3. **本月**
   - 集成 Grafana 進行更好的儀表板
   - 學習時間序列數據的最佳實踐

---

## 快速參考表

| 任務 | 命令 |
|------|------|
| 查看所有指標 | `curl http://127.0.0.1:8000/metrics` |
| 檢查 Prometheus 健康狀態 | `curl http://127.0.0.1:9090/-/healthy` |
| 重啟 Prometheus | `docker compose restart prometheus` |
| 查看 Prometheus 日誌 | `docker compose logs -f prometheus` |
| 測試查詢 | `curl 'http://127.0.0.1:9090/api/v1/query?query=<metric>'` |
| 訪問 UI | 瀏覽器：http://127.0.0.1:9090 |

---

**最後更新：** 2026-04-22  
**涵蓋內容：** 基礎操作、故障排除、PromQL 查詢示例
