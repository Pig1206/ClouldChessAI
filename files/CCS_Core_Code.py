import copy
import math
from typing import List, Tuple, Optional, Dict

class CCScore:
    """五子棋AI核心类（重点优化斜边评估）"""

    def __init__(self, board: List[List[int]], difficulty: int = 3):
        self.board = board
        self.size = 15
        self.max_depth = difficulty + 2  # 稍微增加深度
        self.player = 1
        self.ai = 2

        # 斜对角专用权重表（比水平/垂直更重要）
        self.diagonal_weights = {
            (1, 1): 1.5,   # 主对角线
            (1, -1): 1.5,  # 副对角线
            (1, 0): 1.0,   # 水平
            (0, 1): 1.0,   # 垂直
        }

        # 增强的棋型评分（斜对角加倍）
        self.pattern_scores = {
            # 连五
            "xxxxx": 100000,

            # 活四
            "_xxxx_": 50000,    # 斜对角额外奖励
            "ooxxxxoo": 50000,

            # 冲四
            "oxxxx_": 4000,
            "_xxxxo": 4000,
            "x_xxx": 4200,      # 斜对角模式
            "xx_xx": 4200,
            "xxx_x": 4200,

            # 活三（斜对角加强）
            "_xxx_": 2500,
            "_xx_x_": 2200,
            "_x_xx_": 2200,

            # 跳活三
            "x__xx": 2000,
            "xx__x": 2000,

            # 眠三
            "oxxx__": 300,
            "__xxxo": 300,

            # 活二
            "__xx__": 150,
            "_x_x_": 120,
            "_x__x_": 100,

            # 眠二
            "oxx___": 20,
            "___xxo": 20,

            # 特殊斜对角模式（重点加强）
            "ooxo": 800,    # 斜对角特殊加强
            "oxoo": 600,
            "ooxoo": 1000,
        }

    def find_best_move(self) -> Tuple[int, int]:
        """寻找最佳落子位置（优化斜对角）"""
        # 1. 先检查必胜走法
        ai_win = self.find_diagonal_win(self.ai, check_all=True)
        if ai_win:
            return ai_win

        # 2. 检查对方必胜需要防守
        player_win = self.find_diagonal_win(self.player, check_all=True)
        if player_win:
            return player_win

        # 3. 获取高质量候选（特别关注斜对角）
        candidates = self.get_diagonal_focused_candidates()

        if not candidates:
            return self.select_best_position_by_influence()

        # 4. 对每个候选进行斜对角增强评估
        best_score = -math.inf
        best_move = candidates[0]

        for move in candidates[:15]:  # 限制搜索数量
            row, col = move

            # 快速斜对角评估
            diag_score = self.evaluate_diagonal_potential(row, col, self.ai)
            if diag_score < 200:  # 斜对角潜力太低的跳过
                continue

            self.board[row][col] = self.ai
            score = self.enhanced_minimax(0, -math.inf, math.inf, False)

            # 斜对角额外加成
            diag_bonus = self.calculate_diagonal_bonus(row, col)
            total_score = score + diag_bonus

            self.board[row][col] = 0

            if total_score > best_score:
                best_score = total_score
                best_move = move

        return best_move

    def find_diagonal_win(self, player: int, check_all: bool = False) -> Optional[Tuple[int, int]]:
        """寻找斜对角相关的必胜走法"""
        # 优先检查斜对角
        for row in range(self.size):
            for col in range(self.size):
                if self.board[row][col] == 0:
                    # 检查斜对角方向
                    for dx, dy in [(1, 1), (1, -1)] if not check_all else [(1, 1), (1, -1), (1, 0), (0, 1)]:
                        self.board[row][col] = player
                        if self.check_line_win(row, col, dx, dy, player):
                            self.board[row][col] = 0
                            return (row, col)
                        self.board[row][col] = 0
        return None

    def check_line_win(self, row: int, col: int, dx: int, dy: int, player: int) -> bool:
        """检查一条线上是否形成连五"""
        count = 1

        # 正向
        for i in range(1, 5):
            r, c = row + i * dx, col + i * dy
            if not (0 <= r < self.size and 0 <= c < self.size):
                break
            if self.board[r][c] != player:
                break
            count += 1

        # 反向
        for i in range(1, 5):
            r, c = row - i * dx, col - i * dy
            if not (0 <= r < self.size and 0 <= c < self.size):
                break
            if self.board[r][c] != player:
                break
            count += 1

        return count >= 5

    def get_diagonal_focused_candidates(self) -> List[Tuple[int, int]]:
        """获取候选位置（特别关注斜对角潜力）"""
        candidates = {}

        for row in range(self.size):
            for col in range(self.size):
                if self.board[row][col] == 0:
                    # 计算斜对角影响力
                    diag_influence = self.calculate_diagonal_influence(row, col)

                    # 必须有一定的影响力才考虑
                    if diag_influence > 0 or self.has_nearby_pieces(row, col):
                        candidates[(row, col)] = diag_influence

        # 按斜对角影响力排序
        sorted_candidates = sorted(candidates.items(), key=lambda x: x[1], reverse=True)
        return [pos for pos, _ in sorted_candidates[:25]]  # 返回前25个

    def calculate_diagonal_influence(self, row: int, col: int) -> int:
        """计算一个位置的斜对角影响力"""
        influence = 0

        # 检查两个斜对角方向
        for dx, dy in [(1, 1), (1, -1)]:
            # 向前检查
            forward_score = self.evaluate_direction_potential(row, col, dx, dy, self.ai)
            # 向后检查
            backward_score = self.evaluate_direction_potential(row, col, -dx, -dy, self.ai)

            influence += forward_score + backward_score

            # 对方斜对角威胁
            forward_threat = self.evaluate_direction_potential(row, col, dx, dy, self.player)
            backward_threat = self.evaluate_direction_potential(row, col, -dx, -dy, self.player)

            influence += (forward_threat + backward_threat) * 1.2  # 防守威胁更重要

        return influence

    def evaluate_direction_potential(self, row: int, col: int, dx: int, dy: int, player: int) -> int:
        """评估一个方向的潜力"""
        score = 0
        consecutive = 0
        empty_ends = 0

        # 向前检查最多5格
        for i in range(1, 6):
            r, c = row + i * dx, col + i * dy
            if not (0 <= r < self.size and 0 <= c < self.size):
                break

            if self.board[r][c] == player:
                consecutive += 1
            elif self.board[r][c] == 0:
                empty_ends += 1
                break
            else:
                break  # 对方棋子阻挡

        # 向后检查
        for i in range(1, 6):
            r, c = row - i * dx, col - i * dy
            if not (0 <= r < self.size and 0 <= c < self.size):
                break

            if self.board[r][c] == player:
                consecutive += 1
            elif self.board[r][c] == 0:
                empty_ends += 1
                break
            else:
                break

        # 根据连续棋子数和空端点计算分数
        if consecutive >= 4 and empty_ends >= 1:
            score += 5000  # 冲四潜力
        elif consecutive >= 3:
            if empty_ends >= 2:
                score += 2000  # 活三潜力
            elif empty_ends >= 1:
                score += 800   # 眠三潜力
        elif consecutive >= 2:
            if empty_ends >= 2:
                score += 200   # 活二
            elif empty_ends >= 1:
                score += 50    # 眠二

        return score

    def has_nearby_pieces(self, row: int, col: int) -> bool:
        """检查附近是否有棋子"""
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                r, c = row + dr, col + dc
                if 0 <= r < self.size and 0 <= c < self.size:
                    if self.board[r][c] != 0:
                        return True
        return False

    def evaluate_diagonal_potential(self, row: int, col: int, player: int) -> int:
        """快速评估一个位置的斜对角潜力"""
        if self.board[row][col] != 0:
            return 0

        score = 0

        # 只在斜对角方向评估
        for dx, dy in [(1, 1), (1, -1)]:
            # 模拟落子
            self.board[row][col] = player

            # 检查是否形成威胁
            line_pattern = self.get_line_pattern(row, col, dx, dy, 7)
            line_score = self.analyze_diagonal_pattern(line_pattern, player)
            score += line_score

            self.board[row][col] = 0

        return score

    def get_line_pattern(self, row: int, col: int, dx: int, dy: int, length: int) -> str:
        """获取一条线的模式字符串"""
        pattern = []

        for i in range(-3, 4):  # 中心前后各3格
            r, c = row + i * dx, col + i * dy

            if 0 <= r < self.size and 0 <= c < self.size:
                if self.board[r][c] == 0:
                    pattern.append('o')
                elif self.board[r][c] == self.ai:
                    pattern.append('x')
                else:
                    pattern.append('o')  # 对方棋子
            else:
                pattern.append('b')  # 边界

        return ''.join(pattern)

    def analyze_diagonal_pattern(self, pattern: str, player: int) -> int:
        """分析斜对角模式"""
        score = 0

        # 检查所有斜对角相关模式
        for pat, base_score in self.pattern_scores.items():
            if pat in pattern:
                # 斜对角模式额外加权
                if pat in ["ooxo", "oxoo", "ooxoo", "_xxx_", "_xx_x_", "_x_xx_"]:
                    score += base_score * 1.5
                else:
                    score += base_score

        # 特别检查连续棋子
        if "xxxx" in pattern:
            score += 8000
        elif "xxx" in pattern:
            score += 1500
        elif "xx" in pattern:
            score += 300

        return score

    def calculate_diagonal_bonus(self, row: int, col: int) -> float:
        """计算斜对角额外加成"""
        bonus = 0

        # 检查是否在关键斜对角线上
        if self.is_on_important_diagonal(row, col):
            bonus += 500

        # 检查斜对角连通性
        diag_connections = self.count_diagonal_connections(row, col, self.ai)
        bonus += diag_connections * 200

        # 检查斜对角威胁
        diag_threats = self.count_diagonal_threats(row, col, self.player)
        bonus += diag_threats * 300

        return bonus

    def is_on_important_diagonal(self, row: int, col: int) -> bool:
        """检查是否在重要的斜对角线上"""
        # 检查是否在中心斜对角线上
        main_diag_dist = abs(row - col)
        anti_diag_dist = abs(row + col - 14)

        return main_diag_dist <= 2 or anti_diag_dist <= 2

    def count_diagonal_connections(self, row: int, col: int, player: int) -> int:
        """计算斜对角方向上的连接数"""
        connections = 0

        for dx, dy in [(1, 1), (1, -1)]:
            # 向前检查
            for i in range(1, 3):
                r, c = row + i * dx, col + i * dy
                if 0 <= r < self.size and 0 <= c < self.size:
                    if self.board[r][c] == player:
                        connections += 1
                    else:
                        break
                else:
                    break

            # 向后检查
            for i in range(1, 3):
                r, c = row - i * dx, col - i * dy
                if 0 <= r < self.size and 0 <= c < self.size:
                    if self.board[r][c] == player:
                        connections += 1
                    else:
                        break
                else:
                    break

        return connections

    def count_diagonal_threats(self, row: int, col: int, player: int) -> int:
        """计算斜对角方向上的威胁数"""
        threats = 0

        for dx, dy in [(1, 1), (1, -1)]:
            # 模拟对方在这个位置落子
            self.board[row][col] = player

            # 检查是否形成威胁
            pattern = self.get_line_pattern(row, col, dx, dy, 7)
            if "xxx" in pattern or "x_xx" in pattern or "xx_x" in pattern:
                threats += 1

            self.board[row][col] = 0

        return threats

    def enhanced_minimax(self, depth: int, alpha: float, beta: float, maximizing: bool) -> float:
        """增强的Minimax搜索（考虑斜对角权重）"""
        if depth >= self.max_depth:
            return self.evaluate_board_with_diagonal_emphasis()

        # 检查胜负
        winner = self.check_winner()
        if winner == self.ai:
            return 100000 - depth
        if winner == self.player:
            return -100000 + depth

        if maximizing:
            max_eval = -math.inf
            candidates = self.get_candidate_moves()

            for move in candidates[:10]:  # 限制分支
                row, col = move
                self.board[row][col] = self.ai

                eval_score = self.enhanced_minimax(depth + 1, alpha, beta, False)
                max_eval = max(max_eval, eval_score)

                self.board[row][col] = 0

                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break

            return max_eval
        else:
            min_eval = math.inf
            candidates = self.get_candidate_moves()

            for move in candidates[:10]:
                row, col = move
                self.board[row][col] = self.player

                eval_score = self.enhanced_minimax(depth + 1, alpha, beta, True)
                min_eval = min(min_eval, eval_score)

                self.board[row][col] = 0

                beta = min(beta, eval_score)
                if beta <= alpha:
                    break

            return min_eval

    def evaluate_board_with_diagonal_emphasis(self) -> float:
        """评估棋盘（斜对角重点）"""
        ai_score = 0
        player_score = 0

        # 四个方向评估，斜对角权重更高
        for (dx, dy), weight in self.diagonal_weights.items():
            ai_score += self.evaluate_direction_score(dx, dy, self.ai) * weight
            player_score += self.evaluate_direction_score(dx, dy, self.player) * weight

        # 斜对角特殊模式评估
        ai_diag_special = self.evaluate_diagonal_special_patterns(self.ai)
        player_diag_special = self.evaluate_diagonal_special_patterns(self.player)

        ai_score += ai_diag_special * 1.2
        player_score += player_diag_special * 1.2

        # 位置价值（斜对角位置更优）
        ai_pos_value = self.evaluate_position_with_diagonal_bias(self.ai)
        player_pos_value = self.evaluate_position_with_diagonal_bias(self.player)

        return (ai_score + ai_pos_value) - (player_score + player_pos_value) * 1.15

    def evaluate_direction_score(self, dx: int, dy: int, player: int) -> int:
        """评估一个方向上的分数"""
        score = 0

        for row in range(self.size):
            for col in range(self.size):
                if self.board[row][col] == player:
                    # 检查这个方向
                    pattern = self.extract_direction_pattern(row, col, dx, dy)
                    pattern_str = ''.join(pattern)

                    # 模式匹配
                    for pat, pat_score in self.pattern_scores.items():
                        if pat in pattern_str:
                            score += pat_score

        return score

    def extract_direction_pattern(self, row: int, col: int, dx: int, dy: int) -> List[str]:
        """提取方向模式"""
        pattern = []

        # 前后各取5个位置
        for i in range(-4, 5):
            r, c = row + i * dx, col + i * dy

            if 0 <= r < self.size and 0 <= c < self.size:
                if self.board[r][c] == 0:
                    pattern.append('o')
                elif self.board[r][c] == self.ai:
                    pattern.append('x')
                else:
                    pattern.append('o')  # 对方
            else:
                pattern.append('b')  # 边界

        return pattern

    def evaluate_diagonal_special_patterns(self, player: int) -> int:
        """评估斜对角特殊模式"""
        score = 0

        # 扫描所有可能的斜对角
        for start_row in range(self.size):
            for start_col in range(self.size):
                if self.board[start_row][start_col] == 0:
                    # 检查这个空位在斜对角模式中的价值
                    for dx, dy in [(1, 1), (1, -1)]:
                        diag_value = self.evaluate_diagonal_cell(start_row, start_col, dx, dy, player)
                        score += diag_value

        return score

    def evaluate_diagonal_cell(self, row: int, col: int, dx: int, dy: int, player: int) -> int:
        """评估一个格子在斜对角线上的价值"""
        self.board[row][col] = player

        # 检查这个落子形成的模式
        pattern_forward = []
        pattern_backward = []

        # 向前
        for i in range(1, 4):
            r, c = row + i * dx, col + i * dy
            if 0 <= r < self.size and 0 <= c < self.size:
                if self.board[r][c] == player:
                    pattern_forward.append('x')
                elif self.board[r][c] == 0:
                    pattern_forward.append('o')
                else:
                    pattern_forward.append('b')
                    break
            else:
                pattern_forward.append('b')
                break

        # 向后
        for i in range(1, 4):
            r, c = row - i * dx, col - i * dy
            if 0 <= r < self.size and 0 <= c < self.size:
                if self.board[r][c] == player:
                    pattern_backward.append('x')
                elif self.board[r][c] == 0:
                    pattern_backward.append('o')
                else:
                    pattern_backward.append('b')
                    break
            else:
                pattern_backward.append('b')
                break

        # 反转后向模式并拼接
        pattern_backward.reverse()
        full_pattern = ''.join(pattern_backward) + 'x' + ''.join(pattern_forward)

        self.board[row][col] = 0

        # 分析模式
        pattern_score = 0
        if "xxx" in full_pattern:  # 形成三连
            pattern_score += 1500
        elif "xx" in full_pattern:  # 形成二连
            pattern_score += 300

        return pattern_score

    def evaluate_position_with_diagonal_bias(self, player: int) -> int:
        """评估位置价值（斜对角位置更有价值）"""
        score = 0

        # 斜对角位置价值矩阵
        diag_position_value = [
            [1, 1, 1, 1, 1, 2, 2, 3, 2, 2, 1, 1, 1, 1, 1],
            [1, 2, 2, 2, 2, 3, 3, 4, 3, 3, 2, 2, 2, 2, 1],
            [1, 2, 3, 3, 3, 4, 4, 5, 4, 4, 3, 3, 3, 2, 1],
            [1, 2, 3, 4, 4, 5, 5, 6, 5, 5, 4, 4, 3, 2, 1],
            [1, 2, 3, 4, 5, 6, 6, 7, 6, 6, 5, 4, 3, 2, 1],
            [2, 3, 4, 5, 6, 7, 7, 8, 7, 7, 6, 5, 4, 3, 2],
            [2, 3, 4, 5, 6, 7, 8, 9, 8, 7, 6, 5, 4, 3, 2],
            [3, 4, 5, 6, 7, 8, 9, 10, 9, 8, 7, 6, 5, 4, 3],
            [2, 3, 4, 5, 6, 7, 8, 9, 8, 7, 6, 5, 4, 3, 2],
            [2, 3, 4, 5, 6, 7, 7, 8, 7, 7, 6, 5, 4, 3, 2],
            [1, 2, 3, 4, 5, 6, 6, 7, 6, 6, 5, 4, 3, 2, 1],
            [1, 2, 3, 4, 4, 5, 5, 6, 5, 5, 4, 4, 3, 2, 1],
            [1, 2, 3, 3, 3, 4, 4, 5, 4, 4, 3, 3, 3, 2, 1],
            [1, 2, 2, 2, 2, 3, 3, 4, 3, 3, 2, 2, 2, 2, 1],
            [1, 1, 1, 1, 1, 2, 2, 3, 2, 2, 1, 1, 1, 1, 1],
        ]

        for row in range(self.size):
            for col in range(self.size):
                if self.board[row][col] == player:
                    score += diag_position_value[row][col] * 15

        return score

    def get_candidate_moves(self) -> List[Tuple[int, int]]:
        """获取候选位置"""
        candidates = set()

        for row in range(self.size):
            for col in range(self.size):
                if self.board[row][col] != 0:
                    for dr in range(-2, 3):
                        for dc in range(-2, 3):
                            r, c = row + dr, col + dc
                            if 0 <= r < self.size and 0 <= c < self.size:
                                if self.board[r][c] == 0:
                                    candidates.add((r, c))

        if not candidates:
            candidates.add((7, 7))

        return list(candidates)

    def select_best_position_by_influence(self) -> Tuple[int, int]:
        """根据影响力选择最佳位置"""
        best_score = -1
        best_pos = (7, 7)

        for row in range(self.size):
            for col in range(self.size):
                if self.board[row][col] == 0:
                    influence = self.calculate_total_influence(row, col)
                    if influence > best_score:
                        best_score = influence
                        best_pos = (row, col)

        return best_pos

    def calculate_total_influence(self, row: int, col: int) -> int:
        """计算一个位置的总影响力"""
        influence = 0

        # 四个方向的影响力
        for dx, dy in [(1, 0), (0, 1), (1, 1), (1, -1)]:
            # AI影响力
            ai_influence = self.evaluate_direction_influence(row, col, dx, dy, self.ai)
            # 玩家威胁
            player_threat = self.evaluate_direction_influence(row, col, dx, dy, self.player)

            influence += ai_influence + player_threat * 1.3  # 防守更重要

        return influence

    def evaluate_direction_influence(self, row: int, col: int, dx: int, dy: int, player: int) -> int:
        """评估一个方向上的影响力"""
        self.board[row][col] = player

        influence = 0
        count = 0

        # 正向
        for i in range(1, 4):
            r, c = row + i * dx, col + i * dy
            if 0 <= r < self.size and 0 <= c < self.size:
                if self.board[r][c] == player:
                    count += 1
                else:
                    break
            else:
                break

        # 反向
        for i in range(1, 4):
            r, c = row - i * dx, col - i * dy
            if 0 <= r < self.size and 0 <= c < self.size:
                if self.board[r][c] == player:
                    count += 1
                else:
                    break
            else:
                break

        self.board[row][col] = 0

        # 根据连续棋子数计算影响力
        if count >= 3:
            influence = 1000
        elif count == 2:
            influence = 300
        elif count == 1:
            influence = 100

        return influence

    def check_winner(self) -> Optional[int]:
        """检查获胜者"""
        for row in range(self.size):
            for col in range(self.size):
                player = self.board[row][col]
                if player != 0:
                    for dx, dy in [(1, 0), (0, 1), (1, 1), (1, -1)]:
                        count = 1

                        # 正向
                        for i in range(1, 5):
                            r, c = row + i * dx, col + i * dy
                            if not (0 <= r < self.size and 0 <= c < self.size):
                                break
                            if self.board[r][c] != player:
                                break
                            count += 1

                        # 反向
                        for i in range(1, 5):
                            r, c = row - i * dx, col - i * dy
                            if not (0 <= r < self.size and 0 <= c < self.size):
                                break
                            if self.board[r][c] != player:
                                break
                            count += 1

                        if count >= 5:
                            return player

        return None


