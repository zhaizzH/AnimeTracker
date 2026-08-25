package top.zhaizz.common.storage;

/**
 * 图片对象在存储桶中的固定业务分类
 */
public enum ImageCategory {
    AVATAR("avatars"),
    COVER("covers");

    private final String directory;

    ImageCategory(String directory) {
        this.directory = directory;
    }

    /**
     * 返回该分类对应的对象目录
     */
    public String getDirectory() {
        return directory;
    }
}
