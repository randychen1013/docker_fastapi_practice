# 使用 Python 3.9 的輕量 Linux Image 作為基底
FROM python:3.9-slim

# 避免 Python 產生 .pyc 快取檔
ENV PYTHONDONTWRITEBYTECODE=1

# Python 輸出直接送到 Console，不使用緩衝
ENV PYTHONUNBUFFERED=1

# 設定容器內的工作目錄
WORKDIR /app

# 先複製套件清單，方便利用 Docker 快取
COPY requirements.txt .

# 安裝 Python 套件，繞過公司內網的 SSL 檢查問題
RUN python -m pip install --no-cache-dir \
    --trusted-host pypi.org \
    --trusted-host pypi.python.org \
    --trusted-host files.pythonhosted.org \
    -r requirements.txt

# 複製程式碼到容器
COPY app.py data.py ./

# 說明容器預計使用 8000 port
EXPOSE 8000

# 啟動 Uvicorn ASGI Server 開啟 FastAPI 應用程式，並設定 host 與 port，process workers 數量為 1
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
