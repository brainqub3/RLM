import enum


class TASK_TYPE(enum.Enum):
    """Enum of task types for evaluation data generation."""

    MOST_FREQ = "most_common_label"
    LEAST_FREQ = "least_common_label"
    RELATIVE_FREQ = "relative_freq"
    NUMERIC_ONE_CLASS = "numeric_one_class"
    SECOND_MOST_FREQ = "second_most_freq"
    REPRESENTED_N_TIMES = "represented_n_times"


class ANSWER_TYPE(enum.Enum):
    USER = "user"
    LABEL = "label"
    NUMERIC = "numeric"
    DATE = "date"
    MONTH_YEAR = "month_and_year"
    COMPARISON = "comp"
