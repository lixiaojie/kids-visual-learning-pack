# 孩子可视化学习看板

Project slug: `kids-visual-learning-pack`

这是一个独立静态网页项目，不属于 `xiaojie-shares`。

项目用于按不同孩子喜欢的主题制作可视化学习看板，比如蜘蛛宇宙、汪汪队等。每个主题看板都是独立静态页面，既可直接浏览，也可用浏览器打印为 A4 竖版卡片。

当前主题：

- `boards/spider-verse/`：原创蛛网主题亲子故事板，包含 10 个视觉模块和家长讲解附录，覆盖角色、关系、能力、双剧情地图、问题卡、多元故事书、选择、艺术和创作卡，并已接入批量生成的图片素材。
- `boards/paw-patrol/`：汪汪队任务指挥中心，包含角色分工、地图热点、装备工坊、任务小游戏、流程复述和徽章收集。

详细目录说明见 `docs/project-structure.md`。

## 本地预览

打开总入口：

```bash
open index.html
```

也可以直接打开某个主题：

```bash
open boards/spider-verse/index.html
```

汪汪队任务指挥中心是 Vite + React 页面，推荐安装依赖后启动本地服务器：

```bash
npm install
npm run dev
```

然后访问：

```text
http://127.0.0.1:5173/boards/paw-patrol/
```

也可以先构建：

```bash
npm run build:paw
```

其他静态主题可启动静态服务器：

```bash
python3 -m http.server 8000
```

然后访问总入口：

```text
http://localhost:8000
```

## 打印

具体主题页面右上角有“打印”按钮，也可以使用浏览器打印功能。

建议设置：

- 纸张：A4
- 方向：竖向
- 边距：默认或较小
- 背景图形：开启

每张学习卡会独立分页。

## 版权边界

本项目使用原创 HTML/CSS 信息图表达，不包含官方截图、官方 Logo、精确角色服装复刻或影视分镜复刻。内容定位为家庭教育和亲子讲解材料。
