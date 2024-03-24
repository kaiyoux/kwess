# Introduction

Yet another Questrade API wrapper.

For details about the input parameters and output results, please visit
the [Questrade API documentation](https://www.questrade.com/api/home).

### To install:
**python -m pip install kwess**


# Usage Example

```
import kwess
from datetime import datetime as dt
from pprint import pprint

# It is assumed that your manually generated token has been saved in local file 
# my_token.txt
qs = kwess.Trader(rt_file="my_token.txt", verbose="v")

accs = qs.get_accounts()
for acc in accs:
    print(acc, "\n")

accn = qs.find_account_number("tfsa")
print(accn)

# Get account activities from 1/12/1999 to 28/9/2022
accs = qs.get_account_activities(startdatetime=dt(year=1999, month=12, day=1), \
enddatetime=dt(year=2022, month=9, day=28), verbose="xxx")
for acc in accs:
    print(acc, "\n")

# Get (all types of) TFSA account orders from 17/8/2022 to now
accs = qs.get_account_orders(startdatetime=dt(year=2022, month=8, day=17), \
verbose="vv")
for acc in accs:
    print(acc, "\n")

# Get margin account orders that are still open
accs = qs.get_account_orders(accounttype="margin", startdatetime=dt(year=2022, \
month=7, day=28), enddatetime=dt.now(), statefilter="opened", verbose="333")
for acc in accs:
    print(acc, "\n")

ords = qs.get_account_orders_by_ids(accounttype="tfsa", orderid="1088713788", \
verbose="b")
pprint(ords)

ords = qs.get_account_orders_by_ids(orderid="1098747429,1088752426,1088713788", \
verbose="aa")
pprint(ords)

ords = qs.get_account_orders_by_ids(orderid=1098747429)
pprint(ords)

# Get the current time from the API server
dto = qs.get_server_time()
print(dto[0])
print(dto[1])

# Questrade does not seem to keep old account executions - only the most recent
excs = qs.get_account_executions(startdatetime=dt(year=2022, month=1, day=28), \
enddatetime=dt(year=2022, month=9, day=30), verbose="o")
for exc in excs:
    print(exc, "\n")

accs = qs.get_account_balances()
print(accs)

accs = qs.get_account_positions(verbose="d")
print(accs)

sim = qs.search_symbols("vfv", verbose="88")
print(sim)

sim = qs.get_symbols_by_names("xdiv.to,xuu.to,cve.to", verbose="**")
print(sim)

sim = qs.get_symbols_by_names("hom.un.to")
print(sim)

sim = qs.get_symbols_by_ids(26070347, verbose="e")
print(sim)

sim = qs.get_symbols_by_ids("26070347,12890,8953192,18070692", verbose="ee")
print(sim)

sim = qs.get_symbol_options(12890, verbose="s")
pprint(sim)

mks = qs.get_markets()
pprint(mks)

mks = qs.get_market_quotes(12890,verbose="zz")
print(mks)

mks = qs.get_market_quotes("26070347,12890,8953192,18070692", verbose="h")
print(mks)

ops = qs.get_market_quotes_options(option_ids=[9907637,9907638])
pprint(ops)

```


# API Class And Methods

class Trader
```
__init__(self, rt_file='refreshToken', server_type='live', timeout=15, verbose='')
Description:
    Initializer of a Trader object. Before creating a Trader object (for the very 
    first time or when the present token has expired), you must generate a new 
    token for manual authorization from your Questrade APP HUB, and save that 
    manually generated token in a local file. That local file's filename 
    (or pathname) is passed to rt_file.
    When Trader creates a Trader object, it exchanges that manually obtained token 
    for an access token and a refresh token. The access token expires in 30 minutes 
    and the refresh token expires in three days.
    As long as the refresh token has not expired, creating Trader objects or 
    calling method get_new_refresh_token will obtain a new access token (if the 
    current access token has expired) and obtain a new replacement refresh token 
    that will last for another 3 days.
    Technically, as long as the current refresh token has not expired, it is 
    possible to keep exchanging the current refresh token for a new access token and 
    new refresh token pair indefinitely (by creating Trader objects or calling 
    method get_new_refresh_token).
    If the refresh token ever expires, you must log back into your Questrade account,
    generate a new token for manual authorization under APP HUB, and save that token
    in the local file referred to by rt_file.
Parameters:
    - rt_file name of your local file containing your refresh token.
    Defaults to "refreshToken".
    - server_type could be 2 possible values: "live" or "test". 
    "live" will allow you to interact with your real Questrade account. 
    "test" is for interacting with your test account.
    - timeout number of seconds to wait for the API server to respond before 
    giving up.
    Defaults to 15 seconds. Set timeout to None if you wish to wait forever 
    for a response.
    - verbose level of verbosity represented by the number of characters in a string.
    Defaults to empty string. Maximum verbosity is 1 or "v".
Returns:
    Trader object.


build_datetime_string(self, adatetime=None, gmt=False)
Description:
    Higher level helper method used to build a Questrade datetime string.
Parameters:
    - adatetime a datetime object.
    - gmt optional boolean indicating if datetime is Greenwich Mean Time.
    Default value is False.
Returns:
    A Questrade datetime string.


find_account_number(self, accounttype)
Description:
    Finds the account number corresponding to account type.
Parameters:
    - accounttype the type of account. Example "tfsa", "margin", etc.
Returns:
    An account number in string format.


get_account_activities(self, startdatetime, enddatetime=None, accounttype='TFSA',
verbose='')
Description:
    Generator that returns the account activities from the account related to account 
    type accounttype, between the range specified by startdatetime and enddatetime. 
    Both objects are datetime objects.
Parameters:
    - startdatetime datetime object specifying the start of a range.
    - enddatetime optional datetime object specifying the end of a range. 
    Defaults to now (datetime.datetime.now()) if not specified.
    - accounttype type of Questrade account. 
    Defaults to "tfsa".
    - verbose level of verbosity represented by the number of characters in a string.
    Defaults to empty string. Maximum verbosity is 3 or "vvv".
Yields:
    The account activities as a Python object representation of the returned json,
    between the range startdatetime and enddatetime, in chunks of 30 days.


get_account_balances(self, accounttype='TFSA', verbose='')
Definition:
    Provides the account balances for the account related to account type 
    accounttype.
Paramaters:
    - accounttype type of Questrade account. 
    Defaults to "tfsa".
    - verbose level of verbosity represented by the number of characters in 
    a string. 
    Defaults to empty string. Maximum verbosity is 2 or "vv".
Returns:
    Account balances as a Python object representation of the returned json.


get_account_executions(self, accounttype='TFSA', startdatetime=None, 
enddatetime=None, verbose='')
Description:
    Generator that provides account executions from the account related to 
    account type accounttype, between the range specified by startdatetime and 
    enddatetime. Both objects are datetime objects.
Parameters:
    - startdatetime datetime object representing the beginning of a range.
    - enddatetime datetime object representing the end of a range.
    Defaults to now (datetime.datetime.now()) if not specified.
    - accounttype type of Questrade account. 
    Defaults to "tfsa".
    - verbose level of verbosity represented by the number of characters in 
    a string.
    Defaults to empty string. Maximum verbosity is 3 or "vvv".
Yields:
    Account executions as a Python object representation of the returned json,
    between the range startdatetime and enddatetime, in chunks of 30 days.


get_account_orders(self, startdatetime, enddatetime=None, accounttype='TFSA', 
statefilter='All', verbose='')
Description:
    Generator that provides the account orders from the account related to 
    account type accounttype, between the range specified by startdatetime and 
    enddatetime. Both objects are datetime objects.
Parameters:
    - startdatetime datetime object representing the beginning of a range.
    - enddatetime optional datetime object representing the end of a range.
    Defaults to now (datetime.datetime.now()) if not specified.
    - accounttype type of Questrade account. 
    Defaults to "tfsa".
    - statefilter can be used to specify the state of orders.
    It has 3 possible values: Opened, Closed, or All. 
    Defaults to "All".
    - verbose level of verbosity represented by the number of characters in a string.
    Defaults to empty string. Maximum verbosity is 3 or "vvv".
Yields:
    Account orders as a Python object representation of the returned json,
    between the range startdatetime and enddatetime, in chunks of 30 days.


get_account_orders_by_ids(self, orderid, accounttype='TFSA', verbose='')
Description:
    Provides the account orders, specified by orderid, from the account related to 
    account type accounttype.
Parameters:
    - orderid is a string of one or many orderid numbers. Several orderid numbers are
    seperated by commas (with no spaces). A single orderid could be passed as 
    a numeral instead of a string.
    - accounttype type of Questrade account. 
    Defaults to "tfsa".
    - verbose level of verbosity represented by the number of characters in a string.
    Defaults to empty string. Maximum verbosity is 2 or "vv".
Returns:
    Account orders as a Python object representation of the returned json.


get_account_positions(self, accounttype='TFSA', verbose='')
Definition:
    Provides the account positions for the account related to account type 
    accounttype.
Paramaters:
    - accounttype type of Questrade account. 
    Defaults to "tfsa".
    - verbose level of verbosity represented by the number of characters in a string.
    Defaults to empty string. Maximum verbosity is 2 or "vv".
Returns:
    Account positions as a Python object representation of the returned json.


get_accounts(self, verbose='')
Description:
    Generator that provides the accounts.
Parameters:
    - verbose level of verbosity represented by the number of characters in a string.
    Defaults to empty string. Maximum verbosity is 1 or "v".
Yields:
    All your Questrade accounts as a Python object representation of the returned 
    json.


get_market_candles(self, sid, interval, startdatetime=None, enddatetime=None, 
verbose='')
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


get_market_quotes(self, ids, verbose='')
Definition:
    Provides market quotes data.
Parameter:
    - ids Internal symbol identifier. Could be a single value or a string of values.
    - verbose level of verbosity represented by the number of characters in a string.
    Defaults to empty string. Maximum verbosity is 2 or "vv".
Returns:
    A single Level 1 market data quote for one or more symbols in json string format
    as a Python object representation of the returned json.
    IMPORTANT NOTE: Questrade user needs to be subscribed to a real-time data 
    package, to receive market quotes in real-time, otherwise call to get quote 
    is considered snap quote and limit per market can be quickly reached. 
    Without real-time data package, once limit is reached, the response will return 
    delayed data. (Please check "delay" parameter in response always).


get_market_quotes_options(self, option_ids, filters=None, verbose='')
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


get_market_quotes_strategies(self, variants, verbose='')
Definition:
    Provides a calculated L1 market data quote for a single or many multi-leg 
    strategies.
Parameter:
    - variants is a list of dictionary items.
    - verbose level of verbosity represented by the number of characters in a string.
    Defaults to empty string. Maximum verbosity is 2 or "vv".
Returns:
    A calculated L1 market data quote for a single or many multi-leg strategies
    as a Python object representation of the returned json.


get_markets(self, verbose='')
Description:
    Provides market data.
Parameters:
    - verbose level of verbosity represented by the number of characters in a string.
    Defaults to empty string. Maximum verbosity is 2 or "vv".
Returns:
    Information about supported markets as a Python object representation of 
    the returned json.


get_new_refresh_token(self, token, server_type, verbose='')
Description:
    Obtains a new refresh token (and new access token) from the API server.
    You generally would not need to call this method, as it is potentially called by
    Trader during initialization.
    Trader will only call this method if the access token has expired.
Parameters:
    - token the refresh token that is stored in the local file pointed to by rt_file.
    - server_type should be "live" or "test" for your live Questrade account or 
    your test Questrade account, respectively.
    - verbose level of verbosity represented by the number of characters in a string.
    Defaults to empty string. Maximum verbosity is 1 or "v".


get_server_time(self, verbose='')
Description:
    Provides the time from the Questrade API server.
Parameters:
    - verbose level of verbosity represented by the number of characters in a string.
    Defaults to empty string. Maximum verbosity is 2 or "vv".
Returns:
    The time on the server as a tuple made of a simple datetime object,
    as well as in the expected Python object representation of the returned json.


get_symbol_options(self, sid, verbose='')
Definition:
    Provides symbol options data.
Parameter:
    - sid Internal symbol identifier.
    - verbose level of verbosity represented by the number of characters in a string.
    Defaults to empty string. Maximum verbosity is 2 or "vv".
Returns:
    An option chain for a particular underlying symbol as a Python object 
    representation of the returned json.


get_symbols_by_ids(self, ids, verbose='')
Definition:
    Provides symbols data from symbol id(s).
Parameter:
    - ids Internal symbol identifier(s). Could be a single numeric value or a string 
    of comma-seperated values (with no spaces).
    - verbose level of verbosity represented by the number of characters in a string.
    Defaults to empty string. Maximum verbosity is 2 or "vv".
Returns:
    Detailed information about one or more symbol as a Python object representation
    of the returned json.


get_symbols_by_names(self, names, verbose='')
Definition:
    Provides symbols data from name(s).
Parameter:
    - names is a string of names seperated by commas (with no spaces).
    - verbose level of verbosity represented by the number of characters in a string.
    Defaults to empty string. Maximum verbosity is 2 or "vv".
Returns:
    Detailed information about one or more symbol as a Python object representation
    of the returned json.


object_to_qdstr(self, dto, gmt=False)
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


search_symbols(self, prefix, offset=0, verbose='')
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


values_to_dobj(self, y, m, d, h=0, mi=0, s=0)
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


values_to_qdstr(self, y, m, d, h=0, mi=0, s=0, gmt=False)
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
    The date time and timezone values provided as parameters in Questrade API 
    compatible string format.
    Example: "2011-02-01T00:00:00-05:00".
    If gmt is set to False, time will be in local time.
    If gmt is True, the returned time will be considered as gmt time.
```


Let me know if you have any questions: <kaiyoux@gmail.com>
