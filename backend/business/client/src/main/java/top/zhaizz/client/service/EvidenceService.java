package top.zhaizz.client.service;

import top.zhaizz.pojo.dto.evidence.EvidenceEntityBatchRequestDTO;
import top.zhaizz.pojo.vo.evidence.EvidenceCandidateVO;

import java.util.List;

/** 面向 Agent 的批量证据回查服务。 */
public interface EvidenceService {

    /**
     * 批量回查条目证据。
     * 验证 type、NSFW、active 状态并返回来源时间。
     * 不存在的 ID 不会出现在结果中。
     */
    List<EvidenceCandidateVO> batchEvidence(List<Long> subjectIds);

    /**
     * 将人物、角色或声优关系批量解析为安全动画条目证据。
     * SUBJECT 类型等价于旧 batchEvidence，保留旧 API 兼容。
     */
    List<EvidenceCandidateVO> resolveEvidence(EvidenceEntityBatchRequestDTO request);
}
