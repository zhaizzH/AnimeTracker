package top.zhaizz.common.storage.minio;

import io.minio.MinioClient;
import io.minio.PutObjectArgs;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.mock.web.MockMultipartFile;
import top.zhaizz.common.config.MinioProperties;
import top.zhaizz.common.constant.ErrorType;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.common.storage.ImageCategory;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;

class MinioImageStorageGatewayTest {

    private MinioClient minioClient;
    private MinioImageStorageGateway gateway;

    @BeforeEach
    void setUp() {
        minioClient = mock(MinioClient.class);
        MinioProperties properties = new MinioProperties();
        properties.setEndpoint("http://minio:9000");
        properties.setBucket("anime");
        gateway = new MinioImageStorageGateway(minioClient, properties);
    }

    @Test
    void uploadsAvatarToAvatarDirectoryAndReturnsPublicUrl() throws Exception {
        MockMultipartFile file = new MockMultipartFile(
                "file", "avatar.png", "image/png", new byte[]{1, 2, 3});

        String url = gateway.upload(file, ImageCategory.AVATAR);

        ArgumentCaptor<PutObjectArgs> captor = ArgumentCaptor.forClass(PutObjectArgs.class);
        verify(minioClient).putObject(captor.capture());
        assertThat(captor.getValue().bucket()).isEqualTo("anime");
        assertThat(captor.getValue().object()).startsWith("avatars/").endsWith(".png");
        assertThat(url).startsWith("http://minio:9000/anime/avatars/").endsWith(".png");
    }

    @Test
    void rejectsUnsupportedContentTypeBeforeCallingMinio() {
        MockMultipartFile file = new MockMultipartFile(
                "file", "payload.txt", "text/plain", "not-image".getBytes());

        BizException error = assertThrows(BizException.class,
                () -> gateway.upload(file, ImageCategory.COVER));

        assertThat(error.getCode()).isEqualTo(ErrorType.BAD_REQUEST.getCode());
        assertThat(error.getMessage()).isEqualTo("仅支持 JPG/PNG/WebP 格式的图片");
        verifyNoInteractions(minioClient);
    }

    @Test
    void rejectsMissingContentTypeAsBadRequest() {
        MockMultipartFile file = new MockMultipartFile(
                "file", "payload", null, new byte[]{1});

        BizException error = assertThrows(BizException.class,
                () -> gateway.upload(file, ImageCategory.AVATAR));

        assertThat(error.getCode()).isEqualTo(ErrorType.BAD_REQUEST.getCode());
        assertThat(error.getMessage()).isEqualTo("仅支持 JPG/PNG/WebP 格式的图片");
        verifyNoInteractions(minioClient);
    }

    @Test
    void mapsMinioFailureToInternalErrorWithoutExposingCause() throws Exception {
        MockMultipartFile file = new MockMultipartFile(
                "file", "cover.webp", "image/webp", new byte[]{1});
        when(minioClient.putObject(any(PutObjectArgs.class)))
                .thenThrow(new RuntimeException("private minio address"));

        BizException error = assertThrows(BizException.class,
                () -> gateway.upload(file, ImageCategory.COVER));

        assertThat(error.getCode()).isEqualTo(ErrorType.INTERNAL_ERROR.getCode());
        assertThat(error.getMessage()).isEqualTo("文件上传失败");
        assertThat(error.getMessage()).doesNotContain("private minio address");
    }
}
