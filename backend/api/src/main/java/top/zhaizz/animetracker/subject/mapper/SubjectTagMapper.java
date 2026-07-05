package top.zhaizz.animetracker.subject.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Mapper;
import top.zhaizz.animetracker.subject.entity.SubjectTag;

import java.util.List;

/**
 * 条目-标签关联 Mapper
 */
@Mapper
public interface SubjectTagMapper extends BaseMapper<SubjectTag> {

    /**
     * 查询所有标签及其使用次数（按 count 降序）
     */
    List<SubjectTag> selectTagCountList();
}
