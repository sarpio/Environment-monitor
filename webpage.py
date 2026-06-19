def generate_html(temperature, humidity, pressure):
    return """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">

<title>ESP32S3</title>

<link rel="stylesheet" href="style.css">
</head>

<body class="simple-page">
<div class="card">

<h2>Pomiary</h2>

<div class="label">Temperatura</div>
<div class="value">{:.1f} °C</div>

<div class="label">Wilgotnosc</div>
<div class="value">{:.1f} %RH</div>

<div class="label">Cisnienie</div>
<div class="value">{:.1f} hPa</div>

<form>
<button type="submit">Odswiez</button>
</form>

</div>
</body>
</html>
""".format(temperature, humidity, pressure)
