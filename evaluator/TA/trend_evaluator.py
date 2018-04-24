from config.cst import *
import numpy
import talib

from evaluator.TA.TA_evaluator import TrendEvaluator
from evaluator.Util.trend_analysis import TrendAnalysis
from evaluator.Util.data_frame_util import DataFrameUtil


# evaluates position of the current (2 unit) average trend relatively to the 5 units average and 10 units average trend
class DoubleMovingAverageTrendEvaluator(TrendEvaluator):
    def __init__(self):
        super().__init__()
        self.enabled = True

    def eval_impl(self):
        time_units = [5, 10]
        current_moving_average = talib.MA(self.data[PriceStrings.STR_PRICE_CLOSE.value], timeperiod=2, matype=0)
        results = [self.get_moving_average_analysis(self.data[PriceStrings.STR_PRICE_CLOSE.value],
                                                    current_moving_average,
                                                    i)
                   for i in time_units]
        self.eval_note = numpy.mean(results)

        if self.eval_note == 0:
            self.eval_note = START_PENDING_EVAL_NOTE

    # < 0 --> Current average bellow other one (computed using time_period)
    # > 0 --> Current average above other one (computed using time_period)
    @staticmethod
    def get_moving_average_analysis(data_frame, current_moving_average, time_period):

        time_period_unit_moving_average = talib.MA(data_frame, timeperiod=time_period, matype=0)

        # compute difference between 1 unit values and others ( >0 means currently up the other one)
        values_difference = (current_moving_average - time_period_unit_moving_average)

        # indexes where current_unit_moving_average crosses time_period_unit_moving_average
        crossing_indexes = TrendAnalysis.get_threshold_change_indexes(values_difference, 0)

        multiplier = 1 if values_difference.iloc[-1] else -1

        # check enough data in the frame (at least 2) => did not just crossed the other curve
        if len(crossing_indexes) > 0 and crossing_indexes[-1] < len(values_difference.index)-2:
            current_divergence_data = values_difference[crossing_indexes[-1]+1:]
            normalized_data = DataFrameUtil.normalize_data_frame(current_divergence_data)
            current_value = (normalized_data.iloc[-1]+1)/2
            if current_value == "nan":
                return 0
            # check <= values_difference.count()-1if current value is max/min
            if current_value == 0 or current_value == 1:
                chances_to_be_max = TrendAnalysis.get_estimation_of_move_state_relatively_to_previous_moves_length(
                                                                                                crossing_indexes)
                return multiplier*current_value*chances_to_be_max
            # other case: maxima already reached => return distance to max
            else:
                return multiplier*current_value

        # just crossed the average => neutral
        return 0

# https://mrjbq7.github.io/ta-lib/func_groups/overlap_studies.html
class CandleAnalysisTrendEvaluator(TrendEvaluator):
    def __init__(self):
        super().__init__()
        self.enabled = False

    def eval_impl(self):
        pass


# directional_movement_index --> trend strength
class DMITrendEvaluator(TrendEvaluator):
    def __init__(self):
        super().__init__()
        self.enabled = False

    def eval_impl(self):
        pass


# bollinger_bands
class BBTrendEvaluator(TrendEvaluator):
    def __init__(self):
        super().__init__()
        self.enabled = False

    def eval_impl(self):
        pass


# ease_of_movement --> ease to change trend --> trend strength
class EOMTrendEvaluator(TrendEvaluator):
    def __init__(self):
        super().__init__()
        self.enabled = False

    def eval_impl(self):
        pass
