package top.zhaizz.admin.service.impl;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import top.zhaizz.admin.converter.SubjectConverter;
import top.zhaizz.admin.mapper.ImportRecordMapper;
import top.zhaizz.admin.service.ImportService;
import top.zhaizz.pojo.entity.ImportRecord;
import top.zhaizz.pojo.vo.ImportStatusVO;

import java.util.List;

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
