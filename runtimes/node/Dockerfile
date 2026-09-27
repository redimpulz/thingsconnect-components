FROM node:22-bookworm-slim

# コードは /app に読み取り専用でマウントされる。書き込みは /tmp に行う。
USER node
WORKDIR /app

CMD ["node", "main.js"]
