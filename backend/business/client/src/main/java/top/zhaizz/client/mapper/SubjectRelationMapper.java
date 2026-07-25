package top.zhaizz.client.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Param;
import top.zhaizz.pojo.entity.SubjectRelation;

import java.util.List;

/**
 * 条目关联 Mapper
 */
public interface SubjectRelationMapper extends BaseMapper<SubjectRelation> {

    /** 根据条目 ID 查询关联列表 */
    List<SubjectRelation> findBySubjectId(@Param("subjectId") Long subjectId);
}
