# Nginx 課程紀錄

## 1. 先講結論

Nginx 這一章的目標，不是學一個新工具而已，而是把你的前端從後端拆開，讓它變成獨立 container。

你現在的系統可以理解成：
1. frontend container：負責把 HTML / CSS / JavaScript 提供給瀏覽器。
2. backend container：負責 API、認證、資料處理。
3. db container：負責資料持久化。

Nginx 在這裡的角色，是前端 container 裡的 Web Server / Reverse Proxy。

---

## 2. Nginx 是什麼

Nginx 是一個高效能 Web Server，也可以當 Reverse Proxy 使用。

### 2.1 Web Server
它可以直接提供靜態檔案，例如：
- `index.html`
- CSS
- JavaScript
- 圖片

### 2.2 Reverse Proxy
它可以把某些請求轉發給別的服務，例如：
- `/auth/*` 轉給 backend
- `/transactions/*` 轉給 backend
- `/summary/*` 轉給 backend

### 2.3 為什麼前端常常用 Nginx
因為前端本質上常常就是靜態檔案，Nginx 很適合：
- 啟動快
- 映像檔小
- 設定簡單
- 很適合放在 container 裡

---

## 3. 為什麼要從 0 開始做一個新的 frontend container

你原本的 backend container 是用 Python image 做的，重點是執行 FastAPI。

但 frontend container 的工作不是跑 Python，而是：
1. 提供靜態頁面
2. 把 API 請求轉發到 backend

所以 frontend container 最合理的做法，是直接用 `nginx` 當 base image，再把前端檔案與 Nginx 設定放進去。

這樣做的好處：
- 前端與後端可以獨立更新
- 前端改版不需要重建 Python 環境
- backend 出問題時，前端容器不會一起壞
- 之後上 K8s 時，拆分邏輯更清楚

---

## 4. 從 0 開始要準備哪些檔案

你最少需要這三個部分：

1. `frontend/index.html`
- 前端主頁面

2. `frontend/Dockerfile`
- 告訴 Docker 怎麼做 frontend image

3. `frontend/nginx.conf`
- 告訴 Nginx 怎麼服務靜態檔、怎麼轉發 API

---

## 5. frontend container 的 Dockerfile

一個最基本的 frontend Dockerfile 可以長這樣：

```dockerfile
FROM nginx:1.27-alpine

COPY frontend/index.html /usr/share/nginx/html/index.html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
```

### 5.1 每一行在做什麼

1. `FROM nginx:1.27-alpine`
- 用 Nginx 官方精簡映像當基底。

2. `COPY frontend/index.html ...`
- 把你的首頁放進 Nginx 預設網站目錄。

3. `COPY frontend/nginx.conf ...`
- 把自訂的 Nginx 設定放進去。

4. `EXPOSE 80`
- 宣告這個 container 預期會對外提供 80 port。

### 5.2 為什麼這裡通常不需要 `CMD`
因為 Nginx 官方 image 本來就有預設啟動命令，會自動啟動 Nginx。

所以前端 Dockerfile 和後端 Dockerfile 的差異，不是只有 `CMD`，而是整個設計思維都不同。

---

## 6. nginx.conf 是什麼

`nginx.conf` 是 Nginx 的行為設定檔。

你可以把它想成：
- 哪些路徑直接回靜態檔
- 哪些路徑要轉發到 backend
- 服務 listen 哪個 port

一個適合你專案的範例：

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

### 6.1 這段設定的意思

1. `listen 80`
- Nginx 聽 80 port。

2. `root /usr/share/nginx/html`
- 靜態檔放的目錄。

3. `index index.html`
- 預設首頁是 `index.html`。

4. `location /`
- 所有一般請求先看靜態檔是否存在。

5. `try_files $uri @api`
- 如果找不到靜態檔，就丟給 `@api`。

6. `proxy_pass http://backend:8000`
- 把請求轉給 compose 網路裡名叫 `backend` 的服務。

---

## 7. 前後端 Dockerfile 只差在 CMD 嗎

不是。

差異其實很多，`CMD` 只是最表面的差異之一。

### 7.1 後端 Dockerfile 的重點
後端 Dockerfile 通常會做：
- 選 Python base image
- 安裝 Python 套件
- 複製 app 程式碼
- 用 `uvicorn` 啟動 API

### 7.2 前端 Dockerfile 的重點
前端 Dockerfile 通常會做：
- 選 Nginx base image
- 複製 HTML/CSS/JS
- 複製 Nginx 設定
- 讓 Nginx 提供靜態檔與 proxy

### 7.3 兩者真正不同的地方
1. base image 不同
- 後端：Python image
- 前端：Nginx image

2. 安裝內容不同
- 後端：pip 套件
- 前端：Nginx 設定與靜態檔

3. 啟動邏輯不同
- 後端：跑 API server
- 前端：跑 web server

4. 目的不同
- 後端：算資料、處理請求、連資料庫
- 前端：服務畫面、轉發 API

所以答案是：不只差在 `CMD`，而是整體職責、基底 image、檔案內容、啟動方式都不一樣。

---

## 8. 你要怎麼把它放進 Compose

當你做成三個 container 後，Compose 會像這樣的概念：

1. frontend
- build `frontend/Dockerfile`
- 對外開 `8080:80`

2. backend
- build Python Dockerfile
- 只在內網被 frontend 叫到

3. db
- PostgreSQL
- 只給 backend 用

這樣瀏覽器只要開 `http://127.0.0.1:8080`，剩下的由 frontend container 幫你轉接。

---

## 9. 常見錯誤

1. 把 frontend Dockerfile 也寫成 Python base image
- 這樣就失去 frontend container 的意義。

2. 忘記把 nginx.conf 複製進 image
- Nginx 會用預設設定，不一定能正確 proxy 到 backend。

3. `proxy_pass` 寫錯服務名
- Compose 內要用服務名稱，不是容器名稱。

4. 前端檔案路徑放錯
- `index.html` 沒放到 Nginx root，就會找不到首頁。

---

## 10. 這一章的核心結論

你可以把 frontend container 理解成：
1. 一個專門服務靜態頁面的 Nginx 容器。
2. 一個負責把 API 請求轉給 backend 的入口層。
3. 一個讓前後端真正分離的部署單位。

如果你之後只記得一句話：
前端 container 不是在跑 Python，而是在跑 Nginx 來服務靜態頁和轉發請求。

---

## 11. 目前檢查結果與下一步

### 11.1 現在已確認的事
1. `frontend/Dockerfile` 已能成功 build。
2. `compose.yaml` 已能解析 frontend / backend / db 三個服務。
3. `frontend` 目前使用 `build: ./frontend`，表示 build context 已經切到正確目錄。
4. `nginx.conf` 已正確把 API proxy 到 `backend:8000`。

### 11.2 你接下來要做什麼
1. 用 `docker compose down` 清掉舊容器。
2. 用 `docker compose up -d --build` 重建三容器。
3. 用 `docker compose ps` 看三個 service 是否都 Up。
4. 用 `curl http://127.0.0.1:80` 檢查 frontend 是否能回首頁。
5. 再實際操作登入或新增交易，確認 proxy 到 backend 正常。

### 11.3 如果出錯先看哪裡
1. 先看 `docker compose logs --tail=80 frontend`。
2. 再看 `docker compose logs --tail=80 backend`。
3. 如果首頁正常但 API 失敗，通常是 `proxy_pass`、backend 名稱、或 backend 還沒 ready。

### 11.4 這次實際遇到的問題與修正
我在驗證時遇到 frontend 的 Nginx 啟動失敗，錯誤是 `host not found in upstream "backend"`。

這代表：
1. Nginx 啟動時還找不到 backend 服務名稱。
2. 問題通常不是 nginx.conf 的語法，而是 Compose 啟動順序或服務是否已在網路中可見。

這次的修正方式是：
1. 在 [compose.yaml](../compose.yaml) 的 frontend 服務加上 `depends_on: backend`。
2. 讓 backend 先起來，再讓 frontend 初始化 Nginx proxy 設定。
3. 重新 `docker compose up -d --build` 後，frontend 就能正常對外服務。

### 11.5 這個事件教你的判斷方法
當你看到 `host not found in upstream` 時，優先檢查：
1. 服務名稱是不是寫錯。
2. Compose 裡有沒有把依賴服務先啟動。
3. `docker compose ps` 裡依賴服務是否真的存在。

### 11.6 最後驗證結果
這次修正後，三個服務都已成功啟動：
1. frontend container 可透過 `http://127.0.0.1:80` 提供首頁。
2. backend container 可透過 `http://127.0.0.1:8000/health` 回應 `{"status":"ok"}`。
3. db container 為 healthy，且 backend 已連上 PostgreSQL。