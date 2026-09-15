package top.zhaizz.admin.converter;

import org.junit.jupiter.api.Test;
import top.zhaizz.pojo.entity.Subject;
import top.zhaizz.pojo.entity.SubjectTag;
import top.zhaizz.pojo.vo.tag.TagVO;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.Arrays;
import java.util.List;
import static org.assertj.core.api.Assertions.*;

/** 条目详情与标签转换的空值、字段和顺序契约 */
class SubjectVoConverterTest {
    /** 空实体返回空值，空标签集合返回空集合 */
    @Test
    void acceptsAbsentInputs() {
        assertThat(SubjectVoConverter.toSubjectDetailVO(null, List.of())).isNull();
        assertThat(SubjectVoConverter.toTagVO(null)).isNull();
        assertThat(SubjectVoConverter.toTagVOList(null)).isEmpty();
        assertThat(SubjectVoConverter.toTagVOList(List.of())).isEmpty();
        var detail = SubjectVoConverter.toSubjectDetailVO(new Subject(), null);
        assertThat(detail.getTags()).isNull();
        assertThat(detail.getScore()).isNull();
    }

    /** 详情保留所有展示字段，并保持调用方提供的标签顺序和空元素 */
    @Test
    void mapsDetailWithoutChangingTags() {
        Subject source = new Subject();
        source.setId(42L); source.setBangumiId(420); source.setName("Original"); source.setNameCn("中文标题");
        source.setImage("cover"); source.setScore(new BigDecimal("8.25")); source.setRank(18);
        source.setEps(12); source.setAirDate(LocalDate.of(2026, 7, 1)); source.setType(2);
        source.setSummary("简介"); source.setVolumes(3); source.setAirWeekday(3);
        source.setCollectionTotal(800); source.setNsfw(false);
        source.setCreatedAt(LocalDateTime.of(2026, 1, 1, 0, 0));
        source.setUpdatedAt(LocalDateTime.of(2026, 9, 1, 0, 0));
        TagVO tag = new TagVO(); tag.setId(8L); tag.setName("科幻");
        List<TagVO> tags = Arrays.asList(tag, null);
        var result = SubjectVoConverter.toSubjectDetailVO(source, tags);
        assertThat(result).usingRecursiveComparison().comparingOnlyFields("id", "bangumiId", "name", "nameCn", "image",
                "score", "rank", "eps", "airDate", "type", "summary", "volumes", "airWeekday", "collectionTotal",
                "nsfw", "createdAt", "updatedAt").isEqualTo(source);
        assertThat(result.getTags()).containsExactly(tag, null);
        assertThat(result.getTags()).isSameAs(tags);
        assertThat(source.getNameCn()).isEqualTo("中文标题");
    }

    /** 标签转换保留输入顺序和空元素，创建独立标签响应并保留统计数量 */
    @Test
    void preservesTagOrderAndNullElements() {
        SubjectTag first = new SubjectTag(); first.setId(9L); first.setName("科幻"); first.setCount(20);
        SubjectTag last = new SubjectTag(); last.setId(2L); last.setName("冒险"); last.setCount(5);
        var result = SubjectVoConverter.toTagVOList(Arrays.asList(first, null, last));
        assertThat(result).hasSize(3);
        assertThat(result.get(1)).isNull();
        assertThat(result.get(0)).extracting("id", "name", "count").containsExactly(9L, "科幻", 20);
        assertThat(result.get(2)).extracting("id", "name", "count").containsExactly(2L, "冒险", 5);
        result.get(0).setName("已修改");
        assertThat(first.getName()).isEqualTo("科幻");
    }
}
