package top.zhaizz.admin.converter;

import top.zhaizz.pojo.dto.subject.SubjectCreateDTO;
import top.zhaizz.pojo.dto.subject.SubjectUpdateDTO;
import top.zhaizz.pojo.entity.ImportRecord;
import top.zhaizz.pojo.entity.Subject;
import top.zhaizz.pojo.vo.imprt.ImportRecordVO;

import java.util.List;
import java.util.stream.Collectors;

/**
 * 番剧相关对象转换器
 */
public class SubjectConverter {
    /**
     * 禁止实例化仅提供静态操作的工具类
     */
    private SubjectConverter() {}

    /**
     * 映射创建请求为新实体，未指定类型时使用动画类型 2
     * @param request 创建内容，允许为 {@code null}
     * @return 新实体；输入为空时返回 {@code null}，不修改请求或持久化
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
     * 将请求中的非空字段覆盖到条目实体，空字段保留原值
     * @param subject 被原地修改的目标实体，非空
     * @param request 更新请求，非空；不支持通过空字段清除旧值
     * @throws NullPointerException 请求为空，或条目为空且有字段需要更新
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
     * 将导入记录映射为展示对象，seasonKey 映射到 season
     * @param entity 导入记录，允许为 {@code null}
     * @return 新对象；输入为空时返回 {@code null}，不修改实体
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
     * 按输入顺序映射导入记录，不修改源列表或元素
     * @param entities 导入记录列表，允许为 {@code null} 或包含空元素
     * @return 新列表，保留顺序和空元素；空输入返回空列表
     */
    public static List<ImportRecordVO> toImportRecordVOList(List<ImportRecord> entities) {
        if (entities == null) return List.of();
        return entities.stream()
                .map(SubjectConverter::toImportRecordVO)
                .collect(Collectors.toList());
    }
}
