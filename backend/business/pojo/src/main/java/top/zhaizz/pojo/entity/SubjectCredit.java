package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 旧版条目主创关联实体
 *
 * 新导入关系使用 subject_person_credit；该实体保留 subject_credit 的
 * 兼容读取契约，避免存量数据窗口内 ORM 映射缺失
 */
@Data
@TableName("subject_credit")
public class SubjectCredit {

    /** 记录或资源的唯一标识 */
    private Long id;
    /** 关联条目标识 */
    private Long subjectId;
    /** Bangumi 人物标识 */
    private Integer bangumiPersonId;
    /** 来源数据的原始名称 */
    private String name;
    /** 人员或角色在关系中的职务 */
    private String role;
    /** 主创类型：PERSON 为个人，ORGANIZATION 为组织 */
    private String creditType;
    /** 同级记录的排序序号 */
    private Integer sortOrder;
    /** 来源记录是否仍有效 */
    private Boolean sourceActive;
    /** 记录创建时间 */
    private LocalDateTime createdAt;
    /** 记录最后更新时间 */
    private LocalDateTime updatedAt;
}
