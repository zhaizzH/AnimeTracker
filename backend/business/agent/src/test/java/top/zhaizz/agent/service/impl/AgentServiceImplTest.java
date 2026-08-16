package top.zhaizz.agent.service.impl;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestTemplate;
import top.zhaizz.common.config.AgentProperties;
import top.zhaizz.common.constant.ErrorType;
import top.zhaizz.common.exception.BizException;

import java.net.SocketTimeoutException;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

/**
 * Agent 降级测试：连接失败/超时/上游 5xx 统一归为 503；4xx 尽量保留语义。
 */
class AgentServiceImplTest {

    private RestTemplate restTemplate;
    private AgentServiceImpl service;

    @BeforeEach
    void setUp() {
        restTemplate = mock(RestTemplate.class);
        AgentProperties props = new AgentProperties();
        props.setBaseUrl("http://agent:8090");
        service = new AgentServiceImpl(restTemplate, props, new ObjectMapper());
    }

    private void stubExchange(Throwable throwable) {
        when(restTemplate.exchange(anyString(), any(HttpMethod.class), any(), eq(String.class)))
                .thenThrow(throwable);
    }

    private BizException forwardAndExpect() {
        return org.junit.jupiter.api.Assertions.assertThrows(BizException.class,
                () -> service.forward("/api/x", HttpMethod.GET, null, null));
    }

    @Test
    void connectionFailureMapsToServiceUnavailable() {
        stubExchange(new ResourceAccessException("connect timeout", new SocketTimeoutException("timeout")));
        assertThat(forwardAndExpect().getCode()).isEqualTo(ErrorType.SERVICE_UNAVAILABLE.getCode());
    }

    @Test
    void agent5xxMapsToServiceUnavailable() {
        stubExchange(new HttpServerErrorException(HttpStatus.INTERNAL_SERVER_ERROR, "boom"));
        assertThat(forwardAndExpect().getCode()).isEqualTo(ErrorType.SERVICE_UNAVAILABLE.getCode());
    }

    @Test
    void upstream401KeepsUnauthorizedSemantics() {
        stubExchange(new HttpClientErrorException(HttpStatus.UNAUTHORIZED, "unauthorized"));
        assertThat(forwardAndExpect().getCode()).isEqualTo(ErrorType.UNAUTHORIZED.getCode());
    }

    @Test
    void upstream404KeepsNotFoundSemantics() {
        stubExchange(new HttpClientErrorException(HttpStatus.NOT_FOUND, "not found"));
        assertThat(forwardAndExpect().getCode()).isEqualTo(ErrorType.NOT_FOUND.getCode());
    }
}
