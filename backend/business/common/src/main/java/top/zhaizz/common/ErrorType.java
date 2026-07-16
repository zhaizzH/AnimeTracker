package top.zhaizz.common;

import lombok.Getter;

/**
 * 错误码枚举
 */
@Getter
public enum ErrorType {

    BAD_REQUEST(400, "请求参数错误"),
    UNAUTHORIZED(401, "未认证"),
    FORBIDDEN(403, "无权限"),
    NOT_FOUND(404, "资源不存在"),
    CONFLICT(409, "资源冲突"),
    TOO_MANY_REQUESTS(429, "请求太频繁"),
    VERIFICATION_FAILED(400, "验证失败"),
    EMAIL_NOT_VERIFIED(403, "邮箱未验证"),
    INTERNAL_ERROR(500, "服务器内部错误");

    private final int code;
    private final String message;

    ErrorType(int code, String message) {
        this.code = code;
        this.message = message;
    }
}
