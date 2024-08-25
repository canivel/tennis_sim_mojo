from random import random_float64, random_si64, seed
from time import now
from sys import is_x86, has_avx, has_avx2, has_avx512f, os_is_linux, os_is_macos, os_is_windows, num_physical_cores, num_logical_cores

struct Player:
    var name: String
    var serve_win_prob: Float64
    var ace_prob: Float64
    var double_fault_prob: Float64

    fn __init__(inout self, name: String, serve_win_prob: Float64, ace_prob: Float64, double_fault_prob: Float64):
        self.name = name
        self.serve_win_prob = serve_win_prob
        self.ace_prob = ace_prob
        self.double_fault_prob = double_fault_prob

    fn __copyinit__(inout self, other: Self):
        self.name = other.name
        self.serve_win_prob = other.serve_win_prob
        self.ace_prob = other.ace_prob
        self.double_fault_prob = other.double_fault_prob

fn random_player_index() -> Int:
    return 0 if random_float64(0, 1) < 0.5 else 1

struct TennisMatch:
    var player1: Player
    var player2: Player
    var best_of: Int
    var grand_slam: Bool
    var server_index: Int
    var score_sets: StaticIntTuple[2]
    var score_games: StaticIntTuple[2]
    var score_points: StaticIntTuple[2]
    var total_shots: Int
    var stats_aces: StaticIntTuple[2]
    var stats_double_faults: StaticIntTuple[2]
    var last_point_winner: Int  # 0 for player1, 1 for player2, -1 for none
    var consecutive_points: Int
    var last_point_ace: Bool
    var is_tiebreak: Bool
    var tiebreak_points: Int
    var tiebreak_server: Int  # 0 for player1, 1 for player2, -1 for none

    fn __init__(inout self, player1: Player, player2: Player, best_of: Int = 3, grand_slam: Bool = True):
        self.player1 = player1
        self.player2 = player2
        self.best_of = best_of
        self.grand_slam = grand_slam
        self.server_index = random_player_index()
        self.score_sets = StaticIntTuple[2](0, 0)
        self.score_games = StaticIntTuple[2](0, 0)
        self.score_points = StaticIntTuple[2](0, 0)
        self.total_shots = 0
        self.stats_aces = StaticIntTuple[2](0, 0)
        self.stats_double_faults = StaticIntTuple[2](0, 0)
        self.last_point_winner = -1
        self.consecutive_points = 0
        self.last_point_ace = False
        self.is_tiebreak = False
        self.tiebreak_points = 0
        self.tiebreak_server = -1

    fn switch_server(inout self):
        self.server_index = 1 - self.server_index

    fn is_final_set(self) -> Bool:
        return self.score_sets[0] + self.score_sets[1] == self.best_of - 1

    fn is_set_over(self) -> Bool:
        if not self.is_tiebreak:
            return (max(self.score_games[0], self.score_games[1]) >= 6 and 
                    abs(self.score_games[0] - self.score_games[1]) >= 2)
        else:
            if self.grand_slam and self.is_final_set():
                return (max(self.score_points[0], self.score_points[1]) >= 10 and 
                        abs(self.score_points[0] - self.score_points[1]) >= 2)
            else:
                return (max(self.score_points[0], self.score_points[1]) >= 7 and 
                        abs(self.score_points[0] - self.score_points[1]) >= 2)

    fn play_point(inout self) -> Int:
        self.total_shots += 1
        var ace_prob = self.calculate_ace_probability()
        var receiver_index = 1 - self.server_index
        var current_server = self.player1 if self.server_index == 0 else self.player2
        var winner: Int

        if random_float64(0, 1) < ace_prob:
            self.stats_aces[self.server_index] += 1
            self.score_points[self.server_index] += 1
            winner = self.server_index
            self.last_point_ace = True
        elif random_float64(0, 1) < current_server.double_fault_prob:
            self.stats_double_faults[self.server_index] += 1
            self.score_points[receiver_index] += 1
            winner = receiver_index
            self.last_point_ace = False
        elif random_float64(0, 1) < current_server.serve_win_prob:
            self.score_points[self.server_index] += 1
            winner = self.server_index
            self.last_point_ace = False
        else:
            self.score_points[receiver_index] += 1
            winner = receiver_index
            self.last_point_ace = False

        if winner == self.last_point_winner:
            self.consecutive_points += 1
        else:
            self.consecutive_points = 1
        self.last_point_winner = winner

        if self.is_tiebreak:
            self.tiebreak_points += 1
            if self.tiebreak_points % 2 == 1:
                self.switch_server()

        return winner

    fn play_game(inout self) -> Tuple[Int, Bool]:
        if not self.is_tiebreak:
            self.score_points = StaticIntTuple[2](0, 0)
        self.last_point_winner = -1
        self.consecutive_points = 0
        self.last_point_ace = False
        self.stats_aces[self.server_index] = 0
        self.stats_double_faults[self.server_index] = 0
        
        var winner: Int
        var game_over: Bool
        var set_over: Bool
        
        while True:
            winner = self.play_point()
            game_over = self.is_game_over()
            set_over = self.is_set_over()
            if game_over or set_over:
                if not set_over and not self.is_tiebreak:
                    self.switch_server()
                return (winner, set_over)

    fn play_match(inout self) -> Int:
        while max(self.score_sets[0], self.score_sets[1]) < (self.best_of // 2 + 1):
            var `_` = self.play_set()
        return 0 if self.score_sets[0] > self.score_sets[1] else 1

    fn calculate_ace_probability(self) -> Float64:
        var current_server = self.player1 if self.server_index == 0 else self.player2
        var base_prob = current_server.ace_prob
        
        # Adjust for current score
        var score_diff = self.score_points[self.server_index] - self.score_points[1 - self.server_index]
        var score_adjustment = 0.01 * Float64(score_diff)
        
        # Adjust for momentum (consecutive points won by server)
        var momentum_adjustment = 0.0
        if self.last_point_winner == self.server_index:
            momentum_adjustment = min(0.02, 0.005 * Float64(self.consecutive_points))
        
        # Adjust for recent ace
        var recent_ace_adjustment = 0.02 if self.last_point_ace else 0.0
        
        # Combine all adjustments
        var adjusted_prob = base_prob + score_adjustment + momentum_adjustment + recent_ace_adjustment
        
        # Ensure probability is between 0 and 1, capped at 30% to keep it realistic
        return max(0.0, min(0.3, adjusted_prob))

    fn is_game_over(self) -> Bool:
        if self.is_tiebreak:
            return self.is_set_over()  # In a tiebreak, game over is the same as set over
        
        var server_points = self.score_points[self.server_index]
        var receiver_points = self.score_points[1 - self.server_index]
        
        if max(server_points, receiver_points) < 4:
            return False
        elif abs(server_points - receiver_points) >= 2:
            return True
        else:
            return False

    fn play_set(inout self) -> Int:
        self.score_games = StaticIntTuple[2](0, 0)
        self.is_tiebreak = False
        
        while not self.is_set_over():
            var game_winner: Int
            var set_over: Bool
            game_winner, set_over = self.play_game()
            
            if not self.is_tiebreak:
                self.score_games[game_winner] += 1
            
            if self.score_games[0] == 6 and self.score_games[1] == 6:
                self.is_tiebreak = True
                self.tiebreak_server = self.server_index
                self.tiebreak_points = 0
            
            if set_over:
                break
        
        var set_winner = 0 if self.score_games[0] > self.score_games[1] else 1
        self.score_sets[set_winner] += 1
        return set_winner

fn simulate_single_match(player1: Player, player2: Player, best_of: Int = 3, grand_slam: Bool = False) -> Tuple[Int, Int, StaticIntTuple[2], StaticIntTuple[2]]:
    var `match` = TennisMatch(player1, player2, best_of, grand_slam)
    var winner = `match`.play_match()
    var total_shots = `match`.total_shots
    return (winner, total_shots, `match`.stats_aces, `match`.stats_double_faults)

fn main():
    seed()  
    var num_simulations = 10000
    var num_sets = 5
    
    var player1 = Player("Federer", 0.65, 0.10, 0.05)
    var player2 = Player("Nadal", 0.62, 0.08, 0.04)

    print("Running", num_simulations, "simulations...")
    print("System Information:")
    print("  x86 Architecture:", "Yes" if is_x86() else "No")
    print("  AVX Support:", "Yes" if has_avx() else "No")
    print("  AVX2 Support:", "Yes" if has_avx2() else "No")
    print("  AVX512 Support:", "Yes" if has_avx512f() else "No")
    print("  Operating System:", "Linux" if os_is_linux() else "macOS" if os_is_macos() else "Windows" if os_is_windows() else "Unknown")
    print("  Physical Cores:", num_physical_cores())
    print("  Logical Cores:", num_logical_cores())

    var start_time = now()
    var total_wins = StaticIntTuple[2](0, 0)
    var total_shots = 0
    var total_aces = StaticIntTuple[2](0, 0)
    var total_double_faults = StaticIntTuple[2](0, 0)

    for i in range(num_simulations):
        var winner: Int
        var shots: Int
        var aces: StaticIntTuple[2]
        var double_faults: StaticIntTuple[2]
        winner, shots, aces, double_faults = simulate_single_match(player1, player2, num_sets, True)
        total_wins[winner] += 1
        total_shots += shots
        total_aces[0] += aces[0]
        total_aces[1] += aces[1]
        total_double_faults[0] += double_faults[0]
        total_double_faults[1] += double_faults[1]
        
        if (i + 1) % 1000 == 0:
            print("Completed", i + 1, "simulations")

    var end_time = now()
    var execution_time = (end_time - start_time) / 1e6  # Convert to milliseconds
    
    print("\nResults after", num_simulations, "simulations:")
    print("Percentage of Match wins:")
    print(player1.name + ": " + str(100 * Float64(total_wins[0])/Float64(num_simulations)) + "%")
    print(player2.name + ": " + str(100 * Float64(total_wins[1])/Float64(num_simulations)) + "%")
    
    print("\nTotal shots played:", total_shots)
    print("Average shots per match:", Float64(total_shots)/Float64(num_simulations))
    print("Execution time: " + str(execution_time) + " milliseconds")
    print("Average time per simulation: " + str(execution_time/Float64(num_simulations)) + " milliseconds")
    
    print("\nMatch statistics:")
    print(player1.name + ":")
    print(" Average Aces per match: " + str(Float64(total_aces[0])/Float64(num_simulations)))
    print(" Average Double faults per match: " + str(Float64(total_double_faults[0])/Float64(num_simulations)))
    print(player2.name + ":")
    print(" Average Aces per match: " + str(Float64(total_aces[1])/Float64(num_simulations)))
    print(" Average Double faults per match: " + str(Float64(total_double_faults[1])/Float64(num_simulations)))
