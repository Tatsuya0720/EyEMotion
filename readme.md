# environment
- pipfileに記載

## objective
- アイトラッカーから得られる視線情報付き動画データと脳波測定器から得られるEEGデータを同期して脳波が乱れたときの映像や視線情報を照らし合わせ,福祉に潜む課題の発見を行う

## system construction
![システム構成](https://user-images.githubusercontent.com/47269204/207067322-f4cc3b4a-cae3-49d7-ac80-c64c1653e4bc.jpg)

## branch intro
- master
  - 安定版を置くためのブランチ.featureブランチで機能ごとに開発を行いdevelopで統合したものを最終的にここにステージングする
- develop
  - 動作はするが開発途中のものを置くためのブランチ.featureブランチで機能ごとに開発を行いこのブランチで統合する
- feature-converter
  - 異なるサンプリング時間,サンプリングレートの動画データとEEGデータを同期させる機能の開発
- feature-tobii
  - アイトラッカーのAPI機能を用いてデータのサンプリングを円滑に行う機能の開発

## Appearance
![layout1](https://user-images.githubusercontent.com/47269204/207069306-0e66ed78-a749-4470-84a9-eee64194d8cb.jpg)
![layout2](https://user-images.githubusercontent.com/47269204/207069344-360994ab-1fdb-469a-a8d1-b828569875bf.jpg)
![layout3](https://user-images.githubusercontent.com/47269204/207069351-6592793e-0020-4f7b-920e-00874bdf514c.png)
