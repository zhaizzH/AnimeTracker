package top.zhaizz.client.service;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;
import top.zhaizz.client.mapper.CollectionMapper;
import top.zhaizz.client.model.CollectionProgressCandidate;
import top.zhaizz.pojo.vo.collection.CollectionProgressItemVO;

import java.time.LocalDate;
import java.util.List;
import java.util.Objects;

/**
 * 本周追番进度候选项纯计算
 */
@Component
@RequiredArgsConstructor
public class CollectionProgressCalculator {

    /** 数据查询 Mapper */
    private final CollectionMapper mapper;

    /**
     * 根据用户收藏和日期范围计算收藏进度条目
     * @param userId 所属用户 ID，由调用方确认访问权限
     * @param weekStart 统计周的起始日期
     * @param cutoffDate 统计截止日期
     * @return 截止日前能够增加已看集数的收藏候选，日期倒置时为空列表
     */
    public List<CollectionProgressItemVO> calculate(Long userId, LocalDate weekStart, LocalDate cutoffDate) {
        if (cutoffDate.isBefore(weekStart)) return List.of();
        return mapper.selectProgressCandidates(userId, weekStart, cutoffDate).stream()
                .filter(c -> c.getTargetEpStatus() != null
                        && c.getTargetEpStatus() > Objects.requireNonNullElse(c.getCurrentEpStatus(), 0))
                .map(this::toItem)
                .toList();
    }

    /**
     * 将单个进度候选转换为预览条目，并计算完成后建议状态
     *
     * @param c 查询得到的进度候选
     * @return 进度预览条目
     */
    private CollectionProgressItemVO toItem(CollectionProgressCandidate c) {
        boolean completed = c.getTotalEpisodes() != null
                && c.getTotalEpisodes() > 0
                && c.getTargetEpStatus() >= c.getTotalEpisodes();
        return CollectionProgressItemVO.builder()
                .subjectId(c.getSubjectId())
                .subjectName(c.getSubjectName())
                .currentEpStatus(c.getCurrentEpStatus())
                .targetEpStatus(c.getTargetEpStatus())
                .completedAfterUpdate(completed)
                .suggestMarkAsWatched(completed)
                .build();
    }
}
