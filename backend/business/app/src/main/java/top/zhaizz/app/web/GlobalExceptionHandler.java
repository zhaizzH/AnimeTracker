package top.zhaizz.app.web;

import top.zhaizz.common.exception.BizException;

import jakarta.validation.ConstraintViolation;
import jakarta.validation.ConstraintViolationException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.validation.FieldError;
import org.springframework.web.HttpMediaTypeNotSupportedException;
import org.springframework.web.HttpRequestMethodNotSupportedException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.ServletRequestBindingException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;
import org.springframework.web.multipart.MaxUploadSizeExceededException;
import org.springframework.web.servlet.resource.NoResourceFoundException;
import top.zhaizz.common.constant.ErrorType;
import top.zhaizz.common.result.Result;

import java.util.HashMap;
import java.util.Map;

/**
 * 全局异常处理，捕获 BizException、参数校验异常、Spring MVC 异常等。
 * <p>
 * 统一返回 {code, message, data}，异常按范围从小到大逐级匹配，兜底未知异常 500
 */
@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    /**
     * 处理业务异常 — 将 BizException.code 映射为 HTTP 状态码。
     *
     * @param e 触发当前异常适配的异常实例
     * @return HTTP 状态与业务错误码一致、保留消息及附加数据的响应
     */
    @ExceptionHandler(BizException.class)
    public ResponseEntity<Result<Object>> handleBizException(BizException e) {
        log.warn("业务异常: code={}", e.getCode());
        return ResponseEntity.status(e.getCode())
                .body(Result.error(e.getCode(), e.getMessage(), e.getData()));
    }

    /**
     * 处理方法级鉴权失败（@PreAuthorize / 角色校验）。
     *
     * @param e 触发当前异常适配的异常实例
     * @return 错误码 403 的无数据结果
     */
    @ExceptionHandler(AccessDeniedException.class)
    @ResponseStatus(HttpStatus.FORBIDDEN)
    public Result<Void> handleAccessDenied(AccessDeniedException e) {
        log.warn("无权限");
        return Result.error(ErrorType.FORBIDDEN.getCode(), ErrorType.FORBIDDEN.getMessage());
    }

    /**
     * 处理数据库约束冲突（唯一键 / 外键等）。
     *
     * @param e 触发当前异常适配的异常实例
     * @return 错误码 409 的无数据结果
     */
    @ExceptionHandler(DataIntegrityViolationException.class)
    @ResponseStatus(HttpStatus.CONFLICT)
    public Result<Void> handleDataIntegrityViolation(DataIntegrityViolationException e) {
        log.warn("数据库约束冲突");
        return Result.error(ErrorType.CONFLICT.getCode(), ErrorType.CONFLICT.getMessage());
    }

    /**
     * 处理 @Valid 参数校验失败 — message 取首个字段错误的具体提示，data 保留字段映射。
     *
     * @param e 触发当前异常适配的异常实例
     * @return 错误码 400 的结果，包含首个错误提示及字段错误映射
     */
    @ExceptionHandler(MethodArgumentNotValidException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public Result<Map<String, String>> handleValidationException(MethodArgumentNotValidException e) {
        Map<String, String> errors = new HashMap<>();
        for (FieldError fieldError : e.getBindingResult().getFieldErrors()) {
            errors.put(fieldError.getField(), fieldError.getDefaultMessage());
        }
        String message = e.getBindingResult().getFieldErrors().stream()
                .findFirst()
                .map(FieldError::getDefaultMessage)
                .orElse("请求参数错误");
        log.warn("Valid 参数校验失败，字段数={}", errors.size());
        return Result.error(ErrorType.BAD_REQUEST.getCode(), message, errors);
    }

    /**
     * 处理 @Validated 参数校验失败（如查询参数）— message 取首个约束的具体提示，data 给空 map（方法级无字段 key）。
     *
     * @param e 触发当前异常适配的异常实例
     * @return 错误码 400 的结果，包含首个约束提示与空映射
     */
    @ExceptionHandler(ConstraintViolationException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public Result<Map<String, String>> handleConstraintViolationException(ConstraintViolationException e) {
        String message = e.getConstraintViolations().stream()
                .findFirst()
                .map(ConstraintViolation::getMessage)
                .orElse("请求参数错误");
        log.warn("Validated 参数校验失败");
        return Result.error(ErrorType.BAD_REQUEST.getCode(), message, Map.of());
    }

    /**
     * 处理请求体 JSON 解析失败（空 body / 语法错误 / 字段类型不匹配）。
     *
     * @param e 触发当前异常适配的异常实例
     * @return 错误码 400 的请求体格式错误结果
     */
    @ExceptionHandler(HttpMessageNotReadableException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public Result<Void> handleHttpMessageNotReadable(HttpMessageNotReadableException e) {
        log.warn("请求体解析失败");
        return Result.error(ErrorType.BAD_REQUEST.getCode(), "请求体格式错误");
    }

    /**
     * 处理缺参 / 缺请求头 / 参数类型不匹配。
     *
     * @param e 触发当前异常适配的异常实例
     * @return 错误码 400 的参数错误结果
     */
    @ExceptionHandler({ServletRequestBindingException.class, MethodArgumentTypeMismatchException.class})
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public Result<Void> handleBadRequestParams(Exception e) {
        log.warn("请求参数错误");
        return Result.error(ErrorType.BAD_REQUEST.getCode(), "请求参数错误");
    }

    /**
     * 处理不支持的 Content-Type。
     *
     * @param e 触发当前异常适配的异常实例
     * @return 错误码 415 的无数据结果
     */
    @ExceptionHandler(HttpMediaTypeNotSupportedException.class)
    @ResponseStatus(HttpStatus.UNSUPPORTED_MEDIA_TYPE)
    public Result<Void> handleHttpMediaTypeNotSupported(HttpMediaTypeNotSupportedException e) {
        log.warn("不支持的 Content-Type: {}", e.getContentType());
        return Result.error(ErrorType.UNSUPPORTED_MEDIA_TYPE.getCode(), ErrorType.UNSUPPORTED_MEDIA_TYPE.getMessage());
    }

    /**
     * 处理不支持的 HTTP 方法。
     *
     * @param e 触发当前异常适配的异常实例
     * @return 错误码 405 的结果，消息包含不支持的 HTTP 方法
     */
    @ExceptionHandler(HttpRequestMethodNotSupportedException.class)
    @ResponseStatus(HttpStatus.METHOD_NOT_ALLOWED)
    public Result<Void> handleHttpRequestMethodNotSupported(HttpRequestMethodNotSupportedException e) {
        log.warn("不支持的请求方法: {}", e.getMethod());
        return Result.error(ErrorType.METHOD_NOT_ALLOWED.getCode(), "不支持的请求方法: " + e.getMethod());
    }

    /**
     * 处理上传文件超限。
     *
     * @param e 触发当前异常适配的异常实例
     * @return 错误码 413 的上传超限结果
     */
    @ExceptionHandler(MaxUploadSizeExceededException.class)
    @ResponseStatus(HttpStatus.PAYLOAD_TOO_LARGE)
    public Result<Void> handleMaxUploadSizeExceeded(MaxUploadSizeExceededException e) {
        log.warn("上传文件超限");
        return Result.error(ErrorType.PAYLOAD_TOO_LARGE.getCode(), "上传文件大小超过限制");
    }

    /**
     * 处理静态资源 handler 抛出的 404（未知 API 路径）。
     *
     * @param e 触发当前异常适配的异常实例
     * @return 错误码 404 的接口不存在结果
     */
    @ExceptionHandler(NoResourceFoundException.class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    public Result<Void> handleNoResourceFound(NoResourceFoundException e) {
        return Result.error(ErrorType.NOT_FOUND.getCode(), "接口不存在");
    }

    /**
     * 处理未知异常。
     *
     * @param e 触发当前异常适配的异常实例
     * @return 错误码 500 的通用结果，不包含原始异常信息
     */
    @ExceptionHandler(Exception.class)
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    public Result<Void> handleException(Exception e) {
        log.error("服务器内部错误，异常类型={}", e.getClass().getName());
        return Result.error(ErrorType.INTERNAL_ERROR.getCode(), ErrorType.INTERNAL_ERROR.getMessage());
    }
}


