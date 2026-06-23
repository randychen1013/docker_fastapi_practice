# 目標

建立一個 docker container fastapi 微服務

主程式另外開啟另外一個 threading + queue
主程式丟 input data 透過 queue_input 給 api 然後 api 處理塞到 queue_output
主程式跑完主要的影像辨識後 需要資料再去 queue_output

## 兩種做法

1. input output 各一個服務 用 request_id 去撈 -> 這樣還要考慮錯誤號碼來不及
2. 直接用 fifo 去做沒跑完等於 卡住

TODO

- [ ] 多階段執行 DOCKER FILE 不要太腫
- [ ] container 連線
- [x] 隨機生資料給 api
