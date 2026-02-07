import copy
import math
from typing import List, Tuple, Optional, Dict

class CCScore:
    def __init__(self, board: List[List[int]], difficulty: int = 3):
        self.board = board
        self.size = 15
        self.max_depth = difficulty + 2
        self.player = 1
        self.ai = 2

        self.diagonal_weights = {
            (1, 1): 2.0,
            (1, -1): 2.0,
            (1, 0): 1.0,
            (0, 1): 1.0,
        }

        self.pattern_scores = {
            "xxxxx": 100000,
            "xxxxx": 100000,
            "_xxxx_": 60000,
            "ooxxxxoo": 55000,
            "oxxxx_": 5000,
            "_xxxxo": 5000,
            "x_xxx": 4800,
            "xx_xx": 4800,
            "xxx_x": 4800,
            "_xxx_": 3500,
            "_xx_x_": 3200,
            "_x_xx_": 3200,
            "x__xx": 2500,
            "xx__x": 2500,
            "oxxx__": 500,
            "__xxxo": 500,
            "__xx__": 250,
            "_x_x_": 200,
            "_x__x_": 180,
            "oxx___": 50,
            "___xxo": 50,
            "ooxo": 1200,
            "oxoo": 900,
            "ooxoo": 1500,
            "oxo": 400,
            "xox": 600,
            "oxxo": 800,
            "xoox": 1000,
        }

        self.diagonal_critical_positions = set()
        self.initialize_critical_positions()

    def initialize_critical_positions(self):
        for i in range(5, 10):
            self.diagonal_critical_positions.add((i, i))
            self.diagonal_critical_positions.add((i, 14-i))

        for offset in [1, 2]:
            for i in range(4, 11):
                if 0 <= i+offset < 15 and 0 <= i < 15:
                    self.diagonal_critical_positions.add((i+offset, i))
                    self.diagonal_critical_positions.add((i, i+offset))
                    self.diagonal_critical_positions.add((i+offset, 14-i))
                    self.diagonal_critical_positions.add((i, 14-i-offset))

    def find_best_move(self) -> Tuple[int, int]:
        ai_win = self.find_diagonal_win(self.ai, check_all=True)
        if ai_win:
            return ai_win

        player_win = self.find_diagonal_win(self.player, check_all=True)
        if player_win:
            return player_win

        critical_block = self.find_critical_diagonal_block()
        if critical_block:
            return critical_block

        candidates = self.get_diagonal_focused_candidates()

        if not candidates:
            return self.select_best_position_by_influence()

        best_score = -math.inf
        best_move = candidates[0]

        for move in candidates[:15]:
            row, col = move

            diag_score = self.evaluate_diagonal_potential(row, col, self.ai)
            if diag_score < 200:
                continue

            is_critical = self.is_diagonal_critical_move(row, col, self.ai)
            if is_critical:
                diag_score *= 1.5

            self.board[row][col] = self.ai
            score = self.enhanced_minimax(0, -math.inf, math.inf, False)

            diag_bonus = self.calculate_diagonal_bonus(row, col)
            connection_bonus = self.evaluate_diagonal_connection(row, col, self.ai)
            block_bonus = self.evaluate_diagonal_block(row, col, self.player)

            total_score = score + diag_bonus + connection_bonus * 1.2 + block_bonus * 1.5

            self.board[row][col] = 0

            if total_score > best_score:
                best_score = total_score
                best_move = move

        return best_move

    def find_critical_diagonal_block(self) -> Optional[Tuple[int, int]]:
        for row in range(self.size):
            for col in range(self.size):
                if self.board[row][col] == 0:
                    block_value = self.evaluate_diagonal_block_value(row, col, self.player)
                    if block_value >= 8000:
                        return (row, col)

                    if self.is_diagonal_critical_position(row, col):
                        self.board[row][col] = self.player
                        threat_level = self.evaluate_diagonal_threat_level(row, col, self.player)
                        self.board[row][col] = 0

                        if threat_level >= 6000:
                            return (row, col)

        return None

    def evaluate_diagonal_block_value(self, row: int, col: int, player: int) -> int:
        block_value = 0

        for dx, dy in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
            self.board[row][col] = player
            threat_score = self.evaluate_single_diagonal_threat(row, col, dx, dy, player)
            block_value += threat_score
            self.board[row][col] = 0

            self.board[row][col] = self.ai
            connection_score = self.evaluate_single_diagonal_connection(row, col, dx, dy, self.ai)
            block_value += connection_score * 0.8
            self.board[row][col] = 0

        return block_value

    def evaluate_single_diagonal_threat(self, row: int, col: int, dx: int, dy: int, player: int) -> int:
        threat_score = 0
        consecutive = 0
        open_ends = 0

        for i in range(1, 6):
            r, c = row + i * dx, col + i * dy
            if not (0 <= r < self.size and 0 <= c < self.size):
                break

            if self.board[r][c] == player:
                consecutive += 1
            elif self.board[r][c] == 0:
                open_ends += 1
                break
            else:
                break

        for i in range(1, 6):
            r, c = row - i * dx, col - i * dy
            if not (0 <= r < self.size and 0 <= c < self.size):
                break

            if self.board[r][c] == player:
                consecutive += 1
            elif self.board[r][c] == 0:
                open_ends += 1
                break
            else:
                break

        if consecutive >= 4:
            threat_score = 10000
        elif consecutive == 3:
            if open_ends >= 2:
                threat_score = 8000
            elif open_ends >= 1:
                threat_score = 4000
        elif consecutive == 2:
            if open_ends >= 2:
                threat_score = 1000
            elif open_ends >= 1:
                threat_score = 400

        return threat_score

    def evaluate_single_diagonal_connection(self, row: int, col: int, dx: int, dy: int, player: int) -> int:
        connection_score = 0

        pattern = []
        for i in range(-4, 5):
            r, c = row + i * dx, col + i * dy
            if 0 <= r < self.size and 0 <= c < self.size:
                if self.board[r][c] == player:
                    pattern.append('x')
                elif self.board[r][c] == 0:
                    pattern.append('o')
                else:
                    pattern.append('b')
            else:
                pattern.append('b')

        pattern_str = ''.join(pattern)

        center_index = 4

        left_part = pattern_str[:center_index]
        right_part = pattern_str[center_index+1:]

        left_potential = self.analyze_connection_potential(left_part[::-1])
        right_potential = self.analyze_connection_potential(right_part)

        connection_score = (left_potential + right_potential) * 100

        if 'xox' in pattern_str or 'oxo' in pattern_str:
            connection_score += 500

        return connection_score

    def analyze_connection_potential(self, pattern: str) -> int:
        potential = 0
        x_count = 0

        for i, char in enumerate(pattern):
            if char == 'x':
                x_count += 1
                if i > 0 and pattern[i-1] == 'x':
                    potential += 2
            elif char == 'o':
                if x_count > 0:
                    potential += x_count * 3
                    x_count = 0
            else:
                break

        if x_count > 0:
            potential += x_count * 3

        return potential

    def is_diagonal_critical_move(self, row: int, col: int, player: int) -> bool:
        if not self.is_diagonal_critical_position(row, col):
            return False

        self.board[row][col] = player

        diag_connections = 0
        for dx, dy in [(1, 1), (1, -1)]:
            connection_count = self.count_diagonal_connections(row, col, player)
            if connection_count >= 2:
                diag_connections += 1

        self.board[row][col] = 0

        return diag_connections >= 1

    def is_diagonal_critical_position(self, row: int, col: int) -> bool:
        if (row, col) in self.diagonal_critical_positions:
            return True

        active_diagonals = 0
        for dx, dy in [(1, 1), (1, -1)]:
            has_pieces = False
            for i in range(-3, 4):
                r, c = row + i * dx, col + i * dy
                if 0 <= r < self.size and 0 <= c < self.size:
                    if self.board[r][c] != 0:
                        has_pieces = True
                        break

            if has_pieces:
                active_diagonals += 1

        return active_diagonals >= 1

    def evaluate_diagonal_threat_level(self, row: int, col: int, player: int) -> int:
        threat_level = 0

        for dx, dy in [(1, 1), (1, -1)]:
            pattern = self.get_extended_line_pattern(row, col, dx, dy, 9)
            threat_score = self.analyze_diagonal_threat_pattern(pattern, player)
            threat_level += threat_score

        return threat_level

    def get_extended_line_pattern(self, row: int, col: int, dx: int, dy: int, length: int) -> str:
        pattern = []
        half_length = length // 2

        for i in range(-half_length, half_length + 1):
            r, c = row + i * dx, col + i * dy

            if 0 <= r < self.size and 0 <= c < self.size:
                if self.board[r][c] == 0:
                    pattern.append('o')
                elif self.board[r][c] == self.ai:
                    pattern.append('x')
                else:
                    pattern.append('o')
            else:
                pattern.append('b')

        return ''.join(pattern)

    def analyze_diagonal_threat_pattern(self, pattern: str, player: int) -> int:
        threat_score = 0

        for i in range(len(pattern) - 4):
            sub_pattern = pattern[i:i+5]

            if sub_pattern.count('x') == 4 and 'o' in sub_pattern:
                threat_score += 5000

            if sub_pattern == 'oxxxo':
                threat_score += 3000

            if sub_pattern in ['oxxox', 'xoxxo', 'xxoox', 'xooxx']:
                threat_score += 2000

        x_count = pattern.count('x')
        o_count = pattern.count('o')

        if x_count >= 3 and o_count >= 2:
            threat_score += 1500

        return threat_score

    def evaluate_diagonal_connection(self, row: int, col: int, player: int) -> float:
        connection_value = 0

        for dx, dy in [(1, 1), (1, -1)]:
            connection_strength = self.calculate_diagonal_connection_strength(row, col, dx, dy, player)
            connection_value += connection_strength

            bridge_value = self.evaluate_diagonal_bridge(row, col, dx, dy, player)
            connection_value += bridge_value * 1.5

        return connection_value

    def calculate_diagonal_connection_strength(self, row: int, col: int, dx: int, dy: int, player: int) -> float:
        strength = 0
        forward_connected = 0

        for i in range(1, 5):
            r, c = row + i * dx, col + i * dy
            if not (0 <= r < self.size and 0 <= c < self.size):
                break

            if self.board[r][c] == player:
                forward_connected += 1
                strength += 100 * i
            elif self.board[r][c] == 0:
                if forward_connected > 0:
                    strength += 50
                break
            else:
                break

        backward_connected = 0
        for i in range(1, 5):
            r, c = row - i * dx, col - i * dy
            if not (0 <= r < self.size and 0 <= c < self.size):
                break

            if self.board[r][c] == player:
                backward_connected += 1
                strength += 100 * i
            elif self.board[r][c] == 0:
                if backward_connected > 0:
                    strength += 50
                break
            else:
                break

        total_connected = forward_connected + backward_connected
        if total_connected >= 2:
            strength += 500 * total_connected

        return strength

    def evaluate_diagonal_bridge(self, row: int, col: int, dx: int, dy: int, player: int) -> float:
        bridge_value = 0

        self.board[row][col] = player

        first_group_pos = None
        for i in range(1, 5):
            r, c = row + i * dx, col + i * dy
            if not (0 <= r < self.size and 0 <= c < self.size):
                break

            if self.board[r][c] == player:
                first_group_pos = (r, c)
                break

        second_group_pos = None
        for i in range(1, 5):
            r, c = row - i * dx, col - i * dy
            if not (0 <= r < self.size and 0 <= c < self.size):
                break

            if self.board[r][c] == player:
                second_group_pos = (r, c)
                break

        self.board[row][col] = 0

        if first_group_pos and second_group_pos:
            forward_dist = abs(first_group_pos[0] - row) + abs(first_group_pos[1] - col)
            backward_dist = abs(second_group_pos[0] - row) + abs(second_group_pos[1] - col)
            total_dist = forward_dist + backward_dist

            if total_dist <= 6:
                bridge_value = 800 - total_dist * 50

        return bridge_value

    def evaluate_diagonal_block(self, row: int, col: int, opponent: int) -> float:
        block_value = 0

        for dx, dy in [(1, 1), (1, -1)]:
            block_strength = self.calculate_diagonal_block_strength(row, col, dx, dy, opponent)
            block_value += block_strength

            split_value = self.evaluate_diagonal_split(row, col, dx, dy, opponent)
            block_value += split_value * 1.2

        return block_value

    def calculate_diagonal_block_strength(self, row: int, col: int, dx: int, dy: int, opponent: int) -> float:
        block_strength = 0

        self.board[row][col] = opponent

        max_threat = 0
        for i in range(-4, 5):
            r, c = row + i * dx, col + i * dy
            if 0 <= r < self.size and 0 <= c < self.size:
                if self.board[r][c] == opponent:
                    threat = self.evaluate_single_point_threat(r, c, dx, dy, opponent)
                    max_threat = max(max_threat, threat)

        self.board[row][col] = 0

        if max_threat > 0:
            block_strength = max_threat * 0.8

        return block_strength

    def evaluate_single_point_threat(self, row: int, col: int, dx: int, dy: int, player: int) -> float:
        threat = 0
        consecutive = 0

        for i in range(1, 5):
            r, c = row + i * dx, col + i * dy
            if not (0 <= r < self.size and 0 <= c < self.size):
                break

            if self.board[r][c] == player:
                consecutive += 1
            else:
                break

        for i in range(1, 5):
            r, c = row - i * dx, col - i * dy
            if not (0 <= r < self.size and 0 <= c < self.size):
                break

            if self.board[r][c] == player:
                consecutive += 1
            else:
                break

        consecutive += 1

        if consecutive >= 5:
            threat = 10000
        elif consecutive == 4:
            threat = 5000
        elif consecutive == 3:
            threat = 2000
        elif consecutive == 2:
            threat = 500

        return threat

    def evaluate_diagonal_split(self, row: int, col: int, dx: int, dy: int, opponent: int) -> float:
        split_value = 0

        left_count = 0
        right_count = 0

        for i in range(1, 5):
            r, c = row - i * dx, col - i * dy
            if not (0 <= r < self.size and 0 <= c < self.size):
                break

            if self.board[r][c] == opponent:
                left_count += 1
            else:
                break

        for i in range(1, 5):
            r, c = row + i * dx, col + i * dy
            if not (0 <= r < self.size and 0 <= c < self.size):
                break

            if self.board[r][c] == opponent:
                right_count += 1
            else:
                break

        if left_count > 0 and right_count > 0:
            split_value = (left_count + right_count) * 200

            if left_count >= 2 or right_count >= 2:
                split_value *= 1.5

        return split_value

    def get_diagonal_focused_candidates(self) -> List[Tuple[int, int]]:
        candidates = {}

        for row in range(self.size):
            for col in range(self.size):
                if self.board[row][col] == 0:
                    diag_influence = self.calculate_diagonal_influence(row, col)
                    connection_value = self.evaluate_diagonal_connection(row, col, self.ai)
                    block_value = self.evaluate_diagonal_block(row, col, self.player)

                    total_score = diag_influence + connection_value * 1.2 + block_value * 1.5

                    if self.is_diagonal_critical_position(row, col):
                        total_score *= 1.3

                    candidates[(row, col)] = total_score

        sorted_candidates = sorted(candidates.items(), key=lambda x: x[1], reverse=True)
        return [pos for pos, _ in sorted_candidates[:25]]

    def find_diagonal_win(self, player: int, check_all: bool = False) -> Optional[Tuple[int, int]]:
        for row in range(self.size):
            for col in range(self.size):
                if self.board[row][col] == 0:
                    for dx, dy in [(1, 1), (1, -1)] if not check_all else [(1, 1), (1, -1), (1, 0), (0, 1)]:
                        self.board[row][col] = player
                        if self.check_line_win(row, col, dx, dy, player):
                            self.board[row][col] = 0
                            return (row, col)
                        self.board[row][col] = 0
        return None

    def check_line_win(self, row: int, col: int, dx: int, dy: int, player: int) -> bool:
        count = 1

        for i in range(1, 5):
            r, c = row + i * dx, col + i * dy
            if not (0 <= r < self.size and 0 <= c < self.size):
                break
            if self.board[r][c] != player:
                break
            count += 1

        for i in range(1, 5):
            r, c = row - i * dx, col - i * dy
            if not (0 <= r < self.size and 0 <= c < self.size):
                break
            if self.board[r][c] != player:
                break
            count += 1

        return count >= 5

    def calculate_diagonal_influence(self, row: int, col: int) -> int:
        influence = 0

        for dx, dy in [(1, 1), (1, -1)]:
            forward_score = self.evaluate_direction_potential(row, col, dx, dy, self.ai)
            backward_score = self.evaluate_direction_potential(row, col, -dx, -dy, self.ai)
            influence += forward_score + backward_score

            forward_threat = self.evaluate_direction_potential(row, col, dx, dy, self.player)
            backward_threat = self.evaluate_direction_potential(row, col, -dx, -dy, self.player)
            influence += (forward_threat + backward_threat) * 1.2

        return influence

    def evaluate_direction_potential(self, row: int, col: int, dx: int, dy: int, player: int) -> int:
        score = 0
        consecutive = 0
        empty_ends = 0

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
                break

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

        if consecutive >= 4 and empty_ends >= 1:
            score += 5000
        elif consecutive >= 3:
            if empty_ends >= 2:
                score += 2000
            elif empty_ends >= 1:
                score += 800
        elif consecutive >= 2:
            if empty_ends >= 2:
                score += 200
            elif empty_ends >= 1:
                score += 50

        return score

    def has_nearby_pieces(self, row: int, col: int) -> bool:
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                r, c = row + dr, col + dc
                if 0 <= r < self.size and 0 <= c < self.size:
                    if self.board[r][c] != 0:
                        return True
        return False

    def evaluate_diagonal_potential(self, row: int, col: int, player: int) -> int:
        if self.board[row][col] != 0:
            return 0

        score = 0

        for dx, dy in [(1, 1), (1, -1)]:
            self.board[row][col] = player
            line_pattern = self.get_line_pattern(row, col, dx, dy, 7)
            line_score = self.analyze_diagonal_pattern(line_pattern, player)
            score += line_score
            self.board[row][col] = 0

        return score

    def get_line_pattern(self, row: int, col: int, dx: int, dy: int, length: int) -> str:
        pattern = []

        for i in range(-3, 4):
            r, c = row + i * dx, col + i * dy

            if 0 <= r < self.size and 0 <= c < self.size:
                if self.board[r][c] == 0:
                    pattern.append('o')
                elif self.board[r][c] == self.ai:
                    pattern.append('x')
                else:
                    pattern.append('o')
            else:
                pattern.append('b')

        return ''.join(pattern)

    def analyze_diagonal_pattern(self, pattern: str, player: int) -> int:
        score = 0

        for pat, base_score in self.pattern_scores.items():
            if pat in pattern:
                if pat in ["ooxo", "oxoo", "ooxoo", "_xxx_", "_xx_x_", "_x_xx_"]:
                    score += base_score * 1.5
                else:
                    score += base_score

        if "xxxx" in pattern:
            score += 8000
        elif "xxx" in pattern:
            score += 1500
        elif "xx" in pattern:
            score += 300

        return score

    def calculate_diagonal_bonus(self, row: int, col: int) -> float:
        bonus = 0

        if self.is_on_important_diagonal(row, col):
            bonus += 500

        diag_connections = self.count_diagonal_connections(row, col, self.ai)
        bonus += diag_connections * 200

        diag_threats = self.count_diagonal_threats(row, col, self.player)
        bonus += diag_threats * 300

        return bonus

    def is_on_important_diagonal(self, row: int, col: int) -> bool:
        main_diag_dist = abs(row - col)
        anti_diag_dist = abs(row + col - 14)

        return main_diag_dist <= 2 or anti_diag_dist <= 2

    def count_diagonal_connections(self, row: int, col: int, player: int) -> int:
        connections = 0

        for dx, dy in [(1, 1), (1, -1)]:
            for i in range(1, 3):
                r, c = row + i * dx, col + i * dy
                if 0 <= r < self.size and 0 <= c < self.size:
                    if self.board[r][c] == player:
                        connections += 1
                    else:
                        break
                else:
                    break

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
        threats = 0

        for dx, dy in [(1, 1), (1, -1)]:
            self.board[row][col] = player
            pattern = self.get_line_pattern(row, col, dx, dy, 7)
            if "xxx" in pattern or "x_xx" in pattern or "xx_x" in pattern:
                threats += 1
            self.board[row][col] = 0

        return threats

    def enhanced_minimax(self, depth: int, alpha: float, beta: float, maximizing: bool) -> float:
        if depth >= self.max_depth:
            return self.evaluate_board_with_diagonal_emphasis()

        winner = self.check_winner()
        if winner == self.ai:
            return 100000 - depth
        if winner == self.player:
            return -100000 + depth

        if maximizing:
            max_eval = -math.inf
            candidates = self.get_candidate_moves()

            for move in candidates[:10]:
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
        ai_score = 0
        player_score = 0

        for (dx, dy), weight in self.diagonal_weights.items():
            ai_score += self.evaluate_direction_score(dx, dy, self.ai) * weight
            player_score += self.evaluate_direction_score(dx, dy, self.player) * weight

        ai_diag_special = self.evaluate_diagonal_special_patterns(self.ai)
        player_diag_special = self.evaluate_diagonal_special_patterns(self.player)

        ai_score += ai_diag_special * 1.2
        player_score += player_diag_special * 1.2

        ai_pos_value = self.evaluate_position_with_diagonal_bias(self.ai)
        player_pos_value = self.evaluate_position_with_diagonal_bias(self.player)

        return (ai_score + ai_pos_value) - (player_score + player_pos_value) * 1.15

    def evaluate_direction_score(self, dx: int, dy: int, player: int) -> int:
        score = 0

        for row in range(self.size):
            for col in range(self.size):
                if self.board[row][col] == player:
                    pattern = self.extract_direction_pattern(row, col, dx, dy)
                    pattern_str = ''.join(pattern)

                    for pat, pat_score in self.pattern_scores.items():
                        if pat in pattern_str:
                            score += pat_score

        return score

    def extract_direction_pattern(self, row: int, col: int, dx: int, dy: int) -> List[str]:
        pattern = []

        for i in range(-4, 5):
            r, c = row + i * dx, col + i * dy

            if 0 <= r < self.size and 0 <= c < self.size:
                if self.board[r][c] == 0:
                    pattern.append('o')
                elif self.board[r][c] == self.ai:
                    pattern.append('x')
                else:
                    pattern.append('o')
            else:
                pattern.append('b')

        return pattern

    def evaluate_diagonal_special_patterns(self, player: int) -> int:
        score = 0

        for start_row in range(self.size):
            for start_col in range(self.size):
                if self.board[start_row][start_col] == 0:
                    for dx, dy in [(1, 1), (1, -1)]:
                        diag_value = self.evaluate_diagonal_cell(start_row, start_col, dx, dy, player)
                        score += diag_value

        return score

    def evaluate_diagonal_cell(self, row: int, col: int, dx: int, dy: int, player: int) -> int:
        self.board[row][col] = player

        pattern_forward = []
        pattern_backward = []

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

        pattern_backward.reverse()
        full_pattern = ''.join(pattern_backward) + 'x' + ''.join(pattern_forward)

        self.board[row][col] = 0

        pattern_score = 0
        if "xxx" in full_pattern:
            pattern_score += 1500
        elif "xx" in full_pattern:
            pattern_score += 300

        return pattern_score

    def evaluate_position_with_diagonal_bias(self, player: int) -> int:
        score = 0

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
        influence = 0

        for dx, dy in [(1, 0), (0, 1), (1, 1), (1, -1)]:
            ai_influence = self.evaluate_direction_influence(row, col, dx, dy, self.ai)
            player_threat = self.evaluate_direction_influence(row, col, dx, dy, self.player)
            influence += ai_influence + player_threat * 1.3

        return influence

    def evaluate_direction_influence(self, row: int, col: int, dx: int, dy: int, player: int) -> int:
        self.board[row][col] = player

        influence = 0
        count = 0

        for i in range(1, 4):
            r, c = row + i * dx, col + i * dy
            if 0 <= r < self.size and 0 <= c < self.size:
                if self.board[r][c] == player:
                    count += 1
                else:
                    break
            else:
                break

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

        if count >= 3:
            influence = 1000
        elif count == 2:
            influence = 300
        elif count == 1:
            influence = 100

        return influence

    def check_winner(self) -> Optional[int]:
        for row in range(self.size):
            for col in range(self.size):
                player = self.board[row][col]
                if player != 0:
                    for dx, dy in [(1, 0), (0, 1), (1, 1), (1, -1)]:
                        count = 1

                        for i in range(1, 5):
                            r, c = row + i * dx, col + i * dy
                            if not (0 <= r < self.size and 0 <= c < self.size):
                                break
                            if self.board[r][c] != player:
                                break
                            count += 1

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