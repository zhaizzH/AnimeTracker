package top.zhaizz.client.service;

import top.zhaizz.common.result.PageResult;
import top.zhaizz.pojo.vo.SubjectListVO;
import top.zhaizz.pojo.vo.TagVO;

import java.util.List;

/**
 * 标签服务接口
 */
public interface TagService {

    /** 返回所有标签（按 count 降序） */
    List<TagVO> listTags();

    /** 按标签名筛选条目（分页） */
    PageResult<SubjectListVO> listSubjectsByTag(String tagName, int page, int size);
}
