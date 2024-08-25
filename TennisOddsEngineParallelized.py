import random
import csv
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

class Player:
    def __init__(self, name, serve_win_prob, ace_prob, double_fault_prob):
        self.name = name
        self.serve_win_prob = serve_win_prob
        self.ace_prob = ace_prob
        self.double_fault_prob = double_fault_prob

class TennisMatch:
    def __init__(self, player1, player2, best_of=3, grand_slam=True):
        self.player1 = player1
        self.player2 = player2
        self.best_of = best_of
        self.grand_slam = grand_slam
        self.server = None
        self.receiver = None
        self.score = {"sets": [0, 0], "games": [0, 0], "points": [0, 0]}
        self.set_history = []
        self.total_shots = 0
        self.point_log = []
        self.stats = {player1.name: {"aces": 0, "double_faults": 0},
                      player2.name: {"aces": 0, "double_faults": 0}}
        self.last_point_winner = None
        self.consecutive_points = 0
        self.last_point_ace = False
        self.is_tiebreak = False
        self.tiebreak_points = 0
        self.tiebreak_server = None

    def switch_server(self):
        self.server, self.receiver = self.receiver, self.server

    def is_final_set(self):
        return sum(self.score["sets"]) == self.best_of - 1

    def is_set_over(self):
        if not self.is_tiebreak:
            return (max(self.score["games"]) >= 6 and abs(self.score["games"][0] - self.score["games"][1]) >= 2)
        else:
            if self.grand_slam and self.is_final_set():
                return (max(self.score["points"]) >= 10 and abs(self.score["points"][0] - self.score["points"][1]) >= 2)
            else:
                return (max(self.score["points"]) >= 7 and abs(self.score["points"][0] - self.score["points"][1]) >= 2)

    def format_point_score(self):
        if not self.is_tiebreak:
            server_points = self.score["points"][0 if self.server == self.player1 else 1]
            receiver_points = self.score["points"][1 if self.server == self.player1 else 0]
            if server_points == receiver_points >= 3:
                return "Deuce"
            elif max(server_points, receiver_points) >= 4:
                if abs(server_points - receiver_points) == 1:
                    return "Ad-In" if server_points > receiver_points else "Ad-Out"
                elif abs(server_points - receiver_points) >= 2:
                    return "GAME"
            else:
                return f"{self.point_to_tennis_score(server_points)}-{self.point_to_tennis_score(receiver_points)}"
        else:
            server_points = self.score["points"][0 if self.server == self.player1 else 1]
            receiver_points = self.score["points"][1 if self.server == self.player1 else 0]
            return f"{server_points}-{receiver_points}"

    def point_to_tennis_score(self, points):
        if self.is_tiebreak:
            return str(points)
        return {0: "0", 1: "15", 2: "30", 3: "40"}.get(points, str(points))

    def format_game_score(self):
        server_games = self.score["games"][0 if self.server == self.player1 else 1]
        receiver_games = self.score["games"][1 if self.server == self.player1 else 0]
        return f"{server_games}-{receiver_games}"

    def format_set_score(self):
        server_sets = self.score['sets'][0 if self.server == self.player1 else 1]
        receiver_sets = self.score['sets'][1 if self.server == self.player1 else 0]
        return f"{server_sets}-{receiver_sets}"

    def log_point(self):
        point_score = self.format_point_score()
        game_over = False
        set_over = False
        
        if self.is_tiebreak:
            if self.is_set_over():
                set_over = True
                game_over = True
                point_score = "SET"
                winning_player_index = 0 if self.score["points"][0] > self.score["points"][1] else 1
                self.score["games"][winning_player_index] += 1
                self.score["sets"][winning_player_index] += 1
                self.is_tiebreak = False
        else:
            if point_score == "GAME":
                game_over = True
                winning_player_index = 0 if self.score["points"][0] > self.score["points"][1] else 1
                self.score["games"][winning_player_index] += 1
            
            if self.is_set_over():
                set_over = True
                point_score = "SET"
                winning_player_index = 0 if self.score["games"][0] > self.score["games"][1] else 1
                self.score["sets"][winning_player_index] += 1
            elif self.score["games"][0] == 6 and self.score["games"][1] == 6:
                self.is_tiebreak = True
                self.score["points"] = [0, 0]  # Reset points for tiebreak
                self.tiebreak_server = self.server
                self.tiebreak_points = 0

        game_score = self.format_game_score()
        set_score = self.format_set_score()
        
        # Calculate probabilities (implementation of these methods remains the same)
        match_win_prob1 = self.calculate_match_win_probability(self.player1)
        match_win_prob2 = self.calculate_match_win_probability(self.player2)
        set_win_prob1 = self.calculate_set_win_probability(self.player1)
        set_win_prob2 = self.calculate_set_win_probability(self.player2)
        game_win_prob1 = self.calculate_game_win_probability(self.player1)
        game_win_prob2 = self.calculate_game_win_probability(self.player2)
        next_point_prob1 = self.calculate_next_point_win_probability(self.player1)
        next_point_prob2 = self.calculate_next_point_win_probability(self.player2)
        ace_prob = self.calculate_ace_probability()
        tiebreak_prob = self.calculate_tiebreak_probability()

        self.point_log.append({
            "server": self.server.name,
            "receiver": self.receiver.name,
            "point_score": point_score,
            "game_score": game_score,
            "set_score": set_score,
            f"{self.player1.name}_match_win_prob": match_win_prob1,
            f"{self.player2.name}_match_win_prob": match_win_prob2,
            f"{self.player1.name}_set_win_prob": set_win_prob1,
            f"{self.player2.name}_set_win_prob": set_win_prob2,
            f"{self.player1.name}_game_win_prob": game_win_prob1,
            f"{self.player2.name}_game_win_prob": game_win_prob2,
            f"{self.player1.name}_next_point_win_prob": next_point_prob1,
            f"{self.player2.name}_next_point_win_prob": next_point_prob2,
            "next_serve_ace_prob": ace_prob,
            "tiebreak_prob": tiebreak_prob
        })

        return game_over, set_over

    def play_point(self):
        self.total_shots += 1
        ace_prob = self.calculate_ace_probability()
        if random.random() < ace_prob:
            self.stats[self.server.name]["aces"] += 1
            self.score["points"][0 if self.server == self.player1 else 1] += 1
            winner = self.server
            self.last_point_ace = True
        elif random.random() < self.server.double_fault_prob:
            self.stats[self.server.name]["double_faults"] += 1
            self.score["points"][1 if self.server == self.player1 else 0] += 1
            winner = self.receiver
            self.last_point_ace = False
        elif random.random() < self.server.serve_win_prob:
            self.score["points"][0 if self.server == self.player1 else 1] += 1
            winner = self.server
            self.last_point_ace = False
        else:
            self.score["points"][1 if self.server == self.player1 else 0] += 1
            winner = self.receiver
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

    def play_game(self):
        if not self.is_tiebreak:
            self.score["points"] = [0, 0]
        self.last_point_winner = None
        self.consecutive_points = 0
        self.last_point_ace = False
        self.stats[self.server.name]["aces"] = 0
        self.stats[self.server.name]["double_faults"] = 0
        
        while True:
            winner = self.play_point()
            game_over, set_over = self.log_point()
            if game_over or set_over:
                if not set_over and not self.is_tiebreak:
                    self.switch_server()
                return winner, set_over

    def play_set(self):
        set_stats = {self.player1.name: {"aces": 0, "double_faults": 0},
                     self.player2.name: {"aces": 0, "double_faults": 0}}
        while True:
            winner, set_over = self.play_game()
            if set_over:
                for player in [self.player1.name, self.player2.name]:
                    set_stats[player]["aces"] = self.stats[player]["aces"]
                    set_stats[player]["double_faults"] = self.stats[player]["double_faults"]
                    self.stats[player]["aces"] = 0
                    self.stats[player]["double_faults"] = 0
                self.set_history.append(set_stats)
                self.score["games"] = [0, 0]
                self.score["points"] = [0, 0]
                self.is_tiebreak = False
                self.tiebreak_points = 0
                self.switch_server()  # Switch server for the start of the next set
                return winner

    def play_match(self):
        self.server = random.choice([self.player1, self.player2])
        self.receiver = self.player2 if self.server == self.player1 else self.player1

        while max(self.score["sets"]) < (self.best_of // 2 + 1):
            set_winner = self.play_set()

        return self.player1 if self.score["sets"][0] > self.score["sets"][1] else self.player2

    def calculate_match_win_probability(self, player):
        sets_to_win = self.best_of // 2 + 1
        player_sets = self.score["sets"][0] if player == self.player1 else self.score["sets"][1]
        opponent_sets = self.score["sets"][1] if player == self.player1 else self.score["sets"][0]
        player_games = self.score["games"][0] if player == self.player1 else self.score["games"][1]
        opponent_games = self.score["games"][1] if player == self.player1 else self.score["games"][0]
        
        base_prob = 0.5 + (player_sets - opponent_sets) * 0.1
        game_adjustment = (player_games - opponent_games) * 0.01
        return min(max(base_prob + game_adjustment, 0), 1)

    def calculate_set_win_probability(self, player):
        player_games = self.score["games"][0] if player == self.player1 else self.score["games"][1]
        opponent_games = self.score["games"][1] if player == self.player1 else self.score["games"][0]
        
        base_prob = 0.5 + (player_games - opponent_games) * 0.05
        return min(max(base_prob, 0), 1)

    def calculate_game_win_probability(self, player):
        is_server = player == self.server
        player_points = self.score["points"][0] if is_server else self.score["points"][1]
        opponent_points = self.score["points"][1] if is_server else self.score["points"][0]
        
        if is_server:
            base_prob = self.server.serve_win_prob
        else:
            base_prob = 1 - self.server.serve_win_prob
        
        point_adjustment = (player_points - opponent_points) * 0.05
        return min(max(base_prob + point_adjustment, 0), 1)

    def calculate_next_point_win_probability(self, player):
        base_prob = self.server.serve_win_prob if player == self.server else 1 - self.server.serve_win_prob
        
        # Adjust for current score
        score_diff = self.score["points"][0] - self.score["points"][1]
        if player == self.server:
            score_adjustment = 0.02 * score_diff
        else:
            score_adjustment = -0.02 * score_diff
        
        # Adjust for momentum (consecutive points won)
        momentum_adjustment = 0
        if self.last_point_winner == player:
            momentum_adjustment = min(0.05, 0.01 * self.consecutive_points)
        elif self.last_point_winner is not None:
            momentum_adjustment = -min(0.05, 0.01 * self.consecutive_points)
        
        # Adjust for recent ace or double fault
        recent_ace_adjustment = 0.03 if self.stats[player.name]["aces"] > 0 else 0
        recent_df_adjustment = -0.03 if self.stats[player.name]["double_faults"] > 0 else 0
        
        # Combine all adjustments
        adjusted_prob = base_prob + score_adjustment + momentum_adjustment + recent_ace_adjustment + recent_df_adjustment
        
        # Ensure probability is between 0 and 1
        return max(0, min(1, adjusted_prob))
    
    def calculate_ace_probability(self):
        base_prob = self.server.ace_prob
        
        # Adjust for current score
        score_diff = self.score["points"][0] - self.score["points"][1]
        score_adjustment = 0.01 * score_diff
        
        # Adjust for momentum (consecutive points won by server)
        momentum_adjustment = 0
        if self.last_point_winner == self.server:
            momentum_adjustment = min(0.02, 0.005 * self.consecutive_points)
        
        # Adjust for recent ace
        recent_ace_adjustment = 0.02 if self.last_point_ace else 0
        
        # Combine all adjustments
        adjusted_prob = base_prob + score_adjustment + momentum_adjustment + recent_ace_adjustment
        
        # Ensure probability is between 0 and 1
        return max(0, min(0.3, adjusted_prob))  # Cap at 30% to keep it realistic

    def calculate_tiebreak_probability(self):
        games_sum = sum(self.score["games"])
        if games_sum < 10:
            return 0.1
        elif games_sum == 10:
            return 0.2
        elif games_sum == 11:
            return 0.5
        else:
            return 1.0  # Tiebreak is certain at 6-6

def simulate_single_match(player1, player2, best_of=3, grand_slam=False):
    match = TennisMatch(player1, player2, best_of, grand_slam=grand_slam)
    winner = match.play_match()
    total_shots = match.total_shots
    point_log = match.point_log
    aces = {player1.name: 0, player2.name: 0}
    double_faults = {player1.name: 0, player2.name: 0}

    for player in [player1.name, player2.name]:
        aces[player] = sum(set_stats[player]["aces"] for set_stats in match.set_history)
        double_faults[player] = sum(set_stats[player]["double_faults"] for set_stats in match.set_history)

    return winner.name, total_shots, point_log, aces, double_faults

def simulate_batch(player1, player2, best_of, grand_slam=False, batch_size=10, save_logs=False, filename="match_log_parallel.csv"):
    match_wins = {player1.name: 0, player2.name: 0}
    total_shots = 0
    all_point_logs = []
    total_aces = {player1.name: 0, player2.name: 0}
    total_double_faults = {player1.name: 0, player2.name: 0}
    
    for _ in range(batch_size):
        match = TennisMatch(player1, player2, best_of, grand_slam=grand_slam)
        winner = match.play_match()
        match_wins[winner.name] += 1
        total_shots += match.total_shots
        all_point_logs.extend(match.point_log)
        
        for player in [player1.name, player2.name]:
            total_aces[player] += sum(set_stats[player]["aces"] for set_stats in match.set_history)
            total_double_faults[player] += sum(set_stats[player]["double_faults"] for set_stats in match.set_history)
    
    if save_logs:
        with open(filename, 'a', newline='') as csvfile:
            fieldnames = all_point_logs[0].keys() if all_point_logs else []
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if csvfile.tell() == 0:
                writer.writeheader()
            for point in all_point_logs:
                writer.writerow(point)
    
    return match_wins, total_shots, total_aces, total_double_faults

def simulate_match_parallel(player1, player2, best_of=3, grand_slam=False, num_simulations=1000, max_workers=4, batch_size=10, log_interval=100):
    match_wins = {player1.name: 0, player2.name: 0}
    total_shots = 0
    total_aces = {player1.name: 0, player2.name: 0}
    total_double_faults = {player1.name: 0, player2.name: 0}
    
    start_time = time.perf_counter()
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for i in range(num_simulations // batch_size):
            save_logs = ((i + 1) * batch_size) % log_interval == 0
            futures.append(executor.submit(simulate_batch, player1, player2, best_of, grand_slam, batch_size, save_logs))
        
        for future in as_completed(futures):
            batch_match_wins, batch_shots, batch_aces, batch_double_faults = future.result()
            for player in [player1.name, player2.name]:
                match_wins[player] += batch_match_wins[player]
                total_aces[player] += batch_aces[player]
                total_double_faults[player] += batch_double_faults[player]
            total_shots += batch_shots
    
    end_time = time.perf_counter()
    execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
    
    return match_wins, total_shots, execution_time, total_aces, total_double_faults


if __name__ == "__main__":
    
    num_simulations = 10000
    num_sets = 5
    max_workers = 10  
    batch_size = 10  
    log_interval=100
    
    player1 = Player("Federer", serve_win_prob=0.65, ace_prob=0.10, double_fault_prob=0.05)
    player2 = Player("Nadal", serve_win_prob=0.62, ace_prob=0.08, double_fault_prob=0.04)

    results, total_shots, execution_time, aces, double_faults = simulate_match_parallel(player1, 
                                                                                        player2, 
                                                                                        best_of=num_sets, 
                                                                                        grand_slam=True,
                                                                                        num_simulations=num_simulations, 
                                                                                        max_workers=max_workers, 
                                                                                        batch_size=batch_size,
                                                                                        log_interval=log_interval)
    
    print(f"Perc of Match wins after {num_simulations} matches:")
    for player, wins in results.items():
        print(f"{player}: {wins/num_simulations}")
    
    print(f"\nTotal shots played: {total_shots}")
    print(f"Execution time: {execution_time:.2f} milliseconds")
    
    print("\nMatch statistics:")
    for player in [player1.name, player2.name]:
        print(f"{player}:")
        print(f" Perc. Aces: {aces[player]/num_simulations}")
        print(f" Perc. Double faults: {double_faults[player]/num_simulations}")
    
    print("\nPoint-by-point log exported to 'match_log_parallel.csv'")