package top.zhaizz.pojo.vo.collection;

import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotSame;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * 特征化 {@code @Builder.Default} 迁移后的构建器默认值与显式空值语义
 *
 * <p>这些断言锁定迁移前由 Lombok 生成、迁移后必须保持一致的可观测行为：省略的列表字段在
 * {@code build()} 时获得新的空列表，显式传入 {@code null} 则保持 {@code null}，
 * {@code @Builder.Default} 字段的无参构造同样初始化为独立空列表
 */
class BuilderDefaultsTest {

    /**
     * 验证未设置列表字段时 build() 给出空列表，且每次构建互不共享实例
     */
    @Test
    void fillsUnsetListDefaultsWithFreshEmptyLists() {
        CollectionProgressExecutionVO first = CollectionProgressExecutionVO.builder().build();
        CollectionProgressExecutionVO second = CollectionProgressExecutionVO.builder().build();

        assertEquals(List.of(), first.getSucceeded());
        assertEquals(List.of(), first.getSkipped());
        assertEquals(List.of(), first.getFailed());
        assertNotSame(first.getSucceeded(), second.getSucceeded());
        assertNotSame(first.getSkipped(), second.getSkipped());
        assertNotSame(first.getFailed(), second.getFailed());
    }

    /**
     * 验证显式传入 null 与省略字段含义不同，显式 null 在 build() 后保持 null
     */
    @Test
    void keepsExplicitNullDistinctFromOmitted() {
        CollectionProgressExecutionVO omitted = CollectionProgressExecutionVO.builder().build();
        CollectionProgressExecutionVO explicit = CollectionProgressExecutionVO.builder()
                .succeeded(null)
                .skipped(null)
                .failed(null)
                .build();

        assertTrue(omitted.getSucceeded().isEmpty());
        assertNull(explicit.getSucceeded());
        assertNull(explicit.getSkipped());
        assertNull(explicit.getFailed());
    }

    /**
     * 验证显式传入的列表按引用保存，构建器不复制也不替换为默认空列表
     */
    @Test
    void preservesExplicitListReference() {
        List<CollectionProgressItemVO> succeeded = new ArrayList<>();
        CollectionProgressExecutionVO result = CollectionProgressExecutionVO.builder()
                .succeeded(succeeded)
                .build();

        assertSame(succeeded, result.getSucceeded());
    }

    /**
     * 验证无参构造独立于构建器默认，三个列表字段均为空列表
     */
    @Test
    void initializesNoArgConstructionLists() {
        CollectionProgressExecutionVO vo = new CollectionProgressExecutionVO();

        assertEquals(List.of(), vo.getSucceeded());
        assertEquals(List.of(), vo.getSkipped());
        assertEquals(List.of(), vo.getFailed());
    }

    /**
     * 验证标量字段沿用 Java 默认值，未设置时状态为 null、replayed 为 false
     */
    @Test
    void leavesScalarFieldsAtJavaDefaults() {
        CollectionProgressExecutionVO vo = CollectionProgressExecutionVO.builder().build();

        assertNull(vo.getState());
        assertNull(vo.getPreview());
        assertFalse(vo.isReplayed());
    }
}
