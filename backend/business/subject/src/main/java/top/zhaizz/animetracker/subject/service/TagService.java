package top.zhaizz.animetracker.subject.service;

import top.zhaizz.animetracker.common.result.PageResult;
import top.zhaizz.animetracker.common.vo.SubjectListVO;
import top.zhaizz.animetracker.common.vo.TagVO;

import java.util.List;

public interface TagService {

    /** 返回所有标签（按 count 降序） */
    List<TagVO> listTags();

    /** 按标签名筛选条目（分页） */
    PageResult<SubjectListVO> listSubjectsByTag(String tagName, int page, int size);
}
