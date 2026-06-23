# FastAPI Docker Image 建立與啟動教學

這份範例適合 Python 3.9 的 FastAPI 專案。交接時，對方只要把自己的模型、處理函數、套件需求填進對應檔案，就可以建立 Docker image。

## 1. 專案結構

```text
docker_fastapi_practice/
├── app.py
├── data.py
├── requirements.txt
├── Dockerfile
└── .dockerignore
```

各檔案用途：

```text
app.py            FastAPI 入口，裡面要有 app = FastAPI()
data.py           API input/output 的 Pydantic schema
requirements.txt  Python 套件清單
Dockerfile        建立 Docker image 的設定
.dockerignore     不打包進 image 的檔案
```

## 2. app.py 必要格式

Dockerfile 目前用這個指令啟動：

```text
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 1
```

所以 `app.py` 裡面必須有一個叫做 `app` 的 FastAPI 物件：

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}
```

如果改成 `main.py`，或 FastAPI 物件不叫 `app`，Dockerfile 的啟動指令也要一起改。

## 3. requirements.txt

公司網路限制下，Dockerfile 會用 trusted-host 安裝套件：

```text
fastapi>=0.100,<1.0
uvicorn[standard]>=0.23,<1.0
pydantic>=2,<3
typing-extensions>=4.8
```

如果之後有新增套件，例如 `numpy`、`opencv-python`，就加在 `requirements.txt`。

## 4. 建立 Docker Image

在專案資料夾執行：

```powershell
docker build -t mock-fastapi-api:1.0.0 .
```

指令說明：

```text
mock-fastapi-api 是 image 名稱
1.0.0 是版本 tag
. 代表使用目前資料夾的 Dockerfile
```

如果要重建且不使用 cache：

```powershell
docker build --no-cache -t mock-fastapi-api:1.0.0 .
```

## 5. 啟動 Container

```powershell
docker run --rm -p 8000:8000 --name mock-fastapi-api mock-fastapi-api:1.0.0
```

啟動後可以打開：

```text
http://localhost:8000/docs
```

## 6. 測試 API

用 Swagger 測試：

```text
http://localhost:8000/docs
```

或用 curl：

```powershell
curl -X POST "http://localhost:8000/mock" `
  -H "Content-Type: application/json" `
  -d "{\"timestamp\":\"2026-06-23T12:00:00+08:00\",\"frame_count\":1,\"cam_data\":[{\"cam_id\":21,\"objects\":[]}]}"
```

成功時會回傳 `OutputData` JSON。

## 7. 正式部署建議

正式交接時建議提供：

```text
1. app.py
2. data.py
3. requirements.txt
4. Dockerfile
5. .dockerignore
6. API 測試範例 JSON
7. image build/run 指令
```

如果要固定版本，建議把 `requirements.txt` 改成明確版本，例如：

```text
fastapi==0.115.0
uvicorn[standard]==0.30.6
pydantic==2.9.2
typing-extensions==4.12.2
```

版本固定後，交接與部署會比較穩，不會因為未來套件更新而行為改變。
