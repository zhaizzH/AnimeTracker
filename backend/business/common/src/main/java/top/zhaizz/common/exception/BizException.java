package top.zhaizz.common.exception;

import lombok.Getter;
import top.zhaizz.common.ErrorType;

/**
 * 业务异常基类，包含 code 和 message
 */
@Getter
public class BizException extends RuntimeException {

    private final int code;
    private final Object data;  // 新增

    public BizException(ErrorType errorType) {
        super(errorType.getMessage());
        this.code = errorType.getCode();
        this.data = null;
    }

    public BizException(ErrorType errorType, String message) {
        super(message);
        this.code = errorType.getCode();
        this.data = null;
    }

    // 新增构造器
    public BizException(ErrorType errorType, String message, Object data) {
        super(message);
        this.code = errorType.getCode();
        this.data = data;
    }

    public BizException(int code, String message) {
        super(message);
        this.code = code;
        this.data = null;
    }
}
