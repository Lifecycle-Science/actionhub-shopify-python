const config = {
  apiKey: '{{ client_id }}',
  host: new URLSearchParams(location.search).get("host"),
  forceRedirect: true
};
console.log(config)