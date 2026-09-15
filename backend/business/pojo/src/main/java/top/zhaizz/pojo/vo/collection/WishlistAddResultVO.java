package top.zhaizz.pojo.vo.collection;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 想看加入结果（幂等）：state=ADDED 表示新增成功；state=ALREADY_COLLECTED 表示已存在收藏，不覆盖
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@JsonInclude(JsonInclude.Include.NON_NULL)
public class WishlistAddResultVO {

    /** 加入状态：ADDED 为新增，ALREADY_COLLECTED 为已有收藏 */
    private String state;
    /** ALREADY_COLLECTED 时返回已存在收藏类型（1-5） */
    private Integer existingType;

    /**
     * 创建表示收藏已新增的结果对象
     *
     * @return 状态为 ADDED 且未设置已有收藏类型的结果
     */
    public static WishlistAddResultVO added() {
        return WishlistAddResultVO.builder().state("ADDED").build();
    }

    /**
     * 创建表示收藏已存在并携带原收藏类型的结果对象
     *
     * @param existingType 已有收藏类型，原样保存
     * @return 状态为 ALREADY_COLLECTED 并携带原收藏类型的结果
     */
    public static WishlistAddResultVO alreadyCollected(Integer existingType) {
        return WishlistAddResultVO.builder()
                .state("ALREADY_COLLECTED")
                .existingType(existingType)
                .build();
    }
}
