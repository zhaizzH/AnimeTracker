package top.zhaizz.client.converter;

import top.zhaizz.pojo.entity.Episode;
import top.zhaizz.pojo.entity.Subject;
import top.zhaizz.pojo.entity.SubjectRelation;
import top.zhaizz.pojo.vo.*;
import java.util.List;
import java.util.stream.Collectors;

/**
 * 条目转换器
 */
public class SubjectConverter {
    private SubjectConverter() {}

    /** Subject 转列表 VO */
    public static SubjectListVO toSubjectListVO(Subject entity) {
        if (entity == null) return null;
        SubjectListVO vo = new SubjectListVO();
        vo.setId(entity.getId());
        vo.setName(entity.getName());
        vo.setNameCn(entity.getNameCn());
        vo.setImage(entity.getImage());
        vo.setScore(entity.getScore());
        vo.setRank(entity.getRank());
        vo.setEps(entity.getEps());
        vo.setAirDate(entity.getAirDate());
        vo.setType(entity.getType());
        vo.setAirWeekday(entity.getAirWeekday());
        vo.setCollectionTotal(entity.getCollectionTotal());
        return vo;
    }

    /** Episode 转 VO */
    public static EpisodeVO toEpisodeVO(Episode entity) {
        if (entity == null) return null;
        EpisodeVO vo = new EpisodeVO();
        vo.setId(entity.getId());
        vo.setSubjectId(entity.getSubjectId());
        vo.setType(entity.getType());
        vo.setSort(entity.getSort());
        vo.setName(entity.getName());
        vo.setNameCn(entity.getNameCn());
        vo.setDuration(entity.getDuration());
        vo.setAirdate(entity.getAirdate());
        vo.setDescription(entity.getDescription());
        vo.setStatus(entity.getStatus());
        return vo;
    }

    /** Episode 列表转 VO 列表 */
    public static List<EpisodeVO> toEpisodeVOList(List<Episode> episodes) {
        if (episodes == null) return List.of();
        return episodes.stream().map(SubjectConverter::toEpisodeVO).collect(Collectors.toList());
    }

    /** SubjectRelation + Subject 转 relation VO */
    public static SubjectRelationVO toSubjectRelationVO(SubjectRelation relation, Subject relatedSubject) {
        if (relation == null || relatedSubject == null) return null;
        return new SubjectRelationVO(
                relation.getRelation(),
                toSubjectListVO(relatedSubject)
        );
    }
}
