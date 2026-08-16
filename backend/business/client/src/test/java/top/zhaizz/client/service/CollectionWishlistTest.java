package top.zhaizz.client.service;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.dao.DuplicateKeyException;
import top.zhaizz.client.mapper.CollectionMapper;
import top.zhaizz.client.mapper.SubjectMapper;
import top.zhaizz.client.service.impl.CollectionServiceImpl;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.pojo.entity.Subject;
import top.zhaizz.pojo.entity.UserCollection;
import top.zhaizz.pojo.vo.collection.WishlistAddResultVO;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.argThat;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

/**
 * 想看加入接口测试：原子幂等、不覆盖已有收藏、唯一键并发竞态
 */
@ExtendWith(MockitoExtension.class)
class CollectionWishlistTest {

    @Mock
    private CollectionMapper collectionMapper;
    @Mock
    private SubjectMapper subjectMapper;

    private CollectionServiceImpl service;

    @BeforeEach
    void setUp() {
        service = new CollectionServiceImpl(collectionMapper, subjectMapper);
    }

    @Test
    void addsMissingCollectionAsWishlist() {
        when(subjectMapper.selectById(7L)).thenReturn(new Subject());
        when(collectionMapper.selectOne(any())).thenReturn(null);

        WishlistAddResultVO result = service.addToWishlistIfAbsent(3L, 7L);

        assertThat(result.getState()).isEqualTo("ADDED");
        verify(collectionMapper).insert(argThat(c -> c.getType() == 1 && c.getEpStatus() == 0));
    }

    @Test
    void preservesExistingCollection() {
        UserCollection existing = new UserCollection();
        existing.setType(3);
        when(subjectMapper.selectById(7L)).thenReturn(new Subject());
        when(collectionMapper.selectOne(any())).thenReturn(existing);

        WishlistAddResultVO result = service.addToWishlistIfAbsent(3L, 7L);

        assertThat(result.getState()).isEqualTo("ALREADY_COLLECTED");
        assertThat(result.getExistingType()).isEqualTo(3);
        verify(collectionMapper, never()).insert(any());
    }

    @Test
    void missingSubjectThrowsNotFound() {
        when(subjectMapper.selectById(7L)).thenReturn(null);

        assertThatThrownBy(() -> service.addToWishlistIfAbsent(3L, 7L))
                .isInstanceOfSatisfying(BizException.class, e -> assertThat(e.getCode()).isEqualTo(404));
        verify(collectionMapper, never()).selectOne(any());
        verify(collectionMapper, never()).insert(any());
    }

    @Test
    void duplicateKeyRaceReReadsAndReturnsAlreadyCollected() {
        // READ_COMMITTED 下每个语句读取最新已提交数据：唯一键冲突后重读能看到并发写入行（REPEATABLE READ 快照则看不到）
        UserCollection raced = new UserCollection();
        raced.setType(2);
        when(subjectMapper.selectById(7L)).thenReturn(new Subject());
        when(collectionMapper.selectOne(any()))
                .thenReturn(null)
                .thenReturn(raced);
        org.mockito.Mockito.doThrow(new DuplicateKeyException("dup"))
                .when(collectionMapper).insert(any());

        WishlistAddResultVO result = service.addToWishlistIfAbsent(3L, 7L);

        assertThat(result.getState()).isEqualTo("ALREADY_COLLECTED");
        assertThat(result.getExistingType()).isEqualTo(2);
    }
}
