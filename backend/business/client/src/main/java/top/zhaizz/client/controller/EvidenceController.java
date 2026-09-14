package top.zhaizz.client.controller;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import top.zhaizz.client.service.EvidenceService;
import top.zhaizz.common.result.Result;
import top.zhaizz.pojo.dto.evidence.EvidenceBatchRequestDTO;
import top.zhaizz.pojo.dto.evidence.EvidenceEntityBatchRequestDTO;
import top.zhaizz.pojo.vo.evidence.EvidenceCandidateVO;

import java.util.List;

/**
 * 面向 Agent 的批量证据回查接口。
 * 验证 type、NSFW、active 状态并返回来源时间。
 */
@RestController
@RequestMapping("/api/client/evidence")
@RequiredArgsConstructor
public class EvidenceController {

    /** 证据查询服务。 */
    private final EvidenceService evidenceService;

    /**
     * 回查条目的安全证据与来源信息。
     * @param request 待回查的条目 ID
     * @return 统一成功响应，其数据为：满足动画、安全与有效条件的证据，不存在的条目被省略
     */
    @PostMapping("/batch")
    public Result<List<EvidenceCandidateVO>> batchEvidence(
            @Valid @RequestBody EvidenceBatchRequestDTO request) {
        return Result.success(evidenceService.batchEvidence(request.getSubjectIds()));
    }

    /**
     * 将人物、角色、声优关系或条目 ID 批量解析为最小安全证据候选。
     * 旧 /batch 只接受 subjectIds，本接口不改变其请求契约。
     * @param request 实体类型及 ID 列表
     * @return 统一成功响应，其数据为：实体关联到的安全动画条目证据
     */
    @PostMapping("/resolve")
    public Result<List<EvidenceCandidateVO>> resolveEvidence(
            @Valid @RequestBody EvidenceEntityBatchRequestDTO request) {
        return Result.success(evidenceService.resolveEvidence(request));
    }
}
