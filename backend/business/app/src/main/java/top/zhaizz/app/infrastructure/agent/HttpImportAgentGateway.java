package top.zhaizz.app.infrastructure.agent;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.stereotype.Component;
import org.springframework.web.client.HttpStatusCodeException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.util.UriComponentsBuilder;
import top.zhaizz.admin.gateway.ImportAgentGateway;
import top.zhaizz.common.config.AgentProperties;
import top.zhaizz.common.constant.AgentApiPaths;
import top.zhaizz.common.constant.ErrorType;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.pojo.dto.imprt.ImportRunDTO;

@Slf4j
@Component
@RequiredArgsConstructor
public class HttpImportAgentGateway implements ImportAgentGateway {
    private final RestTemplate restTemplate;
    private final AgentProperties agentProperties;

    @Override
    public void runImport(String authorization, ImportRunDTO request) {
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
        try {
            restTemplate.exchange(url, HttpMethod.POST, new HttpEntity<Void>(headers), String.class);
            log.info("已触发导入: mode={} key={} since={}",
                    request.getMode(), request.getKey(), request.getSince());
        } catch (HttpStatusCodeException exception) {
            if (exception.getStatusCode().value() == 409) {
                throw new BizException(ErrorType.CONFLICT, "已有导入任务运行中");
            }
            String detail = exception.getResponseBodyAsString();
            throw new BizException(
                    exception.getStatusCode().is5xxServerError()
                            ? ErrorType.INTERNAL_ERROR : ErrorType.BAD_REQUEST,
                    "导入任务启动失败: " + (detail == null || detail.isEmpty()
                            ? exception.getStatusText() : detail));
        } catch (ResourceAccessException exception) {
            log.error("Agent 导入服务连接失败: {}", url, exception);
            throw new BizException(ErrorType.INTERNAL_ERROR, "Agent 导入服务连接失败");
        }
    }
}
