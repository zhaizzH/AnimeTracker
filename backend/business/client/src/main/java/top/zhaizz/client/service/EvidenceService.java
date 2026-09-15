package top.zhaizz.client.service;

import top.zhaizz.pojo.dto.evidence.EvidenceEntityBatchRequestDTO;
import top.zhaizz.pojo.vo.evidence.EvidenceCandidateVO;

import java.util.List;

/** 面向 Agent 的批量证据回查服务 */
public interface EvidenceService {

    /**
     * <p>输入为空时返回空列表；去重后按数据库查询顺序返回，不保证输入顺序
     * 批量回查条目证据
     * 验证 type、NSFW、active 状态并返回来源时间
     * 不存在的 ID 不会出现在结果中
     * @param subjectIds 待查询的条目 ID 列表
     * @return 满足动画、安全与有效条件的证据，不存在的条目被省略
     */
    List<EvidenceCandidateVO> batchEvidence(List<Long> subjectIds);

    /**
     * <p>请求、实体类型或 ID 列表缺失时返回空列表；过滤空 ID 并去重后回查
     * 将人物、角色或声优关系批量解析为安全动画条目证据
     * SUBJECT 类型等价于旧 batchEvidence，保留旧 API 兼容
     * @param request 实体类型及 ID 列表
     * @return 实体关联到的安全动画条目证据
     * @throws top.zhaizz.common.exception.BizException 原始 ID 列表超过 50 项时为 BAD_REQUEST
     */
    List<EvidenceCandidateVO> resolveEvidence(EvidenceEntityBatchRequestDTO request);
}
