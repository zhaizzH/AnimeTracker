"""共享实体模型与枚举。

本包定义 Person、Character、SubjectCredit 及其关系表的领域模型，
供 jobs/importer、jobs/indexer 和 app/rag 共同使用。
"""

from app.entities.enums import (
    ActorRelation,
    CharacterRelation,
    CharacterType,
    CreditRelation,
    CreditType,
    DetailStatus,
    EntityKind,
    ImageStorageStatus,
    JobStatus,
    PersonType,
)
from app.entities.models import (
    Character,
    CharacterActor,
    CharacterAlias,
    EntityDetailJob,
    Person,
    PersonAlias,
    SearchIndexJob,
    SubjectCharacter,
    SubjectCredit,
    SubjectPersonCredit,
)

__all__ = [
    "ActorRelation",
    "Character",
    "CharacterActor",
    "CharacterAlias",
    "CharacterRelation",
    "CharacterType",
    "CreditRelation",
    "CreditType",
    "DetailStatus",
    "EntityDetailJob",
    "EntityKind",
    "ImageStorageStatus",
    "JobStatus",
    "Person",
    "PersonAlias",
    "PersonType",
    "SearchIndexJob",
    "SubjectCharacter",
    "SubjectCredit",
    "SubjectPersonCredit",
]
