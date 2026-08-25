package top.zhaizz.admin.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import top.zhaizz.admin.constant.ImportConstants;
import top.zhaizz.admin.converter.SubjectConverter;
import top.zhaizz.admin.gateway.ImportAgentGateway;
import top.zhaizz.admin.mapper.ImportRecordMapper;
import top.zhaizz.admin.service.ImportService;
import top.zhaizz.common.constant.ErrorType;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.common.result.PageResult;
import top.zhaizz.pojo.dto.imprt.ImportRecordQueryDTO;
import top.zhaizz.pojo.dto.imprt.ImportRunDTO;
import top.zhaizz.pojo.entity.ImportRecord;
import top.zhaizz.pojo.vo.imprt.ImportRecordVO;
import top.zhaizz.pojo.vo.imprt.ImportStatusVO;

import java.util.List;
import java.util.Objects;

/**
 * 番剧导入服务实现 — 触发转发至 Python Agent；状态与记录直接查库。
 */
@Service
@RequiredArgsConstructor
public class ImportServiceImpl implements ImportService {
    private final ImportAgentGateway importAgentGateway;
    private final ImportRecordMapper importRecordMapper;

    @Override
    public void runImport(String authorization, ImportRunDTO request) {
        validate(request.getMode(), request.getKey(), request.getSince());
        importAgentGateway.runImport(authorization, request);
    }

    @Override
    public ImportStatusVO getImportStatus() {
        // 当前导入日志数量 = import_record 全量记录数（回归: 2026-08-11 误显示条目总数）
        Long totalLogs = importRecordMapper.selectCount(null);
        List<ImportRecord> recent = importRecordMapper.selectList(
                new LambdaQueryWrapper<ImportRecord>()
                        .orderByDesc(ImportRecord::getStartedAt)
                        .last("LIMIT 10"));
        List<ImportRecordVO> recordVOs = SubjectConverter.toImportRecordVOList(recent);
        ImportStatusVO vo = new ImportStatusVO();
        vo.setTotalLogs(totalLogs == null ? 0L : totalLogs);
        vo.setCompletedCount(importRecordMapper.selectCount(
                new LambdaQueryWrapper<ImportRecord>().eq(ImportRecord::getStatus, "COMPLETED")));
        vo.setFailedCount(importRecordMapper.selectCount(
                new LambdaQueryWrapper<ImportRecord>().eq(ImportRecord::getStatus, "FAILED")));
        vo.setRecentRecords(recordVOs);
        vo.setLastImportedAt(recordVOs.stream()
                .map(ImportRecordVO::getCompletedAt)
                .filter(Objects::nonNull)
                .findFirst()
                .orElse(null));
        return vo;
    }

    @Override
    public PageResult<ImportRecordVO> getImportRecords(ImportRecordQueryDTO request) {
        LambdaQueryWrapper<ImportRecord> qw = new LambdaQueryWrapper<ImportRecord>()
                .eq(StringUtils.hasText(request.getStatus()), ImportRecord::getStatus, request.getStatus())
                .orderByDesc(ImportRecord::getStartedAt);
        Page<ImportRecord> p = importRecordMapper.selectPage(new Page<>(request.getPage(), request.getSize()), qw);
        return PageResult.of(
                SubjectConverter.toImportRecordVOList(p.getRecords()),
                p.getTotal(),
                (int) p.getCurrent(),
                (int) p.getSize());
    }

    private void validate(String mode, String key, String since) {
        if (mode == null || !ImportConstants.MODES.contains(mode)) {
            throw new BizException(ErrorType.BAD_REQUEST, "mode 必须是 full / season / recent / since");
        }
        if (ImportConstants.MODE_SEASON.equals(mode) && (key == null || key.isBlank())) {
            throw new BizException(ErrorType.BAD_REQUEST, "season 模式需要 key");
        }
        if (ImportConstants.MODE_SINCE.equals(mode) && (since == null || since.isBlank())) {
            throw new BizException(ErrorType.BAD_REQUEST, "since 模式需要 since");
        }
    }
}
