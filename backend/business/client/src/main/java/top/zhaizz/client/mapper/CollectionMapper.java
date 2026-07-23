package top.zhaizz.client.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import org.apache.ibatis.annotations.Param;
import top.zhaizz.pojo.entity.UserCollection;
import top.zhaizz.pojo.vo.UserCollectionSubjectVO;

/** 收藏 Mapper */
public interface CollectionMapper extends BaseMapper<UserCollection> {

    /** 分页查询用户收藏列表（含番剧信息） */
    Page<UserCollectionSubjectVO> selectCollectionPage(
            Page<?> page,
            @Param("userId") Long userId,
            @Param("type") Integer type
    );
}
