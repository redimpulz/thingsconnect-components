#!/bin/sh
# /recordings（読み取り専用）を DEST へコピーし続ける。送り先の設定は RCLONE_CONFIG_DEST_* の環境変数で渡す。
set -u
INTERVAL_SEC="${INTERVAL_SEC:-300}"
while true; do
  # 書き込み中の録画を送らないよう、最後の更新から 2 分以上経ったものだけを対象にする。
  rclone copy /recordings "dest:${DEST_PATH}" --min-age 2m --transfers 1 --bwlimit "${BWLIMIT:-off}" \
    || echo "同期に失敗しました。次の周期で再試行します"
  sleep "$INTERVAL_SEC"
done
