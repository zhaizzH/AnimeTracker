package top.zhaizz.client.model;

import lombok.Data;

/** 当前 MySQL 词法/向量双投影的发布指针。 */
@Data
public class SearchIndexReleaseRow {
    /** 检索索引版本标识。 */
    private String indexVersion;
    /** 检索配置版本标识。 */
    private String profileVersion;
}
