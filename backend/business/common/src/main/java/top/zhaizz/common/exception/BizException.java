package top.zhaizz.common.exception;

import lombok.Getter;
import top.zhaizz.common.constant.ErrorType;

/**
 * 业务异常基类，包含 code 和 message。
 */
@Getter
public class BizException extends RuntimeException {

    /** 统一响应或异常的状态码。 */
    private final int code;
    /** 统一响应承载的业务数据。 */
    private final Object data;

    /**
     * 根据错误类型创建业务异常。
     *
     * @param errorType 非空统一错误类型，提供错误码与默认提示
     */
    public BizException(ErrorType errorType) {
        super(errorType.getMessage());
        this.code = errorType.getCode();
        this.data = null;
    }

    /**
     * 根据错误类型和自定义消息创建业务异常。
     *
     * @param errorType 非空统一错误类型，提供错误码与默认提示
     * @param message 向调用方展示的提示消息
     */
    public BizException(ErrorType errorType, String message) {
        super(message);
        this.code = errorType.getCode();
        this.data = null;
    }

    /**
     * 根据错误类型、消息和附加数据创建业务异常。
     *
     * @param errorType 非空统一错误类型，提供错误码与默认提示
     * @param message 向调用方展示的提示消息
     * @param data 附加响应数据，可为空；不进行复制
     */
    public BizException(ErrorType errorType, String message, Object data) {
        super(message);
        this.code = errorType.getCode();
        this.data = data;
    }
}
