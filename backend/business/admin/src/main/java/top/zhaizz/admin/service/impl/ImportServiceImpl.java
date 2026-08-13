package top.zhaizz.admin.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import org.springframework.web.client.HttpStatusCodeException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.util.UriComponentsBuilder;
import top.zhaizz.admin.constant.ImportConstants;
import top.zhaizz.admin.converter.SubjectConverter;
import top.zhaizz.admin.mapper.ImportRecordMapper;
import top.zhaizz.admin.service.ImportService;
import top.zhaizz.common.constant.AgentApiPaths;
import top.zhaizz.common.constant.ErrorType;
import top.zhaizz.common.config.AgentProperties;
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
@Slf4j
@Service
@RequiredArgsConstructor
public class ImportServiceImpl implements ImportService {
    private final RestTemplate restTemplate;
    private final AgentProperties agentProperties;
    private final ImportRecordMapper importRecordMapper;

    @Override
    public void runImport(String authorization, ImportRunDTO request) {
        validate(request.getMode(), request.getKey(), request.getSince());

        HttpHeaders headers = new HttpHeaders();
        if (authorization != null && !authorization.isEmpty()) {
            headers.set(HttpHeaders.AUTHORIZATION, authorization);
        }
        UriComponentsBuilder builder = UriComponentsBuilder
                .fromUriString(agentProperties.getBaseUrl() + AgentApiPaths.ADMIN_IMPORT_RUN)
                .queryParam("mode", request.getMode());
        if (request.getKey() != null) builder.queryParam("key", request.getKey());
        if (request.getSince() != null) builder.queryParam("since", request.getSince());
        if (request.getWorkers() != null) builder.queryParam("workers", request.getWorkers().toString());

        String url = builder.build().encode().toUriString();
        HttpEntity<Void> entity = new HttpEntity<>(headers);
        try {
            restTemplate.exchange(url, HttpMethod.POST, entity, String.class);
            log.info("已触发导入: mode={} key={} since={}", request.getMode(), request.getKey(), request.getSince());
        } catch (HttpStatusCodeException e) {
            if (e.getStatusCode().value() == 409) {
                throw new BizException(ErrorType.CONFLICT, "已有导入任务运行中");
            }
            String detail = e.getResponseBodyAsString();
            throw new BizException(
                    e.getStatusCode().is5xxServerError() ? ErrorType.INTERNAL_ERROR : ErrorType.BAD_REQUEST,
                    "导入任务启动失败: " + (detail == null || detail.isEmpty() ? e.getStatusText() : detail));
        } catch (ResourceAccessException e) {
            log.error("Agent 导入服务连接失败: {}", url, e);
            throw new BizException(ErrorType.INTERNAL_ERROR, "Agent 导入服务连接失败");
        }
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
