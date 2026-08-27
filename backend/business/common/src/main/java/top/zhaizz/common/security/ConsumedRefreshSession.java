package top.zhaizz.common.security;

/** 已原子消费的 refresh session 元数据。 */
public record ConsumedRefreshSession(Long userId, long startedAtEpochMs) {
}