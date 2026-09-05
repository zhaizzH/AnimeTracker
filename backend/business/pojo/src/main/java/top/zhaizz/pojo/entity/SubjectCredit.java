package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 旧版条目主创关联实体。
 *
 * 新导入关系使用 subject_person_credit；该实体保留 subject_credit 的
 * 兼容读取契约，避免存量数据窗口内 ORM 映射缺失。
 */
@Data
@TableName("subject_credit")
public class SubjectCredit {

    private Long id;
    private Long subjectId;
    private Integer bangumiPersonId;
    private String name;
    private String role;
    private String creditType;       // PERSON / ORGANIZATION
    private Integer sortOrder;
    private Boolean sourceActive;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
