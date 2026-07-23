package top.zhaizz.client.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import top.zhaizz.pojo.entity.SubjectTag;
import java.util.List;

/** 标签 Mapper */
public interface SubjectTagMapper extends BaseMapper<SubjectTag> {
    /** 查询标签及其关联条目数量 */
    List<SubjectTag> selectTagCountList();
}
