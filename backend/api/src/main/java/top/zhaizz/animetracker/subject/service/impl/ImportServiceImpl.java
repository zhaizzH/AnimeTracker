package top.zhaizz.animetracker.subject.service.impl;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import top.zhaizz.animetracker.common.entity.ImportRecord;
import top.zhaizz.animetracker.subject.converter.SubjectConverter;
import top.zhaizz.animetracker.subject.mapper.ImportRecordMapper;
import top.zhaizz.animetracker.subject.service.ImportService;
import top.zhaizz.animetracker.common.vo.ImportStatusVO;

import java.util.List;

/**
 * 数据导入服务实现
 * <p>
 * 导入的实际执行由 data-importer/ Python 脚本完成。
 * <p>
 * 本服务提供：
 * <p>
 * 1. 触发导入（记录请求或调用脚本）
 * <p>
 * 2. 查询导入状态（从 import_record 表读取）
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class ImportServiceImpl implements ImportService {
    private final ImportRecordMapper importRecordMapper;

    @Override
    public void runImport() {
        log.info("导入任务已触发（当前为桩实现，实际执行由 data-importer Python 脚本完成）");
    }

    @Override
    public ImportStatusVO getImportStatus() {
        List<ImportRecord> records = importRecordMapper.selectList(null);
        ImportStatusVO vo = new ImportStatusVO();
        vo.setLastImportedAt(records.isEmpty() ? null : records.getFirst().getCompletedAt());
        vo.setTotalSubjects(records.size());
        vo.setRecentRecords(SubjectConverter.toImportRecordVOList(records));
        return vo;
    }
}
