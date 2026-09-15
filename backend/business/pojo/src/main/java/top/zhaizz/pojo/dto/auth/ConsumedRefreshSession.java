package top.zhaizz.pojo.dto.auth;

/**
 * 已原子消费的刷新凭据元数据，仅用于内部续签
 * @param userId 凭据所属用户 ID
 * @param startedAtEpochMs 原始登录时间，UTC 纪元毫秒；刷新不得重置
 */
public record ConsumedRefreshSession(Long userId, long startedAtEpochMs) {
}
