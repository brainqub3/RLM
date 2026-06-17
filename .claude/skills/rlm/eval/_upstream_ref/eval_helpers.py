import litellm
from datasets import load_dataset
import jsonlines
import tiktoken
import dateutil

from datetime import datetime
import os
import ast
import sys
import re
from pathlib import Path

# try to parse the answer; super simple, idea is that we can go back and try harder on "low" or sometimes "med" confidence answers
def synth_attempt_answer_parse(answer):
    parse_confidence = "low"
    if ":" not in answer:  # bad start
        if len(answer) < 20:  # it's short, return the whole thing
            return answer, parse_confidence
        else:
            return answer.split()[-1], parse_confidence
    candidate_answer = answer.split(":")[-1].strip()
    candidate_answer = candidate_answer.replace(
        "*", ""
    )  # OpenAI models like bolding the answer


    candidate_answer = candidate_answer.replace(
        "[", ""
    ) 
    candidate_answer = candidate_answer.replace(
        "]", ""
    )  # Anthropic models like putting the answer in []
    parse_confidence = "med"
    if (
        "User:" in answer
        or "Answer:" in answer
        or "Date:" in answer
        or "Label" in answer
    ):
        parse_confidence = "high"
    if len(candidate_answer) < 20:
        parse_confidence = "vhigh"
    elif "more common" in candidate_answer:
        candidate_answer = "more common"
    elif "less common" in candidate_answer:
        candidate_answer = "less common"
    elif "same frequency" in candidate_answer:
        candidate_answer = "same frequency"

    return candidate_answer, parse_confidence


def synth_process_response(datapoint, output, model):

    score = 0
    gold = (
        ast.literal_eval(datapoint["answer"])[0]
        if "datetime" not in datapoint["answer"]
        else datetime.strptime(datapoint["answer"], "[datetime.date(%Y, %m, %d)]")
    )

    trimmed_output, parse_confidence =  synth_attempt_answer_parse(output)
    if str(trimmed_output) == str(gold):
        score = 1
    elif str(trimmed_output) in ['more common', 'less common', 'same frequency']: # account for these being slightly different wordings
        if str(trimmed_output) in  str(gold):
            score = 1
    elif (
        datapoint["answer_type"] == "ANSWER_TYPE.NUMERIC"
    ):  # partial credit for numbers
        try:
            trimmed_output = int(trimmed_output)
            gold = int(gold)
            score = 0.75 ** (abs(gold - trimmed_output))
        except Exception:
            parse_confidence = "low"  # didn't parse as a number, that's a bad sign
    elif datapoint["answer_type"] == "ANSWER_TYPE.DATE":
        try:
            trimmed_output = dateutil.parser.parse(trimmed_output)
            score = trimmed_output == gold
        except Exception:
            parse_confidence = "low"  # didn't parse as a date, that's a bad sign


    this_output = {
        "id": datapoint["id"],
        "context_window_id": datapoint["context_window_id"],
        "dataset": datapoint["dataset"],
        "model": model,
        "attempted_parse": str(trimmed_output),
        "parse_confidence": parse_confidence,
        "full_answer": output,
        "score": score,
        "answer": str(gold),
    }

    return this_output


"""Eval helpers for DnD split."""
from transformers import AutoTokenizer



def dnd_parse_answer(answer) -> int | str | list[str]:
    """Parse the answer into int, str, or list of str."""
    # Try to convert to int first
    try:
        return int(answer)
    except ValueError:
        pass

    # Check if it contains commas (list case)
    if "," in answer:
        return [item.strip() for item in answer.split(",") if item.strip()]

    # Otherwise return as string
    return answer


def dnd_parse_response(answer) -> tuple[str, str]:
    match = re.search(r"\\boxed\{\\text\{([^}]*)\}\}", answer) or re.search(
        r"\\boxed[\{]+([^}]*)[\}]+", answer
    )
    if match:
        answer = match.group(1)
    else:
        return answer, "low"
    return dnd_parse_answer(answer), "high"


def dnd_process_response(datapoint, output, model) -> dict:
    gold = dnd_parse_answer(datapoint["answer"])
    trimmed_output, parse_confidence = dnd_parse_response(output)
    # score based on the type of gold answer
    score = 0.0
    if isinstance(gold, int) and isinstance(trimmed_output, int):
        score = 0.75 ** abs(gold - trimmed_output)
    elif isinstance(gold, str) and isinstance(trimmed_output, str):
        score = float(gold.strip().lower() == trimmed_output.strip().lower())
    elif isinstance(gold, list) and isinstance(trimmed_output, list):
        overlap = set(gold) & set(trimmed_output)
        score = len(overlap) / len(gold) if gold else 0.0
    # else:
    #     msg = f"unknown match, gold answer type: {type(gold)}, model answer type: {type(trimmed_output)}"
    #     raise ValueError(msg)
    return {
        "id": datapoint["id"],
        "context_window_id": datapoint["context_window_id"],
        "model": model,
        "attempted_parse": trimmed_output,
        "parse_confidence": parse_confidence,
        "full_answer": output,
        "score": score,
        "answer": gold,
    }

