package top.zhaizz.animetracker.subject.service;

import top.zhaizz.animetracker.common.PageResult;
import top.zhaizz.animetracker.subject.vo.SubjectListVO;
import top.zhaizz.animetracker.subject.vo.TagVO;

import java.util.List;

public interface TagService {

    /** 返回所有标签（按 count 降序） */
    List<TagVO> listTags();

    /** 按标签名筛选条目（分页） */
    PageResult<SubjectListVO> listSubjectsByTag(String tagName, int page, int size);
}
