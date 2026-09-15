package top.zhaizz.admin.service;

import top.zhaizz.pojo.dto.subject.SubjectCreateDTO;
import top.zhaizz.pojo.dto.subject.SubjectUpdateDTO;
import top.zhaizz.pojo.vo.subject.SubjectDetailVO;

/**
 * 番剧管理服务接口
 */
public interface AdminSubjectService {
    /**
     * 创建新番剧
     * @param request 待创建的条目字段
     * @return 新建条目的详情
     * @throws top.zhaizz.common.exception.BizException Bangumi ID 已存在时为 CONFLICT
     */
    SubjectDetailVO createSubject(SubjectCreateDTO request);
    /**
     * 更新指定番剧
     * @param id 目标条目 ID
     * @param request 条目更新字段，空字段保留原值
     * @return 修改后的条目详情
     * @throws top.zhaizz.common.exception.BizException 条目不存在时为 NOT_FOUND
     */
    SubjectDetailVO updateSubject(Long id, SubjectUpdateDTO request);
    /**
     * 删除指定番剧
     * @param id 目标条目 ID
     * @throws top.zhaizz.common.exception.BizException 条目不存在时为 NOT_FOUND
     */
    void deleteSubject(Long id);
}
