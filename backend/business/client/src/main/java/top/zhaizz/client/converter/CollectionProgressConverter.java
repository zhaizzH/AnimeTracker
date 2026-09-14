package top.zhaizz.client.converter;

import top.zhaizz.pojo.vo.collection.CollectionProgressFailureVO;
import top.zhaizz.pojo.vo.collection.CollectionProgressItemVO;
import top.zhaizz.pojo.vo.collection.CollectionProgressPreviewVO;
import top.zhaizz.pojo.vo.collection.CollectionProgressState;

import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.util.List;

/** 收藏进度预览响应转换器。 */
public final class CollectionProgressConverter {
    /**
     * 禁止实例化仅提供静态操作的工具类。
     */
    private CollectionProgressConverter() {
    }

    /**
     * 将预览条目的标识与进度映射为失败说明，不修改条目。
     * @param item 预览条目，不可为 {@code null}
     * @param reason 失败原因，允许为空并原样保留
     * @return 新的失败对象
     * @throws NullPointerException 条目为空
     */
    public static CollectionProgressFailureVO toFailure(CollectionProgressItemVO item, String reason) {
        return CollectionProgressFailureVO.builder()
                .subjectId(item.getSubjectId()).subjectName(item.getSubjectName())
                .currentEpStatus(item.getCurrentEpStatus()).targetEpStatus(item.getTargetEpStatus())
                .reason(reason).build();
    }

    /**
     * 组装预览响应，直接引用条目列表，不修改任何输入。
     * @param state 预览状态，原样保留
     * @param previewId 预览标识，原样保留
     * @param items 预览条目列表，可为空，不复制列表或元素
     * @param weekStart 统计周起始日期，原样保留
     * @param cutoffDate 统计截止日期，原样保留
     * @param expiresAt 到期时刻，原样保留
     * @return 新的预览对象；本方法不校验或补全空字段
     */
    public static CollectionProgressPreviewVO toPreviewVO(CollectionProgressState state, String previewId,
                                                          List<CollectionProgressItemVO> items,
                                                          LocalDate weekStart, LocalDate cutoffDate,
                                                          OffsetDateTime expiresAt) {
        return CollectionProgressPreviewVO.builder().previewId(previewId).state(state)
                .expiresAt(expiresAt).weekStart(weekStart).cutoffDate(cutoffDate).items(items).build();
    }
}
