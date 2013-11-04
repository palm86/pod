import scipy.stats as stats


class FTester(object):
    """
    Tests whether an unconstricted/full model provides a significantly
    better fit than a constricted/reduced model.

    The Null Hypothesis is that the full model does NOT provide a significantly
    better fit than the restricted model. The NH is rejected if the F-statistic
    is greater than the critical value of the F-distribution for a particular
    confidence level (1 - false_rejection_prob).

    """
    def __init__(self, confidence_level=0.95):
        """
        If the confidence_level is 0.95, the false rejection
        probability is 0.05
        """
        self.confidence_level = confidence_level

    def one_sided(self, result1, result2):
        self.r1 = result1 if len(result1.parameters) < len(result2.parameters) else result2
        self.r2 = result2 if len(result1.parameters) < len(result2.parameters) else result1
        self.sse1 = self.r1.ss_err
        self.sse2 = self.r2.ss_err
        self.p1 = len(self.r1.parameters)
        self.p2 = len(self.r2.parameters)
        self.n1 = self.r1.n
        self.n2 = self.r2.n
        df_red = self.n1 - self.p1
        df_full = self.n2 - self.p2

        self.f_stat = stats.f_value(self.sse1, self.sse2, df_red, df_full)
        self.f_crit = stats.f.ppf(self.confidence_level, df_red - df_full, df_full)
        self.reject_null = self.f_stat > self.f_crit
        self.winner = self.r2 if self.reject_null else self.r1
