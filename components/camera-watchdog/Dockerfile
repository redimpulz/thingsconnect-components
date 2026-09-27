FROM alpine:3.21

RUN apk add --no-cache ffmpeg python3

WORKDIR /app
COPY app.py .

# ログがすぐ出るようにバッファリングを切る
CMD ["python3", "-u", "app.py"]
