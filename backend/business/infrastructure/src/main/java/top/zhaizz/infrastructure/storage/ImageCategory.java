package top.zhaizz.infrastructure.storage;

/**
 * 图片对象在存储桶中的固定业务分类
 */
public enum ImageCategory {
    /** 用户头像的对象目录 */
    AVATAR("avatars"),
    /** 条目封面的对象目录 */
    COVER("covers");

    /** 对象名前缀目录，不含斜杠 */
    private final String directory;

    /**
     * 定义对象存储分类
     * @param directory 对象目录名称
     */
    ImageCategory(String directory) {
        this.directory = directory;
    }

    /**
     * 返回该分类对应的对象目录
     * @return 不含斜杠的固定目录名
     */
    public String getDirectory() {
        return directory;
    }
}
