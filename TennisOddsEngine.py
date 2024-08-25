import random
import csv
import time

class Player:
    def __init__(self, name, serve_win_prob, ace_prob, double_fault_prob):
        self.name = name
        self.serve_win_prob = serve_win_prob
        self.ace_prob = ace_prob
        self.double_fault_prob = double_fault_prob

class TennisMatch:
    def __init__(self, player1, player2, best_of=3):
        self.player1 = player1
        self.player2 = player2
        self.best_of = best_of
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

    def switch_server(self):
        self.server, self.receiver = self.receiver, self.server

    def is_set_over(self):
        return (max(self.score["games"]) >= 6 and abs(self.score["games"][0] - self.score["games"][1]) >= 2) or \
               (self.score["games"][0] == 7 and self.score["games"][1] == 6) or \
               (self.score["games"][1] == 7 and self.score["games"][0] == 6)

    def format_point_score(self):
        server_points, receiver_points = self.score["points"]
        if server_points == receiver_points >= 3:
            return "Deuce"
        elif max(server_points, receiver_points) >= 4:
            if abs(server_points - receiver_points) == 1:
                return "Ad-In" if server_points > receiver_points else "Ad-Out"
            elif abs(server_points - receiver_points) >= 2:
                return "GAME"
        else:
            return f"{self.point_to_tennis_score(server_points)}-{self.point_to_tennis_score(receiver_points)}"

    def point_to_tennis_score(self, points):
        return {0: "0", 1: "15", 2: "30", 3: "40"}.get(points, str(points))

    def format_game_score(self):
        server_games = self.score["games"][0] if self.server == self.player1 else self.score["games"][1]
        receiver_games = self.score["games"][1] if self.server == self.player1 else self.score["games"][0]
        return f"{server_games}-{receiver_games}"

    def log_point(self):
        point_score = self.format_point_score()
        game_over = point_score == "GAME"
        set_over = False
        
        if game_over:
            if self.score["points"][0] > self.score["points"][1]:
                if self.server == self.player1:
                    self.score["games"][0] += 1
                else:
                    self.score["games"][1] += 1
            else:
                if self.server == self.player1:
                    self.score["games"][1] += 1
                else:
                    self.score["games"][0] += 1
            
            if self.is_set_over():
                set_over = True
                point_score = "SET"
                if self.score["games"][0] > self.score["games"][1]:
                    self.score["sets"][0] += 1
                else:
                    self.score["sets"][1] += 1

        game_score = self.format_game_score()
        set_score = f"{self.score['sets'][0]}-{self.score['sets'][1]}"
        
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
        self.total_shots += 1  # Increment total shots for each point played
        ace_prob = self.calculate_ace_probability()
        if random.random() < ace_prob:
            self.stats[self.server.name]["aces"] += 1
            self.score["points"][0] += 1
            winner = self.server
            self.last_point_ace = True
        elif random.random() < self.server.double_fault_prob:
            self.stats[self.server.name]["double_faults"] += 1
            self.score["points"][1] += 1
            winner = self.receiver
            self.last_point_ace = False
        elif random.random() < self.server.serve_win_prob:
            self.score["points"][0] += 1
            winner = self.server
            self.last_point_ace = False
        else:
            self.score["points"][1] += 1
            winner = self.receiver
            self.last_point_ace = False

        if winner == self.last_point_winner:
            self.consecutive_points += 1
        else:
            self.consecutive_points = 1
        self.last_point_winner = winner

        return winner

    def play_game(self):
        self.score["points"] = [0, 0]
        self.last_point_winner = None
        self.consecutive_points = 0
        self.last_point_ace = False
        self.stats[self.server.name]["aces"] = 0
        self.stats[self.server.name]["double_faults"] = 0
        
        while True:
            winner = self.play_point()
            game_over, set_over = self.log_point()
            if game_over:
                if not set_over:
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
                    # Reset stats for next set
                    self.stats[player]["aces"] = 0
                    self.stats[player]["double_faults"] = 0
                self.set_history.append(set_stats)
                self.score["games"] = [0, 0]  # Reset game score for new set
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

def simulate_match(player1, player2, best_of=3, num_simulations=1):
    match_wins = {player1.name: 0, player2.name: 0}
    total_shots = 0
    all_point_logs = []
    total_aces = {player1.name: 0, player2.name: 0}
    total_double_faults = {player1.name: 0, player2.name: 0}
    
    start_time = time.perf_counter()
    
    for _ in range(num_simulations):
        match = TennisMatch(player1, player2, best_of)
        winner = match.play_match()
        match_wins[winner.name] += 1
        
        total_shots += match.total_shots
        
        all_point_logs.extend(match.point_log)
        
        # Sum up aces and double faults
        for player in [player1.name, player2.name]:
            total_aces[player] += sum(set_stats[player]["aces"] for set_stats in match.set_history)
            total_double_faults[player] += sum(set_stats[player]["double_faults"] for set_stats in match.set_history)
    
    end_time = time.perf_counter()
    execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
    
    # Export point log to CSV
    with open('match_log.csv', 'w', newline='') as csvfile:
        fieldnames = all_point_logs[0].keys() if all_point_logs else []
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if fieldnames:
            writer.writeheader()
            for point in all_point_logs:
                writer.writerow(point)
    
    return match_wins, total_shots, execution_time, total_aces, total_double_faults

# Example usage
if __name__ == "__main__":
    
    num_simulations=1000
    num_sets = 5
    
    player1 = Player("Federer", serve_win_prob=0.65, ace_prob=0.10, double_fault_prob=0.05)
    player2 = Player("Nadal", serve_win_prob=0.62, ace_prob=0.08, double_fault_prob=0.04)
    
    results, total_shots, execution_time, aces, double_faults = simulate_match(player1, player2, best_of=num_sets, num_simulations=num_simulations)
    
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
    
    print("\nPoint-by-point log exported to 'match_log.csv'")