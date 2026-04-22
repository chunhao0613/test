# Skill：如何判斷該用哪個指令、哪個技術、哪段 code

## 1. 先講結論

不是純靠經驗，而是有一套可重複的判斷流程。

經驗只是讓你更快看懂現場；真正可複用的是下面這套方法：
1. 先辨認問題屬於哪一層。
2. 再找這一層的入口點。
3. 再找這一層的驗證指令。
4. 最後只改這一層該改的 code。

---

## 2. 先問自己四個問題

每次做功能、修 bug、部署或排障時，先問：

1. 現在是在做什麼？
- 新功能、修錯、部署、驗證、監控、還是事故處理。

2. 問題屬於哪一層？
- 前端、後端、資料庫、容器、Compose、K8s、監控、日誌、網路。

3. 這一層的啟動點是什麼？
- Python 常看 `app.py`、`main.py`、`uvicorn`。
- 前端常看 `index.html`、`nginx.conf`、`vite.config`、`package.json`。
- Compose 常看 `compose.yaml`。

4. 我怎麼驗證它真的成功？
- 用 curl、docker compose ps、docker logs、browser、healthcheck、metrics 查詢。

---

## 3. 一個實用流程：從問題到指令

### 3.1 先定位層級
- 如果是畫面沒出來，多半是 frontend / Nginx / browser 層。
- 如果是 API 回錯，多半是 backend / routes / auth / DB 層。
- 如果是容器起不來，多半是 Dockerfile / Compose / image 層。
- 如果是資料不見，多半是 volume / DB / migration 層。

### 3.2 找入口檔
- Python API：看 `app.py`、`Dockerfile`。
- 前端靜態站：看 `frontend/index.html`、`frontend/Dockerfile`、`frontend/nginx.conf`。
- 編排：看 `compose.yaml`。

### 3.3 找對的指令
- 要看設定是否正確：先跑 `docker compose config`。
- 要啟動整組服務：跑 `docker compose up -d --build`。
- 要看容器狀態：跑 `docker compose ps`。
- 要看錯誤原因：跑 `docker compose logs`。
- 要看 API 是否回應：跑 `curl`。

### 3.4 先驗證，再修正
- 不要一次改很多地方。
- 一次只改一層。
- 每次改完就跑最短驗證指令。

---

## 4. 怎麼知道該用哪個技術

不是看到新工具就學，而是先看它解決什麼問題。

### 4.1 技術選擇原則
1. 靜態頁面、反向代理、入口層
- 優先想到 Nginx。

2. API、業務邏輯、資料處理
- 優先想到 Python / FastAPI。

3. 資料持久化
- 優先想到資料庫與 volume。

4. 多服務編排
- 優先想到 Docker Compose。

5. 大量服務管理、彈性擴縮、滾動更新
- 再想到 Kubernetes。

6. 指標與告警
- 想到 Prometheus / Alertmanager。

7. 日誌與搜尋
- 想到 ELK / OpenSearch。

### 4.2 技術不是互相取代，而是分工
- Nginx 不取代 backend。
- Compose 不取代 Dockerfile。
- Prometheus 不取代 log。
- K8s 不取代觀測。

---

## 5. 怎麼知道該寫哪段 code

### 5.1 看責任
- 這段 code 是給誰用的？
- 它要解決什麼？
- 它應該留在哪一層？

### 5.2 看慣例
- FastAPI 路由通常放在 app 或 router。
- 靜態頁放在 HTML / JS / CSS。
- Nginx 規則放在 `nginx.conf`。
- Compose 資源放在 `compose.yaml`。

### 5.3 看現成模式
- 先找專案裡已經有的類似寫法。
- 改最接近的範例，而不是重寫一套。

### 5.4 看最小可驗證單位
- 一段 code 寫完後，能不能立即用最小指令驗證？
- 如果不能驗證，通常表示你還沒拆對責任邊界。

---

## 6. 指令選擇速查表

### 6.1 Docker / Compose
- `docker compose config`：先確認 YAML 和合成結果。
- `docker compose up -d --build`：建置並啟動。
- `docker compose ps`：看狀態。
- `docker compose logs -f`：看即時 log。
- `docker compose down`：清理。

### 6.2 Nginx / frontend
- `curl http://127.0.0.1:80`：測首頁。
- `docker build ...`：測 frontend image。

### 6.3 backend / API
- `curl http://127.0.0.1:8000/health`：測健康檢查。
- `curl http://127.0.0.1:8000/...`：測 API 路由。

### 6.4 DB
- `docker compose logs db`：看資料庫是否健康。
- `healthcheck`：檢查 DB 是否 ready。

---

## 7. 診斷實戰：怎麼看指令輸出

### 7.1 curl 輸出怎麼看

#### 7.1.1 最簡單的判斷：只看 HTTP 狀態碼

```bash
curl -i http://127.0.0.1:80
```

輸出會像這樣：
```
HTTP/1.1 200 OK
Server: nginx/1.27.5
Date: Wed, 22 Apr 2026 15:03:07 GMT
Content-Type: text/html; charset=utf-8
Content-Length: 11882
Connection: keep-alive

<!doctype html>
...
```

**第一行的 `HTTP/1.1 200 OK` 就是狀態碼，是最重要的訊息。**

#### 7.1.2 狀態碼分類

| 碼數 | 含義 | 常見原因 |
|------|------|----------|
| `200` | OK | 成功。頁面、API、JSON 都有回應。 |
| `201` | Created | 資源建立成功（通常是 POST）。 |
| `204` | No Content | 成功但沒有回應體（通常是 DELETE）。 |
| `400` | Bad Request | 你的請求格式錯誤（JSON 斷裂、欄位缺少）。 |
| `401` | Unauthorized | 沒登入、token 過期、或 token 假的。 |
| `403` | Forbidden | 有登入，但權限不足。 |
| `404` | Not Found | 網址不存在、或 API 路由寫錯。 |
| `405` | Method Not Allowed | 用了錯的 HTTP 方法（例如 GET 改 POST）。 |
| `422` | Unprocessable Entity | 資料型態或驗證規則不符。 |
| `500` | Internal Server Error | 後端 code crash，或資料庫連不上。 |
| `502` | Bad Gateway | Nginx 找不到後端、或後端容器沒起來。 |
| `503` | Service Unavailable | 依賴服務（DB、外部 API）暫時不可用。 |

#### 7.1.3 看回應體（body）的內容

```bash
curl -i http://127.0.0.1:8000/health
```

輸出：
```
HTTP/1.1 200 OK
date: Wed, 22 Apr 2026 15:03:10 GMT
server: uvicorn
content-length: 15
content-type: application/json

{"status":"ok"}
```

**如果 status code 是 200 但回應體是空的，或 JSON 格式怪，可能表示：**
- Content-Type 不符（期望 JSON 但回應是 HTML）。
- 頁面確實有內容，但 API 邏輯有問題。

#### 7.1.4 看錯誤時的回應

```bash
curl -i http://127.0.0.1:8000/auth/me
```

沒登入時輸出：
```
HTTP/1.1 401 Unauthorized
...
Content-Type: application/json

{"detail":"Not authenticated"}
```

**看 `detail` 欄位，就知道伺服器為什麼拒絕了。**

### 7.2 docker compose logs 怎麼看

#### 7.2.1 看所有服務的 log

```bash
docker compose logs -f
```

或只看某一個服務：
```bash
docker compose logs frontend
docker compose logs backend
docker compose logs db
```

#### 7.2.2 常見的 log 訊息

**Frontend (Nginx) 正常：**
```
frontend  | /docker-entrypoint.sh: Configuration complete; ready for start up
frontend  | 2026/04/22 15:03:07 [notice] 1#1: signal process started
```

**Frontend (Nginx) 有問題：**
```
frontend  | nginx: [emerg] host not found in upstream "backend" in /etc/nginx/conf.d/default.conf:13
```
→ 代表 backend 這個服務還沒起來，或 Compose 網路裡找不到它。

**Backend (Python) 正常：**
```
backend   | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
backend   | INFO:     Application startup complete
```

**Backend 有問題：**
```
backend   | ERROR:    [Errno 111] Connection refused
backend   | Traceback (most recent call last): ...
```
→ 代表後端 code crash，或連不上 DB。

**DB 正常：**
```
db  | ... database system is ready to accept connections
db  | ... database system is ready to accept connections
```

**DB 有問題：**
```
db  | FATAL: data directory "/var/lib/postgresql/data" has wrong ownership
```
→ 代表 volume 權限問題。

### 7.3 docker compose ps 怎麼看

```bash
docker compose ps
```

輸出：
```
NAME                   IMAGE           COMMAND                  SERVICE    STATUS                    PORTS
bookkeeping-backend    test-backend    "python app.py"          backend    Up 15 seconds             0.0.0.0:8000->8000/tcp
bookkeeping-db         postgres:16     "docker-entrypoint.s…"   db         Up 20 seconds (healthy)   5432/tcp
bookkeeping-frontend   test-frontend   "/docker-entrypoint.…"   frontend   Up 14 seconds             0.0.0.0:80->80/tcp
```

**要看的三個欄位：**

1. **STATUS**
   - `Up X seconds` → 正常，已啟動。
   - `Up X seconds (healthy)` → 正常，且通過 healthcheck。
   - `Exited (X)` → 容器已停止，括號內是 exit code。
   - `Restarting` → 容器在重新啟動（通常是 crash 後自動重啟）。

2. **PORTS**
   - `0.0.0.0:8000->8000/tcp` → 外部可以透過 `:8000` 連進去。
   - 如果沒有 PORTS，代表外界無法直接連。

3. **執行順序**
   - 看 STATUS 的「時間差」，就知道誰先起來的。

### 7.4 從一個完整的故障場景來判斷

**場景：你去打 `http://127.0.0.1` 卻沒有回應。**

**第一步：看 ps 輸出**
```bash
docker compose ps
```

如果 frontend 狀態是 `Exited (1)`，代表容器根本沒起來，去看 logs。

**第二步：看 frontend logs**
```bash
docker compose logs frontend
```

如果出現：
```
nginx: [emerg] host not found in upstream "backend"
```

代表問題不在 frontend 本身，而是 backend 還沒起來或網路不通。

**第三步：看 backend 狀態**
```bash
docker compose ps
```

檢查 backend 狀態。如果也是 `Exited`，看它的 logs。

如果 backend logs 裡有：
```
ERROR: Cannot connect to database
```

代表 DB 沒起來。去看 db logs 與 STATUS。

**第四步：檢查 compose 的依賴**
```bash
docker compose config | grep -A5 "depends_on"
```

確認 frontend 有沒有 depend 在 backend 身上、backend 有沒有 depend 在 db 身上。

**修復：加依賴或調整 healthcheck，再 `docker compose down && docker compose up -d`。**

### 7.5 判斷問題的決策樹

```
是不是網頁出不來？
├─ YES → 打 curl http://127.0.0.1:80 看狀態碼
│  ├─ 502 Bad Gateway → backend 沒起來，或連接逾時。
│  │                   check: docker compose logs frontend 找 "host not found"
│  ├─ 404 Not Found → 網址錯、或 Nginx location 設定錯。
│  │                  check: frontend/nginx.conf 有沒有這個路徑。
│  ├─ 超時沒回應 → 容器根本沒起來。
│  │              check: docker compose ps 看 frontend STATUS。
│  └─ 200 OK 但內容怪 → HTML 有問題。
│                       check: curl -i 看完整回應。
│
└─ 網頁出來了，但 API 有問題
   ├─ 401 Unauthorized → 沒登入或 token 過期。
   │                     check: 是否要先註冊 / 登入。
   ├─ 400 Bad Request → 你送的 JSON 格式錯。
   │                   check: curl -X POST -d 的 JSON 是否有效。
   ├─ 500 Internal Server Error → 後端 code crash。
   │                             check: docker compose logs backend 看完整 traceback。
   └─ 超時 → 後端掛起或資料庫掛。
             check: docker compose ps 看 backend、db 狀態。
```

---

## 8. 實戰例子

如果你要做 frontend container：
1. 問題層級是前端。
2. 啟動點是 `frontend/index.html`、`frontend/Dockerfile`、`frontend/nginx.conf`。
3. 技術是 Nginx。
4. 驗證指令是 `docker build`、`docker compose up -d --build`、`curl http://127.0.0.1:80`。

如果你要做 backend：
1. 問題層級是後端。
2. 啟動點是 `app.py`、`Dockerfile`。
3. 技術是 Python / FastAPI。
4. 驗證指令是 `docker build`、`curl http://127.0.0.1:8000`。

---

## 9. 錯誤代碼與診斷速查表

### 9.1 HTTP 狀態碼與原因對應

| 狀態碼 | 英文名 | 常見原因 | 怎麼除錯 |
|--------|--------|---------|----------|
| 200 | OK | 成功。 | 檢查回應體內容是否正確。 |
| 201 | Created | 資源建立成功。 | 通常是 POST 成功，看是否真的寫進 DB。 |
| 204 | No Content | 成功但無回應體。 | 通常是 DELETE / PATCH 成功。 |
| 400 | Bad Request | 送的資料格式或驗證不符。 | 用 `curl -X POST -d '{...}'` 檢查 JSON；或看 `detail` 欄位的說明。 |
| 401 | Unauthorized | 未認證（沒登入、token 無效）。 | 先打 `/auth/register` → `/auth/login`；檢查 cookie 是否有被送出。 |
| 403 | Forbidden | 已認證但無權限。 | 檢查當前用戶的角色與權限邏輯。 |
| 404 | Not Found | 路由不存在。 | 確認 API 網址、參數、方法（GET vs POST）。 |
| 405 | Method Not Allowed | 用了錯誤的 HTTP 方法。 | 檢查該路由是否真的支援你用的方法（GET、POST、PATCH、DELETE）。 |
| 422 | Unprocessable Entity | 資料驗證失敗（常見於 FastAPI）。 | 看 `detail` 陣列，逐個欄位檢查。 |
| 429 | Too Many Requests | 超過速率限制。 | 等待或檢查是否有寫 rate limiter。 |
| 500 | Internal Server Error | 伺服器 code crash。 | 看 `docker compose logs backend`，找 traceback。 |
| 502 | Bad Gateway | 反向代理無法連接後端。 | 檢查 backend 是否有起來、Nginx upstream 設定。 |
| 503 | Service Unavailable | 依賴服務暫時不可用（通常是 DB）。 | 看 `docker compose ps`、`docker compose logs db`。 |

### 9.2 容器常見 exit code

| Exit Code | 含義 | 常見原因 |
|-----------|------|----------|
| 0 | 正常退出 | 容器正常停止（通常是你 down 的）。 |
| 1 | 一般錯誤 | Code 有錯、或啟動命令失敗。 |
| 126 | 命令無法執行 | 檔案沒有執行權限。 |
| 127 | 命令找不到 | 啟動指令寫錯（例如找不到 python）。 |
| 137 | Killed（SIGKILL） | 容器被 kill，通常是記憶體超限。 |
| 139 | Segmentation fault | Code 有嚴重錯誤（很少見）。 |

### 9.3 Docker Compose 常見錯誤

| 現象 | 原因 | 解決方法 |
|------|------|----------|
| `docker compose up` 後容器馬上 `Exited (1)` | 啟動命令有錯，或有必要的環境變數缺失。 | 看 `docker compose logs` 找 traceback；檢查 `Dockerfile` 或 `compose.yaml` 的環境變數。 |
| `cannot find compose file` | 沒有 `compose.yaml`，或用了其他檔名。 | 確保在正確的目錄，檔案名是 `compose.yaml` 或用 `-f` 指定。 |
| `services.X depends_on services.Y condition: service_healthy` 但 Y 沒有 healthcheck | 無法判斷 Y 是否準備好。 | 給 Y 加 healthcheck，或改成 `condition: service_started`（風險較高）。 |
| `network test_default not found` | Compose 下的網路被刪掉了。 | 跑 `docker compose up -d` 會自動重建。 |
| `volume test_pgdata is in use` | 有容器還在用這個 volume。 | 跑 `docker compose down` 確保所有容器停掉。 |

### 9.4 常見錯誤的第一步診斷

```bash
# 最快速的六步診斷
1. docker compose ps           # 看所有容器狀態
2. docker compose logs -f      # 看即時 log
3. curl http://127.0.0.1:80    # 測前端
4. curl http://127.0.0.1:8000/health  # 測後端
5. docker compose config       # 驗證 YAML 是否有效
6. docker compose down && docker compose up -d --build  # 重來一次
```

---

## 10. 常見錯誤及排除邏輯

1. 一開始就選工具，不先看問題層級。
2. 改了 code 但沒有對應的驗證指令。
3. 把 frontend、backend、db 混在同一層處理。
4. 一次改太多，導致不知道錯在哪。
5. Reverse proxy 啟動時找不到 upstream，卻一直盯著 Nginx 設定，不去看服務啟動順序。

---

## 11. 服務啟動順序的判斷

有些問題不是 code 錯，而是「依賴服務還沒起來」。

### 11.1 什麼時候要想啟動順序
- frontend 需要 proxy_pass 到 backend。
- backend 需要連到 db。
- db 需要先完成健康檢查。

### 11.2 你要看什麼
1. Compose 的 `depends_on`。
2. 服務是否有 healthcheck。
3. `docker compose ps` 看的不是只有有沒有容器，而是健康狀態和啟動先後。

### 11.3 一個實際規則
- 如果你看到 `host not found in upstream`，先看依賴服務是否已在網路裡。
- 如果你看到資料庫連不上，先看 db 是否 healthy。
- 如果你看到 API 401 / 403，再看認證邏輯，不要先改部署。

---

## 12. 最後的心法

你不是靠背命令在做事，而是靠這個順序：
1. 先分類問題。
2. 再找入口檔。
3. 再選合適技術。
4. 再選最短驗證指令。
5. 最後只改必要 code。

這樣做久了，經驗會長出來；但一開始也能用這套流程穩定做事。