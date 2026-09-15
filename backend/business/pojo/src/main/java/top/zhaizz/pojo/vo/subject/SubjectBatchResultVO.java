package top.zhaizz.pojo.vo.subject;

import lombok.Data;

import java.util.ArrayList;
import java.util.List;

/** 批量权威回查分类结果 */
@Data
public class SubjectBatchResultVO {
    /** 批处理或预览包含的条目集合 */
    private List<SubjectBatchItemVO> items = new ArrayList<>();
    /** 未找到对应记录的标识列表 */
    private List<Long> missingIds = new ArrayList<>();
    /** 被筛选排除的标识列表 */
    private List<Long> filteredIds = new ArrayList<>();
    /** 已收藏条目标识列表 */
    private List<Long> collectedIds = new ArrayList<>();
}
