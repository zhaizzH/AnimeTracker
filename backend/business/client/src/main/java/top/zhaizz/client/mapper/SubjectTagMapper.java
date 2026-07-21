package top.zhaizz.client.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import top.zhaizz.pojo.entity.SubjectTag;
import java.util.List;

public interface SubjectTagMapper extends BaseMapper<SubjectTag> {
    List<SubjectTag> selectTagCountList();
}
