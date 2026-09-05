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
    private String indexVersion;
    private String profileVersion;
    private List<LexicalSearchCandidateVO> candidates;
}
