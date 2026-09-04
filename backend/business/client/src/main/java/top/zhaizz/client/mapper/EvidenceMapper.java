package top.zhaizz.client.mapper;

import org.apache.ibatis.annotations.Param;
import top.zhaizz.client.model.EvidenceAliasRow;
import top.zhaizz.client.model.EvidenceCharacterRow;
import top.zhaizz.client.model.EvidenceCreditRow;
import top.zhaizz.client.model.EvidenceMetaTagRow;
import top.zhaizz.client.model.EvidenceRelationRow;
import top.zhaizz.client.model.EvidenceSubjectRow;
import top.zhaizz.pojo.entity.Subject;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;

import java.util.List;

/** 证据回查 Mapper：批量查询条目及其关联数据。 */
public interface EvidenceMapper extends BaseMapper<Subject> {

    List<EvidenceSubjectRow> selectSubjectBasics(@Param("ids") List<Long> subjectIds);

    List<EvidenceAliasRow> selectAliases(@Param("ids") List<Long> subjectIds);

    List<EvidenceMetaTagRow> selectMetaTags(@Param("ids") List<Long> subjectIds);

    List<EvidenceCreditRow> selectCredits(@Param("ids") List<Long> subjectIds);

    List<EvidenceCharacterRow> selectCharacters(@Param("ids") List<Long> subjectIds);

    List<EvidenceRelationRow> selectRelations(@Param("ids") List<Long> subjectIds);
}
