# 内容与 IP 风险登记

> 适用范围：公网 H5、小程序首版、后续内容生产。  
> 更新日期：2026-05-13。

## 风险分级

| 等级 | 说明 | 处理 |
|---|---|---|
| P0 | 可能影响小程序审核或品牌安全 | 小程序首版禁止展示 |
| P1 | 公网可访问但不作为主入口 | H5 production 隐藏入口，preview 可留存 |
| P2 | 原创知识内容 | 可进入 H5 与小程序首版 |

## 当前内容登记

| 内容 | 风险 | 当前策略 |
|---|---:|---|
| Kids-World 原创知识 topic | P2 | H5 production 与小程序首版可展示 |
| Paw Patrol 相关看板 | P0 | 小程序首版禁止展示，H5 production 不发布目录 |
| Spider-Verse 相关看板 | P0 | 小程序首版禁止展示，H5 production 不发布目录 |
| 生成图片中的原创小芋头角色 | P2 | 可展示，需保持无第三方品牌标识 |
| 未来新增 topic 图片 | P2 | 必须走 manifest、validate 与人工抽检 |

## 小程序首版规则

- 只展示 `channel-policy.json` 中 `miniprogram.visibleTopics` 指定的 topic。
- 不展示动画世界中的第三方 IP 衍生内容。
- 不使用第三方角色名、商标、影视作品名作为页面标题、分享标题或审核说明重点。
- CDN 图片 URL 必须来自正式 EdgeOne 域名。

## 内容生产规则

- 生成图 prompt 不使用真实品牌、商标、影视角色名称。
- 新图片不覆盖旧图，使用 `v03` / `v04` 等版本号。
- topic JSON 只能引用已存在且通过 manifest 校验的 WebP 资产。
- 新增 topic 进入小程序前，必须先更新 `channel-policy.json` 并通过 `npm run validate`。
