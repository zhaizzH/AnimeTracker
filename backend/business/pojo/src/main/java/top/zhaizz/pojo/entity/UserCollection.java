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

    private Long id;
    private Long userId;
    private Long subjectId;
    private Integer type;       // 1=想看 2=看过 3=在看 4=搁置 5=抛弃
    private Integer rate;       // 0-10，0 未评分
    private Integer epStatus;   // 剧集进度
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
