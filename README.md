# ThingsConnect Components

[ThingsConnect](https://thingsconnect.app) のカスタム処理で使える公開コンポーネントと、スクリプトを動かすランタイムのソースです。どちらも ThingsConnect のコンポーネント一覧に最初から出ていて、エッジPC へそのままデプロイできます。

| ディレクトリ | 中身 | イメージ |
| --- | --- | --- |
| `components/<名前>/` | 公開コンポーネント（Dockerfile・コード・`component.json`） | `public.ecr.aws/<alias>/components/<名前>:<version>` |
| `runtimes/<名前>/` | 画面のエディタで書いたスクリプトを動かすランタイム（Dockerfile・`runtime.json`） | `public.ecr.aws/<alias>/runtimes/<名前>:<version>` |

`component.json` の `config` は、ThingsConnect にバージョンを登録するときの設定（環境変数の既定値・ポート・リソース上限）です。

## 自分用に作り替える

イメージは public ECR に公開しているので、`FROM` で拡張したり、Dockerfile を写して作り替えたりできます。作ったイメージは、ThingsConnect のバージョン登録で「イメージを指定」に URI を入れるか、CLI の `thingsconnect push` で送れば使えます。

ランタイムに無いライブラリが要るスクリプトも、同じ方法で作ったイメージに載せ替えられます。

## 版の付け方

**配った版の中身は変えません。** 中身を変えるときは `version` を上げます（同じ版のイメージは作り直しません）。

このリポジトリは ThingsConnect の開発リポジトリから自動で同期しています。不具合の報告や要望は Issue で受け付けます。

## ライセンス

[MIT](LICENSE)
