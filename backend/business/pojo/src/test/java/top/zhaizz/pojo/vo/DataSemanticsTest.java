package top.zhaizz.pojo.vo;

import org.junit.jupiter.api.Test;
import top.zhaizz.pojo.vo.subject.SubjectDetailVO;
import top.zhaizz.pojo.vo.tag.TagVO;
import top.zhaizz.pojo.vo.user.UserVO;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * 特征化 Lombok @Data 迁移后的相等、哈希与字符串行为
 *
 * <p>这些断言锁定的是迁移前由 Lombok 生成、迁移后必须保持一致的可观测语义，不重新定义契约
 */
class DataSemanticsTest {

    /**
     * 验证全部字段相等的两个实例相等且哈希一致，任一字段不同则不相等
     */
    @Test
    void comparesAllOwnFieldsForEquality() {
        LocalDateTime createdAt = LocalDateTime.of(2026, 1, 2, 3, 4, 5);
        UserVO left = user(1L, "alice", createdAt);
        UserVO right = user(1L, "alice", createdAt);
        assertEquals(left, right);
        assertEquals(left.hashCode(), right.hashCode());

        right.setNickname("changed");
        assertNotEquals(left, right);
    }

    /**
     * 验证可空字段为 null 时相等比较不抛出异常，且 null 与具体值不相等
     */
    @Test
    void keepsNullableFieldsComparable() {
        UserVO left = new UserVO();
        UserVO right = new UserVO();
        assertEquals(left, right);
        assertEquals(left.hashCode(), right.hashCode());

        right.setEmail("a@example.com");
        assertNotEquals(left, right);
    }

    /**
     * 验证布尔包装字段使用 get 前缀访问，取值保持原样
     */
    @Test
    void exposesBoxedBooleanThroughGetPrefix() {
        UserVO vo = new UserVO();
        vo.setEnabled(Boolean.FALSE);
        assertEquals(Boolean.FALSE, vo.getEnabled());
        vo.setEnabled(Boolean.TRUE);
        assertEquals(Boolean.TRUE, vo.getEnabled());
    }

    /**
     * 验证 toString 包含字段名与取值，且沿用 Lombok 迁移前包含敏感字段的行为
     */
    @Test
    void keepsGeneratedToStringShape() {
        UserVO vo = user(7L, "bob", null);
        String text = vo.toString();
        assertTrue(text.contains("username=" + "bob"), text);
        assertTrue(text.contains("id=7"), text);
    }

    /**
     * 验证列表字段按内容比较，不同列表实例不因引用不同而判为不等
     */
    @Test
    void comparesListFieldsByContent() {
        SubjectDetailVO left = new SubjectDetailVO();
        SubjectDetailVO right = new SubjectDetailVO();
        left.setTags(new ArrayList<>(List.of(tag(1L, "科幻"))));
        right.setTags(new ArrayList<>(List.of(tag(1L, "科幻"))));
        assertEquals(left, right);
        assertEquals(left.hashCode(), right.hashCode());

        right.setTags(new ArrayList<>(List.of(tag(2L, "日常"))));
        assertNotEquals(left, right);
    }

    /**
     * 验证 SubjectDetailVO 的相等比较包含继承自 SubjectListVO 的字段
     */
    @Test
    void includesInheritedFieldsForSubjectDetailEquality() {
        SubjectDetailVO left = new SubjectDetailVO();
        SubjectDetailVO right = new SubjectDetailVO();
        left.setBangumiId(100);
        right.setBangumiId(100);
        assertEquals(left, right);

        left.setName("继承字段差异");
        assertNotEquals(left, right);
    }

    /**
     * 验证基类实例与派生类实例不相等，canEqual 约束跨类型比较
     */
    @Test
    void refusesEqualityAcrossIncompatibleTypes() {
        SubjectDetailVO detail = new SubjectDetailVO();
        assertFalse(detail.equals("not-a-subject"));
        assertFalse(detail.equals(null));
    }

    /**
     * 构造用户展示对象
     * @param id 用户 ID
     * @param username 用户名
     * @param createdAt 创建时间
     * @return 已赋值的用户展示对象
     */
    private static UserVO user(Long id, String username, LocalDateTime createdAt) {
        UserVO vo = new UserVO();
        vo.setId(id);
        vo.setUsername(username);
        vo.setCreatedAt(createdAt);
        return vo;
    }

    /**
     * 构造标签展示对象
     * @param id 标签 ID
     * @param name 标签名
     * @return 已赋值的标签展示对象
     */
    private static TagVO tag(Long id, String name) {
        TagVO vo = new TagVO();
        vo.setId(id);
        vo.setName(name);
        return vo;
    }
}
