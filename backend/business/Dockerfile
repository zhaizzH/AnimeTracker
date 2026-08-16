# ===================================================================
# AnimeTracker Business — 多阶段构建
# 构建: maven 3.9 + Temurin 21 (JDK)
# 运行: eclipse-temurin 21 (JRE, 非 root)
# ===================================================================
FROM maven:3.9-eclipse-temurin-21 AS builder

WORKDIR /build

# 先复制 pom 与源码,利用 Maven 依赖层缓存(依赖不变时跳过重复下载)
COPY pom.xml ./
COPY common/pom.xml common/pom.xml
COPY pojo/pom.xml pojo/pom.xml
COPY admin/pom.xml admin/pom.xml
COPY client/pom.xml client/pom.xml
COPY agent/pom.xml agent/pom.xml
COPY app/pom.xml app/pom.xml
COPY common/src common/src
COPY pojo/src pojo/src
COPY admin/src admin/src
COPY client/src client/src
COPY agent/src agent/src
COPY app/src app/src

# 离线 resolve 依赖以缓存;失败不阻塞(镜像构建时需联网拉取公共依赖)
RUN mvn -q -pl app -am dependency:go-offline -B || true

RUN mvn -pl app -am package -DskipTests -B -DfinalName=app

# ---------- 运行阶段 ----------
FROM eclipse-temurin:21-jre

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r app && useradd -r -g app -d /app app

WORKDIR /app
COPY --from=builder /build/app/target/app.jar /app/app.jar

USER app
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8080/actuator/health/liveness || exit 1

ENTRYPOINT ["java", "-jar", "/app/app.jar"]
