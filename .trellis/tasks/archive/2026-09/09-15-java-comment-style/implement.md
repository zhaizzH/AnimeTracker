# 执行计划

## 当前停点
completed：规范与检查器回归已完成，主体提交为 3861752b；任务已归档，复核发现的示例和状态记录遗漏已修正

## 执行步骤
1. 收到明确实施批准后复核工作区，读取 PRD/design/上下文，执行 task.py start
2. 更新 quality-guidelines.md 的措辞、首句、标签和 Java 示例；保留普通文档正文标点，必要时同步 backend/index.md
3. 增加检查器无句号合法样例及兼容性回归；除非证明存在不兼容，不修改核心扫描器
4. 验证并人工核对必要契约未丢失，记录结果
5. 按后续授权提交与归档；存量注释批量整理单独开展

## 验证命令（仓库根目录）
```powershell
python backend/business/tools/test_check_javadoc.py
mvn -B clean test -f backend/business/pom.xml
python backend/business/tools/check_javadoc.py
git diff --check
python .trellis/scripts/task.py validate .trellis/tasks/archive/2026-09/09-15-java-comment-style
```
Maven 构建为完整 doclint 提供真实依赖类路径，随后检查声明与 Javadoc 语法。人工审查说明、标签、空值和单位，不用机械通过代替语义审查，不沿用历史测试数量

## 完成记录
- 删除末尾句号要求，补齐类型、字段、方法标签和方法体注释示例
- 检查器 7 项回归通过，主体实现阶段 Business clean test 与声明/doclint 检查通过
- 复核修正停点记录，归档后上下文校验通过
- 本任务直接在 main 完成，未创建 PR；归档使用 --skip-branch-validation
