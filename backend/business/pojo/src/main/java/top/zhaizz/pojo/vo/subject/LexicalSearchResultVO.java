package top.zhaizz.pojo.vo.subject;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/** 带 active release 版本的词法召回结果。 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class LexicalSearchResultVO {
    /** 检索索引版本标识。 */
    private String indexVersion;
    /** 检索配置版本标识。 */
    private String profileVersion;
    /** 检索或证据候选列表。 */
    private List<LexicalSearchCandidateVO> candidates;
}
