# 修复后端 Java 注释规范

## 目标

按自然中文注释规范清理 backend/business Java 注释末尾句号，保持声明契约、标签、字符串和业务行为不变，并通过全量 Javadoc 与 Maven 校验

## 需求

- 扫描 backend/business 下全部 Java 源码，覆盖 main、test 和 tools
- 将中文注释行末的句号改为自然表达；保留多句说明的句间标点、代码、URL、版本号中的点号和所有 Javadoc 标签语义
- 不修改字符串字面量、业务逻辑、接口签名、异常行为和非注释文本
- 保持现有检查器对声明覆盖、标签匹配、中文摘要、机械模板和 doclint 的约束
- 记录实际修改范围和验证结果，按 Trellis 任务完成并提交

## 验收标准

- [x] 全量 Java 注释扫描不再报告中文说明行末句号，代码值和字符串保持不变
- [x] Javadoc 检查器通过，声明、参数、返回值和异常标签无新增违规
- [x] Business Maven 测试通过
- [x] 任务记录包含范围、验证命令和提交信息

## 范围外

不迁移 Python、前端注释，不改注释内容语义，不新增检查器硬门禁，不调整模块职责或业务实现

## 实施记录

- 更新 255 个 Java 文件，删除 1635 处注释行末中文句号
- 基线重放核对修改边界，未触碰字符串、代码、接口签名或 Javadoc 标签结构
- python backend/business/tools/test_check_javadoc.py：7 项通过
- python backend/business/tools/check_javadoc.py：255 个文件、1658 个声明、0 违规；声明检查和 doclint 均通过
- mvn -B clean test -f backend/business/pom.xml：10 个模块构建成功，测试全部通过
- git diff --check：通过
