package top.zhaizz.client.converter;

import org.junit.jupiter.api.Test;
import top.zhaizz.pojo.entity.UserCollection;
import top.zhaizz.pojo.vo.collection.UserCollectionSubjectVO;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.Arrays;
import java.util.List;
import static org.assertj.core.api.Assertions.*;

/** 收藏查询扁平结果与嵌套响应的映射契约。 */
class CollectionConverterTest {
    /** 空实体返回空值，空列表返回空集合。 */
    @Test
    void handlesAbsentInputs() {
        assertThat(CollectionConverter.toUserCollectionVO(null)).isNull();
        assertThat(CollectionConverter.toSimpleVO(null)).isNull();
        assertThat(CollectionConverter.toUserCollectionVOList(null)).isEmpty();
        assertThat(CollectionConverter.toUserCollectionVOList(List.of())).isEmpty();
    }

    /** 收藏类型与条目类型分别映射，查询字段完整填入嵌套条目。 */
    @Test
    void mapsCollectionAndNestedSubject() {
        UserCollectionSubjectVO row = new UserCollectionSubjectVO();
        row.setId(7L); row.setSubjectId(42L); row.setType(3); row.setRate(0); row.setEpStatus(5);
        row.setName("Original"); row.setNameCn("中文标题"); row.setImage("cover");
        row.setScore(new BigDecimal("8.5")); row.setEps(12); row.setAirDate(LocalDate.of(2026, 7, 1));
        row.setAirWeekday(3); row.setSubjectType(2);
        var result = CollectionConverter.toUserCollectionVO(row);
        assertThat(result).extracting("id", "subjectId", "type", "rate", "epStatus").containsExactly(7L, 42L, 3, 0, 5);
        assertThat(result.getSubject()).extracting("id", "name", "nameCn", "image", "score", "eps", "airDate", "airWeekday", "type")
                .containsExactly(42L, "Original", "中文标题", "cover", new BigDecimal("8.5"), 12, LocalDate.of(2026, 7, 1), 3, 2);
        result.getSubject().setName("修改");
        assertThat(row.getName()).isEqualTo("Original");
    }

    /** 列表不排序、不丢弃空元素，缺失的条目字段保持空值。 */
    @Test
    void preservesOrderAndNullFields() {
        UserCollectionSubjectVO first = new UserCollectionSubjectVO(); first.setId(9L);
        UserCollectionSubjectVO last = new UserCollectionSubjectVO(); last.setId(2L);
        var result = CollectionConverter.toUserCollectionVOList(Arrays.asList(first, null, last));
        assertThat(result).hasSize(3);
        assertThat(result.get(0).getId()).isEqualTo(9L);
        assertThat(result.get(1)).isNull();
        assertThat(result.get(2).getId()).isEqualTo(2L);
        assertThat(result.get(0).getSubject()).isNotNull();
        assertThat(result.get(0).getSubject().getName()).isNull();
        assertThat(result.get(0).getRate()).isNull();
    }

    /** 简要响应保留收藏字段而不虚构未查询的条目详情。 */
    @Test
    void mapsSimpleCollectionWithoutSubject() {
        UserCollection source = new UserCollection();
        source.setId(7L); source.setSubjectId(42L); source.setType(3); source.setRate(8); source.setEpStatus(5);
        var result = CollectionConverter.toSimpleVO(source);
        assertThat(result).extracting("id", "subjectId", "type", "rate", "epStatus").containsExactly(7L, 42L, 3, 8, 5);
        assertThat(result.getSubject()).isNull();
    }
}
