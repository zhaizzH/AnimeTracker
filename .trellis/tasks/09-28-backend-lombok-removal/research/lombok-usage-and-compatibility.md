# Backend Lombok Usage and Compatibility Research

## Scope inventory

Inspection of the current repository found Lombok usage only in the Java Maven reactor `backend/business`; the separate Python service `backend/agent` and frontend are outside scope. No Lombok imports/annotations were found in backend test sources, generated/vendor Java, or a Lombok configuration file.

| Module | Production Java files importing Lombok |
|---|---:|
| `pojo` | 83 |
| `client` | 32 |
| `admin` | 11 |
| `auth` | 4 |
| `infrastructure` | 5 |
| `log` | 3 |
| `agent` | 4 |
| `app` | 4 |
| `common` | 4 |
| **Total** | **150** |

There are 197 Lombok import statements and 214 Lombok annotation usages including nested types and the five `@Builder.Default` field annotations. Annotation usage counts: `@Data` 100; `@Builder` 13 plus `@Builder.Default` 5; `@NoArgsConstructor` 16; `@AllArgsConstructor` 18; `@RequiredArgsConstructor` 45; `@Getter` 5; `@Setter` 1; `@Slf4j` 10; `@EqualsAndHashCode` 1. The import total is 197 because some source files import multiple Lombok annotations.

Build/documentation references occur in the parent `backend/business/pom.xml`, all nine module POMs, and the dependency table in `backend/business/README.md`. No explicit Lombok compiler plugin or annotation processor configuration was found. Remove the dependency management/version and all child declarations only after replacing generated source behavior.

## Compatibility examples

- `backend/business/pojo/src/main/java/top/zhaizz/pojo/vo/collection/CollectionProgressExecutionVO.java`: `@Data`, `@Builder`, no/all-args constructors, Jackson `NON_NULL`, three `@Builder.Default` list fields. For builders, omitted values must get fresh empty lists; explicitly supplied null must remain null. No-arg construction uses field initializers independently.
- `backend/business/pojo/src/main/java/top/zhaizz/pojo/vo/collection/CollectionProgressPreviewVO.java` and `backend/business/client/src/main/java/top/zhaizz/client/model/ProgressPreviewSnapshot.java`: list builder defaults; the snapshot is serialized to Redis by `ProgressPreviewStore`, so bean construction/accessors and JSON round-trip matter.
- `backend/business/pojo/src/main/java/top/zhaizz/pojo/vo/evidence/EvidenceCandidateVO.java`: outer and nested data classes use builders and constructors; `EvidenceConverter` builds nested credit/character/relation items and outer VO.
- `backend/business/pojo/src/main/java/top/zhaizz/pojo/vo/collection/WishlistAddResultVO.java`: builder and `NON_NULL`, with static factory methods using the builder.
- `backend/business/pojo/src/main/java/top/zhaizz/pojo/vo/subject/SubjectDetailVO.java`: `@EqualsAndHashCode(callSuper = true)` means equality/hash includes inherited `SubjectListVO` properties.
- `backend/business/pojo/src/main/java/top/zhaizz/pojo/vo/subject/SubjectRelationVO.java`: an explicit positional constructor call exists in `client/converter/SubjectConverter.java`; retain constructor signature/order and no-arg construction.
- `backend/business/pojo/src/main/java/top/zhaizz/pojo/entity/User.java`: mutable entity with `@Data`; generated `toString()` includes all fields including password unless behavior changes. Treat redaction as a separate decision.
- `AgentProperties`, `CorsProperties`, `AuthCookieProperties`, and `MinioProperties` are mutable `@ConfigurationProperties` beans; preserve no-arg construction and JavaBeans accessors for Spring binding.
- DTO field-level Bean Validation annotations (including collection element constraints) must not move or change target. MyBatis entity accessors and mapping annotations, including the escaped `Subject.rank` mapping, remain in place.
- Ten `@Slf4j` classes use a generated field named `log`; explicit SLF4J loggers should preserve class category, field name, level, message, and placeholders.
- `JwtAuthenticationFilter` uses `org.springframework.lang.NonNull`, not Lombok `@NonNull`; keep that framework annotation and import.

## Existing test/build checks

Existing tests already exercise builder use, positional/no-arg/all-args constructors, config-property binding, entity alias registration, and converters. Relevant files include `client/src/test/java/top/zhaizz/client/controller/EvidenceControllerTest.java`, `client/src/test/java/top/zhaizz/client/service/impl/EvidenceServiceImplTest.java`, `client/src/test/java/top/zhaizz/client/service/impl/AuthServiceImplTest.java`, `app/src/test/java/top/zhaizz/app/config/AppConfigurationBindingTest.java`, and `app/src/test/java/top/zhaizz/app/config/MyBatisEntityAliasTest.java`. Reuse them and add characterization only where generated semantics are not already proven.

The reactor command for validation is `mvn -B clean test -f backend/business/pom.xml`. The existing project-wide Java declaration/documentation checks are `python backend/business/tools/check_javadoc.py` and `python backend/business/tools/test_check_javadoc.py`.

## Recommended focused coverage

1. Verify representative `@Data` equality/hash/toString semantics, including `SubjectDetailVO` parent fields; deliberately keep sensitive values within current behavior for this task.
2. Verify constructors and accessor names/types through existing tests plus reflection/JavaBeans checks where generated names are ambiguous, particularly primitive `is...` versus boxed `get...` methods.
3. For each builder default, assert omitted value receives the right new default and explicit null remains null; separately assert no-arg initialization.
4. Round-trip `ProgressPreviewSnapshot` through the configured Jackson mapper and assert expected property names, boolean fields, and `NON_NULL` response serialization.
5. Retain Spring property binding and MyBatis entity alias/mapping tests; exercise any unrepresented fields whose source accessors change.

## Source evidence and references

- `.trellis/spec/backend/index.md` and `.trellis/spec/backend/directory-structure.md`: Java Business module boundaries.
- `.trellis/spec/backend/quality-guidelines.md`: Java handwritten-member Javadocs and checker commands.
- `.trellis/spec/backend/database-guidelines.md`: MyBatis entity mapping conventions.
- `backend/business/pom.xml` and module POMs: dependency management and module dependency declarations.
