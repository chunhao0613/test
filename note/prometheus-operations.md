# Prometheus 操作記錄

## 日期：2026-04-22

### 系統狀態驗證

#### 容器狀態
```
NAME                     STATUS                   PORTS
bookkeeping-backend      Up 31 seconds            0.0.0.0:8000->8000/tcp
bookkeeping-db           Up 2 minutes (healthy)   5432/tcp
bookkeeping-frontend     Up 2 minutes             0.0.0.0:80->80/tcp
bookkeeping-prometheus   Up 2 minutes             0.0.0.0:9090->9090/tcp
```
✅ 所有 4 個容器都在正常運行

---

## 驗證步驟

### 1️⃣ 測試後端 `/metrics` 端點

**命令：**
```bash
curl -s http://127.0.0.1:8000/metrics | head -30
```

**結果：** ✅ 指標端點返回有效的 Prometheus 格式數據

**觀察：**
- 返回 Python 默認指標（gc、進程信息等）
- HTTP 請求指標已正確暴露

---

### 2️⃣ 驗證自定義指標

**命令：**
```bash
curl -s http://127.0.0.1:8000/metrics | grep http_requests
```

**結果：** ✅ 自定義指標存在且包含數據

**指標數據：**
```
# 請求計數器
http_requests_total{endpoint="/metrics",method="GET",status="200"} 4.0
http_requests_total{endpoint="/",method="GET",status="200"} 1.0
http_requests_total{endpoint="/auth/me",method="GET",status="401"} 1.0

# 請求創建時間
http_requests_created{endpoint="/metrics",method="GET",status="200"} 1.7768710762433217e+09
```

**分析：**
- 自動中間件正在攔截並記錄所有請求
- 標籤包含：方法（GET）、端點路徑、狀態碼（200、401）
- /metrics 被調用了多次（來自 Prometheus 抓取）

---

### 3️⃣ 驗證 Prometheus 目標健康狀態

**命令：**
```bash
curl -s http://127.0.0.1:9090/api/v1/targets | python3 -m json.tool
```

**結果：** ✅ Backend 目標健康且活躍

**目標詳情：**
```json
{
  "health": "up",
  "scrapeUrl": "http://backend:8000/metrics",
  "lastScrape": "2026-04-22T15:18:56.174637657Z",
  "lastScrapeDuration": 0.007535831,
  "scrapeInterval": "15s",
  "scrapeTimeout": "10s"
}
```

**驗證點：**
- ✅ Backend 目標狀態：UP（綠色）
- ✅ 最後抓取成功
- ✅ 抓取耗時僅 7.5ms
- ✅ 抓取間隔：15 秒

---

### 4️⃣ 測試 PromQL 查詢

**查詢命令：**
```bash
curl -s 'http://127.0.0.1:9090/api/v1/query?query=http_requests_total'
```

**查詢結果：** ✅ 返回 3 個時間序列

**返回數據示例：**
```
{
  "endpoint": "/metrics",
  "method": "GET",
  "status": "200",
  "value": 7  # 已調用 7 次
}
{
  "endpoint": "/",
  "method": "GET",
  "status": "200",
  "value": 1  # 已調用 1 次
}
{
  "endpoint": "/auth/me",
  "method": "GET",
  "status": "401",
  "value": 1  # 已調用 1 次
}
```

**分析：**
- PromQL 查詢正常工作
- 指標標籤完整且正確
- 時間序列聚合正確

---

## Prometheus UI 訪問

**URL：** `http://127.0.0.1:9090`

**在 UI 中可以：**
1. 查看 Targets 頁面：所有目標狀態
2. Graph 頁面：執行 PromQL 查詢並可視化
3. 嘗試的查詢示例：
   - `http_requests_total` - 查看總請求計數
   - `http_requests_total{status="200"}` - 只查看成功請求
   - `http_requests_total{endpoint="/metrics"}` - 只查看 /metrics 端點

---

## 整合狀態總結

| 組件 | 狀態 | 備註 |
|------|------|------|
| Backend App | ✅ 運行中 | 正常暴露 `/metrics` 端點 |
| Prometheus 伺服器 | ✅ 運行中 | 正在抓取後端指標 |
| Docker Network | ✅ 正常 | 容器間通信正常（backend:8000） |
| 指標收集 | ✅ 工作中 | 自動中間件正在記錄所有請求 |
| PromQL 查詢 | ✅ 功能正常 | 可以查詢和聚合指標 |

---

## 核心概念回顧

### 指標流程：
```
FastAPI 應用
  ↓
中間件攔截請求
  ↓
更新 Counter/Histogram
  ↓
/metrics 端點暴露指標
  ↓
Prometheus 每 15s 抓取一次
  ↓
存儲在時間序列數據庫
  ↓
PromQL 查詢和可視化
```

### 為什麼這個設計好：
1. **自動化**：無需修改業務邏輯，中間件自動記錄所有請求
2. **標準化**：使用 prometheus-client 庫的標準格式
3. **可觀測性**：完整的標籤集合（方法、端點、狀態碼）
4. **低開銷**：抓取耗時僅 7.5ms
5. **可拓展**：可以輕鬆添加更多自定義指標

---

## 下一步可以做什麼

### 短期
- [ ] 生成更多流量來觀察實時指標變化
- [ ] 在 Prometheus UI 中嘗試更複雜的 PromQL 查詢
- [ ] 添加業務指標（如交易數量、用戶登入次數）

### 中期
- [ ] 設置告警規則（例如：錯誤率超過 5%）
- [ ] 集成 Grafana 進行更好的可視化
- [ ] 監控應用性能指標（p99 延遲等）

### 長期
- [ ] 設置日誌聚合（ELK Stack）
- [ ] 實現分佈式追蹤（Jaeger）
- [ ] 建立完整的可觀測性平台

---

## 故障排除

如果 Backend 無法啟動（Duplicated timeseries 錯誤）：

**原因：** 指標被多次定義

**解決方案：** 在 app.py 中使用 try/except：
```python
try:
    request_count = Counter(...)
except ValueError:
    request_count = REGISTRY._names_to_collectors['http_requests_total']
```

這允許應用在 reload 時不會因為重複註冊而失敗。

---

**最後驗證時間：** 2026-04-22 15:18 UTC
**驗證者：** Copilot Agent
**驗證結果：** ✅ 所有系統正常運行
