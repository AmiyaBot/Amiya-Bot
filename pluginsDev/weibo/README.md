- 管理员发送 `兔兔开启微博推送` 即可，微博更新时会自动推送。
- 管理员发送 `兔兔关闭微博推送` 即可取消。

### 配置

```yaml
setting:
    # 抓取的时间间隔
    checkRate: 30
    # 是否发送GIF图
    sendGIF: false
    # 缓存图片的目录
    imagesCache: log/weibo

# listen 下可追加需要监听的微博ID
listen:
    - 6279793937
    - ...
    - ...
```
