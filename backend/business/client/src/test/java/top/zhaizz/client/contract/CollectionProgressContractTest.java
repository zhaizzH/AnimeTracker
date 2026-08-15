package top.zhaizz.client.contract;

import org.junit.jupiter.api.Test;
import top.zhaizz.pojo.vo.collection.CollectionProgressPreviewVO;
import top.zhaizz.pojo.vo.collection.CollectionProgressState;

import java.lang.reflect.Field;
import java.util.Arrays;
import java.util.Set;
import java.util.stream.Collectors;

import static org.assertj.core.api.Assertions.assertThat;
import static top.zhaizz.pojo.vo.collection.CollectionProgressState.COMPLETED;
import static top.zhaizz.pojo.vo.collection.CollectionProgressState.PENDING;
import static top.zhaizz.pojo.vo.collection.CollectionProgressState.PREVIEW_CHANGED;

/**
 * 收藏进度契约测试：业务 VO 不重复包装 code/message/data
 */
class CollectionProgressContractTest {

    @Test
    void previewVoDoesNotDuplicateResultWrapperFields() {
        Set<String> names = Arrays.stream(CollectionProgressPreviewVO.class.getDeclaredFields())
                .map(Field::getName)
                .collect(Collectors.toSet());
        assertThat(names).doesNotContain("code", "message", "data");
        assertThat(CollectionProgressState.values())
                .containsExactly(PENDING, PREVIEW_CHANGED, COMPLETED);
    }
}
