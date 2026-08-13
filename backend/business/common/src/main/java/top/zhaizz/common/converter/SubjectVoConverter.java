package top.zhaizz.common.converter;

import top.zhaizz.pojo.entity.Subject;
import top.zhaizz.pojo.entity.SubjectTag;
import top.zhaizz.pojo.vo.subject.SubjectDetailVO;
import top.zhaizz.pojo.vo.tag.TagVO;

import java.util.List;
import java.util.stream.Collectors;

/** Subject 详情/标签转换器（admin 与 client 共用，消除重复） */
public final class SubjectVoConverter {
    private SubjectVoConverter() {}

    /** Subject 转详情 VO */
    public static SubjectDetailVO toSubjectDetailVO(Subject entity, List<TagVO> tags) {
        if (entity == null) return null;
        SubjectDetailVO vo = new SubjectDetailVO();
        vo.setId(entity.getId());
        vo.setName(entity.getName());
        vo.setNameCn(entity.getNameCn());
        vo.setImage(entity.getImage());
        vo.setScore(entity.getScore());
        vo.setRank(entity.getRank());
        vo.setEps(entity.getEps());
        vo.setAirDate(entity.getAirDate());
        vo.setType(entity.getType());
        vo.setBangumiId(entity.getBangumiId());
        vo.setSummary(entity.getSummary());
        vo.setVolumes(entity.getVolumes());
        vo.setAirWeekday(entity.getAirWeekday());
        vo.setCollectionTotal(entity.getCollectionTotal());
        vo.setNsfw(entity.getNsfw());
        vo.setTags(tags);
        vo.setCreatedAt(entity.getCreatedAt());
        vo.setUpdatedAt(entity.getUpdatedAt());
        return vo;
    }

    /** SubjectTag 转 TagVO */
    public static TagVO toTagVO(SubjectTag entity) {
        if (entity == null) return null;
        TagVO vo = new TagVO();
        vo.setId(entity.getId());
        vo.setName(entity.getName());
        vo.setCount(entity.getCount());
        return vo;
    }

    /** SubjectTag 列表转 TagVO 列表 */
    public static List<TagVO> toTagVOList(List<SubjectTag> tags) {
        if (tags == null) return List.of();
        return tags.stream().map(SubjectVoConverter::toTagVO).collect(Collectors.toList());
    }
}
