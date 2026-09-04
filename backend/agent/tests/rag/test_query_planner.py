from app.rag.query_planner import plan_retrieval_query
from app.rag.schemas import RetrievalQuery


def test_planner_extracts_explicit_chinese_conditions():
    planned = plan_retrieval_query(
        RetrievalQuery(semantic_query="2024年春季在播评分8以上且评分人数1000以上的动画")
    )

    assert planned.year_from == 2024
    assert planned.year_to == 2024
    assert planned.quarter == "spring"
    assert planned.air_status == "AIRING"
    assert planned.score_min == 8.0
    assert planned.rating_total_min == 1000


def test_planner_extracts_year_range_and_quarter_alias():
    planned = plan_retrieval_query(RetrievalQuery(semantic_query="2020-2022 Q4 已完结"))

    assert planned.year_from == 2020
    assert planned.year_to == 2022
    assert planned.quarter == "winter"
    assert planned.air_status == "FINISHED"


def test_explicit_fields_are_never_overwritten_by_text_hints():
    query = RetrievalQuery(
        semantic_query="2024年夏季在播评分9以上",
        year_from=2020,
        year_to=2021,
        quarter="winter",
        air_status="FINISHED",
        score_min=6,
    )

    planned = plan_retrieval_query(query)

    assert planned == query


def test_ambiguous_or_invalid_hints_are_left_unstructured():
    query = RetrievalQuery(semantic_query="编号2024，评分11以上，评分人数很多")

    planned = plan_retrieval_query(query)

    assert planned.year_from is None
    assert planned.year_to is None
    assert planned.score_min is None
    assert planned.rating_total_min is None


def test_operator_thresholds_are_supported_but_plain_score_is_not_inferred():
    threshold = plan_retrieval_query(RetrievalQuery(semantic_query="评分>=8且评分人数>1000"))
    plain = plan_retrieval_query(RetrievalQuery(semantic_query="评分8分的动画"))

    assert threshold.score_min == 8.0
    assert threshold.rating_total_min == 1000
    assert plain.score_min is None


def test_negative_finished_phrase_is_not_misclassified():
    planned = plan_retrieval_query(RetrievalQuery(semantic_query="尚未完结的动画"))

    assert planned.air_status is None
