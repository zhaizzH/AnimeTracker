package top.zhaizz.subject.converter;

import top.zhaizz.pojo.dto.SubjectCreateDTO;
import top.zhaizz.pojo.dto.SubjectUpdateDTO;
import top.zhaizz.pojo.entity.Episode;
import top.zhaizz.pojo.entity.ImportRecord;
import top.zhaizz.pojo.entity.Subject;
import top.zhaizz.pojo.entity.SubjectTag;
import top.zhaizz.pojo.vo.*;

import java.util.List;
import java.util.stream.Collectors;

/**
 * 实体 ↔ VO 转换工具类
 */
public class SubjectConverter {

    private SubjectConverter() {}

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
        return vo;
    }

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

    public static List<EpisodeVO> toEpisodeVOList(List<Episode> episodes) {
        if (episodes == null) return List.of();
        return episodes.stream()
                .map(SubjectConverter::toEpisodeVO)
                .collect(Collectors.toList());
    }

    public static TagVO toTagVO(SubjectTag entity) {
        if (entity == null) return null;
        TagVO vo = new TagVO();
        vo.setId(entity.getId());
        vo.setName(entity.getName());
        vo.setCount(entity.getCount());
        return vo;
    }

    public static List<TagVO> toTagVOList(List<SubjectTag> tags) {
        if (tags == null) return List.of();
        return tags.stream()
                .map(SubjectConverter::toTagVO)
                .collect(Collectors.toList());
    }

    public static ImportRecordVO toImportRecordVO(ImportRecord entity) {
        if (entity == null) return null;
        ImportRecordVO vo = new ImportRecordVO();
        vo.setId(entity.getId());
        vo.setSeason(entity.getSeasonKey());
        vo.setStartedAt(entity.getStartedAt());
        vo.setCompletedAt(entity.getCompletedAt());
        vo.setStatus(entity.getStatus());
        vo.setSubjectCount(entity.getSubjectCount());
        vo.setErrorMessage(entity.getErrorMessage());
        return vo;
    }

    public static List<ImportRecordVO> toImportRecordVOList(List<ImportRecord> entities) {
        if (entities == null) return List.of();
        return entities.stream()
                .map(SubjectConverter::toImportRecordVO)
                .collect(Collectors.toList());
    }

    /**
     * 将 SubjectCreateDTO 的非空字段映射到实体
     */
    public static Subject toEntityFromCreate(SubjectCreateDTO request) {
        if (request == null) return null;
        Subject entity = new Subject();
        entity.setBangumiId(request.getBangumiId());
        entity.setName(request.getName());
        entity.setNameCn(request.getNameCn());
        entity.setSummary(request.getSummary());
        entity.setType(request.getType() != null ? request.getType() : 2);
        entity.setEps(request.getEps());
        entity.setAirDate(request.getAirDate());
        entity.setImage(request.getImage());
        return entity;
    }

    /**
     * 将 SubjectUpdateDTO 的非空字段合并到已有实体
     */
    public static void updateFromRequest(Subject subject, SubjectUpdateDTO request) {
        if (request.getName() != null) subject.setName(request.getName());
        if (request.getNameCn() != null) subject.setNameCn(request.getNameCn());
        if (request.getSummary() != null) subject.setSummary(request.getSummary());
        if (request.getType() != null) subject.setType(request.getType());
        if (request.getEps() != null) subject.setEps(request.getEps());
        if (request.getAirDate() != null) subject.setAirDate(request.getAirDate());
        if (request.getImage() != null) subject.setImage(request.getImage());
    }
}
