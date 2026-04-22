# Docker 課程紀錄

## 課程定位
這門課會帶你從 Docker 一路走到 incident-response。
你指定的學習路線如下：
1. docker
2. docker-compose
3. kubernetes
4. helm
5. gitlab ci
6. jenkins
7. prometheus
8. elk
9. incident-response

目前進度：`docker`（第 1 章）

---

## 1. 本章學習目標（Docker）
完成本章後，你應該能夠：
- 理解 Docker 解決了什麼問題（環境一致性、快速部署、隔離）
- 分辨 image、container、registry 的差異
- 使用常見 Docker CLI 指令
- 自己寫出一份可運行的 `Dockerfile`
- 在本機測試容器化應用

---

## 2. 核心觀念

### 2.1 Docker 是什麼
Docker 是一種「容器化（Containerization）」技術。它會把應用程式與相依套件打包成 image，執行時變成 container。

### 2.2 Image vs Container
- Image：唯讀模板，像是「安裝檔」
- Container：image 執行後的實例，像是「正在跑的程式」

### 2.3 為什麼不是 VM？
- VM：每台都要帶完整作業系統，較重
- Container：共享宿主機 kernel，啟動快、資源開銷小

---

## 3. 必學指令（先背這些）

```bash
# 查看 Docker 版本
docker --version

# 查看本機 images
docker images

# 查看執行中的 containers
docker ps

# 查看所有 containers（包含停止）
docker ps -a

# 從 Docker Hub 拉 image
docker pull nginx:latest

# 啟動容器（前景）
docker run nginx:latest

# 啟動容器（背景）並映射 port
docker run -d --name web01 -p 8080:80 nginx:latest

# 停止 / 刪除容器
docker stop web01
docker rm web01

# 刪除 image
docker rmi nginx:latest
```

---

## 4. 第一個實作：把 Python app 容器化

以下示範把專案中的 `app.py` 容器化。

### 4.1 建立 Dockerfile
在專案根目錄新增 `Dockerfile`：

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "app.py"]
```

### 4.2 建立 image
```bash
docker build -t bookkeeping-app:1.0 .
```

### 4.3 啟動 container
```bash
docker run -d --name bookkeeping-api -p 8000:8000 bookkeeping-app:1.0
```

### 4.4 驗證
```bash
docker ps
curl http://127.0.0.1:8000
```

### 4.5 查看 log
```bash
docker logs -f bookkeeping-api
```

### 4.6 清理
```bash
docker stop bookkeeping-api
docker rm bookkeeping-api
```

---

## 5. Dockerfile 重要最佳實務（初學必懂）
- 盡量使用小型 base image（例如 `python:3.11-slim`）
- `COPY requirements.txt` 後先 `pip install`，可利用 layer cache 加速重建
- 加上 `.dockerignore`，避免把不必要檔案打包進 image
- 不要把密碼、token 寫進 image

範例 `.dockerignore`：

```txt
.venv
__pycache__
.git
*.pyc
*.log
```

---

## 6. 常見錯誤排查
- Port 衝突：`Bind for 0.0.0.0:8000 failed`  
  解法：改成 `-p 8001:8000` 或先釋放 8000 port。

- 容器啟動後立刻退出：  
  解法：`docker logs <container_name>` 看錯誤，多半是啟動命令錯誤或相依套件缺失。

- `ModuleNotFoundError`：  
  解法：確認 `requirements.txt` 完整、且 Dockerfile 有正確安裝依賴。

---

## 7. 本章練習（請你實作）
1. 使用 `docker run` 啟動 `nginx` 並用瀏覽器開 `http://127.0.0.1:8080`。
2. 將 `bookkeeping` 專案打包成 `bookkeeping-app:dev` image。
3. 修改 `app.py` 任一回應文字後，重新 build 並驗證容器輸出有變更。
4. 使用 `docker logs` 與 `docker exec -it <name> sh` 進入容器檢查檔案。

---

## 8. 學習檢核（過關條件）
你可以回答以下問題就算過關：
- Docker image 和 container 的差別是什麼？
- 為什麼 Dockerfile 要把 `COPY requirements.txt` 放在前面？
- `-p 8080:80` 左右兩個數字各代表什麼？
- 你會怎麼查容器為什麼啟動失敗？

---

## 9. 下一章預告：Docker Compose
下一章會進入 `docker-compose`，你會學到：
- 用一個 `compose.yaml` 同時啟動多個服務
- 服務間網路與依賴管理
- 把 app + db 一次啟動，接近真實開發場景

---

## 10. Dockerfile 逐行白話解釋（課堂問答紀錄）

以下內容對應目前的 `Dockerfile`：

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "app.py"]
```

逐行說明：

1. `FROM python:3.11-slim`  
  以 Python 3.11 的精簡映像作為基底環境。

2. `WORKDIR /app`  
  設定容器內工作目錄為 `/app`，後續指令預設都在這裡執行。

3. `COPY requirements.txt ./`  
  先把依賴清單複製進容器，目的是讓套件安裝可利用 Docker layer cache。

4. `RUN pip install --no-cache-dir -r requirements.txt`  
  在建置映像時安裝套件；`--no-cache-dir` 可避免保留 pip 快取，減少映像大小。

5. `COPY . .`  
  把目前專案檔案複製到容器工作目錄（`/app`）。

6. `EXPOSE 8000`  
  宣告容器預期使用 8000 port。這是文件性宣告，對外連線仍要在執行時用 `-p` 映射。

7. `CMD ["python", "app.py"]`  
  設定容器啟動後的預設命令，會執行 `python app.py`。

整體流程一句話：
選基底環境 -> 設工作目錄 -> 安裝依賴 -> 複製程式碼 -> 宣告服務埠 -> 設定啟動命令。

---

## 11. 事件復盤紀錄：Dockerfile cannot be empty

### 11.1 現象
執行以下命令時失敗：

```bash
docker build -t bookkeeping-app:1.0 .
```

錯誤訊息：

```txt
ERROR: failed to build: failed to solve: the Dockerfile cannot be empty
```

### 11.2 我是如何定位問題的
當下先做兩件事：

1. 重新執行同一個 build，確認錯誤可穩定重現（排除暫時性問題）。
2. 檢查 `Dockerfile` 實體檔案狀態（不是只看編輯器畫面）：

```bash
ls -l Dockerfile
wc -c Dockerfile
file Dockerfile
```

檢查結果顯示 `Dockerfile` 當下是 0 bytes（空檔），因此 Docker 才會拋出 cannot be empty。

### 11.3 我是如何修復的
修復步驟：

1. 將正確內容重新寫回 `Dockerfile`。
2. 再次執行：

```bash
docker build -t bookkeeping-app:1.0 .
```

3. Build 成功，映像 `bookkeeping-app:1.0` 已產生。

### 11.4 為什麼會發生
最常見原因是「編輯器顯示有內容，但磁碟上的檔案其實被清空或尚未寫入」。

可能情境：
- 編輯流程中曾誤操作清空檔案並保存。
- 外部工具或腳本覆寫檔案。
- 多視窗/外掛同步造成內容未落盤。

### 11.5 預防措施（SRE 思維）
每次 build 前做最小健康檢查：

```bash
wc -c Dockerfile
sed -n '1,40p' Dockerfile
```

若再次遇到相同錯誤，先跑以下排查順序：

1. `wc -c Dockerfile` 檢查是否為 0 bytes。
2. `ls -l Dockerfile` 檢查修改時間是否異常。
3. `docker build --no-cache -t bookkeeping-app:1.0 .` 排除快取影響。
4. 若仍異常，再檢查 `.dockerignore` 與 build context。

### 11.6 可複用的 lesson learned
- 排錯優先看「磁碟實體檔」，不要只依賴編輯器畫面。
- 先重現、再定位、最後修復與驗證，避免一次改太多難以回溯。
- 把命令與結果記錄下來，後續可直接轉成 incident-response runbook。

---

## 12. Incident Response 紀錄版（可當範本）

### 12.1 Incident Title
Docker build 失敗：Dockerfile cannot be empty

### 12.2 Severity
SEV-3（開發流程中斷，但未影響正式服務）

### 12.3 Impact
- 影響範圍：本機開發與學習流程
- 影響內容：無法建置映像，導致後續容器測試中斷
- 使用者影響：無外部使用者受影響

### 12.4 Detection
- 偵測方式：手動執行 build 命令時收到錯誤
- 告警來源：CLI 錯誤訊息

### 12.5 Timeline
1. T0：執行 docker build，收到 cannot be empty。
2. T0+1：重試 build，錯誤可穩定重現。
3. T0+2：檢查 Dockerfile 實體檔，確認為 0 bytes。
4. T0+3：回填正確 Dockerfile 內容。
5. T0+4：重新 build 成功，incident 結束。

### 12.6 Root Cause
直接原因：磁碟上的 Dockerfile 為空檔，導致 builder 無法解析建置指令。

潛在原因：編輯流程或外部覆寫導致檔案內容未正確落盤。

### 12.7 Mitigation and Recovery
- 臨時處置：重建 Dockerfile 內容並重新建置。
- 恢復驗證：映像 bookkeeping-app:1.0 成功產生。

### 12.8 Corrective Actions
1. 建置前加入最小檢查：先看 Dockerfile 檔案大小與前幾行內容。
2. 發生建置錯誤時先重現，再檢查實體檔，避免誤判。
3. 將排錯步驟固定成 runbook，後續 incident 可直接套用。

### 12.9 Preventive Actions
1. 建立 pre-build checklist。
2. 重要設定檔建立版本控管保護，避免空檔覆寫未被注意。
3. 在 CI 加入 Dockerfile 基本檢查，提早攔截異常。
