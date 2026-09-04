package top.zhaizz.client.service.impl;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import top.zhaizz.client.mapper.EvidenceMapper;
import top.zhaizz.client.model.*;
import top.zhaizz.client.service.EvidenceService;
import top.zhaizz.common.constant.ErrorType;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.pojo.dto.evidence.EvidenceEntityBatchRequestDTO;
import top.zhaizz.pojo.vo.evidence.EvidenceCandidateVO;

import java.util.*;
import java.util.stream.Collectors;

/** 证据回查服务实现。 */
@Service
@RequiredArgsConstructor
public class EvidenceServiceImpl implements EvidenceService {

    private static final int MAX_BATCH_SIZE = 50;

    private final EvidenceMapper evidenceMapper;

    @Override
    public List<EvidenceCandidateVO> batchEvidence(List<Long> subjectIds) {
        if (subjectIds == null || subjectIds.isEmpty()) {
            return Collections.emptyList();
        }

        List<Long> distinctIds = subjectIds.stream().distinct().toList();

        List<EvidenceSubjectRow> subjects = evidenceMapper.selectSubjectBasics(distinctIds);
        if (subjects.isEmpty()) {
            return Collections.emptyList();
        }

        Set<Long> foundIds = subjects.stream().map(EvidenceSubjectRow::getSubjectId).collect(Collectors.toSet());

        List<EvidenceAliasRow> aliases = evidenceMapper.selectAliases(new ArrayList<>(foundIds));
        List<EvidenceMetaTagRow> metaTags = evidenceMapper.selectMetaTags(new ArrayList<>(foundIds));
        List<EvidenceCreditRow> credits = evidenceMapper.selectCredits(new ArrayList<>(foundIds));
        List<EvidenceCharacterRow> characters = evidenceMapper.selectCharacters(new ArrayList<>(foundIds));
        List<EvidenceRelationRow> relations = evidenceMapper.selectRelations(new ArrayList<>(foundIds));

        Map<Long, List<String>> aliasMap = aliases.stream()
                .collect(Collectors.groupingBy(EvidenceAliasRow::getSubjectId,
                        Collectors.mapping(EvidenceAliasRow::getName, Collectors.toList())));

        Map<Long, List<String>> metaTagMap = metaTags.stream()
                .collect(Collectors.groupingBy(EvidenceMetaTagRow::getSubjectId,
                        Collectors.mapping(EvidenceMetaTagRow::getName, Collectors.toList())));

        Map<Long, List<EvidenceCreditRow>> creditMap = credits.stream()
                .collect(Collectors.groupingBy(EvidenceCreditRow::getSubjectId));

        Map<Long, List<EvidenceCharacterRow>> characterMap = characters.stream()
                .collect(Collectors.groupingBy(EvidenceCharacterRow::getSubjectId));

        Map<Long, List<EvidenceRelationRow>> relationMap = relations.stream()
                .collect(Collectors.groupingBy(EvidenceRelationRow::getSubjectId));

        return subjects.stream()
                .map(s -> buildCandidate(s, aliasMap, metaTagMap, creditMap, characterMap, relationMap))
                .toList();
    }

    @Override
    public List<EvidenceCandidateVO> resolveEvidence(EvidenceEntityBatchRequestDTO request) {
        if (request == null || request.getEntityType() == null
                || request.getIds() == null || request.getIds().isEmpty()) {
            return Collections.emptyList();
        }
        if (request.getIds().size() > MAX_BATCH_SIZE) {
            throw new BizException(ErrorType.BAD_REQUEST, "实体 ID 最多 50 个");
        }

        List<Long> ids = request.getIds().stream()
                .filter(Objects::nonNull)
                .distinct()
                .toList();
        if (ids.isEmpty()) {
            return Collections.emptyList();
        }

        List<Long> subjectIds = switch (request.getEntityType()) {
            case SUBJECT -> ids;
            case RELATION_SUBJECT -> evidenceMapper.selectRelatedSubjectIds(ids);
            case PERSON -> evidenceMapper.selectSubjectIdsByPersonIds(ids);
            case CHARACTER -> evidenceMapper.selectSubjectIdsByCharacterIds(ids);
            case ACTOR -> evidenceMapper.selectSubjectIdsByActorIds(ids);
        };
        if (subjectIds == null || subjectIds.isEmpty()) {
            return Collections.emptyList();
        }
        return batchEvidence(subjectIds.stream().filter(Objects::nonNull).distinct().toList());
    }

    private EvidenceCandidateVO buildCandidate(
            EvidenceSubjectRow subject,
            Map<Long, List<String>> aliasMap,
            Map<Long, List<String>> metaTagMap,
            Map<Long, List<EvidenceCreditRow>> creditMap,
            Map<Long, List<EvidenceCharacterRow>> characterMap,
            Map<Long, List<EvidenceRelationRow>> relationMap) {

        Long id = subject.getSubjectId();

        List<EvidenceCandidateVO.CreditItem> creditItems = creditMap.getOrDefault(id, Collections.emptyList())
                .stream()
                .map(c -> EvidenceCandidateVO.CreditItem.builder()
                        .personName(c.getPersonName())
                        .role(c.getRole())
                        .relation(c.getRelation())
                        .build())
                .toList();

        List<EvidenceCandidateVO.CharacterItem> characterItems = characterMap.getOrDefault(id, Collections.emptyList())
                .stream()
                .map(c -> EvidenceCandidateVO.CharacterItem.builder()
                        .characterName(c.getCharacterName())
                        .relation(c.getRelation())
                        .build())
                .toList();

        List<EvidenceCandidateVO.RelationItem> relationItems = relationMap.getOrDefault(id, Collections.emptyList())
                .stream()
                .map(r -> EvidenceCandidateVO.RelationItem.builder()
                        .relatedSubjectId(r.getRelatedSubjectId())
                        .relatedSubjectName(r.getRelatedSubjectName())
                        .relatedSubjectNameCn(r.getRelatedSubjectNameCn())
                        .relation(r.getRelation())
                        .build())
                .toList();

        return EvidenceCandidateVO.builder()
                .subjectId(id)
                .name(subject.getName())
                .nameCn(subject.getNameCn())
                .type(subject.getType())
                .nsfw(subject.getNsfw())
                .active(subject.getActive())
                .sourceId(subject.getSourceId())
                .sourceUrl(subject.getSourceUrl())
                .score(subject.getScore())
                .rank(subject.getRank())
                .ratingTotal(subject.getRatingTotal())
                .collectionTotal(subject.getCollectionTotal())
                .airDate(subject.getAirDate())
                .summary(subject.getSummary())
                .aliases(aliasMap.getOrDefault(id, Collections.emptyList()))
                .metaTags(metaTagMap.getOrDefault(id, Collections.emptyList()))
                .credits(creditItems.isEmpty() ? null : creditItems)
                .characters(characterItems.isEmpty() ? null : characterItems)
                .relations(relationItems.isEmpty() ? null : relationItems)
                .sourceTime(subject.getSourceFetchedAt())
                .sourceFetchedAt(subject.getSourceFetchedAt())
                .build();
    }
}
