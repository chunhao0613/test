# Docker Compose 課程紀錄

## 1. 為何要拆服務（每份一個 container）

將前端、後端、資料庫拆成不同 container，不只是技術潔癖，而是為了可維運性：

1. 職責分離
前端只負責 UI，後端只負責 API，資料庫只負責資料持久化。

2. 可獨立擴縮
高流量時通常先擴 API，不一定要同時擴 DB 或前端。

3. 故障隔離
某個服務失效時，不會整包一起倒。

4. 安全邊界清楚
DB 不暴露到公網，API 才是對外入口。

5. 部署可演進
本機用 Compose，進階可平滑遷移到 Kubernetes。

---

## 2. 這個專案的拆分策略

目前程式是單一 app 且預設使用 SQLite。為了做出「多 container」的真實場景，建議分兩階段：

### 階段 A（先完成，最重要）
拆成 2 份：
1. backend container：FastAPI 應用
2. db container：PostgreSQL

### 階段 B（進階）
拆成 3 份：
1. frontend container：Nginx 靜態頁（或你自己的前端）
2. backend container：FastAPI API
3. db container：PostgreSQL

註：你目前 app.py 內含 HTML UI，屬於「前後端同服務」型態。先完成階段 A，再做真正前後端拆分最穩。

---

## 3. 下一步實作（由你動手，我負責帶）

你要自己建立與修改以下檔案：
1. Dockerfile（backend 映像）
2. compose.yaml（服務編排）
3. .env（環境變數）

我不直接替你完成，改成「你做一步，我幫你檢查一步」。

---

## 4. 實作任務清單（階段 A：2 containers）

### 任務 A1：準備 backend Dockerfile
目標：確保 backend 可在容器內啟動。

你要確認 Dockerfile 啟動命令為：
- 以 0.0.0.0:8000 對外監聽
- 使用 uvicorn 啟動 app:app

參考命令：
python -m uvicorn app:app --host 0.0.0.0 --port 8000

### 任務 A2：建立 compose.yaml
目標：一次啟動 backend + postgres。

你需要定義至少兩個服務：
1. db
- image: postgres:16
- 設定 POSTGRES_DB、POSTGRES_USER、POSTGRES_PASSWORD
- 使用 volume 保存資料
- 建立 healthcheck

2. backend
- build: .
- depends_on: db（建議使用 service_healthy）
- environment 設定 DATABASE_URL 指向 db 服務
- ports 對映 8000:8000

DATABASE_URL 範例：
postgresql+psycopg2://bookkeeper:bookkeeper@db:5432/bookkeeping

### 任務 A3：啟動與驗證
目標：確認兩服務可正常運作。

建議驗證順序：
1. docker compose up -d --build
2. docker compose ps
3. docker compose logs -f db
4. docker compose logs -f backend
5. curl http://127.0.0.1:8000

---

## 5. 你實作時的提交格式（請照這個回我）

每完成一步，貼上：
1. 你修改的檔案內容（或重點片段）
2. 你執行的命令
3. 命令輸出（成功或錯誤都要）

我會回你：
1. 是否通過
2. 若失敗，最小修正建議（只改必要行）
3. 下一步指令

---

## 6. 常見坑位（先避雷）

1. backend 只監聽 127.0.0.1
會導致容器外無法連線，必須改成 0.0.0.0。

2. DATABASE_URL 還是 sqlite
Compose 下要切成 PostgreSQL 連線字串。

3. depends_on 只保證啟動順序，不保證 DB 已可連線
加 healthcheck 才能降低啟動競態問題。

4. DB 資料沒做 volume
容器重建後資料會消失。

---

## 7. 下一章銜接（你完成 A 後）

完成階段 A 後，我會帶你做階段 B：
1. 將前端從 app.py 拆出
2. 前端改呼叫 backend API
3. Compose 擴展成 frontend + backend + db（3 containers）

到這裡你就會真正達成「拆成 n 份，每份一個 container」的設計能力。

---

## 8. 進度紀錄：A1 已通過

你已完成：
1. Dockerfile 啟動命令改為 uvicorn。
2. 映像建置成功（bookkeeping-app:compose-a1）。
3. 容器啟動成功，curl 回傳首頁 HTML。

結論：A1 驗收通過，可進入 A2。

---

## 9. A2 手把手教學（你實作，我驗收）

### 9.1 你要建立的檔案
在專案根目錄新增 compose.yaml。

### 9.2 你要自己輸入的內容骨架
請你照著下列結構自己打進 compose.yaml：

1. `services.db`
- image 使用 postgres:16
- container_name 可先命名為 bookkeeping-db
- environment 放 3 個變數：
	- POSTGRES_DB=bookkeeping
	- POSTGRES_USER=bookkeeper
	- POSTGRES_PASSWORD=bookkeeper
- volumes 掛一個 named volume（例如 pgdata）到 /var/lib/postgresql/data
- healthcheck 使用 pg_isready（目標使用者 bookkeeper，資料庫 bookkeeping）

2. `services.backend`
- build 指向目前目錄
- container_name 可先命名為 bookkeeping-backend
- depends_on 設定 db 需健康（service_healthy）
- environment 至少放：
	- DATABASE_URL=postgresql+psycopg2://bookkeeper:bookkeeper@db:5432/bookkeeping
	- SECRET_KEY=change-me-in-compose
- ports 對映 8000:8000

3. `volumes`
- 宣告 pgdata

### 9.3 你要執行的命令順序
1. docker compose config
2. docker compose up -d --build
3. docker compose ps
4. docker compose logs --tail=80 db
5. docker compose logs --tail=80 backend
6. curl http://127.0.0.1:8000

### 9.4 我驗收時會看什麼
1. db 狀態是否 healthy。
2. backend 是否連到 PostgreSQL（不是 SQLite）。
3. 首頁是否可正常回應。

### 9.5 你回傳格式（固定）
1. compose.yaml 全文。
2. 上面 6 個命令的輸出。
3. 若失敗，貼第一個錯誤訊息即可。

---

## 10. YAML 層級教學：組件與關係要怎麼看

你卡住的點很關鍵：Compose 不是在背語法，而是在描述「資源圖」。

可先把 compose.yaml 想成三層：

1. 專案層（最外層）
- 這層放「共用資源定義」與總配置。
- 常見鍵：services、volumes、networks、secrets、configs。

2. 服務層（services.<service_name>）
- 每個服務就是一個容器規格。
- 例如 db、backend。

3. 服務內屬性層
- 每個服務的 image/build、environment、ports、depends_on、healthcheck、volumes 等。

### 10.1 為什麼 volumes 要放在 services 外面

因為 top-level volumes 是「命名資源宣告」，不是某個服務自己的欄位。

關係是：
1. 先在最外層宣告 volume 名稱（例如 pgdata）。
2. 再由某個服務去掛載它（例如 db 服務把 pgdata 掛到 /var/lib/postgresql/data）。

如果把 volumes 宣告塞進 services 底下，Compose 會把它當成「一個服務名稱」，就會出現你之前看到的驗證錯誤。

### 10.2 你的檔案對照解讀

以你現在的 compose 結構來看：

1. services.db
- image: postgres:16（資料庫容器）
- environment（建立 DB 所需帳密）
- healthcheck（確認 DB 真的可用）
- volumes: pgdata:/var/lib/postgresql/data（把資料放到命名 volume）

2. services.backend
- build: .（用目前專案 Dockerfile 建映像）
- environment.DATABASE_URL（改連 db 服務，不用 sqlite）
- depends_on.db.condition: service_healthy（等 DB 健康再啟動）
- ports: 8000:8000（把 API 對外）

3. top-level volumes
- pgdata:（宣告命名 volume）
- 這是專案級資源，不屬於某一個服務。

### 10.3 層級速記口訣

1. 先看最外層：有哪些資源（services/volumes/networks）。
2. 再看 services：有哪些容器（db/backend）。
3. 再看每個容器：如何建、連誰、存哪、開哪些 port。

### 10.4 最常見層級錯誤

1. 把 top-level volumes 寫到 services 裡。
2. 把 depends_on 寫成陣列卻塞 condition。
3. environment 混用格式造成縮排看不懂。

建議初學一律用 mapping 寫法，可讀性最好：

```yaml
environment:
	POSTGRES_USER: bookkeeper
	POSTGRES_PASSWORD: bookkeeper
```

---

## 11. 進度紀錄：A2 已通過

你已完成：
1. docker compose config 可解析（僅剩 version obsolete 警告）。
2. docker compose up -d --build 成功。
3. db 狀態 healthy，backend 已啟動。
4. curl http://127.0.0.1:8000 可回應 HTML。

結論：A2 驗收通過。

### 11.1 小優化（下一次可做）
Compose v2 已不需要 version 欄位，建議移除 `version` 以消除警告並避免混淆。

### 11.2 已完成的整理
你目前的 [compose.yaml](compose.yaml) 已改成不含 `version` 的 v2 寫法，後續直接以 `services`、`volumes`、`networks` 這些 top-level key 為主。

---

## 12. 下一步：把前端從 app.py 拆出去

你現在的專案還是「前端 + 後端同一支程式」的狀態。

目前 app.py 內大致包含兩種角色：
1. 後端 API
- 登入、註冊、交易、新增刪改查、summary 等路由

2. 前端頁面
- render_page() 回傳的 HTML + CSS + JavaScript

### 12.1 為什麼要拆
- 前端與後端更新節奏不同
- 前端可用 Nginx 靜態部署
- 後端可專心處理 API 與資料庫
- 拆開後，Compose 就更接近真實環境

### 12.2 拆分後的目標結構
你最後會得到 3 個 container：
1. frontend
- 只放靜態頁面或前端 build 產物

2. backend
- 只放 FastAPI 與 API 邏輯

3. db
- 只放 PostgreSQL 與資料持久化

### 12.3 你接下來要學會辨認的第一件事
先把 app.py 裡的 render_page() 視為「前端」，把其餘路由視為「後端」。

這樣你就會知道下一步不是亂拆，而是：
1. 把 HTML/JS/CSS 移出去
2. 前端透過 HTTP 呼叫 backend
3. Compose 再把 frontend、backend、db 串起來

### 12.4 這次我已幫你做了什麼
- 把首頁內容抽到 [frontend/index.html](frontend/index.html)
- 讓 [app.py](app.py) 只負責讀取前端檔案並提供 API
- 你接下來只要專心做 SRE 相關內容，不需要再手改前端頁面

### 12.5 驗證結果
你現在可以直接用 GET 方式打開首頁，前端內容會從 [frontend/index.html](frontend/index.html) 載入；`curl -I` 會回 405 是正常的，因為這個路由只定義了 GET。

---

## 13. 目前 compose 完整度（最新紀錄）

以「階段 A（backend + db）」目標來看，現在是完整可用：
1. `docker compose config` 可解析。
2. `docker compose up -d --build` 可啟動。
3. `db` 為 healthy，`backend` 為 up。
4. `curl http://127.0.0.1:8000` 可回首頁 HTML。

補充：
- 若你用 `curl -I` 對 `/`，回 405 是正常（HEAD 未定義）。
- 先前看到的 exit code 56 是連線時序或請求型態造成，不代表 compose 結構錯誤。

---

## 14. 最後一步：frontend container 實作指南（3 containers 完整版）

目標：把前端改成獨立容器，最終服務為 `frontend + backend + db`。

### 14.1 你要新增的檔案
1. [frontend/Dockerfile](frontend/Dockerfile)
2. [frontend/nginx.conf](frontend/nginx.conf)

### 14.2 frontend/Dockerfile 內容

```dockerfile
FROM nginx:1.27-alpine

COPY frontend/index.html /usr/share/nginx/html/index.html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
```

### 14.3 frontend/nginx.conf 內容

```nginx
server {
	listen 80;
	server_name _;

	root /usr/share/nginx/html;
	index index.html;

	location / {
		try_files $uri @api;
	}

	location @api {
		proxy_pass http://backend:8000;
		proxy_set_header Host $host;
		proxy_set_header X-Real-IP $remote_addr;
		proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
		proxy_set_header X-Forwarded-Proto $scheme;
	}
}
```

說明：
1. 前端頁面與靜態檔由 Nginx 提供。
2. `/auth/*`、`/transactions*`、`/summary/*` 等 API 會被 proxy 到 `backend:8000`。
3. 這樣前端程式不用改 API base URL，仍可用相對路徑呼叫。

### 14.4 compose.yaml 要調整的地方
1. 新增 `frontend` 服務：
- `build` 指向專案根目錄（讓 Dockerfile 可複製 frontend 檔案）
- `dockerfile` 指向 `frontend/Dockerfile`
- `ports` 設為 `8080:80`
- `depends_on` backend

2. `backend` 服務建議移除對外 `ports`，改用：
- `expose: ["8000"]`

3. 保留 `db` 與 `pgdata` 設定不變。

### 14.5 驗證命令
1. `docker compose down`
2. `docker compose up -d --build`
3. `docker compose ps`
4. `curl http://127.0.0.1:8080`
5. `docker compose logs --tail=80 frontend`
6. `docker compose logs --tail=80 backend`

完成條件：
1. `frontend`、`backend`、`db` 三個服務都為 Up。
2. 開 `http://127.0.0.1:8080` 可使用登入與交易功能。

---

## 15. 名詞白話解釋（你剛問的字典）

1. frontend container
- 裝前端靜態頁（HTML/CSS/JS）的容器。

2. backend container
- 跑 API 與商業邏輯的容器。

3. db container
- 跑資料庫（例如 PostgreSQL）的容器。

4. image
- 容器模板，像安裝包。

5. container
- image 執行後的實例，像正在跑的程式。

6. volume
- 容器外的持久化儲存空間，容器重建資料不會消失。

7. network（compose default network）
- 讓服務可用服務名互相連線，例如 `backend` 連 `db`。

8. service（compose service）
- compose.yaml 裡的一個服務定義，通常對應一組容器規格。

9. reverse proxy
- 前面接請求，再轉送到後端服務（這裡是 Nginx -> backend）。

10. healthcheck
- 自動健康檢查，判斷服務是否真的可用。
