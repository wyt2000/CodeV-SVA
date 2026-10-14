def stdsft_to_trl(dataset):
    for item in dataset:
        yield {"messages": item["question"] + item["response"]}
