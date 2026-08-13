package top.zhaizz.admin.converter;

import top.zhaizz.pojo.dto.subject.SubjectCreateDTO;
import top.zhaizz.pojo.dto.subject.SubjectUpdateDTO;
import top.zhaizz.pojo.entity.ImportRecord;
import top.zhaizz.pojo.entity.Subject;
import top.zhaizz.pojo.vo.ImportRecordVO;

import java.util.List;
import java.util.stream.Collectors;

/**
 * 番剧相关对象转换器
 */
public class SubjectConverter {
    private SubjectConverter() {}

    /**
     * 创建 DTO 转为 Subject 实体
     */
    public static Subject toEntityFromCreate(SubjectCreateDTO request) {
        if (request == null) return null;
        Subject entity = new Subject();
        entity.setBangumiId(request.getBangumiId());
        entity.setName(request.getName());
        entity.setNameCn(request.getNameCn());
        entity.setSummary(request.getSummary());
        entity.setType(request.getType() != null ? request.getType() : 2); // 未指定时默认动画类型 2
        entity.setEps(request.getEps());
        entity.setAirDate(request.getAirDate());
        entity.setImage(request.getImage());
        return entity;
    }

    /**
     * 用更新 DTO 的非空字段更新 Subject 实体
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

    /**
     * ImportRecord 转为导入记录 VO
     */
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

    /**
     * ImportRecord 列表转为导入记录 VO 列表
     */
    public static List<ImportRecordVO> toImportRecordVOList(List<ImportRecord> entities) {
        if (entities == null) return List.of();
        return entities.stream()
                .map(SubjectConverter::toImportRecordVO)
                .collect(Collectors.toList());
    }
}
