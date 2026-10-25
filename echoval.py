import logging
import queue
import threading
import time
import pandas as pd
import gradio as gr
from deal_agent_framework import DealAgentFramework
from agents.deals import Opportunity, Deal
from log_utils import reformat


class QueueHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(self.format(record))

def html_for(log_data):
    output = '<br>'.join(log_data[-18:])
    return f"""
    <div id="scrollContent" style="height: 400px; overflow-y: auto; border: 1px solid #333; background-color: #1a1a24; padding: 12px; font-family: monospace; font-size: 13px; line-height: 1.5; border-radius: 8px;">
    {output}
    </div>
    """

def setup_logging(log_queue):
    handler = QueueHandler(log_queue)
    formatter = logging.Formatter(
        "[%(asctime)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S %z",
    )
    handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class App:

    def __init__(self):
        self.agent_framework = None

    def get_agent_framework(self):
        if not self.agent_framework:
            self.agent_framework = DealAgentFramework()
            self.agent_framework.init_agents_as_needed()
        return self.agent_framework

    def run(self):
        css_style = """
            #logs_column {
                max-width: 420px;
            }
            .dataframe th {
                background-color: #2a2a36 !important;
                color: #ffffff !important;
                font-weight: 600 !important;
            }
        """
        with gr.Blocks(title="EchoVal AI", fill_width=True) as ui:

            log_data = gr.State([])

            def table_for(opps):
                columns = ["Deals found so far", "Price", "Estimate", "Discount", "URL"]
                if not opps:
                    return pd.DataFrame(columns=columns)
                data = [
                    [
                        opp.deal.product_description,
                        f"${opp.deal.price:.2f}",
                        f"${opp.estimate:.2f}",
                        f"${opp.discount:.2f}",
                        opp.deal.url
                    ]
                    for opp in opps
                ]
                return pd.DataFrame(data, columns=columns)

            def update_output(log_data, log_queue, result_queue):
                initial_result = table_for(self.get_agent_framework().memory)
                final_result = None
                while True:
                    try:
                        message = log_queue.get_nowait()
                        log_data.append(reformat(message))
                        yield log_data, html_for(log_data), final_result or initial_result
                    except queue.Empty:
                        try:
                            final_result = result_queue.get_nowait()
                            yield log_data, html_for(log_data), final_result or initial_result
                        except queue.Empty:
                            if final_result is not None:
                                break
                            time.sleep(0.1)

            def do_run():
                new_opportunities = self.get_agent_framework().run()
                table = table_for(new_opportunities)
                return table

            def run_with_logging(initial_log_data):
                log_queue = queue.Queue()
                result_queue = queue.Queue()
                setup_logging(log_queue)

                def worker():
                    result = do_run()
                    result_queue.put(result)

                thread = threading.Thread(target=worker)
                thread.start()

                for log_data, output, final_result in update_output(initial_log_data, log_queue, result_queue):
                    yield log_data, output, final_result

            def do_select(selected_index: gr.SelectData):
                opportunities = self.get_agent_framework().memory
                row = selected_index.index[0]
                if row < len(opportunities):
                    opportunity = opportunities[row]
                    self.get_agent_framework().planner.messenger.alert(opportunity)

            with gr.Row():
                gr.Markdown('<div style="text-align: center;font-size:26px;margin-top:10px;"><strong>EchoVal AI</strong>: Autonomous Multi-Agent Deal Intelligence</div>')
            with gr.Row():
                gr.Markdown('<div style="text-align: center;font-size:14px;color:#888;margin-bottom:12px;">A fine-tuned QLoRA model deployed on Modal GPU infrastructure and structured multi-agent coordination continuously evaluate online deals and dispatch real-time alerts.</div>')

            with gr.Row():
                with gr.Column(scale=1):
                    initial_opps = table_for(self.get_agent_framework().memory)
                    opportunities_dataframe = gr.Dataframe(
                        value=initial_opps,
                        headers=["Deals found so far", "Price", "Estimate", "Discount", "URL"],
                        wrap=True,
                        column_widths=["44%", "14%", "14%", "14%", "14%"],
                    )
                with gr.Column(scale=1, elem_id="logs_column"):
                    initial_logs = [
                        "[Agent Framework] Initializing EchoVal AI multi-agent pipeline...",
                        f"[Memory] Successfully loaded {len(self.get_agent_framework().memory)} verified opportunities from state store",
                        "[Planner Agent] Scanner, Specialist, and Messaging agents active",
                        "[Ready] Standing by for scheduled polling cycles"
                    ]
                    logs = gr.HTML(value=html_for(initial_logs))

            ui.load(run_with_logging, inputs=[log_data], outputs=[log_data, logs, opportunities_dataframe])

            timer = gr.Timer(value=300, active=True)
            timer.tick(run_with_logging, inputs=[log_data], outputs=[log_data, logs, opportunities_dataframe])

            opportunities_dataframe.select(do_select)

        ui.launch(share=False, inbrowser=False, server_port=7860, css=css_style)


if __name__ == "__main__":
    App().run()
