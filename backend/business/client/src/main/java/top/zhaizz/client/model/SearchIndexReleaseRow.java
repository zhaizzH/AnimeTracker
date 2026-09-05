package top.zhaizz.client.model;

import lombok.Data;

/** 当前 MySQL 词法/向量双投影的发布指针。 */
@Data
public class SearchIndexReleaseRow {
    private String indexVersion;
    private String profileVersion;
}
