# 原型：agent 导航 UI（V1/V2/V3 三变体）

**这是参考物，不是可合并代码。** 落地时按 `../implement.md` 重写。

## 运行

```bash
cd frontend
npx vite --config scripts/prototype.vite.config.mts
# 打开 http://localhost:5174/
```

配置放在 `frontend/scripts/` 而非本目录，原因：vite 配置文件本身要 `import 'vite'`，
而 `.trellis/` 向上找不到 `node_modules`，放在这里会直接 `ERR_MODULE_NOT_FOUND`。
放在 `frontend/` 下可以正常解析，只把 `root` 指向本目录。

原型目录在 `frontend/` 之外，裸模块解析不到，因此 `react` / `react-dom` / `lucide-react`
在配置里全部显式别名到 `frontend/node_modules`。

不影响生产构建：`root` 是原型目录，输出到 `frontend/.prototype-dist/`（已 gitignore）。

## 三个变体

底部浮动切换。**V1 已定案**：浮层内一行系统提示 `⚡ 已跳转到「…」`，面板位置尺寸完全不动。

- **V1**（采用）：系统提示嵌在浮层消息流里
- **V2**：toast 提示——已否，遮挡右下角且与浮层按钮打架
- **V3**：窄屏自动收起——已否，一期不做

## 实测记录（CDP + ws 真实点击驱动，非静态截图）

- V1：年份下拉真变 2022、标题变「共 8 部作品」、卡片换成 2022 组、浮层出现系统提示、
  URL 条变 `/anime?year=2022&page=1`
- 复合指令：预览阶段 URL 仍 `/anime?page=1` 不跳；点确认后 → `/my-collections?tab=want&page=1`，计数 3→4
- vite error 计数 0，生产文件零改动，零网络请求

## 注意

原型里的数据是 `data.ts` 里的假数据，不请求后端。它只验证「界面形态」，
不验证业务逻辑。设计结论见 `../prototype.md` 与 `../design.md`。
