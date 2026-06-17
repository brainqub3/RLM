from typing import Sequence
import itertools
import random
from collections import Counter, defaultdict

from constants import TASK_TYPE, ANSWER_TYPE


class Task:
    question: str
    answer: Sequence[str] = []
    task_type: TASK_TYPE
    answer_type: ANSWER_TYPE
    input_subset: bool

    def __init__(self, question, answer, task, answer_type, input_subset=False) -> None:
        self.question = question
        self.answer = answer
        self.task_type = task
        self.answer_type = answer_type
        self.input_subset = input_subset

    def eval(self, candidate):
        if candidate in self.answer:
            return 1
        else:
            return 0


class CountingTasks:
    tasks: Sequence[Task]

    def __init__(self, true_counts):
        self.tasks = []
        label_list = ", ".join(list(true_counts.keys()))
        total_count = sum([true_counts[key] for key in true_counts.keys()])

        def get_closest(key):
            min_diff = 1
            keyfreq = true_counts[key] / total_count
            for compkey in true_counts:
                if compkey == key:
                    continue
                diff = abs(keyfreq - true_counts[compkey] / total_count)
                if diff < min_diff:
                    min_diff = diff
            return min_diff

        # get max val task
        max_val = true_counts[max(true_counts, key=true_counts.get)]
        keys = [k for k in true_counts if true_counts[k] == max_val]
        if len(keys) == 1 and get_closest(keys[0]) > 0.02:
            self.tasks.append(
                Task(
                    question=f"In the above data, which of the labels is the most common? Give your final answer in the form 'Label: answer' where answer is one of the labels: {label_list}.",
                    answer=[k for k in true_counts if true_counts[k] == max_val],
                    task=TASK_TYPE.MOST_FREQ,
                    answer_type=ANSWER_TYPE.LABEL,
                )
            )

        # get min value task
        min_val = true_counts[min(true_counts, key=true_counts.get)]
        self.tasks.append(
            Task(
                question=f"In the above data, which of the labels is the least common? Give your final answer in the form 'Label: answer' where answer is one of the labels: {label_list}.",
                answer=[k for k in true_counts if true_counts[k] == min_val],
                task=TASK_TYPE.LEAST_FREQ,
                answer_type=ANSWER_TYPE.LABEL,
            )
        )

        # get comparisons tasks
        comparisons = list(itertools.combinations(list(true_counts.keys()), 2))
        for A, B in comparisons:
            diff = true_counts[A] / total_count - true_counts[B] / total_count
            if abs(diff) > 0.02 or (diff == 0 and A != B):
                self.tasks.append(
                    Task(
                        question=f"In the above data, is label '{A}' more common, less common, or the same frequency as label '{B}'? Give your final answer in the form 'Answer: {A} is [X] {B}', where [X] is 'more common than', 'less common than', or 'same frequency as'.",
                        answer=[
                            "more common than"
                            if (true_counts[A] > true_counts[B])
                            else "less common than"
                            if (true_counts[A] < true_counts[B])
                            else "same frequency as"
                        ],
                        task=TASK_TYPE.RELATIVE_FREQ,
                        answer_type=ANSWER_TYPE.COMPARISON,
                    )
                )

        # get absolute counts tasks
        for label in true_counts.keys():
            self.tasks.append(
                Task(
                    question=f"In the above data, how many data points should be classified as label '{label}'? Give your final answer in the form 'Answer: number'.",
                    answer=[true_counts[label]],
                    task=TASK_TYPE.NUMERIC_ONE_CLASS,
                    answer_type=ANSWER_TYPE.NUMERIC,
                )
            )


class TemporalTasks:
    tasks: Sequence[Task]

    def __init__(self, true_counts, in_context):
        self.tasks = []

        most_common_dates = sorted(
            Counter(in_context["dateobj"]).items(), key=lambda x: x[1], reverse=True
        )[:50]

        if len(most_common_dates) == 1: # can only really ask one temporal question 
            self.tasks.append(
                Task(
                    question="In the above data, which date is represented most often? Give your final answer in the form 'Date: [X]', where [X] is the date in the format MM/DD/YYYY.",
                    answer=[most_common_dates[0][0]],
                    task=TASK_TYPE.MOST_FREQ,
                    answer_type=ANSWER_TYPE.DATE,
                )
            )
            return 
        
        if most_common_dates[0][1] > most_common_dates[1][1]:
            self.tasks.append(
                Task(
                    question="In the above data, which date is represented most often? Give your final answer in the form 'Date: [X]', where [X] is the date in the format MM/DD/YYYY.",
                    answer=[most_common_dates[0][0]],
                    task=TASK_TYPE.MOST_FREQ,
                    answer_type=ANSWER_TYPE.DATE,
                )
            )
            if most_common_dates[1][1] > most_common_dates[2][1]:
                self.tasks.append(
                    Task(
                        question="In the above data, which date is represented the second most often? Give your final answer in the form 'Date: [X]', where [X] is the date in the format MM/DD/YYYY.",
                        answer=[most_common_dates[1][0]],
                        task=TASK_TYPE.SECOND_MOST_FREQ,
                        answer_type=ANSWER_TYPE.DATE,
                    )
                )
        n = most_common_dates[3][1]
        self.tasks.append(
            Task(
                question=f"In the above data, how many dates are represented exactly {n} times? Give your final answer in the form 'Answer: [X]', where [X] is the number of dates represented exactly {n} times.",
                answer=[
                    len(
                        [datepair for datepair in most_common_dates if datepair[1] == n]
                    )
                ],
                task=TASK_TYPE.REPRESENTED_N_TIMES,
                answer_type=ANSWER_TYPE.NUMERIC,
            )
        )

        # get frequency before or after time task
        sorted_by_date = in_context.sort("dateobj")

        def get_frac(set, label):
            return len([s for s in set if s == label]) / len(set)

        patience = 10
        question_generated = False
        while not question_generated and patience > 0:
            starting_point = random.randint(
                int(len(in_context) * 0.15), int(len(in_context) * 0.75)
            )
            if starting_point == len(sorted_by_date) - 1:
                starting_point -= 2
            time = sorted_by_date[starting_point]["dateobj"]
            before_index = starting_point

            # compensate for possible duplicate times
            while sorted_by_date[before_index - 1]["dateobj"] == time:
                before_index -= 1

            after_index = starting_point + 1
            while sorted_by_date[after_index]["dateobj"] == time:
                after_index += 1

            before = sorted_by_date[:before_index]["y"]
            after = sorted_by_date[after_index:]["y"]

            label_dist_before = {k: get_frac(before, k) for k in set(before)}
            label_dist_after = {k: get_frac(after, k) for k in set(after)}
            label_dist_after

            labellist = list(label_dist_before.keys())
            random.shuffle(labellist)
            for key in labellist:
                diff = label_dist_before.get(key, 0) - label_dist_after.get(key, 0)
                if abs(diff) > 0.02:  # require a 2% difference to ask the question
                    self.tasks.append(
                        Task(
                            question=f"In the above data, was label '{key}' more common, less common, or the same frequency before {time}, as compared to after {time}? Give your final answer in the form 'Answer: {key} is [X] before {time}', where [X] is 'more common', 'less common', or 'the same frequency'.",
                            answer=["more common" if diff > 0 else "less common"],
                            task=TASK_TYPE.RELATIVE_FREQ,
                            answer_type=ANSWER_TYPE.COMPARISON,
                        )
                    )
                    question_generated = True
                elif diff == 0:
                    self.tasks.append(
                        Task(
                            question=f"In the above data, was label '{key}' more common, less common, or the same frequency before {time}, as compared to after {time}? Give your final answer in the form 'Answer: {key} is [X] before {time}', where [X] is 'more common', 'less common', or 'the same frequency'.",
                            answer=["the same frequency"],
                            task=TASK_TYPE.RELATIVE_FREQ,
                            answer_type=ANSWER_TYPE.COMPARISON,
                        )
                    )
            patience -= 1


        # counting tasks but only for a specific month
        months = {
            1: "January",
            2: "February",
            3: "March",
            4: "April",
            5: "May",
            6: "June",
            7: "July",
            8: "August",
            9: "September",
            10: "October",
            11: "November",
            12: "December",
        }

        def select_month():
            selected_month = random.choice(list(months.keys()))
            month_name = months[selected_month]
            month_counts = dict(
                Counter(
                    [t["y"] for t in in_context if t["dateobj"].month == selected_month]
                )
            )
            return month_counts, month_name

        month_counts, month_name = select_month()
        patience = 20
        while len(month_counts) == 0 and patience > 0:  # resample in the case where we have very little data and none of it corresponds to this month
            month_counts, month_name = select_month()
            patience -= 1

        new_tasks = CountingTasks(month_counts).tasks
        for task in new_tasks:
            task.question = task.question.replace(
                "In the above data,",
                f"For the following question, only consider the subset of instances that occur in {month_name} of any year. Among instances occuring in {month_name},",
            )
            task.input_subset = True
            self.tasks.append(task)


        # counting tasks but for a specific date range
        starting_point = random.randint(
            int(len(in_context) * 0.1), int(len(in_context) * 0.5)
        )
        starting_date = sorted_by_date[starting_point]["formatted_date"]
        while (
            sorted_by_date[starting_point - 1]["formatted_date"] == starting_date
        ):  # fixes date to actually be date-aware, not index-aware
            starting_point -= 1

        offset_amount = 10
        if len(in_context) < 11:
            offset_amount = len(in_context) // 2 
            if starting_point + offset_amount + 2 >= len(in_context):
                offset_amount = -1
        
        if offset_amount > 2: # enough examples to meaningfully do this
            ending_point = random.randint(
                starting_point + offset_amount, max(starting_point + offset_amount + 2, int(len(in_context) * 0.9))
            )
            if ending_point >= len(sorted_by_date):
                ending_point = len(sorted_by_date) - 1
            ending_date = sorted_by_date[ending_point]["formatted_date"]
            if ending_point < (len(sorted_by_date) - 1):
                while (
                    sorted_by_date[ending_point + 1]["formatted_date"] == ending_date
                ):  # fixes date to actually be date-aware, not index-aware
                    ending_point += 1

            selected = sorted_by_date[starting_point : ending_point + 1]
            range_counts = dict(Counter(selected["y"]))
            new_tasks = CountingTasks(range_counts).tasks
            for task in new_tasks:
                task.question = task.question.replace(
                    "In the above data,",
                    f"For the following question, only consider the subset of instances that occur between {starting_date} and {ending_date}, inclusive. Among instances occuring in this date range,",
                )
                task.input_subset = True
                self.tasks.append(task)

        sep_by_month = {}

        sep_by_month = defaultdict(list)
        for row in sorted_by_date:
            key = (row["dateobj"].month, row["dateobj"].year)
            sep_by_month[key].append(row["y"])

        freq_by_month = {}
        for daterange in sep_by_month:
            counter = Counter(sep_by_month[daterange])
            total_count = sum(counter.values())  # or len(sep_by_month[daterange])
            freq_by_month[daterange] = {
                label: count / total_count 
                for label, count in counter.items()
            }

        # when did <x> first become more frequent than <y>?
        for label1 in set(sorted_by_date["y"]):
            for label2 in set(sorted_by_date["y"]):
                if label1 == label2:
                    continue
                num_months_more_freq = 0
                for month in freq_by_month:
                    freq1 = freq_by_month[month].get(label1, 0.0)
                    freq2 = freq_by_month[month].get(label2, 0.0)

                    if freq1 > freq2:
                        self.tasks.append(
                            Task(
                                question=f"In which month did the label '{label1} first occur more often than the label '{label2}'? Give your final answer in the form 'Answer: [month] [year]', where [month] is the name of the month and [year] is the four-digit year where '{label1}' first occured more often than '{label2}.'",
                                answer=[f"{months[month[0]]} {month[1]}"],
                                task=TASK_TYPE.RELATIVE_FREQ,
                                answer_type=ANSWER_TYPE.MONTH_YEAR,
                            )
                        )
                    break


        # in how many months is <x> more frequent than y?
        for label1 in set(sorted_by_date["y"]):
            for label2 in set(sorted_by_date["y"]):
                if label1 == label2:
                    continue
                num_months_more_freq = 0
                for month in freq_by_month:
                    freq1 = freq_by_month[month].get(label1, 0.0)
                    freq2 = freq_by_month[month].get(label2, 0.0)

                    if freq1 > freq2:
                        num_months_more_freq += 1
                self.tasks.append(
                    Task(
                        question=f"For how many months does the label '{label1}' occur more frequently than the label '{label2}'? Disregard months where there is a tie.  Give your final answer in the form 'Answer: [X]', where [X] is the number of months where '{label1}' occurs more often than '{label2}.'",
                        answer=[num_months_more_freq],
                        task=TASK_TYPE.RELATIVE_FREQ,
                        answer_type=ANSWER_TYPE.NUMERIC,
                    )
                )

        # in how many months is x the single most frequent label?

        for label in set(sorted_by_date["y"]):
            num_months_most_freq = 0
            for month in freq_by_month:
                found_larger = False
                comp = freq_by_month[month].get(label, 0.0)
                for complabel in freq_by_month[month].keys():
                    if complabel != label and freq_by_month[month][complabel] >= comp:
                        found_larger = True
                        break
                if not found_larger:
                    num_months_most_freq += 1
            self.tasks.append(
                Task(
                    question=f"For how many months is the label '{label}' the single most frequently occuring label? Disregard months where there is a tie for the most common label.  Give your final answer in the form 'Answer: [X]', where [X] is the number of months where '{label}' is the most common label.",
                    answer=[num_months_most_freq],
                    task=TASK_TYPE.MOST_FREQ,
                    answer_type=ANSWER_TYPE.NUMERIC,
                )
            )

class UserTasks:
    tasks: Sequence[Task]

    def __init__(self, true_counts, in_context):

        max_num_users = len(set(in_context["user_id"]))
        max_set_size = min(50, max_num_users)
        self.tasks = []

        users = in_context["user_id"]
        label_column = in_context["y"]

        from collections import Counter


        user_id_counts = Counter(users)
        top_users = sorted(user_id_counts.items(), key=lambda x: x[1], reverse=True)[
            :max_set_size
        ]

        if len(top_users) > 1:
            if top_users[0][1] > top_users[1][1]:
                self.tasks.append(
                    Task(
                        question="In the above data, which user is represented most often? Give your final answer in the form 'User: [X]', where [X] is the user ID.",
                        answer=[top_users[0][0]],
                        task=TASK_TYPE.MOST_FREQ,
                        answer_type=ANSWER_TYPE.USER,
                    )
                )
                if len(top_users) == 2 or top_users[1][1] > top_users[2][1]:
                    self.tasks.append(
                        Task(
                            question="In the above data, which user is represented the second most often? Give your final answer in the form 'User: [X]', where [X] is the user ID.",
                            answer=[top_users[1][0]],
                            task=TASK_TYPE.SECOND_MOST_FREQ,
                            answer_type=ANSWER_TYPE.USER,
                        )
                    )

        # SUBSET OF USERS
        user_subset = random.sample(
            top_users, min(1,min(random.randint(0, 10) + 10, int(max_set_size * 0.8)))
        )

        users_subset_ids_only = [
            str(user_subset[i][0]) for i in range(len(user_subset))
        ]

        user_names = ", ".join(users_subset_ids_only)

        labels_for_user_subset = [
            (user_id, y_val)
            for user_id, y_val in zip(in_context["user_id"], in_context["y"])
            if str(user_id) in users_subset_ids_only
        ]

        user_id_counts = Counter([u[0] for u in labels_for_user_subset])

        top_users = sorted(user_id_counts.items(), key=lambda x: x[1], reverse=True)[
            :max_set_size
        ]
        if len(top_users) > 1:
            if top_users[0][1] > top_users[1][1]:
                self.tasks.append(
                    Task(
                        question=f"For the following question, only consider the subset of users with IDs {user_names}. Among these users, which user is represented most often? Give your final answer in the form 'User: [X]', where [X] is the user ID.",
                        answer=[top_users[0][0]],
                        task=TASK_TYPE.MOST_FREQ,
                        answer_type=ANSWER_TYPE.USER,
                        input_subset=True,
                    )
                )
                if len(top_users) > 2 and top_users[1][1] > top_users[2][1]:
                    self.tasks.append(
                        Task(
                            question=f"For the following question, only consider the subset of users with IDs {user_names}. Among these users, which user is represented the second most often? Give your final answer in the form 'User: [X]', where [X] is the user ID.",
                            answer=[top_users[1][0]],
                            task=TASK_TYPE.SECOND_MOST_FREQ,
                            answer_type=ANSWER_TYPE.USER,
                            input_subset=True,
                        )
                    )
        # counting tasks with user subset
        user_subset_counts = dict(
            Counter([label[1] for label in labels_for_user_subset])
        )
        if len(user_subset_counts) > 0:
            new_tasks = CountingTasks(user_subset_counts).tasks
            for task in new_tasks:
                task.question = task.question.replace(
                    "In the above data,",
                    f"For the following question, only consider the subset of instances that are associated with user IDs {user_names}. Among instances associated with these users,",
                )
                task.input_subset = True
                self.tasks.append(task)


            label_user_counts = defaultdict(list)
            for user_id, label in labels_for_user_subset:
                label_user_counts[label].append(user_id)
                
            for label in label_user_counts:
                usercounts = Counter(label_user_counts[label])
                top_users = sorted(usercounts.items(), key=lambda x: x[1], reverse=True)[
                    :10
                ]

                if len(top_users) > 1 and (top_users[0][1] > top_users[1][1]):
                    self.tasks.append(
                        Task(
                            question=f"For the following question, only consider the subset of users with IDs {user_names}. Among these users, which user has the most instances with the label {label}? Give your final answer in the form 'User: [X]', where [X] is the user ID.",
                            answer=[top_users[0][0]],
                            task=TASK_TYPE.MOST_FREQ,
                            answer_type=ANSWER_TYPE.USER,
                            input_subset=True,
                        )
                    )

            label_user_counts = {}
            label_user_counts = defaultdict(list)
            for user_id, label in zip(users, label_column):
                label_user_counts[label].append(user_id)
            for label in label_user_counts:
                usercounts = Counter(label_user_counts[label])
                top_users = sorted(usercounts.items(), key=lambda x: x[1], reverse=True)[
                    :10
                ]
                if len(top_users) > 1 and (top_users[0][1] > top_users[1][1]):
                    self.tasks.append(
                        Task(
                            question=f"In the above data, which user has the most instances with the label {label}? Give your final answer in the form 'User: [X]', where [X] is the user ID.",
                            answer=[top_users[0][0]],
                            task=TASK_TYPE.MOST_FREQ,
                            answer_type=ANSWER_TYPE.USER,
                        )
                    )

                found = False
                patience = 10
                range_middle = 5
                range_end = 9
                if range_end >= len(top_users):
                    range_end = len(top_users) - 1
                    range_middle = int(range_end // 2)
                while not found and patience > 0:
                    rand1 = random.randint(0, range_middle)
                    rand2 = random.randint(range_middle, range_end)

                    if top_users[rand1][1] > top_users[rand2][1] + 1:
                        self.tasks.append(
                            Task(
                                question=f"In the above data, which user has more instances with the label {label}: User {top_users[rand1][0]} or User {top_users[rand2][0]}? Give your final answer in the form 'User: [X]', where [X] is the user ID.",
                                answer=[top_users[rand1][0]],
                                task=TASK_TYPE.RELATIVE_FREQ,
                                answer_type=ANSWER_TYPE.USER,
                            )
                        )
                        found = True
                    else:
                        patience -= 1

        