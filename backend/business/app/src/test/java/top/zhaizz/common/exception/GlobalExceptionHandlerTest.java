package top.zhaizz.common.exception;

import org.junit.jupiter.api.Test;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.web.HttpMediaTypeNotSupportedException;
import org.springframework.web.servlet.resource.NoResourceFoundException;
import top.zhaizz.common.ErrorType;
import top.zhaizz.common.result.Result;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

class GlobalExceptionHandlerTest {

    private final GlobalExceptionHandler handler = new GlobalExceptionHandler();

    @Test
    void bizExceptionMapsErrorTypeToStatusCode() {
        ResponseEntity<Result<Object>> resp = handler.handleBizException(new BizException(ErrorType.CONFLICT, "资源冲突"));
        assertThat(resp.getStatusCode()).isEqualTo(HttpStatus.CONFLICT);
        assertThat(resp.getBody().getMessage()).isEqualTo("资源冲突");
    }

    @Test
    void accessDeniedMapsTo403() {
        Result<Void> body = handler.handleAccessDenied(new AccessDeniedException("denied"));
        assertThat(body.getCode()).isEqualTo(403);
        assertThat(body.getMessage()).isEqualTo("无权限");
    }

    @Test
    void dataIntegrityViolationMapsTo409() {
        Result<Void> body = handler.handleDataIntegrityViolation(new DataIntegrityViolationException("duplicate key"));
        assertThat(body.getCode()).isEqualTo(409);
        assertThat(body.getMessage()).isEqualTo("资源冲突");
    }

    @Test
    void noResourceFoundHidesInternalPath() {
        Result<Void> body = handler.handleNoResourceFound(new NoResourceFoundException(HttpMethod.GET, "/secret"));
        assertThat(body.getCode()).isEqualTo(404);
        assertThat(body.getMessage()).isEqualTo("接口不存在");
        assertThat(body.getMessage()).doesNotContain("/secret");
    }

    @Test
    void mediaTypeNotSupportedHidesContentType() {
        Result<Void> body = handler.handleHttpMediaTypeNotSupported(
                new HttpMediaTypeNotSupportedException(new MediaType("text", "html"), List.of(MediaType.APPLICATION_JSON)));
        assertThat(body.getCode()).isEqualTo(415);
        assertThat(body.getMessage()).isEqualTo("不支持的 Content-Type");
        assertThat(body.getMessage()).doesNotContain("html");
    }

    @Test
    void unknownExceptionMapsTo500() {
        Result<Void> body = handler.handleException(new RuntimeException("boom"));
        assertThat(body.getCode()).isEqualTo(500);
        assertThat(body.getMessage()).isEqualTo("服务器内部错误");
    }
}
