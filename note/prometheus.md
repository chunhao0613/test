# Prometheus 與指標監控

## 1. Prometheus 是什麼

Prometheus 是一個時間序列資料庫（Time Series Database），用來收集、儲存、查詢系統與應用的**指標**（metrics）。

### 1.1 核心概念

- **指標（Metric）**：一個測量值，例如 API 請求數、CPU 使用率、響應時間。
- **時間序列（Time Series）**：同一指標在不同時刻的值。例如 `http_requests_total{method="GET"} = 100 at 10:00, 105 at 10:01`。
- **標籤（Label）**：指標的維度，用來區分不同的情況。例如 `method="GET"` 或 `status="200"`。
- **抓取（Scrape）**：Prometheus 定期到應用暴露的 endpoint 去拉取指標。
- **暴露端點（Expose Endpoint）**：應用提供指標的 HTTP endpoint，通常是 `/metrics`。

### 1.2 為什麼要用 Prometheus

你可以：
1. 看到應用的實時狀態。
2. 問出像「過去 5 分鐘內有多少個 API 請求？」的問題。
3. 設定告警（Alertmanager），當指標超過閾值時提醒。
4. 追蹤效能，找瓶頸。

---

## 2. Prometheus 的運作流程

```
應用 (暴露指標)
  ↓ 
Prometheus (定期抓取)
  ↓
TSDB (儲存時間序列)
  ↓
查詢 & 告警 & 可視化
```

### 2.1 實際流程

1. **應用端**：FastAPI 暴露一個 `/metrics` endpoint，返回所有指標。
2. **Prometheus 端**：每 15 秒抓取一次 `/metrics`。
3. **儲存**：Prometheus 把指標按時間戳存進 TSDB。
4. **查詢**：用 Prometheus 的查詢語言 PromQL 查詢。例如：
   ```
   rate(http_requests_total[5m])  # 過去 5 分鐘的請求速率
   ```

---

## 3. 怎麼讓 FastAPI 暴露指標

### 3.1 用 prometheus-client 庫

```python
from prometheus_client import Counter, Histogram, generate_latest

# 定義指標
request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])

# 在中間件裡記錄
# 每次 API 被呼叫時，就更新指標

# 暴露 /metrics endpoint
@app.get("/metrics")
def metrics():
    return generate_latest()
```

### 3.2 什麼指標要記錄

常見的有：
- `http_requests_total`：總請求數（計數器，只增不減）。
- `http_request_duration_seconds`：請求耗時（直方圖，看分佈）。
- `http_requests_in_progress`：正在進行的請求（量規，會上下浮動）。
- `db_connections`：資料庫連線數。
- `errors_total`：錯誤總數。

---

## 4. Prometheus 的配置與部署

### 4.1 prometheus.yml 的結構

```yaml
global:
  scrape_interval: 15s      # 每 15 秒抓取一次
  evaluation_interval: 15s  # 每 15 秒評估一次告警規則

scrape_configs:
  - job_name: 'backend'
    static_configs:
      - targets: ['http://backend:8000']  # 抓取後端的 /metrics
    metrics_path: '/metrics'              # 指標在這個路徑
    scrape_interval: 15s
```

### 4.2 怎麼用 Compose 啟動 Prometheus

加入 compose.yaml：
```yaml
prometheus:
  image: prom/prometheus:latest
  container_name: bookkeeping-prometheus
  ports:
    - "9090:9090"  # 外界可以透過 http://127.0.0.1:9090 訪問
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
    - prometheus_data:/prometheus
  command:
    - '--config.file=/etc/prometheus/prometheus.yml'
    - '--storage.tsdb.path=/prometheus'
  depends_on:
    - backend

volumes:
  prometheus_data:
```

---

## 5. 實際操作步驟

### 5.1 裝 prometheus-client 到後端

```bash
pip install prometheus-client
# 或加進 requirements.txt
```

### 5.2 在 app.py 裡加中間件與 /metrics endpoint

見 [app.py](../app.py) 的修改部分。

### 5.3 建立 prometheus.yml

見 [prometheus.yml](../prometheus.yml)。

### 5.4 改 compose.yaml 加入 prometheus 服務

見 [compose.yaml](../compose.yaml) 的修改部分。

### 5.5 啟動整個堆棧

```bash
docker compose down && docker compose up -d --build
```

### 5.6 打開 Prometheus UI

```
http://127.0.0.1:9090
```

### 5.7 檢查 targets 頁面

- 看 backend 是否正常被抓取。
- 如果是 DOWN，check docker logs。

### 5.8 測試查詢

在 Prometheus UI 的 Graph 頁面，輸入：
```
http_requests_total
```

或者查詢速率：
```
rate(http_requests_total[1m])
```

---

## 6. 常見錯誤與除錯

### 6.1 targets 頁面顯示 DOWN

**原因**：Prometheus 無法連到後端。

**檢查**：
1. 後端容器是否有起來：`docker compose ps`。
2. 後端是否暴露了 /metrics：`curl http://127.0.0.1:8000/metrics`。
3. Prometheus 是否能看到 backend：`docker compose logs prometheus`。

### 6.2 /metrics 回應 404

**原因**：後端沒有加 /metrics endpoint。

**修復**：在 app.py 加 `@app.get("/metrics")` 路由。

### 6.3 Prometheus 容器馬上 Exited

**原因**：prometheus.yml 有語法錯誤。

**檢查**：`docker compose logs prometheus`。

### 6.4 看到指標但都是 0

**原因**：還沒有流量。先跑幾個 API 請求。

---

## 7. PromQL 查詢範例

### 7.1 基礎查詢

```
http_requests_total              # 整個指標的所有時間序列
http_requests_total{method="GET"}  # 只看 GET 請求
```

### 7.2 聚合與速率

```
sum(http_requests_total)         # 總請求數
rate(http_requests_total[5m])    # 過去 5 分鐘的速率（請求/秒）
increase(http_requests_total[1h])  # 過去 1 小時的增量
```

### 7.3 直方圖查詢

```
http_request_duration_seconds_bucket{le="0.1"}  # 看 100ms 以內的請求
```

---

## 8. 告警（Alertmanager）初步

告警規則定義在 prometheus.yml 裡，例如：
```yaml
alert:
  - name: HighErrorRate
    expr: rate(errors_total[5m]) > 0.05  # 如果 5 分鐘內錯誤率 > 5%
    for: 5m  # 持續 5 分鐘才觸發
    annotations:
      summary: "Error rate is high"
```

詳細設定留到後面。

---

## 9. 學習心得與操作記錄

### 啟動 Prometheus 堆棧

執行：
```bash
docker compose down && docker compose up -d --build
```

預期結果：
- backend 啟動並暴露 /metrics。
- prometheus 每 15 秒抓取一次後端的指標。
- 可在 http://127.0.0.1:9090 訪問 Prometheus UI。

### 測試指標抓取

步驟：
1. 打幾個 API 呼叫產生流量。
2. 進 Prometheus，查詢 `http_requests_total`。
3. 看是否能看到請求計數。

### 下一步

- 設定 Grafana 畫儀表板。
- 加入告警規則。
- 監控 DB 連線數。
