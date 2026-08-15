package top.zhaizz.client.service;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;
import top.zhaizz.client.mapper.CollectionProgressMapper;
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

    private final CollectionProgressMapper mapper;

    public List<CollectionProgressItemVO> calculate(Long userId, LocalDate weekStart, LocalDate cutoffDate) {
        if (cutoffDate.isBefore(weekStart)) return List.of();
        return mapper.selectCandidates(userId, weekStart, cutoffDate).stream()
                .filter(c -> c.getTargetEpStatus() != null
                        && c.getTargetEpStatus() > Objects.requireNonNullElse(c.getCurrentEpStatus(), 0))
                .map(this::toItem)
                .toList();
    }

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
