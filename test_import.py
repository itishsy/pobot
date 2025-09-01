# 测试导入
try:
    from src.core.game_state import GameState, Round, Player
    print('Successfully imported from src.core.game_state')
except ImportError as e:
    print('Import error:', e)

try:
    from src.utils.card import compare_hands
    print('Successfully imported from src.utils.card')
except ImportError as e:
    print('Import error:', e)

try:
    import sys
    sys.path.append('src')
    from core.game_state import GameState, Round, Player
    print('Successfully imported from core.game_state after path append')
except ImportError as e:
    print('Import error after path append:', e)

