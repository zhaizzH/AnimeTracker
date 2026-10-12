# 实施：两端 UI 重建（父任务 = 排序与集成验收）

> 父任务**不直接实施**。各行代码改动在子任务中进行；本文件只描述子任务排序、子任务间门禁与父任务层的集成验收。

## 子任务排序

```
1 rebuild-prep ──► 2 ui-infra ──┬──► 3 client-shell ──► 4 client-pages
                                └──► 5 admin-verify        （5 与 2/3/4 无依赖，可并行）
```

| 阶段 | 子任务 | 退出条件（该子任务自身 AC 通过） |
|---|---|---|
| A | `10-12-rebuild-prep` | tag 已打、核对表落盘、shared 清 antd 且其测试通过、**client** 旧实现已删（admin 不删） |
| B | `10-12-ui-infra` | client 空壳 `dev` 可启动、admin 基线不受影响、暗色切换经 theme-bridge 生效、typecheck/build 通过 |
| C | `10-12-client-shell` | 侧栏导航可用、未登录守卫带 `state.from` 重定向、`PublicOnly` 重定向 |
| D | `10-12-client-pages` | 12 页接真实数据、三态齐全、client 测试通过且覆盖不减少 |
| E | `10-12-admin-verify` | `admin-diff.md` 落盘、明确「是否需改动」结论、admin typecheck/test 基线通过 |

每个阶段结束后**回报父任务**：完成项、被阻塞项、deferred 项。

## 子任务间门禁

- B 依赖 A 的「旧实现已删」——A 未完成不得开始 B（否则配置改动与旧代码互相干扰）。
- D 依赖 C 的路由骨架——C 未完成不得开始 D。
- E 只依赖 A，与 B/C/D 完全并行；**只读核验**，不改 admin 源码。
- 子任务内部不通过的验收，**退回该子任务修复**，不在父任务或兄弟子任务里就地打补丁。

## 父任务集成验收（全部子任务完成后执行）

- [ ] 跑全量门禁：`cd frontend && npm run typecheck && npm test && npm run build`
- [ ] AC2 核残留：`grep -rn "from 'antd'\|@ant-design/icons\|od-" frontend --include=*.ts --include=*.tsx --exclude-dir=node_modules` 无业务结果
- [ ] AC3 核 `@shared` 引用完整（对照 `10-12-rebuild-prep/research/shared-refs.txt`）
- [ ] AC4 两端 `dev` 冒烟 + `/api` 代理 + 守卫重定向（admin 作为「未被本次变更破坏」的基线）
- [ ] AC5 主链路走查：client 筛选/收藏/进度/日历/Profile/Agent；admin 侧对照 `10-12-admin-verify/research/admin-diff.md` 的「已对齐」结论
- [ ] AC6 对照原 16 用例核覆盖清单
- [ ] AC7 更新 spec 与 README
- [ ] AC8 汇总 deferred 清单
- [ ] `task.py finish` + 提交

## 验证命令

```bash
cd frontend
npm run typecheck
npm test
npm run build
```

## 汇总与回滚

- **汇总**：各子任务产出向父任务汇总（完成项 / 阻塞项 / deferred / 新增风险），父任务在集成验收后统一决定是否收口。
- **回滚锚点**：子任务 1 打下的 `pre-frontend-rebuild` tag。
- **整体回滚**：`git checkout pre-frontend-rebuild -- frontend/`。
- **分阶段回滚**：按子任务边界，A/B/C/D/E 各自可独立还原。
