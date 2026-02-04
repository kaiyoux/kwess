# kwess_acb.py

import json
from pathlib import Path
from pprint import pprint as pp
from datetime import datetime as dt
import argparse
import math
import sys


class Activities:
    def __init__(self, cut_off_year=0, path="."):
        """
        Description:
            Initializer of an Activities object.
            Parameters:
                - cut_off_year the ACB will be calculated up until (but not including) the cut_off_year.
                - path directory path in which your Questrade investment activities logs are located.
            Returns:
                Activities object.
        """
        self.data = []
        self.all_symbols = set()
        self.path = path
        self.symbol = ""
        if cut_off_year == 0:
            self.cut_off_year = dt.today().year
        else:
            self.cut_off_year = cut_off_year
        self.load_from_json_files()

        
    def load_from_json_files(self):
        """
        Description:
            Loads activities logs. It is called during Activities object initialization.
        """
        p = Path(self.path)
        if not p.exists():
            print(f"Invalid path: {self.path}")
            sys.exit(1)
        data = []
        for e in p.glob("*activities*.json"):
            with e.open(mode="rt") as f:
                t = f.read()
                t = t.replace("}{", "},{")
                s = "[" + t + "]"
                l = json.loads(s)
                for d in l:
                    for v in d.values():
                        for a in v:
                            #pp(a)
                            if (dt.fromisoformat(a["settlementDate"]).year < self.cut_off_year) and (a["action"] in ("Buy", "Sell")):
                                data.append(a)
                                self.all_symbols.add(a["symbol"])
        self.data = sorted(data, key=lambda x: dt.fromisoformat(x["settlementDate"]))


    def generate_adjusted_cost_base(self, symbol, include_fees=True):
        """
        Description:
            Calculates the ACB and prints profit/loss of Sell transactions for the given symbol.
        Parameters:
                - symbol the ticker symbol.
                - include_fees whether or not to include the commission fees in the calculation. Defaults to True.    
        """
        prev_shares = 0
        prev_cost_base = 0
        prev_cost_base_per_share = 1
        add_newline = False
        for e in self.data:
            if e["symbol"] == symbol.upper():
                if e["action"] == "Buy":
                    shares = e["quantity"] + prev_shares
                    if include_fees:
                        cost_base = math.fabs(e["netAmount"]) + prev_cost_base  # includes commission and fees
                    else:
                        cost_base = math.fabs(e["grossAmount"]) + prev_cost_base  # does not include commission and fees
                    e["total_shares"] = shares
                    e["total_cost_base"] = cost_base
                    e["cost_base_per_share"] = cost_base / shares
                    prev_shares = shares
                    prev_cost_base = cost_base
                    prev_cost_base_per_share = e["cost_base_per_share"]
                elif e["action"] == "Sell":
                    cost_base_per_share = prev_cost_base_per_share
                    if include_fees:
                        #print(f"e[grossAmount] {e["grossAmount"]}\ne[commission] {e["commission"]}\ne[quantity] {e["quantity"]}\nprev_cost_base {prev_cost_base}\n prev_shares {prev_shares}")
                        capital_gain_loss = e["grossAmount"] + e["commission"] + e["quantity"] * cost_base_per_share
                    else:
                        capital_gain_loss = e["grossAmount"] + e["quantity"] * cost_base_per_share
                    prev_cost_base += e["quantity"] * cost_base_per_share
                    prev_shares += e["quantity"]
                    e["capital_gain_loss"] = capital_gain_loss
                    e["total_shares"] = prev_shares
                    e["total_cost_base"] = prev_cost_base # for debugging
                    e["cost_base_per_share"] = cost_base_per_share # for debugging
                    if capital_gain_loss > 0:
                        print(f'{symbol} capital gain of {capital_gain_loss} on {e["settlementDate"]}')
                        add_newline = True
                    elif capital_gain_loss < 0:
                        print(f'{symbol} capital loss of {capital_gain_loss} on {e["settlementDate"]}')
                        add_newline = True
        if add_newline:
            print()


    def generate_all_ACBs(self, include_fees=True):
        """
        Description:
            Calculates the ACB and prints profit/loss of Sell transactions for all the symbols present in the activities logs.
        Parameters:
                - include_fees whether or not to include the commission fees in the calculation. Defaults to True.    
        """
        for symbol in self.all_symbols:
            self.generate_adjusted_cost_base(symbol, include_fees)


    def print_by_symbol(self, symbol):
        """
        Description:
            Prints the activities logs relating to symbol.
        Parameters:
                - symbol the ticker symbol.    
        """
        for e in self.data:
            if e["symbol"] == symbol.upper():
                pp(e)


    def __str__(self):
        """
        Description:
            Used for printing the activities logs.
        Returns:
            String representation of the activities logs.
        """
        s = ""
        for e in self.data:
            s = "\n".join([s, str(e)])
        return s


    def __repr__(self):
        """
        Description:
            Used for printing the activities object.
        Returns:
            String representation of the Activities object.
        """
        return f"Activities(data: {self.data}\nsymbol: {self.symbol}\nall_symbols: {self.all_symbols}\npath: {self.path}\ncut_off_year: {self.cut_off_year})"


def main():
    """
        Description:
            Calculates the ACB and prints the profit/loss of Sell transactions for the symbol(s) present in the activities logs.
    """
    parser = argparse.ArgumentParser(prog="kwess_acb.py", description="Computes the ACB (Average/Adjusted Cost Base) from kwess activity logs, and prints profit/loss of Sell transactions.")
    parser.add_argument("-s", "--symbol", nargs="+", help="ticker symbol(s).")
    parser.add_argument("-y", "--cut_off_year", default=0, help="cut off year. defaults to the current year.")
    parser.add_argument("-p", "--path", default=".", help="path of the directory containing the logs. defaults to the current directory.")
    args = parser.parse_args()

    acts = Activities(cut_off_year=int(args.cut_off_year), path=args.path)
    if args.symbol:
        for symbol in args.symbol:
            acts.generate_adjusted_cost_base(symbol)
    else:
        acts.generate_all_ACBs()



if __name__ == "__main__":
    main()
