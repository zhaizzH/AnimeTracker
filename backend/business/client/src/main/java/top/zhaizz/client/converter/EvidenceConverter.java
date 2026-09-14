package top.zhaizz.client.converter;

import top.zhaizz.client.model.EvidenceCharacterRow;
import top.zhaizz.client.model.EvidenceCreditRow;
import top.zhaizz.client.model.EvidenceRelationRow;
import top.zhaizz.client.model.EvidenceSubjectRow;
import top.zhaizz.pojo.vo.evidence.EvidenceCandidateVO;

import java.util.Collections;
import java.util.List;
import java.util.Map;

/** 证据回查结果转换器。 */
public final class EvidenceConverter {
    /**
     * 禁止实例化仅提供静态操作的工具类。
     */
    private EvidenceConverter() {
    }

    /**
     * 将查询行及其关联数据转换为证据候选响应，不修改输入。
     * <p>映射和条目须非空，关联列表不得含空元素；列表顺序保留。
     * 别名和元标签列表直接引用，缺键时为空列表；主创、角色和关系缺键或空列表时输出 null。
     * @param subject 条目基础查询行
     * @param aliasMap 别名映射
     * @param metaTagMap 元标签映射
     * @param creditMap 演职员映射
     * @param characterMap 角色映射
     * @param relationMap 关联条目映射
     * @return 证据候选响应
     */
    public static EvidenceCandidateVO toCandidate(
            EvidenceSubjectRow subject,
            Map<Long, List<String>> aliasMap,
            Map<Long, List<String>> metaTagMap,
            Map<Long, List<EvidenceCreditRow>> creditMap,
            Map<Long, List<EvidenceCharacterRow>> characterMap,
            Map<Long, List<EvidenceRelationRow>> relationMap) {
        Long id = subject.getSubjectId();
        List<EvidenceCandidateVO.CreditItem> creditItems = creditMap.getOrDefault(id, Collections.emptyList())
                .stream().map(c -> EvidenceCandidateVO.CreditItem.builder()
                        .personName(c.getPersonName()).role(c.getRole()).relation(c.getRelation()).build()).toList();
        List<EvidenceCandidateVO.CharacterItem> characterItems = characterMap.getOrDefault(id, Collections.emptyList())
                .stream().map(c -> EvidenceCandidateVO.CharacterItem.builder()
                        .characterName(c.getCharacterName()).relation(c.getRelation()).build()).toList();
        List<EvidenceCandidateVO.RelationItem> relationItems = relationMap.getOrDefault(id, Collections.emptyList())
                .stream().map(r -> EvidenceCandidateVO.RelationItem.builder()
                        .relatedSubjectId(r.getRelatedSubjectId()).relatedSubjectName(r.getRelatedSubjectName())
                        .relatedSubjectNameCn(r.getRelatedSubjectNameCn()).relation(r.getRelation()).build()).toList();
        return EvidenceCandidateVO.builder()
                .subjectId(id).name(subject.getName()).nameCn(subject.getNameCn()).type(subject.getType())
                .nsfw(subject.getNsfw()).active(subject.getActive()).sourceId(subject.getSourceId())
                .sourceUrl(subject.getSourceUrl()).score(subject.getScore()).rank(subject.getRank())
                .ratingTotal(subject.getRatingTotal()).collectionTotal(subject.getCollectionTotal())
                .airDate(subject.getAirDate()).airStatus(subject.getAirStatus()).summary(subject.getSummary())
                .aliases(aliasMap.getOrDefault(id, Collections.emptyList()))
                .metaTags(metaTagMap.getOrDefault(id, Collections.emptyList()))
                .credits(creditItems.isEmpty() ? null : creditItems)
                .characters(characterItems.isEmpty() ? null : characterItems)
                .relations(relationItems.isEmpty() ? null : relationItems)
                .sourceTime(subject.getSourceFetchedAt()).sourceFetchedAt(subject.getSourceFetchedAt()).build();
    }
}
