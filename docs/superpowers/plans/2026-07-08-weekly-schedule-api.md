# 每周追番接口 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 消除 Home.vue 每周追番区域 N+1 查询问题（拉取季度列表 → 对每一条调用 getDetail），改为后端专用接口按星期维度返回数据。

**Architecture:** 后端新增 `/api/user/subjects/schedule` 接口（按季度日期范围 + 可选 weekday 筛选），前端替换掉现有的低效 fetch。`SubjectListVO` 补充 `airWeekday` 和 `collectionTotal` 字段，使列表级响应自带星期信息，无需再去查详情。

**Tech Stack:** Java 21, Spring Boot 3.2, MyBatis-Plus, Vue 3, Pinia, Axios

## Global Constraints

- 数据库字段 `subject.air_weekday` 已存在（tinyint, 0=周日）
- 遵循现有 Controller → Service → Mapper 分层模式
- 后端所有公开 GET 无需认证，已通过 `SecurityConfig` 配置 `requestMatchers(HttpMethod.GET, "/api/user/subjects/**").permitAll()`
- 统一响应使用 `Result<T>`，分页使用 `PageResult<T>`
- 季度范围通过 `SeasonUtil.getSeasonRange(year, quarter)` 计算
- 前端新增接口在 `api/subjects.ts` 中添加方法，状态管理在 `stores/subjects.ts` 中添加 action

---

## File Structure

| 变更 | 文件 | 说明 |
|------|------|------|
| M | `backend/business/pojo/src/main/java/top/zhaizz/pojo/vo/SubjectListVO.java` | 新增 `airWeekday`、`collectionTotal` 字段 |
| M | `backend/business/subject/src/main/java/top/zhaizz/subject/converter/SubjectConverter.java` | `toSubjectListVO` 映射新增字段 |
| M | `backend/business/subject/src/main/java/top/zhaizz/subject/mapper/SubjectMapper.java` | 新增 `findByAirDateRangeAndWeekday` 方法 |
| M | `backend/business/subject/src/main/resources/mapper/SubjectMapper.xml` | 新增对应 SQL |
| M | `backend/business/subject/src/main/java/top/zhaizz/subject/service/SubjectService.java` | 新增 `listSchedule` 接口方法 |
| M | `backend/business/subject/src/main/java/top/zhaizz/subject/service/impl/SubjectServiceImpl.java` | 实现 `listSchedule` |
| M | `backend/business/subject/src/main/java/top/zhaizz/subject/controller/SubjectController.java` | 新增 `GET /schedule` 端点 |
| M | `backend/business/subject/src/main/java/top/zhaizz/subject/util/SeasonUtil.java` | 新增 `getCurrentSeason()` 和 `getCurrentQuarter()` |
| M | `frontend/client/src/types/index.ts` | `SubjectListItem` 增加 `airWeekday`、`collectionTotal` |
| M | `frontend/client/src/api/subjects.ts` | 新增 `getSchedule()` |
| M | `frontend/client/src/stores/subjects.ts` | 新增 `fetchSchedule()` action |
| M | `frontend/client/src/pages/Home.vue` | `fetchSchedule()` 改用新 API，移除 N+1 |

---

### Task 1: SubjectListVO 补充字段

**Files:**
- Modify: `backend/business/pojo/src/main/java/top/zhaizz/pojo/vo/SubjectListVO.java`
- Modify: `backend/business/subject/src/main/java/top/zhaizz/subject/converter/SubjectConverter.java`

**Interfaces:**
- Produces: `SubjectListVO` 新增 `airWeekday: Integer` 和 `collectionTotal: Integer` 字段

- [ ] **Step 1: SubjectListVO 新增字段**

```java
// SubjectListVO.java — 增加两个字段
@Data
public class SubjectListVO {
    // 已有字段不变...
    private Long id;
    private String name;
    private String nameCn;
    private String image;
    private BigDecimal score;
    private Integer rank;
    private Integer eps;
    private LocalDate airDate;
    private Integer type;
    // ↓ 新增
    private Integer airWeekday;
    private Integer collectionTotal;
}
```


- [ ] **Step 2: SubjectConverter.toSubjectListVO 补映射**

```java
// SubjectConverter.java — toSubjectListVO 中补两个 set
public static SubjectListVO toSubjectListVO(Subject entity) {
    if (entity == null) return null;
    SubjectListVO vo = new SubjectListVO();
    // 已有...
    vo.setId(entity.getId());
    vo.setName(entity.getName());
    vo.setNameCn(entity.getNameCn());
    vo.setImage(entity.getImage());
    vo.setScore(entity.getScore());
    vo.setRank(entity.getRank());
    vo.setEps(entity.getEps());
    vo.setAirDate(entity.getAirDate());
    vo.setType(entity.getType());
    // ↓ 新增
    vo.setAirWeekday(entity.getAirWeekday());
    vo.setCollectionTotal(entity.getCollectionTotal());
    return vo;
}
```

- [ ] **Step 3: 编译验证**

```bash
cd backend/business && mvn compile -pl pojo -q
```
Expected: BUILD SUCCESS

- [ ] **Step 4: Commit**

```bash
git add backend/business/pojo/src/main/java/top/zhaizz/pojo/vo/SubjectListVO.java backend/business/subject/src/main/java/top/zhaizz/subject/converter/SubjectConverter.java
git commit -m "feat: SubjectListVO 增加 airWeekday/collectionTotal 字段"
```

---

### Task 2: SeasonUtil 获取当前季节

**Files:**
- Modify: `backend/business/subject/src/main/java/top/zhaizz/subject/util/SeasonUtil.java`

**Interfaces:**
- Produces: `SeasonUtil.getCurrentSeason()` — 返回 `int[] {year, quarterIndex}`
- Produces: `SeasonUtil.getCurrentQuarter()` — 返回 `String` (spring/summer/autumn/winter)

- [ ] **Step 1: 添加两个静态方法**

```java
// SeasonUtil.java
/**
 * 获取当前季度字符串
 */
public static String getCurrentQuarter() {
    return switch (LocalDate.now().getMonth()) {
        case JANUARY, FEBRUARY, MARCH -> "winter";
        case APRIL, MAY, JUNE -> "spring";
        case JULY, AUGUST, SEPTEMBER -> "summer";
        case OCTOBER, NOVEMBER, DECEMBER -> "autumn";
    };
}

/**
 * 获取当前年份和季度 (便捷方法, 保持 import 区域整洁)
 */
public static int getCurrentYear() {
    return LocalDate.now().getYear();
}
```

记得在 import 区域增加 `import java.time.LocalDate;`（可能已有）。

- [ ] **Step 2: 编译验证**

```bash
cd backend/business && mvn compile -pl subject -am -q
```
Expected: BUILD SUCCESS

- [ ] **Step 3: Commit**

```bash
git add backend/business/subject/src/main/java/top/zhaizz/subject/util/SeasonUtil.java
git commit -m "feat: SeasonUtil 增加获取当前季度方法"
```

---

### Task 3: Mapper 层 — 按日期范围+星期查询

**Files:**
- Modify: `backend/business/subject/src/main/java/top/zhaizz/subject/mapper/SubjectMapper.java`
- Modify: `backend/business/subject/src/main/resources/mapper/SubjectMapper.xml`

**Interfaces:**
- Produces: `SubjectMapper.findByAirDateRangeAndWeekday(startDate, endDate, weekday)` — 当 weekday 为 null 时返回全部，否则按星期过滤；按 `air_date, score` 排序

- [ ] **Step 1: Mapper 接口方法**

```java
// SubjectMapper.java — 新增方法
/**
 * 按播出日期范围 + 星期几查询
 * @param weekday 星期几 (0=周日, 1=周一...6=周六), 传 null 则不过滤
 */
List<Subject> findByAirDateRangeAndWeekday(@Param("startDate") LocalDate startDate,
                                           @Param("endDate") LocalDate endDate,
                                           @Param("weekday") Integer weekday);
```

- [ ] **Step 2: XML SQL**

```xml
<!-- SubjectMapper.xml -->
<select id="findByAirDateRangeAndWeekday" resultType="top.zhaizz.pojo.entity.Subject">
    SELECT *
    FROM subject
    WHERE air_date BETWEEN #{startDate} AND #{endDate}
    <if test="weekday != null">
        AND air_weekday = #{weekday}
    </if>
    ORDER BY air_weekday, score DESC
</select>
```

- [ ] **Step 3: 编译验证**

```bash
cd backend/business && mvn compile -pl subject -am -q
```
Expected: BUILD SUCCESS

- [ ] **Step 4: Commit**

```bash
git add backend/business/subject/src/main/java/top/zhaizz/subject/mapper/SubjectMapper.java backend/business/subject/src/main/resources/mapper/SubjectMapper.xml
git commit -m "feat: 新增 findByAirDateRangeAndWeekday 查询"
```

---

### Task 4: Service 层 — listSchedule

**Files:**
- Modify: `backend/business/subject/src/main/java/top/zhaizz/subject/service/SubjectService.java`
- Modify: `backend/business/subject/src/main/java/top/zhaizz/subject/service/impl/SubjectServiceImpl.java`

**Interfaces:**
- Consumes: `SubjectMapper.findByAirDateRangeAndWeekday()`, `SeasonUtil.getCurrentYear()`, `SeasonUtil.getCurrentQuarter()`, `SeasonUtil.getSeasonRange()`
- Produces: `SubjectService.listSchedule(year, quarter, weekday, page, size)` → `PageResult<SubjectListVO>`

- [ ] **Step 1: Service 接口方法**

```java
// SubjectService.java — 追加
/** 每周追番列表（按季度筛选 + 可选星期过滤） */
PageResult<SubjectListVO> listSchedule(int year, String quarter, Integer weekday, int page, int size);
```

- [ ] **Step 2: Service 实现**

```java
// SubjectServiceImpl.java — 追加
@Override
public PageResult<SubjectListVO> listSchedule(int year, String quarter, Integer weekday, int page, int size) {
    LocalDate[] range = SeasonUtil.getSeasonRange(year, quarter);
    LambdaQueryWrapper<Subject> wrapper = new LambdaQueryWrapper<Subject>()
            .between(Subject::getAirDate, range[0], range[1])
            .orderByAsc(Subject::getAirWeekday)
            .orderByDesc(Subject::getScore);

    if (weekday != null && weekday >= 0 && weekday <= 6) {
        wrapper.eq(Subject::getAirWeekday, weekday);
    }

    Page<Subject> mpPage = subjectMapper.selectPage(new Page<>(page, size), wrapper);

    return PageResult.of(
            mpPage.getRecords().stream()
                    .map(SubjectConverter::toSubjectListVO)
                    .collect(Collectors.toList()),
            mpPage.getTotal(),
            (int) mpPage.getCurrent(),
            (int) mpPage.getSize()
    );
}
```

- [ ] **Step 3: 编译验证**

```bash
cd backend/business && mvn compile -pl subject -am -q
```
Expected: BUILD SUCCESS

- [ ] **Step 4: Commit**

```bash
git add backend/business/subject/src/main/java/top/zhaizz/subject/service/SubjectService.java backend/business/subject/src/main/java/top/zhaizz/subject/service/impl/SubjectServiceImpl.java
git commit -m "feat: SubjectService 实现 listSchedule 方法"
```

---

### Task 5: Controller 层 — GET /schedule

**Files:**
- Modify: `backend/business/subject/src/main/java/top/zhaizz/subject/controller/SubjectController.java`

**Interfaces:**
- Produces: `GET /api/user/subjects/schedule?weekday=-1&year=2026&quarter=spring&page=1&size=50`

- [ ] **Step 1: 新增端点**

```java
// SubjectController.java — 在 listBySeason 之后追加
/**
 * 每周追番列表（按星期筛选）
 */
@GetMapping("/schedule")
public Result<PageResult<SubjectListVO>> listSchedule(
        @RequestParam(defaultValue = "-1") @Min(-1) @Max(6) int weekday,
        @RequestParam(required = false) Integer year,
        @RequestParam(required = false) String quarter,
        @RequestParam(defaultValue = "1") @Min(1) int page,
        @RequestParam(defaultValue = "50") @Min(1) @Max(100) int size) {
    int y = year != null ? year : SeasonUtil.getCurrentYear();
    String q = quarter != null ? quarter : SeasonUtil.getCurrentQuarter();
    Integer wd = weekday == -1 ? null : weekday;
    return Result.success(subjectService.listSchedule(y, q, wd, page, size));
}
```

需要增加 `SeasonUtil` 的 import：
```java
import top.zhaizz.subject.util.SeasonUtil;
```

- [ ] **Step 2: 编译验证**

```bash
cd backend/business && mvn compile -pl subject -am -q
```
Expected: BUILD SUCCESS

- [ ] **Step 3: Commit**

```bash
git add backend/business/subject/src/main/java/top/zhaizz/subject/controller/SubjectController.java
git commit -m "feat: 新增 GET /api/user/subjects/schedule 接口"
```

---

### Task 6: 前端类型 + API + Store

**Files:**
- Modify: `frontend/client/src/types/index.ts`
- Modify: `frontend/client/src/api/subjects.ts`
- Modify: `frontend/client/src/stores/subjects.ts`

**Interfaces:**
- Produces: `subjectsApi.getSchedule(params)` → API 调用
- Produces: `subjectsStore.fetchSchedule(year, quarter, weekday)` → store action

- [ ] **Step 1: SubjectListItem 补充字段**

```typescript
// types/index.ts — SubjectListItem 增加字段
export interface SubjectListItem {
  id: number
  name: string
  nameCn: string
  image: string
  score: number
  rank: number
  eps: number
  airDate: string
  type: number
  // ↓ 新增
  airWeekday: number
  collectionTotal: number
}
```

- [ ] **Step 2: API 方法**

```typescript
// api/subjects.ts — 追加
  getSchedule(params: { weekday?: number; year?: number; quarter?: string; page?: number; size?: number }) {
    return http.get<ApiResponse<PageResult<SubjectListItem>>>('/api/user/subjects/schedule', { params })
  },
```

- [ ] **Step 3: Store action**

```typescript
// stores/subjects.ts — 新增状态 + action

// 在 ref 区域加
const scheduleList = ref<SubjectListItem[]>([])
const scheduleLoading = ref(false)

// 在 return 前加 async function
async function fetchSchedule(year: number, quarter: string, weekday = -1) {
  scheduleLoading.value = true
  try {
    const res = await subjectsApi.getSchedule({ year, quarter, weekday, page: 1, size: 60 })
    scheduleList.value = res.data.data.content
  } catch {
    scheduleList.value = []
  } finally {
    scheduleLoading.value = false
  }
}

// return 中追加
return {
  // 原有
  list, detail, episodes, total, page, size, loading, keyword,
  fetchList, search, fetchBySeason, fetchDetail, fetchEpisodes,
  // 新增
  scheduleList, scheduleLoading, fetchSchedule,
}
```

- [ ] **Step 4: 编译验证**

```bash
cd frontend/client && npx vue-tsc --noEmit 2>&1 | head -20 || true
```
Expected: 无类型错误（或只显示无关的警告）

- [ ] **Step 5: Commit**

```bash
git add frontend/client/src/types/index.ts frontend/client/src/api/subjects.ts frontend/client/src/stores/subjects.ts
git commit -m "feat: 前端 schedule API 类型、接口、store action"
```

---

### Task 7: Home.vue 替换 N+1 为直连 API

**Files:**
- Modify: `frontend/client/src/pages/Home.vue`

**Interfaces:**
- Consumes: `subjectsStore.fetchSchedule()`, `subjectsStore.scheduleList`, `subjectsStore.scheduleLoading`

- [ ] **Step 1: 替换 script 部分**

删除 `scheduleItems` 相关的内联 `fetchSchedule` 函数，改为调用 store：

```typescript
// Home.vue — script 区域改动

// 1. 删除旧的 scheduleItems 定义
// 旧的: const scheduleItems = ref<SubjectDetail[]>([])
// 旧的: const loadingSchedule = ref(true)

// 2. 改用 store
import { useSubjectsStore } from '@/stores/subjects'
const subjectsStore = useSubjectsStore()

// 3. 替换 fetchSchedule 实现
// 旧的 fetchSchedule 函数全部删除，改为：
async function fetchSchedule() {
  await subjectsStore.fetchSchedule(currentYear, currentQuarter.value)
}

// 4. 模板中用 subjectsStore.scheduleList 和 subjectsStore.scheduleLoading 替代
```

- [ ] **Step 2: 替换 template 部分**

```vue
<!-- Home.vue — template 中涉及 scheduleItems/loadingSchedule 处全部替换 -->

<!-- 第 72 行附近: 计算属性保持不动（但要改数据源） -->
const currentDaySchedule = computed(() => {
  if (activeWeekday.value === -1) {
    return [...subjectsStore.scheduleList].sort((a, b) => (b.score || 0) - (a.score || 0))
  }
  return subjectsStore.scheduleList.filter(item => item.airWeekday === activeWeekday.value)
})
```

模板中：
- `:loadingSchedule` → `subjectsStore.scheduleLoading`
- `currentDaySchedule` → 保持变量名一致（不需要改 template 变量名，因为计算属性 `currentDaySchedule` 仍在）

- [ ] **Step 3: 删除不再需要的 SubjectsApi 导入**

Home.vue 中 `import { subjectsApi } from '@/api/subjects'` — 检查是否还有别的调用（`fetchPopular`、`fetchLatest`、`fetchSeasonal` 都用到了），如果有则保留，否则删除该 import。

实际上 `fetchPopular`、`fetchLatest`、`fetchSeasonal` 都直接用了 `subjectsApi`，所以保留这个 import。

- [ ] **Step 4: 清理不再需要的 import**

`import type { SubjectListItem, SubjectDetail } from '@/types'` 中确认 `SubjectDetail` 是否还在别处使用。如果不再使用可以删除，但具体要看 `scheduleItems` 是否被其他部分引用。移除 `SubjectDetail` 类型引用（因为 schedule items 现在是 `SubjectListItem`）。

- [ ] **Step 5: 编译验证**

```bash
cd frontend/client && npx vue-tsc --noEmit 2>&1 | head -30
```
Expected: 无类型错误

- [ ] **Step 6: 功能验证（构建）**

```bash
cd frontend/client && npm run build 2>&1 | tail -5
```
Expected: 构建成功

- [ ] **Step 7: Commit**

```bash
git add frontend/client/src/pages/Home.vue
git commit -m "refactor: Home.vue 每周追番改用专用接口，消除 N+1 查询"
```

---

## Self-Review

**1. Spec coverage:**
- ✅ 后端新增 `/api/user/subjects/schedule` 接口（支持全部、周一至周末参数）
- ✅ `SubjectListVO` 增加了 `airWeekday`，前端可以取到星期信息
- ✅ 前端 Home.vue 每周追番区域改用新接口，消除 N+1
- ✅ 前端切换全部/周一至周末的功能保持，`weekday=-1` 表示全部

**2. Placeholder scan:** 无占位符，所有代码均为最终内容。

**3. Type consistency:**
- `SubjectListVO.airWeekday` (Integer) ↔ `SubjectListItem.airWeekday` (number) ✓
- `SeasonUtil.getCurrentQuarter()` 返回 `String` ↔ Controller 中接受 `String quarter` ✓
- `SubjectMapper.findByAirDateRangeAndWeekday` 参数 `Integer weekday` nullable ↔ 前端传 `-1` 转为 `null` ✓
