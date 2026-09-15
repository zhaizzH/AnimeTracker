package top.zhaizz.common.constant;

import lombok.Getter;

/**
 * 错误码枚举
 * <p>
 * 业务错误码即 HTTP 状态码（code == status），BizException 只接受该枚举，
 * 禁止通过裸 int 构造绕过
 */
@Getter
public enum ErrorType {

    /**
     * 请求参数错误，对应 HTTP 400
     */
    BAD_REQUEST(400, "请求参数错误"),
    /**
     * 未认证，对应 HTTP 401
     */
    UNAUTHORIZED(401, "未认证"),
    /**
     * 无权限，对应 HTTP 403
     */
    FORBIDDEN(403, "无权限"),
    /**
     * 资源不存在，对应 HTTP 404
     */
    NOT_FOUND(404, "资源不存在"),
    /**
     * 资源冲突，对应 HTTP 409
     */
    CONFLICT(409, "资源冲突"),
    /**
     * 请求太频繁，对应 HTTP 429
     */
    TOO_MANY_REQUESTS(429, "请求太频繁"),
    /**
     * 验证失败，对应 HTTP 400
     */
    VERIFICATION_FAILED(400, "验证失败"),
    /**
     * 邮箱未验证，对应 HTTP 403
     */
    EMAIL_NOT_VERIFIED(403, "邮箱未验证"),
    /**
     * 请求方法不允许，对应 HTTP 405
     */
    METHOD_NOT_ALLOWED(405, "请求方法不允许"),
    /**
     * 不支持的 Content-Type，对应 HTTP 415
     */
    UNSUPPORTED_MEDIA_TYPE(415, "不支持的 Content-Type"),
    /**
     * 上传文件大小超过限制，对应 HTTP 413
     */
    PAYLOAD_TOO_LARGE(413, "上传文件大小超过限制"),
    /**
     * 服务暂不可用，对应 HTTP 503
     */
    SERVICE_UNAVAILABLE(503, "服务暂不可用"),
    /**
     * 服务器内部错误，对应 HTTP 500
     */
    INTERNAL_ERROR(500, "服务器内部错误");

    /** 错误或响应使用的状态码 */
    private final int code;
    /** 错误码对应的默认提示消息 */
    private final String message;

    /**
     * 绑定错误状态码与默认提示
     * @param code 与 HTTP 状态一致的错误码
     * @param message 默认业务提示
     */
    ErrorType(int code, String message) {
        this.code = code;
        this.message = message;
    }
}
