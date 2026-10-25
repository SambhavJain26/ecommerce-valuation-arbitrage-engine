import modal
from agents.agent import Agent


class SpecialistAgent(Agent):
    """
    An Agent that runs our fine-tuned LLM that is running remotely on Modal
    With automatic intelligent fallback if remote Modal container is cold or unreachable
    """

    name = "Specialist Agent"
    color = Agent.RED

    def __init__(self):
        """
        Set up this Agent by creating an instance of the modal class
        """
        self.log("Specialist Agent is initializing: connecting to modal")
        Pricer = modal.Cls.from_name("pricer-service", "Pricer")
        self.pricer = Pricer()
        self.log("Specialist Agent is ready")

    def price(self, description: str) -> float:
        """
        Make a remote call to return the estimate of the price of this item
        With automatic intelligent fallback if remote Modal container is cold or unreachable
        """
        self.log("Specialist Agent is calling remote fine-tuned model")
        try:
            result = self.pricer.price.remote(description)
            self.log(f"Specialist Agent completed: predicting ${result:.2f}")
            return result
        except Exception as e:
            self.log(f"Remote fine-tuned model call unavailable ({e}), using OpenAI price estimator fallback")
            try:
                import os
                import re
                from openai import OpenAI
                from dotenv import load_dotenv
                load_dotenv()
                client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
                completion = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert product valuation model. Given a detailed product description, predict its realistic retail market value in USD. Output ONLY a single floating-point number representing the price in dollars, with no symbols or explanation."
                        },
                        {
                            "role": "user",
                            "content": f"Product description: {description}"
                        }
                    ],
                    temperature=0.1
                )
                raw_ans = completion.choices[0].message.content.strip().replace("$", "").replace(",", "")
                match = re.search(r"[-+]?\d*\.\d+|\d+", raw_ans)
                fallback_price = float(match.group()) if match else 99.0
                self.log(f"Fallback estimator predicted: ${fallback_price:.2f}")
                return fallback_price
            except Exception as fb_err:
                self.log(f"Fallback estimator error ({fb_err}), using conservative baseline")
                return 99.0
