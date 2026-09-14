package top.zhaizz.client.service;

import top.zhaizz.common.result.PageResult;
import top.zhaizz.pojo.vo.subject.SubjectListVO;
import top.zhaizz.pojo.vo.tag.TagVO;

import java.util.List;

/**
 * 标签服务接口。
 */
public interface TagService {

    /**
     * 返回所有标签（按 count 降序）。
     * @return 按使用次数降序排列的标签
     */
    List<TagVO> listTags();

    /**
     * 按标签名筛选条目（分页）。
     * @param tagName 用于匹配条目的标签名称
     * @param page 分页页码，从 1 开始
     * @param size 每页记录数
     * @return 匹配标签的条目分页
     */
    PageResult<SubjectListVO> listSubjectsByTag(String tagName, int page, int size);
}
