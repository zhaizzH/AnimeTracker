package top.zhaizz.client.converter;

import top.zhaizz.pojo.entity.Episode;
import top.zhaizz.pojo.entity.Subject;
import top.zhaizz.pojo.entity.SubjectRelation;
import top.zhaizz.pojo.vo.subject.EpisodeVO;
import top.zhaizz.pojo.vo.subject.SubjectListVO;
import top.zhaizz.pojo.vo.subject.SubjectRelationVO;
import java.time.LocalDate;
import java.util.List;
import java.util.stream.Collectors;

/**
 * 条目转换器。
 */
public class SubjectConverter {
    /**
     * 禁止实例化仅提供静态操作的工具类。
     */
    private SubjectConverter() {}

    /**
     * 将条目基本信息映射为列表展示对象，不修改实体。
     * @param entity 条目实体，允许为 {@code null}
     * @return 新的列表项；输入为空时返回 {@code null}
     */
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

    /**
     * 映射剧集信息，并按系统当前日期计算播出状态，不修改实体。
     * @param entity 剧集实体，允许为 {@code null}
     * @return 新的剧集对象；过去播出为 Air、今日为 Today、未来或日期缺失为 NA；实体为空返回 {@code null}
     */
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
        vo.setStatus(computeStatus(entity.getAirdate()));
        return vo;
    }

    /**
     * 以系统默认时区的当前日期判断剧集是否播出。
     * @param airdate 播出日期，允许为 {@code null}
     * @return 过去日期返回 Air，今日返回 Today，未来或空日期返回 NA
     */
    private static String computeStatus(LocalDate airdate) {
        if (airdate == null) return "NA";
        LocalDate today = LocalDate.now();
        if (airdate.isBefore(today)) return "Air";
        if (airdate.isEqual(today)) return "Today";
        return "NA";
    }

    /**
     * 按输入顺序转换剧集列表，不修改源列表与元素。
     * @param episodes 剧集列表，允许为 {@code null} 或包含空元素
     * @return 新列表，保留顺序和空元素；空输入返回空列表
     */
    public static List<EpisodeVO> toEpisodeVOList(List<Episode> episodes) {
        if (episodes == null) return List.of();
        return episodes.stream().map(SubjectConverter::toEpisodeVO).collect(Collectors.toList());
    }

    /**
     * 映射关系名称并创建嵌套的关联条目列表项，不修改输入。
     * @param relation 条目关联记录，允许为 {@code null}
     * @param relatedSubject 关联目标条目，允许为 {@code null}
     * @return 新的关联展示对象；任一输入为空时返回 {@code null}
     */
    public static SubjectRelationVO toSubjectRelationVO(SubjectRelation relation, Subject relatedSubject) {
        if (relation == null || relatedSubject == null) return null;
        return new SubjectRelationVO(
                relation.getRelation(),
                toSubjectListVO(relatedSubject)
        );
    }

    /**
     * 映射批量回查展示字段，以导入状态恰为 1 判定 active。
     * @param subject 条目实体，允许为 {@code null}
     * @return 新的批量项；输入为空返回 {@code null}，不修改实体
     */
    public static top.zhaizz.pojo.vo.subject.SubjectBatchItemVO toBatchItemVO(Subject subject) {
        if (subject == null) return null;
        var item = new top.zhaizz.pojo.vo.subject.SubjectBatchItemVO();
        item.setId(subject.getId());
        item.setName(subject.getName());
        item.setNameCn(subject.getNameCn());
        item.setImage(subject.getImage());
        item.setScore(subject.getScore());
        item.setRatingTotal(subject.getRatingTotal());
        item.setCollectionTotal(subject.getCollectionTotal());
        item.setAirDate(subject.getAirDate());
        item.setType(subject.getType());
        item.setNsfw(subject.getNsfw());
        item.setActive(Integer.valueOf(1).equals(subject.getImportStatus()));
        return item;
    }

}
