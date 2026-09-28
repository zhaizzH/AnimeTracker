# Technical Design: Remove Lombok from Java Business

## Scope and boundaries

The migration covers the complete `backend/business` Java 21 / Spring Boot 3.2 Maven reactor: `common`, `pojo`, `infrastructure`, `auth`, `log`, `agent`, `client`, `admin`, and `app`. `backend/agent` is the separate Python service and is excluded. Repository discovery found 150 production Java files with Lombok imports, 214 Lombok annotation usages (including five `@Builder.Default` annotations), 197 import statements, no test-source Lombok usage, Lombok dependencies in the root reactor and each child POM, and a Lombok row in `backend/business/README.md`.

This is a behavior-preserving source rewrite, not a DTO redesign or application refactor. Keep the current class types, mutability, field types, validation/Jackson/MyBatis/Spring annotations, property names, API shapes, database mappings, business logic, and existing logging statements. No replacement annotation processor or code-generation dependency will be introduced.

## Replacement strategy

### Data and configuration types

For every entity and other mutable `@Data` type, write explicit JavaBeans getters and setters for the same fields; do not rely on implicit access, MyBatis reflection, or framework field access as a substitute. Preserve generated names, types, visibility, and primitive/boxed boolean accessor naming, and implement Lombok-equivalent `equals`, `hashCode`, and `toString` semantics. Match the applicable superclass behavior: Lombok `@Data` equality normally compares the class's own fields, while `SubjectDetailVO` explicitly opts into parent fields through `@EqualsAndHashCode(callSuper = true)`. Preserve current `toString` output semantics, including current sensitive-field inclusion; changing redaction is a separate security decision, not part of this migration.

For getter-only types (`Result`, `ErrorType`, `UserPrincipal`), retain only the accessors Lombok currently creates. For `PageResult`, retain read accessors and mutable setters. Do not replace mutable DTOs/entities/configuration beans with records or immutable types. Keep all validation/Jackson/MyBatis annotations on their current targets and fields.

### Constructors and dependency injection

Replace constructor annotations with explicit constructors having the same generated signature, visibility, and field order. `@RequiredArgsConstructor` must include final and Lombok-`@NonNull` fields that are not initialized, with matching null checks if applicable. Preserve explicitly called all-args/no-args constructors, including positional calls such as `SubjectRelationVO` construction, and the existing constructor overloads in `UserPrincipal`. Spring's single-constructor injection behavior must remain unchanged.

### Builders and defaults

Implement static builder APIs for Lombok `@Builder` types with the same entry-point name, fluent property methods, and `build()` result. Preserve public visibility and nested builder names/signatures. For each `@Builder.Default`, distinguish an omitted property from an explicitly supplied `null`; omitted values use the same fresh default value as Lombok, while explicit null stays null. Preserve class field initializers for no-argument construction independently of builder defaults. Keep existing factory methods and call sites unchanged unless generated API equivalence requires a mechanical update, which must be justified and covered.

### Logging and null contracts

Replace each `@Slf4j` field with an explicit `private static final org.slf4j.Logger log = org.slf4j.LoggerFactory.getLogger(CurrentClass.class);` (or exact class literal for nested types), retaining logger name, level, message, placeholders, and calls. Keep Spring/Jakarta annotations such as Spring `@NonNull`; remove only actual `lombok.*` imports and annotations. Reproduce Lombok-generated null-check behavior only for actual Lombok `@NonNull` use; source inventory indicates no Lombok `@NonNull` import was found.

### Dependency removal

Remove every Lombok dependency/reference from the parent and all nine child POMs: delete the managed artifact/version and each direct module dependency. Remove the Business README dependency-table entry. Do not change unrelated dependency scopes or versions. A broad source/config/documentation search must confirm no Lombok dependency reference remains in the Business backend; the task's own PRD/design/research may describe Lombok for audit purposes.

## Compatibility surfaces and checks

- Jackson and Redis: preserve bean constructors/accessors, JSON property names, `NON_NULL` behavior, booleans, builder defaults, and `ProgressPreviewSnapshot` round-trip behavior used by `ProgressPreviewStore`.
- Spring configuration: retain mutable JavaBeans accessors and no-arg construction for `AgentProperties`, `CorsProperties`, `AuthCookieProperties`, and `MinioProperties`; continue using the existing configuration binding tests.
- Validation: keep field and container-element constraint placement on DTOs; exercise invalid field/list-member cases where affected behavior is not already asserted.
- MyBatis: preserve mutable entity bean accessors, constructors, and all mapping annotations including the escaped `Subject.rank` mapping; retain entity alias tests.
- API and builders: preserve builder use in evidence, lexical-search, wishlist, and collection-progress paths; preserve response JSON shapes and explicit constructor call signatures.
- Equality/string behavior: characterize representative `@Data` behavior and the `SubjectDetailVO` superclass contract; ensure generated string behavior isn't silently changed during this compatibility task.
- Javadocs: handwritten declarations follow `.trellis/spec/backend/quality-guidelines.md`; do not blindly stamp repetitive prose. Existing checker commands are part of acceptance.

## Risks and trade-offs

The rewrite is broad and repetitive, so accidental signature drift, omitted fields, changed boolean getter names, builder null/default differences, or missing annotation targets are the main risks. The largest behavioral concentrations are the `pojo` DTO/VO/entity set, constructor-injected Spring classes, and builders in collection progress/evidence flows. Mutable all-field equality/hash/string behavior from `@Data` may be undesirable in a future cleanup, especially password inclusion in `User.toString()`, but changing those semantics here would mix a security/product decision with a dependency-removal task. Preserve behavior now and track any redaction/identity redesign separately if later requested.

## Rollback

Revert only this task's Lombok-expansion, test, documentation, and POM edits. Do not restore unrelated pre-existing worktree content or alter database/Redis data. Since Lombok dependencies are removed only after source expansion is complete, the POM cleanup is the final migration stage; reverting the task restores a coherent prior Lombok-backed build.