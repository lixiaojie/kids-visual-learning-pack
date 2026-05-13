# 微信小程序首版合规清单

> 适用范围：小程序首版（个人主体，Taro 原生小程序）。  
> 更新日期：2026-05-13。

## 路线结论

- 小程序首版不使用 `web-view`，因为个人主体小程序不支持该能力。
- 小程序首版使用 Taro 编译为微信小程序原生页面。
- EdgeOne 只承担图片 CDN 与 H5 预览站职责，不作为小程序页面容器。

## 小程序首版范围

- 展示 Kids-World 的 12 个 render-ready topic。
- 首页展示世界入口与推荐 topic。
- Topic 页面展示核心学习内容、图片、点击任务、复述模板与家长提示。
- About 页面展示家长说明、隐私政策与用户协议摘要。
- 分享路径使用 `/pages/topic/index?slug=<topic>&locale=<locale>`。

## 明确不做

- 不接微信登录。
- 不接云开发、云函数、云数据库。
- 不接第三方统计 SDK。
- 不接支付。
- 不做 UGC、评论、上传、社交关系。
- 不采集儿童姓名、年龄、头像、位置、通讯录、录音、摄像头或精细行为数据。
- 不展示 `paw-patrol` 或 `spider-verse` 入口。

## 隐私与数据

- 学习进度如需保存，首版只允许使用本地存储。
- 本地存储只记录 topic slug、locale、完成状态，不记录儿童身份。
- 网络请求只允许加载 EdgeOne CDN 图片和小程序自身静态资源。

## 提审前检查

- [ ] `channel-policy.json` 的 `miniprogram.visibleBoards` 只包含 `kids-world`。
- [ ] `channel-policy.json` 的 `miniprogram.visibleTopics` 全部为 render-ready topic。
- [ ] 小程序包内无 `paw-patrol` / `spider-verse` 页面入口。
- [ ] 小程序包内无未备案或 IP 形式资源地址。
- [ ] 隐私政策和用户协议页面可从 About 页面进入。
- [ ] iOS 微信真机至少检查 5 个 topic。
- [ ] Android 微信真机至少检查 5 个 topic。
- [ ] 分享好友后能恢复 topic。
- [ ] CDN 图片加载失败时页面仍有文字内容可读。
