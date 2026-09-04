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

    /** 通过主创人物本地 ID 扩展安全动画条目。 */
    List<Long> selectSubjectIdsByPersonIds(@Param("ids") List<Long> personIds);

    /** 通过角色本地 ID 扩展安全动画条目。 */
    List<Long> selectSubjectIdsByCharacterIds(@Param("ids") List<Long> characterIds);

    /** 通过声优人物本地 ID 沿 character_actor 关系扩展安全动画条目。 */
    List<Long> selectSubjectIdsByActorIds(@Param("ids") List<Long> actorIds);
}
