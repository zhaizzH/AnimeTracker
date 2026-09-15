package top.zhaizz.common.result;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.Getter;

/**
 * 统一响应体 {code, message, data}
 *
 * @param <T> 承载的数据类型
 */
@Getter
@JsonInclude(JsonInclude.Include.NON_NULL)
public class Result<T> {

    /** 统一响应或异常的状态码 */
    private int code;
    /** 统一响应的状态说明 */
    private String message;
    /** 统一响应承载的业务数据 */
    private T data;

    /** 创建空响应 */
    public Result() {}

    /**
     * 创建包含状态、消息和数据的响应
     *
     * @param code 响应状态码
     * @param message 向调用方展示的提示消息
     * @param data 附加响应数据，可为空；不进行复制
     */
    public Result(int code, String message, T data) {
        this.code = code;
        this.message = message;
        this.data = data;
    }

    /**
     * 创建表示成功的统一响应
     *
     * @param <T> 承载的数据类型
     * @param data 附加响应数据，可为空；不进行复制
     * @return 状态码为 200 的成功响应，附加数据保持传入值
     */
    public static <T> Result<T> success(T data) {
        return new Result<>(200, "success", data);
    }

    /**
     * 创建表示成功的统一响应
     *
     * @param <T> 承载的数据类型
     * @return 状态码为 200 且附加数据为空的成功响应
     */
    public static <T> Result<T> success() {
        return new Result<>(200, "success", null);
    }

    /**
     * 创建包含状态码、消息及可选数据的失败响应
     *
     * @param <T> 承载的数据类型
     * @param code 响应状态码
     * @param message 向调用方展示的提示消息
     * @return 包含传入状态码与消息的响应；未传数据时数据为空
     */
    public static <T> Result<T> error(int code, String message) {
        return new Result<>(code, message, null);
    }

    /**
     * 创建包含状态码、消息及可选数据的失败响应
     *
     * @param <T> 承载的数据类型
     * @param code 响应状态码
     * @param message 向调用方展示的提示消息
     * @param data 附加响应数据，可为空；不进行复制
     * @return 包含传入状态码与消息的响应；未传数据时数据为空
     */
    public static <T> Result<T> error(int code, String message, T data) {
        return new Result<>(code, message, data);
    }
}
