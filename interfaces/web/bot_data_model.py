import time

import plotly
import plotly.graph_objs as go

from config.cst import PriceStrings, TimeFrames
from evaluator.evaluator_matrix import EvaluatorMatrix
from interfaces.web import get_bot, add_to_matrix_history, get_matrix_history, add_to_symbol_data_history, \
    add_to_portfolio_value_history, get_portfolio_value_history
from trading.trader.portfolio import Portfolio


def get_value_from_dict_or_string(data, is_time_frame=False):
    if isinstance(data, dict):
        if is_time_frame:
            return TimeFrames(data["value"])
        else:
            return data["value"]
    else:
        if is_time_frame:
            return TimeFrames(data)
        else:
            return data


def get_portfolio_currencies_update():
    currencies = []
    bot = get_bot()
    traders = [trader for trader in bot.get_exchange_traders().values()] + \
              [trader for trader in bot.get_exchange_trader_simulators().values()]
    for trader in traders:
        currencies += [
                        {
                            "Cryptocurrency": [currency],
                            "Total (available)": ["{} ({})".format(amounts[Portfolio.TOTAL],
                                                                   amounts[Portfolio.AVAILABLE])],
                            "Exchange": [trader.exchange.get_name()],
                            "Real / Simulator": ["Simulator" if trader.get_simulate() else "Real"]
                        }
                        for currency, amounts in trader.get_portfolio().get_portfolio().items()]
    return currencies


def get_portfolio_value_in_history():

    reference_market = None
    at_least_one_simulated = False
    max_value = 0
    simulated_value = 0
    real_value = 0
    bot = get_bot()
    traders = [trader for trader in bot.get_exchange_traders().values()] + \
              [trader for trader in bot.get_exchange_trader_simulators().values()]
    for trader in traders:
        trade_manager = trader.get_trades_manager()
        if not reference_market:
            reference_market = trade_manager.get_reference()
        if trader.get_simulate():
            simulated_value += trade_manager.get_portfolio_current_value()
            at_least_one_simulated = False
        else:
            real_value += trade_manager.get_portfolio_current_value()

    add_to_portfolio_value_history(real_value, simulated_value)

    formatted_real_value_history = {
        "timestamps": [],
        "value": []
    }
    formatted_simulated_value_history = {
        "timestamps": [],
        "value": []
    }

    for value in get_portfolio_value_history():
        time_stamp = value["timestamp"]
        real_value = value["real_value"]
        simulated_value = value["simulated_value"]

        formatted_real_value_history["timestamps"].append(time_stamp)
        formatted_simulated_value_history["timestamps"].append(time_stamp)
        formatted_real_value_history["value"].append(real_value)
        formatted_simulated_value_history["value"].append(simulated_value)

        if max_value < real_value:
            max_value = real_value
        if max_value < simulated_value:
            max_value = simulated_value

    real_data = plotly.graph_objs.Scatter(
        x=formatted_real_value_history["timestamps"],
        y=formatted_real_value_history["value"],
        name='Real Portfolio in {}'.format(reference_market),
        mode='lines+markers'
    )

    simulated_data = plotly.graph_objs.Scatter(
        x=formatted_simulated_value_history["timestamps"],
        y=formatted_simulated_value_history["value"],
        name='Simulated Portfolio in {}'.format(reference_market),
        mode='lines+markers'
    )

    merged_data = [real_data]
    if at_least_one_simulated:
        merged_data.append(simulated_data)

    return {'data': merged_data,
            'layout': go.Layout(xaxis=dict(range=[get_bot().get_start_time(), time.time()]),
                                yaxis=dict(range=[0, max(0.01, max_value)]), )}


def get_currency_graph_update(exchange_name, symbol, time_frame):
    symbol_evaluator_list = get_bot().get_symbol_evaluator_list()
    exchange_list = get_bot().get_exchanges_list()

    if time_frame is not None:
        if len(symbol_evaluator_list) > 0:
            evaluator_thread_managers = symbol_evaluator_list[symbol].get_evaluator_thread_managers(
                exchange_list[exchange_name])

            for evaluator_thread_manager in evaluator_thread_managers:
                if evaluator_thread_manager.get_evaluator().get_time_frame() == time_frame:
                    df = evaluator_thread_manager.get_evaluator().get_data()

                    if df is not None:
                        add_to_symbol_data_history(symbol, df, time_frame)

                        X = df[PriceStrings.STR_PRICE_TIME.value]
                        Y = df[PriceStrings.STR_PRICE_CLOSE.value]

                        # Candlestick
                        data = go.Ohlc(x=df[PriceStrings.STR_PRICE_TIME.value],
                                       open=df[PriceStrings.STR_PRICE_OPEN.value],
                                       high=df[PriceStrings.STR_PRICE_HIGH.value],
                                       low=df[PriceStrings.STR_PRICE_LOW.value],
                                       close=df[PriceStrings.STR_PRICE_CLOSE.value])

                        return {'data': [data], 'layout': go.Layout(xaxis=dict(range=[min(X), max(X)]),
                                                                    yaxis=dict(range=[min(Y) * 0.98, max(Y) * 1.02]), )}
    return None


def get_evaluator_graph_in_matrix_history(symbol,
                                          exchange_name,
                                          evaluator_type,
                                          evaluator_name,
                                          time_frame):
    symbol_evaluator_list = get_bot().get_symbol_evaluator_list()
    exchange_list = get_bot().get_exchanges_list()

    if evaluator_name is not None and len(symbol_evaluator_list) > 0:
        matrix = symbol_evaluator_list[symbol].get_matrix(exchange_list[exchange_name])
        add_to_matrix_history(matrix)

        formatted_matrix_history = {
            "timestamps": [],
            "evaluator_data": []
        }

        for matrix in get_matrix_history():
            eval_note = EvaluatorMatrix.get_eval_note(matrix["matrix"], evaluator_type, evaluator_name, time_frame)

            if eval_note is not None:
                formatted_matrix_history["evaluator_data"].append(eval_note)
                formatted_matrix_history["timestamps"].append(matrix["timestamp"])

        data = plotly.graph_objs.Scatter(
            x=formatted_matrix_history["timestamps"],
            y=formatted_matrix_history["evaluator_data"],
            name='Scatter',
            mode='lines+markers'
        )

        return {'data': [data], 'layout': go.Layout(xaxis=dict(range=[get_bot().get_start_time(), time.time()]),
                                                    yaxis=dict(range=[-1, 1]), )}
    return None
