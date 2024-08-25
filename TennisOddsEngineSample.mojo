struct TennisOddsEngine:
    var p_serve_a: Float64
    var p_serve_b: Float64

    fn __init__(inout self, p_serve_a: Float64, p_serve_b: Float64):
        self.p_serve_a = p_serve_a
        self.p_serve_b = p_serve_b

    fn calculate_game_win_prob(self, p_serve: Float64) -> Float64:
        var q_serve = 1 - p_serve
        return (
            pow(p_serve, 4) * (1 + 4*q_serve + 10*pow(q_serve, 2)) +
            20 * pow(p_serve, 5) * pow(q_serve, 3) /
            (1 - 2*p_serve*q_serve)
        )

    fn calculate_tiebreak_win_prob(self) -> Float64:
        var p_tb = (self.p_serve_a + self.p_serve_b) / 2
        var q_tb = 1 - p_tb
        return (
            pow(p_tb, 7) + 7*pow(p_tb, 7)*q_tb + 28*pow(p_tb, 7)*pow(q_tb, 2) +
            84*pow(p_tb, 7)*pow(q_tb, 3) + 210*pow(p_tb, 7)*pow(q_tb, 4) +
            462*pow(p_tb, 7)*pow(q_tb, 5) +
            924*pow(p_tb, 8)*pow(q_tb, 6) / (1 - 2*p_tb*q_tb)
        )

    fn calculate_set_win_prob(self) -> Float64:
        var p_game_a = self.calculate_game_win_prob(self.p_serve_a)
        var p_game_b = 1 - self.calculate_game_win_prob(self.p_serve_b)
        var p_tb = self.calculate_tiebreak_win_prob()

        # Probability of winning a single game (average of serving and returning)
        var p_game = (p_game_a + p_game_b) / 2

        # Probability of winning the set before reaching 5-5
        var p_win_before_55 = 0.0
        for i in range(6):
            p_win_before_55 += self.binomial_coefficient(i+5, 5) * pow(p_game, 6) * pow(1-p_game, Float64(i))

        # Probability of reaching 5-5
        var p_reach_55 = self.binomial_coefficient(10, 5) * pow(p_game, 5) * pow(1-p_game, 5)

        # Probability of winning given 5-5 is reached
        var p_win_from_55 = p_game * p_game + p_game * (1-p_game) * p_game

        # Probability of reaching 6-6
        var p_reach_66 = p_reach_55 * p_game * (1-p_game)

        # Total probability
        return p_win_before_55 + p_reach_55 * p_win_from_55 + p_reach_66 * p_tb

    fn binomial_coefficient(self, n: Int, k: Int) -> Int:
        var k_copy = k
        if k_copy == 0 or k_copy == n:
            return 1
        if k_copy > n - k_copy:
            k_copy = n - k_copy
        var c = 1
        for i in range(k_copy):
            c = c * (n - i) // (i + 1)
        return c

fn main():
    var engine = TennisOddsEngine(0.65, 0.60)
    
    var p_game_a = engine.calculate_game_win_prob(engine.p_serve_a)
    var p_game_b = engine.calculate_game_win_prob(engine.p_serve_b)
    var p_tiebreak = engine.calculate_tiebreak_win_prob()
    var p_set = engine.calculate_set_win_prob()

    print("Probability of player A winning a game on serve:", p_game_a)
    print("Probability of player B winning a game on serve:", p_game_b)
    print("Probability of player A winning a tiebreak:", p_tiebreak)
    print("Probability of player A winning a set:", p_set)