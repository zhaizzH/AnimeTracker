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

    private final EvidenceService evidenceService;

    @PostMapping("/batch")
    public Result<List<EvidenceCandidateVO>> batchEvidence(
            @Valid @RequestBody EvidenceBatchRequestDTO request) {
        return Result.success(evidenceService.batchEvidence(request.getSubjectIds()));
    }
}
