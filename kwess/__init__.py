
import requests
import sys
from pprint import pprint
from datetime import datetime as dt, timezone as tz, timedelta as td
import time
import json
    


class Trader:
    def __init__(self, rt_file="refreshToken", server_type="live", timeout=15, verbose=''):
        """
        Description:
            Initializer of a Trader object. Before creating a Trader object for the very first time,
            you must generate a new token for manual authorization from your Questrade APP HUB,
            and save that manually generated token in a local file. That local file's filename
            (or pathname) is passed to rt_file.
            When Trader creates a Trader object, it exchanges that manually obtained token for an
            access token and a refresh token. The access token expires in 30 minutes and
            the refresh token expires in three days.
            As long as the refresh token has not expired, creating Trader objects or calling method
            get_new_refresh_token will obtain a new access token (if the current access token has
            expired) and obtain a new replacement refresh token that will last for another 3 days.
            Technically, as long as the current refresh token has not expired, it is possible
            to keep exchanging the current refresh token for a new access token and new refresh
            token pair indefinitely (by creating Trader objects or calling method
            get_new_refresh_token).
            If the refresh token ever expires, you must log back into your Questrade account,
            generate a new token for manual authorization under APP HUB, and save that token
            in the local file referred to by rt_file.
        Parameters:
            - rt_file name of your local file containing your refresh token.
            Defaults to "refreshToken".
            - server_type could be 2 possible values: "live" or "test". "live" will allow you to
            interact with your real Questrade account. "test" is for interacting with your test
            account.
            - timeout number of seconds to wait for the API server to respond before giving up.
            Defaults to 15 seconds. Set timeout to None if you wish to wait forever for a response.
            - verbose level of verbosity represented by the number of characters in a string.
            Defaults to empty string. Maximum verbosity is 1 or "v".
        Returns:
            Trader object.
        """
        self.server_url  = {
        "live":	"https://login.questrade.com/oauth2/token",
        "test":	"https://practicelogin.questrade.com/oauth2/token"
        }
        self.rt_file = rt_file
        self.timeout = timeout
        self.server_type = server_type
        try:
            with open("accessToken.json", mode="r", encoding="utf-8") as fp:
                rd = json.load(fp)
                self.access_token = rd["access_token"]
                self.token_type = rd["token_type"]
                self.api_server = rd["api_server"][:-1]
                self.refresh_token = rd["refresh_token"]
                self.expires_in = rd["expires_in"]
                self.expiry_date = rd["expiry_date"]
                dto = dt.strptime(self.expiry_date, '%Y-%m-%d %X')
                now = dt.now()
                if dto >= now:
                    try:
                        if verbose:
                            print("Access token still valid.")
                        self._get_accounts()
                        if verbose:
                            print("Got account(s)")
                    except:
                        raise Exception(f"Failed to obtain account(s).\nWill try to exchange refresh token from file {self.rt_file} for new access token/refresh token pair.")
                else:
                   raise Exception(f"Access token expired.\nWill try to exchange refresh token from file {self.rt_file} for new access token/refresh token pair.") 
        except:
            try:
                with open(rt_file, mode="rt", encoding="utf-8") as fp:
                    self.refresh_token = fp.read().strip()
                    self.get_new_refresh_token(token=self.refresh_token)
                    self._get_accounts()
                    if verbose:
                        print("Got account(s)")
            except Exception as ex:
                print(ex)
                print(f"Please log into your Questrade account (APP HUB), generate a new token for manual authorization, and save that token in local file {self.rt_file}, then try again.")
                sys.exit(1)
            

    def get_new_refresh_token(self, token, verbose=''):
        """
        Description:
            Obtains a new refresh token (and new access token) from the API server.
            You generally would not need to call this method, as it is potentially called by Trader
            during initialization.
            Trader will only call this method if the access token has expired.
        Parameters:
            - token the refresh token that is stored in the local file pointed to by rt_file.
            - verbose level of verbosity represented by the number of characters in a string.
            Defaults to empty string. Maximum verbosity is 1 or "v".
        """
        refresh_parameters = {'grant_type': 'refresh_token', 'refresh_token': token}
        try:
            resp = requests.get(self.server_url[self.server_type], params=refresh_parameters, timeout=self.timeout)
            resp.raise_for_status()
        except requests.exceptions.RequestException as ex:
            print(resp.request.url)
            print(f"{self.server_type} server returned {resp.status_code} on get_new_refresh_token() attempt.")
            print(ex)
            raise Exception()

        rd = resp.json()
        self.access_token = rd["access_token"]
        self.token_type = rd["token_type"]
        self.api_server = rd["api_server"][:-1]
        self.refresh_token = rd["refresh_token"]
        self.expires_in = rd["expires_in"]
        if verbose:
            print("Successfully exchanged refresh token for a new one, and a new {} minutes access token.".format(self.expires_in // 60))

        try:
            with open(self.rt_file, mode="wt", encoding="utf-8") as fp:
                fp.write(self.refresh_token)
        except Exception as ex:
            print(f"Could not save new refresh token in file {self.rt_file}:")
            print(ex)
        try:
            with open("accessToken.json", mode="w", encoding='utf-8') as jfp:
                now = dt.now()
                self.expiry_date = now + td(seconds=self.expires_in)
                rd["expiry_date"] = str(self.expiry_date)[:-7]
                json.dump(rd, jfp, ensure_ascii=False, indent=4)
        except Exception as ex:
            print("Could not save new access token in file accessToken.json:")
            print(ex)
            raise Exception()


    def _report_and_exit(self, *args):
        """
        Description:
            Prints messages passed as positional arguments, and exits.
        Parameters:
            - args tuple of printable objects.
        """
        for m in args:
            print(m)
        sys.exit(1)

        
    def _get_accounts(self):
        """
        Description:
            Retrieves the accounts associated with the user on behalf of which this API client
            is authorized.
            You generally would never call this method, as it is called in Trader.
            To obtain your account information, call the get_accounts method.
        """
        cmd_class = "v1/accounts"
        try:
            resp = requests.get("/".join([self.api_server, cmd_class]), headers={'Authorization': " ".join([self.token_type, self.access_token])}, timeout=self.timeout)
            resp.raise_for_status()
        except requests.exceptions.RequestException as ex:
            self._report_and_exit(resp.request.url, resp.text, f"{self.server_type} server returned {resp.status_code} on get_new_refresh_token() attempt.", ex)

        self.userid = resp.json()["userId"]
        self.accounts = resp.json()["accounts"] # list of accounts


    def get_accounts(self, verbose=''):
        """
        Description:
            Generator that provides the accounts.
        Parameters:
                - verbose level of verbosity represented by the number of characters in a string.
                Defaults to empty string. Maximum verbosity is 1 or "v".
        Returns:
            All your Questrade accounts as a Python object representation of the returned json.
        """
        if verbose:
            print(f"Accounts for user id {self.userid}:")
        for account in self.accounts:
            if verbose:
                pprint(account)
            yield account


    def get_all(f):
        """
        Description:
            Decorator used to circumvent the 30 day range limit imposed by Questrade for queries
            based on datetime ranges.
        Parameters:
            - f function containing two datetime parameters, among others, as start datetime and
            end datetime.
        Returns:
            A function containing two datetime parameters, among others, as start datetime and
            end datetime.
        """
        def inner(self, startdatetime, enddatetime=None, *args, **kwargs):
            if enddatetime == None:
                enddatetime = dt.now()
            dlt = enddatetime - startdatetime
            if dlt.days <= 29:
                js = f(self, startdatetime=startdatetime, enddatetime=enddatetime, *args, **kwargs)
                yield js
            else:
                thirdy_days = td(days=29)
                idt = startdatetime + thirdy_days
                js = f(self, startdatetime=startdatetime, enddatetime=idt, *args, **kwargs)
                yield js
                startdatetime = idt
                idt = startdatetime + thirdy_days
                dlt = enddatetime - startdatetime
                while dlt.days > 29:
                    js = f(self, startdatetime=startdatetime, enddatetime=idt, *args, **kwargs)
                    yield js
                    startdatetime = idt
                    idt = startdatetime + thirdy_days
                    dlt = enddatetime - startdatetime
                if dlt.days >= 1:
                    js = f(self, startdatetime=startdatetime, enddatetime=enddatetime, *args, **kwargs)
                    yield js
        return inner
            

    @get_all
    def get_account_activities(self, startdatetime, enddatetime=None, accounttype="TFSA", verbose=''):
        """ Description:
                Generator that returns the account activities from the account related to account
                type accounttype, 
                between the range specified by startdatetime and enddatetime. Both objects are
                datetime objects.
            Parameters:
                - startdatetime datetime object sepecifying the start of a range.
                - enddatetime optional datetime object specifying the end of a range. Defaults to
                now (datetime.datetime.now()) if not specified.
                - accounttype type of Questrade account. Defaults to "tfsa".
                - verbose level of verbosity represented by the number of characters in a string.
                Defaults to empty string. Maximum verbosity is 3 or "vvv".
            Returns:
                The account activities as a Python object representation of the returned json,
                between the range startdatetime and enddatetime, in chunks of 30 days.
        """
        accountnumber = self.find_account_number(accounttype)
        if accountnumber == None:
            self._report_and_exit(f"Nonexistent {accounttype} account.")
            
        sdt = self.build_datetime_string(startdatetime)
        edt = self.build_datetime_string(enddatetime)

        cmd_class = "v1/accounts"
        verbosity = len(verbose)
        if verbosity > 2:
            print("/".join([self.api_server, cmd_class, accountnumber, 'activities']))
            print(" ".join([self.token_type, self.access_token]))
        if verbosity > 0:
            print({'startTime': sdt, 'endTime': edt})	
        parameters = {'startTime': sdt, 'endTime': edt}
        try:
            resp = requests.get("/".join([self.api_server, cmd_class, accountnumber, 'activities']), headers={'Authorization': " ".join([self.token_type, self.access_token])}, params=parameters, timeout=self.timeout)
            resp.raise_for_status()
        except requests.exceptions.RequestException as ex:
            self._report_and_exit(resp.request.url, resp.text, "Failed to query server for account activities.", f"{self.server_type} server returned {resp.status_code} on get_account_activities().", ex)

        if verbosity > 1:
            pprint(resp.json())
        return resp.json()
    

    def values_to_dobj(self, y, m, d, h=0, mi=0, s=0):
        """
        Description:
            Helper method that builds a datetime object.
        Parameters:
            - y integer to be set as the year.
            - m intiger to be set as the month.
            - d integer to be set as the day.
            - h optional integer to be set as the hour. Default value is 0.
            - mi optional integer to be set as the minutes. Default value is 0.
            - s optional integer to be set as the seconds. Default value is 0.
        Returns:
            A datetime object from the values provided as parameters.
        """
        dto = dt.datetime(year=y, month=m, day=d, hour=h, minute=mi, second=s)
        return dto


    def object_to_qdstr(self, dto, gmt=False):
        """
        Description:
            Converts a datetime object to a Questrade datetime string.
        Parameters:
            - dto datetime object.
            - gmt optional boolean indicating if datetime is Greenwich Mean Time.
            Default value is False. 
        Returns:
            The provided datetime object in Questrade API compatible string format.
            Example: "2011-02-01T00:00:00-05:00".
            If gmt is set to False, time will be in local time.
            If gmt is True, the returned time will be considered as gmt time.
        """
        utcoffset = time.strftime("%z")
        if gmt:
            dto.replace(tzinfo=tz.utc)
            utcoffset = "+0000"
        stxt = dto.strftime("%Y-%m-%dT%X{}:{}".format(utcoffset[:3], utcoffset[-2:]))
        return stxt


    def values_to_qdstr(self, y, m, d, h=0, mi=0, s=0, gmt=False):
        """
        Description:
            Helper method that builds a Questrade datetime string.
            - y integer to be set as the year.
            - m intiger to be set as the month.
            - d integer to be set as the day.
            - h optional integer to be set as the hour. Default value is 0.
            - mi optional integer to be set as the minutes. Default value is 0.
            - s optional integer to be set as the seconds. Default value is 0.
            - gmt optional boolean indicating if datetime is Greenwich Mean Time.
            Default value is False. 
        Returns:
            The date time and timezone values provided as parameters in Questrade API compatible
            string format.
            Example: "2011-02-01T00:00:00-05:00".
            If gmt is set to False, time will be in local time.
            If gmt is True, the returned time will be considered as gmt time.
        """
        dto = self.values_to_dobj(y, m, d, h, mi, s)
        return self.object_to_qdstr(dto, gmt)

                            
    def build_datetime_string(self, adatetime=None, gmt=False):
        """
        Description:
            Higher level helper method used to build a Questrade datetime string.
        Parameters:
            - adatetime a datetime object.
            - gmt optional boolean indicating if datetime is Greenwich Mean Time.
            Default value is False.
        Returns:
            A Questrade datetime string.
        """
        if adatetime is None:
            d2 = dt.now()
            adt = self.object_to_qdstr(d2, gmt)
        else:
            adt = self.object_to_qdstr(adatetime, gmt)
        return adt


    def find_account_number(self, accounttype):
        """
        Description:
            Finds the account number corresponding to account type.
        Parameters:
            - accounttype the type of account. Example "tfsa", "margin", etc.
        Returns:
            An account number in string format.
        """
        for account in self.accounts:
            if accounttype.lower() == account["type"].lower():
                return account["number"]
        return None


    @get_all
    def get_account_orders(self, startdatetime, enddatetime=None, accounttype="TFSA", statefilter="All", verbose=''):
        """
        Description:
            Generator that provides the account orders from the account related to account type
            accounttype, 
            between the range specified by startdatetime and enddatetime. Both objects are
            datetime objects.
        Parameters:
            - startdatetime datetime object representing the beginning of a range.
            - enddatetime optional datetime object representing the end of a range.
            Defaults to now (datetime.datetime.now()) if not specified.
            - accounttype type of Questrade account. Defaults to "tfsa".
            - statefilter can be used to specify the state of orders.
            It has 3 possible values: Opened, Closed, or All. Defaults to "All".
            - verbose level of verbosity represented by the number of characters in a string.
            Defaults to empty string. Maximum verbosity is 3 or "vvv".
        Returns:
            Account orders as a Python object representation of the returned json,
            between the range startdatetime and enddatetime, in chunks of 30 days.
        """
        accountnumber = self.find_account_number(accounttype)
        if accountnumber == None:
            self._report_and_exit(f"Nonexistent {accounttype} account.")

        sdt = self.build_datetime_string(startdatetime)
        edt = self.build_datetime_string(enddatetime)

        cmd_class = "v1/accounts"
        verbosity = len(verbose)

        if statefilter.lower().startswith("o"):
            statefilter = "Open"
        elif statefilter.lower().startswith("c"):
            statefilter = "Closed"
        else:
            statefilter = "All"
        if verbosity > 2:
            print("/".join([self.api_server, cmd_class, accountnumber, 'orders']))
            print(" ".join([self.token_type, self.access_token]))
        if verbosity > 0:
            print({'startTime': sdt, 'endTime': edt})
        parameters = {'startTime': sdt, 'endTime': edt, 'stateFilter': statefilter}
        try:
            resp = requests.get("/".join([self.api_server, cmd_class, accountnumber, 'orders']), headers={'Authorization': " ".join([self.token_type, self.access_token])}, params=parameters, timeout=self.timeout)
            resp.raise_for_status()
        except requests.exceptions.RequestException as ex:
            self._report_and_exit(resp.request.url, resp.text, "Failed to query server for account orders.", f"{self.server_type} server returned {resp.status_code} on get_account_orders().", ex)

        if verbosity > 1:
            pprint(resp.json())
        return resp.json()


    def get_account_orders_by_ids(self, orderid, accounttype="TFSA", verbose=''):
        """
        Description:
            Provides the account orders, specified by orderid, from the account related to account
            type accounttype, 
        Parameters:
            - orderid is a string of one or many orderid numbers. Several orderid numbers are
            seperated by commas (with no spaces).
            a single orderid could be passed as a numeral instead of a string.
            - accounttype type of Questrade account. Defaults to "tfsa".
            - verbose level of verbosity represented by the number of characters in a string.
            Defaults to empty string. Maximum verbosity is 2 or "vv".
        Returns:
            Account orders as a Python object representation of the returned json.
        """
        accountnumber = self.find_account_number(accounttype)
        if accountnumber == None:
            self._report_and_exit(f"Nonexistent {accounttype} account.")
            
        cmd_class = "v1/accounts"
        verbosity = len(verbose)
        if verbosity > 1:
            print("/".join([self.api_server, cmd_class, accountnumber, 'orders']))
            print(" ".join([self.token_type, self.access_token]))
        parameters = {'ids': orderid}
        try:
            resp = requests.get("/".join([self.api_server, cmd_class, accountnumber, 'orders']), headers={'Authorization': " ".join([self.token_type, self.access_token])}, params=parameters, timeout=self.timeout)
            resp.raise_for_status()
        except requests.exceptions.RequestException as ex:
            self._report_and_exit(resp.request.url, resp.text, "Failed to query server for account orders by ids.", f"{self.server_type} server returned {resp.status_code} on get_account_orders_by_ids().", ex)

        if verbosity > 0:
            pprint(resp.json())
        return resp.json()
    

    @get_all
    def get_account_executions(self, accounttype="TFSA", startdatetime=None, enddatetime=None, verbose=''):
        """
        Description:
            Generator that provides account executions from the account related to account type
            accounttype, 
            between the range specified by startdatetime and enddatetime.
            Both objects are datetime objects.
        Parameters:
            - startdatetime datetime object representing the beginning of a range.
            - enddatetime datetime object representing the end of a range.
            Defaults to now (datetime.datetime.now()) if not specified.
            - accounttype type of Questrade account. Defaults to "tfsa".
            - verbose level of verbosity represented by the number of characters in a string.
            Defaults to empty string. Maximum verbosity is 3 or "vvv".
        Returns:
            Account executions as a Python object representation of the returned json,
            between the range startdatetime and enddatetime, in chunks of 30 days.
        """
        accountnumber = self.find_account_number(accounttype)
        if accountnumber == None:
            self._report_and_exit(f"Nonexistent {accounttype} account.")

        sdt = self.build_datetime_string(startdatetime)
        edt = self.build_datetime_string(enddatetime)

        cmd_class = "v1/accounts"
        verbosity = len(verbose)
        if verbosity > 2:
            print("/".join([self.api_server, cmd_class, accountnumber, 'executions']))
            print(" ".join([self.token_type, self.access_token]))
        if verbosity > 0:
            print({'startTime': sdt, 'endTime': edt})
        parameters = {'startTime': sdt, 'endTime': edt}
        try:
            resp = requests.get("/".join([self.api_server, cmd_class, accountnumber, 'executions']), headers={'Authorization': " ".join([self.token_type, self.access_token])}, params=parameters, timeout=self.timeout)
            resp.raise_for_status()
        except requests.exceptions.RequestException as ex:
            self._report_and_exit(resp.request.url, resp.text, "Failed to query server for account executions.", f"{self.server_type} server returned {resp.status_code} on get_account_executions().", ex)

        if verbosity > 1:
            pprint(resp.json())
        return resp.json()


    def get_account_balances(self, accounttype="TFSA", verbose=''):
        """
        Definition:
            Provides the account balances for the account related to account type accounttype.
        Paramaters:
            - accounttype type of Questrade account. Defaults to "tfsa".
            - verbose level of verbosity represented by the number of characters in a string.
            Defaults to empty string. Maximum verbosity is 2 or "vv".
        Returns:
            Account balances as a Python object representation of the returned json.
        """
        accountnumber = self.find_account_number(accounttype)
        if accountnumber == None:
            self._report_and_exit(f"Nonexistent {accounttype} account.")
            
        cmd_class = "v1/accounts"
        verbosity = len(verbose)
        if verbosity > 1:
            print("/".join([self.api_server, cmd_class, accountnumber, 'balances']))
            print(" ".join([self.token_type, self.access_token]))
        try:
            resp = requests.get("/".join([self.api_server, cmd_class, accountnumber, 'balances']), headers={'Authorization': " ".join([self.token_type, self.access_token])})
            resp.raise_for_status()
        except requests.exceptions.RequestException as ex:
            self._report_and_exit(resp.request.url, resp.text, "Failed to query server for account balances.", f"{self.server_type} server returned {resp.status_code} on get_account_balances().", ex)

        if verbosity > 0:
            pprint(resp.json())
        return resp.json()


    def get_account_positions(self, accounttype="TFSA", verbose=''):
        """
        Definition:
            Provides the account positions for the account related to account type accounttype.
        Paramaters:
            - accounttype type of Questrade account. Defaults to "tfsa".
            - verbose level of verbosity represented by the number of characters in a string.
            Defaults to empty string. Maximum verbosity is 2 or "vv".
        Returns:
            Account positions as a Python object representation of the returned json.
        """
        accountnumber = self.find_account_number(accounttype)
        if accountnumber == None:
            self._report_and_exit(f"Nonexistent {accounttype} account.")
            
        cmd_class = "v1/accounts"
        verbosity = len(verbose)
        if verbosity > 1:
            print("/".join([self.api_server, cmd_class, accountnumber, 'positions']))
            print(" ".join([self.token_type, self.access_token]))
        try:
            resp = requests.get("/".join([self.api_server, cmd_class, accountnumber, 'positions']), headers={'Authorization': " ".join([self.token_type, self.access_token])}, timeout=self.timeout)
            resp.raise_for_status()
        except requests.exceptions.RequestException as ex:
            self._report_and_exit(resp.request.url, resp.text, "Failed to query server for account positions.", f"{self.server_type} server returned {resp.status_code} on get_account_positions().", ex)

        if verbosity > 0:
            pprint(resp.json())
        return resp.json()


    def get_server_time(self, verbose=''):
        """
        Description:
            Provides the time from the Questrade API server.
        Parameters:
            - verbose level of verbosity represented by the number of characters in a string.
            Defaults to empty string. Maximum verbosity is 2 or "vv".
        Returns:
            The time on the server as a tuple made of a simple datetime object,
            as well as in the expected Python object representation of the returned json.
        """
        verbosity = len(verbose)
        if verbosity > 1:
            print("/".join([self.api_server, "v1/time"]))
            print(" ".join([self.token_type, self.access_token]))
        try:
            resp = requests.get("/".join([self.api_server, "v1/time"]), headers={'Authorization': " ".join([self.token_type, self.access_token])}, timeout=self.timeout)
            resp.raise_for_status()
        except requests.exceptions.RequestException as ex:
            self._report_and_exit(resp.request.url, resp.text, "Failed to query server for its time.", f"{self.server_type} server returned {resp.status_code} on get_server_time().", ex)

        rd = resp.json()
        if verbosity > 0:
            pprint(dt.strptime(rd["time"][:-13], '%Y-%m-%dT%X'))
        return dt.strptime(rd["time"][:-13], '%Y-%m-%dT%X'), rd


    @get_all
    def get_market_candles(self, sid, interval, startdatetime=None, enddatetime=None, verbose=''):
        """
        Description:
            Provides a list of json formatted market candles.
        Parameters:
            - sid symbol id as a string or numeral.
            - interval is the Historical Data Granularity.
            Examples: "OneMinute", "HalfHour", "OneYear".
            - startdatetime datetime object representing the beginning of a range.
            - enddatetime datetime object representing the end of a range.
            Defaults to now if not specified.
            - verbose level of verbosity represented by the number of characters in a string.
            Defaults to empty string. Maximum verbosity is 2 or "vv".
        Returns:
            Historical market data in the form of OHLC candlesticks for a specified symbol
            as a Python object representation of the returned json.
            This call is limited to returning 2,000 candlesticks in a single response.
            sid is a symbol id.
        """
        sdt = self.build_datetime_string(startdatetime)
        edt = self.build_datetime_string(enddatetime)
        
        cmd_class = "v1/markets"
        verbosity = len(verbose)
        if verbosity > 1:
            print("/".join([self.api_server, cmd_class, "candles", str(sid)]))
            print(" ".join([self.token_type, self.access_token]))
        parameters = {'startTime': sdt, 'endTime': edt, "interval": interval}
        try:
            resp = requests.get("/".join([self.api_server, cmd_class, "candles", str(sid)]), headers={'Authorization': " ".join([self.token_type, self.access_token])}, params=parameters, timeout=self.timeout)
            resp.raise_for_status()
        except requests.exceptions.RequestException as ex:
            self._report_and_exit(resp.request.url, resp.text, "Failed to query server for market candles.", f"{self.server_type} server returned {resp.status_code} on get_market_candles().", ex)

        if verbosity > 0:
            pprint(resp.json())
        return resp.json()
            

    def get_market_quotes_strategies(self, variants, verbose=''):
        """
        Definition:
            Provides a calculated L1 market data quote for a single or many multi-leg strategies.
        Parameter:
            - variants is a list of dictionary items.
            - verbose level of verbosity represented by the number of characters in a string.
            Defaults to empty string. Maximum verbosity is 2 or "vv".
        Returns:
            A calculated L1 market data quote for a single or many multi-leg strategies
            as a Python object representation of the returned json.
        """
        cmd_class = "v1/markets"
        parameters = {"variants": variants}
        verbosity = len(verbose)
        if verbosity > 1:
            print("/".join([self.api_server, cmd_class, "quotes/strategies"]))
            print(" ".join([self.token_type, self.access_token]))
        try:
            resp = requests.get("/".join([self.api_server, cmd_class, "quotes/strategies"]), headers={'Authorization': " ".join([self.token_type, self.access_token])}, params=parameters, timeout=self.timeout)
            resp.raise_for_status()
        except requests.exceptions.RequestException as ex:
            self._report_and_exit(resp.request.url, resp.text, "Failed to query server for market quote strategies.", f"{self.server_type} server returned {resp.status_code} on get_market_quotes_strategies().", ex)

        if verbosity > 0:
            pprint(resp.json())
        return resp.json()


    def get_market_quotes_options(self, option_ids, filters=None, verbose=''):
        """
        Definition:
            Provides market quotes options.
        Parameters:
            - option_ids is a list of stock option ids.
            - filters optional list of dictionary items.
            - verbose level of verbosity represented by the number of characters in a string.
            Defaults to empty string. Maximum verbosity is 2 or "vv".
        Returns:
            A single Level 1 market data quote and Greek data for one or more option symbols
            as a Python object representation of the returned json.
        """
        cmd_class = "v1/markets"
        parameters = {"optionIds": option_ids}
        if filters:
            parameters["filters"] = filters
        verbosity = len(verbose)
        if verbosity > 1:
            print("/".join([self.api_server, cmd_class, "quotes/options"]))
            print(" ".join([self.token_type, self.access_token]))
        try:
            resp = requests.post("/".join([self.api_server, cmd_class, "quotes/options"]), headers={'Authorization': " ".join([self.token_type, self.access_token])}, json=parameters, timeout=self.timeout)
            resp.raise_for_status()
        except requests.exceptions.RequestException as ex:
            self._report_and_exit(resp.request.url, resp.text, "Failed to query server for market quote options.", f"{self.server_type} server returned {resp.status_code} on get_market_quotes_options().", ex)

        if verbosity > 0:
            pprint(resp.json())
        return resp.json()
            
            
    def get_market_quotes(self, ids, verbose=''):
        """
        Definition:
            Provides market quotes data.
        Parameter:
            - ids Internal symbol identifier. Could be a single value or a string of values.
            - verbose level of verbosity represented by the number of characters in a string.
            Defaults to empty string. Maximum verbosity is 2 or "vv".
        Returns:
            A single Level 1 market data quote for one or more symbols in json string format
            as a Python object representation of the returned json.
            IMPORTANT NOTE: Questrade user needs to be subscribed to a real-time data package,
            to receive market quotes in real-time, otherwise call to get quote is considered
            snap quote and limit per market can be quickly reached. Without real-time data package,
            once limit is reached, the response will return delayed data.
            (Please check "delay" parameter in response always).
        """
        ids = str(ids)
        cmd_class = "v1/markets"
        parameters = {}
        resp = None
        verbosity = len(verbose)
        try:
            if type(ids) is str and "," in ids:
                parameters['ids'] = ids
                if verbosity > 1:
                    print("/".join([self.api_server, cmd_class, "quotes"]))
                    print(" ".join([self.token_type, self.access_token]))
                resp = requests.get("/".join([self.api_server, cmd_class, "quotes"]), headers={'Authorization': " ".join([self.token_type, self.access_token])}, params=parameters, timeout=self.timeout)
            elif ids: # single id
                if verbosity > 1:
                    print("/".join([self.api_server, cmd_class, "quotes", ids]))
                    print(" ".join([self.token_type, self.access_token]))
                resp = requests.get("/".join([self.api_server, cmd_class, "quotes", ids]), headers={'Authorization': " ".join([self.token_type, self.access_token])}, timeout=self.timeout)
            else:
                self._report_and_exit("Invalid parameter(s) for get_market_quotes.")
            resp.raise_for_status()
        except requests.exceptions.RequestException as ex:
            self._report_and_exit(resp.request.url, resp.text, "Failed to query server for market quotes.", f"{self.server_type} server returned {resp.status_code} on get_market_quotes().", ex)

        if verbosity > 0:
            pprint(resp.json())
        return resp.json()
    

    def get_markets(self, verbose=''):
        """
        Description:
            Provides market data.
        Parameters:
            - verbose level of verbosity represented by the number of characters in a string.
            Defaults to empty string. Maximum verbosity is 2 or "vv".
        Return:
            Information about supported markets as a Python object representation
            of the returned json.
        """
        cmd_class = "v1/markets"
        verbosity = len(verbose)
        if verbosity > 1:
            print("/".join([self.api_server, cmd_class]))
            print(" ".join([self.token_type, self.access_token]))
        try:
            resp = requests.get("/".join([self.api_server, cmd_class]), headers={'Authorization': " ".join([self.token_type, self.access_token])}, timeout=self.timeout)
            resp.raise_for_status()
        except requests.exceptions.RequestException as ex:
            self._report_and_exit(resp.request.url, resp.text, "Failed to query server for markets.", f"{self.server_type} server returned {resp.status_code} on get_markets().", ex)

        if verbosity > 0:
            pprint(resp.json())
        return resp.json()
    

    def get_symbol_options(self, sid, verbose=''):
        """
        Definition:
            Provides symbol options data.
        Parameter:
            - sid Internal symbol identifier.
            - verbose level of verbosity represented by the number of characters in a string.
            Defaults to empty string. Maximum verbosity is 2 or "vv".
        Returns:
            An option chain for a particular underlying symbol as a Python object representation
            of the returned json.
        """
        cmd_class = "v1/symbols"
        verbosity = len(verbose)
        if verbosity > 1:
            print("/".join([self.api_server, cmd_class, str(sid), "options"]))
            print(" ".join([self.token_type, self.access_token]))
        try:
            resp = requests.get("/".join([self.api_server, cmd_class, str(sid), "options"]), headers={'Authorization': " ".join([self.token_type, self.access_token])}, timeout=self.timeout)
            resp.raise_for_status()
        except requests.exceptions.RequestException as ex:
            self._report_and_exit(resp.request.url, resp.text, "Failed to query server for symbol options.", f"{self.server_type} server returned {resp.status_code} on get_symbol_options().", ex)

        if verbosity > 0:
            pprint(resp.json())
        return resp.json()
            

    def search_symbols(self, prefix, offset=0, verbose=''):
        """
        Definition:
            Provides symbol(s) data using several search criteria.
        Parameters:
            - prefix Prefix of a symbol or any word in the description.
            - offset Offset in number of records from the beginning of a result set.
            Default is not to offset.
            - verbose level of verbosity represented by the number of characters in a string.
            Defaults to empty string. Maximum verbosity is 2 or "vv".
        Returns:
            Symbol(s) data as a Python object representation of the returned json.
        """
        cmd_class = "v1/symbols"
        parameters = {"prefix": prefix, "offset": offset}
        verbosity = len(verbose)
        if verbosity > 1:
            print("/".join([self.api_server, cmd_class, 'search']))
            print(" ".join([self.token_type, self.access_token]))
        try:
            resp = requests.get("/".join([self.api_server, cmd_class, 'search']), headers={'Authorization': " ".join([self.token_type, self.access_token])}, params=parameters, timeout=self.timeout)
            resp.raise_for_status()
        except requests.exceptions.RequestException as ex:
            self._report_and_exit(resp.request.url, resp.text, "Failed to search server for symbols.", f"{self.server_type} server returned {resp.status_code} on search_symbols().", ex)

        if verbosity > 0:
            pprint(resp.json())
        return resp.json()


    def get_symbols_by_ids(self, ids, verbose=''):
        """
        Definition:
            Provides symbols data from symbol id(s).
        Parameter:
            - ids Internal symbol identifier(s). Could be a single numeric value or a string of
            comma-seperated values (with no spaces).
            - verbose level of verbosity represented by the number of characters in a string.
            Defaults to empty string. Maximum verbosity is 2 or "vv".
        Returns:
            Detailed information about one or more symbol as a Python object representation
            of the returned json.
        """
        ids = str(ids)
        cmd_class = "v1/symbols"
        parameters = {}
        resp = None
        verbosity = len(verbose)
        try:
            if type(ids) is str and "," in ids:
                parameters['ids'] = ids
                if verbosity > 1:
                    print("/".join([self.api_server, cmd_class]))
                    print(" ".join([self.token_type, self.access_token]))
                resp = requests.get("/".join([self.api_server, cmd_class]), headers={'Authorization': " ".join([self.token_type, self.access_token])}, params=parameters, timeout=self.timeout)
            elif ids: # single id
                if verbosity > 1:
                    print("/".join([self.api_server, cmd_class, ids]))
                    print(" ".join([self.token_type, self.access_token]))
                resp = requests.get("/".join([self.api_server, cmd_class, ids]), headers={'Authorization': " ".join([self.token_type, self.access_token])}, timeout=self.timeout)
            else:
                self._report_and_exit("Invalid parameter(s) for get_symbols_by_ids.")
            resp.raise_for_status()
        except requests.exceptions.RequestException as ex:
            self._report_and_exit(resp.request.url, resp.text, "Failed to query server for symbols by ids.", f"{self.server_type} server returned {resp.status_code} on get_symbols_by_ids().", ex)

        if verbosity > 0:
            pprint(resp.json())
        return resp.json()


    def get_symbols_by_names(self, names, verbose=''):
        """
        Definition:
            Provides symbols data from name(s).
        Parameter:
            - names is a string of names seperated by commas (with no spaces).
            - verbose level of verbosity represented by the number of characters in a string.
            Defaults to empty string. Maximum verbosity is 2 or "vv".
        Returns:
            Detailed information about one or more symbol as a Python object representation
            of the returned json.
        """
        cmd_class = "v1/symbols"
        parameters = {}
        resp = None
        verbosity = len(verbose)
        try:
            if names:
                parameters['names'] = names
                if verbosity > 1:
                    print("/".join([self.api_server, cmd_class]))
                    print(" ".join([self.token_type, self.access_token]))
                resp = requests.get("/".join([self.api_server, cmd_class]), headers={'Authorization': " ".join([self.token_type, self.access_token])}, params=parameters, timeout=self.timeout)
            else:
                self._report_and_exit("Invalid parameter(s) for get_symbols_by_names.")
            resp.raise_for_status()
        except requests.exceptions.RequestException as ex:
            self._report_and_exit(resp.request.url, resp.text, "Failed to query server for symbols by names.", f"{self.server_type} server returned {resp.status_code} on get_symbols_by_names().", ex)

        if verbosity > 0:
            pprint(resp.json())
        return resp.json()

