"""收藏写操作工具包：按业务能力拆分，显式组合 action_tools，保持依赖可见。"""

from app.agent.client.actions.collection_progress import collection_progress_tools
from app.agent.client.actions.wishlist import wishlist_tools

action_tools = [*collection_progress_tools, *wishlist_tools]
