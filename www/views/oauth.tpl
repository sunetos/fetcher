<!doctype html>
<html>
<head>
	<meta charset="utf-8">
	<meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">

	<title>fetcher - a downloader for put.io</title>
	<meta name="description" content="">
	<meta name="author" content="">

	<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">

  <style>
    #token {
    }
  </style>
</head>
<body>
  <label for="token">Copy and paste this into Fetcher: </label>
  <input id="token" type="text" value="" readonly />

  <script>
    var url = '{{ url|safe }}', token = '{{ token|safe }}';
    var cue = 'access_token';

    if (!localStorage.putio_token) {
      var hash = window.location.hash;
      if (hash.charAt(0) === '#') hash = hash.substr(1);
      if (hash.substr(0, cue.length) === cue) {
        var token = hash.substr(cue.length);
        localStorage.putio_token = token;
      } else if (token.length) {
        localStorage.putio_token = token;
      } else {
        window.location.href = '{{ url|safe }}';
      }
    }
    if (localStorage.putio_token) {
      var tokenElem = document.getElementById('token');
      tokenElem.setAttribute('value', localStorage.putio_token);
    }
  </script>
</body>
</html>
