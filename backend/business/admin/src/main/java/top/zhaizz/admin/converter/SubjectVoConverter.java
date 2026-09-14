package top.zhaizz.admin.converter;

import top.zhaizz.pojo.entity.Subject;
import top.zhaizz.pojo.entity.SubjectTag;
import top.zhaizz.pojo.vo.subject.SubjectDetailVO;
import top.zhaizz.pojo.vo.tag.TagVO;

import java.util.List;
import java.util.stream.Collectors;

/** 管理端条目详情与标签映射；由本模块独立维护。 */
public final class SubjectVoConverter {
    /**
     * 禁止实例化仅提供静态操作的工具类。
     */
    private SubjectVoConverter() {}

    /**
     * 映射条目详情，并引用调用方提供的标签列表，不查询关联数据。
     * @param entity 条目实体，允许为 {@code null}
     * @param tags 标签列表，允许为 {@code null}，不复制列表或元素
     * @return 新的详情对象；实体为空时返回 {@code null}，不修改输入
     */
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

    /**
     * 将条目标签映射为新的标签展示对象。
     * @param entity 标签实体，允许为 {@code null}
     * @return 含 ID、名称和次数的展示对象；输入为空时返回 {@code null}，不修改实体
     */
    public static TagVO toTagVO(SubjectTag entity) {
        if (entity == null) return null;
        TagVO vo = new TagVO();
        vo.setId(entity.getId());
        vo.setName(entity.getName());
        vo.setCount(entity.getCount());
        return vo;
    }

    /**
     * 按输入顺序映射标签，不修改源列表与元素。
     * @param tags 标签列表，允许为 {@code null} 或包含空元素
     * @return 新列表，保留顺序和空元素；空输入返回空列表
     */
    public static List<TagVO> toTagVOList(List<SubjectTag> tags) {
        if (tags == null) return List.of();
        return tags.stream().map(SubjectVoConverter::toTagVO).collect(Collectors.toList());
    }
}

