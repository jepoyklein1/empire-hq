import json,base64,os
ROOT=os.path.dirname(os.path.abspath(__file__))
t=open(os.path.join(ROOT,'template.html')).read()
data=json.load(open(os.path.join(ROOT,'edition.json')))
djs=json.dumps(data,ensure_ascii=False,indent=1).replace("<","\\u003c")
av={k:"data:image/jpeg;base64,"+base64.b64encode(open(os.path.join(ROOT,"av",f"p_{k}.jpg"),"rb").read()).decode() for k in ["margaret","kenny","simone","jeff","anita","mona"]}
page=t.replace("__DATA__",djs).replace("__AV__",json.dumps(av))
head=("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
 "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1,viewport-fit=cover\">"
 "<meta name=\"robots\" content=\"noindex,nofollow\">"
 "<meta name=\"description\" content=\"League news, standings and dynasty rankings for The Empire Strikes Back.\">"
 "<style>html{color-scheme:light}:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}"
 "body{margin:0;font:14px/1.5 system-ui,-apple-system,sans-serif}img{max-width:100%}[hidden]{display:none!important}</style></head><body>")
open(os.path.join(ROOT,'..','index.html'),'w').write(head+page+"</body></html>")
print("built index.html")
