# AnimeTracker「番组手账」测试报告（第五轮 · 全量回归）

> 报告版本：v1.0（2026-08-11）
> 被测 commit：6015eca（fix: admin dashboard图表卡被压成1/3宽）
> 基线 commit：9749df0e77（round-3 全绿 153/153，见 baseline-success-sha.txt）
> 计划文件：docs/test/plan/test-plan-2026-08-11.md
> 执行人：Hermes Agent（project-test-pipeline skill v1.1.0）
> 执行时间：2026-08-11 09:27 ~ 09:56

---

## 一、基础信息（环境指纹）

| 项 | 值 |
|---|---|
| OS | Debian 13 (linux 6.12.101+deb13-amd64) |
| 机器 | 本机 192.168.0.3（DHCP，原 192.168.0.110 已失效） |
| JDK | OpenJDK 21.0.11 |
| Maven | 3.9.9 |
| Node | v24.19.0 |
| MySQL | 8.4.9（Docker 1Panel-mysql-aeEP） |
| Redis | 8.8.0（Docker 1Panel-redis-HGyc，应用数据 db=1） |
| MinIO | minio RELEASE.2025-04-22（Docker） |
| swap | 7.9G（4G /swapfile + 3.9G 分区） |
| profile | local（application-local.yml + /etc/animetracker/ 覆盖层） |
| 被测 SHA | 6015eca01e54002ed3cdb5c0aecafd4380e2ee24 |
| 基线 SHA | 9749df0e77caef3a54a737aba34057390a52fe9f |
| 数据基线 | user_collection 5 条（type=3 ×4 + type=1 ×1），user 3 条（admin/test1/test2），subject 10614，episode 148782 |

## 二、分层结果汇总

| 层 | 用例数 | PASS | FAIL | SKIP | LIMITED | 通过率 | 耗时 |
|---|---|---|---|---|---|---|---|
| L0 Java 单测 | 34 | 34 | 0 | 0 | 0 | 100% | ~2.5min |
| L1 pytest + AI 文本 | 101 | 101 | 0 | 0 | 0 | 100% | ~5s + AI对话~60s |
| L2 前端构建 | 4 | 4 | 0 | 0 | 0 | 100% | ~28s |
| L3 API 冒烟 | 10 | 10 | 0 | 0 | 0 | 100% | ~15s |
| L4 E2E 浏览器 | 9 | 9 | 0 | 0 | 0 | 100% | ~2min |
| **合计** | **158** | **158** | **0** | **0** | **0** | **100%** | |

注：L0 从 33 增至 34（新增防护用例 hotSubjectsMapCollectionCount）；L1 从 100 增至 101（AI 文本四方核对 L1-AI-001）。总用例较上轮 153 增 5。

## 三、缺陷清单（按 P0-P3 分级）

### P1（严重，本轮发现并已修复）

**#10 热门榜 collectionCount 恒为 0**
- 层：L3/L4（/api/admin/dashboard/hot）
- 表现：热门榜 5 条收藏数全为 0，与 DB 实际不符（皮丘与皮卡丘等各 1 条收藏）
- 根因：`DashboardMapper.xml` hotSubjects SQL 别名 `COUNT(uc.id) AS count`，而 VO `HotSubjectVO.collectionCount` 字段名不匹配（map-underscore-to-camel-case=true 只认 `collection_count` → collectionCount），MyBatis 自动映射失败，字段恒为默认值 0
- 证据：接口返回 `{"id":1,"collectionCount":0}` vs DB `SELECT COUNT(*) FROM user_collection WHERE subject_id=1` = 1
- 修复：
  1. `DashboardMapper.xml`：`AS count` → `AS collection_count`，`ORDER BY count` → `ORDER BY collection_count`（修复轮次 1，Codex 诊断+方案，Hermes 应用，claude 网关不可用降级）
  2. 防护用例：`DashboardMapperTest.hotSubjectsMapCollectionCount` 断言全部 ≥0 且至少一条 >0（配套新增，P0/P1 硬性验收卡点）
- 复验：mvn test 34/34 通过；接口返回 collectionCount=1 正确；浏览器热门榜显示 1/1/1 ✅
- 审计：修复 Agent=codex（诊断）+ hermes（应用），进程 pid 250797，claude 网关 Not logged in 降级

### P2（一般，登记技术债，不阻塞本次交付）

**#11 subject.image 硬编码失效 IP（112 条）**
- 层：数据（subject 表 image 字段）
- 表现：112 条封面 URL 为 `http://192.168.0.110:9000/...`（旧机器 IP，已失效），前端加载报 ERR_ADDRESS_UNREACHABLE；其余 10362 条为 `http://47.96.127.231:9000/...`（公网，本机网络不可达但浏览器可直连）
- 根因：历史导入（bangumi 抓取）时 MinIO endpoint 写入了当时的局域网 IP
- 影响：详情页/列表封面图部分加载失败（P2 视觉缺陷，不影响功能）
- 建议：数据修复 `UPDATE subject SET image = REPLACE(image, '192.168.0.110', '<当前MinIO可达地址>') WHERE image LIKE '%192.168.0.110%'`，修复前需确认线上 MinIO 公网/内网可达地址；排期处理

## 四、Flaky / 受限 / 未覆盖

| 项 | 说明 |
|---|---|
| Flaky | 无（本轮 158 例无间歇性失败） |
| 受限 | 无 |
| 未覆盖 | L5 可选层（混沌/性能/SAST）未启用（用户未显式指令）；真实 LLM 长对话未覆盖（API key 受限）；压测未做 |

## 五、变更影响摘要

基线 9749df0 → 被测 6015eca 变更（4 个修复 commit）：
1. a1db24e agent 收藏类型语义修复（prompt 映射 + 工具返回 label）→ L1/L4 重点验证 ✅ 通过
2. 06e5fae 收藏页移动端卡片布局 → L4 移动端 390px 验证 ✅ 通过
3. 6015eca admin dashboard grid 特异性修复 → L4 chart-lg span 8 验证 ✅ 通过
4. 40d4d30 文档（计划/报告）

本轮回归覆盖全部变更影响区，未发现回归。

## 六、上线建议

- **结论：放行**（158/158 全绿，无 P0，P1 已修复并配防护用例）
- 本次新增：1 个 P1 修复（DashboardMapper.xml 别名 + 防护用例）
- 待提交内容：DashboardMapper.xml（修复）、DashboardMapperTest.java（防护用例）、docs/test/plan/test-plan-2026-08-11.md、docs/test/report/test-report-2026-08-11.md、baseline-success-sha.txt、scripts/test-seed.sql（种子数据脚本）、未跟踪的本地文件（AGENTS.md/CLAUDE.md/update.sh 不提交）
- 回滚触发条件：上线后热门榜接口异常（SQL 语法错误/字段缺失）→ 回滚 6015eca 或 revert 本次修复；数据类异常（收藏数显示异常）检查 collection_count 别名与 VO 字段一致性
- 边界约定：本流水线仅预合并门禁；生产灰度冒烟为后置补充；测试通过 ≠ 自动上线，合并/上线决策权保留给用户

## 七、审计链路

| 轮次 | Agent | 动作 | 结果 |
|---|---|---|---|
| 1 | codex（pid 250797） | 诊断 #10 根因 + 产出修复方案与防护用例代码 | 沙箱只读未落盘，方案正确 |
| 1 | hermes | 应用补丁（XML 别名×2 + 测试用例×1） | mvn 34/34 ✅ |
| 1 | hermes | 重启 business 复验接口 + 浏览器热门榜 | collectionCount=1 ✅ |
| 备注 | claude | 网关 Not logged in（minimax-m3），SOP 评审职责由 Hermes 补位 | 降级记录 |

## 八、附：关键证据

- AI 文本四方核对：AI 回答「4 部在看、1 部想看，没有看过」= DB（type=3×4+type=1×1）= 接口 = 前端 ✅
- chart-lg 布局：`getComputedStyle` gridColumn=span 8，宽 671px（2/3 宽）✅
- 移动端 390px：docSW=390=winW 无溢出，5 卡片可见，取消收藏按钮可见可点 ✅
- 截图存证：/tmp/l4_20260811-*.png（client-home/collections/inwatch/detail、admin-dashboard、mobile-collections/inwatch、admin-mobile、admin-hot-fixed）
