# 执行计划

1. [x] 完成任务启动前规范读取和候选注释统计
2. [x] 分批修复 Java 注释末尾句号，优先 main 源码，再处理测试和工具
3. [x] 复核字符串、URL、版本号、Javadoc 标签和多句说明未被误改
4. [x] 运行 Javadoc 检查器、Business Maven 测试、差异检查和 Trellis 校验
5. [x] 更新任务记录并按工作流提交代码和收尾 bookkeeping

## 实际结果

- 255 个 Java 文件共删除 1635 处注释行末中文句号
- 全量 Javadoc 检查、7 项检查器回归和 Business Maven clean test 通过
- 代码里程碑已提交为 ef8775b，任务进入归档收尾

## 验证命令

python backend/business/tools/test_check_javadoc.py
python backend/business/tools/check_javadoc.py
mvn -B clean test -f backend/business/pom.xml
git diff --check
python .trellis/scripts/task.py validate .trellis/tasks/09-15-backend-java-comment-migration

