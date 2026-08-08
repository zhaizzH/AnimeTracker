package top.zhaizz.admin.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.HttpStatusCodeException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestTemplate;
import top.zhaizz.admin.converter.SubjectConverter;
import top.zhaizz.admin.mapper.ImportRecordMapper;
import top.zhaizz.admin.service.ImportService;
import top.zhaizz.common.ErrorType;
import top.zhaizz.common.config.AgentProperties;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.pojo.entity.ImportRecord;
import top.zhaizz.pojo.vo.ImportStatusVO;

import java.util.List;
import java.util.Set;

/**
 * 番剧导入服务实现 — 触发转发至 Python Agent 导入端点，进程管理由 agent 侧负责。
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class ImportServiceImpl implements ImportService {
    private static final Set<String> MODES = Set.of("full", "season", "recent", "since");
    private static final String RUN_PATH = "/api/admin/agent/import/run";

    private final RestTemplate restTemplate;
    private final AgentProperties agentProperties;
    private final ImportRecordMapper importRecordMapper;

    @Override
    public void runImport(String authorization, String mode, String key, String since, Integer workers) {
        validate(mode, key, since);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_FORM_URLENCODED);
        if (authorization != null && !authorization.isEmpty()) {
            headers.set(HttpHeaders.AUTHORIZATION, authorization);
        }
        MultiValueMap<String, String> form = new LinkedMultiValueMap<>();
        form.add("mode", mode);
        if (key != null) form.add("key", key);
        if (since != null) form.add("since", since);
        if (workers != null) form.add("workers", workers.toString());

        String url = agentProperties.getBaseUrl() + RUN_PATH;
        HttpEntity<MultiValueMap<String, String>> entity = new HttpEntity<>(form, headers);
        try {
            restTemplate.exchange(url, HttpMethod.POST, entity, String.class);
            log.info("已触发导入: mode={} key={} since={}", mode, key, since);
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
        List<ImportRecord> records = importRecordMapper.selectList(
                new LambdaQueryWrapper<ImportRecord>()
                        .orderByDesc(ImportRecord::getStartedAt)
                        .last("LIMIT 10"));
        ImportStatusVO vo = new ImportStatusVO();
        vo.setLastImportedAt(records.isEmpty() ? null : records.getFirst().getCompletedAt());
        vo.setTotalSubjects(records.size());
        vo.setRecentRecords(SubjectConverter.toImportRecordVOList(records));
        return vo;
    }

    private void validate(String mode, String key, String since) {
        if (mode == null || !MODES.contains(mode)) {
            throw new BizException(ErrorType.BAD_REQUEST, "mode 必须是 full / season / recent / since");
        }
        if ("season".equals(mode) && (key == null || key.isBlank())) {
            throw new BizException(ErrorType.BAD_REQUEST, "season 模式需要 key");
        }
        if ("since".equals(mode) && (since == null || since.isBlank())) {
            throw new BizException(ErrorType.BAD_REQUEST, "since 模式需要 since");
        }
    }
}
