package top.zhaizz.animetracker.common.exception;

import lombok.Getter;
import top.zhaizz.animetracker.common.ErrorType;

/**
 * 业务异常基类，包含 code 和 message
 */
@Getter
public class BizException extends RuntimeException {

    private final int code;

    public BizException(ErrorType errorType) {
        super(errorType.getMessage());
        this.code = errorType.getCode();
    }

    public BizException(ErrorType errorType, String message) {
        super(message);
        this.code = errorType.getCode();
    }

    public BizException(int code, String message) {
        super(message);
        this.code = code;
    }
}
