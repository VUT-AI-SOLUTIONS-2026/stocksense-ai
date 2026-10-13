"""Ask StockSense in a terminal: python -m stocksense.terminal"""
import argparse
import re
import sys

from stocksense.assistant import ConversationContext, SUGGESTED_QUESTIONS, answer_question
from stocksense.data import ITEMS
from stocksense.inventory import plan_stock
from stocksense.runtime import ForecastService, load_assistant

HELP = """Type a question, or use these commands:
  /product N  Select Product 1 to 5; reset follow-up focus and its stock plan.
  /stock      Enter stock and delivery inputs, then calculate a suggested order.
  /forecast   Show the sales forecast.
  /history    Show recent observed sales.
  /compare    Compare all five products' forecasts.
  /models     Explain the recorded model results.
  /status     Show the selected product and follow-up focus.
  /clear      Reset follow-up focus; keep the selected product's stock plan.
  /help       Show this help and example questions.
  /quit       Exit. You can also type exit or quit.

Examples: Forecast for Product 2; Show the daily breakdown;
Which is the busiest forecast day?; What is buffer stock?
An explicitly named product becomes the focus for follow-up questions.
Use /product N before /stock: stock inputs apply to the selected product.
"""
SHORTCUTS = {"/forecast": SUGGESTED_QUESTIONS[0], "/history": SUGGESTED_QUESTIONS[2],
             "/models": SUGGESTED_QUESTIONS[3], "/compare": SUGGESTED_QUESTIONS[4]}


class TerminalSession:
    """Keep this terminal's conversation and submitted stock plan in memory."""
    def __init__(self, service, model, item=1):
        self.service = service
        self.model = model
        self.item = item
        self.stock_plan = None
        self.conversation = ConversationContext()
        self.select_product(item)

    def select_product(self, item):
        if isinstance(item, bool) or item not in ITEMS:
            raise ValueError("Choose a product number from 1 to 5, for example /product 2.")
        if item != self.item:
            self.stock_plan = None
            self.clear()
        self.item = item

    def clear(self):
        self.conversation = ConversationContext()

    def calculate_stock(self, **inputs):
        self.stock_plan = None
        self.stock_plan = plan_stock(self.service.forecast(self.item)["prediction"], **inputs)
        self.conversation.remember([self.item], "reorder")
        return self.stock_plan

    def answer(self, question):
        context = self.service.context_for_item(self.item)
        return answer_question(question, model=self.model, item=self.item, **context,
                               stock_plan=self.stock_plan, comparison=self.service.comparison,
                               context_for_item=self.service.context_for_item,
                               conversation=self.conversation, interface="terminal")

    def status(self):
        focus = ", ".join(f"Product {item}" for item in self.conversation.items) or "selected product"
        stock = "calculated" if self.stock_plan is not None else "not calculated"
        return f"Selected: Product {self.item} | Follow-up focus: {focus} | Stock plan: {stock}"

    def prompt(self):
        focus = self.conversation.items
        if len(focus) == 1 and focus[0] != self.item:
            return f"You [selected Product {self.item}; focus Product {focus[0]}]> "
        if len(focus) > 1:
            return f"You [Product {self.item}; comparison focus]> "
        return f"You [Product {self.item}]> "


def plain_text(answer):
    """Remove bold markers and align the assistant's small tables for a terminal."""
    lines = re.sub(r"\*\*(.*?)\*\*", r"\1", answer).splitlines()
    output = []
    index = 0
    while index < len(lines):
        if not lines[index].startswith("|"):
            output.append(lines[index])
            index += 1
            continue
        rows = []
        while index < len(lines) and lines[index].startswith("|"):
            cells = [cell.strip() for cell in lines[index].strip("|").split("|")]
            if not all(re.fullmatch(r":?-+:?", cell) for cell in cells):
                rows.append(cells)
            index += 1
        widths = [max(len(row[column]) for row in rows) for column in range(len(rows[0]))]
        for row_index, row in enumerate(rows):
            output.append("  ".join(cell.ljust(width) for cell, width in zip(row, widths)).rstrip())
            if row_index == 0:
                output.append("  ".join("-" * width for width in widths))
    return "\n".join(output)


class StockEntryCancelled(Exception):
    pass


def read_number(label, default, minimum=0, maximum=None):
    while True:
        entered = input(f"{label} [{default}]: ").strip()
        if entered.lower() in {"cancel", "/cancel"}:
            raise StockEntryCancelled
        try:
            value = default if not entered else int(entered)
            if value < minimum or (maximum is not None and value > maximum):
                raise ValueError
            return value
        except ValueError:
            limit = f"from {minimum} to {maximum}" if maximum is not None else f"at least {minimum}"
            print(f"Enter a whole number {limit}, or /cancel.")


def read_stock_inputs(item):
    print(f"\nStock planning for Product {item}.")
    print("Press Enter to accept each example value, or type /cancel to stop.")
    print("These defaults are demonstration inputs. Enter your own values for a stock scenario.")
    print("Delivery arrives after the lead-time days. Lead time + review interval must be at most 7.")
    stock = read_number("Stock available (units)", 50)
    outstanding = read_number("Outstanding units", 0)
    lead = read_number("Supplier lead time (days)", 2, maximum=6)
    review = read_number("Review interval (days)", min(3, 7 - lead), minimum=1, maximum=7 - lead)
    buffer = read_number("Buffer stock (units)", 10)
    return dict(stock=stock, outstanding=outstanding, lead_days=lead, review_days=review, buffer=buffer)


def run_chat(session):
    service = session.service
    forecast = service.forecast(session.item)
    print("\nStockSense AI | Sunrise Mini Market | Terminal chat")
    print("Fictional retailer; anonymous Store 1 and Products 1 to 5.")
    print(f"Forecast method: {service.label}. Last observed day: {service.cutoff:%d %B %Y}.")
    print(f"Historical demonstration: forecasts cover {forecast['date'].min():%d %B %Y} "
          f"to {forecast['date'].max():%d %B %Y}; these dates have no measured outcomes here.")
    print("Type a question. Use /help for examples, /stock for an order or /quit to exit.\n")
    while True:
        question = input(session.prompt()).strip()
        if not question:
            continue
        if question.lower() in {"/quit", "/exit", "quit", "exit"}:
            return
        if len(question) > 500:
            print("Please keep your question to 500 characters or fewer.\n")
            continue
        try:
            command, _, argument = question.partition(" ")
            command = command.lower()
            if command in {"/help", "/status", "/clear", "/stock", *SHORTCUTS} and argument.strip():
                print(f"Use {command} by itself. Type /help for the command list.\n")
                continue
            if command == "/help":
                print(HELP)
            elif command == "/status":
                print(session.status() + "\n")
            elif command == "/clear":
                session.clear()
                print("Follow-up focus cleared. " + session.status() + "\n")
            elif command == "/product":
                try:
                    selected = int(argument.strip())
                except ValueError:
                    raise ValueError("Use /product followed by a number from 1 to 5, for example /product 2.") from None
                session.select_product(selected)
                print(session.status() + "\n")
            elif command == "/stock":
                try:
                    inputs = read_stock_inputs(session.item)
                except StockEntryCancelled:
                    print("Stock entry cancelled. " + session.status() + "\n")
                    continue
                session.calculate_stock(**inputs)
                print("\nStockSense: " + plain_text(session.answer("Explain my suggested order")) + "\n")
            elif command.startswith("/") and command not in SHORTCUTS:
                print("Unknown command. Type /help for the command list.\n")
            else:
                print("\nStockSense: " + plain_text(session.answer(SHORTCUTS.get(command, question))) + "\n")
        except (ValueError, OSError, KeyError, ImportError) as error:
            print(f"StockSense: {error}\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Ask StockSense AI in your terminal using the saved project models.")
    parser.add_argument("--product", type=int, choices=ITEMS, default=1, help="Initially selected product (default: 1).")
    parser.add_argument("-q", "--question", help="Answer one question and exit instead of opening a chat.")
    args = parser.parse_args(argv)
    try:
        session = TerminalSession(ForecastService.load(), load_assistant(), args.product)
        if args.question is not None:
            print(plain_text(session.answer(args.question)))
        else:
            run_chat(session)
            print("Goodbye from StockSense.")
        return 0
    except (EOFError, KeyboardInterrupt):
        print("\nGoodbye from StockSense.")
        return 0
    except (ValueError, OSError, KeyError, ImportError) as error:
        print(f"Unable to start StockSense: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
