FROM python:3.12-slim-bookworm

# カメラの映像を扱う処理が多いので、ffmpeg と OpenCV を最初から入れておく。
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
  && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir numpy opencv-python-headless requests paho-mqtt

# コードは /app に読み取り専用でマウントされる。書き込みは /tmp に行う。
RUN useradd --uid 10001 --create-home app
USER app
WORKDIR /app

# ログがすぐ出るようにバッファリングを切る
CMD ["python3", "-u", "main.py"]
