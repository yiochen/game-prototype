import http.server,urllib.request,urllib.parse,pathlib,re,json,hashlib
B=pathlib.Path(__file__).resolve().parent.parent;R=B/'reviews';mode='independent';rows=[]
class Proxy(http.server.BaseHTTPRequestHandler):
 def do_GET(self):
  global mode
  url=urllib.parse.urlsplit(self.path);q=urllib.parse.parse_qs(url.query,keep_blank_values=True)
  if url.path.endswith('/source/consumer-bench.html') and 'mode' in q:mode=q['mode'][0]
  match=re.search(r'/assets/production/sprites/(belt-corner-n-e|belt-straight-n)/running-([NESW])\.png$',url.path)
  if match and 'import' not in q:
   ident,d=match.groups();f=B/'candidates/round-01/atlases'/f'{"family-frames" if ident=="belt-straight-n" else "frames" if mode=="independent" else mode}-{d}.png';data=f.read_bytes();mime='image/png';rows.append({'url':self.path,'mode':mode,'file':str(f),'sha256':hashlib.sha256(data).hexdigest()});(R/'round01-proxy-served.json').write_text(json.dumps(rows,indent=2))
  else:
   try:
    with urllib.request.urlopen('http://127.0.0.1:4178'+self.path) as res:data=res.read();mime=res.headers.get('Content-Type','application/octet-stream')
   except Exception as e:self.send_error(502,str(e));return
  self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)
 def log_message(self,*args):pass
http.server.ThreadingHTTPServer(('127.0.0.1',4187),Proxy).serve_forever()
