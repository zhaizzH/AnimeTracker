package top.zhaizz.client.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import org.apache.ibatis.annotations.Param;
import top.zhaizz.pojo.entity.UserCollection;
import top.zhaizz.pojo.vo.UserCollectionSubjectVO;

public interface CollectionMapper extends BaseMapper<UserCollection> {

    Page<UserCollectionSubjectVO> selectCollectionPage(
            Page<?> page,
            @Param("userId") Long userId,
            @Param("type") Integer type
    );
}
