package top.zhaizz.pojo.vo.subject;

import lombok.Data;

import java.util.ArrayList;
import java.util.List;

/** 批量权威回查分类结果。 */
@Data
public class SubjectBatchResultVO {
    private List<SubjectBatchItemVO> items = new ArrayList<>();
    private List<Long> missingIds = new ArrayList<>();
    private List<Long> filteredIds = new ArrayList<>();
    private List<Long> collectedIds = new ArrayList<>();
}
