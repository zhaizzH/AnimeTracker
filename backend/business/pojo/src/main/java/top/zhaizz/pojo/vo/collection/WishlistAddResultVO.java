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

    private String state;           // ADDED | ALREADY_COLLECTED
    private Integer existingType;   // ALREADY_COLLECTED 时返回已存在收藏类型（1-5）

    public static WishlistAddResultVO added() {
        return WishlistAddResultVO.builder().state("ADDED").build();
    }

    public static WishlistAddResultVO alreadyCollected(Integer existingType) {
        return WishlistAddResultVO.builder()
                .state("ALREADY_COLLECTED")
                .existingType(existingType)
                .build();
    }
}
