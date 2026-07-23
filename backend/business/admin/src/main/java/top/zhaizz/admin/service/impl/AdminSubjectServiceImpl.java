package top.zhaizz.admin.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import top.zhaizz.admin.converter.SubjectConverter;
import top.zhaizz.admin.mapper.AdminSubjectMapper;
import top.zhaizz.admin.mapper.AdminSubjectTagMapper;
import top.zhaizz.admin.service.AdminSubjectService;
import top.zhaizz.common.ErrorType;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.pojo.dto.SubjectCreateDTO;
import top.zhaizz.pojo.dto.SubjectUpdateDTO;
import top.zhaizz.pojo.entity.Subject;
import top.zhaizz.pojo.entity.SubjectTag;
import top.zhaizz.pojo.vo.SubjectDetailVO;
import top.zhaizz.pojo.vo.TagVO;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 番剧管理服务实现
 */
@Service
@RequiredArgsConstructor
public class AdminSubjectServiceImpl implements AdminSubjectService {

    private final AdminSubjectMapper subjectMapper;
    private final AdminSubjectTagMapper subjectTagMapper;

    @Override
    @Transactional
    public SubjectDetailVO createSubject(SubjectCreateDTO request) {
        if (request.getBangumiId() != null) {
            Long count = subjectMapper.selectCount(
                    new LambdaQueryWrapper<Subject>().eq(Subject::getBangumiId, request.getBangumiId())
            );
            if (count > 0) {
                throw new BizException(ErrorType.CONFLICT, "该 Bangumi 条目已存在");
            }
        }

        Subject subject = SubjectConverter.toEntityFromCreate(request);
        subject.setNsfw(false);
        subject.setImportStatus(0);
        subject.setCreatedAt(LocalDateTime.now());
        subject.setUpdatedAt(LocalDateTime.now());

        subjectMapper.insert(subject);
        return getSubjectDetail(subject.getId());
    }

    @Override
    @Transactional
    public SubjectDetailVO updateSubject(Long id, SubjectUpdateDTO request) {
        Subject subject = subjectMapper.selectById(id);
        if (subject == null) {
            throw new BizException(ErrorType.NOT_FOUND, "条目不存在");
        }

        SubjectConverter.updateFromRequest(subject, request);
        subject.setUpdatedAt(LocalDateTime.now());
        subjectMapper.updateById(subject);

        return getSubjectDetail(id);
    }

    @Override
    @Transactional
    public void deleteSubject(Long id) {
        Subject subject = subjectMapper.selectById(id);
        if (subject == null) {
            throw new BizException(ErrorType.NOT_FOUND, "条目不存在");
        }

        subjectMapper.deleteById(id);
    }

    private SubjectDetailVO getSubjectDetail(Long id) {
        Subject subject = subjectMapper.selectById(id);
        if (subject == null) {
            throw new BizException(ErrorType.NOT_FOUND, "条目不存在");
        }

        List<SubjectTag> tags = subjectTagMapper.selectList(
                new LambdaQueryWrapper<SubjectTag>().eq(SubjectTag::getSubjectId, id)
        );
        List<TagVO> tagVOs = SubjectConverter.toTagVOList(tags);

        return SubjectConverter.toSubjectDetailVO(subject, tagVOs);
    }
}
