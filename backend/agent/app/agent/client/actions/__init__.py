"""收藏写操作工具包：按业务能力拆分，显式组合 action_tools，保持依赖可见。"""

from app.agent.client.actions.collection_progress import build_collection_progress_tools
from app.agent.client.actions.wishlist import build_wishlist_tools
from app.agent.ports import BusinessGateway


def build_action_tools(business: BusinessGateway):
    return [*build_collection_progress_tools(business), *build_wishlist_tools(business)]
