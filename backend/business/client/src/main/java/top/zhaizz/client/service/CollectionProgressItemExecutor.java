package top.zhaizz.client.service;

import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;
import top.zhaizz.client.mapper.CollectionProgressMapper;
import top.zhaizz.common.constant.ErrorType;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.pojo.entity.UserCollection;
import top.zhaizz.pojo.vo.collection.CollectionProgressItemVO;

import java.time.LocalDateTime;

/**
 * 收藏进度单项独立事务执行器
 * <p>
 * 独立 @Service 避免同类内部调用绕过 Spring 代理，确保每部番剧 REQUIRES_NEW 独立事务、允许部分成功。
 */
@Service
@RequiredArgsConstructor
public class CollectionProgressItemExecutor {

    private final CollectionProgressMapper collectionMapper;

    /**
     * 单项进度更新：SQL 再次约束 userId/subjectId/type=3/原进度，确认后并发修改不被覆盖
     */
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void update(Long userId, CollectionProgressItemVO item) {
        int affected = collectionMapper.update(null,
                Wrappers.<UserCollection>lambdaUpdate()
                        .eq(UserCollection::getUserId, userId)
                        .eq(UserCollection::getSubjectId, item.getSubjectId())
                        .eq(UserCollection::getType, 3)
                        .eq(UserCollection::getEpStatus, item.getCurrentEpStatus())
                        .set(UserCollection::getEpStatus, item.getTargetEpStatus())
                        .set(UserCollection::getUpdatedAt, LocalDateTime.now()));
        if (affected != 1) {
            throw new BizException(ErrorType.CONFLICT, "收藏进度已发生变化");
        }
    }
}
