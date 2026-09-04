package top.zhaizz.client.service;

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
}
