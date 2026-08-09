package top.zhaizz.admin.service.impl;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.stereotype.Service;
import org.springframework.web.client.HttpStatusCodeException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.util.UriComponentsBuilder;
import top.zhaizz.admin.service.ImportService;
import top.zhaizz.common.ErrorType;
import top.zhaizz.common.config.AgentProperties;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.pojo.vo.ImportStatusVO;

import java.util.Set;

/**
 * 番剧导入服务实现 — 触发与状态均转发至 Python Agent 导入端点，进程与记录状态由 agent 侧统一负责。
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class ImportServiceImpl implements ImportService {
    private static final Set<String> MODES = Set.of("full", "season", "recent", "since");
    private static final String RUN_PATH = "/api/admin/agent/import/run";
    private static final String STATUS_PATH = "/api/admin/agent/import/status";

    private final RestTemplate restTemplate;
    private final AgentProperties agentProperties;

    @Override
    public void runImport(String authorization, String mode, String key, String since, Integer workers) {
        validate(mode, key, since);

        HttpHeaders headers = new HttpHeaders();
        if (authorization != null && !authorization.isEmpty()) {
            headers.set(HttpHeaders.AUTHORIZATION, authorization);
        }
        UriComponentsBuilder builder = UriComponentsBuilder
                .fromUriString(agentProperties.getBaseUrl() + RUN_PATH)
                .queryParam("mode", mode);
        if (key != null) builder.queryParam("key", key);
        if (since != null) builder.queryParam("since", since);
        if (workers != null) builder.queryParam("workers", workers.toString());

        String url = builder.build().encode().toUriString();
        HttpEntity<Void> entity = new HttpEntity<>(headers);
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
    public ImportStatusVO getImportStatus(String authorization) {
        HttpHeaders headers = new HttpHeaders();
        if (authorization != null && !authorization.isEmpty()) {
            headers.set(HttpHeaders.AUTHORIZATION, authorization);
        }
        String url = agentProperties.getBaseUrl() + STATUS_PATH;
        try {
            return restTemplate.exchange(url, HttpMethod.GET, new HttpEntity<>(headers), ImportStatusVO.class).getBody();
        } catch (HttpStatusCodeException e) {
            String detail = e.getResponseBodyAsString();
            throw new BizException(
                    e.getStatusCode().is5xxServerError() ? ErrorType.INTERNAL_ERROR : ErrorType.BAD_REQUEST,
                    "导入状态获取失败: " + (detail == null || detail.isEmpty() ? e.getStatusText() : detail));
        } catch (ResourceAccessException e) {
            log.error("Agent 导入服务连接失败: {}", url, e);
            throw new BizException(ErrorType.INTERNAL_ERROR, "Agent 导入服务连接失败");
        }
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
