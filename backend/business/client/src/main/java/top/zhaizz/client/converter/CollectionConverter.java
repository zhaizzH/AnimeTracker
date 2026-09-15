package top.zhaizz.client.converter;

import top.zhaizz.pojo.vo.subject.SubjectListVO;
import top.zhaizz.pojo.vo.collection.UserCollectionSubjectVO;
import top.zhaizz.pojo.vo.collection.UserCollectionVO;

import java.util.List;
import java.util.stream.Collectors;

/**
 * 收藏转换器
 */
public class CollectionConverter {
    /**
     * 禁止实例化仅提供静态操作的工具类
     */
    private CollectionConverter() {}

    /**
     * 将收藏与条目联合数据映射为收藏展示对象及新的嵌套条目对象
     * @param vo 联合查询结果，允许为 {@code null}
     * @return 新的收藏对象；输入为空时返回 {@code null}，不修改输入
     */
    public static UserCollectionVO toUserCollectionVO(UserCollectionSubjectVO vo) {
        if (vo == null) return null;
        UserCollectionVO result = new UserCollectionVO();
        result.setId(vo.getId());
        result.setSubjectId(vo.getSubjectId());
        result.setType(vo.getType());
        result.setRate(vo.getRate());
        result.setEpStatus(vo.getEpStatus());

        SubjectListVO subject = new SubjectListVO();
        subject.setId(vo.getSubjectId());
        subject.setName(vo.getName());
        subject.setNameCn(vo.getNameCn());
        subject.setImage(vo.getImage());
        subject.setScore(vo.getScore());
        subject.setEps(vo.getEps());
        subject.setAirDate(vo.getAirDate());
        subject.setAirWeekday(vo.getAirWeekday());
        subject.setType(vo.getSubjectType());
        result.setSubject(subject);

        return result;
    }

    /**
     * 按输入顺序转换收藏列表，不修改源列表与元素
     * @param list 联合查询结果，允许为 {@code null} 或包含空元素
     * @return 新列表，保留顺序和空元素；空输入返回空列表
     */
    public static List<UserCollectionVO> toUserCollectionVOList(List<UserCollectionSubjectVO> list) {
        if (list == null) return List.of();
        return list.stream()
                .map(CollectionConverter::toUserCollectionVO)
                .collect(Collectors.toList());
    }

    /**
     * 映射收藏自身字段，不查询或填充嵌套条目详情
     * @param entity 收藏实体，允许为 {@code null}
     * @return 新的简要收藏对象，subject 字段保持空；输入为空时返回 {@code null}
     */
    public static UserCollectionVO toSimpleVO(top.zhaizz.pojo.entity.UserCollection entity) {
        if (entity == null) return null;
        UserCollectionVO vo = new UserCollectionVO();
        vo.setId(entity.getId());
        vo.setSubjectId(entity.getSubjectId());
        vo.setType(entity.getType());
        vo.setRate(entity.getRate());
        vo.setEpStatus(entity.getEpStatus());
        return vo;
    }

}
