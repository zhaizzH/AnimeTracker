package top.zhaizz.subject.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import top.zhaizz.pojo.entity.SubjectTag;

import java.util.List;

/**
 * 条目-标签关联 Mapper
 */
public interface SubjectTagMapper extends BaseMapper<SubjectTag> {

    /**
     * 查询所有标签及其使用次数（按 count 降序）
     */
    List<SubjectTag> selectTagCountList();
}
