import os
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)


def get_prices(symbol, interval):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

    params = {
        "interval": interval,
        "range": "1d"
    }

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=15
    )

    response.raise_for_status()

    data = response.json()
    result = data["chart"]["result"][0]

    closes = result["indicators"]["quote"][0]["close"]

    prices = []

    for price in closes:
        if price is not None:
            prices.append(float(price))

    return prices


def ema(prices, period):
    if len(prices) < period:
        return None

    value = sum(prices[:period]) / period
    multiplier = 2 / (period + 1)

    for price in prices[period:]:
        value = (price - value) * multiplier + value

    return value


def rsi(prices, period=14):
    if len(prices) < period + 1:
        return None

    gains = []
    losses = []

    for i in range(1, len(prices)):
        change = prices[i] - prices[i - 1]

        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):
        avg_gain = (
            (avg_gain * (period - 1)) + gains[i]
        ) / period

        avg_loss = (
            (avg_loss * (period - 1)) + losses[i]
        ) / period

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss

    return 100 - (100 / (1 + rs))


def make_signal(prices):

    if len(prices) < 30:
        return {
            "signal": "WAIT",
            "confidence": 0,
            "reason": "Not enough market data."
        }

    price = prices[-1]

    ema9 = ema(prices, 9)
    ema21 = ema(prices, 21)
    rsi_value = rsi(prices)

    score = 0
    reasons = []

    if ema9 > ema21:
        score += 1
        reasons.append("EMA 9 is above EMA 21")
    else:
        score -= 1
        reasons.append("EMA 9 is below EMA 21")

    if price > ema9:
        score += 1
        reasons.append("Price is above EMA 9")
    else:
        score -= 1
        reasons.append("Price is below EMA 9")

    if rsi_value < 30:
        score += 1
        reasons.append("RSI is oversold")
    elif rsi_value > 70:
        score -= 1
        reasons.append("RSI is overbought")

    if score >= 2:
        signal = "BUY"
    elif score <= -2:
        signal = "SELL"
    else:
        signal = "WAIT"

    confidence = min(95, 50 + abs(score) * 15)

    return {
        "signal": signal,
        "confidence": confidence,
        "price": round(price, 5),
        "ema9": round(ema9, 5),
        "ema21": round(ema21, 5),
        "rsi": round(rsi_value, 2),
        "reason": " • ".join(reasons)
    }


@app.route("/")
def home():

    return """
<!DOCTYPE html>

<html>

<head>

<meta name="viewport"
content="width=device-width, initial-scale=1">

<title>Smart Signal AI</title>

<style>

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #07111f;
    color: white;
}

.container {
    max-width: 700px;
    margin: auto;
    padding: 20px;
}

h1 {
    text-align: center;
    margin-bottom: 5px;
}

.subtitle {
    text-align: center;
    color: #9ca9ba;
    margin-bottom: 20px;
}

.card {
    background: #101d2e;
    padding: 20px;
    margin-top: 15px;
    border-radius: 15px;
    border: 1px solid #24354a;
}

label {
    display: block;
    margin-top: 10px;
    color: #b7c4d4;
}

select,
button {

    width: 100%;
    padding: 14px;
    margin-top: 8px;
    border-radius: 10px;
    font-size: 16px;
}

select {
    background: #07111f;
    color: white;
    border: 1px solid #34465c;
}

button {
    background: #2563eb;
    color: white;
    border: none;
    font-weight: bold;
    margin-top: 20px;
}

#signal {

    text-align: center;
    font-size: 45px;
    font-weight: bold;
    margin: 20px;
}

.green {
    color: #22c55e;
}

.red {
    color: #ef4444;
}

.yellow {
    color: #f59e0b;
}

.stats {

    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
}

.stat {

    background: #07111f;
    padding: 15px;
    border-radius: 10px;
    text-align: center;
}

.stat-title {
    color: #8998aa;
    font-size: 13px;
    margin-bottom: 7px;
}

.stat-value {
    font-size: 18px;
    font-weight: bold;
}

.reason {
    color: #c4cfdb;
    line-height: 1.6;
}

.warning {
    color: #8998aa;
    font-size: 12px;
    text-align: center;
    margin-top: 20px;
}

</style>

</head>

<body>

<div class="container">

<h1>🤖 Smart Signal AI</h1>

<div class="subtitle">
Indicator-based market analysis
</div>


<div class="card">

<label>Choose Market</label>

<select id="symbol">

<option value="EURUSD=X">
EUR/USD
</option>

<option value="GBPUSD=X">
GBP/USD
</option>

<option value="USDJPY=X">
USD/JPY
</option>

<option value="AUDUSD=X">
AUD/USD
</option>

<option value="USDCAD=X">
USD/CAD
</option>

<option value="BTC-USD">
Bitcoin
</option>

<option value="ETH-USD">
Ethereum
</option>

</select>


<label>Choose Timeframe</label>

<select id="interval">

<option value="1m">
1 Minute
</option>

<option value="5m" selected>
5 Minutes
</option>

<option value="15m">
15 Minutes
</option>

<option value="30m">
30 Minutes
</option>

<option value="1h">
1 Hour
</option>

</select>


<button onclick="getSignal()">
GET AI SIGNAL
</button>

</div>


<div class="card">

<div id="signal" class="yellow">
WAIT
</div>

<div id="confidence"
style="text-align:center;color:#b7c4d4;">
Press GET AI SIGNAL
</div>

</div>


<div class="card">
<div class="card">

    <h3>📊 Live Candlestick Chart</h3>

    <p style="color:#9ca9ba;">
        View market movements and candlestick patterns.
    </p>

    <div
        class="tradingview-widget-container"
        style="height:450px;width:100%;"
    >

        <div
            class="tradingview-widget-container__widget"
            style="height:450px;width:100%;"
        ></div>

        <script
            type="text/javascript"
            src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js"
            async
        >
        {
            "autosize": true,
            "symbol": "FX:USDJPY",
            "interval": "1",
            "timezone": "Etc/UTC",
            "theme": "dark",
            "style": "1",
            "locale": "en",
            "allow_symbol_change": true,
            "hide_side_toolbar": true,
            "withdateranges": true,
            "details": false,
            "hotlist": false,
            "calendar": false,
            "support_host": "https://www.tradingview.com"
        }
        </script>

    </div>

</div>
<div class="stats">

<div class="stat">

<div class="stat-title">
PRICE
</div>

<div id="price" class="stat-value">
--
</div>

</div>


<div class="stat">

<div class="stat-title">
EMA 9
</div>

<div id="ema9" class="stat-value">
--
</div>

</div>


<div class="stat">

<div class="stat-title">
EMA 21
</div>

<div id="ema21" class="stat-value">
--
</div>

</div>


<div class="stat">

<div class="stat-title">
RSI
</div>

<div id="rsi" class="stat-value">
--
</div>

</div>

</div>

</div>


<div class="card">

<h3>📊 Analysis</h3>

<div id="reason" class="reason">
No analysis yet.
</div>

</div>


<div class="warning">
Signals are indicator-based and are not guaranteed.
</div>


</div>


<script>

async function getSignal() {

    const symbol =
        document.getElementById("symbol").value;

    const interval =
        document.getElementById("interval").value;

    const signal =
        document.getElementById("signal");

    signal.innerText = "LOADING...";

    signal.className = "yellow";


    try {

        const response =
            await fetch(
                "/api/signal?symbol="
                + encodeURIComponent(symbol)
                + "&interval="
                + encodeURIComponent(interval)
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.error ||
                "Unable to get market data"
            );

        }


        signal.innerText =
            data.signal;


        if (data.signal === "BUY") {

            signal.className = "green";

        }

        else if (data.signal === "SELL") {

            signal.className = "red";

        }

        else {

            signal.className = "yellow";

        }


        document.getElementById("confidence")
            .innerText =
            "Confidence: "
            + data.confidence
            + "%";


        document.getElementById("price")
            .innerText =
            data.price ?? "--";


        document.getElementById("ema9")
            .innerText =
            data.ema9 ?? "--";


        document.getElementById("ema21")
            .innerText =
            data.ema21 ?? "--";


        document.getElementById("rsi")
            .innerText =
            data.rsi ?? "--";


        document.getElementById("reason")
            .innerText =
            data.reason ||
            "No analysis available.";

    }

    catch(error) {

        signal.innerText = "ERROR";

        signal.className = "red";

        document.getElementById("confidence")
            .innerText =
            error.message;

    }

}

</script>

</body>

</html>
"""


@app.route("/api/signal")
def api_signal():

    symbol = request.args.get(
        "symbol",
        "EURUSD=X"
    )

    interval = request.args.get(
        "interval",
        "5m"
    )

    try:

        prices = get_prices(
            symbol,
            interval
        )

        result = make_signal(prices)

        result["symbol"] = symbol
        result["interval"] = interval

        return jsonify(result)

    except Exception as e:

        return jsonify({
            "signal": "WAIT",
            "confidence": 0,
            "error": str(e)
        }), 500


if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
