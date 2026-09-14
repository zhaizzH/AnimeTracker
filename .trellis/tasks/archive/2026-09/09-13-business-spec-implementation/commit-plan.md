# 剩余修复提交计划

建议一次提交：`fix(business): 完成规范复核缺陷修复与文档校验`。

本次只包含下列已检查文件；不修改既有提交，不推送。

- backend/business/agent/src/main/java/top/zhaizz/agent/gateway/HttpImportAgentGateway.java
- backend/business/agent/src/test/java/top/zhaizz/agent/gateway/HttpImportAgentGatewayTest.java
- backend/business/app/src/main/java/top/zhaizz/app/config/CorsConfig.java
- backend/business/app/src/main/java/top/zhaizz/app/config/SecurityConfig.java
- backend/business/tools/CheckJavadoc.java
- backend/business/tools/check_javadoc.py
- backend/business/tools/test_check_javadoc.py
- .trellis/spec/backend/index.md
- .trellis/spec/backend/quality-guidelines.md
- .trellis/tasks/09-13-business-spec-implementation/implement.md
- .trellis/tasks/09-13-business-spec-implementation/review.md
- .trellis/tasks/09-13-business-spec-implementation/javadoc-check.txt
- .trellis/tasks/09-13-business-spec-implementation/javadoc-run.txt
- .trellis/tasks/09-13-business-spec-implementation/commit-plan.md

验证：完整 Maven 95 tests passed；AST 255 files / 1658 declarations / 0 violations；JDK doclint 0；检查器 6 个回归测试通过；git diff --check 通过。

未识别的其他脏文件：无。提交需用户一次确认；归档与日志按提交后的 Trellis 收尾流程处理。
