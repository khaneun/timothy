
def budget_for_single_portfolio(deposit, mode=0, captive_rate=0.5, sharing_rate=0.25, single_budget=100000):

    budget = 0

    if mode == 0:
        # 예산의 12.5%를 단일 종목 매수에 모두 사용함
        budget = int(deposit) * captive_rate
        budget = budget * sharing_rate

    elif mode == 1:
        # 종목당 고정 금액(Default 100000) 사용함
        budget = single_budget

    return int(budget)