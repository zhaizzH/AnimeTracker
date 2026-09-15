package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 用户追番收藏实体
 */
@Data
@TableName("user_collection")
public class UserCollection {

    /** 收藏ID */
    private Long id;                    // 收藏ID
    /** 用户ID */
    private Long userId;                // 用户ID
    /** 条目ID */
    private Long subjectId;             // 条目ID
    /** 收藏状态: 1=想看, 2=看过, 3=在看, 4=搁置, 5=抛弃 */
    private Integer type;               // 收藏状态: 1=想看, 2=看过, 3=在看, 4=搁置, 5=抛弃
    /** 评分（0~10, 0 表示未评分） */
    private Integer rate;               // 评分（0~10, 0 表示未评分）
    /** 看到第几集 */
    private Integer epStatus;           // 看到第几集
    /** 创建时间 */
    private LocalDateTime createdAt;    // 创建时间
    /** 更新时间 */
    private LocalDateTime updatedAt;    // 更新时间
}
