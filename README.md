##A restful email send service via smtp

- 支持ssl方式
- 支持ip白名单
- 可配置方式

##使用说明

- curl方式

curl -X POST -H "Content-Type: application/json; charset=utf-8" -d '{"to":"xxx@zuobin.net", "subject":"Send Test","content":"Test Mail"}' http://ip:port/sendMail

- api方式

post请求即可



