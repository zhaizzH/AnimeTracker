package top.zhaizz.agent.gateway;

import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.web.client.HttpStatusCodeException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.util.UriComponentsBuilder;
import top.zhaizz.agent.constant.AgentApiPaths;
import top.zhaizz.common.constant.ErrorType;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.pojo.dto.imprt.ImportRunDTO;

/** 通过 HTTP 触发 Python Agent 导入任务的网关实现。 */
@Slf4j
public class HttpImportAgentGateway implements ImportAgentGateway {
    /** 用于普通 Agent 请求的 HTTP 客户端。 */
    private final RestTemplate restTemplate;
    /** Agent 服务的基础 URL。 */
    private final String baseUrl;

    /**
     * 创建导入网关。
     *
     * @param restTemplate HTTP 客户端
     * @param baseUrl Agent 服务基础地址
     */
    public HttpImportAgentGateway(RestTemplate restTemplate, String baseUrl) {
        this.restTemplate = restTemplate;
        this.baseUrl = baseUrl;
    }

    /** {@inheritDoc} */
    @Override
    public void runImport(String authorization, ImportRunDTO request) {
        HttpHeaders headers = new HttpHeaders();
        if (authorization != null && !authorization.isEmpty()) {
            headers.set(HttpHeaders.AUTHORIZATION, authorization);
        }
        UriComponentsBuilder builder = UriComponentsBuilder.fromUriString(baseUrl + AgentApiPaths.ADMIN_IMPORT_RUN)
                .queryParam("mode", request.getMode());
        if (request.getKey() != null) builder.queryParam("key", request.getKey());
        if (request.getSince() != null) builder.queryParam("since", request.getSince());
        if (request.getWorkers() != null) builder.queryParam("workers", request.getWorkers().toString());

        String url = builder.build().encode().toUriString();
        try {
            restTemplate.exchange(url, HttpMethod.POST, new HttpEntity<Void>(headers), String.class);
            log.info("已触发导入任务");
        } catch (HttpStatusCodeException exception) {
            if (exception.getStatusCode().value() == 409) {
                throw new BizException(ErrorType.CONFLICT, "已有导入任务运行中");
            }
            ErrorType errorType = exception.getStatusCode().is5xxServerError()
                    ? ErrorType.INTERNAL_ERROR
                    : ErrorType.BAD_REQUEST;
            throw new BizException(errorType, "导入任务启动失败");
        } catch (ResourceAccessException exception) {
            log.error("Agent 导入服务连接失败");
            throw new BizException(ErrorType.INTERNAL_ERROR, "Agent 导入服务连接失败");
        }
    }
}

