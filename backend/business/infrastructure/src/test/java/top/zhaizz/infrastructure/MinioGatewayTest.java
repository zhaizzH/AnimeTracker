package top.zhaizz.infrastructure;

import io.minio.MinioClient;
import io.minio.PutObjectArgs;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.mock.web.MockMultipartFile;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.infrastructure.storage.ImageCategory;
import top.zhaizz.infrastructure.storage.minio.MinioConfig;
import top.zhaizz.infrastructure.storage.minio.MinioImageStorageGateway;
import top.zhaizz.infrastructure.storage.minio.MinioProperties;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

/** 验证上传分类、对象名与失败行为在迁移后保持一致 */
class MinioGatewayTest {
    /** 上传保留 MIME 和桶，使用服务端名称生成公开 URL */
    @Test
    void uploadsIntoCategoryWithGeneratedName() throws Exception {
        MinioClient client = mock(MinioClient.class);
        MinioProperties properties = properties();
        var gateway = new MinioImageStorageGateway(client, properties);
        String url = gateway.upload(new MockMultipartFile("file", "unsafe.png", "image/png", new byte[]{1}), ImageCategory.AVATAR);
        ArgumentCaptor<PutObjectArgs> args = ArgumentCaptor.forClass(PutObjectArgs.class);
        verify(client).putObject(args.capture());
        assertEquals("images", args.getValue().bucket());
        assertTrue(args.getValue().object().matches("avatars/[0-9a-f-]+\\.png"));
        assertEquals("http://storage/images/" + args.getValue().object(), url);
    }

    /** 不支持的类型拒绝上传，SDK 故障映射为既有业务错误 */
    @Test
    void rejectsUnsupportedTypeAndMapsUploadFailure() throws Exception {
        MinioClient client = mock(MinioClient.class);
        var gateway = new MinioImageStorageGateway(client, properties());
        assertThrows(BizException.class, () -> gateway.upload(new MockMultipartFile("file", "a.gif", "image/gif", new byte[]{1}), ImageCategory.COVER));
        verifyNoInteractions(client);
        when(client.putObject(any(PutObjectArgs.class))).thenThrow(new IllegalStateException("offline"));
        assertEquals("文件上传失败", assertThrows(BizException.class, () -> gateway.upload(new MockMultipartFile("file", "a.png", "image/png", new byte[]{1}), ImageCategory.COVER)).getMessage());
    }

    /** 桶初始化连接失败返回 false，不阻断应用装配 */
    @Test
    void bucketFailureDoesNotAbortStartup() throws Exception {
        MinioClient client = mock(MinioClient.class);
        when(client.bucketExists(any())).thenThrow(new IllegalStateException("offline"));
        assertFalse(new MinioConfig(properties()).initMinioBucket(client));
    }

    /**
     * 提供不连接外部服务的存储配置
     * @return 测试使用的端点与桶
     */
    private MinioProperties properties() {
        MinioProperties properties = new MinioProperties();
        properties.setEndpoint("http://storage");
        properties.setBucket("images");
        return properties;
    }
}
