package top.zhaizz.animetracker.subject.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Mapper;
import top.zhaizz.animetracker.common.entity.ImportRecord;

/**
 * 导入记录 Mapper
 */
@Mapper
public interface ImportRecordMapper extends BaseMapper<ImportRecord> {
}
