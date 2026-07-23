package top.zhaizz.client.converter;

import top.zhaizz.pojo.vo.SubjectListVO;
import top.zhaizz.pojo.vo.UserCollectionSubjectVO;
import top.zhaizz.pojo.vo.UserCollectionVO;

import java.util.List;
import java.util.stream.Collectors;

/**
 * 收藏转换器
 */
public class CollectionConverter {
    private CollectionConverter() {}

    /** UserCollectionSubjectVO 转 UserCollectionVO */
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
        subject.setType(vo.getSubjectType());
        result.setSubject(subject);

        return result;
    }

    /** 列表转换 */
    public static List<UserCollectionVO> toUserCollectionVOList(List<UserCollectionSubjectVO> list) {
        if (list == null) return List.of();
        return list.stream()
                .map(CollectionConverter::toUserCollectionVO)
                .collect(Collectors.toList());
    }
}
