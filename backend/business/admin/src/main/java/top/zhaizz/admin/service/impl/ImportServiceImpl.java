package top.zhaizz.admin.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import top.zhaizz.admin.converter.SubjectConverter;
import top.zhaizz.admin.mapper.ImportRecordMapper;
import top.zhaizz.admin.service.ImportService;
import top.zhaizz.common.ErrorType;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.pojo.entity.ImportRecord;
import top.zhaizz.pojo.vo.ImportStatusVO;

import java.io.File;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * 番剧导入服务实现
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class ImportServiceImpl implements ImportService {
    private static final Set<String> MODES = Set.of("full", "season", "recent", "since");

    private final ImportRecordMapper importRecordMapper;

    @Value("${at.importer.python-command:python}")
    private String pythonCommand;
    @Value("${at.importer.script-dir:backend/data/importer}")
    private String scriptDir;
    @Value("${at.importer.script-name:main.py}")
    private String scriptName;

    // ponytail: 单实例 JVM 内 CAS + 存活进程 Map；JVM 重启后丢失，Python 进程独立存活仍会自收尾，接受
    private final AtomicBoolean running = new AtomicBoolean(false);
    private final Map<Long, Process> processes = new ConcurrentHashMap<>();

    @Override
    public void runImport(String mode, String key, String since, Integer workers) {
        validate(mode, key, since);
        sweep();
        if (!running.compareAndSet(false, true)) {
            throw new BizException(ErrorType.CONFLICT, "已有导入任务运行中");
        }
        try {
            long beforeId = maxRecordId();
            Process process = startProcess(mode, key, since, workers);
            Long id = waitForRunningRecord(beforeId);
            if (id == null) {
                process.destroy();
                throw new BizException(ErrorType.INTERNAL_ERROR, "导入进程启动后未创建导入记录");
            }
            processes.put(id, process);
        } catch (Exception e) {
            running.set(false);
            if (e instanceof BizException be) {
                throw be;
            }
            throw new BizException(ErrorType.INTERNAL_ERROR, "启动导入进程失败: " + e.getMessage());
        }
    }

    @Override
    public ImportStatusVO getImportStatus() {
        List<ImportRecord> records = importRecordMapper.selectList(
                new LambdaQueryWrapper<ImportRecord>()
                        .orderByDesc(ImportRecord::getStartedAt)
                        .last("LIMIT 10"));
        ImportStatusVO vo = new ImportStatusVO();
        vo.setLastImportedAt(records.isEmpty() ? null : records.getFirst().getCompletedAt());
        vo.setTotalSubjects(records.size());
        vo.setRecentRecords(SubjectConverter.toImportRecordVOList(records));
        return vo;
    }

    private void validate(String mode, String key, String since) {
        if (mode == null || !MODES.contains(mode)) {
            throw new BizException(ErrorType.BAD_REQUEST, "mode 必须是 full / season / recent / since");
        }
        if ("season".equals(mode) && (key == null || key.isBlank())) {
            throw new BizException(ErrorType.BAD_REQUEST, "season 模式需要 key");
        }
        if ("since".equals(mode) && (since == null || since.isBlank())) {
            throw new BizException(ErrorType.BAD_REQUEST, "since 模式需要 since");
        }
    }

    /** 回收已退出进程：仍 RUNNING 的记录翻 FAILED，Map 清空后释放 CAS 门禁。 */
    private void sweep() {
        for (Map.Entry<Long, Process> e : processes.entrySet()) {
            if (!e.getValue().isAlive()) {
                ImportRecord rec = importRecordMapper.selectById(e.getKey());
                if (rec != null && "RUNNING".equals(rec.getStatus())) {
                    rec.setStatus("FAILED");
                    rec.setErrorMessage("导入进程提前退出");
                    rec.setCompletedAt(LocalDateTime.now());
                    importRecordMapper.updateById(rec);
                    log.warn("导入进程提前退出，record {} 翻为 FAILED", e.getKey());
                }
                processes.remove(e.getKey());
            }
        }
        if (processes.isEmpty()) {
            running.set(false);
        }
    }

    private long maxRecordId() {
        return importRecordMapper.selectList(new LambdaQueryWrapper<ImportRecord>()
                        .orderByDesc(ImportRecord::getId)
                        .last("LIMIT 1"))
                .stream().findFirst().map(ImportRecord::getId).orElse(0L);
    }

    private Process startProcess(String mode, String key, String since, Integer workers) throws Exception {
        List<String> cmd = new ArrayList<>();
        cmd.add(pythonCommand);
        cmd.add(scriptName);
        cmd.add("--mode");
        cmd.add(mode);
        if (key != null) {
            cmd.add("--key");
            cmd.add(key);
        }
        if (since != null) {
            cmd.add("--since");
            cmd.add(since);
        }
        if (workers != null) {
            cmd.add("--workers");
            cmd.add(workers.toString());
        }
        ProcessBuilder pb = new ProcessBuilder(cmd);
        pb.directory(new File(scriptDir));
        pb.redirectErrorStream(true);
        // ponytail: 输出落日志文件，避免管道缓冲区占满阻塞 Python 写日志
        pb.redirectOutput(new File(scriptDir, "import.log"));
        log.info("启动导入进程: {}", String.join(" ", cmd));
        return pb.start();
    }

    /** 轮询直到出现新创建的 RUNNING 记录（进程启动到写库存在窗口期）。 */
    private Long waitForRunningRecord(long beforeId) throws InterruptedException {
        long deadline = System.currentTimeMillis() + 15_000;
        while (System.currentTimeMillis() < deadline) {
            List<ImportRecord> recs = importRecordMapper.selectList(
                    new LambdaQueryWrapper<ImportRecord>()
                            .gt(ImportRecord::getId, beforeId)
                            .eq(ImportRecord::getStatus, "RUNNING")
                            .orderByDesc(ImportRecord::getId)
                            .last("LIMIT 1"));
            if (!recs.isEmpty()) {
                return recs.getFirst().getId();
            }
            Thread.sleep(500);
        }
        return null;
    }
}
